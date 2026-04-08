"""
Validador técnico de XML contra XSD y reglas DIAN
"""
import re
import xml.etree.ElementTree as ET
from decimal import Decimal, getcontext, ROUND_HALF_UP
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import logging

from .utils import detect_encoding_issues, normalize_text

logger = logging.getLogger(__name__)

# Configurar precisión decimal
getcontext().prec = 28


class DianXMLValidator:
    """
    Validador de XML de facturación electrónica DIAN
    """
    
    def __init__(self, xsd_paths: Dict[str, Path]):
        self.schemas = {}
        self.xsd_paths = xsd_paths
        
        # Intentar cargar XSDs si existen
        for name, path in xsd_paths.items():
            if path and path.exists():
                try:
                    import xmlschema
                    self.schemas[name] = xmlschema.XMLSchema(str(path))
                    logger.info(f"Schema cargado: {name} desde {path}")
                except Exception as e:
                    logger.warning(f"No se pudo cargar schema {name}: {e}")
    
    def validate_structure(self, xml_content: str, schema_name: str = "invoice") -> Dict[str, Any]:
        """
        Valida la estructura del XML contra el XSD
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Primero verificar que sea XML válido
            root = ET.fromstring(xml_content)
            result["root_tag"] = root.tag
            
            # Validar contra schema si está disponible
            if schema_name in self.schemas:
                try:
                    self.schemas[schema_name].validate(xml_content)
                    result["valid"] = True
                    result["message"] = f"Estructura válida contra schema {schema_name}"
                except Exception as e:
                    result["errors"].append(f"Error contra schema: {str(e)[:200]}")
            else:
                # Validación básica
                result["valid"] = True
                result["warnings"].append(f"Schema {schema_name} no disponible, solo validación básica")
            
            return result
            
        except ET.ParseError as e:
            result["errors"].append(f"Error de parsing XML: {e}")
            return result
        except Exception as e:
            result["errors"].append(f"Error inesperado: {e}")
            return result
    
    def validate_totals(self, xml_content: str) -> Dict[str, Any]:
        """
        Valida los totales matemáticos (IVA, retenciones, totales)
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "line_by_line": [],
            "summary": {}
        }
        
        try:
            root = ET.fromstring(xml_content)
            ns = self._extract_namespaces(root)
            
            # Extraer valores totales
            line_extension = self._get_decimal(root, ".//cbc:LineExtensionAmount", ns)
            tax_exclusive = self._get_decimal(root, ".//cbc:TaxExclusiveAmount", ns)
            tax_inclusive = self._get_decimal(root, ".//cbc:TaxInclusiveAmount", ns)
            payable = self._get_decimal(root, ".//cbc:PayableAmount", ns)
            
            result["summary"] = {
                "line_extension": float(line_extension),
                "tax_exclusive": float(tax_exclusive),
                "tax_inclusive": float(tax_inclusive),
                "payable": float(payable)
            }
            
            # Validar consistencia básica
            if line_extension != tax_exclusive:
                result["errors"].append(
                    f"LineExtensionAmount ({line_extension}) != TaxExclusiveAmount ({tax_exclusive})"
                )
                result["valid"] = False
            
            # Sumar IVA y retenciones de líneas
            line_iva_sum = Decimal('0')
            line_ret_fuente_sum = Decimal('0')
            line_ret_iva_sum = Decimal('0')
            line_total_base = Decimal('0')
            
            for line in root.findall(".//cac:InvoiceLine", ns):
                line_id = self._get_text(line, "cbc:ID", ns)
                line_amount = self._get_decimal(line, "cbc:LineExtensionAmount", ns)
                line_total_base += line_amount
                
                # IVA por línea
                tax_amount = self._get_decimal(line, ".//cac:TaxTotal/cbc:TaxAmount", ns)
                if tax_amount:
                    line_iva_sum += tax_amount
                
                # Retenciones por línea
                rete_fuente = self._get_line_withholding(line, "06", ns)
                rete_iva = self._get_line_withholding(line, "05", ns)
                line_ret_fuente_sum += rete_fuente
                line_ret_iva_sum += rete_iva
                
                result["line_by_line"].append({
                    "line_id": line_id,
                    "amount": float(line_amount),
                    "iva": float(tax_amount) if tax_amount else 0,
                    "rete_fuente": float(rete_fuente),
                    "rete_iva": float(rete_iva)
                })
            
            # Obtener totales declarados a nivel factura
            tax_total = self._get_decimal(root, ".//cac:TaxTotal/cbc:TaxAmount", ns)
            ret_fuente_total = self._get_withholding_total(root, "06", ns)
            ret_iva_total = self._get_withholding_total(root, "05", ns)
            
            result["summary"].update({
                "iva_declared": float(tax_total),
                "rete_fuente_declared": float(ret_fuente_total),
                "rete_iva_declared": float(ret_iva_total),
                "iva_from_lines": float(line_iva_sum),
                "rete_fuente_from_lines": float(line_ret_fuente_sum),
                "rete_iva_from_lines": float(line_ret_iva_sum),
                "total_lines_base": float(line_total_base)
            })
            
            # Validar sumas
            tolerance = Decimal('0.01')
            
            if abs(line_iva_sum - tax_total) > tolerance:
                result["errors"].append(
                    f"Suma IVA líneas ({line_iva_sum}) != TaxTotal ({tax_total})"
                )
                result["valid"] = False
            
            if abs(line_ret_fuente_sum - ret_fuente_total) > tolerance:
                result["errors"].append(
                    f"Suma ReteFuente líneas ({line_ret_fuente_sum}) != ReteFuente total ({ret_fuente_total})"
                )
                result["valid"] = False
            
            if abs(line_ret_iva_sum - ret_iva_total) > tolerance:
                result["errors"].append(
                    f"Suma ReteIVA líneas ({line_ret_iva_sum}) != ReteIVA total ({ret_iva_total})"
                )
                result["valid"] = False
            
            # Validar que el total pagable sea correcto
            expected_payable = line_extension + tax_total - ret_fuente_total - ret_iva_total
            if abs(expected_payable - payable) > tolerance:
                result["errors"].append(
                    f"PayableAmount ({payable}) no coincide con el cálculo esperado ({expected_payable})"
                )
                result["valid"] = False
            
        except Exception as e:
            result["errors"].append(f"Error en validación de totales: {e}")
            result["valid"] = False
        
        return result
    
    def validate_encoding(self, xml_content: str) -> Dict[str, Any]:
        """
        Valida que el XML esté correctamente codificado en UTF-8
        """
        result = {
            "valid": True,
            "errors": [],
            "detected_issues": [],
            "suggestions": []
        }
        
        # Verificar declaración de encoding
        encoding_match = re.search(r'<\?xml.*encoding=["\']([^"\']+)["\']', xml_content, re.IGNORECASE)
        if not encoding_match:
            result["errors"].append("Falta declaración de encoding en el XML")
            result["valid"] = False
        else:
            declared_encoding = encoding_match.group(1).lower()
            if declared_encoding != 'utf-8':
                result["errors"].append(f"Encoding declarado es '{declared_encoding}', debe ser 'utf-8'")
                result["valid"] = False
        
        # Detectar problemas de codificación
        encoding_issues = detect_encoding_issues(xml_content)
        if encoding_issues["has_issues"]:
            result["valid"] = False
            result["detected_issues"] = encoding_issues["issues"]
            result["suggestions"] = encoding_issues["suggestions"]
        
        return result
    
    def validate_cufe(self, xml_content: str) -> Dict[str, Any]:
        """
        Valida el formato del CUFE
        """
        result = {
            "valid": False,
            "cufe": None,
            "errors": []
        }
        
        try:
            root = ET.fromstring(xml_content)
            ns = self._extract_namespaces(root)
            
            cufe = self._get_text(root, ".//cbc:UUID", ns)
            if not cufe:
                cufe = self._get_text(root, ".//cbc:UUID[@schemeName='CUFE-SHA384']", ns)
            
            if not cufe:
                result["errors"].append("CUFE no encontrado en el XML")
                return result
            
            result["cufe"] = cufe
            
            # Validar formato (SHA-384 = 96 caracteres hex)
            if len(cufe) != 96:
                result["errors"].append(f"CUFE tiene {len(cufe)} caracteres, deben ser 96")
            elif not re.match(r'^[a-fA-F0-9]{96}$', cufe):
                result["errors"].append("CUFE no es un hash hexadecimal válido")
            else:
                result["valid"] = True
                
        except Exception as e:
            result["errors"].append(f"Error validando CUFE: {e}")
        
        return result
    
    def _extract_namespaces(self, root: ET.Element) -> Dict:
        """Extrae namespaces del XML"""
        ns = {}
        for elem in root.iter():
            if elem.tag.startswith('{'):
                uri = elem.tag.split('}')[0].strip('{')
                # Detectar prefix común
                if 'cbc' in uri:
                    ns['cbc'] = uri
                elif 'cac' in uri:
                    ns['cac'] = uri
                elif 'ext' in uri:
                    ns['ext'] = uri
                elif 'sts' in uri:
                    ns['sts'] = uri
                elif 'ds' in uri:
                    ns['ds'] = uri
        return ns
    
    def _get_decimal(self, element: ET.Element, xpath: str, ns: Dict) -> Decimal:
        """Extrae valor Decimal de un elemento"""
        value = self._get_text(element, xpath, ns)
        if value:
            try:
                # Limpiar formato
                clean = value.replace(',', '.').replace(' ', '').strip()
                return Decimal(clean)
            except:
                return Decimal('0')
        return Decimal('0')
    
    def _get_text(self, element: ET.Element, xpath: str, ns: Dict) -> str:
        """Extrae texto de un elemento"""
        try:
            if ':' in xpath:
                prefix, tag = xpath.split(':')
                if prefix in ns:
                    elem = element.find(f".//{{{ns[prefix]}}}{tag}")
                    if elem is not None and elem.text:
                        return elem.text.strip()
            else:
                elem = element.find(f".//{xpath}")
                if elem is not None and elem.text:
                    return elem.text.strip()
        except:
            pass
        return ""
    
    def _get_withholding_total(self, root: ET.Element, tax_id: str, ns: Dict) -> Decimal:
        """Obtiene total de retención específica a nivel factura"""
        for withholding in root.findall(".//cac:WithholdingTaxTotal", ns):
            scheme_id = self._get_text(withholding, ".//cac:TaxScheme/cbc:ID", ns)
            if scheme_id == tax_id:
                return self._get_decimal(withholding, "cbc:TaxAmount", ns)
        return Decimal('0')
    
    def _get_line_withholding(self, line: ET.Element, tax_id: str, ns: Dict) -> Decimal:
        """Obtiene retención de una línea específica"""
        total = Decimal('0')
        for withholding in line.findall("cac:WithholdingTaxTotal", ns):
            scheme_id = self._get_text(withholding, ".//cac:TaxScheme/cbc:ID", ns)
            if scheme_id == tax_id:
                total += self._get_decimal(withholding, "cbc:TaxAmount", ns)
        return total