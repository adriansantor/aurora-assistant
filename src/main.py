#!/usr/bin/env python3
"""Aurora Assistant - Orquestador principal que integra predicción, enrutamiento y ejecución."""
import logging
import sys
from pathlib import Path

from src.nlp.predict import predict, PredictError
from src.core.executor import CommandExecutor, CommandExecutionError, CommandNotAllowedError
from src.core.router import CommandRouter, UserConfirmationRequired, ConfidenceTooLowError
from src.audio.wakeword import remove_wakeword
from src.audio.mic import get_capture, MicrophoneError
from src.asr.transcribe import get_transcriber, TranscriptionError, UnauthorizedSpeakerError
from src.audio.speaker_verify import get_verifier, SpeakerVerificationError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent


class AuroraAssistant:
    """Orquestador principal del Asistente Aurora."""
    
    def __init__(
        self,
        auto_execute_threshold: float = 0.75,
        confirmation_threshold: float = 0.4,
        commands_path: str = None,
    ):
        """Inicializar Asistente Aurora con umbrales de confianza configurables."""
        if commands_path is None:
            commands_path = PROJECT_ROOT / "commands" / "commands.json"
        
        # Inicializar componentes
        self.executor = CommandExecutor(Path(commands_path))
        self.router = CommandRouter(
            executor=self.executor,
            auto_execute_threshold=auto_execute_threshold,
            confirmation_threshold=confirmation_threshold,
        )
        
        logger.info("Asistente Aurora inicializado")
        logger.info(f"Comandos disponibles: {', '.join(self.executor.list_commands())}")
    
    def process_text(self, text: str) -> bool:
        """Procesar texto de entrada del usuario. Retorna True si ejecutado, False en caso contrario."""
        logger.info(f"Procesando: '{text}'")
        
        # Paso 0: Eliminar wakeword si está presente
        clean_text = remove_wakeword(text)
        if clean_text != text:
            logger.debug(f"Wakeword eliminado: '{text}' -> '{clean_text}'")
        
        # Paso 1: Predecir intención
        try:
            intent_result = predict(clean_text)
            logger.info(f"Predicho: {intent_result}")
        except PredictError as e:
            logger.error(f"Predicción fallida: {e}")
            print(f"Error de predicción: {e}")
            return False
        
        # Paso 2: Enrutar (decidir: ejecutar o pedir confirmación)
        try:
            self.router.route(intent_result)
            logger.info(f"Comando ejecutado: {intent_result.intent_id}")
            print(f"Executed: {intent_result.intent_id}")
            return True
            
        except UserConfirmationRequired as e:
            logger.warning(f"Confirmación necesaria: {e}")
            print(f"Advertencia: {e}")
            print(f"   ¿Ejecutar '{intent_result.intent_id}'? (y/n)")
            
            # Pedir confirmación al usuario
            response = input("   > ").strip().lower()
            if response in ('y', 'yes'):
                try:
                    self.executor.execute(intent_result.intent_id)
                    logger.info(f"Comando ejecutado tras confirmación: {intent_result.intent_id}")
                    print(f"Ejecutado: {intent_result.intent_id}")
                    return True
                except (CommandExecutionError, CommandNotAllowedError) as e:
                    logger.error(f"Ejecución fallida: {e}")
                    print(f"Error de ejecución: {e}")
                    return False
            else:
                logger.info("Usuario declinó la ejecución")
                print("Cancelado")
                return False
        
        except ConfidenceTooLowError as e:
            logger.warning(f"Confianza muy baja: {e}")
            print(f"Confianza muy baja: {intent_result.intent_id} ({intent_result.confidence:.1%})")
            return False
        
        except (CommandExecutionError, CommandNotAllowedError) as e:
            logger.error(f"Ejecución fallida: {e}")
            print(f"Error de ejecución: {e}")
            return False
    
    def run_interactive(self):
        """Ejecutar en modo interactivo (leer desde stdin)."""
        print("\n" + "="*60)
        print("Asistente Aurora - Modo Interactivo")
        print("="*60)
        print("Comandos disponibles: " + ", ".join(self.executor.list_commands()))
        print("Escribe el texto del comando (Ctrl+C para salir)\n")
        
        try:
            while True:
                text = input("You: ").strip()
                if text:
                    self.process_text(text)
                    print()
        except KeyboardInterrupt:
            print("\n\n¡Adiós!")
            return 0
    
    def run_single(self, text: str) -> int:
        """Ejecutar con una única entrada."""
        success = self.process_text(text)
        return 0 if success else 1
    
    def run_voice(self, continuous: bool = False, verify_speaker: bool = False) -> int:
        """
        Ejecutar en modo voz (captura desde micrófono).
        Args:
            continuous: Si True, escucha continuamente. Si False, solo una vez.
            verify_speaker: Si True, verifica que sea el hablante autorizado.
        """
        print("\n" + "="*60)
        print("Asistente Aurora - Modo Voz")
        print("="*60)
        print("Comandos disponibles: " + ", ".join(self.executor.list_commands()))
        
        try:
            # Inicializar captura y transcripción
            capture = get_capture()
            transcriber = get_transcriber(verify_speaker=verify_speaker)
            
            print(f"\nConfiguración:")
            print(f"  - Motor de reconocimiento: {transcriber.engine}")
            print(f"  - Idioma: {transcriber.language}")
            print(f"  - Verificación de hablante: {'Activada' if verify_speaker else 'Desactivada'}")
            print(f"  - Modo: {'Continuo' if continuous else 'Una vez'}")
            
            # Calibrar micrófono
            print("\nCalibrando micrófono...")
            capture.calibrate()
            print("Calibración completa\n")
            
            if continuous:
                print("Escuchando continuamente (Ctrl+C para salir)...")
                print("-"*60 + "\n")
            
            while True:
                try:
                    # Capturar audio
                    print("Escuchando... (di 'aurora' + tu comando)")
                    audio = capture.listen(timeout=5, phrase_time_limit=10)
                    
                    print("Transcribiendo...")
                    text = transcriber.transcribe(audio)
                    print(f"   Escuchado: '{text}'\n")
                    
                    # Procesar comando
                    self.process_text(text)
                    print()
                    
                    if not continuous:
                        break
                
                except UnauthorizedSpeakerError as e:
                    print(f"❌ {e}\n")
                    if not continuous:
                        return 1
                    # En modo continuo, continuar escuchando
                    continue
                    
                except TimeoutError:
                    if not continuous:
                        print("Timeout: No se detectó voz\n")
                        break
                    else:
                        # En modo continuo, simplemente reintentar
                        continue
                
                except TranscriptionError as e:
                    print(f"Error de transcripción: {e}\n")
                    if not continuous:
                        return 1
                    # En modo continuo, continuar escuchando
                    continue
            
            return 0
            
        except MicrophoneError as e:
            print(f"\nError de micrófono: {e}")
            print("\nConsejos:")
            print("  - Verifica que tu micrófono esté conectado")
            print("  - Revisa los permisos de audio")
            print("  - Lista micrófonos con: python -m src.audio.mic")
            return 1
        
        except KeyboardInterrupt:
            print("\n\nAdiós!")
            return 0
        
        except Exception as e:
            logger.error(f"Error en modo voz: {e}")
            print(f"\nError: {e}")
            return 1
    
    def run_speaker_training(self, n_samples: int = 5) -> int:
        """
        Ejecutar modo entrenamiento de verificación de hablante.
        
        Args:
            n_samples: Número de muestras de voz a capturar
        """
        print("\n" + "="*60)
        print("Asistente Aurora - Entrenamiento de Hablante")
        print("="*60)
        print(f"Vamos a capturar {n_samples} muestras de tu voz")
        print("Esto permitirá que Aurora reconozca solo tu voz\n")
        
        try:
            # Inicializar captura y verificador
            capture = get_capture()
            verifier = get_verifier()
            
            print(f"Estado actual del modelo:")
            print(f"  - Ya entrenado: {verifier.is_trained}")
            print(f"  - Muestras previas: {verifier.n_samples}")
            print(f"  - Umbral de confianza: {verifier.threshold}")
            
            if verifier.is_trained:
                print(f"\nYa existe un modelo entrenado con {verifier.n_samples} muestras")
                print("Las nuevas muestras se AÑADIRÁN al modelo existente\n")
            else:
                print("\nNo hay modelo previo. Creando nuevo modelo...\n")
            
            # Calibrar micrófono
            print("Calibrando micrófono...")
            capture.calibrate()
            print("Calibración completa\n")
            
            # Capturar muestras
            print("Instrucciones:")
            print("  - Habla claramente cuando se te indique")
            print("  - Di frases diferentes en cada muestra")
            print("  - Ejemplos: 'Aurora abre el navegador', 'Aurora cuál es el clima'\n")
            
            input("Presiona Enter cuando estés listo para comenzar...")
            print()
            
            successful_samples = 0
            for i in range(n_samples):
                try:
                    print(f"Muestra {i+1}/{n_samples}")
                    print("   Habla ahora (3-10 segundos)...")
                    
                    audio = capture.listen(timeout=5, phrase_time_limit=10)
                    
                    print("   Procesando muestra...")
                    verifier.train(audio)
                    
                    successful_samples += 1
                    print(f"   Muestra {i+1} registrada correctamente")
                    print(f"   Total de muestras en el modelo: {verifier.n_samples}\n")
                    
                except TimeoutError:
                    print(f"   Timeout - no se detectó voz")
                    print(f"   Reintentando muestra {i+1}...\n")
                    # No incrementar i, reintentar
                    continue
                
                except SpeakerVerificationError as e:
                    print(f"   Error al procesar muestra: {e}")
                    print(f"   Reintentando muestra {i+1}...\n")
                    continue
                
                except Exception as e:
                    print(f"   Error inesperado: {e}")
                    print(f"   Reintentando muestra {i+1}...\n")
                    continue
            
            print("\n" + "="*60)
            print("✅ ENTRENAMIENTO COMPLETADO")
            print("="*60)
            print(f"Muestras capturadas en esta sesión: {successful_samples}")
            print(f"Total de muestras en el modelo: {verifier.n_samples}")
            print(f"\nAhora puedes usar --single-voice para que Aurora")
            print(f"solo responda a tu voz\n")
            
            return 0
            
        except MicrophoneError as e:
            print(f"\nError de micrófono: {e}")
            print("\nConsejos:")
            print("  - Verifica que tu micrófono esté conectado")
            print("  - Revisa los permisos de audio")
            return 1
        
        except KeyboardInterrupt:
            print("\n\nEntrenamiento interrumpido")
            print(f"Muestras guardadas hasta ahora: {verifier.n_samples}")
            return 0
        
        except Exception as e:
            logger.error(f"Error en entrenamiento: {e}")
            print(f"\nError: {e}")
            return 1


