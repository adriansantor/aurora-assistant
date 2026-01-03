"""
Estructuras de datos para inferencia NLP.
"""
from dataclasses import dataclass


@dataclass
class IntentResult:
    """
    Resultado de predicción de intención.
    
    Atributos:
        intent_id (str): El ID de la intención predicha (ej: "LOCK_SCREEN")
        confidence (float): Probabilidad del clasificador (0.0 a 1.0)
        text (str): El texto usado para inferencia (para logging/feedback)
    """
    intent_id: str
    confidence: float
    text: str

    def __repr__(self) -> str:
        return f"IntentResult(intent_id='{self.intent_id}', confidence={self.confidence:.2f}, text='{self.text}')"
