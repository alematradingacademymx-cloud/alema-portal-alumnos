import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="ALEMA Trading Academy", page_icon="📈", layout="centered")

# Estilos CSS personalizados con Fondo Azul Oscuro Elegante
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
        font-size: 32px;
        font-weight: 800;
        color: #FF6B00; /* Naranja Institucional */
        margin-top: 10px;
        margin-bottom: 0px;
        letter-spacing: 1px;
    }
    .sub-title {
        text-align: center;
        font-size: 17px;
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
    </style>
""", unsafe_allow_html=True)

# --- CARRUSEL SUPERIOR TIPO TICKER ---
ticker_html = """
<!-- TradingView Widget BEGIN -->
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
<!-- TradingView Widget END -->
"""

components.html(ticker_html, height=78)

# Encabezado principal
st.markdown('<div class="main-title">ALEMA TRADING ACADEMY</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Calculadora Operativa & Gestión de Riesgo Multi-Activo</div>', unsafe_allow_html=True)

# --- GUÍA RÁPIDA PLEGABLE ---
with st.expander("📖 Guía Rápida de Uso para Alumnos"):
    st.markdown("""
    1. **Ingresa el activo:** Escribe el par (ej. `EUR/USD` o `USD/JPY`).
    2. **Define tu riesgo:** Mantén el riesgo por operación preferentemente entre **1% y 2%**.
    3. **Ingresa tu Stop Loss:** Mide los pips en TradingView y colócalos en la casilla.
    4. **Copia tus datos:** Usa el bloque inferior para copiar el lotaje, SL y TP exactos a tu MetaTrader o cTrader.
    """)

st.divider()

# --- SECCIÓN 1: ENTRADA DE DATOS ---
st.subheader("⚙️ Parámetros de la Operación")

col1, col2 = st.columns(2)

with col1:
    par_seleccionado = st.text_input("Par de Divisas / Activo", value="EUR/USD").strip().upper()
    
    symbol_tv = par_seleccionado.replace("/", "").replace("-", "").replace(" ", "")
    tv_url = f"https://es.tradingview.com/chart/?symbol=FX:{symbol_tv}"
    investing_url = "https://es.investing.com/economic-calendar/"
    
    st.link_button("📈 Ver Gráfico en TradingView", tv_url)
    st.link_button("📅 Ver Calendario Económico (Investing)", investing_url)
    
    es_jpy = "JPY" in par_seleccionado
    divisor_pip = 100.0 if es_jpy else 10000.0
    valor_pip_sugerido = 7.0 if es_jpy else 10.0
    
    balance = st.number_input("Balance de la Cuenta ($)", value=200.0, step=10.0)
    riesgo_pct = st.number_input("Porcentaje de Riesgo (%)", value=2.0, step=0.5)
    sl_pips = st.number_input("Tamaño del Stop Loss (Pips)", value=15.0, step=1.0)

with col2:
    tipo_orden = st.selectbox("Tipo de Orden", ["Compra", "Venta"])
    
    precio_defecto = 155.200 if es_jpy else 1.08500
    paso_precio = 0.001 if es_jpy else 0.00001
    formato_precio = "%.3f" if es_jpy else "%.5f"
    
    precio_entrada = st.number_input(
        "Precio de Entrada", 
        value=precio_defecto, 
        step=paso_precio, 
        format=formato_precio
    )
    
    valor_pip = st.number_input("Valor del Pip por Lote Estándar ($)", value=valor_pip_sugerido, step=0.5)
    ratio = st.number_input("Ratio (Riesgo:Beneficio)", value=3.0, step=0.5)

# --- SECCIÓN 2: CÁLCULOS MATEMÁTICOS ---
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

# --- SEMÁFORO DE GESTIÓN DE RIESGO (PSICOTRADING) ---
if riesgo_pct <= 2.0:
    st.success(f"🟢 **Gestión Institucional Excelente ({riesgo_pct}%):** Operación con riesgo controlado dentro de los estándares de ALEMA Trading Academy.")
elif riesgo_pct <= 5.0:
    st.warning(f"🟠 **Riesgo Moderado ({riesgo_pct}%):** Asegúrate de contar con alta confluencia técnica antes de tomar esta entrada.")
else:
    st.error(f"🔴 **Alerta de Sobrerriesgo ({riesgo_pct}%):** Riesgo elevado. Se sugiere reducir el riesgo para asegurar la longevidad de tu cuenta.")

# --- SECCIÓN 3: RESULTADOS ---
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

# --- COPIA RÁPIDA PARA METATRADER / CTRADER ---
st.subheader("📋 Datos Listos para Ejecutar")
st.markdown(f"""
<div class="copy-box">
<b>{par_seleccionado}</b> | <b>{tipo_orden.upper()}</b><br>
🔹 Lotaje: <b>{lotaje:.2f}</b><br>
🛑 Stop Loss: <b>{str_sl}</b><br>
🎯 Take Profit: <b>{str_tp}</b>
</div>
""", unsafe_allow_html=True)

# --- GRÁFICO VISUAL DE DISTRIBUCIÓN DE CUENTA ---
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

st.caption("© ALEMA Trading Academy. Reservados todos los derechos.")
