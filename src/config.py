"""
Configuración central del agente
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Rutas base - ADAPTADO A TU UBICACIÓN
BASE_DIR = Path(r"G:\Mi unidad\001 - Organizado\0.1 - Previsora\7- Automatizaciones\5- bot dian")
DATA_DIR = BASE_DIR / "data"
MANUALES_DIR = DATA_DIR / "manuales"
EJEMPLOS_DIR = DATA_DIR / "ejemplos"
XSD_DIR = DATA_DIR / "xsd"
PLANTILLAS_DIR = DATA_DIR / "plantillas"
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"
LOG_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"

# Crear directorios si no existen
for dir_path in [MANUALES_DIR, EJEMPLOS_DIR, XSD_DIR, PLANTILLAS_DIR, KNOWLEDGE_DIR, LOG_DIR, OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Configuración del LLM
LLM_CONFIG = {
    "type": "local",  # "local" o "api"
    "local_model": "mistral",  # modelo de Ollama
    "api_type": "openai",  # "openai" o "anthropic"
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "temperature": 0.1,  # Baja temperatura para respuestas precisas
    "max_tokens": 4096
}

# Validadores DIAN - BUSCA XSD EN LA CARPETA data/xsd
DIAN_SCHEMAS = {
    "invoice": XSD_DIR / "ubl-invoice-2.1.xsd",
    "attached_document": XSD_DIR / "ubl-attached-document-2.1.xsd",
    "application_response": XSD_DIR / "ubl-application-response-2.1.xsd"
}

# Reglas de negocio DIAN
DIAN_RULES = {
    "tax_codes": {
        "01": "IVA",
        "02": "Consumo",
        "03": "Industria y Comercio",
        "04": "Timbre",
        "05": "ReteIVA",
        "06": "ReteFuente",
        "07": "ICA"
    },
    "currency": "COP",
    "decimal_precision": 2,
    "cufe_algorithm": "SHA-384",
    "response_codes": {
        "00": "Aceptado por la DIAN",
        "02": "Documento validado por la DIAN",
        "03": "Documento rechazado por la DIAN",
        "RUT01": "Validación de RUT pendiente"
    }
}

# Logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOG_DIR / "agent.log"
}