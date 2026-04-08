"""
Valida que los documentos fiscales (Invoice, CreditNote, DebitNote)
estén dentro de un AttachedDocument cuando sea requerido.
"""

import xml.etree.ElementTree as ET

class MissingContainerValidator:
    def validate(self, xml_content: str) -> dict:
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "document_type": None
        }
        try:
            root = ET.fromstring(xml_content)
            tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            result["document_type"] = tag

            # Si el documento raíz es Invoice, CreditNote o DebitNote y NO está dentro de AttachedDocument
            if tag in ["Invoice", "CreditNote", "DebitNote"]:
                # Verificar si el elemento padre es AttachedDocument (difícil aquí, mejor usar contexto)
                # En este caso, el XML no tiene contenedor, emitimos advertencia
                result["warnings"].append(f"El documento raíz es '{tag}' sin contenedor AttachedDocument. Para envíos a la DIAN se recomienda usar AttachedDocument como raíz.")
                result["valid"] = False  # o True si solo quieres advertencia
                result["errors"].append(f"❌ El XML debe tener <AttachedDocument> como elemento raíz, no '{tag}'. Revise el anexo técnico DIAN.")
        except Exception as e:
            result["errors"].append(f"Error al analizar: {e}")
            result["valid"] = False
        return result
