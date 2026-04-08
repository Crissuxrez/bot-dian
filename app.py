"""
Interfaz gráfica para el CrisValid
Uso: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os
import tempfile

# Agregar src al path
sys.path.insert(0, os.path.dirname(__file__))

from src.agent import DianSupportAgent
from src.config import MANUALES_DIR, EJEMPLOS_DIR, OUTPUT_DIR

# Configuración de la página
st.set_page_config(
    page_title="CrisValid",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
<style>
    .diagnosis-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 15px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 15px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 15px;
        margin: 10px 0;
    }
    .recommendation-box {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 15px;
        margin: 10px 0;
    }
    .stExpander {
        border-radius: 10px;
    }
    .main-header {
        background: linear-gradient(90deg, #003366, #0066cc);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Inicializa el estado de la sesión"""
    if 'agent' not in st.session_state:
        with st.spinner("Inicializando agente y cargando base de conocimiento..."):
            st.session_state.agent = DianSupportAgent()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'last_analysis' not in st.session_state:
        st.session_state.last_analysis = None
    
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None


def display_analysis(analysis):
    """Muestra el análisis en formato visual"""
    
    if analysis.get('success'):
        st.markdown('<div class="success-box">✅ <strong>ANÁLISIS COMPLETADO</strong> - No se detectaron errores críticos</div>', 
                   unsafe_allow_html=True)
    else:
        st.markdown('<div class="error-box">❌ <strong>ERRORES DETECTADOS</strong> - Se encontraron problemas que requieren corrección</div>', 
                   unsafe_allow_html=True)
    
    # Encoding issues
    if analysis.get('validations', {}).get('encoding'):
        enc = analysis['validations']['encoding']
        if not enc['valid']:
            with st.expander("🔤 Problemas de codificación UTF-8", expanded=True):
                st.markdown("### Caracteres mal codificados encontrados:")
                for issue in enc.get('detected_issues', []):
                    st.error(f"`{issue}`")
                
                st.markdown("### Solución:")
                st.info("""
                **Regenerar el XML con codificación UTF-8 correcta:**
                - Asegurar que la fuente de datos esté en UTF-8
                - Evitar usar `utf8_encode()` si los datos ya están en UTF-8
                - Al guardar el XML, especificar `encoding='utf-8'`
                - Verificar que no haya conversiones dobles
                """)
    
    # Totals issues
    if analysis.get('validations', {}).get('totals'):
        totals = analysis['validations']['totals']
        if not totals['valid']:
            with st.expander("💰 Errores en totales y retenciones", expanded=True):
                for error in totals.get('errors', []):
                    st.error(error)
                
                # Mostrar resumen de totales
                if totals.get('summary'):
                    st.markdown("### Resumen de valores")
                    summary_data = {
                        "Concepto": ["Subtotal", "IVA", "ReteFuente", "ReteIVA", "Total a pagar"],
                        "Declarado": [
                            f"${totals['summary'].get('payable', 0):,.0f}",
                            f"${totals['summary'].get('iva_declared', 0):,.0f}",
                            f"${totals['summary'].get('rete_fuente_declared', 0):,.0f}",
                            f"${totals['summary'].get('rete_iva_declared', 0):,.0f}",
                            f"${totals['summary'].get('payable', 0):,.0f}"
                        ],
                        "Calculado": [
                            f"${totals['summary'].get('line_extension', 0):,.0f}",
                            f"${totals['summary'].get('iva_from_lines', 0):,.0f}",
                            f"${totals['summary'].get('rete_fuente_from_lines', 0):,.0f}",
                            f"${totals['summary'].get('rete_iva_from_lines', 0):,.0f}",
                            f"${totals['summary'].get('payable', 0):,.0f}"
                        ]
                    }
                    df = pd.DataFrame(summary_data)
                    st.dataframe(df, use_container_width=True)
                
                # Detalle por línea
                if totals.get('line_by_line'):
                    st.markdown("### Detalle por línea")
                    df_lines = pd.DataFrame(totals['line_by_line'])
                    st.dataframe(df_lines, use_container_width=True)
    
    # CUFE issues
    if analysis.get('validations', {}).get('cufe'):
        cufe = analysis['validations']['cufe']
        if not cufe['valid']:
            with st.expander("🔑 Problemas con CUFE", expanded=True):
                for error in cufe['errors']:
                    st.error(error)
                if cufe.get('cufe'):
                    st.code(cufe['cufe'], language='text')
    
    # Errores generales
    if analysis.get('errors'):
        with st.expander("📋 Lista completa de errores", expanded=False):
            for error in analysis['errors']:
                st.error(f"❌ {error}")
    
    # Advertencias
    if analysis.get('warnings'):
        with st.expander("⚠️ Advertencias", expanded=False):
            for warning in analysis['warnings']:
                st.warning(f"⚠️ {warning}")
    
    # Recomendaciones
    if analysis.get('recommendations'):
        with st.expander("✅ Recomendaciones técnicas", expanded=True):
            for rec in analysis['recommendations']:
                st.markdown(f"🔧 {rec}")
    
    # Conocimiento encontrado
    if analysis.get('knowledge_base_matches'):
        with st.expander("📚 Documentación relevante encontrada", expanded=False):
            for match in analysis['knowledge_base_matches']:
                st.markdown(f"**📄 {match['source']}** (Relevancia: {match['relevance']:.2%})")
                st.text(match['content'][:400] + "..." if len(match['content']) > 400 else match['content'])
                st.markdown("---")


