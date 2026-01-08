#!/usr/bin/env python3

import json
import sys
import shlex
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
COMMANDS_TXT = BASE_DIR / "commands.txt"
COMMANDS_JSON = BASE_DIR / "commands.json"

FORBIDDEN_TOKENS = {
    ";", "&&", "||", "|", "`", "$(", ">", "<"
}


def is_safe_command(cmd: str) -> bool:
    """
    Verificación de seguridad BÁSICA
    """
    for token in FORBIDDEN_TOKENS:
        if token in cmd:
            return False
    return True


def parse_commands_file(path: Path) -> dict:
    commands = {}

    with path.open("r", encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                raise ValueError(f"Línea {lineno}: falta '='")

            key, value = map(str.strip, line.split("=", 1))

            if not key.isidentifier():
                raise ValueError(f"Línea {lineno}: ID de comando inválido '{key}'")

            if key in commands:
                raise ValueError(f"Línea {lineno}: ID de comando duplicado '{key}'")

            if not value:
                raise ValueError(f"Línea {lineno}: comando vacío para '{key}'")

            if not is_safe_command(value):
                raise ValueError(
                    f"Línea {lineno}: token shell prohibido en comando '{value}'"
                )

            # Validar que el comando sea parseable por el shell
            try:
                shlex.split(value)
            except ValueError as e:
                raise ValueError(
                    f"Línea {lineno}: error de parsing shell: {e}"
                )

            commands[key] = {
                "cmd": value,
                "danger": "unknown"
            }

    if not commands:
        raise ValueError("No se encontraron comandos válidos en commands.txt")

    return commands


def main():
    if not COMMANDS_TXT.exists():
        print("commands.txt no encontrado", file=sys.stderr)
        sys.exit(1)

    try:
        commands = parse_commands_file(COMMANDS_TXT)
    except ValueError as e:
        print(f"Error de validación: {e}", file=sys.stderr)
        sys.exit(2)

    with COMMANDS_JSON.open("w", encoding="utf-8") as f:
        json.dump(commands, f, indent=2, ensure_ascii=False)

    print(f"✔ Generado {COMMANDS_JSON.name} con {len(commands)} comandos")


if __name__ == "__main__":
    main()
