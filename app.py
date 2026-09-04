import streamlit as st
import pandas as pd
import datetime
import json
import os

# ==========================================
# PARTE 1: CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="ALEMA Trading Academy",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialización del estado de sesión
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = ""
if "tipo_usuario" not in st.session_state:
    st.session_state["tipo_usuario"] = "ALUMNO"


# ==========================================
# PARTE 2: 🔑 FUNCIÓN PARA CONVERTIR CUALQUIER FECHA
# ==========================================
def parsear_fecha(valor_fecha):
    """Convierte cadenas o stamps a objetos datetime.date para evitar inconsistencias."""
    if pd.isna(valor_fecha) or not valor_fecha:
        return datetime.date.today()
    try:
        return pd.to_datetime(valor_fecha).date()
    except Exception:
        return datetime.date.today()


# ==========================================
# PARTE 3: 🔑 BASE DE DATOS DE USUARIOS (GOOGLE SHEETS)
# ==========================================
# ID de Google Sheets extraído de tu enlace
SHEET_ID = "1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA"
GDATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def cargar_base_datos_sheets():
    """Lee la hoja de cálculo pública o mediante credenciales."""
    try:
        df = pd.read_csv(GDATA_URL)
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

# Control de acceso (Login)
if not st.session_state["autenticado"]:
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>ALEMA TRADING ACADEMY</h2>", unsafe_allow_html=True)
        st.caption("Portal Institucional de Alumnos y Coordinación")
        
        with st.form("form_login_principal"):
            usr = st.text_input("Matrícula / Usuario", key="input_usr").strip()
            pwd = st.text_input("Contraseña", type="password", key="input_pwd")
            if st.form_submit_button("🔑 Iniciar Sesión", use_container_width=True):
                # Validación de prueba (Se conectará con las columnas del Sheet)
                if usr and pwd:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_actual"] = usr
                    st.rerun()
    st.stop()


# ==========================================
# PARTE 4: ⚙️ PANEL DE CONTROL ADMIN (SOLO PARA ADMINS EN SIDEBAR)
# ==========================================
def render_panel_admin_sidebar():
    if st.session_state.get("tipo_usuario") == "ADMIN":
        st.sidebar.divider()
        st.sidebar.markdown("**⚙️ Panel Coordinación Admin**")
        if st.sidebar.button("🔄 Sincronizar Base de Datos", key="btn_admin_sync", use_container_width=True):
            st.cache_data.clear()
            st.sidebar.success("Datos actualizados desde Google Sheets.")
            st.rerun()


# ==========================================
# PARTE 5: 🚀 MENÚ LATERAL Y NAVEGACIÓN SEGÚN ROL
# ==========================================
with st.sidebar:
    st.title("🧭 Menú Principal")
    
    opciones_menu = [
        "Mi Avance Académico",
        "Calculadoras de Lotes",
        "Trading Journal",
        "Simulador Institucional",
        "Biblioteca de Guías",
        "Evaluaciones y Control Académico"
    ]
    
    seccion_activa = st.radio("Selecciona una sección:", opciones_menu, key="menu_navegacion_principal")
    
    render_panel_admin_sidebar()
    
    st.sidebar.divider()
    if st.sidebar.button("🚪 Cerrar Sesión", key="btn_logout_main", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ==========================================
# PARTE 6: SECCIÓN: MI AVANCE ACADÉMICO (ALUMNOS/ADMIN)
# ==========================================
if seccion_activa == "Mi Avance Académico":
    st.title("📈 Mi Avance Académico")
    st.info("Resumen de trayectoria, estatus de beca y matrícula.")


# ==========================================
# PARTE 7: SECCIÓN: CALCULADORAS DE LOTES
# ==========================================
elif seccion_activa == "Calculadoras de Lotes":
    st.title("🧮 Calculadoras de Lotes y Gestión")


# ==========================================
# PARTE 8: SECCIÓN: TRADING JOURNAL
# ==========================================
elif seccion_activa == "Trading Journal":
    st.title("📓 Bitácora de Operaciones (Trading Journal)")


# ==========================================
# PARTE 9: SIMULADOR INSTITUCIONAL ALEMA TRADING ACADEMY
# (VERSIÓN CONECTADA A BASE DE DATOS GOOGLE SHEETS CON CHALLENGE)
# ==========================================
elif seccion_activa == "Simulador Institucional":
    st.title("📊 Simulador Institucional & Challenge")


# ==========================================
# PARTE 10: SECCIÓN: BIBLIOTECA DE GUÍAS
# ==========================================
elif seccion_activa == "Biblioteca de Guías":
    st.title("📚 Biblioteca de Guías y Recursos")


# ==========================================
# PARTE 11: SECCIÓN: EVALUACIONES Y CONTROL ACADÉMICO
# ==========================================
elif seccion_activa == "Evaluaciones y Control Académico":
    st.title("🎓 Evaluaciones y Control Académico")
    
    # Sub-pestanas de la sección de evaluaciones
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Ruta & Exámenes",
        "Certificados",
        "Creador (Admin)",
        "Candados (Admin)",
        "Dictamen (Admin)",
        "Archivos (Admin)"
    ])
    
    # PARTE 12: PESTAÑA 1: RUTA ACADÉMICA Y PRESENTACIÓN DE EXÁMENES
    with tab1:
        st.markdown("**Ruta Académica y Exámenes Disponibles**")

    # PARTE 13: PESTAÑA 2: RESULTADOS Y DESCARGA DE CERTIFICADOS (ALUMNO)
    with tab2:
        st.markdown("**Resultados e Histórico de Certificaciones**")

    # PARTE 14: PESTAÑA 3: CREADOR DINÁMICO DE EXÁMENES (ADMIN)
    with tab3:
        st.markdown("**Generador de Exámenes para Coordinación**")

    # PARTE 15: PESTAÑA 4: GESTOR DE CANDADOS (ADMIN)
    with tab4:
        st.markdown("**Control de Bloqueos y Módulos**")

    # PARTE 16: PESTAÑA 5: REVISIÓN, DICTAMEN Y CARGA DE CERTIFICADO (ADMIN)
    with tab5:
        st.markdown("**Revisiones de Exámenes y Emisión**")

    # PARTE 17: PESTAÑA 6: ARCHIVOS Y EXCEL (ADMIN)
    with tab6:
        st.markdown("**Gestor de Exportación y Tablas**")
