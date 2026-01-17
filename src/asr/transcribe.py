#!/usr/bin/env python3
"""Módulo de transcripción de audio a texto (ASR)."""
import logging
from pathlib import Path
from typing import Optional

import speech_recognition as sr
import yaml

from src.audio.speaker_verify import get_verifier, SpeakerVerificationError

logger = logging.getLogger(__name__)

_transcriber: Optional['SpeechTranscriber'] = None


class TranscriptionError(Exception):
    """Se lanza cuando falla la transcripción."""
    pass


class UnauthorizedSpeakerError(Exception):
    """Se lanza cuando el hablante no está autorizado."""
    pass


class SpeechTranscriber:
    """
    Transcribe audio a texto usando Google Speech Recognition.
    
    """
    
    def __init__(
        self,
        language: str = "es-ES",
        timeout: float = 10,
        phrase_time_limit: float = 10,
        config_path: Optional[str] = None,
        verify_speaker: bool = False
    ):
        """
        Inicializar transcriptor con Google Speech Recognition.
        
        Args:
            language: Codigo de idioma (ej: es-ES, en-US)
            timeout: Tiempo maximo de espera (segundos)
            phrase_time_limit: Duracion maxima de frase (segundos)
            config_path: Ruta al archivo YAML
            verify_speaker: Si True, verifica el hablante antes de transcribir
        """
        # Cargar configuración
        if config_path:
            self._load_config(Path(config_path))
        else:
            self.language = language
            self.timeout = timeout
            self.phrase_time_limit = phrase_time_limit
        
        self.recognizer = sr.Recognizer()
        self.engine = "google"
        self.verify_speaker = verify_speaker
        
        # Inicializar verificador de hablante si está habilitado
        if self.verify_speaker:
            try:
                self.speaker_verifier = get_verifier()
                logger.info("Verificación de hablante habilitada")
            except Exception as e:
                logger.warning(f"No se pudo inicializar verificador de hablante: {e}")
                self.speaker_verifier = None
                self.verify_speaker = False
        else:
            self.speaker_verifier = None
        
        logger.info(
            f"SpeechTranscriber inicializado: engine=google, "
            f"language={self.language}, verify_speaker={self.verify_speaker}"
        )
    
    def _load_config(self, config_path: Path):
        """Cargar configuracion desde el YAML."""
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
            
            sr_config = config.get('speech_recognition', {})
            self.language = sr_config.get('language', 'es-ES')
            self.timeout = sr_config.get('timeout', 10)
            self.phrase_time_limit = sr_config.get('phrase_time_limit', 10)
            
            logger.info(f"Configuracion de transcripcion cargada desde {config_path}")
        except FileNotFoundError:
            logger.warning(f"Archivo de configuracion no encontrado: {config_path}. Usando valores por defecto.")
            self.language = 'es-ES'
            self.timeout = 10
            self.phrase_time_limit = 10
        except yaml.YAMLError as e:
            logger.error(f"Error al parsear YAML: {e}. Usando valores por defecto.")
            self.language = 'es-ES'
            self.timeout = 10
            self.phrase_time_limit = 10
    
    def transcribe(self, audio: sr.AudioData, skip_verification: bool = False) -> str:
        """
        Transcribir audio a texto.
        
        Args:
            audio: Datos de audio a transcribir
            skip_verification: Si True, omite la verificación de hablante
            
        Returns:
            Texto transcrito
            
        Raises:
            TranscriptionError: Si la transcripcion falla
            UnauthorizedSpeakerError: Si el hablante no está autorizado
        """
        # Verificar hablante si está habilitado
        if self.verify_speaker and not skip_verification and self.speaker_verifier:
            try:
                is_authorized, confidence = self.speaker_verifier.verify(audio)
                
                if not is_authorized:
                    logger.warning(
                        f"Hablante no autorizado (confianza={confidence:.3f})"
                    )
                    raise UnauthorizedSpeakerError(
                        f"Hablante no autorizado. Confianza: {confidence:.3f}"
                    )
                
                logger.info(f"Hablante autorizado (confianza={confidence:.3f})")
                
            except SpeakerVerificationError as e:
                logger.error(f"Error en verificación de hablante: {e}")
                # Continuar sin verificación si hay error
                logger.warning("Continuando sin verificación de hablante")
        
        try:
            logger.info("Transcribiendo con Google Speech Recognition...")
            text = self.recognizer.recognize_google(audio, language=self.language)
            logger.info(f"Transcripcion exitosa: '{text}'")
            return text
            
        except sr.UnknownValueError:
            logger.warning("No se pudo entender el audio")
            raise TranscriptionError("No se pudo entender el audio")
        except sr.RequestError as e:
            logger.error(f"Error en el servicio de reconocimiento: {e}")
            raise TranscriptionError(f"Error del servicio: {e}")
        except Exception as e:
            logger.error(f"Error durante la transcripcion: {e}")
            raise TranscriptionError(f"Error de transcripcion: {e}")
    
    def transcribe_with_alternatives(self, audio: sr.AudioData) -> list:
        """
        Transcribir y obtener alternativas si estan disponibles.
        
        Args:
            audio: Datos de audio
            
        Returns:
            Lista de transcripciones alternativas (si Google las proporciona)
        """
        try:
            result = self.recognizer.recognize_google(
                audio,
                language=self.language,
                show_all=True
            )
            if isinstance(result, dict) and 'alternative' in result:
                return [alt['transcript'] for alt in result['alternative']]
            elif isinstance(result, dict) and 'result' in result:
                return [r['alternative'][0]['transcript'] for r in result['result'] if 'alternative' in r]
            else:
                return [result] if result else []
        except sr.UnknownValueError:
            logger.warning("No se pudo entender el audio")
            raise TranscriptionError("No se pudo entender el audio")
        except sr.RequestError as e:
            logger.error(f"Error en el servicio: {e}")
            raise TranscriptionError(f"Error del servicio: {e}")


