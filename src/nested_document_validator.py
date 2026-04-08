"""
Validador de documentos anidados dentro de AttachedDocument
"""

import xml.etree.ElementTree as ET

class NestedDocumentValidator:
    def validate(self, xml_content: str) -> dict:
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "has_invoice": False,
            "has_application_response": False
        }
        try:
            root = ET.fromstring(xml_content)
            tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            if tag != "AttachedDocument":
                result["warnings"].append("No es un AttachedDocument, no se validan documentos anidados.")
                return result

            # Extraer namespaces del elemento raíz
            namespaces = self._extract_namespaces(root)

            # Buscar elementos cbc:Description usando los namespaces extraídos
            desc_elements = root.findall('.//cbc:Description', namespaces=namespaces)
            # Si no se encontraron con el prefijo, intentar buscar solo 'Description' (sin namespace)
            if not desc_elements:
                desc_elements = root.findall('.//Description')

            for desc in desc_elements:
                if desc.text is None:
                    continue
                text = desc.text
                if '<Invoice' in text and not result["has_invoice"]:
                    result["has_invoice"] = True
                    result["warnings"].append("✅ Se encontró Invoice dentro del AttachedDocument.")
                if '<ApplicationResponse' in text and not result["has_application_response"]:
                    result["has_application_response"] = True
                    result["warnings"].append("✅ Se encontró ApplicationResponse dentro del AttachedDocument.")

            if not result["has_invoice"]:
                result["errors"].append("❌ El AttachedDocument no contiene ningún Invoice dentro de cbc:Description.")
                result["valid"] = False
                result["recommendations"].append("Incluir la factura electrónica (Invoice) dentro de un CDATA en cbc:Description.")

        except ET.ParseError as e:
            result["valid"] = False
            result["errors"].append(f"Error al parsear XML: {e}")
        return result

    def _extract_namespaces(self, elem):
        """Extrae los namespaces del elemento y sus ancestros (simple)."""
        namespaces = {}
        # Buscar en el propio elemento
        for attr, value in elem.attrib.items():
            if attr.startswith('xmlns'):
                if ':' in attr:
                    prefix = attr.split(':')[1]
                else:
                    prefix = ''
                namespaces[prefix] = value
        # Agregar prefijos por defecto si no existen (para que las búsquedas funcionen)
        if 'cbc' not in namespaces:
            namespaces['cbc'] = 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        if 'cac' not in namespaces:
            namespaces['cac'] = 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
        return namespaces