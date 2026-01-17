(Gracias copilot por la documentación, descripciones, y algún que otro manejo de errores 😛)

# Aurora Assistant

Asistente inteligente que detecta intenciones del usuario y ejecuta comandos del sistema de forma segura.

## ⚡ Quick Start

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Entrenar modelo
python -m src.nlp.train

# 3. Ejecutar asistente
python -m src.main "abre firefox"
```

## 📚 Documentación

- **[GUIDE.md](GUIDE.md)** - Guía completa (arquitectura, funcionamiento, instalación)
- **[ADDING_COMMANDS.md](ADDING_COMMANDS.md)** - Cómo agregar comandos nuevos (workflow paso a paso)
- **[SCRIPTS.md](SCRIPTS.md)** - Referencia de scripts (qué hace cada uno)
- **[WAKEWORD.md](WAKEWORD.md)** - Sistema de palabra de activación "aurora"
- **[VOICE.md](VOICE.md)** - Sistema de reconocimiento de voz (micrófono → texto)
- **[SPEAKER_VERIFICATION.md](SPEAKER_VERIFICATION.md)** - 🆕 Sistema de reconocimiento de hablante (solo tu voz)

## 🏗️ Arquitectura

```
VOZ: Micrófono → ASR → [Speaker Verify] → Texto → [Wakeword] → predict.py → router.py → executor.py
                        ↓                   ↓         ↓         ↓            ↓            ↓
                   Verifica             Transcribe  Elimina    Intent +    Decisión    Ejecución
                   hablante                         "aurora"   Confianza   (0.40-0.75)   Segura
                   (opcional)
```

## 🎯 Componentes Principales

```
src/
├── main.py              ← Orquestador principal
├── nlp/
│   ├── predict.py       ← Predicción ML (inference)
│   ├── train.py         ← Entrenamiento del modelo
│   └── intent_model.py  ← Estructuras de datos
└── core/
    ├── router.py        ← Decisiones basadas en confianza
    └── executor.py      ← Ejecución segura de comandos
```

## 🚀 Uso

```bash
# Comando único
python -m src.main "abre firefox"

# Con wakeword (se elimina automáticamente)
python -m src.main "aurora abre firefox"  # Procesa: "abre firefox"

# Modo interactivo
python -m src.main

# Modo voz (desde micrófono)
python -m src.main --voice

# Modo voz continuo (escucha permanente)
python -m src.main --voice --continuous

# 🆕 Modo voz con verificación de hablante (solo tu voz)
python -m src.main --voice --single-voice

# Con umbrales personalizados
python -m src.main "texto" --auto-threshold 0.60
```

## 🔐 Verificación de Hablante (Nuevo!)

Aurora ahora puede reconocer **solo tu voz**. Entrena el modelo con tu voz y el asistente rechazará comandos de otras personas:

```bash
# 1. Entrenar con tu voz (5-10 muestras recomendadas)
python -m src.main --train-speaker

# 2. Usar Aurora solo con tu voz
python -m src.main --voice --single-voice

# 3. Script dedicado para más opciones
python scripts/train_speaker.py --samples 10
```

**Características**:
- ✅ Entrenamiento acumulativo (más muestras = más precisión)
- ✅ Modelo persistente (se guarda automáticamente)
- ✅ Configurable (ajusta el umbral de confianza)
- ✅ Flexible (--single-voice para seguridad, --all-voices para uso normal)

Ver [SPEAKER_VERIFICATION.md](SPEAKER_VERIFICATION.md) para guía completa.

## 🎙️ Wakeword (Palabra de Activación)

El sistema incluye procesamiento automático del wakeword "aurora":



## 🎤 Reconocimiento de Voz

El sistema incluye captura desde micrófono y transcripción automática:


Ver [WAKEWORD.md](WAKEWORD.md) para más detalles.

## 📖 Más Información

- Ver [GUIDE.md](GUIDE.md) para documentación completa
- Ver [ADDING_COMMANDS.md](ADDING_COMMANDS.md) para agregar comandos
- Ver [SCRIPTS.md](SCRIPTS.md) para referencia de cada script


## TODO
- ~~Añadir reconocimiento de voz~~ ✅ (ver VOICE.md)
- ~~Añadir reconocimiento de UNA sola voz~~ ✅ (ver SPEAKER_VERIFICATION.md)
- Añadir Wake-on-call
- Añadir algún tipo de "peligro" en los comandos, para pedir más o menos confianza
