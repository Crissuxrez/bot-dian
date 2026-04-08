"""
Validador de presencia de contenedor AttachedDocument
"""

import xml.etree.ElementTree as ET

class ContainerValidator:
    def validate(self, xml_content: str) -> dict:
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "root_tag": None
        }
        try:
            root = ET.fromstring(xml_content)
            tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            result["root_tag"] = tag

            if tag == "Invoice":
                result["valid"] = False
                result["errors"].append("❌ El XML raíz es 'Invoice'. Para envíos a la DIAN se requiere que la factura esté dentro de un contenedor 'AttachedDocument'.")
                result["recommendations"].append("Envolver el Invoice dentro de un AttachedDocument según el anexo técnico DIAN.")
            elif tag == "AttachedDocument":
                result["warnings"].append("✅ El documento usa el contenedor AttachedDocument correctamente.")
            else:
                result["warnings"].append(f"⚠️ Tipo de documento raíz desconocido: {tag}")
        except ET.ParseError as e:
            result["valid"] = False
            result["errors"].append(f"Error al parsear XML: {e}")
        return result