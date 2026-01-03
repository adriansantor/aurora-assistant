# Agregando Comandos Nuevos

Guía completa para agregar nuevos comandos al sistema Aurora Assistant.

## 📚 Índice
- [Workflow Completo](#workflow-completo)
- [Paso a Paso Detallado](#paso-a-paso-detallado)
- [Ejemplo Práctico: UNLOCK_SESSION](#ejemplo-práctico-unlock_session)
- [Mejorando la Confianza](#mejorando-la-confianza)
- [Checklist](#checklist)

---

## 🔄 Workflow Completo

```
1. Definir comando
   └─ Editar commands/commands.txt
          ↓
2. Validar seguridad
   └─ Ejecutar commands/validator.py
          ↓
3. Agregar ejemplos de entrenamiento
   └─ Editar data/raw/intents.csv
          ↓
4. Entrenar modelo
   └─ Ejecutar src/nlp/train.py
          ↓
5. Probar comando
   └─ Ejecutar src/main.py
          ↓
6. Verificar confianza
   └─ Si < 0.75: Agregar más ejemplos
```

---

## 📋 Paso a Paso Detallado

### Paso 1: Definir el Comando

**Archivo:** `commands/commands.txt`

**Formato:**
```
COMMAND_ID = sistema_comando
```

**Ejemplo:**
```
UNLOCK_SESSION = loginctl unlock-session
```

**Reglas:**
- Un comando por línea
- COMMAND_ID en MAYÚSCULAS_CON_GUIONES_BAJOS
- Sin caracteres peligrosos: `;`, `&&`, `||`, `|`, `` ` ``, `$`, `>`, `<`
- Comando debe existir en el sistema

**Comandos Seguros vs Peligrosos:**

✅ **SEGURO:**
```
OPEN_FIREFOX = firefox
LOCK_SCREEN = loginctl lock-session
PLAY_MUSIC = spotify
```

❌ **PELIGROSO (rechazado):**
```
MALICIOUS = rm -rf /; echo "done"     # Contiene ;
INJECTION = echo "test" && rm file    # Contiene &&
PIPE = cat file | grep text           # Contiene |
```

---

### Paso 2: Validar con validator.py

**Comando:**
```bash
python commands/validator.py
```

**¿Qué hace?**
1. Lee `commands/commands.txt`
2. Valida formato: `COMMAND_ID = comando`
3. Detecta caracteres peligrosos
4. Genera `commands/commands.json` si todo es válido

**Salida esperada:**
```
✔ Generated commands.json with N commands
```

**En caso de error:**
```
❌ Invalid format at line 3: "WRONG FORMAT"
❌ Dangerous character ';' detected in command: "rm -rf /"
```

**Resultado:** `commands/commands.json`
```json
{
  "UNLOCK_SESSION": {
    "cmd": "loginctl unlock-session",
    "danger": "unknown"
  }
}
```

---

### Paso 3: Agregar Ejemplos de Entrenamiento

**Archivo:** `data/raw/intents.csv`

**Formato CSV:**
```csv
text,intent
frase de ejemplo,COMMAND_ID
otra variación,COMMAND_ID
```

**Principios:**
- ✅ Mínimo 8 ejemplos por comando
- ✅ Variaciones naturales del lenguaje
- ✅ Diferentes contextos de uso
- ✅ Frases cortas y largas
- ❌ No copiar de otros intents

**Ejemplo para UNLOCK_SESSION:**
```csv
text,intent
desbloquea la sesion,UNLOCK_SESSION
desbloquea,UNLOCK_SESSION
abre la sesion,UNLOCK_SESSION
activa la pantalla,UNLOCK_SESSION
necesito trabajar,UNLOCK_SESSION
quiero acceder,UNLOCK_SESSION
abre el ordenador,UNLOCK_SESSION
hazme visible,UNLOCK_SESSION
```

**Consejos:**
- Incluir sinónimos: "desbloquea", "abre", "activa"
- Contextos: "necesito trabajar", "quiero acceder"
- Variaciones: con/sin artículos, formal/informal
- Más ejemplos → Mayor confianza

---

### Paso 4: Entrenar el Modelo

**Comando:**
```bash
python -m src.nlp.train
```

**¿Qué hace?**
1. Carga `data/raw/intents.csv` (31+ ejemplos)
2. Vectoriza textos con TfidfVectorizer
3. Entrena LogisticRegression
4. Guarda artefactos:
   - `models/intent_model.pkl`
   - `models/vectorizer.pkl`
   - `data/processed/label_map.json`

**Salida esperada:**
```
2026-01-03 21:41:16 - INFO - Starting model training...
2026-01-03 21:41:16 - INFO - Loaded 31 training examples
2026-01-03 21:41:16 - INFO - Unique intents: {'LOCK_SCREEN', 'OPEN_FIREFOX', 'SUSPEND', 'UNLOCK_SESSION'}
2026-01-03 21:41:16 - INFO - Vectorizing texts...
2026-01-03 21:41:16 - INFO - Created 36 features
2026-01-03 21:41:16 - INFO - Encoding labels...
2026-01-03 21:41:16 - INFO - Created label map: {'0': 'LOCK_SCREEN', '1': 'OPEN_FIREFOX', '2': 'SUSPEND', '3': 'UNLOCK_SESSION'}
2026-01-03 21:41:16 - INFO - Training LogisticRegression...
2026-01-03 21:41:16 - INFO - Model trained. Classes: [0 1 2 3]
2026-01-03 21:41:16 - INFO - ✓ Training completed successfully!
```

**Verificar label_map.json:**
```bash
cat data/processed/label_map.json
```

Debe contener tu nuevo intent:
```json
{
  "0": "LOCK_SCREEN",
  "1": "OPEN_FIREFOX",
  "2": "SUSPEND",
  "3": "UNLOCK_SESSION"
}
```

---

### Paso 5: Probar el Comando

**Test de Predicción:**
```bash
python -m src.nlp.predict "desbloquea"
```

**Salida esperada:**
```
IntentResult(intent_id='UNLOCK_SESSION', confidence=0.50, text='desbloquea')
```

**Test Completo:**
```bash
python -m src.main "desbloquea"
```

**Flujo esperado:**
```
2026-01-03 21:37:59 - INFO - Aurora Assistant initialized
2026-01-03 21:37:59 - INFO - Available commands: LOCK_SCREEN, OPEN_FIREFOX, SUSPEND, UNLOCK_SESSION
2026-01-03 21:37:59 - INFO - Processing: 'desbloquea'
2026-01-03 21:37:59 - INFO - Predicted: IntentResult(intent_id='UNLOCK_SESSION', confidence=0.50, text='desbloquea')
2026-01-03 21:37:59 - WARNING - Confirmation needed: Confirmation required for intent 'UNLOCK_SESSION' (confidence=0.50)
⚠ Confirmation required for intent 'UNLOCK_SESSION' (confidence=0.50)
   Execute 'UNLOCK_SESSION'? (y/n)
   > y
2026-01-03 21:38:04 - INFO - ✓ Command executed after confirmation: UNLOCK_SESSION
✓ Executed: UNLOCK_SESSION
```

---

### Paso 6: Verificar Confianza

**Objetivo:** Confianza ≥ 0.75 para auto-ejecución sin confirmación

**Niveles de Confianza:**
- `≥ 0.75`: ✅ Auto-ejecución
- `0.40 - 0.75`: ⚠️ Requiere confirmación
- `< 0.40`: ❌ Rechazado

**Si confianza < 0.75:**
Ver sección [Mejorando la Confianza](#mejorando-la-confianza)

---

## 📖 Ejemplo Práctico: UNLOCK_SESSION

### Contexto
Agregar comando para desbloquear la sesión del sistema.

### Fase 1: Definición
```bash
# Editar commands/commands.txt
echo "UNLOCK_SESSION = loginctl unlock-session" >> commands/commands.txt
```

### Fase 2: Validación
```bash
python commands/validator.py
```
**Salida:** `✔ Generated commands.json with 4 commands`

### Fase 3: Datos de Entrenamiento
```bash
# Editar data/raw/intents.csv
cat >> data/raw/intents.csv << EOF
desbloquea la sesion,UNLOCK_SESSION
desbloquea,UNLOCK_SESSION
abre la sesion,UNLOCK_SESSION
activa la pantalla,UNLOCK_SESSION
necesito trabajar,UNLOCK_SESSION
quiero acceder,UNLOCK_SESSION
abre el ordenador,UNLOCK_SESSION
hazme visible,UNLOCK_SESSION
EOF
```

### Fase 4: Entrenamiento
```bash
python -m src.nlp.train
```
**Resultado:** Modelo con 4 intents (31 ejemplos)

### Fase 5: Testing
```bash
# Predicción
python -m src.nlp.predict "desbloquea"
# → IntentResult(intent_id='UNLOCK_SESSION', confidence=0.50)

# Ejecución completa
python -m src.main "desbloquea"
# → Pide confirmación (0.50 < 0.75)
# → Usuario: "y"
# → ✓ Executed: UNLOCK_SESSION
```

### Resultados
- ✅ Comando agregado exitosamente
- ⚠️ Confianza: 0.50 (requiere mejora)
- ✅ Funciona correctamente

---

## 🚀 Mejorando la Confianza

### Opción A: Más Ejemplos Variados

**Estrategia:** Agregar 10-15 ejemplos más con diferentes estructuras

```csv
# Agregar a intents.csv
desbloquea mi ordenador,UNLOCK_SESSION
dame acceso,UNLOCK_SESSION
quiero acceder al ordenador,UNLOCK_SESSION
activa mi sesion,UNLOCK_SESSION
vuelve a mostrar la pantalla,UNLOCK_SESSION
necesito mi ordenador,UNLOCK_SESSION
dame la pantalla,UNLOCK_SESSION
abre mi sesion,UNLOCK_SESSION
despierta el ordenador,UNLOCK_SESSION
quiero trabajar,UNLOCK_SESSION
vuelvo a casa,UNLOCK_SESSION
activa la sesion,UNLOCK_SESSION
desbloquea todo,UNLOCK_SESSION
necesito la pantalla,UNLOCK_SESSION
permiteme trabajar,UNLOCK_SESSION
```

**Reentrenar:**
```bash
python -m src.nlp.train
python -m src.nlp.predict "desbloquea"
# Objetivo: confidence > 0.75
```

---

### Opción B: Palabras Clave Más Específicas

**Problema:** Palabras genéricas bajan la confianza

❌ **Palabras débiles:**
```csv
vuelvo,UNLOCK_SESSION         # Muy vaga
ya estoy,UNLOCK_SESSION       # Ambigua
despierta,UNLOCK_SESSION      # Puede ser SUSPEND
```

✅ **Palabras fuertes:**
```csv
desbloquea la sesion,UNLOCK_SESSION       # Muy específica
activa mi pantalla,UNLOCK_SESSION         # Clara
abre acceso al ordenador,UNLOCK_SESSION   # Descriptiva
```

**Reemplazar ejemplos débiles:**
```bash
# Editar intents.csv
# Cambiar "vuelvo" → "desbloquea la sesion"
# Cambiar "ya estoy" → "activa mi pantalla"
```

---

### Opción C: Ajustar Parámetros del Modelo

**Archivo:** `src/nlp/train.py`

**Vectorizador - Agregar bigramas:**
```python
vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words='english',
    max_features=5000,
    ngram_range=(1, 2)  # ← Usar unigramas + bigramas
)
```

**Modelo - Ajustar regularización:**
```python
model = LogisticRegression(
    max_iter=2000,      # ← Más iteraciones
    C=0.5,              # ← Regularización más débil
    solver='lbfgs'
)
```

**Reentrenar:**
```bash
python -m src.nlp.train
```

**Verificar mejora:**
```bash
python -m src.nlp.predict "desbloquea"
# Esperado: confidence > 0.75
```

---

### Opción D: Balancear Dataset

**Problema:** Clases desbalanceadas

```bash
# Verificar distribución
grep -c "LOCK_SCREEN" data/raw/intents.csv    # 8
grep -c "OPEN_FIREFOX" data/raw/intents.csv   # 8
grep -c "SUSPEND" data/raw/intents.csv        # 7
grep -c "UNLOCK_SESSION" data/raw/intents.csv # 8
```

**Objetivo:** ~10 ejemplos por clase, todos balanceados

**Agregar ejemplos a clases con pocos:**
```bash
# Si SUSPEND tiene 7, agregar 3 más
echo "dormir ahora,SUSPEND" >> data/raw/intents.csv
echo "quiero descansar,SUSPEND" >> data/raw/intents.csv
echo "pausa el sistema,SUSPEND" >> data/raw/intents.csv
```

---

## ✅ Checklist

```markdown
Fase 1: Definición
□ Editado commands/commands.txt
  └─ Formato: COMANDO_ID = comando_sistema
□ Comando existe en el sistema
□ Sin caracteres peligrosos

Fase 2: Validación
□ Ejecutado: python commands/validator.py
□ Confirmado: ✔ Generated commands.json with N commands
□ Verificado: Comando presente en commands.json

Fase 3: Datos de Entrenamiento
□ Editado data/raw/intents.csv
□ Agregados: Mínimo 8 ejemplos variados
□ Sin duplicados de otros intents

Fase 4: Entrenamiento
□ Ejecutado: python -m src.nlp.train
□ Confirmado: ✓ Training completed successfully!
□ Verificado: Intent en label_map.json

Fase 5: Testing
□ Test predicción: python -m src.nlp.predict "ejemplo"
□ Confirmado: IntentResult correcto
□ Test ejecución: python -m src.main "ejemplo"
□ Confirmado: Comando ejecutado

Fase 6: Confianza
□ Verificada confianza de predicción
  └─ Si < 0.75: Agregar ejemplos / ajustar parámetros
  └─ Si ≥ 0.75: ✓ Ejecución automática habilitada
```

---

## 📊 Tabla de Archivos Involucrados

| Archivo                         | Acción      | Fase |
| ------------------------------- | ----------- | ---- |
| `commands/commands.txt`         | ✏️ Editar   | 1    |
| `commands/validator.py`         | ▶️ Ejecutar | 2    |
| `commands/commands.json`        | ✅ Verificar | 2    |
| `data/raw/intents.csv`          | ✏️ Editar   | 3    |
| `src/nlp/train.py`              | ▶️ Ejecutar | 4    |
| `models/intent_model.pkl`       | ✅ Regenerar | 4    |
| `models/vectorizer.pkl`         | ✅ Regenerar | 4    |
| `data/processed/label_map.json` | ✅ Regenerar | 4    |
| `src/main.py`                   | ▶️ Ejecutar | 5    |

---

## 🎓 Tips Avanzados

### Probar Múltiples Variaciones Rápidamente

```bash
# Crear script de test
cat > test_variations.sh << 'EOF'
#!/bin/bash
for phrase in "desbloquea" "abre sesion" "activa pantalla" "necesito trabajar"; do
    echo "Testing: $phrase"
    python -m src.nlp.predict "$phrase" | grep -E "intent_id|confidence"
    echo ""
done
EOF

chmod +x test_variations.sh
./test_variations.sh
```

### Ver Todas las Predicciones

```bash
# Predecir todos los ejemplos de un intent
grep "UNLOCK_SESSION" data/raw/intents.csv | cut -d',' -f1 | while read phrase; do
    python -m src.nlp.predict "$phrase"
done
```

### Comparar Antes/Después

```bash
# Guardar confianza antes
python -m src.nlp.predict "desbloquea" > antes.txt

# Agregar ejemplos y reentrenar
echo "nuevos ejemplos..." >> data/raw/intents.csv
python -m src.nlp.train

# Guardar confianza después
python -m src.nlp.predict "desbloquea" > despues.txt

# Comparar
diff antes.txt despues.txt
```

---

## 🎯 Resultado Esperado

Después de completar todos los pasos:

✅ **Comando funcional** con:
- Definido en `commands.txt`
- Validado en `commands.json`
- Entrenado con 8+ ejemplos
- Modelo con 4+ intents
- Predicción correcta
- Ejecución exitosa

✅ **Confianza óptima** (meta: ≥ 0.75):
- 10-15 ejemplos variados
- Palabras clave específicas
- Dataset balanceado
- Auto-ejecución sin confirmación

✅ **Documentado** para replicación futura

---

**Última actualización:** Enero 2026  
**Documentación relacionada:** [GUIDE.md](GUIDE.md) | [SCRIPTS.md](SCRIPTS.md)
