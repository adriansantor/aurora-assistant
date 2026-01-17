#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path
from typing import Dict


class CommandExecutionError(Exception):
    """Se lanza cuando un comando falla al ejecutarse correctamente."""


class CommandNotAllowedError(Exception):
    """Se lanza cuando un ID de comando no está presente en commands.json."""


class CommandExecutor:
    def __init__(self, commands_json_path: Path):
        if not commands_json_path.exists():
            raise FileNotFoundError(f"{commands_json_path} no encontrado")

        with commands_json_path.open("r", encoding="utf-8") as f:
            self.commands: Dict[str, Dict[str, str]] = json.load(f)

        if not isinstance(self.commands, dict) or not self.commands:
            raise ValueError("commands.json está vacío o malformado")

    def list_commands(self) -> list[str]:
        return sorted(self.commands.keys())

    def execute(self, command_id: str) -> None:
        """
        Ejecuta un comando por ID.

        - Solo se permiten comandos presentes en commands.json
        - Usa subprocess sin shell=True
        - Lanza excepciones explícitas en caso de fallo
        """
        if command_id not in self.commands:
            raise CommandNotAllowedError(
                f"Comando '{command_id}' no está permitido"
            )

        command_entry = self.commands[command_id]

        if "cmd" not in command_entry:
            raise ValueError(f"El comando '{command_id}' no tiene campo 'cmd'")

        cmd_str = command_entry["cmd"]

        # Dividir comando de forma segura (sin shell)
        cmd_parts = cmd_str.split()

        try:
            completed = subprocess.run(
                cmd_parts,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise CommandExecutionError(
                f"Comando '{command_id}' falló: {e.stderr.strip()}"
            ) from e
        except FileNotFoundError as e:
            raise CommandExecutionError(
                f"Ejecutable no encontrado para comando '{command_id}'"
            ) from e

        return completed
