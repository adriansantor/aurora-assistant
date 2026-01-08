# Aurora Assistant - Guía Completa

## 📚 Índice
- [Visión General](#visión-general)
- [Arquitectura](#arquitectura)
- [Cómo Funciona](#cómo-funciona)
- [Instalación y Uso](#instalación-y-uso)
- [Estructura del Proyecto](#estructura-del-proyecto)

---

## 🎯 Visión General

**Aurora Assistant** es un asistente inteligente que:
1. **Entiende** lo que el usuario dice mediante un módulo de predicción
2. **Decide** si ejecutar o pedir confirmación (enrutamiento trust-based)
3. **Ejecuta** comandos del sistema de forma segura

### Flujo Básico
```
Texto Usuario → Predicción ML → Decisión de Confianza → Ejecución Segura
```

### Ejemplo Práctico
```bash
$ python -m src.main "abre firefox"

1. Predicción: OPEN_FIREFOX (confianza: 0.60)
2. Decisión: Pide confirmación (0.40 < 0.60 < 0.75)
3. Usuario confirma: "y"
4. Ejecuta: firefox
5. Resultado: ✓ Firefox abierto
```

---

## 🏗️ Arquitectura

### Componentes Principales

```
┌─────────────────────────────────────────────────┐
│                  USUARIO                        │
│               "abre firefox"                    │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│              src/main.py                        │
│         (Orquestador Principal)                 │
│  - Punto de entrada                             │
│  - Coordina todo el flujo                       │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│           src/nlp/predict.py                    │
│         (Predicción de Intención)               │
│  - Carga modelo entrenado                       │
│  - Vectoriza texto                              │
│  - Predice intent + confianza                   │
│  → IntentResult(id, confidence, text)           │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│            src/core/router.py                   │
│          (Enrutamiento Inteligente)             │
│  - conf ≥ 0.75: Ejecuta automáticamente         │
│  - 0.40 ≤ conf < 0.75: Pide confirmación        │
│  - conf < 0.40: Rechaza                         │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│           src/core/executor.py                  │
│          (Ejecución Segura)                     │
│  - Valida contra whitelist (commands.json)      │
│  - Ejecuta con subprocess (sin shell)           │
│  - Captura errores                              │
└─────────────────────────────────────────────────┘
```

### Estructura de Archivos

```
aurora-assistant/
├── src/
│   ├── main.py                 ← Punto de entrada
│   ├── nlp/
│   │   ├── predict.py         ← Predicción ML
│   │   ├── train.py           ← Entrenamiento
│   │   ├── intent_model.py    ← Estructuras de datos
│   │   └── __init__.py
│   └── core/
│       ├── router.py          ← Enrutamiento
│       └── executor.py        ← Ejecución segura
│
├── data/
│   ├── raw/
│   │   └── intents.csv        ← Datos de entrenamiento
│   └── processed/
│       └── label_map.json     ← Mapeo de clases
│
├── models/
│   ├── intent_model.pkl       ← Modelo entrenado
│   └── vectorizer.pkl         ← Vectorizador TF-IDF
│
├── commands/
│   ├── commands.txt           ← Definición de comandos
│   ├── commands.json          ← Comandos validados
│   └── validator.py           ← Validador de seguridad
│
└── requirements.txt           ← Dependencias
```

---

## 🔄 Cómo Funciona

### Pipeline Completo

#### 1. Predicción (predict.py)

**Input:** Texto limpio
```python
"abre firefox"
```

**Proceso:**
1. Carga artefactos (modelo, vectorizador, label_map)
2. Normaliza texto: `"abre firefox"` → `"abre firefox"` (lowercase, strip)
3. Vectoriza: TfidfVectorizer → vector de 36 features
4. Predice: LogisticRegression.predict_proba() → `[0.05, 0.60, 0.35]`
5. Extrae clase: argmax(probabilities) → índice 1
6. Mapea: label_map["1"] → `"OPEN_FIREFOX"`
7. Confianza: max(probabilities) → 0.60

**Output:** 
```python
IntentResult(
    intent_id="OPEN_FIREFOX",
    confidence=0.60,
    text="abre firefox"
)
```

#### 2. Enrutamiento (router.py)

**Input:** IntentResult con confidence=0.60

**Lógica:**
```python
if confidence >= 0.75:
    # Alta confianza → Ejecutar automáticamente
    return AUTO_EXECUTE
elif confidence >= 0.40:
    # Confianza media → Pedir confirmación
    return CONFIRM
else:
    # Confianza baja → Rechazar
    return REJECT
```

**Decisión:** CONFIRM (0.40 ≤ 0.60 < 0.75)

#### 3. Confirmación (main.py)

```
⚠ Confirmation required for intent 'OPEN_FIREFOX' (confidence=0.60)
   Execute 'OPEN_FIREFOX'? (y/n)
   > y
```

#### 4. Ejecución (executor.py)

**Proceso:**
1. Busca `OPEN_FIREFOX` en `commands.json`
2. Obtiene comando: `"firefox"`
3. Valida que está en whitelist
4. Ejecuta: `subprocess.run(["firefox"])` (sin shell=True)
5. Captura resultado

**Output:**
```
✓ Executed: OPEN_FIREFOX
```

### Modelo de Machine Learning

**Algoritmo:** LogisticRegression + TfidfVectorizer

**Entrenamiento:**
```
data/raw/intents.csv
         ↓
TfidfVectorizer (vectorización)
         ↓
LogisticRegression (clasificación)
         ↓
		Clases
         ↓
models/intent_model.pkl + vectorizer.pkl
```

**Predicción:**
```
"abre firefox"
      ↓
Vectorizador (transform)
      ↓
Vector [0.0, 0.8, 0.1, ...]
      ↓
Modelo (predict_proba)
      ↓
[0.05, 0.60, 0.30, 0.05]
      ↓
argmax() → clase 1 → "OPEN_FIREFOX"
max() → 0.60 (confianza)
```

---

## 🚀 Instalación y Uso

### Requisitos Previos

- Python 3.8+
- pip
- Sistema Linux/Mac (o WSL en Windows)

### Instalación

```bash
# 1. Clonar/descargar proyecto
cd aurora-assistant

# 2. Crear entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

**Dependencias principales:**
- scikit-learn (ML)
- numpy (operaciones numéricas)
- pandas (manejo de datos)
- joblib (serialización)

### Configuración Inicial

```bash
# 1. Entrenar el modelo
python -m src.nlp.train

# Salida esperada:
# ✓ Training completed successfully!
# Artifacts saved:
#   - models/intent_model.pkl
#   - models/vectorizer.pkl
#   - data/processed/label_map.json
```

### Uso Básico

#### Modo Comando Único
```bash
python -m src.main "abre firefox"
```

#### Modo Interactivo
```bash
python -m src.main

You: abre firefox
⚠ Confirmation required for intent 'OPEN_FIREFOX' (confidence=0.60)
   Execute 'OPEN_FIREFOX'? (y/n)
   > y
✓ Executed: OPEN_FIREFOX

You: exit
```

### Pruebas Rápidas

#### Test de Predicción
```bash
python -m src.nlp.predict "abre firefox"

# Salida:
# IntentResult(intent_id='OPEN_FIREFOX', confidence=0.60, text='abre firefox')
```

#### Test de Validación
```bash
python commands/validator.py

# Salida:
# ✔ Generated commands.json with 4 commands
```

---


### Formato de Datos

#### intents.csv
```csv
text,intent
abre firefox,OPEN_FIREFOX
abre el navegador,OPEN_FIREFOX
me voy del ordenador,LOCK_SCREEN
suspender,SUSPEND
desbloquea,UNLOCK_SESSION
```

#### commands.txt
```
OPEN_FIREFOX = firefox
LOCK_SCREEN = loginctl lock-session
SUSPEND = systemctl suspend
UNLOCK_SESSION = loginctl unlock-session
```

#### label_map.json
```json
{
  "0": "LOCK_SCREEN",
  "1": "OPEN_FIREFOX",
  "2": "SUSPEND",
  "3": "UNLOCK_SESSION"
}
```

---

## 🛡️ Seguridad

### Capas de Protección

1. **Validación de Comandos**
   - Solo comandos en `commands.json` son ejecutables
   - `validator.py` rechaza caracteres peligrosos: `;`, `&&`, `|`, `>`, `<`, `` ` ``

2. **Validación de Confianza**
   - Mínimo 0.40 para considerar ejecución
   - Auto-ejecución solo con confianza ≥ 0.75

3. **Confirmación Humana**
   - Requerida para confianza 0.40-0.75
   - Loop explícito esperando "y" o "n"

4. **Ejecución Segura**
   - `subprocess.run()` sin `shell=True` (evita inyección)
   - Lista de argumentos en lugar de string
   - Captura de errores explícita

### Ejemplo de Validación

```python
# ❌ RECHAZADO por validator.py
"MALICIOUS = rm -rf / ; echo done"  # Contiene ; (peligroso)

# ✅ ACEPTADO
"OPEN_FIREFOX = firefox"            # Sin caracteres peligrosos
```

---

## 📈 Mejorando el Modelo

### Agregar Más Ejemplos

Editar `data/raw/intents.csv`:
```csv
# Agregar variaciones para OPEN_FIREFOX
lanza el navegador,OPEN_FIREFOX
necesito navegar,OPEN_FIREFOX
quiero internet,OPEN_FIREFOX
```

Reentrenar:
```bash
python -m src.nlp.train
```

### Ajustar Parámetros

Editar `src/nlp/train.py`:
```python
# Vectorizador
vectorizer = TfidfVectorizer(
    max_features=5000,      # Aumentar vocabulario
    ngram_range=(1, 2)      # Usar bigramas
)

# Modelo
model = LogisticRegression(
    max_iter=2000,          # Más iteraciones
    C=0.5                   # Ajustar regularización
)
```

### Verificar Métricas

```bash
# Predecir varios ejemplos
python -m src.nlp.predict "abre firefox"
python -m src.nlp.predict "lanza navegador"
python -m src.nlp.predict "quiero internet"

# Verificar confianza
# Meta: confianza ≥ 0.75 para auto-ejecución
```

---

## 🔧 Troubleshooting

### Error: "model not found"
**Causa:** Modelo no entrenado
**Solución:**
```bash
python -m src.nlp.train
```

### Error: "does not support predict_proba"
**Causa:** Modelo incorrecto (ej: SVM sin probability=True)
**Solución:** Usar LogisticRegression en `train.py`

### Confianza Siempre Baja (<0.40)
**Causa:** Pocos ejemplos de entrenamiento
**Solución:** Agregar más variaciones en `intents.csv`

### Comando No Se Ejecuta
**Causa:** No está en `commands.json`
**Solución:**
1. Agregar a `commands/commands.txt`
2. Ejecutar `python commands/validator.py`

---

## 📚 Documentación Adicional

- **[ADDING_COMMANDS.md](ADDING_COMMANDS.md)** - Cómo agregar comandos nuevos (workflow completo)
- **[SCRIPTS.md](SCRIPTS.md)** - Referencia de cada script (qué hace cada uno)
- **[README.md](README.md)** - Quick start

---

**Versión:** 1.0  
**Última actualización:** Enero 2026
