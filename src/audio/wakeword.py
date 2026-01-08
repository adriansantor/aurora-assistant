#!/usr/bin/env python3
"""Módulo de detección y procesamiento de wakeword (palabra de activación)."""
import logging
import re
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


class WakewordProcessor:
    """
    Procesador de wakeword que detecta y elimina la palabra de activación del texto.
    
    """
    
    def __init__(
        self,
        wakeword: str = "aurora",
        case_sensitive: bool = False,
        remove_from_start_only: bool = True,
        config_path: Optional[str] = None
    ):
        """
        Inicializar el procesador de wakeword.
        
        Args:
            wakeword: Palabra de activación (por defecto "aurora")
            case_sensitive: Si la detección distingue mayúsculas/minúsculas
            remove_from_start_only: Si solo eliminar del inicio o de cualquier parte
            config_path: Ruta al archivo de configuración YAML (opcional)
        """
        # Cargar configuración desde archivo si existe
        if config_path:
            self._load_config(Path(config_path))
        else:
            self.wakeword = wakeword.strip()
            self.case_sensitive = case_sensitive
            self.remove_from_start_only = remove_from_start_only
    
    def _load_config(self, config_path: Path):
        """Cargar configuración desde el YAML."""
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
            
            self.wakeword = config.get('wakeword', 'aurora').strip()
            self.case_sensitive = config.get('case_sensitive', False)
            self.remove_from_start_only = config.get('remove_from_start_only', True)
            
            logger.info(f"Configuración cargada desde {config_path}")
        except FileNotFoundError:
            logger.warning(f"Archivo de configuración no encontrado: {config_path}. Usando valores por defecto.")
            self.wakeword = 'aurora'
            self.case_sensitive = False
            self.remove_from_start_only = True
        except yaml.YAMLError as e:
            logger.error(f"Error al parsear YAML: {e}. Usando valores por defecto.")
            self.wakeword = 'aurora'
            self.case_sensitive = False
            self.remove_from_start_only = True
    
    def detect(self, text: str) -> bool:
        """
        Detecta si el wakeword está presente en el texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            True si el wakeword está presente, False si no
        """
        if not text:
            return False
        
        search_text = text if self.case_sensitive else text.lower()
        search_word = self.wakeword if self.case_sensitive else self.wakeword.lower()
        
        if self.remove_from_start_only:
            # Detectar solo al inicio (con posibles espacios/puntuación)
            return search_text.strip().startswith(search_word)
        else:
            # Detectar en cualquier parte
            return search_word in search_text
    
    def remove(self, text: str) -> str:
        """
        Elimina el wakeword del texto.
        
        Args:
            text: Texto del que eliminar el wakeword
            
        Returns:
            Texto sin el wakeword, con espacios normalizados
        """
        if not text:
            return ""
        
        result = text.strip()
        
        if self.remove_from_start_only:
            # Eliminar solo del inicio
            if self.case_sensitive:
                if result.startswith(self.wakeword):
                    result = result[len(self.wakeword):].strip()
            else:
                # Usar regex para eliminar case-insensitive del inicio
                pattern = re.compile(rf"^{re.escape(self.wakeword)}\s*", re.IGNORECASE)
                result = pattern.sub("", result).strip()
        else:
            # Eliminar de cualquier parte (con límite de 1 ocurrencia para evitar efectos no deseados)
            if self.case_sensitive:
                result = result.replace(self.wakeword, "", 1).strip()
            else:
                # Regex para reemplazar case-insensitive
                pattern = re.compile(re.escape(self.wakeword), re.IGNORECASE)
                result = pattern.sub("", result, count=1).strip()
        
        # Normalizar múltiples espacios
        result = re.sub(r'\s+', ' ', result)
        
        logger.debug(f"Wakeword quitado: '{text}' -> '{result}'")
        return result
    
    def process(self, text: str) -> tuple[bool, str]:
        """
        Procesa el texto: detecta el wakeword y lo elimina si está
        
        Args:
            text: Texto a procesar
            
        Returns:
            Tupla (wakeword_detectado, texto_limpio)
        """
        detected = self.detect(text)
        clean_text = self.remove(text) if detected else text
        return detected, clean_text


# Instancia singleton por conveniencia
_processor: Optional[WakewordProcessor] = None


def get_processor(config_path: Optional[str] = None) -> WakewordProcessor:
    """
    Obtiene o crea el procesador de wakeword por defecto.
    
    Args:
        config_path: Ruta al archivo de configuración (opcional)
        
    Returns:
        Instancia de WakewordProcessor
    """
    global _processor
    if _processor is None:
        if config_path is None:
            # Usar ruta por defecto
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "wakeword.yaml"
        _processor = WakewordProcessor(config_path=str(config_path))
    return _processor


def remove_wakeword(text: str, config_path: Optional[str] = None) -> str:
    """
    Función para eliminar el wakeword del texto.
    
    Args:
        text: Texto del que eliminar el wakeword
        config_path: Ruta al archivo de configuración (opcional)
        
    Returns:
        Texto sin el wakeword
    """
    processor = get_processor(config_path)
    _, clean_text = processor.process(text)
    return clean_text


if __name__ == "__main__":
    # CLI simple para pruebas
    import sys
    
    # Inicializar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    processor = get_processor()
    
    if len(sys.argv) > 1:
        # Procesar desde argumentos de línea de comandos
        text = " ".join(sys.argv[1:])
        detected, clean_text = processor.process(text)
        print(f"Original: {text}")
        print(f"Wakeword detectado: {detected}")
        print(f"Texto limpio: {clean_text}")
    else:
        # Modo interactivo
        print("Procesador de Wakeword - Pruebas (Ctrl+C para salir)")
        print(f"Wakeword configurado: '{processor.wakeword}'")
        print()
        
        try:
            while True:
                text = input("Texto: ").strip()
                if text:
                    detected, clean_text = processor.process(text)
                    print(f"  Detectado: {detected}")
                    print(f"  Limpio: {clean_text}")
                    print()
        except KeyboardInterrupt:
            print("\n¡Adiós!")