def main():
    """Punto de entrada CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Aurora Assistant - Voice command executor"
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Command text to process (if not provided, runs in interactive mode)"
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Run in voice mode (listen from microphone)"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Continuous listening mode (use with --voice)"
    )
    parser.add_argument(
        "--single-voice",
        action="store_true",
        help="Enable speaker verification (only recognize trained voice)"
    )
    parser.add_argument(
        "--all-voices",
        action="store_true",
        help="Disable speaker verification (recognize any voice) [default]"
    )
    parser.add_argument(
        "--train-speaker",
        action="store_true",
        help="Enter speaker training mode (train voice recognition)"
    )
    parser.add_argument(
        "--training-samples",
        type=int,
        default=5,
        help="Number of voice samples to capture during training (default: 5)"
    )
    parser.add_argument(
        "--auto-threshold",
        type=float,
        default=0.75,
        help="Confidence threshold for automatic execution (default: 0.75)"
    )
    parser.add_argument(
        "--confirm-threshold",
        type=float,
        default=0.4,
        help="Confidence threshold for asking confirmation (default: 0.4)"
    )
    parser.add_argument(
        "--commands",
        help="Path to commands.json (default: commands/commands.json)"
    )
    
    args = parser.parse_args()
    
    # Validar argumentos
    if args.single_voice and args.all_voices:
        print("Error: No puedes usar --single-voice y --all-voices al mismo tiempo")
        return 1
    
    # Determinar si verificar hablante
    verify_speaker = args.single_voice  # Por defecto False (all-voices)
    
    try:
        # Modo entrenamiento de hablante
        if args.train_speaker:
            assistant = AuroraAssistant()  # No necesitamos configurar nada más
            return assistant.run_speaker_training(n_samples=args.training_samples)
        
        # Modos normales de operación
        assistant = AuroraAssistant(
            auto_execute_threshold=args.auto_threshold,
            confirmation_threshold=args.confirm_threshold,
            commands_path=args.commands,
        )
        
        if args.voice:
            # Modo voz
            return assistant.run_voice(
                continuous=args.continuous,
                verify_speaker=verify_speaker
            )
        elif args.text:
            # Modo entrada única
            return assistant.run_single(args.text)
        else:
            # Modo interactivo
            return assistant.run_interactive()
    
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        print(f"Error fatal: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
