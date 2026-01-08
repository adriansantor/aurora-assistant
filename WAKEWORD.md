# Wakeword (Palabra de Activación)

## Descripción

El módulo de **wakeword** detecta y elimina la palabra de activación "aurora" del inicio de los comandos antes de procesarlos. Esto permite que el usuario diga "aurora abre firefox" y el sistema procese únicamente "abre firefox" para la predicción de intenciones.

## Características

- ✅ **Detección case-insensitive**: "aurora", "Aurora", "AURORA" son todas válidas
- ✅ **Eliminación inteligente**: Solo elimina del inicio del texto (configurable)
- ✅ **Normalización de espacios**: Limpia múltiples espacios automáticamente
- ✅ **Configurable**: Todos los parámetros se pueden ajustar en `config/wakeword.yaml`
- ✅ **Integrado**: Funciona automáticamente en el flujo principal

## Configuración

Archivo: `config/wakeword.yaml`

```yaml
# Palabra que activa el asistente
wakeword: "aurora"

# Si la detección debe distinguir entre mayúsculas y minúsculas
case_sensitive: false

# Si solo eliminar el wakeword del inicio del texto o de cualquier parte
remove_from_start_only: true
```

### Parámetros

- **wakeword**: La palabra de activación (por defecto: "aurora")
- **case_sensitive**: Si distinguir mayúsculas/minúsculas (por defecto: false)
- **remove_from_start_only**: Si solo eliminar del inicio (recomendado: true)

## Uso

### Uso automático en el sistema

El wakeword se procesa automáticamente en `main.py`:

```python
from src.audio.wakeword import remove_wakeword

# En process_text()
clean_text = remove_wakeword(text)  # Elimina "aurora" si está presente
intent_result = predict(clean_text)  # Predice con el texto limpio
```

### Uso directo del módulo

```python
from src.audio.wakeword import remove_wakeword, WakewordProcessor

# Función simple
clean = remove_wakeword("aurora abre firefox")  # -> "abre firefox"

# Procesador completo
processor = WakewordProcessor()
detected, clean_text = processor.process("aurora cierra ventana")
# detected = True
# clean_text = "cierra ventana"
```

## Ejemplos

```python
# Ejemplos de procesamiento
"aurora abre firefox"      -> "abre firefox"
"AURORA cierra ventana"    -> "cierra ventana"
"Aurora reproduce música"  -> "reproduce música"
"abre firefox"             -> "abre firefox"  (sin cambios)
"aurora"                   -> ""  (vacío)
"aurora  abre  navegador"  -> "abre navegador"  (normaliza espacios)
"aurora aurora test"       -> "aurora test"  (solo primera ocurrencia)
```

## Pruebas

Ejecutar el script de pruebas:

```bash
python scripts/test_wakeword.py
```

O probar manualmente:

```bash
# Modo interactivo
python -m src.audio.wakeword

# Con argumentos
python -m src.audio.wakeword "aurora abre firefox"
```

## Integración con el sistema principal

### Flujo de procesamiento

```
Usuario: "aurora abre firefox"
    ↓
[Wakeword] Detecta y elimina "aurora" → "abre firefox"
    ↓
[Predictor] Predice intención → intent_id='OPEN_FIREFOX'
    ↓
[Router] Decide si ejecutar
    ↓
[Executor] Ejecuta comando
```

### Logging

El sistema registra cuando el wakeword es eliminado:

```
2026-01-08 23:30:00 - INFO - Procesando: 'aurora desbloquea'
2026-01-08 23:30:00 - DEBUG - Wakeword eliminado: 'aurora desbloquea' -> 'desbloquea'
2026-01-08 23:30:00 - INFO - Predicho: IntentResult(intent_id='UNLOCK_SESSION', ...)
```

## Arquitectura

### Clase principal: `WakewordProcessor`

```python
class WakewordProcessor:
    def detect(self, text: str) -> bool:
        """Detecta si el wakeword está presente"""
        
    def remove(self, text: str) -> str:
        """Elimina el wakeword del texto"""
        
    def process(self, text: str) -> tuple[bool, str]:
        """Detecta y elimina en un solo paso"""
```

### Función de conveniencia

```python
def remove_wakeword(text: str) -> str:
    """Elimina el wakeword usando el procesador singleton"""
```

## Casos especiales

### Múltiples wakewords

Si el texto contiene el wakeword múltiples veces, solo se elimina la primera ocurrencia:

```python
"aurora aurora test" -> "aurora test"
```

### Wakeword en medio del texto

Con `remove_from_start_only: true` (recomendado), no se elimina:

```python
"abre la aurora boreal" -> "abre la aurora boreal"  (sin cambios)
```

### Wakeword solo

Si el texto solo contiene el wakeword, devuelve string vacío:

```python
"aurora" -> ""
"  aurora  " -> ""
```

## Extensibilidad

### Cambiar el wakeword

Edita `config/wakeword.yaml`:

```yaml
wakeword: "asistente"  # o cualquier otra palabra
```

### Múltiples wakewords (futura mejora)

Actualmente soporta una sola palabra. Para múltiples, modifica `WakewordProcessor.__init__()`:

```python
self.wakewords = ["aurora", "hey aurora", "ok aurora"]
```

## Notas técnicas

- **Regex**: Usa expresiones regulares para detección case-insensitive
- **Normalización**: Elimina espacios múltiples con `re.sub(r'\s+', ' ', text)`
- **Singleton**: Usa un patrón singleton para el procesador por defecto
- **Thread-safe**: La instancia singleton no es thread-safe (usar lock si es necesario)

## Archivos relacionados

- `src/audio/wakeword.py` - Implementación principal
- `config/wakeword.yaml` - Configuración
- `scripts/test_wakeword.py` - Pruebas
- `src/main.py` - Integración en el flujo principal
