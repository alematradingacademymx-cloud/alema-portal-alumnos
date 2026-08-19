import streamlit as st
import pandas as pd
import numpy as np
import os

# Configuración de página
st.set_page_config(
    page_title="Calculadora de Gestión de Riesgo | ALEMA",
    page_icon="📊",
    layout="wide"
)

# Estilos personalizados
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #0066cc;
        color: white;
        font-weight: bold;
    }
    .metric-card {
        background-color: #1e293b;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Calculadora de Gestión de Riesgo & Guías ALEMA")
st.caption("ALEMA Trading Academy — Herramienta Educativa y Operativa")

# Menú principal de navegación
opcion = st.sidebar.radio(
    "Selecciona una herramienta:",
    ["🧮 Calculadora de Lotaje", "📚 Guías Educativas PDF"]
)

# ---------------------------------------------------------
# SECCIÓN 1: CALCULADORA DE LOTAJE
# ---------------------------------------------------------
if opcion == "🧮 Calculadora de Lotaje":
    st.header("🧮 Calculadora de Gestión de Riesgo y Lotaje")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Configuración de la Cuenta")
        balance = st.number_input("Balance de la Cuenta ($):", min_value=10.0, value=1000.0, step=50.0)
        riesgo_pct = st.slider("Riesgo por Operación (%):", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
        
        st.subheader("Detalles del Trade")
        instrumento = st.selectbox("Instrumento:", ["Forex (Pips)", "Índices / Criptos / Acciones (Puntos)"])
        stop_loss = st.number_input("Stop Loss (en Pips o Puntos):", min_value=1.0, value=20.0, step=1.0)
        
        if instrumento == "Forex (Pips)":
            par = st.selectbox("Par / Tipo de Par:", ["Pares Estándar (EURUSD, GBPUSD, etc.)", "JPY (USDJPY, EURJPY, etc.)", "Oro (XAUUSD)"])
            
    with col2:
        st.subheader("📊 Resultados de Gestión")
        
        monto_riesgo = balance * (riesgo_pct / 100.0)
        
        if instrumento == "Forex (Pips)":
            if "JPY" in par:
                pip_value_std = 1000 / 130  # Aprox para JPY
                lotes = monto_riesgo / (stop_loss * 10)
            elif "Oro" in par:
                lotes = monto_riesgo / (stop_loss * 10)
            else:
                lotes = monto_riesgo / (stop_loss * 10)
        else:
            lotes = monto_riesgo / stop_loss
            
        st.metric(label="Riesgo Máximo Permitido ($)", value=f"${monto_riesgo:.2f}")
        st.metric(label="Tamaño de Posición Sugerido (Lotes)", value=f"{lotes:.2f} lotes")
        
        st.info("💡 **Regla de Oro ALEMA:** Nunca arriesgues más del 1% al 2% de tu capital por operación.")

# ---------------------------------------------------------
# SECCIÓN 2: GUÍAS EDUCATIVAS PDF
# ---------------------------------------------------------
elif opcion == "📚 Guías Educativas PDF":
    st.header("📚 Biblioteca de Guías Educativas ALEMA")
    st.write("Consulta o descarga el material de estudio oficial directamente dentro de la aplicación.")
    
    # Mapeo exacto de los nombres de tus archivos subidos
    GUIAS = {
        "📙 Acción del Precio y Estructura": "Nueva guia Accion del precio.pdf",
        "📗 Manual del Trader (Básico)": "Manual del Trader (Básico).pdf"
    }
    
    guia_seleccionada = st.selectbox("Selecciona la guía que deseas consultar:", list(GUIAS.keys()))
    nombre_archivo = GUIAS[guia_seleccionada]
    
    # Ruta en la carpeta del repositorio
    ruta_pdf = os.path.join(nombre_archivo)
    
    if os.path.exists(ruta_pdf):
        with open(ruta_pdf, "rb") as f:
            pdf_bytes = f.read()
            
        st.download_button(
            label=f"📥 Descargar {guia_seleccionada}",
            data=pdf_bytes,
            file_name=nombre_archivo,
            mime="application/pdf"
        )
        
        # Visor de PDF integrado
        import base64
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.warning(f"El archivo `{nombre_archivo}` se está cargando o está en proceso de sincronización. Si acabas de subirlo, espera un momento y recarga la página.")
