import requests
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import os
import json
import pandas as pd
from datetime import datetime
import yfinance as yf

# Configuración de página
st.set_page_config(page_title="ALEMA Trading Academy - Portal de Alumnos", page_icon="📈", layout="centered")

# Funciones de persistencia JSON auxiliares
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

# Estilos CSS personalizados con Fondo Azul Oscuro Elegante y Botón Verde
st.markdown("""
    <style>
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

# ==========================================
# 🔑 BASE DE DATOS DE USUARIOS (GOOGLE SHEETS)
# ==========================================
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

# --- PANTALLA DE INICIO DE SESIÓN ---
if not st.session_state.autenticado:
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
                    
                    st.success("¡Acceso concedido!")
                    st.rerun()
            else:
                st.error("❌ Matrícula o contraseña incorrecta. Verifica con administración.")
    
    st.markdown("---")
    st.markdown("### 🚀 ¿Aún no tienes tu acceso al Portal?")
    st.write(
        "Obtén acceso a las **Calculadoras Operativas**, **Biblioteca de Guías en PDF** "
        "y **Cápsulas de Psicotrading** por solo **$150 MXN / mes**."
    )

    num_whatsapp = "528136462129"
    mensaje_preset = (
        "¡Hola Daniela! 👋 Vengo del portal web y me gustaría adquirir mi suscripción "
        "a la Membresía ALEMA Suite ($150 MXN/mes) para obtener mis credenciales de acceso."
    )

    url_wa = f"https://wa.me/{num_whatsapp}?text={mensaje_preset.replace(' ', '%20')}"
    st.link_button("📲 Solicitar Membresía por WhatsApp", url_wa, use_container_width=True)

    st.caption("© ALEMA Trading Academy. Reservados todos los derechos.")
    st.stop()

# ==========================================
# ⚙️ PANEL DE CONTROL ADMIN (SOLO PARA ADMINS EN SIDEBAR)
# ==========================================
if st.session_state.get("tipo_usuario") == "ADMIN":
    st.sidebar.divider()
    st.sidebar.markdown("### ⚙️ Panel Coordinación Admin")
    
    lista_matriculas = list(USUARIOS_AUTORIZADOS.keys())
    alumno_seleccionado = st.sidebar.selectbox("Gestionar Alumno", lista_matriculas, key="select_admin_alumno")
    
    if st.sidebar.button("🔄 Sincronizar / Reiniciar Capital", use_container_width=True):
        cargar_usuarios_desde_sheets.clear()
        datos_frescos = cargar_usuarios_desde_sheets()
        capital_nuevo = datos_frescos.get(alumno_seleccionado, {}).get('capital_base', 300.0)
        
        if alumno_seleccionado == st.session_state.usuario_actual:
            st.session_state.balance_pedagogico = capital_nuevo
            st.session_state.posiciones_abiertas = []
            guardar_datos_json(st.session_state.archivo_pos, [])
            st.success(f"¡Tu cuenta ha sido reiniciada a ${capital_nuevo:,.2f}!")
        else:
            st.sidebar.success(f"Capital de {alumno_seleccionado} actualizado en base.")
        st.rerun()
# ==========================================
# 🚀 MENÚ LATERAL Y NAVEGACIÓN SEGÚN ROL
# ==========================================
import streamlit.components.v1 as components

st.sidebar.image("alema trading academy.png", width=180)

st.sidebar.markdown("### 🎓 ALEMA PORTAL")
st.sidebar.write(f"Usuario: **{st.session_state.usuario_actual}**")
st.sidebar.caption(f"Rol: {st.session_state.tipo_usuario}")
st.sidebar.markdown("---")

if st.session_state.tipo_usuario in ["ADMIN", "ALUMNO"]:
    opciones_disponibles = ["📊 Mi Avance Académico", "🧮 Calculadoras de Lotes", "📓 Trading Journal", "📉 Alema Trade live", "📚 Biblioteca de Guías"]
else:
    opciones_disponibles = ["🧮 Calculadoras de Lotes", "📚 Biblioteca de Guías"]

opcion_menu = st.sidebar.radio(
    "Selecciona una sección:",
    opciones_disponibles,
    key="navegacion_principal"
)

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.autenticado = False
    st.session_state.usuario_actual = ""
    st.session_state.tipo_usuario = "ALUMNO"
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
        
        // Escuchador global de toque/clic en la barra lateral para móviles
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
# SIMULADOR INSTITUCIONAL ALEMA TRADING ACADEMY
# (VERSIÓN CONECTADA A BASE DE DATOS GOOGLE SHEETS)
# ==========================================
elif opcion_menu == "📉 Alema Trade live":
    
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

    # --- FUNCIÓN DE CONEXIÓN Y LECTURA DE CAPITAL DESDE GOOGLE SHEETS ---
    @st.cache_data(ttl=10) # Se actualiza cada 10 segundos desde la base de datos
    def obtener_capital_desde_sheets(usuario_target):
        try:
            sheet_url = "https://docs.google.com/spreadsheets/d/1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA/export?format=csv&gid=0"
            df = pd.read_csv(sheet_url)
            df.columns = [str(c).strip() for c in df.columns]
            
            # Identificar columnas de Usuario y Capital en la hoja
            col_user = next((c for c in df.columns if any(k in c.lower() for k in ["usuario", "matricula", "user"])), None)
            col_cap = next((c for c in df.columns if any(k in c.lower() for k in ["capital", "monto", "balance"])), None)
            
            if col_user and col_cap:
                filtro = df[df[col_user].astype(str).str.strip().str.lower() == str(usuario_target).strip().lower()]
                if not filtro.empty:
                    val_str = str(filtro[col_cap].values[0]).replace("$", "").replace(",", "").strip()
                    return float(val_str)
        except Exception:
            pass
        return 300.00  # Valor por defecto en caso de falla de conexión

    # Cargar operaciones activas e historial
    st.session_state.posiciones_abiertas = cargar_datos_json(ARCH_PERSISTENCIA_ACTIVAS, [])
    st.session_state.historial_cerradas = cargar_datos_json(ARCH_PERSISTENCIA_HISTORIAL, [])

    # CÁLCULO DINÁMICO DEL BALANCE: CAPITAL DE SHEETS + PnL ACUMULADO DEL ALUMNO
    capital_base_sheets = obtener_capital_desde_sheets(usuario)
    pnl_acumulado_historico = sum(float(trade.get("Beneficio", 0.0)) for trade in st.session_state.historial_cerradas)
    st.session_state.balance_pedagogico = capital_base_sheets + pnl_acumulado_historico
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

    # --- DASHBOARD Y GRÁFICOS ---
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("Balance Base (Sheets)", f"${st.session_state.balance_pedagogico:,.2f}")
    with col_m2:
        pnl_flotante_total = sum([
            calcular_pnl_institucional(p["activo"], p["tipo"], p["entrada"], p.get("bid_vela_actual", p["entrada"]) if p["tipo"] == "BUY" else p.get("ask_vela_actual", p["entrada"]), p["lotes"]) 
            for p in st.session_state.posiciones_abiertas
        ])
        st.metric("Beneficio Flotante", f"${pnl_flotante_total:,.2f}", delta=f"${pnl_flotante_total:,.2f}")
    with col_m3: st.metric("Posiciones Activas", f"{len(st.session_state.posiciones_abiertas)}")
    with col_m4: 
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
# SECCIÓN: BIBLIOTECA DE GUÍAS
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
        
        @st.cache_data
        def cargar_bytes_pdf(ruta):
            with open(ruta, "rb") as f:
                return f.read()

        pdf_bytes = cargar_bytes_pdf(archivo_pdf)

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

st.caption("© ALEMA Trading Academy. Reservados todos los derechos.")