def main():
    init_session_state()
    
    # Header
    st.markdown("""
<div class="main-header">
    <h1>🤖 CrisValid - facturación electrónica </h1>
    <p>Análisis técnico de facturación electrónica | Validación DIAN | Detección de errores</p>
</div>
""", unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://www.dian.gov.co/PublishingImages/Escudo-Dian.png", width=100)
        st.markdown("## 📚 Gestión de Conocimiento")
        st.title("🤖 CrisValid")  
        
        # Mostrar estado
        st.metric("Documentos en KB", st.session_state.agent.knowledge_manager.count())
        
        st.markdown("---")
        
        # Cargar manuales
        st.subheader("📄 Cargar Documentos")
        
        uploaded_file = st.file_uploader(
            "Selecciona PDF, XML o TXT",
            type=['pdf', 'xml', 'txt', 'json', 'html'],
            key="manual_upload"
        )
        
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            if st.button("Cargar a la base de conocimiento"):
                with st.spinner(f"Cargando {uploaded_file.name}..."):
                    if st.session_state.agent.load_manual(tmp_path):
                        st.success(f"✅ {uploaded_file.name} cargado correctamente")
                        st.rerun()
                    else:
                        st.error(f"❌ Error cargando {uploaded_file.name}")
        
        # Listar manuales cargados
        st.markdown("---")
        st.subheader("📚 Documentos cargados")
        
        manuals = st.session_state.agent.list_manuals()
        if manuals:
            for manual in manuals:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"📄 {manual['filename']}")
                with col2:
                    if st.button("🗑️", key=f"del_{manual['filename']}"):
                        if st.session_state.agent.remove_manual(manual['filename']):
                            st.success(f"Eliminado {manual['filename']}")
                            st.rerun()
        else:
            st.info("No hay documentos cargados. Carga PDFs de manuales DIAN o ejemplos.")
        
        st.markdown("---")
        
        # Opciones
        st.subheader("⚙️ Configuración")
        
        show_raw = st.checkbox("Mostrar análisis detallado", value=True)
        
        if st.button("🗑️ Limpiar historial"):
            st.session_state.agent.clear_history()
            st.session_state.messages = []
            st.session_state.last_analysis = None
            st.success("Historial limpiado")
    
    # Área principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📝 Análisis de Documentos")
        
        # Entrada de texto
        user_input = st.text_area(
            "Describe el problema o pega el contenido del XML:",
            height=150,
            placeholder="Ejemplo: 'El XML fue rechazado con error de codificación' o pega el contenido del XML aquí..."
        )
        
        # Subida de archivo
        uploaded_doc = st.file_uploader(
            "O sube el archivo XML/PDF a analizar:",
            type=['xml', 'pdf', 'txt'],
            key="doc_upload"
        )
        
        # Botón de análisis
        if st.button("🔍 Analizar Documento", type="primary"):
            content = ""
            filename = ""
            file_type = "xml"
            
            if uploaded_doc:
                content = uploaded_doc.getvalue().decode('utf-8', errors='replace')
                filename = uploaded_doc.name
                if filename.endswith('.pdf'):
                    file_type = "pdf"
                elif filename.endswith('.txt'):
                    file_type = "txt"
            elif user_input:
                content = user_input
                filename = "text_input"
                file_type = "xml" if "<xml" in content.lower() or "<?xml" in content else "text"
            else:
                st.warning("Por favor ingresa texto o sube un archivo")
            
            if content:
                with st.spinner("Analizando documento..."):
                    analysis = st.session_state.agent.analyze_document(
                        content, 
                        file_type=file_type,
                        filename=filename
                    )
                    st.session_state.last_analysis = analysis
                    
                    # Generar respuesta
                    if analysis['errors']:
                        prompt = f"El documento {filename} tiene los siguientes errores: {analysis['errors'][:3]}"
                    else:
                        prompt = f"El documento {filename} fue analizado y no se encontraron errores estructurales. ¿Qué más puedo revisar?"
                    
                    response = st.session_state.agent.generate_response(prompt, analysis)
                    
                    # Guardar en historial
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Mostrar análisis
        if st.session_state.last_analysis and show_raw:
            st.markdown("---")
            st.markdown("### 📊 Resultado del Análisis")
            display_analysis(st.session_state.last_analysis)
    
    with col2:
        st.markdown("### 💬 Respuesta del Agente")
        
        # Mostrar historial de conversación
        if st.session_state.messages:
            for msg in st.session_state.messages[-6:]:
                if msg["role"] == "user":
                    st.markdown(f"**👤 Tú:** {msg['content'][:200]}...")
                else:
                    st.markdown(f"**🤖 Agente:**")
                    st.markdown(msg['content'])
                st.markdown("---")
        else:
            st.info("El análisis se mostrará aquí después de procesar un documento.")
        
        # Input rápido
        st.markdown("### ✏️ Consulta adicional")
        follow_up = st.text_input("Pregunta algo más sobre el análisis:")
        if follow_up and st.button("Enviar consulta"):
            response = st.session_state.agent.generate_response(
                follow_up, 
                st.session_state.last_analysis
            )
            st.session_state.messages.append({"role": "user", "content": follow_up})
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: gray; font-size: 12px;">
        Agente de Soporte Técnico DIAN v1.0 | Desarrollado con Python, Streamlit y ChromaDB
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()