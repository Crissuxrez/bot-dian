@"
# 🤖 Agente de Soporte Técnico DIAN

Agente automatizado para validación de facturación electrónica colombiana (DIAN).

## Características
- Validación de estructura XML
- Verificación de codificación UTF-8
- Validación de totales (IVA, retenciones)
- Base de conocimiento con documentación DIAN

## Cómo usar
1. Sube un XML de facturación electrónica
2. El agente analiza y detecta errores
3. Recibe recomendaciones de corrección

## Tecnologías
- Python + Streamlit
- Validación XML con lxml
- Base de conocimiento vectorial

---
Desarrollado para soporte técnico DIAN
"@ | Out-File -FilePath README.md -Encoding utf8