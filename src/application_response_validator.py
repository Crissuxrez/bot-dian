"""
Validador específico para ApplicationResponse (con manejo robusto de namespaces)
"""

import xml.etree.ElementTree as ET

class ApplicationResponseValidator:
    def validate(self, xml_content: str) -> dict:
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "response_code": None,
            "line_errors": []
        }
        try:
            root = ET.fromstring(xml_content)
            ns = self._extract_namespaces(root)

            # Buscar ResponseCode
            resp_code = root.find('.//cbc:ResponseCode', namespaces=ns)
            if resp_code is None:
                resp_code = root.find('.//ResponseCode')
            if resp_code is not None:
                code = resp_code.text
                result["response_code"] = code
                if code in ["02", "00"]:
                    result["warnings"].append(f"✅ Documento aceptado por la DIAN (ResponseCode: {code})")
                elif code in ["03", "FAJ43b"]:
                    result["errors"].append(f"❌ Documento rechazado por la DIAN (ResponseCode: {code})")
                    result["valid"] = False
                elif code == "RUT01":
                    result["warnings"].append("⚠️ Validación de RUT no disponible temporalmente.")
            else:
                result["errors"].append("❌ No se encontró cbc:ResponseCode en ApplicationResponse.")
                result["valid"] = False

            # Buscar LineResponse
            line_responses = root.findall('.//cac:LineResponse', namespaces=ns)
            if not line_responses:
                line_responses = root.findall('.//LineResponse')
            for line_resp in line_responses:
                line_id = line_resp.find('.//cbc:LineID', namespaces=ns)
                if line_id is None:
                    line_id = line_resp.find('.//LineID')
                line_code = line_resp.find('.//cbc:ResponseCode', namespaces=ns)
                if line_code is None:
                    line_code = line_resp.find('.//ResponseCode')
                line_desc = line_resp.find('.//cbc:Description', namespaces=ns)
                if line_desc is None:
                    line_desc = line_resp.find('.//Description')
                if line_code is not None and line_code.text not in ["0000", "00"]:
                    num = line_id.text if line_id is not None else "?"
                    desc = line_desc.text if line_desc is not None else "Sin descripción"
                    error_msg = f"Error en línea {num}: {line_code.text} - {desc}"
                    result["line_errors"].append(error_msg)
                    result["errors"].append(f"❌ {error_msg}")
                    result["valid"] = False

        except ET.ParseError as e:
            result["errors"].append(f"Error al parsear ApplicationResponse: {e}")
            result["valid"] = False
        return result

    def _extract_namespaces(self, elem):
        namespaces = {}
        for attr, value in elem.attrib.items():
            if attr.startswith('xmlns'):
                if ':' in attr:
                    prefix = attr.split(':')[1]
                else:
                    prefix = ''
                namespaces[prefix] = value
        if 'cbc' not in namespaces:
            namespaces['cbc'] = 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        if 'cac' not in namespaces:
            namespaces['cac'] = 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
        return namespaces