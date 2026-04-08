"""
Validador de campos obligatorios (schemeID, LineCountNumeric)
"""

import xml.etree.ElementTree as ET

class RequiredFieldsValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.recommendations = []

    def validate(self, xml_content: str) -> dict:
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        self.errors = []
        self.warnings = []
        self.recommendations = []

        try:
            root = ET.fromstring(xml_content)
            namespaces = self._extract_namespaces(root)

            self._validate_customer_scheme_id(root, namespaces)
            self._validate_line_count_consistency(root, namespaces)

        except ET.ParseError as e:
            result["errors"].append(f"Error al parsear XML: {e}")
            result["valid"] = False

        result["errors"].extend(self.errors)
        result["warnings"].extend(self.warnings)
        result["recommendations"].extend(self.recommendations)
        if result["errors"]:
            result["valid"] = False
        return result

    def _validate_customer_scheme_id(self, root, ns):
        # Buscar usando namespaces o sin ellos
        company_id = None
        # Primero con namespace
        company_id = root.find('.//cac:AccountingCustomerParty//cac:PartyLegalEntity/cbc:CompanyID', namespaces=ns)
        if company_id is None:
            # Buscar sin namespace
            for elem in root.findall('.//AccountingCustomerParty//PartyLegalEntity/CompanyID'):
                company_id = elem
                break
        if company_id is not None and company_id.text:
            scheme_id = company_id.get('schemeID')
            if scheme_id == '5':
                self.errors.append("❌ El 'schemeID' del NIT del cliente es '5', debe ser '1' (NIT colombiano) o '2' (persona jurídica extranjera).")
                self.recommendations.append("Cambiar schemeID='1' para NIT colombiano.")
            elif scheme_id is None:
                self.warnings.append("⚠️ El 'schemeID' del NIT del cliente está ausente. Se recomienda usar '1'.")

    def _validate_line_count_consistency(self, root, ns):
        line_count_elem = root.find('.//cbc:LineCountNumeric', namespaces=ns)
        if line_count_elem is None:
            line_count_elem = root.find('.//LineCountNumeric')
        if line_count_elem is None or not line_count_elem.text:
            return
        try:
            line_count = int(line_count_elem.text)
        except ValueError:
            return

        ar_xml = self._extract_application_response(root, ns)
        if not ar_xml:
            return

        try:
            ar_root = ET.fromstring(ar_xml)
            ar_ns = self._extract_namespaces(ar_root)
            line_ids = []
            for line_resp in ar_root.findall('.//cac:LineResponse', namespaces=ar_ns):
                line_id_elem = line_resp.find('.//cbc:LineID', namespaces=ar_ns)
                if line_id_elem is None:
                    line_id_elem = line_resp.find('.//LineID')
                if line_id_elem is not None and line_id_elem.text:
                    try:
                        line_ids.append(int(line_id_elem.text))
                    except ValueError:
                        pass
            if line_ids:
                max_line_id = max(line_ids)
                if max_line_id > line_count:
                    self.errors.append(f"❌ ApplicationResponse reporta líneas hasta {max_line_id}, pero la factura tiene solo {line_count} líneas.")
                    self.recommendations.append("Corregir LineCountNumeric o eliminar líneas sobrantes en ApplicationResponse.")
                elif max_line_id < line_count:
                    self.warnings.append(f"⚠️ La factura tiene {line_count} líneas, pero ApplicationResponse solo reporta hasta {max_line_id}.")
        except Exception:
            pass

    def _extract_application_response(self, root, ns):
        # Buscar en cbc:Description con namespace o sin él
        for desc in root.findall('.//cbc:Description', namespaces=ns):
            if desc.text and '<ApplicationResponse' in desc.text:
                start = desc.text.find('<ApplicationResponse')
                if start == -1:
                    continue
                end = desc.text.find('</ApplicationResponse>')
                if end == -1:
                    continue
                return desc.text[start:end+21]
        # Fallback sin namespace
        for desc in root.findall('.//Description'):
            if desc.text and '<ApplicationResponse' in desc.text:
                start = desc.text.find('<ApplicationResponse')
                if start == -1:
                    continue
                end = desc.text.find('</ApplicationResponse>')
                if end == -1:
                    continue
                return desc.text[start:end+21]
        return ""

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