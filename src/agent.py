import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from .config import LLM_CONFIG, DIAN_SCHEMAS
from .knowledge_manager import KnowledgeManager
from .xml_validator import DianXMLValidator
from .container_validator import ContainerValidator
from .nested_document_validator import NestedDocumentValidator
from .application_response_validator import ApplicationResponseValidator
from .required_fields_validator import RequiredFieldsValidator
from .utils import normalize_text

logger = logging.getLogger(__name__)

class DianSupportAgent:
    def __init__(self, knowledge_base_path: Optional[str] = None):
        self.knowledge_manager = KnowledgeManager(knowledge_base_path)
        self.validator = DianXMLValidator(DIAN_SCHEMAS)
        self.container_validator = ContainerValidator()
        self.nested_validator = NestedDocumentValidator()
        self.ar_validator = ApplicationResponseValidator()
        self.required_validator = RequiredFieldsValidator()
        self.conversation_history = []
        logger.info("Agente de soporte DIAN inicializado")

    def analyze_document(self, document_content: str, file_type: str = "xml", filename: str = "documento") -> Dict[str, Any]:
        result = {
            "success": False,
            "filename": filename,
            "file_type": file_type,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "validations": {}
        }
        document_content = normalize_text(document_content)

        if file_type == "xml":
            encoding_check = self.validator.validate_encoding(document_content)
            result["validations"]["encoding"] = encoding_check
            if not encoding_check["valid"]:
                result["errors"].append("Problemas de codificación UTF-8 detectados")
                result["recommendations"].append("Regenerar XML con codificación UTF-8 correcta")

            structure_check = self.validator.validate_structure(document_content)
            result["validations"]["structure"] = structure_check
            if not structure_check["valid"]:
                result["errors"].extend(structure_check["errors"])

            container_check = self.container_validator.validate(document_content)
            result["validations"]["container"] = container_check
            if not container_check["valid"]:
                result["errors"].extend(container_check["errors"])
                result["warnings"].extend(container_check["warnings"])
                result["recommendations"].extend(container_check["recommendations"])

            nested_check = self.nested_validator.validate(document_content)
            result["validations"]["nested_documents"] = nested_check
            if not nested_check["valid"]:
                result["errors"].extend(nested_check["errors"])
                result["warnings"].extend(nested_check["warnings"])
                result["recommendations"].extend(nested_check["recommendations"])

            required_check = self.required_validator.validate(document_content)
            result["validations"]["required_fields"] = required_check
            if not required_check["valid"]:
                result["errors"].extend(required_check["errors"])
                result["warnings"].extend(required_check["warnings"])
                result["recommendations"].extend(required_check["recommendations"])

            ar_content = self._extract_application_response_from_content(document_content)
            if ar_content:
                ar_check = self.ar_validator.validate(ar_content)
                result["validations"]["application_response"] = ar_check
                if not ar_check["valid"]:
                    result["errors"].extend(ar_check["errors"])
                    result["warnings"].extend(ar_check["warnings"])
                    result["recommendations"].extend(ar_check["recommendations"])

        result["success"] = len(result["errors"]) == 0
        return result

    def _extract_application_response_from_content(self, content: str) -> str:
        import re
        if content.strip().startswith('<ApplicationResponse'):
            return content
        match = re.search(r'<!\[CDATA\[.*?(<ApplicationResponse.*?</ApplicationResponse>).*?\]\]>', content, re.DOTALL)
        if match:
            return match.group(1)
        match2 = re.search(r'<ApplicationResponse.*?</ApplicationResponse>', content, re.DOTALL)
        return match2.group(0) if match2 else ""

    def generate_response(self, user_input: str, document_analysis: Optional[Dict] = None) -> str:
        response = "🛑 DIAGNÓSTICO DEL ERROR\n\n"
        if document_analysis and document_analysis.get("errors"):
            response += f"Problema principal: {document_analysis['errors'][0]}\n\n"
        response += "🔍 VERIFICACIÓN PASO A PASO:\n\n"
        if document_analysis:
            for error in document_analysis.get("errors", [])[:5]:
                response += f"❌ {error}\n"
        response += "\n✅ RECOMENDACIÓN TÉCNICA:\n\n"
        if document_analysis and document_analysis.get("recommendations"):
            for rec in document_analysis["recommendations"][:5]:
                response += f"- {rec}\n"
        else:
            response += "- Revisar codificación UTF-8 del XML\n"
            response += "- Verificar sumatorias de IVA y retenciones\n"
            response += "- Asegurar que todos los campos obligatorios estén presentes\n"
            response += "- Comprobar que AttachedDocument contenga Invoice dentro de CDATA\n"
        return response

    def load_manual(self, file_path: str) -> bool:
        try:
            self.knowledge_manager.add_document(file_path)
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            return False

    def load_manuals_from_folder(self, folder_path: str) -> Dict[str, bool]:
        results = {}
        folder = Path(folder_path)
        if not folder.exists():
            return {"error": "Folder no existe"}
        for file_path in folder.iterdir():
            if file_path.suffix.lower() in ['.pdf', '.txt', '.xml', '.json', '.xlsx', '.xls']:
                results[file_path.name] = self.load_manual(str(file_path))
        return results

    def list_manuals(self) -> list:
        return self.knowledge_manager.list_documents()

    def remove_manual(self, filename: str) -> bool:
        return self.knowledge_manager.remove_document(filename)