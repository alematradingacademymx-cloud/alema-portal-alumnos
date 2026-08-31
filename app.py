import requests
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import os
import pandas as pd
from datetime import datetime
import yfinance as yf

# Configuración de página
st.set_page_config(page_title="ALEMA Trading Academy - Portal de Alumnos", page_icon="📈", layout="centered")

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
        
        dict_usuarios = {}
        for _, row in df.iterrows():
            dict_usuarios[row['Matricula']] = {
                'password': row['Password'],
                'tipo': row['Tipo_Usuario'],
                'vencimiento': row['Fecha_Vencimiento']
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
            
            dict_usuarios = {}
            for _, row in df.iterrows():
                dict_usuarios[row['Matricula']] = {
                    'password': row['Password'],
                    'tipo': row['Tipo_Usuario'],
                    'vencimiento': row['Fecha_Vencimiento']
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
# 🚀 MENÚ LATERAL Y NAVEGACIÓN SEGÚN ROL
# ==========================================
import streamlit.components.v1 as components

st.sidebar.image("alema trading academy.png", width=180)

st.sidebar.markdown("### 🎓 ALEMA PORTAL")
st.sidebar.write(f"Usuario: **{st.session_state.usuario_actual}**")
st.sidebar.caption(f"Rol: {st.session_state.tipo_usuario}")
st.sidebar.markdown("---")

if st.session_state.tipo_usuario in ["ADMIN", "ALUMNO"]:
    opciones_disponibles = ["📊 Mi Avance Académico", "🧮 Calculadoras de Lotes", "📓 Trading Journal", "🧪 Simulador de Ejecución", "📚 Biblioteca de Guías"]
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
# SECCIÓN: SIMULADOR DE EJECUCIÓN INSTITUCIONAL (ESTILO MT5)
# ==========================================
if opcion_menu == "🧪 Simulador de Ejecución":
    
    import json
    import os
    from datetime import datetime
    import pytz
    import pandas as pd

    TZ_MEXICO = pytz.timezone("America/Mexico_City")

    ARCH_PERSISTENCIA_ACTIVAS = "posiciones_activas_alema.json"
    ARCH_PERSISTENCIA_HISTORIAL = "historial_cerradas_alema.json"

    def cargar_datos_json(archivo):
        if os.path.exists(archivo):
            try:
                with open(archivo, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def guardar_datos_json(archivo, datos):
        try:
            with open(archivo, "w") as f:
                json.dump(datos, f)
        except Exception:
            pass

    st.markdown("""
        <style>
            .mt5-terminal-card {
                background-color: #131722;
                border: 1px solid #2A2E39;
                padding: 10px 15px;
                border-radius: 4px;
                margin-bottom: 8px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title" style="text-align: left; font-size: 24px; font-weight: 700;">ALEMA TRADING ACADEMY | Terminal ALEMA </div>', unsafe_allow_html=True)

    if 'balance_pedagogico' not in st.session_state:
        st.session_state.balance_pedagogico = 300.00
    if 'posiciones_abiertas' not in st.session_state:
        st.session_state.posiciones_abiertas = cargar_datos_json(ARCH_PERSISTENCIA_ACTIVAS)
    if 'historial_cerradas' not in st.session_state:
        st.session_state.historial_cerradas = cargar_datos_json(ARCH_PERSISTENCIA_HISTORIAL)

    # Panel de Métricas Superior
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Balance", f"${st.session_state.balance_pedagogico:,.2f}")
    with col_m2:
        st.metric("Beneficio Flotante", "$0.00", delta="$0.00")
    with col_m3:
        st.metric("Posiciones Activas", f"{len(st.session_state.posiciones_abiertas)}")
    with col_m4:
        st.metric("Servidor", "ALEMA-Live")

    st.divider()

    col_grafico, col_panel = st.columns([2.4, 1.0])

    with col_grafico:
        par_activo = st.selectbox("Símbolo de Mercado", ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSDT"], key="select_chart_asset")
        
        # Precio base inicial según el activo
        if par_activo == "EURUSD":
            precio_base_inicial = 1.15903
        elif par_activo == "GBPUSD":
            precio_base_inicial = 1.30250
        elif par_activo == "USDJPY":
            precio_base_inicial = 155.200
        elif par_activo == "XAUUSD":
            precio_base_inicial = 2385.50
        else:
            precio_base_inicial = 64200.0

        chart_html = f"""
        <div style="background-color: #131722; padding: 10px; border-radius: 6px; border: 1px solid #2A2E39;">
            <div style="color: #94A3B8; font-size: 13px; margin-bottom: 6px; font-family: sans-serif;">Gráfico Institucional En Vivo - {par_activo}</div>
            <div id="tv_chart_container" style="width: 100%; height: 500px;"></div>
        </div>
        <script type="text/javascript" src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
        <script type="text/javascript">
            const chartDom = document.getElementById('tv_chart_container');
            const chart = LightweightCharts.createChart(chartDom, {{
                width: chartDom.clientWidth,
                height: 500,
                layout: {{ background: {{ type: 'solid', color: '#131722' }}, text: '#D1D4DC' }},
                grid: {{ vertLines: {{ color: '#2A2E39' }}, horzLines: {{ color: '#2A2E39' }} }},
                timeScale: {{ timeVisible: true, secondsVisible: true }}
            }});
            
            const candlestickSeries = chart.addCandlestickSeries({{
                upColor: '#26a69a', downColor: '#ef5350', borderVisible: false,
                wickUpColor: '#26a69a', wickDownColor: '#ef5350'
            }});

            let basePrice = {precio_base_inicial};
            let now = Math.floor(Date.now() / 1000) - 300;
            let initialData = [];
            for(let i = 0; i < 60; i++) {{
                let change = (Math.random() - 0.48) * (basePrice * 0.0004);
                let open = basePrice;
                let close = open + change;
                let high = Math.max(open, close) + Math.random() * (basePrice * 0.0002);
                let low = Math.min(open, close) - Math.random() * (basePrice * 0.0002);
                initialData.push({{ time: now + (i * 60), open: open, high: high, low: low, close: close }});
                basePrice = close;
            }}
            candlestickSeries.setData(initialData);
            chart.timeScale().fitContent();

            setInterval(() => {{
                let lastCandle = initialData[initialData.length - 1];
                let movement = (Math.random() - 0.49) * (lastCandle.close * 0.0001);
                lastCandle.close += movement;
                lastCandle.high = Math.max(lastCandle.high, lastCandle.close);
                lastCandle.low = Math.min(lastCandle.low, lastCandle.close);
                candlestickSeries.update(lastCandle);
            }}, 1000);
        </script>
        """
        st.components.v1.html(chart_html, height=560)

    with col_panel:
        st.markdown("### 🎛️ Nueva Orden (Mercado)")
        
        sim_tipo = st.radio("Dirección", ["BUY", "SELL"], horizontal=True, key="sim_direccion")
        sim_lotes = st.number_input("Volumen (Lotes)", value=0.10, min_value=0.01, step=0.01, key="sim_lote")
        
        es_jpy_sim = "JPY" in par_activo
        es_crypto_oro = "XAU" in par_activo or "BTC" in par_activo
        n_decimals = 3 if es_jpy_sim else (2 if es_crypto_oro else 5)
        formato = "%.3f" if es_jpy_sim else ("%.2f" if es_crypto_oro else "%.5f")
        step_val = 0.001 if es_jpy_sim else (0.10 if es_crypto_oro else 0.00001)

        ref_precio = precio_base_inicial
        
        dist_def_sl = 0.00200 if not es_jpy_sim and not es_crypto_oro else (0.200 if es_jpy_sim else 10.0)
        dist_def_tp = 0.00400 if not es_jpy_sim and not es_crypto_oro else (0.400 if es_jpy_sim else 20.0)

        default_sl = round(ref_precio - dist_def_sl if sim_tipo == "BUY" else ref_precio + dist_def_sl, n_decimals)
        default_tp = round(ref_precio + dist_def_tp if sim_tipo == "BUY" else ref_precio - dist_def_tp, n_decimals)

        st.markdown(f"<small style='color: #787B86;'>Precio de Mercado Actual: <b>{formato % ref_precio}</b></small>", unsafe_allow_html=True)
        
        sim_precio_sl = st.number_input("Stop Loss", value=float(default_sl), format=formato, step=step_val, key=f"sl_in_{sim_tipo}_{par_activo}")
        sim_precio_tp = st.number_input("Take Profit", value=float(default_tp), format=formato, step=step_val, key=f"tp_in_{sim_tipo}_{par_activo}")

        if st.button(f"🟢 COMPRAR" if sim_tipo == "BUY" else f"🔴 VENDER", key="btn_ejecutar_sim", use_container_width=True):
            fecha_mx_str = str(datetime.now(TZ_MEXICO).date())

            nueva_orden = {
                "id": int(datetime.now().timestamp() * 1000),
                "fecha": fecha_mx_str,
                "activo": par_activo,
                "tipo": sim_tipo,
                "lotes": float(sim_lotes),
                "entrada": float(ref_precio),
                "sl": float(sim_precio_sl),
                "tp": float(sim_precio_tp)
            }
            st.session_state.posiciones_abiertas.append(nueva_orden)
            guardar_datos_json(ARCH_PERSISTENCIA_ACTIVAS, st.session_state.posiciones_abiertas)
            st.success(f"¡Orden ejecutada al precio de mercado: {formato % ref_precio}!")
            st.rerun()

    # --- PANEL INFERIOR: POSICIONES ABIERTAS ---
    st.markdown("### 📊 Posiciones Abiertas (Tiempo Real)")

    if st.session_state.posiciones_abiertas:
        hubo_cambios = False
        posiciones_conservadas = []
        
        for pos in st.session_state.posiciones_abiertas:
            es_jpy = "JPY" in pos["activo"]
            is_mc = "XAU" in pos["activo"] or "BTC" in pos["activo"]
            fmt = "%.3f" if es_jpy else ("%.2f" if is_mc else "%.5f")
            
            mp = 100.0 if es_jpy else (1.0 if is_mc else 10000.0)
            vp = 7.0 if es_jpy else 10.0

            with st.container():
                st.markdown(f"""
                    <div class="mt5-terminal-card">
                        <table style="width:100%; color: #D1D4DC; font-size: 13px; text-align: center;">
                            <tr style="color: #787B86; font-size: 11px; border-bottom: 1px solid #2A2E39;">
                                <th style="text-align:left;">ACTIVO</th>
                                <th>LOTAJE</th>
                                <th>ENTRADA</th>
                                <th>MERCADO (VIVO)</th>
                                <th>TP</th>
                                <th>SL</th>
                                <th>TIPO</th>
                                <th>ESTATUS</th>
                            </tr>
                            <tr>
                                <td style="text-align:left; font-weight:bold; color: #fff;">{pos['activo']}</td>
                                <td>{pos['lotes']} L</td>
                                <td><code>{fmt % pos['entrada']}</code></td>
                                <td><code style="color: #E2B714;">{fmt % pos['entrada']}</code></td>
                                <td><code>{fmt % pos['tp']}</code></td>
                                <td><code>{fmt % pos['sl']}</code></td>
                                <td style="color: {'#26a69a' if pos['tipo']=='BUY' else '#ef5350'}; font-weight:bold;">{pos['tipo']}</td>
                                <td style="color: #2962FF;">● Activa (Esperando TP/SL)</td>
                            </tr>
                        </table>
                    </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 2])
                
                with col_btn1:
                    if st.button(f"🎯 Simular TP #{str(pos['id'])[-4:]}", key=f"tp_{pos['id']}", use_container_width=True):
                        pips_tp = (pos["tp"] - pos["entrada"]) if pos["tipo"] == "BUY" else (pos["entrada"] - pos["tp"])
                        pnl_tp = pips_tp * mp * vp * pos["lotes"]
                        st.session_state.balance_pedagogico += pnl_tp
                        ahora_mexico = datetime.now(TZ_MEXICO)
                        
                        registro_historial = {
                            "Marca temporal": ahora_mexico.strftime("%d/%m/%Y %H:%M:%S"),
                            "Matricula": st.session_state.get("usuario_actual", "DIRALEX"),
                            "Fecha": pos['fecha'],
                            "Activo": pos['activo'],
                            "Tipo": pos['tipo'],
                            "Lotes": pos['lotes'],
                            "Pips": round(pips_tp, 1),
                            "Resultado USD": round(pnl_tp, 2)
                        }
                        st.session_state.historial_cerradas.append(registro_historial)
                        guardar_datos_json(ARCH_PERSISTENCIA_HISTORIAL, st.session_state.historial_cerradas)
                        hubo_cambios = True

                with col_btn2:
                    if st.button(f"🛑 Simular SL #{str(pos['id'])[-4:]}", key=f"sl_{pos['id']}", use_container_width=True):
                        pips_sl = (pos["sl"] - pos["entrada"]) if pos["tipo"] == "BUY" else (pos["entrada"] - pos["sl"])
                        pnl_sl = pips_sl * mp * vp * pos["lotes"]
                        st.session_state.balance_pedagogico += pnl_sl
                        ahora_mexico = datetime.now(TZ_MEXICO)
                        
                        registro_historial = {
                            "Marca temporal": ahora_mexico.strftime("%d/%m/%Y %H:%M:%S"),
                            "Matricula": st.session_state.get("usuario_actual", "DIRALEX"),
                            "Fecha": pos['fecha'],
                            "Activo": pos['activo'],
                            "Tipo": pos['tipo'],
                            "Lotes": pos['lotes'],
                            "Pips": round(pips_sl, 1),
                            "Resultado USD": round(pnl_sl, 2)
                        }
                        st.session_state.historial_cerradas.append(registro_historial)
                        guardar_datos_json(ARCH_PERSISTENCIA_HISTORIAL, st.session_state.historial_cerradas)
                        hubo_cambios = True

                with col_btn3:
                    if st.button(f"❌ Cerrar Manual #{str(pos['id'])[-4:]}", key=f"manual_{pos['id']}", use_container_width=True):
                        pnl_man = 0.0
                        st.session_state.balance_pedagogico += pnl_man
                        ahora_mexico = datetime.now(TZ_MEXICO)
                        
                        registro_historial = {
                            "Marca temporal": ahora_mexico.strftime("%d/%m/%Y %H:%M:%S"),
                            "Matricula": st.session_state.get("usuario_actual", "DIRALEX"),
                            "Fecha": pos['fecha'],
                            "Activo": pos['activo'],
                            "Tipo": pos['tipo'],
                            "Lotes": pos['lotes'],
                            "Pips": 0.0,
                            "Resultado USD": 0.0
                        }
                        st.session_state.historial_cerradas.append(registro_historial)
                        guardar_datos_json(ARCH_PERSISTENCIA_HISTORIAL, st.session_state.historial_cerradas)
                        hubo_cambios = True

                if not hubo_cambios:
                    posiciones_conservadas.append(pos)

        if hubo_cambios:
            st.session_state.posiciones_abiertas = posiciones_conservadas
            guardar_datos_json(ARCH_PERSISTENCIA_ACTIVAS, st.session_state.posiciones_abiertas)
            st.rerun()
    else:
        st.info("No hay posiciones activas actualmente.")

    # --- SECCIÓN: BITÁCORA HISTÓRICA PERMANENTE ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Bitácora Histórica Permanente")
    
    if st.session_state.historial_cerradas:
        df_historial = pd.DataFrame(st.session_state.historial_cerradas)
        st.dataframe(df_historial, use_container_width=True, hide_index=False)
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
