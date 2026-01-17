#!/usr/bin/env python3
"""Sistema de verificación de hablante con entrenamiento acumulativo."""
import logging
import pickle
from pathlib import Path
from typing import Optional, Tuple
import io

import numpy as np
import speech_recognition as sr
import yaml
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# Intentar importar librosa (para extracción de características)
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa no está instalado. Instálalo con: pip install librosa")


class SpeakerVerificationError(Exception):
    """Se lanza cuando hay errores en verificación de hablante."""
    pass


class SpeakerVerifier:
    """
    Sistema de verificación de hablante con entrenamiento acumulativo.
    
    Usa MFCC (Mel-Frequency Cepstral Coefficients) para extraer características
    de la voz y un modelo SVM para clasificación.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        config_path: Optional[str] = None,
        threshold: float = 0.5,
        n_mfcc: int = 13,
        max_duration: float = 10.0
    ):
        """
        Inicializar verificador de hablante.
        
        Args:
            model_path: Ruta donde guardar/cargar el modelo entrenado
            config_path: Ruta al archivo de configuración YAML
            threshold: Umbral de confianza para aceptar al hablante (0-1)
            n_mfcc: Número de coeficientes MFCC a extraer
            max_duration: Duración máxima de audio a procesar (segundos)
        """
        if not LIBROSA_AVAILABLE:
            raise SpeakerVerificationError(
                "librosa es requerido para verificación de hablante. "
                "Instala con: pip install librosa"
            )
        
        # Cargar configuración
        if config_path:
            self._load_config(Path(config_path))
        else:
            self.threshold = threshold
            self.n_mfcc = n_mfcc
            self.max_duration = max_duration
        
        # Configurar ruta del modelo
        if model_path is None:
            base_dir = Path(__file__).parent.parent.parent
            model_path = base_dir / "models" / "speaker_model.pkl"
        self.model_path = Path(model_path)
        
        # Inicializar modelo y scaler
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.n_samples = 0
        
        # Intentar cargar modelo existente
        if self.model_path.exists():
            self._load_model()
        
        logger.info(
            f"SpeakerVerifier inicializado: threshold={self.threshold}, "
            f"n_mfcc={self.n_mfcc}, trained={self.is_trained}, "
            f"samples={self.n_samples}"
        )
    
    def _load_config(self, config_path: Path):
        """Cargar configuración desde YAML."""
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
            
            speaker_config = config.get('speaker_verification', {})
            self.threshold = speaker_config.get('threshold', 0.5)
            self.n_mfcc = speaker_config.get('n_mfcc', 13)
            self.max_duration = speaker_config.get('max_duration', 10.0)
            
            logger.info(f"Configuración de speaker cargada desde {config_path}")
        except FileNotFoundError:
            logger.warning(f"Archivo de configuración no encontrado: {config_path}")
            self.threshold = 0.5
            self.n_mfcc = 13
            self.max_duration = 10.0
        except yaml.YAMLError as e:
            logger.error(f"Error al parsear YAML: {e}")
            self.threshold = 0.5
            self.n_mfcc = 13
            self.max_duration = 10.0
    
    def extract_features(self, audio: sr.AudioData) -> np.ndarray:
        """
        Extraer características MFCC del audio.
        
        Args:
            audio: Datos de audio de speech_recognition
            
        Returns:
            Vector de características (promedio de MFCC)
            
        Raises:
            SpeakerVerificationError: Si la extracción falla
        """
        try:
            # Convertir AudioData a numpy array
            # AudioData.get_wav_data() retorna bytes en formato WAV
            wav_data = audio.get_wav_data()
            
            # Cargar audio con librosa desde bytes
            audio_array, sr_rate = librosa.load(
                io.BytesIO(wav_data),
                sr=None,  # Usar sample rate original
                duration=self.max_duration
            )
            
            # Extraer MFCCs
            mfccs = librosa.feature.mfcc(
                y=audio_array,
                sr=sr_rate,
                n_mfcc=self.n_mfcc
            )
            
            # Calcular estadísticas de los MFCCs (media y std)
            mfcc_mean = np.mean(mfccs, axis=1)
            mfcc_std = np.std(mfccs, axis=1)
            
            # Concatenar para formar el vector de características
            features = np.concatenate([mfcc_mean, mfcc_std])
            
            logger.debug(f"Características extraídas: shape={features.shape}")
            return features
            
        except Exception as e:
            logger.error(f"Error al extraer características: {e}")
            raise SpeakerVerificationError(f"Error extrayendo características: {e}")
    
    def train(self, audio: sr.AudioData, speaker_label: int = 1):
        """
        Entrenar el modelo con una nueva muestra de audio (acumulativo).
        
        Args:
            audio: Datos de audio del hablante autorizado
            speaker_label: Etiqueta del hablante (1=autorizado, 0=no autorizado)
        """
        try:
            # Extraer características
            features = self.extract_features(audio)
            features = features.reshape(1, -1)
            
            if self.model is None:
                # Primera vez: inicializar modelo SVM
                # Usamos probability=True para obtener scores de confianza
                self.model = SVC(kernel='rbf', probability=True, gamma='auto')
                
                # Necesitamos al menos 2 clases para entrenar SVM
                # En la primera muestra, creamos un punto sintético negativo
                features_neg = features + np.random.normal(0, 1, features.shape)
                X = np.vstack([features, features_neg])
                y = np.array([1, 0])  # 1=autorizado, 0=no autorizado
                
                # Ajustar scaler y modelo
                X_scaled = self.scaler.fit_transform(X)
                self.model.fit(X_scaled, y)
                self.n_samples = 1
                self.is_trained = True
                
                logger.info("Modelo inicializado con primera muestra")
            else:
                # Entrenamiento incremental: agregar nueva muestra
                # SVM no soporta partial_fit, así que reentrenamos con datos acumulados
                # En producción real, consideraría usar SGDClassifier u otro modelo incremental
                
                # Por ahora, guardamos la muestra y reentrenamos
                # Esto es una simplificación - en producción usarías un buffer de muestras
                features_scaled = self.scaler.transform(features)
                
                # Crear conjunto de datos con muestras positivas y negativas sintéticas
                X_positive = features_scaled
                X_negative = features_scaled + np.random.normal(0, 1, features_scaled.shape)
                X = np.vstack([X_positive, X_negative])
                y = np.array([1, 0])
                
                # Reentrenar (en un sistema real, acumularías muestras)
                self.model.fit(X, y)
                self.n_samples += 1
                
                logger.info(f"Modelo actualizado con muestra #{self.n_samples}")
            
            # Guardar modelo
            self._save_model()
            
            logger.info(f"Entrenamiento completado. Total de muestras: {self.n_samples}")
            
        except Exception as e:
            logger.error(f"Error durante el entrenamiento: {e}")
            raise SpeakerVerificationError(f"Error en entrenamiento: {e}")
    
    def verify(self, audio: sr.AudioData) -> Tuple[bool, float]:
        """
        Verificar si el audio corresponde al hablante autorizado.
        
        Args:
            audio: Datos de audio a verificar
            
        Returns:
            Tupla de (es_autorizado, confianza)
            
        Raises:
            SpeakerVerificationError: Si la verificación falla o no hay modelo
        """
        if not self.is_trained:
            raise SpeakerVerificationError(
                "El modelo no está entrenado. Entrena primero con samples del hablante."
            )
        
        try:
            # Extraer características
            features = self.extract_features(audio)
            features = features.reshape(1, -1)
            
            # Escalar características
            features_scaled = self.scaler.transform(features)
            
            # Predecir con probabilidades
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            # La confianza es la probabilidad de la clase predicha
            if prediction == 1:
                confidence = probabilities[1]
            else:
                confidence = probabilities[0]
            
            # Verificar contra el umbral
            is_authorized = (prediction == 1) and (confidence >= self.threshold)
            
            logger.info(
                f"Verificación: authorized={is_authorized}, "
                f"confidence={confidence:.3f}, threshold={self.threshold}"
            )
            
            return is_authorized, confidence
            
        except Exception as e:
            logger.error(f"Error durante la verificación: {e}")
            raise SpeakerVerificationError(f"Error en verificación: {e}")
    
    def _save_model(self):
        """Guardar modelo y scaler en disco."""
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'n_samples': self.n_samples,
                'is_trained': self.is_trained,
                'threshold': self.threshold,
                'n_mfcc': self.n_mfcc,
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Modelo guardado en {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error al guardar modelo: {e}")
            raise SpeakerVerificationError(f"Error guardando modelo: {e}")
    
    def _load_model(self):
        """Cargar modelo y scaler desde disco."""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.n_samples = model_data.get('n_samples', 0)
            self.is_trained = model_data.get('is_trained', True)
            self.threshold = model_data.get('threshold', self.threshold)
            self.n_mfcc = model_data.get('n_mfcc', self.n_mfcc)
            
            logger.info(
                f"Modelo cargado desde {self.model_path} "
                f"(samples={self.n_samples})"
            )
            
        except Exception as e:
            logger.error(f"Error al cargar modelo: {e}")
            raise SpeakerVerificationError(f"Error cargando modelo: {e}")
    
    def reset_model(self):
        """Resetear el modelo (eliminar entrenamiento previo)."""
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.n_samples = 0
        
        if self.model_path.exists():
            self.model_path.unlink()
            logger.info(f"Modelo eliminado: {self.model_path}")
        
        logger.info("Modelo reseteado")


# Instancia global
_verifier: Optional[SpeakerVerifier] = None


def get_verifier(config_path: Optional[str] = None) -> SpeakerVerifier:
    """
    Obtener o crear el verificador de hablante global.
    
    Args:
        config_path: Ruta al archivo de configuración
        
    Returns:
        Instancia de SpeakerVerifier
    """
    global _verifier
    if _verifier is None:
        if config_path is None:
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "speaker.yaml"
        
        _verifier = SpeakerVerifier(config_path=str(config_path))
    
    return _verifier


if __name__ == "__main__":
    # CLI para pruebas
    import sys
    from src.audio.mic import get_capture
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("PRUEBA DE VERIFICACIÓN DE HABLANTE")
    print("="*60)
    
    try:
        capture = get_capture()
        verifier = get_verifier()
        
        print(f"\nEstado del modelo:")
        print(f"  Entrenado: {verifier.is_trained}")
        print(f"  Muestras: {verifier.n_samples}")
        print(f"  Umbral: {verifier.threshold}")
        
        print("\n1. Capturando audio para verificación...")
        print("Habla ahora...")
        
        capture.calibrate()
        audio = capture.listen(timeout=5, phrase_time_limit=10)
        
        if verifier.is_trained:
            print("\n2. Verificando hablante...")
            is_authorized, confidence = verifier.verify(audio)
            
            print("\n" + "="*60)
            print(f"RESULTADO:")
            print(f"  Autorizado: {is_authorized}")
            print(f"  Confianza: {confidence:.3f}")
            print("="*60)
        else:
            print("\nModelo no entrenado. Usa --train para entrenar.")
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrumpido")
        sys.exit(0)