def get_transcriber(config_path: Optional[str] = None, verify_speaker: bool = False) -> SpeechTranscriber:
    """
    Obtiene o crea el transcriptor por defecto.
    
    Args:
        config_path: Ruta al archivo de configuracion
        verify_speaker: Si True, habilita verificación de hablante
        
    Returns:
        Instancia de SpeechTranscriber
    """
    global _transcriber
    if _transcriber is None:
        if config_path is None:
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "audio.yaml"
        _transcriber = SpeechTranscriber(
            config_path=str(config_path),
            verify_speaker=verify_speaker
        )
    return _transcriber


def transcribe_audio(audio: sr.AudioData, config_path: Optional[str] = None) -> str:
    """
    Funcion de conveniencia para transcribir audio.
    
    Args:
        audio: Datos de audio
        config_path: Ruta al archivo de configuracion
        
    Returns:
        Texto transcrito
    """
    transcriber = get_transcriber(config_path)
    return transcriber.transcribe(audio)


if __name__ == "__main__":
    # CLI para pruebas
    import sys
    from src.audio.mic import get_capture
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("PRUEBA DE TRANSCRIPCION DE VOZ")
    print("="*60)
    
    try:
        # Inicializar
        capture = get_capture()
        transcriber = get_transcriber()
        
        print(f"\nConfiguracion:")
        print(f"  Engine: {transcriber.engine}")
        print(f"  Idioma: {transcriber.language}")
        
        # Calibrar microfono
        print("\nCalibrando microfono...")
        capture.calibrate()
        
        # Capturar audio
        print("\nHabla ahora...")
        audio = capture.listen(timeout=5, phrase_time_limit=10)
        
        print("Audio capturado, transcribiendo...")
        
        # Transcribir
        text = transcriber.transcribe(audio)
        
        print("\n" + "="*60)
        print(f"TEXTO TRANSCRITO: {text}")
        print("="*60)
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrumpido por el usuario")
        sys.exit(0)
