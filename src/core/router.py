#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Optional

from src.core.executor import (
    CommandExecutor,
    CommandNotAllowedError,
    CommandExecutionError,
)


class ConfidenceTooLowError(Exception):
    """Se lanza cuando la confianza del modelo está por debajo del umbral mínimo."""


class UserConfirmationRequired(Exception):
    """Se lanza cuando la ejecución requiere confirmación explícita del usuario."""


@dataclass(frozen=True)
class IntentResult:
    intent_id: str
    confidence: float
    text: str


class CommandRouter:
    def __init__(
        self,
        executor: CommandExecutor,
        auto_execute_threshold: float = 0.75,
        confirmation_threshold: float = 0.4,
    ):
        if not (0.0 <= confirmation_threshold <= auto_execute_threshold <= 1.0):
            raise ValueError("Umbrales de confianza inválidos")

        self.executor = executor
        self.auto_execute_threshold = auto_execute_threshold
        self.confirmation_threshold = confirmation_threshold

    def route(self, intent: IntentResult) -> None:
        """
        Decide si ejecutar un comando basándose en la confianza.

        Política:
        - confianza >= auto_execute_threshold → ejecutar
        - confirmation_threshold <= confianza < auto_execute_threshold → requiere confirmación
        - confianza < confirmation_threshold → rechazar
        """
        if intent.confidence < self.confirmation_threshold:
            raise ConfidenceTooLowError(
                f"Confianza {intent.confidence:.2f} muy baja para intención '{intent.intent_id}'"
            )

        if intent.confidence < self.auto_execute_threshold:
            raise UserConfirmationRequired(
                f"Se requiere confirmación para intención '{intent.intent_id}' "
                f"(confianza={intent.confidence:.2f})"
            )

        # Alta confianza: intentar ejecución
        try:
            self.executor.execute(intent.intent_id)
        except (CommandNotAllowedError, CommandExecutionError):
            # Dejar que el llamador maneje el logging / feedback al usuario
            raise
