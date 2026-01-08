# Referencia de Scripts

Documentación detallada de cada script del proyecto Aurora Assistant.

## 📚 Índice
- [Scripts Principales](#scripts-principales)
- [Scripts de Utilidad](#scripts-de-utilidad)
- [Módulos Core](#módulos-core)

---

## 🚀 Scripts Principales

### `src/main.py`

**Propósito:** Punto de entrada y orquestador principal del sistema

**¿Qué hace?**
1. Inicializa el sistema (carga configuración)
2. Lee texto del usuario (CLI o interactivo)
3. Llama a `predict.py` para obtener predicción
4. Usa `router.py` para decidir acción
5. Ejecuta comando con `executor.py`
6. Maneja errores y logging

**Uso:**
```bash
# Comando único
python -m src.main "abre firefox"

# Modo interactivo
python -m src.main

# Con parámetros
python -m src.main "texto" --auto-threshold 0.75 --confirm-threshold 0.4
```

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `text` | str | None | Texto a procesar (None = modo interactivo) |
| `--auto-threshold` | float | 0.75 | Confianza mínima para auto-ejecutar |
| `--confirm-threshold` | float | 0.40 | Confianza mínima para pedir confirmación |
| `--commands` | path | commands/commands.json | Ruta a archivo de comandos |

**Flujo Interno:**
```python
def main():
    1. Parse arguments
    2. Initialize AuroraAssistant
    3. if text:
         process_single(text)
       else:
         run_interactive()

def process_text(text):
    1. result = predict(text)
    2. decision = router.route(result)
    3. if decision == AUTO_EXECUTE:
         executor.execute(result.intent_id)
    4. elif decision == CONFIRM:
         if user_confirms():
            executor.execute(result.intent_id)
    5. else:
         print("Confidence too low")
```

**Salidas:**
- Logs detallados en cada paso
- Confirmación de ejecución: `✓ Executed: INTENT_ID`
- Errores explícitos si algo falla

**Líneas:** ~200

---

### `src/nlp/predict.py`

**Propósito:** Predicción de intención (inference only)

**¿Qué hace?**
1. Carga artefactos entrenados (modelo, vectorizador, label_map)
2. Normaliza texto de entrada
3. Vectoriza con TfidfVectorizer
4. Predice con LogisticRegression
5. Devuelve IntentResult con confianza real

**Uso:**
```bash
# CLI - comando único
python -m src.nlp.predict "abre firefox"

# Interactivo
python -m src.nlp.predict
> abre firefox
  IntentResult(intent_id='OPEN_FIREFOX', confidence=0.60, text='abre firefox')
```

**Uso programático:**
```python
from src.nlp.predict import predict

result = predict("abre firefox")
print(result.intent_id)    # "OPEN_FIREFOX"
print(result.confidence)   # 0.60
print(result.text)         # "abre firefox"
```

**Artefactos requeridos:**
- `models/intent_model.pkl` (LogisticRegression)
- `models/vectorizer.pkl` (TfidfVectorizer)
- `data/processed/label_map.json` (mapeo índice→intent)
- `commands/commands.json` (validación de intents)

**Proceso:**
```
1. normalize_text("abre firefox")
   → "abre firefox" (lowercase, strip)

2. vectorizer.transform([text])
   → sparse matrix [0.0, 0.8, 0.1, ...]

3. model.predict_proba(X)[0]
   → [0.05, 0.60, 0.30, 0.05]

4. argmax(probabilities)
   → 1

5. label_map["1"]
   → "OPEN_FIREFOX"

6. max(probabilities)
   → 0.60

7. return IntentResult(
     intent_id="OPEN_FIREFOX",
     confidence=0.60,
     text="abre firefox"
   )
```

**NO hace:**
- ❌ No ejecuta comandos
- ❌ No entrena modelos
- ❌ No modifica estado
- ❌ No procesa audio

**Errores comunes:**
- `PredictError: model not found` → Entrenar modelo
- `PredictError: does not support predict_proba` → Usar LogisticRegression
- `PredictError: text cannot be empty` → Pasar texto válido

**Líneas:** ~237

---

### `src/nlp/train.py`

**Propósito:** Entrenamiento del modelo de clasificación

**¿Qué hace?**
1. Carga datos de `data/raw/intents.csv`
2. Vectoriza textos con TfidfVectorizer
3. Codifica labels (intent → índice)
4. Entrena LogisticRegression
5. Guarda artefactos en `models/` y `data/processed/`

**Uso:**
```bash
# Entrenar con datos por defecto
python -m src.nlp.train

# Con CSV personalizado
python -m src.nlp.train /ruta/a/intents.csv
```

**Input:** `data/raw/intents.csv`
```csv
text,intent
abre firefox,OPEN_FIREFOX
me voy,LOCK_SCREEN
suspender,SUSPEND
```

**Outputs:**

| Archivo | Descripción |
|---------|-------------|
| `models/intent_model.pkl` | LogisticRegression entrenado |
| `models/vectorizer.pkl` | TfidfVectorizer fitted |
| `data/processed/label_map.json` | Mapeo {"0": "INTENT_ID"} |
| `data/processed/X_train.npy` | Features de entrenamiento |
| `data/processed/y_train.npy` | Labels de entrenamiento |

**Parámetros del modelo:**
```python
# Vectorizador
TfidfVectorizer(
    lowercase=True,
    stop_words='english',
    max_features=5000
)

# Clasificador
LogisticRegression(
    max_iter=1000,
    solver='lbfgs',
    random_state=42
)
```

**Proceso:**
```
1. load_training_data()
   → DataFrame(text, intent)

2. TfidfVectorizer.fit_transform(texts)
   → X: sparse matrix (n_samples, n_features)

3. LabelEncoder.fit_transform(intents)
   → y: array [0, 1, 2, ...]

4. LogisticRegression.fit(X, y)
   → Modelo entrenado

5. save_artifacts()
   → Guardar todo en disco
```

**Salida esperada:**
```
2026-01-03 21:41:16 - INFO - Starting model training...
2026-01-03 21:41:16 - INFO - Loaded 31 training examples
2026-01-03 21:41:16 - INFO - Unique intents: {'LOCK_SCREEN', 'OPEN_FIREFOX', 'SUSPEND', 'UNLOCK_SESSION'}
2026-01-03 21:41:16 - INFO - Vectorizing texts...
2026-01-03 21:41:16 - INFO - Created 36 features
2026-01-03 21:41:16 - INFO - Training LogisticRegression...
2026-01-03 21:41:16 - INFO - ✓ Training completed successfully!
```

**Líneas:** ~280

---

## 🔧 Scripts de Utilidad

### `commands/validator.py`

**Propósito:** Validar y generar commands.json de forma segura

**¿Qué hace?**
1. Lee `commands/commands.txt`
2. Valida formato: `COMMAND_ID = comando`
3. Detecta caracteres peligrosos: `;`, `&&`, `|`, `>`, `<`, `` ` ``, `$`
4. Genera `commands/commands.json` si todo es válido

**Uso:**
```bash
python commands/validator.py
```

**Input:** `commands/commands.txt`
```
OPEN_FIREFOX = firefox
LOCK_SCREEN = loginctl lock-session
```

**Output:** `commands/commands.json`
```json
{
  "OPEN_FIREFOX": {
    "cmd": "firefox",
    "danger": "unknown"
  },
  "LOCK_SCREEN": {
    "cmd": "loginctl lock-session",
    "danger": "unknown"
  }
}
```

**Validaciones:**
- ✅ Formato correcto: `ID = comando`
- ✅ Sin caracteres de shell injection
- ✅ ID en MAYÚSCULAS
- ❌ Rechaza líneas vacías
- ❌ Rechaza formato incorrecto

**Caracteres prohibidos:**
```python
DANGEROUS_CHARS = [';', '&&', '||', '|', '`', '$', '>', '<']
```

**Salidas:**
- `✔ Generated commands.json with N commands` (éxito)
- `❌ Invalid format at line N` (error)
- `❌ Dangerous character 'X' detected` (error)

**Líneas:** ~95

---

### `src/nlp/intent_model.py`

**Propósito:** Definir estructuras de datos

**¿Qué hace?**
Define la clase `IntentResult` usada en todo el sistema

**Estructura:**
```python
@dataclass
class IntentResult:
    intent_id: str      # "OPEN_FIREFOX"
    confidence: float   # 0.60 (0.0 - 1.0)
    text: str          # "abre firefox"
```

**Uso:**
```python
from src.nlp.intent_model import IntentResult

result = IntentResult(
    intent_id="OPEN_FIREFOX",
    confidence=0.60,
    text="abre firefox"
)

print(result.intent_id)    # "OPEN_FIREFOX"
print(result.confidence)   # 0.60
print(result)              # IntentResult(intent_id='OPEN_FIREFOX', ...)
```

**Líneas:** ~23

---

## ⚙️ Módulos Core

### `src/core/router.py`

**Propósito:** Enrutamiento basado en confianza

**¿Qué hace?**
Decide la acción según la confianza de predicción:
- Alta (≥0.75): Ejecutar automáticamente
- Media (0.40-0.75): Pedir confirmación
- Baja (<0.40): Rechazar

**Uso programático:**
```python
from src.core.router import CommandRouter
from src.core.executor import CommandExecutor

executor = CommandExecutor(Path("commands/commands.json"))
router = CommandRouter(
    executor=executor,
    auto_execute_threshold=0.75,
    confirmation_threshold=0.40
)

result = predict("abre firefox")  # confidence=0.60
action = router.route(result)
# → CONFIRM (0.40 ≤ 0.60 < 0.75)
```

**Política de decisión:**
```python
if confidence >= auto_threshold:
    return AUTO_EXECUTE
elif confidence >= confirm_threshold:
    return CONFIRM
else:
    return REJECT
```

**Parámetros configurables:**
- `auto_execute_threshold` (default: 0.75)
- `confirmation_threshold` (default: 0.40)

**Líneas:** ~68

---

### `src/core/executor.py`

**Propósito:** Ejecución segura de comandos del sistema

**¿Qué hace?**
1. Lee `commands.json` (whitelist)
2. Valida que intent_id existe
3. Ejecuta comando con `subprocess.run()`
4. Captura stdout/stderr
5. Maneja errores

**Uso programático:**
```python
from src.core.executor import CommandExecutor
from pathlib import Path

executor = CommandExecutor(Path("commands/commands.json"))
executor.execute("OPEN_FIREFOX")
# → Ejecuta: firefox
```

**Seguridad:**
- ✅ Solo ejecuta comandos en whitelist (commands.json)
- ✅ Usa `subprocess.run()` sin `shell=True`
- ✅ Lista de argumentos en lugar de string
- ✅ Captura de errores explícita
- ❌ No permite comandos no autorizados

**Ejemplo de ejecución:**
```python
# commands.json
{
  "OPEN_FIREFOX": {
    "cmd": "firefox",
    "danger": "unknown"
  }
}

# Código
executor.execute("OPEN_FIREFOX")

# Internamente:
subprocess.run(
    ["firefox"],  # Lista, no string
    shell=False,  # Sin shell injection
    capture_output=True,
    timeout=30
)
```

**Errores:**
- `ExecutionError: Unknown command 'X'` → No está en commands.json
- `ExecutionError: Command 'X' failed: ...` → Error al ejecutar

**Líneas:** ~71

---

## 📊 Resumen de Scripts

| Script | Propósito | Líneas | Input | Output |
|--------|-----------|--------|-------|--------|
| `src/main.py` | Orquestador | ~200 | Texto usuario | Comando ejecutado |
| `src/nlp/predict.py` | Predicción | ~237 | Texto | IntentResult |
| `src/nlp/train.py` | Entrenamiento | ~280 | intents.csv | Artefactos ML |
| `src/nlp/intent_model.py` | Estructuras | ~23 | - | IntentResult class |
| `src/core/router.py` | Enrutamiento | ~68 | IntentResult | Decisión |
| `src/core/executor.py` | Ejecución | ~71 | intent_id | Comando ejecutado |
| `commands/validator.py` | Validación | ~95 | commands.txt | commands.json |

**Total:** ~1,074 líneas de código core

---

## 🔗 Flujo de Interacción

```
┌─────────────-─┐
│   Usuario     │
│ "abre firefox"│
└─-─────┬───────┘
        │
        ▼
┌──────────────────┐
│   src/main.py    │ ← Orquestador
└──────┬───────────┘
       │
       ├─→ predict.py        → IntentResult(OPEN_FIREFOX, 0.60)
       │
       ├─→ router.py         → CONFIRM (0.40 < 0.60 < 0.75)
       │
       ├─→ [Confirmación]    → Usuario: "y"
       │
       └─→ executor.py       → subprocess.run(["firefox"])
                              → ✓ Executed: OPEN_FIREFOX
```

---

## 🎓 Cuándo Usar Cada Script

### Uso Normal del Sistema
```bash
# Solo necesitas esto:
python -m src.main "abre firefox"
```

### Desarrollo/Debug
```bash
# Test de predicción solo
python -m src.nlp.predict "texto"

# Entrenar modelo
python -m src.nlp.train

# Validar comandos
python commands/validator.py
```

### Integración en Otro Sistema
```python
# Import de módulos core
from src.nlp.predict import predict
from src.core.router import CommandRouter
from src.core.executor import CommandExecutor

# Usar programáticamente
result = predict("abre firefox")
if result.confidence >= 0.75:
    executor.execute(result.intent_id)
```

---

## 📚 Documentación Relacionada

- **[GUIDE.md](GUIDE.md)** - Documentación general completa
- **[ADDING_COMMANDS.md](ADDING_COMMANDS.md)** - Workflow de agregar comandos
- **[README.md](README.md)** - Quick start

---

**Última actualización:** Enero 2026
