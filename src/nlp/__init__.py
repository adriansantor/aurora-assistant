"""
Módulo NLP para el Asistente Aurora.

Exportaciones principales:
- predict(): Interfaz simple para predicción de intención
- IntentPredictor: Clase completa del predictor
- IntentResult: Dataclass de resultado
- PredictError: Excepción para errores de predicción
"""

from .intent_model import IntentResult
from .predict import IntentPredictor, PredictError, predict, get_predictor

__all__ = [
    "predict",
    "get_predictor",
    "IntentPredictor",
    "IntentResult",
    "PredictError",
]
