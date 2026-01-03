"""Módulo de predicción de intenciones. Convierte texto a predicciones estructuradas de intención."""
import json
import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .intent_model import IntentResult

logger = logging.getLogger(__name__)


class PredictError(Exception):
    """Se lanza cuando la predicción no puede realizarse."""
    pass


class IntentPredictor:
    """
    Motor mínimo de predicción de intenciones.
    
    Carga modelo preentrenado, vectorizador y mapa de etiquetas.
    Predice intención desde texto sin modificación.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        vectorizer_path: Optional[str] = None,
        label_map_path: Optional[str] = None,
        commands_path: Optional[str] = None,
    ):
        """Inicializar predictor cargando artefactos. Lanza PredictError si falta algún artefacto."""
        # Resolver rutas
        base_dir = Path(__file__).parent.parent.parent  # raíz del proyecto
        
        self.model_path = Path(model_path or base_dir / "models" / "intent_model.pkl")
        self.vectorizer_path = Path(vectorizer_path or base_dir / "models" / "vectorizer.pkl")
        self.label_map_path = Path(label_map_path or base_dir / "data" / "processed" / "label_map.json")
        self.commands_path = Path(commands_path or base_dir / "commands" / "commands.json")
        
        # Cargar artefactos
        self.model = self._load_artifact(self.model_path, "model")
        self.vectorizer = self._load_artifact(self.vectorizer_path, "vectorizer")
        self.label_map = self._load_label_map()
        self.valid_intents = self._load_valid_intents()
        
        # Validar capacidades del modelo
        self._validate_model()

    def _load_artifact(self, path: Path, name: str):
        """Cargar un artefacto serializado."""
        try:
            return joblib.load(path)
        except FileNotFoundError:
            raise PredictError(f"{name} no encontrado en {path}")
        except Exception as e:
            raise PredictError(f"Fallo al cargar {name} desde {path}: {e}")

    def _load_label_map(self) -> dict:
        """Cargar mapeo de etiqueta a intent_id."""
        try:
            with open(self.label_map_path) as f:
                return json.load(f)
        except FileNotFoundError:
            raise PredictError(f"label_map.json no encontrado en {self.label_map_path}")
        except json.JSONDecodeError:
            raise PredictError(f"label_map.json es JSON inválido")

    def _load_valid_intents(self) -> set:
        """Cargar IDs de intenciones válidas desde commands.json."""
        try:
            with open(self.commands_path) as f:
                commands = json.load(f)
                return set(commands.keys())
        except FileNotFoundError:
            raise PredictError(f"commands.json no encontrado en {self.commands_path}")
        except json.JSONDecodeError:
            raise PredictError(f"commands.json es JSON inválido")

    def _validate_model(self):
        """Asegurar que el modelo soporta predict_proba."""
        if not hasattr(self.model, "predict_proba"):
            raise PredictError(
                f"El modelo {self.model_path} no soporta predict_proba. "
                "Usa LogisticRegression, RandomForest, o similar."
            )

    def _normalize_text(self, text: str) -> str:
        """
        Normalización mínima de texto.
        Debe coincidir con la normalización usada durante el entrenamiento.
        
        Actualmente:
        - eliminar espacios en blanco
        - minúsculas
        """
        return text.strip().lower()

    def predict(self, text: str) -> IntentResult:
        """Predice la intención a partir del texto. Lanza PredictError si falla la predicción."""
        if not isinstance(text, str):
            raise PredictError(f"text debe ser str, se recibió {type(text)}")
        
        if not text.strip():
            raise PredictError("text no puede estar vacío")
        
        # Normalizar texto
        normalized_text = self._normalize_text(text)
        
        # Vectorizar (nunca fit_transform)
        try:
            X = self.vectorizer.transform([normalized_text])
        except Exception as e:
            raise PredictError(f"Vectorización fallida: {e}")
        
        # Obtener probabilidades
        try:
            probabilities = self.model.predict_proba(X)[0]
        except Exception as e:
            raise PredictError(f"Predicción del modelo fallida: {e}")
        
        # Obtener índice de la clase predicha
        predicted_class_idx = np.argmax(probabilities)
        confidence = float(probabilities[predicted_class_idx])
        
        # Mapear índice a intent_id
        try:
            intent_id = self.label_map[str(predicted_class_idx)]
        except KeyError:
            raise PredictError(f"Índice de clase {predicted_class_idx} no está en label_map")
        
        # Validar que la intención existe en commands
        if intent_id not in self.valid_intents:
            raise PredictError(
                f"Intención predicha '{intent_id}' no encontrada en commands.json"
            )
        
        return IntentResult(
            intent_id=intent_id,
            confidence=confidence,
            text=text,  # Texto original para logging/feedback
        )


# Instancia singleton por conveniencia
_predictor: Optional[IntentPredictor] = None


def get_predictor() -> IntentPredictor:
    """Obtiene o crea el predictor por defecto."""
    global _predictor
    if _predictor is None:
        _predictor = IntentPredictor()
    return _predictor


def predict(text: str) -> IntentResult:
    """Función de conveniencia para predecir intención. Usa el predictor por defecto."""
    return get_predictor().predict(text)


if __name__ == "__main__":
    # CLI simple para pruebas
    import sys
    
    try:
        predictor = IntentPredictor()
        
        if len(sys.argv) > 1:
            # Predecir desde argumento de línea de comandos
            text = " ".join(sys.argv[1:])
            result = predictor.predict(text)
            print(result)
        else:
            # Modo interactivo
            print("Predictor de Intenciones (Ctrl+C para salir)")
            while True:
                text = input("> ").strip()
                if text:
                    try:
                        result = predictor.predict(text)
                        print(f"  {result}\n")
                    except PredictError as e:
                        print(f"  Error: {e}\n")
    except PredictError as e:
        print(f"Error fatal: {e}", file=sys.stderr)
        sys.exit(1)
