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

## 🏗️ Arquitectura

```
Texto Usuario → predict.py → router.py → executor.py → Comando Ejecutado
                   ↓            ↓            ↓
                Intent +    Decisión    Ejecución
               Confianza   (0.40-0.75)   Segura
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

# Modo interactivo
python -m src.main

# Con umbrales personalizados
python -m src.main "texto" --auto-threshold 0.60
```

## 📖 Más Información

- Ver [GUIDE.md](GUIDE.md) para documentación completa
- Ver [ADDING_COMMANDS.md](ADDING_COMMANDS.md) para agregar comandos
- Ver [SCRIPTS.md](SCRIPTS.md) para referencia de cada script


## TODO
- Añadir reconocimiento de voz
- Añadir Wake-on-call
- Añadir algún tipo de "peligro" en los comandos, para pedir más o menos confianza