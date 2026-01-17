# Sistema de Reconocimiento de Voz del Hablante

Aurora ahora incluye un sistema de verificación de hablante que permite que el asistente **solo reconozca tu voz**. Esto añade una capa de seguridad adicional, asegurando que solo tú puedas controlar a Aurora mediante comandos de voz.

## 🎯 Características

- **Entrenamiento acumulativo**: Cuantas más muestras de voz captures, más preciso será el reconocimiento
- **Persistencia**: El modelo se guarda automáticamente y se carga en futuros usos
- **Flexible**: Puedes entrenar múltiples veces para mejorar la precisión
- **Configurable**: Ajusta el umbral de confianza según tus necesidades

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
pip install librosa
# O instalar todas las dependencias
pip install -r requirements.txt
```

### 2. Entrenar el modelo

```bash
# Entrenamiento básico (5 muestras)
python -m src.main --train-speaker

# O usa el script dedicado para más opciones
python scripts/train_speaker.py --samples 10
```

Durante el entrenamiento:
- Habla claramente cuando se te indique
- Di frases **diferentes** en cada muestra
- Mantén un tono de voz natural
- Cada grabación dura 3-10 segundos

### 3. Usar Aurora con verificación de voz

```bash
# Modo voz con verificación (solo tu voz)
python -m src.main --voice --single-voice

# Modo continuo con verificación
python -m src.main --voice --continuous --single-voice

# Modo normal sin verificación (acepta cualquier voz)
python -m src.main --voice --all-voices
```

## 📖 Guía Detallada

### Entrenamiento

#### Opción 1: Desde el main

```bash
# Entrenamiento rápido (5 muestras)
python -m src.main --train-speaker

# Entrenamiento con más muestras
python -m src.main --train-speaker --training-samples 10
```

#### Opción 2: Script dedicado (recomendado)

```bash
# Entrenamiento básico
python scripts/train_speaker.py

# Entrenamiento personalizado
python scripts/train_speaker.py --samples 15

# Resetear modelo y empezar desde cero
python scripts/train_speaker.py --reset --samples 10

# Probar el modelo actual
python scripts/train_speaker.py --test
```

### Consejos para un Buen Entrenamiento

✅ **Haz esto:**
- Entrena en el mismo ambiente donde usarás Aurora
- Usa diferentes frases (ejemplos de comandos reales)
- Habla con naturalidad, no fuerces la voz
- Captura al menos 5-10 muestras inicialmente
- Añade más muestras si experimentas falsos rechazos

❌ **Evita esto:**
- No uses la misma frase en todas las muestras
- No cambies drásticamente tu tono de voz
- No entrenes con mucho ruido de fondo
- No hables demasiado cerca o lejos del micrófono

### Ejemplos de Frases para Entrenamiento

```
"Aurora, abre el navegador web"
"Aurora, muéstrame el clima de hoy"
"Hola Aurora, cierra todas las ventanas"
"Aurora, dime qué hora es"
"Aurora, reproduce música relajante"
"Aurora, apaga la computadora en diez minutos"
"Aurora, abre el editor de código"
"Aurora, cuál es mi calendario para hoy"
```

## 🎛️ Configuración

El archivo `config/speaker.yaml` controla el comportamiento del sistema:

```yaml
speaker_verification:
  # Umbral de confianza (0.0 - 1.0)
  # Valores más altos = más estricto
  threshold: 0.5
  
  # Número de coeficientes MFCC
  n_mfcc: 13
  
  # Duración máxima de audio (segundos)
  max_duration: 10.0
  
  # Ruta del modelo
  model_path: "models/speaker_model.pkl"
```

### Ajustar el Umbral

- **threshold: 0.3-0.4**: Menos estricto, puede aceptar voces similares
- **threshold: 0.5**: Balance (recomendado)
- **threshold: 0.6-0.8**: Más estricto, puede rechazar tu propia voz ocasionalmente

## 🔧 Uso Avanzado

### Entrenamiento Acumulativo

El sistema permite entrenar múltiples veces, y las muestras se **acumulan**:

```bash
# Primera sesión: 5 muestras
python scripts/train_speaker.py --samples 5

# Segunda sesión: +10 muestras (total: 15)
python scripts/train_speaker.py --samples 10

