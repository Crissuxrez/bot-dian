"""
Utilidades para el agente
"""
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """
    Normaliza texto corrigiendo problemas comunes de codificación
    """
    if not text:
        return text
    
    # Patrones comunes de doble codificación UTF-8 -> ISO-8859-1
    replacements = [
        (r'Ã¡', 'á'), (r'Ã©', 'é'), (r'Ã­', 'í'), (r'Ã³', 'ó'), (r'Ãº', 'ú'),
        (r'Ã±', 'ñ'), (r'Ã‘', 'Ñ'), (r'Ã„', 'Ä'), (r'Ã–', 'Ö'), (r'Ãœ', 'Ü'),
        (r'Â¡', '¡'), (r'Â¿', '¿'), (r'Âº', 'º'), (r'Âª', 'ª'),
        (r'â€™', "'"), (r'â€œ', '"'), (r'â€\x9d', '"'), (r'â€¦', '...'),
        (r'Â', '')
    ]
    
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    
    return text


def detect_encoding_issues(text: str) -> Dict[str, Any]:
    """
    Detecta problemas de codificación en un texto
    """
    result = {
        "has_issues": False,
        "issues": [],
        "suggestions": []
    }
    
    problematic_patterns = [
        (r'Ã¡|Ã©|Ã­|Ã³|Ãº', 'acentos'),
        (r'Ã±|Ã‘', 'ñ/Ñ'),
        (r'Â', 'carácter Â sobrante'),
        (r'â€', 'caracteres especiales')
    ]
    
    for pattern, description in problematic_patterns:
        if re.search(pattern, text):
            result["has_issues"] = True
            result["issues"].append(f"Patrón encontrado: {pattern} - {description}")
            result["suggestions"].append("Regenerar el documento con codificación UTF-8 correcta")
    
    return result


def save_analysis_result(content: str, filename: str, analysis: Dict) -> Path:
    """
    Guarda el resultado del análisis en la carpeta output
    """
    from .config import OUTPUT_DIR
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
    output_file = OUTPUT_DIR / f"analysis_{safe_filename}_{timestamp}.json"
    
    result = {
        "timestamp": timestamp,
        "filename": filename,
        "analysis": analysis,
        "content_preview": content[:1000] if content else ""
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Análisis guardado en {output_file}")
    return output_file


def format_currency(value: float) -> str:
    """Formatea un valor en COP"""
    return f"${value:,.0f} COP"


def extract_xml_from_attached(xml_content: str) -> Optional[str]:
    """
    Extrae el XML interno de un AttachedDocument
    """
    try:
        # Buscar el contenido dentro de <cbc:Description><![CDATA[...]]></cbc:Description>
        pattern = r'<!\[CDATA\[(.*?)\]\]>'
        match = re.search(pattern, xml_content, re.DOTALL)
        if match:
            return match.group(1)
    except Exception as e:
        logger.error(f"Error extrayendo XML interno: {e}")
    
    return None


def validate_prefix_range(prefix: str, from_num: int, to_num: int, current: int) -> Dict[str, Any]:
    """
    Valida que el número de factura esté dentro del rango autorizado
    """
    result = {
        "valid": False,
        "message": ""
    }
    
    if current < from_num:
        result["message"] = f"Factura {prefix}{current} está por debajo del rango autorizado ({from_num})"
    elif current > to_num:
        result["message"] = f"Factura {prefix}{current} excede el rango autorizado ({to_num})"
    else:
        result["valid"] = True
        result["message"] = f"Factura dentro del rango autorizado: {from_num} - {to_num}"
    
    return result