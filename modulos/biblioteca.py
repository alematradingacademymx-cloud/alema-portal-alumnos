import base64
import os
import streamlit as st

# ==========================================
# SECCIÓN: BIBLIOTECA DE GUÍAS
# ==========================================
st.markdown('<div class="main-title" style="text-align: left;">ALEMA TRADING ACADEMY</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title" style="text-align: left;">Biblioteca Digital Exclusiva para Alumnos y Suscriptores</div>', unsafe_allow_html=True)

st.subheader("📖 Lectura y Consulta de Materiales")

GUIAS_DISPONIBLES = {
    "📙 Acción del Precio y Estructura": "Nueva guia Accion del precio.pdf",
    "📗 Manual del Trader (Básico)": "Manual del Trader (Básico).pdf"
}

guia_seleccionada = st.selectbox(
    "Selecciona la guía que deseas consultar:",
    list(GUIAS_DISPONIBLES.keys()),
    key="selector_guias_pdf"
)

archivo_pdf = GUIAS_DISPONIBLES[guia_seleccionada]

if os.path.exists(archivo_pdf):
    st.success(f"📄 Lectura en pantalla: **{guia_seleccionada}**")
    
    @st.cache_data
    def cargar_bytes_pdf(ruta):
        with open(ruta, "rb") as f:
            return f.read()

    pdf_bytes = cargar_bytes_pdf(archivo_pdf)
    
    # Convertimos los bytes del PDF a cadena base64 para renderizado HTML
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

    # Visualizador PDF integrado con ocultación de barra de descarga (#toolbar=0)
    pdf_display = f'''
        <iframe 
            src="data:application/pdf;base64,{base64_pdf}#toolbar=0&navpanes=0&scrollbar=1" 
            width="100%" 
            height="800" 
            type="application/pdf"
            style="border: 1px solid #444; border-radius: 8px;">
        </iframe>
    '''
    
    st.markdown(pdf_display, unsafe_allow_html=True)
    st.caption("💡 **Tip de lectura:** En dispositivos móviles, gira la pantalla horizontalmente para ampliar el visor.")
else:
    st.warning(f"⚠️ El archivo `{archivo_pdf}` no se encuentra en el repositorio.")
