#!/usr/bin/env python3
"""Aurora Assistant - Orquestador principal que integra predicción, enrutamiento y ejecución."""
import logging
import sys
from pathlib import Path

from src.nlp.predict import predict, PredictError
from src.core.executor import CommandExecutor, CommandExecutionError, CommandNotAllowedError
from src.core.router import CommandRouter, UserConfirmationRequired, ConfidenceTooLowError

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
        
        # Paso 1: Predecir intención
        try:
            intent_result = predict(text)
            logger.info(f"Predicho: {intent_result}")
        except PredictError as e:
            logger.error(f"Predicción fallida: {e}")
            print(f"Error de predicción: {e}")
            return False
        
        # Paso 2: Enrutar (decidir: ejecutar o pedir confirmación)
        try:
            self.router.route(intent_result)
            logger.info(f"✓ Comando ejecutado: {intent_result.intent_id}")
            print(f"✓ Executed: {intent_result.intent_id}")
            return True
            
        except UserConfirmationRequired as e:
            logger.warning(f"Confirmación necesaria: {e}")
            print(f"⚠ {e}")
            print(f"   ¿Ejecutar '{intent_result.intent_id}'? (y/n)")
            
            # Pedir confirmación al usuario
            response = input("   > ").strip().lower()
            if response in ('y', 'yes'):
                try:
                    self.executor.execute(intent_result.intent_id)
                    logger.info(f"✓ Comando ejecutado tras confirmación: {intent_result.intent_id}")
                    print(f"✓ Ejecutado: {intent_result.intent_id}")
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
    
    try:
        assistant = AuroraAssistant(
            auto_execute_threshold=args.auto_threshold,
            confirmation_threshold=args.confirm_threshold,
            commands_path=args.commands,
        )
        
        if args.text:
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
