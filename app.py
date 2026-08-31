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
# SECCIÓN: SIMULADOR DE EJECUCIÓN INSTITUCIONAL (ESTILO MT5)
# ==========================================
elif opcion_menu == "🧪 Simulador de Ejecución":
    
    import json
    import os
    from datetime import datetime
    import requests
    import pandas as pd
    import yfinance as yf

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
        pnl_flotante_total = 0.0
        for pos in st.session_state.posiciones_abiertas:
            act_p = pos.get("precio_vela_actual", pos["entrada"]) 
            is_jpy_m = "JPY" in pos["activo"]
            is_mc_m = "XAU" in pos["activo"] or "BTC" in pos["activo"]
            mp = 100.0 if is_jpy_m else (1.0 if is_mc_m else 10000.0)
            vp = 7.0 if is_jpy_m else 10.0
            pips_calc = (act_p - pos["entrada"]) if pos["tipo"] == "BUY" else (pos["entrada"] - act_p)
            pnl_flotante_total += (pips_calc * mp * vp * pos["lotes"])
        st.metric("Beneficio Flotante", f"${pnl_flotante_total:,.2f}", delta=f"${pnl_flotante_total:,.2f}")
    with col_m3:
        st.metric("Posiciones Activas", f"{len(st.session_state.posiciones_abiertas)}")
    with col_m4:
        st.metric("Servidor", "ALEMA-Live")

    st.divider()

    col_grafico, col_panel = st.columns([2.4, 1.0])

    with col_grafico:
        par_activo = st.selectbox("Símbolo de Mercado", ["FX:EURUSD", "FX:GBPUSD", "FX:USDJPY", "OANDA:XAUUSD", "BITSTAMP:BTCUSD"], key="select_chart_asset")
        
        tradingview_html = f"""
        <div class="tradingview-widget-container" style="height:540px;width:100%">
          <div id="tradingview_chart" style="height:540px;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget(
          {{
            "autosize": true,
            "symbol": "{par_activo}",
            "interval": "1",
            "timezone": "America/Mexico_City",
            "theme": "dark",
            "style": "1",
            "locale": "es",
            "toolbar_bg": "#131722",
            "enable_publishing": false,
            "hide_top_toolbar": false,
            "hide_side_toolbar": false,
            "allow_symbol_change": false,
            "container_id": "tradingview_chart"
          }}
          );
          </script>
        </div>
        """
        st.components.v1.html(tradingview_html, height=550)

    with col_panel:
        st.markdown("### 🎛️ Nueva Orden")
        activo_sim = par_activo.split(":")[-1]
        
        modo_ejecucion = st.radio("Tipo", ["Ejecución por Mercado", "Pendiente"], horizontal=True, key="sim_modo")
        sim_tipo = st.radio("Dirección", ["BUY", "SELL"], horizontal=True, key="sim_direccion")
        sim_lotes = st.number_input("Volumen (Lotes)", value=0.10, min_value=0.01, step=0.01, key="sim_lote")
        
        es_jpy_sim = "JPY" in activo_sim
        es_crypto_oro = "XAU" in activo_sim or "BTC" in activo_sim
        n_decimals = 3 if es_jpy_sim else (2 if es_crypto_oro else 5)
        formato = "%.3f" if es_jpy_sim else ("%.2f" if es_crypto_oro else "%.5f")
        step_val = 0.001 if es_jpy_sim else (0.10 if es_crypto_oro else 0.00001)

        # Función de captura de precio optimizada
        def obtener_precio_instante(simbolo):
            mapa_tickers = {
                "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", 
                "USDJPY": "JPY=X", "XAUUSD": "GC=F", "BTCUSD": "BTC-USD"
            }
            try:
                data = yf.Ticker(mapa_tickers.get(simbolo)).history(period="1d", interval="1m")
                if not data.empty: return float(data['Close'].iloc[-1])
            except: pass
            precios_base = {"EURUSD": 1.15781, "GBPUSD": 1.30000, "USDJPY": 155.200, "XAUUSD": 2600.00, "BTCUSD": 65000.00}
            return precios_base.get(simbolo, 1.15781)

        precio_referencia_vela = obtener_precio_instante(activo_sim)
        
        # Renderizado condicional del precio de entrada
        sim_precio_entrada = precio_referencia_vela
        if modo_ejecucion == "Pendiente":
            sim_precio_entrada = st.number_input(
                "Precio de Entrada (Límite/Stop)", 
                value=float(precio_referencia_vela), 
                format=formato, 
                step=step_val, 
                key=f"precio_vela_sync_{activo_sim}"
            )
        else:
            st.info(f"El precio se asignará automáticamente a condiciones de mercado al ejecutar.")
        
        dist_sl = 0.00500 if not es_jpy_sim and not es_crypto_oro else (0.500 if es_jpy_sim else 20.0)
        dist_tp = 0.01000 if not es_jpy_sim and not es_crypto_oro else (1.000 if es_jpy_sim else 40.0)

        # Cálculo default de SL/TP basado en la referencia actual
        default_sl = round(precio_referencia_vela - dist_sl if sim_tipo == "BUY" else precio_referencia_vela + dist_sl, n_decimals)
        default_tp = round(precio_referencia_vela + dist_tp if sim_tipo == "BUY" else precio_referencia_vela - dist_tp, n_decimals)
        
        sim_precio_sl = st.number_input("Stop Loss", value=default_sl, format=formato, step=step_val, key=f"sl_in_{sim_tipo}_{activo_sim}")
        sim_precio_tp = st.number_input("Take Profit", value=default_tp, format=formato, step=step_val, key=f"tp_in_{sim_tipo}_{activo_sim}")

        if st.button(f"🟢 COMPRAR" if sim_tipo == "BUY" else f"🔴 VENDER", key="btn_ejecutar_sim", use_container_width=True):
            # Captura de precio EXACTO al momento del clic si es ejecución por mercado
            precio_ejecucion_final = obtener_precio_instante(activo_sim) if modo_ejecucion == "Ejecución por Mercado" else sim_precio_entrada
            
            nueva_orden = {
                "id": len(st.session_state.posiciones_abiertas) + len(st.session_state.historial_cerradas) + 1,
                "fecha": str(datetime.now().date()),
                "activo": activo_sim,
                "tipo": sim_tipo,
                "lotes": float(sim_lotes),
                "entrada": float(precio_ejecucion_final),
                "sl": float(sim_precio_sl),
                "tp": float(sim_precio_tp),
                "precio_vela_actual": float(precio_ejecucion_final)
            }
            st.session_state.posiciones_abiertas.append(nueva_orden)
            guardar_datos_json(ARCH_PERSISTENCIA_ACTIVAS, st.session_state.posiciones_abiertas)
            st.success(f"¡Orden ejecutada a {precio_ejecucion_final} con éxito!")
            st.rerun()

    # --- PANEL INFERIOR: POSICIONES ABIERTAS ---
    st.markdown("### 📊 Posiciones Abiertas (Tiempo Real)")

    if st.session_state.posiciones_abiertas:
        posiciones_a_cerrar = []
        
        for idx, pos in enumerate(st.session_state.posiciones_abiertas):
            precio_actual_vela = obtener_precio_instante(pos["activo"])
            pos["precio_vela_actual"] = precio_actual_vela 
            
            es_jpy = "JPY" in pos["activo"]
            is_mc = "XAU" in pos["activo"] or "BTC" in pos["activo"]
            fmt = "%.3f" if es_jpy else ("%.2f" if is_mc else "%.5f")
            
            mp = 100.0 if es_jpy else (1.0 if is_mc else 10000.0)
            vp = 7.0 if es_jpy else 10.0
            pips = (precio_actual_vela - pos["entrada"]) if pos["tipo"] == "BUY" else (pos["entrada"] - precio_actual_vela)
            pnl = pips * mp * vp * pos["lotes"]

            cierre_automatico = False
            motivo_cierre = "Activa"
            
            if pos["tipo"] == "BUY":
                if precio_actual_vela >= pos["tp"]:
                    cierre_automatico, motivo_cierre = True, "Take Profit (TP)"
                elif precio_actual_vela <= pos["sl"]:
                    cierre_automatico, motivo_cierre = True, "Stop Loss (SL)"
            else: 
                if precio_actual_vela <= pos["tp"]:
                    cierre_automatico, motivo_cierre = True, "Take Profit (TP)"
                elif precio_actual_vela >= pos["sl"]:
                    cierre_automatico, motivo_cierre = True, "Stop Loss (SL)"

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
                                <th>GANANCIA FLOTANTE ($)</th>
                                <th>ESTATUS</th>
                            </tr>
                            <tr>
                                <td style="text-align:left; font-weight:bold; color: #fff;">{pos['activo']}</td>
                                <td>{pos['lotes']} L</td>
                                <td><code>{fmt % pos['entrada']}</code></td>
                                <td><code style="color: #E2B714;">{fmt % precio_actual_vela}</code></td>
                                <td><code>{fmt % pos['tp']}</code></td>
                                <td><code>{fmt % pos['sl']}</code></td>
                                <td style="color: {'#26a69a' if pos['tipo']=='BUY' else '#ef5350'}; font-weight:bold;">{pos['tipo']}</td>
                                <td style="color: {'#26a69a' if pnl>=0 else '#ef5350'}; font-weight:bold;">${pnl:,.2f}</td>
                                <td style="color: {'#26a69a' if cierre_automatico else '#2962FF'};">{'● Cierre ' + motivo_cierre if cierre_automatico else '● Activa'}</td>
                            </tr>
                        </table>
                    </div>
                """, unsafe_allow_html=True)
                
                col_info_btn, col_btn_cerrar = st.columns([4, 1])
                with col_btn_cerrar:
                    btn_manual = st.button(f"Cerrar #{pos['id']}", key=f"btn_cierre_manual_{pos['id']}_{idx}", use_container_width=True)

                if cierre_automatico or btn_manual:
                    st.session_state.balance_pedagogico += pnl
                    registro_historial = {
                        "Marca temporal": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "Matricula": st.session_state.get("usuario_actual", "DIRALEX"),
                        "Fecha": pos['fecha'],
                        "Activo": pos['activo'].replace("/", "").replace("USD", "/USD"),
                        "Tipo": pos['tipo'],
                        "Lotes": pos['lotes'],
                        "Pips": round(pips, 1),
                        "Resultado USD": round(pnl, 2)
                    }
                    st.session_state.historial_cerradas.append(registro_historial)
                    guardar_datos_json(ARCH_PERSISTENCIA_HISTORIAL, st.session_state.historial_cerradas)
                    posiciones_a_cerrar.append(idx)

        if posiciones_a_cerrar:
            for index in sorted(posiciones_a_cerrar, reverse=True):
                st.session_state.posiciones_abiertas.pop(index)
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
