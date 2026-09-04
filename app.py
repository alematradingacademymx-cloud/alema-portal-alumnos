import os
import json
import requests
import pandas as pd
from PIL import Image
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go

import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# ⚙️ CONFIGURACIÓN DE PÁGINA Y LOGO OFICIAL
# ==========================================
archivo_logo = "alema trading academy.png"

if not os.path.exists(archivo_logo):
    coincidencias = [f for f in os.listdir(".") if f.lower().startswith("alema trading academ")]
    if coincidencias:
        archivo_logo = coincidencias[0]

if os.path.exists(archivo_logo):
    try:
        icono_pagina = Image.open(archivo_logo)
    except Exception:
        icono_pagina = "📈"
else:
    icono_pagina = "📈"

# Se cambia a layout="wide" para dar espacio a la barra lateral y tablas
st.set_page_config(
    page_title="ALEMA Trading Academy - Portal de Alumnos", 
    page_icon=icono_pagina, 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🛠️ FUNCIONES DE PERSISTENCIA JSON AUXILIARES
# ==========================================
def cargar_datos_json(filepath, default_value):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_value
    return default_value

def guardar_datos_json(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

# ==========================================
# 🎨 ESTILOS CSS PERSONALIZADOS (CORREGIDOS)
# ==========================================
st.markdown("""
    <style>
    /* Ocultar únicamente marcas de Streamlit y menú de opciones de la derecha, preservando el botón del sidebar */
    [data-testid="stToolbar"] {
        visibility: hidden !important;
        height: 0px !important;
    }
    
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Fondo General Azul Oscuro */
    .stApp {
        background-color: #0E1726;
        color: #F1F5F9;
    }
    
    /* Encabezados y Textos */
    .main-title {
        text-align: center;
        font-size: 30px;
        font-weight: 800;
        color: #FF6B00; /* Naranja Institucional */
        margin-top: 10px;
        margin-bottom: 0px;
        letter-spacing: 1px;
    }
    .sub-title {
        text-align: center;
        font-size: 16px;
        color: #94A3B8;
        margin-bottom: 20px;
    }
    
    /* Contenedor de Copia Rápida */
    .copy-box {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 15px;
        font-family: monospace;
        font-size: 15px;
        color: #38BDF8;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    
    /* Estilo Caja de Login y Tarjetas */
    .card-box {
        background-color: #1E293B;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    
    /* Personalización Sidebar */
    [data-testid="stSidebar"] {
        background-color: #141E2E;
        border-right: 1px solid #334155;
    }

    /* ESTILO BOTÓN VERDE DE EJECUCIÓN */
    div.stButton > button[key="btn_ejecutar_sim"] {
        background-color: #10B981 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        transition: 0.3s !important;
    }
    div.stButton > button[key="btn_ejecutar_sim"]:hover {
        background-color: #059669 !important;
        box-shadow: 0px 4px 12px rgba(16, 185, 129, 0.4) !important;
    }

    /* ESTILO PRECIO ENTRADA AMARILLO (EJECUCIÓN EN VIVO) */
    .precio-amarillo input {
        background-color: #FEF08A !important;
        color: #0F172A !important;
        font-weight: bold !important;
        border: 2px solid #EAB308 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔑 FUNCIÓN PARA CONVERTIR CUALQUIER FECHA
# ==========================================
def parsear_fecha(fecha_str):
    if not fecha_str or str(fecha_str).strip() == '':
        return datetime(2030, 12, 31).date()
    
    fecha_clean = str(fecha_str).strip()
    formatos = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
        "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y", "%Y-%m-%d %H:%M:%S"
    ]
    for fmt in formatos:
        try:
            return datetime.strptime(fecha_clean, fmt).date()
        except ValueError:
            pass
    return datetime(2030, 12, 31).date()

# ===# ==========================================
# 🔑 BASE DE DATOS DE USUARIOS (GOOGLE SHEETS) Y AUTENTICACIÓN
# ==========================================
import os
import base64
import requests
import pandas as pd
import streamlit as st
from datetime import datetime

SHEET_ID = "1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA"

URL_USUARIOS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Usuarios"
URL_AVANCES = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Avances"
URL_FORM_RESPONSE = "https://docs.google.com/forms/d/e/1FAIpQLSf9mOAhtFyAcjxJ2WK2mwCbPOtDa_9dSnsz9gHNPbOJ8M51cQ/formResponse"
URL_JOURNAL_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Journal"

@st.cache_data(ttl=10)
def cargar_usuarios_desde_sheets():
    try:
        df = pd.read_csv(URL_USUARIOS, dtype=str)
        df.columns = df.columns.str.strip()
        df['Matricula'] = df['Matricula'].fillna('').str.strip().str.upper()
        df['Password'] = df['Password'].fillna('').str.strip()
        df['Tipo_Usuario'] = df['Tipo_Usuario'].fillna('ALUMNO').str.strip().str.upper()
        df['Fecha_Vencimiento'] = df['Fecha_Vencimiento'].fillna('2030-12-31').str.strip()
        df['Capital'] = pd.to_numeric(df['Capital'].fillna('300'), errors='coerce').fillna(300.0)
        
        dict_usuarios = {}
        for _, row in df.iterrows():
            dict_usuarios[row['Matricula']] = {
                'password': row['Password'],
                'tipo': row['Tipo_Usuario'],
                'vencimiento': row['Fecha_Vencimiento'],
                'capital_base': float(row['Capital'])
            }
        return dict_usuarios
    except Exception:
        try:
            url_fallback = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
            df = pd.read_csv(url_fallback, dtype=str)
            df.columns = df.columns.str.strip()
            df['Matricula'] = df['Matricula'].fillna('').str.strip().str.upper()
            df['Password'] = df['Password'].fillna('').str.strip()
            df['Tipo_Usuario'] = df['Tipo_Usuario'].fillna('ALUMNO').str.strip().str.upper()
            df['Fecha_Vencimiento'] = df['Fecha_Vencimiento'].fillna('2030-12-31').str.strip()
            df['Capital'] = pd.to_numeric(df['Capital'].fillna('300'), errors='coerce').fillna(300.0)
            
            dict_usuarios = {}
            for _, row in df.iterrows():
                dict_usuarios[row['Matricula']] = {
                    'password': row['Password'],
                    'tipo': row['Tipo_Usuario'],
                    'vencimiento': row['Fecha_Vencimiento'],
                    'capital_base': float(row['Capital'])
                }
            return dict_usuarios
        except Exception:
            return {}

@st.cache_data(ttl=10)
def obtener_avance_alumno(matricula_usuario):
    try:
        df_avances = pd.read_csv(URL_AVANCES, dtype=str)
        df_avances.columns = df_avances.columns.str.strip()
        df_avances['Matricula'] = df_avances['Matricula'].fillna('').str.strip().str.upper()
        
        alumno_data = df_avances[df_avances['Matricula'] == matricula_usuario]
        if not alumno_data.empty:
            return alumno_data.iloc[0].to_dict()
        return None
    except Exception:
        return None

USUARIOS_AUTORIZADOS = cargar_usuarios_desde_sheets()

# --- CONTROL Y PERSISTENCIA DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = ""

if "tipo_usuario" not in st.session_state:
    st.session_state.tipo_usuario = "ALUMNO"

if "journal_trades" not in st.session_state:
    st.session_state.journal_trades = []

# Inicializar rutas por defecto seguras en session_state
if "archivo_pos" not in st.session_state:
    st.session_state.archivo_pos = "posiciones_invitado.json"
if "archivo_hist" not in st.session_state:
    st.session_state.archivo_hist = "historial_invitado.json"

# --- PANTALLA DE INICIO DE SESIÓN Y PORTAL PÚBLICO ---
if not st.session_state.autenticado:
    # 🖼️ ISOTIPO BLANCO CENTRADO Y RESPONSIVO
    archivo_iso = "alema_iso.png"
    
    if not os.path.exists(archivo_iso):
        coincidencias = [f for f in os.listdir(".") if f.lower().startswith("alema_iso") or f.lower().startswith("alema_a")]
        if coincidencias:
            archivo_iso = coincidencias[0]

    if os.path.exists(archivo_iso):
        with open(archivo_iso, "rb") as img_file:
            img_b64 = base64.b64encode(img_file.read()).decode()
        st.markdown(
            f'''
            <div style="text-align: center; margin-bottom: 15px;">
                <img src="data:image/png;base64,{img_b64}" style="width: 95px; height: auto;">
            </div>
            ''',
            unsafe_allow_html=True)
            
    st.markdown('<div class="main-title">ALEMA TRADING ACADEMY</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Portal Exclusivo para Alumnos Certificados y Suscriptores</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 👋 ¡Bienvenido al Portal Institucional!")
    st.write(
        "Este es tu ecosistema de herramientas operativas, calculadoras de gestión de riesgo, "
        "journal de operaciones y biblioteca digital. Ingresa tus credenciales para comenzar."
    )
    
    st.markdown("---")
    
    st.subheader("🔒 Acceso al Portal Privado")
    st.write("Ingresa tus credenciales institucionales:")
    
    matricula_input = st.text_input("Matrícula / Usuario", key="login_user").strip().upper()
    password_input = st.text_input("Contraseña", type="password", key="login_pass")
    
    col_btn, _ = st.columns([1, 1])
    with col_btn:
        if st.button("🔑 Iniciar Sesión", use_container_width=True):
            if matricula_input in USUARIOS_AUTORIZADOS and USUARIOS_AUTORIZADOS[matricula_input]['password'] == password_input:
                user_info = USUARIOS_AUTORIZADOS[matricula_input]
                
                fecha_venc = parsear_fecha(user_info['vencimiento'])
                hoy = datetime.now().date()
                
                if hoy > fecha_venc:
                    st.error(f"⛔ **Suscripción Vencida:** Tu acceso venció el {fecha_venc.strftime('%d/%m/%Y')}. Por favor, renueva tu suscripción para volver a ingresar.")
                else:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = matricula_input
                    st.session_state.tipo_usuario = user_info['tipo']
                    st.session_state.balance_pedagogico = float(user_info['capital_base'])
                    
                    # BLINDAJE DE SESIÓN: Fijar rutas únicas directamente en st.session_state
                    st.session_state.archivo_pos = f"posiciones_{matricula_input}.json"
                    st.session_state.archivo_hist = f"historial_{matricula_input}.json"
                    
                    # Cargar archivos específicos del alumno autenticado
                    if os.path.exists(st.session_state.archivo_pos):
                        st.session_state.posiciones_abiertas = cargar_datos_json(st.session_state.archivo_pos, [])
                    else:
                        st.session_state.posiciones_abiertas = []

                    if os.path.exists(st.session_state.archivo_hist):
                        st.session_state.historial_cerradas = cargar_datos_json(st.session_state.archivo_hist, [])
                    else:
                        st.session_state.historial_cerradas = []
                    
                    st.rerun()
            else:
                st.error("❌ Matrícula o contraseña incorrecta. Verifica con administración.")
    
    st.markdown("---")
    st.markdown("### ¿Aún no tienes tu acceso al Portal?")
    st.write(
        "Obtén acceso a las **Calculadoras Operativas**, **Biblioteca de Guías en PDF** "
        "y **Cápsulas de Psicotrading** por solo **$150 MXN / mes**."
    )

    num_whatsapp = "528136462129"
    mensaje_preset = (
        "¡Hola Daniela! 👋 Vengo del portal web y me gustaría adquirir mi suscripción "
        "a la Membresía Mensual Alema ($150 MXN/mes) para obtener mis credenciales de acceso."
    )

    url_wa = f"https://wa.me/{num_whatsapp}?text={requests.utils.quote(mensaje_preset)}"
    st.link_button("📲 Solicitar Membresía por WhatsApp", url_wa, use_container_width=True)
    
    st.markdown(
        f'''
        <a href="{url_wa}" target="_blank" style="text-decoration: none;">
            <div style="
                background-color: #25D366;
                color: #FFFFFF;
                padding: 12px 20px;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 1rem;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
                margin: 10px 0;
                transition: background-color 0.2s ease;">
                📲 Solicitar Membresía por WhatsApp
            </div>
        </a>
        ''',
        unsafe_allow_html=True)

    st.markdown("<h2 style='text-align: center;'> ¿Deseas Formarte como Trader en ALEMA?</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #a0aec0; font-size: 1.1rem;'>"
        "Conoce nuestro programa educativo integral, herramientas operativas y acompañamiento personalizado."
        "</p>", 
        unsafe_allow_html=True
    )

    col_info1, col_info2 = st.columns(2)

    with col_info1:
        st.markdown("### 📚 Ruta Académica Oficial")
        st.markdown("""
        * **Módulo Básico:** Fundamentos de mercados financieros, estructura de precios y lectura de velas.
        * **Módulo Intermedio:** Metodología institucional, zonas de oferta/demanda y Fibonacci.
        * **Módulo Avanzado:** Wyckoff, liquidez de mercado y modelos de entrada de alta probabilidad.
        * **Módulo Práctico & Psicotrading:** Gestión de riesgo matemática, bitácora y control emocional.
        """)

    with col_info2:
        st.markdown("### 💡 Beneficios del Portal Privado")
        st.markdown("""
        * **Calculadoras Operativas:** Gestión exacta de lotaje y riesgo por operación.
        * **Evaluaciones Progresivas:** Exámenes técnicos revisados directamente por Dirección General.
        * **Constancia Institucional:** Reconocimiento con validez interna al aprobar cada nivel.
        * **Biblioteca y Reportes:** Descarga de manuales en PDF y retroalimentación personalizada.
        """)

    st.divider()

    # --- SECCIÓN DE INSCRIPCIÓN Y WHATSAPP COORDINACIÓN ---
    st.markdown("<h3 style='text-align: center;'>💳 Cuota e Inscripciones</h3>", unsafe_allow_html=True)
    
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p2:
        st.info(
            "📌 **Membresía Elite ALEMA / Acceso al Portal:** **$1890 MXN / mes**\n\n"
            "**Incluye:**\n"
            "* Acceso completo al portal de alumnos\n"
            "* Calculadoras de gestión\n"
            "* Biblioteca digital\n"
            "* Clases personalizadas en vivo vía Zoom\n"
            "* Plataforma Educativa\n"
            "* Journal Alema\n"
            "* Evaluaciones")
            
        num_whatsapp = "528136462129"
        mensaje_preset = (
            "¡Hola Daniela! 👋 Vengo del portal web y me gustaría solicitar información e inscribirme "
            "a ALEMA Trading Academy. ¿Me podrías compartir los datos de pago y requisitos?"
        )

        url_wa = f"https://wa.me/{num_whatsapp}?text={requests.utils.quote(mensaje_preset)}"

        st.markdown(
            f'''
            <a href="{url_wa}" target="_blank" style="text-decoration: none;">
                <button style="
                    width: 100%;
                    background-color: #25D366;
                    color: white;
                    padding: 14px 20px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 16px;
                    font-weight: bold;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;">
                    📲 ¡Quiero Inscribirme! (Contactar a Daniela por WhatsApp)
                </button>
            </a>
            ''',
            unsafe_allow_html=True
        )

    st.markdown("<br><p style='text-align: center; color: #718096;'>© ALEMA Trading Academy. Reservados todos los derechos.</p>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# ⚙️ PANEL DE CONTROL ADMIN (SOLO PARA ADMINS EN SIDEBAR)
# ==========================================
if st.session_state.get("tipo_usuario") == "ADMIN":
    st.sidebar.divider()
    st.sidebar.markdown("### ⚙️ Panel Coordinación Admin")
    
    lista_matriculas = list(USUARIOS_AUTORIZADOS.keys())
    alumno_seleccionado = st.sidebar.selectbox("Gestionar Alumno", lista_matriculas, key="select_admin_alumno")
    
    # --- 1. BOTÓN PARA FORZAR LECTURA DE CAPITAL DESDE GOOGLE SHEETS ---
    if st.sidebar.button("🔄 Sincronizar Capital (Sheets)", use_container_width=True):
        st.cache_data.clear()
        st.sidebar.success(f"Capital de '{alumno_seleccionado}' actualizado desde Google Sheets.")
        st.rerun()
        
    # --- 2. BOTÓN PARA REINICIAR BITÁCORA HISTÓRICA DEL ALUMNO ---
    if st.sidebar.button("🗑️ Reiniciar Bitácora de Alumno", use_container_width=True):
        # Localiza el archivo JSON del alumno seleccionado y lo vacía
        arch_bita_alumno = f"historial_cerradas_{alumno_seleccionado}.json"
        guardar_datos_json(arch_bita_alumno, [])
            
        st.cache_data.clear()
        st.sidebar.success(f"Bitácora de '{alumno_seleccionado}' limpiada a 0.")
        st.rerun()
import streamlit.components.v1 as components

# ==========================================
# 🚀 MENÚ LATERAL Y NAVEGACIÓN SEGÚN ROL (PARTE 5)
# ==========================================

# Verificación de seguridad: solo se ejecuta si el usuario está autenticado
if st.session_state.get("autenticado", False):

    # 1. ENCABEZADO Y LOGO DE LA BARRA LATERAL
    st.sidebar.image("alema trading academy.png", width=180)
    st.sidebar.markdown("### 🎓 ALEMA PORTAL")
    st.sidebar.write(f"Usuario: **{st.session_state.get('usuario_actual', '')}**")
    st.sidebar.caption(f"Rol: {st.session_state.get('tipo_usuario', 'ALUMNO')}")
    st.sidebar.markdown("---")

    # 2. OPCIONES DEL MENÚ SEGÚN EL ROL
    if st.session_state.get("tipo_usuario") in ["ADMIN", "ALUMNO"]:
        opciones_disponibles = [
            "📊 Mi Avance Académico", 
            "🧮 Calculadoras de Lotes", 
            "📓 Trading Journal", 
            "📝 Evaluaciones", 
            "📉 Alema Trade live", 
            "📚 Biblioteca de Guías"
        ]
    else:
        opciones_disponibles = [
            "🧮 Calculadoras de Lotes", 
            "📚 Biblioteca de Guías"
        ]

    # 3. SELECCIÓN DE NAVEGACIÓN
    opcion_menu = st.sidebar.radio(
        "Selecciona una sección:",
        opciones_disponibles,
        key="navegacion_principal"
    )

    # 4. BOTÓN CERRAR SESIÓN
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = ""
        st.session_state.tipo_usuario = "ALUMNO"
        st.rerun()

    # ==========================================
    # ⚙️ PANEL DE CONTROL ADMIN (SOLO PARA ADMINS EN SIDEBAR)
    # ==========================================
    if st.session_state.get("tipo_usuario") == "ADMIN":
        st.sidebar.divider()
        st.sidebar.markdown("### ⚙️ Panel Coordinación Admin")
        
        lista_matriculas = list(USUARIOS_AUTORIZADOS.keys())
        alumno_seleccionado = st.sidebar.selectbox(
    "Gestionar Alumno", 
    lista_matriculas, 
    key=f"select_admin_alumno_{idx}"
)
        
        # --- 1. BOTÓN PARA FORZAR LECTURA DE CAPITAL DESDE GOOGLE SHEETS ---
        if st.sidebar.button("🔄 Sincronizar Capital (Sheets)", use_container_width=True):
            st.cache_data.clear()
            st.sidebar.success(f"Capital de '{alumno_seleccionado}' actualizado desde Google Sheets.")
            st.rerun()
            
        # --- 2. BOTÓN PARA REINICIAR BITÁCORA HISTÓRICA DEL ALUMNO ---
        if st.sidebar.button("🗑️ Reiniciar Bitácora de Alumno", use_container_width=True):
            # Localiza el archivo JSON del alumno seleccionado y lo vacía
            arch_bita_alumno = f"historial_cerradas_{alumno_seleccionado}.json"
            guardar_datos_json(arch_bita_alumno, [])
                
            st.cache_data.clear()
            st.sidebar.success(f"Bitácora de '{alumno_seleccionado}' limpiada a 0.")
            st.rerun()

    # --- SCRIPT DE CIERRE TÁCTIL PARA SAFARI / ANDROID ---
    collapse_script = """
    <script>
        (function() {
            const doc = window.parent.document;
            function closeMobileSidebar() {
                if (window.parent.innerWidth < 768) {
                    const collapseBtn = doc.querySelector('button[data-testid="collapsedControl"]');
                    const sidebarExpanded = doc.querySelector('section[data-testid="stSidebar"][aria-expanded="true"]');
                    if (collapseBtn && sidebarExpanded) {
                        collapseBtn.click();
                    }
                }
            }
            
            setTimeout(() => {
                const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
                if (sidebar) {
                    sidebar.addEventListener('touchend', function(e) {
                        if (e.target.closest('label') || e.target.closest('div[role="radiogroup"]')) {
                            setTimeout(closeMobileSidebar, 300);
                        }
                    }, {passive: true});
                }
            }, 600);
        })();
    </script>
    """
    components.html(collapse_script, height=0, width=0)

    # --- TICKER DE TRADINGVIEW SUPERIOR ---
    ticker_html = """
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {
      "symbols": [
        {"proName": "FX_IDC:EURUSD", "title": "EUR/USD"},
        {"proName": "FX_IDC:GBPUSD", "title": "GBP/USD"},
        {"proName": "FX_IDC:USDJPY", "title": "USD/JPY"},
        {"proName": "FX_IDC:AUDUSD", "title": "AUD/USD"},
        {"proName": "FX_IDC:USDCAD", "title": "USD/CAD"},
        {"proName": "FX_IDC:USDCHF", "title": "USD/CHF"},
        {"proName": "BITSTAMP:BTCUSD", "title": "BTC/USD"}
      ],
      "showSymbolLogo": true,
      "isTransparent": false,
      "displayMode": "adaptive",
      "colorTheme": "dark",
      "locale": "es"
    }
      </script>
    </div>
    <style>
      .tradingview-widget-container {
        background-color: #FF6B00 !important;
        border-radius: 8px;
        overflow: hidden;
      }
    </style>
    """
    components.html(ticker_html, height=78)
# ==========================================
# SECCIÓN: MI AVANCE ACADÉMICO (ALUMNOS/ADMIN)
# ==========================================
if opcion_menu == "📊 Mi Avance Académico":
    st.markdown('<div class="main-title" style="text-align: left;">ALEMA TRADING ACADEMY</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title" style="text-align: left;">Expediente Institucional del Alumno</div>', unsafe_allow_html=True)

    datos_alumno = obtener_avance_alumno(st.session_state.usuario_actual)

    if datos_alumno:
        st.subheader(f"👋 Bienvenid@, {datos_alumno.get('Nombre', 'Alumno')}")
        
        col_av1, col_av2, col_av3 = st.columns(3)
        with col_av1:
            st.metric(label="Módulo Actual", value=str(datos_alumno.get('Modulo_Actual', 'N/A')))
        with col_av2:
            st.metric(label="Progreso General", value=str(datos_alumno.get('Porcentaje', '0%')))
        with col_av3:
            st.metric(label="Estatus de Beca", value=str(datos_alumno.get('Estatus_Beca', 'N/A')))
            
        st.divider()
        
        st.subheader("📌 Indicaciones & Calendario de Evaluación")
        st.info(f"💡 **Nota del Coordinador:** {datos_alumno.get('Notas', 'Sin observaciones registradas.')}")
        
    else:
        st.warning("⚠️ No se encontraron registros de avance para tu matrícula. Consulta con coordinación.")

# ==========================================
# SECCIÓN: CALCULADORAS DE LOTES
# ==========================================
elif opcion_menu == "🧮 Calculadoras de Lotes":
    st.markdown('<div class="main-title" style="text-align: left;">ALEMA TRADING ACADEMY</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title" style="text-align: left;">Módulo Institucional de Gestión de Riesgo y Lotajes</div>', unsafe_allow_html=True)

    tab_operativa, tab_rapida = st.tabs(["⚡ Calculadora Operativa Completa", "🛡️ Calculadora de Lotes Rápidos (Riesgo)"])

    with tab_operativa:
        st.subheader("⚡ Calculadora Operativa & Multi-Activo")
        
        with st.expander("📖 Guía Rápida de Uso"):
            st.markdown("""
            1. **Ingresa el activo:** Escribe el par (ej. `EUR/USD` o `USD/JPY`).
            2. **Define tu riesgo:** Mantén el riesgo por operación preferentemente entre **1% y 2%**.
            3. **Ingresa tu Stop Loss:** Mide los pips en TradingView y colócalos en la casilla.
            4. **Copia tus datos:** Usa el bloque inferior para copiar el lotaje, SL y TP exactos a tu MetaTrader o cTrader.
            """)

        st.divider()

        st.subheader("⚙️ Parámetros de la Operación")
        col1, col2 = st.columns(2)

        with col1:
            par_seleccionado = st.text_input("Par de Divisas / Activo", value="EUR/USD", key="op_par").strip().upper()
            
            symbol_tv = par_seleccionado.replace("/", "").replace("-", "").replace(" ", "")
            tv_url = f"https://es.tradingview.com/chart/?symbol=FX:{symbol_tv}"
            investing_url = "https://es.investing.com/economic-calendar/"
            
            st.link_button("📈 Ver Gráfico en TradingView", tv_url)
            st.link_button("📅 Ver Calendario Económico (Investing)", investing_url)
            
            es_jpy = "JPY" in par_seleccionado
            divisor_pip = 100.0 if es_jpy else 10000.0
            valor_pip_sugerido = 7.0 if es_jpy else 10.0

            if es_jpy:
                st.warning(
                    "⚠️ **Par JPY Detectado:**\n"
                    "• El valor del pip se ajustó a **$7.0 USD/lote**.\n"
                    "• 📌 **Importante:** Verifica el **Precio de Entrada** actual en TradingView."
                )
            
            balance = st.number_input("Balance de la Cuenta ($)", value=200.0, step=10.0, key="op_balance")
            riesgo_pct = st.number_input("Porcentaje de Riesgo (%)", value=2.0, step=0.5, key="op_riesgo")
            sl_pips = st.number_input("Tamaño del Stop Loss (Pips)", value=15.0, step=1.0, key="op_sl_pips")

        with col2:
            tipo_orden = st.selectbox("Tipo de Orden", ["Compra", "Venta"], key="op_tipo_orden")
            
            precio_defecto = 155.200 if es_jpy else 1.08500
            paso_precio = 0.001 if es_jpy else 0.00001
            formato_precio = "%.3f" if es_jpy else "%.5f"
            
            precio_entrada = st.number_input(
                "Precio de Entrada", 
                value=precio_defecto, 
                step=paso_precio, 
                format=formato_precio,
                key=f"op_entrada_{es_jpy}"
            )
            
            valor_pip = st.number_input("Valor del Pip por Lote Estándar ($)", value=valor_pip_sugerido, step=0.5, key=f"op_val_pip_{es_jpy}")
            ratio = st.number_input("Ratio (Riesgo:Beneficio)", value=3.0, step=0.5, key="op_ratio")

        dinero_arriesgar = balance * (riesgo_pct / 100.0)
        lotaje = dinero_arriesgar / (sl_pips * valor_pip) if sl_pips > 0 and valor_pip > 0 else 0.0
        tp_pips = sl_pips * ratio
        ganancia = lotaje * tp_pips * valor_pip

        distancia_sl_precio = sl_pips / divisor_pip
        distancia_tp_precio = tp_pips / divisor_pip

        if tipo_orden == "Compra":
            precio_sl = precio_entrada - distancia_sl_precio
            precio_tp = precio_entrada + distancia_tp_precio
        else:
            precio_sl = precio_entrada + distancia_sl_precio
            precio_tp = precio_entrada - distancia_tp_precio

        str_sl = f"{precio_sl:.3f}" if es_jpy else f"{precio_sl:.5f}"
        str_tp = f"{precio_tp:.3f}" if es_jpy else f"{precio_tp:.5f}"

        st.divider()

        if riesgo_pct <= 2.0:
            st.success(f"🟢 **Gestión Institucional Excelente ({riesgo_pct}%):** Riesgo controlado.")
        elif riesgo_pct <= 5.0:
            st.warning(f"🟠 **Riesgo Moderado ({riesgo_pct}%):** Requiere confirmación de alta probabilidad.")
        else:
            st.error(f"🔴 **Alerta de Sobrerriesgo ({riesgo_pct}%):** Reduce la exposición.")

        st.subheader("📊 Resultados de Ejecución")
        res_col1, res_col2 = st.columns(2)

        with res_col1:
            st.metric(label="Riesgo Máximo ($)", value=f"${dinero_arriesgar:.2f}")
            st.metric(label="Lotaje Exacto", value=f"{lotaje:.2f}")
            st.metric(label="Precio Stop Loss", value=str_sl)

        with res_col2:
            st.metric(label="Ganancia Potencial ($)", value=f"${ganancia:.2f}")
            st.metric(label="Tamaño TP (PIPS)", value=f"{tp_pips:.0f} pips")
            st.metric(label="Precio Take Profit", value=str_tp)

        st.subheader("📋 Datos Listos para Ejecutar")
        st.markdown(f"""
        <div class="copy-box">
        <b>{par_seleccionado}</b> | <b>{tipo_orden.upper()}</b><br>
        🔹 Lotaje: <b>{lotaje:.2f}</b><br>
        🛑 Stop Loss: <b>{str_sl}</b><br>
        🎯 Take Profit: <b>{str_tp}</b>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("📉 Distribución de Balance")
        capital_seguro = max(0.0, balance - dinero_arriesgar)

        fig = go.Figure(data=[go.Pie(
            labels=['Capital Seguro', 'Capital en Riesgo'],
            values=[capital_seguro, dinero_arriesgar],
            hole=.5,
            marker_colors=['#10B981', '#FF6B00']
        )])

        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            height=220,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#F1F5F9'),
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab_rapida:
        st.subheader("🛡️ Calculadora Rápida de Lotaje y Riesgo")
        st.write("Calcula de forma inmediata el lotaje exacto según tu capital y tolerancia de riesgo.")

        col_r1, col_r2 = st.columns(2)

        with col_r1:
            bal_r = st.number_input("Balance Total de la Cuenta ($)", value=500.0, step=50.0, key="rap_balance")
            riesgo_r = st.number_input("Porcentaje de Riesgo a Arriesgar (%)", value=1.0, step=0.5, key="rap_riesgo")

        with col_r2:
            sl_r = st.number_input("Stop Loss en Pips / Puntos", value=20.0, step=1.0, key="rap_sl")
            val_pip_r = st.number_input("Valor por Pip (1 Lote Estándar $)", value=10.0, step=0.5, key="rap_pip_val")

        monto_arriesgar = bal_r * (riesgo_r / 100.0)
        lotaje_rapido = monto_arriesgar / (sl_r * val_pip_r) if sl_r > 0 and val_pip_r > 0 else 0.0

        st.divider()

        st.subheader("🎯 Resultado de Lotaje Recomendado")
        
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            st.metric(label="Monto Máximo a Arriesgar", value=f"${monto_arriesgar:.2f}")
        with c_res2:
            st.metric(label="Lote Exacto a Operar", value=f"{lotaje_rapido:.2f} Lotes")

        st.markdown(f"""
        <div class="copy-box" style="text-align: center; font-size: 18px;">
        💡 <b>LOTAGE SUGERIDO:</b> <span style="color:#FF6B00; font-size: 22px;"><b>{lotaje_rapido:.2f}</b></span>
        </div>
        """, unsafe_allow_html=True)
# ==========================================
# SECCIÓN: TRADING JOURNAL
# ==========================================
elif opcion_menu == "📓 Trading Journal":
    st.markdown('<div class="main-title" style="text-align: left;">ALEMA TRADING ACADEMY</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title" style="text-align: left;">Journal Institucional de Operaciones y Bitácora Psicológica</div>', unsafe_allow_html=True)

    @st.cache_data(ttl=3)
    def cargar_journal_persiste(matricula_usuario):
        try:
            df = pd.read_csv(URL_JOURNAL_CSV, dtype=str)
            df.columns = df.columns.str.strip()
            
            col_mat = [c for c in df.columns if 'Matricula' in c or 'Matrícula' in c]
            if col_mat:
                nombre_col_mat = col_mat[0]
                df_user = df[df[nombre_col_mat].str.strip().str.upper() == matricula_usuario].copy()
            else:
                df_user = pd.DataFrame()

            col_res = [c for c in df.columns if 'Resultado' in c or 'USD' in c or 'pnl' in c.lower()]
            if col_res:
                df_user['Resultado_Num'] = pd.to_numeric(df_user[col_res[0]], errors='coerce').fillna(0.0)
            else:
                df_user['Resultado_Num'] = 0.0

            return df_user
        except Exception:
            return pd.DataFrame()

    df_user_journal = cargar_journal_persiste(st.session_state.usuario_actual)
    total_trades = len(df_user_journal)

    if total_trades > 0:
        pnl_total = df_user_journal['Resultado_Num'].sum()
        wins = len(df_user_journal[df_user_journal['Resultado_Num'] > 0])
        win_rate = (wins / total_trades) * 100
    else:
        pnl_total = 0.0
        win_rate = 0.0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total de Trades", f"{total_trades}")
    with m2:
        st.metric("Win Rate (%)", f"{win_rate:.1f}%")
    with m3:
        st.metric("P&L Total ($ USD)", f"${pnl_total:.2f}")

    st.divider()

    st.subheader("✍️ Registrar Nueva Operación Manual")
    
    with st.form("form_journal_directo", clear_on_submit=True):
        col_j1, col_j2 = st.columns(2)
        
        with col_j1:
            j_fecha = st.date_input("Fecha", value=datetime.now())
            j_activo = st.text_input("Activo / Par", value="EUR/USD").strip().upper()
            j_tipo = st.selectbox("Tipo", ["BUY", "SELL"])
            j_lotes = st.number_input("Lotes Operados", value=0.10, step=0.01)
            
        with col_j2:
            j_pips = st.number_input("Pips (+/-)", value=20.0, step=1.0)
            j_pnl = st.number_input("Resultado ($ USD)", value=20.0, step=1.0)
            j_emocion = st.selectbox("Estado Emocional / Psicotrading", [
                "🟢 Disciplinado",
                "🟡 Ansiedad",
                "🔴 Impulsivo / FOMO",
                "🔴 Revancha"
            ])
            j_link = st.text_input("Enlace / Captura de TradingView", value="")

        j_notas = st.text_area("Observaciones / Conclusión Técnica", placeholder="¿Por qué entraste? ¿Qué confirmó tu setup?")
        
        submitted = st.form_submit_button("💾 Guardar en Journal", use_container_width=True)
        
        if submitted:
            form_data = {
                "entry.990498500": st.session_state.usuario_actual,
                "entry.155506709": str(j_fecha),
                "entry.906926856": j_activo,
                "entry.1849778551": j_tipo,
                "entry.974887529": str(j_lotes),
                "entry.46118986": str(j_pips),
                "entry.1003289205": str(j_pnl),
                "entry.372443422": j_emocion,
                "entry.332810614": j_notas,
                "entry.635428194": j_link
            }
            
            try:
                res = requests.post(URL_FORM_RESPONSE, data=form_data)
                if res.status_code == 200 or res.status_code == 0:
                    st.success("✅ Operación registrada exitosamente en tu bitácora permanente.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("⚠️ Error al registrar la operación en Google Sheets.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

    st.divider()

    st.subheader("📋 Bitácora Histórica Permanente")
    if not df_user_journal.empty:
        df_mostrar = df_user_journal.drop(columns=['Resultado_Num'], errors='ignore')
        st.dataframe(df_mostrar, use_container_width=True)
    else:
        st.info("💡 Aún no tienes trades guardados en tu historial permanente.")


# ==========================================
# SIMULADOR INSTITUCIONAL ALEMA TRADING ACADEMY
# (VERSIÓN CONECTADA A BASE DE DATOS GOOGLE SHEETS CON CHALLENGE)
# ==========================================
    import json
    import os
    import time
    from datetime import datetime, timedelta
    import requests
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    from streamlit_autorefresh import st_autorefresh

    # Recarga automática de la pantalla cada 4 segundos
    st_autorefresh(interval=4000, key="auto_refresh_terminal_forex_live")

    # --- IDENTIFICADOR DE USUARIO Y RUTAS PERSISTENTES ---
    usuario = st.session_state.get("usuario_actual", "alema")
    ARCH_PERSISTENCIA_ACTIVAS = f"posiciones_activas_{usuario}.json"
    ARCH_PERSISTENCIA_HISTORIAL = f"historial_cerradas_{usuario}.json"

    def cargar_datos_json(archivo, valor_defecto):
        if os.path.exists(archivo):
            try:
                with open(archivo, "r") as f:
                    return json.load(f)
            except Exception:
                return valor_defecto
        return valor_defecto

    def guardar_datos_json(archivo, datos):
        try:
            with open(archivo, "w") as f:
                json.dump(datos, f, indent=4)
        except Exception:
            pass

    # --- FUNCIÓN DE CONEXIÓN Y LECTURA DE CAPITAL Y CHALLENGE DESDE GOOGLE SHEETS ---
    @st.cache_data(ttl=10) # Se actualiza cada 10 segundos desde la base de datos
    def obtener_datos_usuario_desde_sheets(usuario_target):
        capital_defecto = 300.00
        nivel_defecto = "Nivel 1"
        try:
            sheet_url = "https://docs.google.com/spreadsheets/d/1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA/export?format=csv&gid=0"
            df = pd.read_csv(sheet_url)
            df.columns = [str(c).strip() for c in df.columns]
            
            # Identificar columnas de Usuario, Capital y Challenge en la hoja
            col_user = next((c for c in df.columns if any(k in c.lower() for k in ["usuario", "matricula", "user"])), None)
            col_cap = next((c for c in df.columns if any(k in c.lower() for k in ["capital", "monto", "balance"])), None)
            col_challenge = next((c for c in df.columns if any(k in c.lower() for k in ["challenge", "nivel", "level"])), None)
            
            if col_user:
                filtro = df[df[col_user].astype(str).str.strip().str.lower() == str(usuario_target).strip().lower()]
                if not filtro.empty:
                    # Lectura de Capital
                    if col_cap:
                        val_str = str(filtro[col_cap].values[0]).replace("$", "").replace(",", "").strip()
                        capital_defecto = float(val_str)
                    # Lectura de Nivel de Challenge
                    if col_challenge:
                        val_chal = str(filtro[col_challenge].values[0]).strip()
                        if val_chal and val_chal.lower() != "nan":
                            nivel_defecto = val_chal
        except Exception:
            pass
        return capital_defecto, nivel_defecto

    # Cargar operaciones activas e historial
    st.session_state.posiciones_abiertas = cargar_datos_json(ARCH_PERSISTENCIA_ACTIVAS, [])
    st.session_state.historial_cerradas = cargar_datos_json(ARCH_PERSISTENCIA_HISTORIAL, [])

    # CÁLCULO DINÁMICO DEL BALANCE Y ASIGNACIÓN DE NIVEL DE CHALLENGE
    capital_base_sheets, nivel_challenge_sheets = obtener_datos_usuario_desde_sheets(usuario)
    pnl_acumulado_historico = sum(float(trade.get("Beneficio", 0.0)) for trade in st.session_state.historial_cerradas)
    st.session_state.balance_pedagogico = capital_base_sheets + pnl_acumulado_historico
    st.session_state.nivel_challenge = nivel_challenge_sheets
    st.session_state.current_loaded_user = usuario

    if 'cache_precios_forex' not in st.session_state:
        st.session_state.cache_precios_forex = {}
    if 'ultimo_tiempo_api' not in st.session_state:
        st.session_state.ultimo_tiempo_api = {}

    def calcular_pnl_institucional(activo, tipo, entrada, salida, lotes):
        diferencia = (salida - entrada) if tipo == "BUY" else (entrada - salida)
        
        if "XAU" in activo: return diferencia * 100.0 * lotes
        elif "BTC" in activo: return diferencia * 1.0 * lotes
        elif "WTI" in activo or "BRENT" in activo: return diferencia * 1000.0 * lotes
        elif any(idx in activo for idx in ["US30", "SPX500", "NAS100", "GER40"]): return diferencia * 1.0 * lotes
        elif "JPY" in activo:
            valor_pip_usd_por_lote = 1000.0 / salida if salida != 0 else 6.80
            pips = diferencia * 100.0
            return pips * valor_pip_usd_por_lote * lotes
        else:
            return diferencia * 100000.0 * lotes

    def obtener_config_activo(simbolo):
        if "JPY" in simbolo: return 3, "%.3f", 0.001, 0.100, 0.200, 0.015
        elif "XAU" in simbolo: return 2, "%.2f", 0.10, 2.00, 4.00, 0.35
        elif "WTI" in simbolo or "BRENT" in simbolo: return 2, "%.2f", 0.01, 0.30, 0.60, 0.04
        elif "BTC" in simbolo: return 2, "%.2f", 1.0, 100.0, 200.0, 25.00
        elif any(idx in simbolo for idx in ["US30", "NAS100", "GER40"]): return 2, "%.2f", 1.0, 20.0, 40.0, 2.00
        elif "SPX" in simbolo: return 2, "%.2f", 0.10, 4.00, 8.00, 0.40
        else: return 5, "%.5f", 0.00001, 0.00100, 0.00200, 0.00012

    # Estilos CSS
    st.markdown("""
        <style>
            .mt5-terminal-card { background-color: #131722; border: 1px solid #2A2E39; padding: 10px 15px; border-radius: 4px; margin-bottom: 8px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .live-ticker-price { color: #f59e0b; font-weight: 700; font-size: 15px; }
            .live-ticker-bid { color: #ef5350; font-weight: 700; font-size: 15px; }
            .live-ticker-ask { color: #26a69a; font-weight: 700; font-size: 15px; }
            .mt5-table-container { overflow-x: auto; border: 1px solid #2A2E39; border-radius: 4px; margin-top: 10px; }
            .mt5-table { width: 100%; border-collapse: collapse; font-family: 'Segoe UI', Tahoma, sans-serif; font-size: 13px; background-color: #131722; color: #d1d4dc; }
            .mt5-table th { background-color: #1e222d; color: #848e9c; padding: 8px 12px; text-align: left; border-bottom: 1px solid #2A2E39; font-weight: 600; white-space: nowrap; }
            .mt5-table td { padding: 7px 12px; border-bottom: 1px solid #1e222d; white-space: nowrap; }
            .mt5-buy { color: #2962FF; font-weight: 600; }
            .mt5-sell { color: #ef5350; font-weight: 600; }
            .mt5-profit { color: #26a69a; font-weight: 600; }
            .mt5-loss { color: #ef5350; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title" style="text-align: left; font-size: 24px; font-weight: 700;">ALEMA TRADING ACADEMY | Terminal Institucional</div>', unsafe_allow_html=True)

    lista_activos = [
        "EURUSD", "GBPUSD", "USDJPY", "EURJPY", "AUDUSD", "USDCAD", "USDCHF", "GBPJPY", 
        "XAUUSD", "WTIUSD", "BRENTUSD", 
        "US30", "SPX500", "NAS100", "GER40", "BTCUSD"
    ]

    par_activo = st.selectbox("Símbolo de Mercado", lista_activos, key="select_chart_asset_forex")

    # --- NÚCLEO DE PRECIOS CON PROTECCIÓN DE API ---
    def obtener_cotizacion_completa(simbolo):
        dec, _, step_val, _, _, spread_val = obtener_config_activo(simbolo)
        simbolos_map = { "EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "USDJPY": "USD/JPY", "EURJPY": "EUR/JPY", "AUDUSD": "AUD/USD", "USDCAD": "USD/CAD", "USDCHF": "USD/CHF", "GBPJPY": "GBP/JPY", "XAUUSD": "XAU/USD", "WTIUSD": "WTI/USD", "BRENTUSD": "BRENT/USD", "US30": "US30", "SPX500": "SPX", "NAS100": "NDX", "GER40": "DAX", "BTCUSD": "BTC/USD" }
        simbolo_api = simbolos_map.get(simbolo, "EUR/USD")
        api_key = "6223c6d78f7a43b2872fc3acbb3f578e"
        ahora = time.time()
        tiempo_ultimo = st.session_state.ultimo_tiempo_api.get(simbolo, 0)
        
        if ahora - tiempo_ultimo > 45:
            try:
                url = f"https://api.twelvedata.com/price?symbol={simbolo_api}&apikey={api_key}"
                res = requests.get(url, timeout=3)
                if res.status_code == 200:
                    data = res.json()
                    if "price" in data:
                        st.session_state.cache_precios_forex[simbolo] = float(data["price"])
            except Exception:
                pass
            finally:
                st.session_state.ultimo_tiempo_api[simbolo] = ahora

        if simbolo in st.session_state.cache_precios_forex:
            precio_base = st.session_state.cache_precios_forex[simbolo]
        else:
            precios_fallback = { "EURUSD": 1.15919, "GBPUSD": 1.31210, "USDJPY": 146.850, "EURJPY": 162.450, "XAUUSD": 2512.30, "US30": 41200.00, "BTCUSD": 62500.00 }
            precio_base = precios_fallback.get(simbolo, 1.0000)
            st.session_state.cache_precios_forex[simbolo] = precio_base

        ruido = np.random.normal(0, step_val * 1.2)
        precio_vivo = round(precio_base + ruido, dec)
        precio_bid = precio_vivo
        precio_ask = round(precio_bid + spread_val, dec)

        return precio_bid, precio_ask, precio_vivo

    precios_tick_actual = {}
    
    def get_precio_sincronizado(simbolo):
        if simbolo not in precios_tick_actual:
            precios_tick_actual[simbolo] = obtener_cotizacion_completa(simbolo)
        return precios_tick_actual[simbolo]

    bid_actual, ask_actual, precio_vivo_actual = get_precio_sincronizado(par_activo)

    if 'mercado_forex_df' not in st.session_state:
        st.session_state.mercado_forex_df = {}

    def obtener_dataframe_forex(simbolo, precio_actual):
        if simbolo not in st.session_state.mercado_forex_df:
            fechas = [datetime.now() - timedelta(minutes=15 * i) for i in range(50)][::-1]
            vol = precio_actual * 0.0004
            np.random.seed(123)
            closes = np.linspace(precio_actual - (vol * 4), precio_actual, 50) + np.random.normal(0, vol * 0.2, 50)
            opens = closes + np.random.normal(0, vol * 0.1, 50)
            highs = np.maximum(opens, closes) + abs(np.random.normal(0, vol * 0.2, 50))
            lows = np.minimum(opens, closes) - abs(np.random.normal(0, vol * 0.2, 50))
            
            df_init = pd.DataFrame({'Open': opens, 'High': highs, 'Low': lows, 'Close': closes}, index=fechas)
            st.session_state.mercado_forex_df[simbolo] = df_init
            
        df = st.session_state.mercado_forex_df[simbolo]
        df.iloc[-1, df.columns.get_loc('Close')] = precio_actual
        df.iloc[-1, df.columns.get_loc('High')] = max(df.iloc[-1]['Open'], max(df.iloc[-1]['High'], precio_actual))
        df.iloc[-1, df.columns.get_loc('Low')] = min(df.iloc[-1]['Open'], min(df.iloc[-1]['Low'], precio_actual))
        return df

    df_history = obtener_dataframe_forex(par_activo, bid_actual)

    # --- MONITOREO DE ORDENES ACTIVAS (CIERRE EXACTO ECN) ---
    if st.session_state.posiciones_abiertas:
        posiciones_conservadas = []
        hubo_cambios_auto = False

        for pos in st.session_state.posiciones_abiertas:
            sim_pos = pos["activo"]
            dec_pos, _, _, _, _, _ = obtener_config_activo(sim_pos)
            
            p_bid, p_ask, _ = get_precio_sincronizado(sim_pos)
            
            pos["bid_vela_actual"] = p_bid
            pos["ask_vela_actual"] = p_ask

            tp_exacto = round(pos["tp"], dec_pos)
            sl_exacto = round(pos["sl"], dec_pos)

            cierre_por_tp_sl = False
            precio_ejecucion_salida = p_bid if pos["tipo"] == "BUY" else p_ask

            if pos["tipo"] == "BUY":
                if p_bid >= tp_exacto:
                    cierre_por_tp_sl = True
                    precio_ejecucion_salida = tp_exacto
                elif p_bid <= sl_exacto:
                    cierre_por_tp_sl = True
                    precio_ejecucion_salida = sl_exacto
            else: # SELL
                if p_ask <= tp_exacto:
                    cierre_por_tp_sl = True
                    precio_ejecucion_salida = tp_exacto
                elif p_ask >= sl_exacto:
                    cierre_por_tp_sl = True
                    precio_ejecucion_salida = sl_exacto

            if cierre_por_tp_sl:
                pnl_real = calcular_pnl_institucional(sim_pos, pos["tipo"], pos["entrada"], precio_ejecucion_salida, pos["lotes"])
                
                st.session_state.balance_pedagogico += pnl_real
                
                registro_historial = {
                    "Tipo": pos['tipo'].lower(),
                    "Volumen": pos['lotes'],
                    "Símbolo": sim_pos,
                    "S / L": sl_exacto,
                    "T / P": tp_exacto,
                    "Tiempo Cierre": datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
                    "Precio Cierre": precio_ejecucion_salida,
                    "Beneficio": round(pnl_real, 2)
                }
                st.session_state.historial_cerradas.append(registro_historial)
                guardar_datos_json(ARCH_PERSISTENCIA_HISTORIAL, st.session_state.historial_cerradas)
                hubo_cambios_auto = True
            else:
                posiciones_conservadas.append(pos)

        if hubo_cambios_auto:
            st.session_state.posiciones_abiertas = posiciones_conservadas
            guardar_datos_json(ARCH_PERSISTENCIA_ACTIVAS, st.session_state.posiciones_abiertas)
            st.rerun()

    # --- DASHBOARD Y GRÁFICOS CON VISUALIZACIÓN DE CHALLENGE Y ROL ADMIN ---
    es_admin = st.session_state.get("tipo_usuario") == "ADMIN"

    if es_admin:
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    else:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    with col_m1: 
        st.metric("Balance Base", f"${st.session_state.balance_pedagogico:,.2f}")
    with col_m2:
        pnl_flotante_total = sum([
            calcular_pnl_institucional(p["activo"], p["tipo"], p["entrada"], p.get("bid_vela_actual", p["entrada"]) if p["tipo"] == "BUY" else p.get("ask_vela_actual", p["entrada"]), p["lotes"]) 
            for p in st.session_state.posiciones_abiertas
        ])
        st.metric("Beneficio Flotante", f"${pnl_flotante_total:,.2f}", delta=f"${pnl_flotante_total:,.2f}")
    with col_m3: 
        st.metric("Posiciones Activas", f"{len(st.session_state.posiciones_abiertas)}")
    with col_m4:
        st.metric("Fase Challenge", st.session_state.get("nivel_challenge", "Nivel 1"))

    if es_admin:
        with col_m5: 
            if st.button("🔄 Sincronizar Sheets"):
                st.cache_data.clear()
                st.rerun()

    st.divider()

    col_grafico, col_panel = st.columns([2.4, 1.0])
    n_decimals, formato_str, step_val, dist_sl, dist_tp, spread_val = obtener_config_activo(par_activo)

    with col_grafico:
        st.markdown(
            f"<div style='color: #94A3B8; font-size: 13px; margin-bottom: 4px;'>"
            f"Gráfico {par_activo} | Precio Actual: <span class='live-ticker-price'>{formato_str % precio_vivo_actual}</span> | "
            f"BID: <span class='live-ticker-bid'>{formato_str % bid_actual}</span> | ASK: <span class='live-ticker-ask'>{formato_str % ask_actual}</span> | "
            f"Spread: <b style='color:#d1d4dc;'>{formato_str % spread_val}</b></div>", unsafe_allow_html=True
        )

        fig = go.Figure()
        if not df_history.empty:
            fig.add_trace(go.Candlestick(x=df_history.index, open=df_history['Open'], high=df_history['High'], low=df_history['Low'], close=df_history['Close'], name=par_activo, increasing_line_color='#26a69a', decreasing_line_color='#ef5350'))

        for pos in st.session_state.posiciones_abiertas:
            if pos["activo"] == par_activo:
                fig.add_hline(y=pos["entrada"], line_dash="dash", line_color="#2962FF", annotation_text=f"Entrada ({pos['entrada']})")
                fig.add_hline(y=pos["tp"], line_dash="dot", line_color="#26a69a", annotation_text=f"TP ({pos['tp']})")
                fig.add_hline(y=pos["sl"], line_dash="dot", line_color="#ef5350", annotation_text=f"SL ({pos['sl']})")

        fig.update_layout(template="plotly_dark", paper_bgcolor="#131722", plot_bgcolor="#131722", height=430, margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(showgrid=True, gridcolor='#2A2E39', rangeslider=dict(visible=False)), yaxis=dict(showgrid=True, gridcolor='#2A2E39', zeroline=False), dragmode='pan')
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True, 'displaylogo': False})

    with col_panel:
        st.markdown("### Nueva Orden")
        sim_tipo = st.radio("Dirección", ["BUY", "SELL"], horizontal=True, key="sim_dir_forex")
        sim_lotes = st.number_input("Volumen (Lotes)", value=0.10, min_value=0.01, step=0.01)
        
        precio_ref_orden = ask_actual if sim_tipo == "BUY" else bid_actual

        key_sl = f"sim_precio_sl_{par_activo}_{sim_tipo}"
        key_tp = f"sim_precio_tp_{par_activo}_{sim_tipo}"

        if key_sl not in st.session_state:
            st.session_state[key_sl] = float(round(precio_ref_orden - dist_sl if sim_tipo == "BUY" else precio_ref_orden + dist_sl, n_decimals))
        if key_tp not in st.session_state:
            st.session_state[key_tp] = float(round(precio_ref_orden + dist_tp if sim_tipo == "BUY" else precio_ref_orden - dist_tp, n_decimals))

        sim_precio_sl = st.number_input("Stop Loss", format=formato_str, step=step_val, key=key_sl)
        sim_precio_tp = st.number_input("Take Profit", format=formato_str, step=step_val, key=key_tp)

        texto_boton = "🟢 EJECUTAR ORDEN DE COMPRA" if sim_tipo == "BUY" else "🔴 EJECUTAR ORDEN DE VENTA"
        
        if st.button(texto_boton, use_container_width=True):
            nueva_orden = {
                "id": int(datetime.now().timestamp()),
                "tiempo_apertura": datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
                "activo": par_activo, "tipo": sim_tipo, "lotes": float(sim_lotes),
                "entrada": float(precio_ref_orden), "sl": float(sim_precio_sl), "tp": float(sim_precio_tp),
                "bid_vela_actual": float(bid_actual), "ask_vela_actual": float(ask_actual)
            }
            st.session_state.posiciones_abiertas.append(nueva_orden)
            guardar_datos_json(ARCH_PERSISTENCIA_ACTIVAS, st.session_state.posiciones_abiertas)
            st.rerun()

    # --- POSICIONES ACTIVAS ---
    st.markdown("### Posiciones Abiertas (Monitoreo ECN en Vivo)")
    if st.session_state.posiciones_abiertas:
        for idx, pos in enumerate(st.session_state.posiciones_abiertas):
            p_salida = pos.get("bid_vela_actual", pos["entrada"]) if pos["tipo"] == "BUY" else pos.get("ask_vela_actual", pos["entrada"])
            dec_pos, fmt_pos, _, _, _, _ = obtener_config_activo(pos["activo"])
            pnl_card = calcular_pnl_institucional(pos["activo"], pos["tipo"], pos["entrada"], p_salida, pos["lotes"])

            st.markdown(f"""
                <div class="mt5-terminal-card">
                    <b>{pos['activo']}</b> | Tipo: <span style="color: {'#26a69a' if pos['tipo']=='BUY' else '#ef5350'}">{pos['tipo']}</span> | 
                    Entrada: <code>{fmt_pos % pos['entrada']}</code> | Salida Actual: <code style="color: #26a69a;">{fmt_pos % p_salida}</code> | 
                    TP: <span style="color:#26a69a;">{fmt_pos % pos['tp']}</span> | SL: <span style="color:#ef5350;">{fmt_pos % pos['sl']}</span> | 
                    PnL: <b style="color: {'#26a69a' if pnl_card>=0 else '#ef5350'}">${pnl_card:,.2f} USD</b>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Cerrar Manual #{pos['id']}", key=f"btn_close_{pos['id']}_{idx}"):
                st.session_state.balance_pedagogico += pnl_card
                st.session_state.historial_cerradas.append({
                    "Tipo": pos['tipo'].lower(), "Volumen": pos['lotes'], "Símbolo": pos['activo'],
                    "S / L": pos['sl'], "T / P": pos['tp'], "Tiempo Cierre": datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
                    "Precio Cierre": round(p_salida, dec_pos), "Beneficio": round(pnl_card, 2)
                })
                guardar_datos_json(ARCH_PERSISTENCIA_HISTORIAL, st.session_state.historial_cerradas)
                st.session_state.posiciones_abiertas.pop(idx)
                guardar_datos_json(ARCH_PERSISTENCIA_ACTIVAS, st.session_state.posiciones_abiertas)
                st.rerun()
    else:
        st.info("No hay posiciones activas.")

    # --- BITÁCORA ---
    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.get("tipo_usuario") == "ADMIN":
        col_tit_bita, col_btn_bita = st.columns([3.0, 1.0])
        with col_tit_bita: 
            st.markdown("### Bitácora Histórica")
        with col_btn_bita:
            if st.button("🗑️ Limpiar Historial"):
                st.session_state.historial_cerradas = []
                guardar_datos_json(ARCH_PERSISTENCIA_HISTORIAL, [])
                st.rerun()
    else:
        st.markdown("### Bitácora Histórica")

    if st.session_state.historial_cerradas:
        filas_html = []
        for item in reversed(st.session_state.historial_cerradas):
            _, fmt_pos, _, _, _, _ = obtener_config_activo(item.get("Símbolo", "EURUSD"))
            filas_html.append(
                f'<tr><td>{item.get("Tiempo Cierre")}</td><td class="{"mt5-buy" if item.get("Tipo")=="buy" else "mt5-sell"}">{item.get("Tipo")}</td>'
                f'<td>{item.get("Volumen"):.2f}</td><td>{item.get("Símbolo")}</td><td>{fmt_pos % item.get("S / L")}</td>'
                f'<td>{fmt_pos % item.get("T / P")}</td><td>{fmt_pos % item.get("Precio Cierre")}</td>'
                f'<td class="{"mt5-profit" if item.get("Beneficio")>=0 else "mt5-loss"}">{item.get("Beneficio"):+.2f}</td></tr>'
            )
        st.markdown(f'<div class="mt5-table-container"><table class="mt5-table"><thead><tr><th>Tiempo</th><th>Tipo</th><th>Vol.</th><th>Símbolo</th><th>S/L</th><th>T/P</th><th>Precio Cierre</th><th>Beneficio</th></tr></thead><tbody>{"".join(filas_html)}</tbody></table></div>', unsafe_allow_html=True)
    else:
        st.info("Aún no hay operaciones cerradas.")


# ==========================================
# MENÚ: BIBLIOTECA DE GUÍAS
# ==========================================
elif opcion_menu == "📚 Biblioteca de Guías":
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
        st.success(f"📄 Documento seleccionado: **{guia_seleccionada}**")
        
        with open(archivo_pdf, "rb") as f:
            pdf_bytes = f.read()

        st.download_button(
            label=f"📥 Abrir / Descargar Guía Completa ({guia_seleccionada})",
            data=pdf_bytes,
            file_name=archivo_pdf,
            mime="application/pdf",
            use_container_width=True,
            key="btn_descarga_pdf"
        )
        
        st.info("💡 **Recomendación para Celulares:** Presiona el botón naranja superior para abrir el manual directamente en tu teléfono.")
    else:
        st.warning(f"⚠️ El archivo `{archivo_pdf}` no se encuentra en el repositorio.")

# ==========================================
# SECCIÓN: EVALUACIONES Y CONTROL ACADÉMICO
# ==========================================
elif opcion_menu == "📝 Evaluaciones":
    import streamlit as st
    import pandas as pd
    import json
    import os
    import io
    from datetime import datetime

    st.markdown('<div class="main-title" style="text-align: left;">ALEMA TRADING ACADEMY</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title" style="text-align: left;">Sistema Progresivo de Evaluaciones y Certificaciones Oficiales</div>', unsafe_allow_html=True)

    usuario_actual = st.session_state.get("usuario_actual", "DIRALEX")
    es_admin = (usuario_actual.upper() == "DIRALEX")

    # Módulos oficiales de la academia
    LISTA_MODULOS = [
        "Básico",
        "Básico Intermedio",
        "Intermedio",
        "Intermedio Avanzado",
        "Avanzado",
        "Práctico"
    ]

    # Rutas de almacenamiento local
    FILE_BANCO_EXAMENES = "bd_banco_examenes.json"
    FILE_DESBLOQUEOS = "bd_desbloqueos_alumnos.json"
    FILE_RESPUESTAS = "bd_respuestas_evaluaciones.json"
    FOLDER_EXCEL_UPLOADS = "archivos_excel_evaluaciones"
    FOLDER_CERTIFICADOS = "certificados_oficiales"

    # Crear carpetas si no existen
    for folder in [FOLDER_EXCEL_UPLOADS, FOLDER_CERTIFICADOS]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # --- FUNCIONES DE PERSISTENCIA JSON ---
    def cargar_json_local(filepath, default):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def guardar_json_local(filepath, data):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    banco_examenes = cargar_json_local(FILE_BANCO_EXAMENES, {})
    permisos_alumnos = cargar_json_local(FILE_DESBLOQUEOS, {})
    respuestas_evals = cargar_json_local(FILE_RESPUESTAS, [])

    # Permiso inicial por defecto para alumnos nuevos
    if usuario_actual not in permisos_alumnos:
        permisos_alumnos[usuario_actual] = ["Básico"]
        guardar_json_local(FILE_DESBLOQUEOS, permisos_alumnos)

    # --- PESTAÑAS DE NAVEGACIÓN SEGÚN ROL ---
    if es_admin:
        tab_alumnos, tab_historial, tab_crear, tab_permisos, tab_coordinacion, tab_archivos = st.tabs([
            "📚 Ruta Académica", 
            "📊 Mis Resultados", 
            "➕ Cargar Exámenes (ADMIN)", 
            "🔓 Gestor Candados (ADMIN)", 
            "👑 Revisión / Dictamen (ADMIN)",
            "📁 Archivos y Excel (ADMIN)"
        ])
    else:
        tab_alumnos, tab_historial = st.tabs(["📚 Ruta Académica", "📊 Mis Resultados y Certificados"])

    # -------------------------------------------------------------
    # PESTAÑA 1: RUTA ACADÉMICA Y PRESENTACIÓN DE EXÁMENES
    # -------------------------------------------------------------
    with tab_alumnos:
        st.subheader("🗺️ Ruta Institucional de Aprendizaje")
        st.caption("Selecciona tu módulo actual para presentar tus exámenes programados.")

        modulos_desbloqueados = permisos_alumnos.get(usuario_actual, ["Básico"])

        for modulo in LISTA_MODULOS:
            esta_desbloqueado = modulo in modulos_desbloqueados
            icono_modulo = "🔓" if esta_desbloqueado else "🔒"
            
            with st.expander(f"{icono_modulo} Módulo: {modulo}", expanded=esta_desbloqueado):
                if not esta_desbloqueado:
                    st.warning("🔒 **Módulo Bloqueado.** Este nivel se activará cuando Dirección apruebe tu avance.")
                else:
                    st.markdown(f"#### Exámenes Disponibles - Nivel {modulo}")
                    
                    for num_ex in range(1, 4):
                        key_examen = f"{modulo}_Examen_{num_ex}"
                        examen_datos = banco_examenes.get(key_examen, None)

                        col_e1, col_e2 = st.columns([3, 1])
                        with col_e1:
                            st.markdown(f"**📝 Examen {num_ex}:** {examen_datos['titulo'] if examen_datos else 'Sin examen cargado aún'}")
                        with col_e2:
                            if not examen_datos:
                                st.caption("⏳ En preparación")
                            else:
                                ya_presento = any(r for r in respuestas_evals if r["matricula"].upper() == usuario_actual.upper() and r["key_examen"] == key_examen)
                                if ya_presento:
                                    st.success("✅ Presentado")
                                else:
                                    if st.button(f"Presentar Examen {num_ex}", key=f"btn_pres_{key_examen}"):
                                        st.session_state[f"modo_examen_{key_examen}"] = True

                        # Despliegue del formulario del examen
                        if st.session_state.get(f"modo_examen_{key_examen}", False) and examen_datos:
                            with st.form(f"form_responder_{key_examen}"):
                                st.info(f"### {examen_datos['titulo']}")
                                st.write(examen_datos['descripcion'])
                                st.caption(f"Total de preguntas: {len(examen_datos['preguntas'])}")
                                st.divider()

                                respuestas_alumno = {}
                                for idx_q, q in enumerate(examen_datos['preguntas']):
                                    st.markdown(f"**Pregunta {idx_q+1}:** {q['pregunta']}")
                                    respuestas_alumno[f"p_{idx_q}"] = st.radio(
                                        f"Selecciona tu respuesta ({idx_q+1}):", 
                                        q['opciones'], 
                                        key=f"radio_{key_examen}_{idx_q}"
                                    )
                                    st.markdown("---")

                                link_tv = st.text_input("Enlace de Evidencia en TradingView:", placeholder="https://www.tradingview.com/x/...")
                                justificacion = st.text_area("Justificación Técnica de tu Análisis:", placeholder="Explica tu confirmación, zona POI y gestión...")

                                if st.form_submit_button("💾 Enviar Examen a Dirección", use_container_width=True):
                                    score = 0
                                    total_p = len(examen_datos['preguntas'])
                                    pts_por_p = 100 / total_p if total_p > 0 else 100

                                    for idx_q, q in enumerate(examen_datos['preguntas']):
                                        if respuestas_alumno.get(f"p_{idx_q}") == q['correcta']:
                                            score += pts_por_p

                                    respuestas_evals.append({
                                        "id": len(respuestas_evals) + 1,
                                        "matricula": usuario_actual,
                                        "key_examen": key_examen,
                                        "modulo": modulo,
                                        "num_examen": num_ex,
                                        "titulo": examen_datos['titulo'],
                                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                        "score_teorico": round(score, 1),
                                        "link_tv": link_tv,
                                        "justificacion": justificacion,
                                        "estatus": "⏳ A la espera de calificación de Dirección",
                                        "observaciones_director": "Aún no evaluado por Dirección.",
                                        "archivo_certificados": None  # Aquí se guardará el nombre del archivo subido por admin
                                    })
                                    guardar_json_local(FILE_RESPUESTAS, respuestas_evals)
                                    st.session_state[f"modo_examen_{key_examen}"] = False
                                    st.success("✅ Examen enviado con éxito a Dirección General.")
                                    st.rerun()

    # -------------------------------------------------------------
    # PESTAÑA 2: RESULTADOS Y DESCARGA DE CERTIFICADOS (ALUMNO)
    # -------------------------------------------------------------
    with tab_historial:
        st.subheader("📊 Diagnóstico Académico y Certificados Oficiales")
        mis_resp = [r for r in respuestas_evals if r["matricula"].upper() == usuario_actual.upper()]

        # Archivos de consulta general subidos por la academia
        archivos_disponibles = os.listdir(FOLDER_EXCEL_UPLOADS)
        if archivos_disponibles:
            with st.expander("📥 Reportes y Hojas de Comentarios de Dirección General", expanded=False):
                st.write("Consulta los documentos emitidos por la academia:")
                for fname in archivos_disponibles:
                    fpath = os.path.join(FOLDER_EXCEL_UPLOADS, fname)
                    with open(fpath, "rb") as f_excel:
                        st.download_button(
                            label=f"📄 Descargar {fname}",
                            data=f_excel,
                            file_name=fname,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

        if mis_resp:
            for item in reversed(mis_resp):
                with st.expander(f"📌 {item['modulo']} - Examen {item['num_examen']} ({item['fecha']})", expanded=True):
                    stus = item["estatus"]
                    if "Aprobado" in stus and "No" not in stus:
                        st.success(f"### Estatus: {stus}")
                    elif "revisión" in stus.lower():
                        st.warning(f"### Estatus: {stus}")
                    elif "No aprobado" in stus:
                        st.error(f"### Estatus: {stus}")
                    else:
                        st.info(f"### Estatus: {stus}")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Puntaje Teórico", f"{item['score_teorico']} / 100 PTS")
                        if item['link_tv']:
                            st.markdown(f"🔗 [Ver Gráfico TradingView]({item['link_tv']})")
                    with col_b:
                        st.markdown("**📝 Retroalimentación de Dirección:**")
                        st.info(item["observaciones_director"])

                    # Botón de Descarga del Reconocimiento Oficial Subido por el Admin
                    archivo_cert = item.get("archivo_certificados", None)
                    if archivo_cert and "Aprobado" in stus:
                        path_cert = os.path.join(FOLDER_CERTIFICADOS, archivo_cert)
                        if os.path.exists(path_cert):
                            st.divider()
                            with open(path_cert, "rb") as fc:
                                bytes_cert = fc.read()
                                ext = archivo_cert.split(".")[-1].lower()
                                mime_type = "application/pdf" if ext == "pdf" else f"image/{ext}"
                                
                                st.download_button(
                                    label="📜 Descargar Reconocimiento / Certificado Oficial",
                                    data=bytes_cert,
                                    file_name=f"Reconocimiento_Oficial_{usuario_actual}_{item['modulo']}.{ext}",
                                    mime=mime_type,
                                    use_container_width=True
                                )
        else:
            st.info("💡 No has presentado ninguna evaluación hasta el momento.")

    # -------------------------------------------------------------
    # PESTAÑA 3: CREADOR DINÁMICO DE EXÁMENES (ADMIN)
    # -------------------------------------------------------------
    if es_admin:
        with tab_crear:
            st.subheader("➕ Cargar / Configurar Exámenes Dinámicos")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                mod_target = st.selectbox("Módulo a Configurar:", LISTA_MODULOS)
            with col_c2:
                num_ex_target = st.selectbox("Número de Examen:", [1, 2, 3])

            key_target = f"{mod_target}_Examen_{num_ex_target}"
            ex_existente = banco_examenes.get(key_target, {})

            titulo_ex = st.text_input("Título del Examen:", value=ex_existente.get("titulo", f"Evaluación {mod_target} #{num_ex_target}"))
            desc_ex = st.text_area("Instrucciones:", value=ex_existente.get("descripcion", "Responde las preguntas y adjunta tu enlace de TradingView."))

            st.divider()
            if f"num_preg_state_{key_target}" not in st.session_state:
                st.session_state[f"num_preg_state_{key_target}"] = len(ex_existente.get("preguntas", [])) if ex_existente.get("preguntas") else 3

            col_p_btn1, col_p_btn2, _ = st.columns([1, 1, 2])
            with col_p_btn1:
                if st.button("➕ Agregar Pregunta"):
                    st.session_state[f"num_preg_state_{key_target}"] += 1
            with col_p_btn2:
                if st.button("➖ Quitar Pregunta") and st.session_state[f"num_preg_state_{key_target}"] > 1:
                    st.session_state[f"num_preg_state_{key_target}"] -= 1

            total_p = st.session_state[f"num_preg_state_{key_target}"]
            st.info(f"Total de preguntas para este examen: **{total_p}**")

            preguntas_recopiladas = []
            for i in range(total_p):
                st.markdown(f"##### **Pregunta #{i+1}**")
                p_prev = ex_existente.get("preguntas", [])[i] if i < len(ex_existente.get("preguntas", [])) else {}

                txt_p = st.text_input(f"Enunciado Pregunta #{i+1}:", value=p_prev.get("pregunta", ""), key=f"input_p_{key_target}_{i}")
                
                c_op1, c_op2, c_op3 = st.columns(3)
                opts = p_prev.get("opciones", ["", "", ""])
                with c_op1: op1 = st.text_input(f"Opción A (P{i+1}):", value=opts[0] if len(opts)>0 else "", key=f"op1_{key_target}_{i}")
                with c_op2: op2 = st.text_input(f"Opción B (P{i+1}):", value=opts[1] if len(opts)>1 else "", key=f"op2_{key_target}_{i}")
                with c_op3: op3 = st.text_input(f"Opción C (P{i+1}):", value=opts[2] if len(opts)>2 else "", key=f"op3_{key_target}_{i}")

                opciones_validas = [o for o in [op1, op2, op3] if o.strip() != ""]
                correcta = st.selectbox(
                    f"Respuesta Correcta Pregunta #{i+1}:", 
                    opciones_validas if opciones_validas else ["Define opciones primero"],
                    key=f"cor_{key_target}_{i}"
                )

                preguntas_recopiladas.append({"pregunta": txt_p, "opciones": [op1, op2, op3], "correcta": correcta})
                st.markdown("---")

            if st.button("💾 Guardar Examen Completo", use_container_width=True):
                banco_examenes[key_target] = {"titulo": titulo_ex, "descripcion": desc_ex, "preguntas": preguntas_recopiladas}
                guardar_json_local(FILE_BANCO_EXAMENES, banco_examenes)
                st.success(f"✅ Examen **{key_target}** guardado con éxito.")
                st.rerun()

        # -------------------------------------------------------------
        # PESTAÑA 4: GESTOR DE CANDADOS (ADMIN)
        # -------------------------------------------------------------
        with tab_permisos:
            st.subheader("🔓 Gestor de Candados por Alumno")
            alumno_mat_permiso = st.text_input("Matrícula del Alumno:", value="").strip().upper()

            if alumno_mat_permiso:
                permisos_actuales_alumno = permisos_alumnos.get(alumno_mat_permiso, ["Básico"])
                st.markdown(f"#### Configurando Módulos para: `{alumno_mat_permiso}`")
                
                with st.form("form_permisos_alumno"):
                    nuevos_permisos = []
                    for m in LISTA_MODULOS:
                        check = st.checkbox(f"🔓 Habilitar Módulo: {m}", value=(m in permisos_actuales_alumno))
                        if check:
                            nuevos_permisos.append(m)

                    if st.form_submit_button("💾 Guardar Permisos", use_container_width=True):
                        permisos_alumnos[alumno_mat_permiso] = nuevos_permisos
                        guardar_json_local(FILE_DESBLOQUEOS, permisos_alumnos)
                        st.success(f"✅ Permisos actualizados para **{alumno_mat_permiso}**.")
                        st.rerun()

        # -------------------------------------------------------------
        # PESTAÑA 5: REVISIÓN, DICTAMEN Y CARGA DE CERTIFICADO (ADMIN)
        # -------------------------------------------------------------
        with tab_coordinacion:
            st.subheader("👑 Panel de Dictamen y Carga de Certificados (DIRALEX)")

            if respuestas_evals:
                lista_pendientes = [f"ID: {r['id']} | Alumno: {r['matricula']} | Examen: {r['key_examen']}" for r in respuestas_evals]
                sel_dictamen = st.selectbox("Selecciona Evaluación a Revisar:", lista_pendientes)

                id_target = int(sel_dictamen.split("|")[0].replace("ID:", "").strip())
                target_resp = next((r for r in respuestas_evals if r["id"] == id_target), None)

                if target_resp:
                    st.divider()
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        st.markdown(f"**Alumno:** `{target_resp['matricula']}`")
                        st.markdown(f"**Examen:** {target_resp['titulo']}")
                        st.markdown(f"**Fecha:** {target_resp['fecha']}")
                        st.markdown(f"**Puntaje Teórico:** {target_resp['score_teorico']} pts")
                        if target_resp['link_tv']:
                            st.markdown(f"🔗 [Abrir Gráfico TradingView]({target_resp['link_tv']})")
                        st.text_area("Justificación del Alumno:", value=target_resp['justificacion'], disabled=True)

                    with col_d2:
                        with st.form("form_dictamen_admin"):
                            e_dictamen = st.selectbox(
                                "Asignar Estatus Académico:",
                                ["🟢 Aprobado", "🟡 A revisión en vivo", "🔴 No aprobado / No presentado"],
                                index=0 if "Aprobado" in target_resp["estatus"] else 1 if "revisión" in target_resp["estatus"] else 2
                            )
                            
                            obs_dictamen = st.text_area("Observaciones del Mentor / Coordinación:", value=target_resp["observaciones_director"])

                            # Carga del Archivo Oficial del Reconocimiento / Certificado
                            st.markdown("---")
                            st.markdown("📜 **Adjuntar Reconocimiento Oficial Firma / Logo (PDF, PNG, JPG):**")
                            up_cert = st.file_uploader("Sube el certificado emitido para este alumno:", type=["pdf", "png", "jpg", "jpeg"])

                            if st.form_submit_button("💾 Guardar Dictamen y Certificado", use_container_width=True):
                                file_cert_name = target_resp.get("archivo_certificados", None)

                                if up_cert is not None:
                                    ext_cert = up_cert.name.split(".")[-1]
                                    file_cert_name = f"Certificado_{target_resp['matricula']}_{target_resp['key_examen']}.{ext_cert}"
                                    path_save_cert = os.path.join(FOLDER_CERTIFICADOS, file_cert_name)
                                    with open(path_save_cert, "wb") as f_out:
                                        f_out.write(up_cert.getbuffer())

                                for idx, r in enumerate(respuestas_evals):
                                    if r["id"] == id_target:
                                        respuestas_evals[idx]["estatus"] = e_dictamen
                                        respuestas_evals[idx]["observaciones_director"] = obs_dictamen
                                        respuestas_evals[idx]["archivo_certificados"] = file_cert_name
                                        break

                                guardar_json_local(FILE_RESPUESTAS, respuestas_evals)
                                st.success("✅ Dictamen y Reconocimiento Oficial guardados exitosamente.")
                                st.rerun()
            else:
                st.info("💡 No hay evaluaciones pendientes registradas.")

        # -------------------------------------------------------------
        # PESTAÑA 6: ARCHIVOS Y EXCEL (ADMIN)
        # -------------------------------------------------------------
        with tab_archivos:
            st.subheader("📁 Archivos y Reportes Generales")
            
            st.markdown("#### **1. Subir Archivo Excel / Hoja de Retroalimentación**")
            uploaded_excel = st.file_uploader("Selecciona un archivo Excel (.xlsx) para ponerlo a disposición de los alumnos:", type=["xlsx", "xls"])
            if uploaded_excel is not None:
                save_path = os.path.join(FOLDER_EXCEL_UPLOADS, uploaded_excel.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_excel.getbuffer())
                st.success(f"✅ Archivo **{uploaded_excel.name}** subido correctamente.")

            st.divider()
            st.markdown("#### **2. Exportar Respuestas de Exámenes a Excel**")
            if respuestas_evals:
                df_exp = pd.DataFrame(respuestas_evals)
                buffer_excel = io.BytesIO()
                with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                    df_exp.to_excel(writer, index=False, sheet_name='Evaluaciones')
                
                st.download_button(
                    label="📊 Descargar Historial Completo (.xlsx)",
                    data=buffer_excel.getvalue(),
                    file_name=f"Historial_Evaluaciones_ALEMA_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )


st.caption("© ALEMA Trading Academy. Reservados todos los derechos.")
