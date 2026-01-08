#!/usr/bin/env python3
"""Módulo de captura de audio desde el micrófono."""
import logging
from pathlib import Path
from typing import Optional

import speech_recognition as sr
import yaml

logger = logging.getLogger(__name__)


class MicrophoneError(Exception):
    """Se lanza cuando hay problemas con el micrófono."""
    pass


class AudioCapture:
    """
    Captura audio desde el micrófono para procesamiento de voz.

    """
    
    def __init__(
        self,
        device_index: Optional[int] = None,
        pause_threshold: float = 1.0,
        energy_threshold: Optional[int] = None,
        dynamic_energy_threshold: bool = True,
        calibration_duration: float = 1.0,
        config_path: Optional[str] = None
    ):
        """
        Inicializar capturador de audio.
        
        Args:
            device_index: Índice del dispositivo de micrófono (-1 = predeterminado)
            pause_threshold: Duración del silencio para terminar captura (segundos)
            energy_threshold: Umbral de energía para detectar voz (None = auto)
            dynamic_energy_threshold: Ajuste automático del umbral
            calibration_duration: Duración de calibración (segundos)
            config_path: Ruta al archivo de configuración YAML
        """
        # Cargar configuración
        if config_path:
            self._load_config(Path(config_path))
        else:
            self.device_index = None if device_index == -1 else device_index
            self.pause_threshold = pause_threshold
            self.energy_threshold = energy_threshold
            self.dynamic_energy_threshold = dynamic_energy_threshold
            self.calibration_duration = calibration_duration
        
        # Inicializar reconocedor
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = self.pause_threshold
        self.recognizer.dynamic_energy_threshold = self.dynamic_energy_threshold
        
        if self.energy_threshold is not None:
            self.recognizer.energy_threshold = self.energy_threshold
        
        logger.info(
            f"AudioCapture inicializado: device_index={self.device_index}, "
            f"pause_threshold={self.pause_threshold}s"
        )
    
    def _load_config(self, config_path: Path):
        """Cargar configuración desde el YAML."""
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
            
            mic_config = config.get('microphone', {})
            self.device_index = mic_config.get('device_index', -1)
            if self.device_index == -1:
                self.device_index = None
            
            self.pause_threshold = mic_config.get('pause_threshold', 1.0)
            self.energy_threshold = mic_config.get('energy_threshold')
            self.dynamic_energy_threshold = mic_config.get('dynamic_energy_threshold', True)
            self.calibration_duration = mic_config.get('calibration_duration', 1.0)
            
            logger.info(f"Configuración de audio cargada desde {config_path}")
        except FileNotFoundError:
            logger.warning(f"Archivo de configuración no encontrado: {config_path}. Usando valores por defecto.")
            self.device_index = None
            self.pause_threshold = 1.0
            self.energy_threshold = None
            self.dynamic_energy_threshold = True
            self.calibration_duration = 1.0
        except yaml.YAMLError as e:
            logger.error(f"Error al parsear YAML: {e}. Usando valores por defecto.")
            self.device_index = None
            self.pause_threshold = 1.0
            self.energy_threshold = None
            self.dynamic_energy_threshold = True
            self.calibration_duration = 1.0
    
    def list_microphones(self) -> list[tuple[int, str]]:
        """
        Lista todos los micrófonos disponibles.
        
        Returns:
            Lista de tuplas (índice, nombre)
        """
        try:
            mics = []
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                mics.append((index, name))
            return mics
        except Exception as e:
            logger.error(f"Error al listar micrófonos: {e}")
            raise MicrophoneError(f"No se pudieron listar micrófonos: {e}")
    
    def calibrate(self, duration: Optional[float] = None) -> None:
        """
        Calibrar el umbral de energía basándose en el ruido ambiente.
        
        Args:
            duration: Duración de la calibración en segundos
        """
        if duration is None:
            duration = self.calibration_duration
        
        try:
            with sr.Microphone(device_index=self.device_index) as source:
                logger.info(f"Calibrando micrófono por {duration}s... (manténgase en silencio)")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                logger.info(f"Calibración completa. Umbral de energía: {self.recognizer.energy_threshold}")
        except OSError as e:
            logger.error(f"Error al acceder al micrófono: {e}")
            raise MicrophoneError(f"No se pudo acceder al micrófono: {e}")
        except Exception as e:
            logger.error(f"Error durante calibración: {e}")
            raise MicrophoneError(f"Error en calibración: {e}")
    
    def listen(
        self,
        timeout: Optional[float] = None,
        phrase_time_limit: Optional[float] = None,
        auto_calibrate: bool = False
    ) -> sr.AudioData:
        """
        Escuchar y capturar audio desde el micrófono.
        
        Args:
            timeout: Tiempo máximo de espera para inicio de voz (segundos)
            phrase_time_limit: Duración máxima de la frase (segundos)
            auto_calibrate: Si calibrar automáticamente antes de escuchar
            
        Returns:
            AudioData capturado
            
        Raises:
            MicrophoneError: Si hay problemas con el micrófono
            TimeoutError: Si no se detecta voz en el tiempo límite
        """
        try:
            with sr.Microphone(device_index=self.device_index) as source:
                # Calibración automática si se solicita
                if auto_calibrate:
                    logger.info("Calibrando ruido ambiente...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=self.calibration_duration)
                    logger.info(f"Calibración completa. Umbral: {self.recognizer.energy_threshold}")
                
                logger.info("Escuchando... (habla ahora)")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                logger.info("Audio capturado correctamente")
                return audio
                
        except sr.WaitTimeoutError:
            logger.warning("Timeout: no se detectó voz")
            raise TimeoutError("No se detectó voz en el tiempo límite")
        except OSError as e:
            logger.error(f"Error al acceder al micrófono: {e}")
            raise MicrophoneError(f"No se pudo acceder al micrófono: {e}")
        except Exception as e:
            logger.error(f"Error durante captura de audio: {e}")
            raise MicrophoneError(f"Error capturando audio: {e}")
    
    def listen_with_retry(
        self,
        max_retries: int = 3,
        timeout: Optional[float] = None,
        phrase_time_limit: Optional[float] = None,
        auto_calibrate: bool = False
    ) -> Optional[sr.AudioData]:
        """
        Escuchar con reintentos automáticos en caso de timeout.
        
        Args:
            max_retries: Número máximo de reintentos
            timeout: Tiempo máximo de espera para inicio de voz
            phrase_time_limit: Duración máxima de la frase
            auto_calibrate: Si calibrar automáticamente antes de escuchar
            
        Returns:
            AudioData capturado o None si se agotaron los reintentos
        """
        for attempt in range(1, max_retries + 1):
            try:
                return self.listen(
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                    auto_calibrate=(auto_calibrate and attempt == 1)
                )
            except TimeoutError:
                if attempt < max_retries:
                    logger.info(f"Reintento {attempt}/{max_retries}...")
                    continue
                else:
                    logger.warning("Se agotaron los reintentos")
                    return None
            except MicrophoneError:
                raise


# Instancia singleton
_capture: Optional[AudioCapture] = None


def get_capture(config_path: Optional[str] = None) -> AudioCapture:
    """
    Obtiene o crea el capturador de audio por defecto.
    
    Args:
        config_path: Ruta al archivo de configuración
        
    Returns:
        Instancia de AudioCapture
    """
    global _capture
    if _capture is None:
        if config_path is None:
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "audio.yaml"
        _capture = AudioCapture(config_path=str(config_path))
    return _capture


if __name__ == "__main__":
    # CLI PARA TESTING
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    capture = get_capture()
    
    # Listar micrófonos
    print("\n" + "="*60)
    print("MICRÓFONOS DISPONIBLES")
    print("="*60)
    try:
        mics = capture.list_microphones()
        for idx, name in mics:
            marker = " [DEFAULT]" if idx == capture.device_index else ""
            print(f"{idx}: {name}{marker}")
    except MicrophoneError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("PRUEBA DE CAPTURA DE AUDIO")
    print("="*60)
    
    try:
        # Calibrar
        print("\nCalibración del micrófono...")
        capture.calibrate()
        
        # Capturar audio
        print("\nHabla ahora...")
        audio = capture.listen(timeout=5, phrase_time_limit=10)
        
        print(f"Audio capturado: {len(audio.frame_data)} bytes")
        print(f"  Sample rate: {audio.sample_rate} Hz")
        print(f"  Sample width: {audio.sample_width} bytes")
        
    except (MicrophoneError, TimeoutError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrumpido por el usuario")
        sys.exit(0)