# Tercera sesión: +5 muestras (total: 20)
python scripts/train_speaker.py --samples 5
```

Cada sesión **mejora** el modelo. Mientras más muestras, más preciso.

### Resetear el Modelo

Si quieres empezar desde cero:

```bash
# Eliminar modelo y entrenar desde cero
python scripts/train_speaker.py --reset --samples 10
```

O manualmente:

```bash
# Eliminar el archivo del modelo
rm models/speaker_model.pkl
```

### Verificar el Modelo

Para probar si el modelo te reconoce:

```bash
python scripts/train_speaker.py --test
```

Esto capturará una muestra de tu voz y te dirá si te reconoce como autorizado.

## 🎮 Modos de Operación

### Modo 1: Solo tu voz (--single-voice)

```bash
python -m src.main --voice --single-voice
```

- ✅ Aurora solo responderá a tu voz
- ❌ Rechazará otras voces
- Requiere modelo entrenado

### Modo 2: Todas las voces (--all-voices o por defecto)

```bash
python -m src.main --voice --all-voices
# O simplemente:
python -m src.main --voice
```

- ✅ Aurora responderá a cualquier voz
- Comportamiento original
- No requiere entrenamiento

### Modo 3: Entrenamiento

```bash
python -m src.main --train-speaker
```

- Captura muestras de tu voz
- Entrena/actualiza el modelo
- Guarda automáticamente

## 🛠️ Troubleshooting

### "librosa no está instalado"

```bash
pip install librosa
```

### "El modelo no está entrenado"

Debes entrenar primero:

```bash
python -m src.main --train-speaker
```

### "Hablante no autorizado" (falso rechazo)

Posibles soluciones:
1. **Entrena más muestras**:
   ```bash
   python scripts/train_speaker.py --samples 10
   ```

2. **Reduce el umbral** en `config/speaker.yaml`:
   ```yaml
   threshold: 0.4  # era 0.5
   ```

3. **Resetea y reentrena** en el mismo ambiente:
   ```bash
   python scripts/train_speaker.py --reset --samples 15
   ```

### Acepta voces de otras personas (falso positivo)

1. **Aumenta el umbral** en `config/speaker.yaml`:
   ```yaml
   threshold: 0.6  # era 0.5
   ```

2. **Entrena con más muestras** para mejor diferenciación:
   ```bash
   python scripts/train_speaker.py --samples 15
   ```

### Error de micrófono

```bash
# Verificar micrófonos disponibles
python -m src.audio.mic

# Verificar permisos de audio en tu sistema
```

## 📊 Cómo Funciona

El sistema utiliza:

1. **MFCC (Mel-Frequency Cepstral Coefficients)**: Extrae características únicas de tu voz
2. **SVM (Support Vector Machine)**: Modelo de clasificación que aprende tu patrón vocal
3. **Scaler**: Normaliza las características para mejor precisión
4. **Entrenamiento incremental**: Cada nueva sesión mejora el modelo

El flujo es:

```
Audio → Extracción MFCC → Normalización → SVM → Decisión (Autorizado/No autorizado)
```

## 🎯 Recomendaciones

- **Mínimo recomendado**: 5 muestras
- **Óptimo**: 10-15 muestras
- **Para máxima precisión**: 20+ muestras
- **Reentrena** si cambias de micrófono o ambiente
- **Usa --single-voice** en ambientes compartidos
- **Usa --all-voices** para demos o ambientes privados

## 📝 Ejemplo Completo

```bash
# 1. Entrenar el modelo
python scripts/train_speaker.py --samples 10

# 2. Probar que funciona
python scripts/train_speaker.py --test

# 3. Usar Aurora con tu voz
python -m src.main --voice --continuous --single-voice

# 4. Si necesitas más precisión, añade más muestras
python scripts/train_speaker.py --samples 10  # ahora tienes 20 total

# 5. Para resetear y empezar de nuevo
python scripts/train_speaker.py --reset --samples 15
```

## 🔐 Seguridad

**Importante**: Este sistema NO es criptográficamente seguro. Es una capa de comodidad y seguridad básica, pero no debe ser tu única línea de defensa para operaciones críticas.

**Limitaciones**:
- Grabaciones de tu voz podrían engañar al sistema
- Voces muy similares podrían ser aceptadas
- No protege contra ataques de reproducción

**Recomendaciones**:
- Usa permisos del sistema (`config/security.yaml`) para comandos sensibles
- No confíes únicamente en la verificación de voz para operaciones críticas
- Considera el sistema como una capa adicional de seguridad, no la única

---

¿Preguntas o problemas? Consulta los logs en modo debug:

```bash
python -m src.main --voice --single-voice 2>&1 | tee aurora.log
```
