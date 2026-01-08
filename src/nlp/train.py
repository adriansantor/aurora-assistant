"""Módulo de entrenamiento de modelo. Entrena clasificador de intenciones desde ejemplos etiquetados."""
import json
import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import pandas as pd

logger = logging.getLogger(__name__)


class TrainingError(Exception):
    """Se lanza cuando el entrenamiento no puede completarse."""
    pass


def load_training_data(csv_path: str) -> tuple[list[str], list[str]]:
    """Cargar datos de entrenamiento desde CSV con columnas 'text' e 'intent'. Lanza TrainingError si inválido."""
    csv_path = Path(csv_path)
    
    if not csv_path.exists():
        raise TrainingError(f"Datos de entrenamiento no encontrados: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise TrainingError(f"Fallo al leer CSV: {e}")
    
    # Verificar columnas requeridas
    if 'text' not in df.columns or 'intent' not in df.columns:
        raise TrainingError(
            f"CSV debe tener columnas 'text' e 'intent'. "
            f"Encontradas: {list(df.columns)}"
        )
    
    # Eliminar filas vacías
    df = df.dropna(subset=['text', 'intent'])
    df = df[df['text'].str.strip() != '']
    
    if len(df) == 0:
        raise TrainingError("No se encontraron datos de entrenamiento válidos")
    
    texts = df['text'].tolist()
    intents = df['intent'].tolist()
    
    logger.info(f"Cargados {len(texts)} ejemplos de entrenamiento")
    logger.info(f"Intenciones únicas: {set(intents)}")
    
    return texts, intents


def train_model(
    texts: list[str],
    intents: list[str],
    random_state: int = 42,
) -> tuple[TfidfVectorizer, LogisticRegression, dict, np.ndarray, np.ndarray]:
    """Entrenar vectorizador y clasificador. Lanza TrainingError si el entrenamiento falla."""
    if len(texts) != len(intents):
        raise TrainingError("texts e intents deben tener la misma longitud")
    
    if len(texts) == 0:
        raise TrainingError("No se proporcionaron datos de entrenamiento")
    
    # Vectorizar textos
    try:
        logger.info("Vectorizando textos...")
        vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents='unicode',
            stop_words='english',
            max_features=5000,
            min_df=1,
            max_df=0.9,
        )
        X = vectorizer.fit_transform(texts)
        logger.info(f"Creadas {X.shape[1]} características")
    except Exception as e:
        raise TrainingError(f"Vectorización fallida: {e}")
    
    # Codificar etiquetas
    try:
        logger.info("Codificando etiquetas...")
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(intents)
        
        # Crear label_map: index -> intent_id
        label_map = {str(i): intent for i, intent in enumerate(label_encoder.classes_)}
        logger.info(f"Creado label map: {label_map}")
    except Exception as e:
        raise TrainingError(f"Codificación de etiquetas fallida: {e}")
    
    # Entrenar modelo
    try:
        logger.info("Entrenando LogisticRegression...")
        model = LogisticRegression(
            random_state=random_state,
            max_iter=1000,
            solver='lbfgs',
            n_jobs=-1,
        )
        model.fit(X, y)
        logger.info(f"Modelo entrenado. Clases: {model.classes_}")
    except Exception as e:
        raise TrainingError(f"Entrenamiento del modelo fallido: {e}")
    
    
    return vectorizer, model, label_map, X, y


def save_artifacts(
    vectorizer: TfidfVectorizer,
    model: LogisticRegression,
    label_map: dict,
    X: np.ndarray,
    y: np.ndarray,
    output_dir: str = None,
) -> dict:
    """Guardar artefactos de entrenamiento. Lanza TrainingError si el guardado falla."""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent  # raíz del proyecto
    else:
        output_dir = Path(output_dir)
    
    # Crear directorios
    models_dir = output_dir / "models"
    processed_dir = output_dir / "data" / "processed"
    
    models_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    artifacts = {}
    
    # Guardar vectorizador
    try:
        vectorizer_path = models_dir / "vectorizer.pkl"
        joblib.dump(vectorizer, vectorizer_path)
        logger.info(f"Guardado vectorizador: {vectorizer_path}")
        artifacts['vectorizer'] = str(vectorizer_path)
    except Exception as e:
        raise TrainingError(f"Fallo al guardar vectorizador: {e}")
    
    # Guardar modelo
    try:
        model_path = models_dir / "intent_model.pkl"
        joblib.dump(model, model_path)
        logger.info(f"Guardado modelo: {model_path}")
        artifacts['model'] = str(model_path)
    except Exception as e:
        raise TrainingError(f"Fallo al guardar modelo: {e}")
    
    # Guardar label_map
    try:
        label_map_path = processed_dir / "label_map.json"
        with open(label_map_path, 'w') as f:
            json.dump(label_map, f, indent=2)
        logger.info(f"Guardado label_map: {label_map_path}")
        artifacts['label_map'] = str(label_map_path)
    except Exception as e:
        raise TrainingError(f"Fallo al guardar label_map: {e}")
    
    # Guardar datos de entrenamiento (para referencia)
    try:
        X_path = processed_dir / "X_train.npy"
        y_path = processed_dir / "y_train.npy"
        np.save(X_path, X)
        np.save(y_path, y)
        logger.info(f"Guardados datos de entrenamiento: {X_path}, {y_path}")
        artifacts['X_train'] = str(X_path)
        artifacts['y_train'] = str(y_path)
    except Exception as e:
        logger.warning(f"Fallo al guardar datos de entrenamiento: {e}")
    
    return artifacts


def train_and_save(
    csv_path: str = None,
    output_dir: str = None,
) -> dict:
    """Pipeline completo de entrenamiento: cargar, entrenar, guardar. Lanza TrainingError si falla algún paso."""
    if csv_path is None:
        csv_path = Path(__file__).parent.parent.parent / "data" / "raw" / "intents.csv"
    
    # Cargar datos
    texts, intents = load_training_data(csv_path)
    
    # Train
    vectorizer, model, label_map, X, y = train_model(texts, intents)
    
    # Save
    artifacts = save_artifacts(
        vectorizer, model, label_map, X, y,
        output_dir=output_dir,
    )
    
    return artifacts


def main():
    """Punto de entrada CLI."""
    import sys
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Obtener rutas de argumentos o usar valores por defecto
        csv_path = sys.argv[1] if len(sys.argv) > 1 else None
        output_dir = sys.argv[2] if len(sys.argv) > 2 else None
        
        logger.info("Iniciando entrenamiento del modelo...")
        artifacts = train_and_save(csv_path, output_dir)
        
        logger.info("\n" + "="*60)
        logger.info("[OK] Entrenamiento completado exitosamente!")
        logger.info("="*60)
        logger.info("\nArtefactos guardados:")
        for name, path in artifacts.items():
            logger.info(f"  {name}: {path}")
        logger.info("\n¡Ahora puedes usar predict.py!")
        
        return 0
        
    except TrainingError as e:
        logger.error(f"\n[ERROR] Entrenamiento fallido: {e}")
        return 1
    except Exception as e:
        logger.error(f"\n[ERROR] Error inesperado: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
