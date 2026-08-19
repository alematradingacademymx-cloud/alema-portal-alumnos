import streamlit as st

# Configuración de página
st.set_page_config(page_title="ALEMA Trading Academy", page_icon="📈", layout="centered")

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-size: 32px;
        font-weight: 800;
        color: #FF6B00; /* Color Naranja Institucional */
        margin-bottom: 0px;
        letter-spacing: 1px;
    }
    .sub-title {
        text-align: center;
        font-size: 18px;
        color: #64748B;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado principal
st.markdown('<div class="main-title">ALEMA TRADING ACADEMY</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Calculadora Operativa & Gestión de Riesgo Multi-Activo</div>', unsafe_allow_html=True)

st.divider()

# --- SECCIÓN 1: ENTRADA DE DATOS ---
st.subheader("⚙️ Parámetros de la Operación")

col1, col2 = st.columns(2)

with col1:
    par_seleccionado = st.text_input("Par de Divisas / Activo", value="EUR/USD").strip().upper()
    
    # Limpiar el nombre del par para el enlace de TradingView
    symbol_tv = par_seleccionado.replace("/", "").replace("-", "").replace(" ", "")
    tv_url = f"https://es.tradingview.com/chart/?symbol=FX:{symbol_tv}"
    investing_url = "https://es.investing.com/economic-calendar/"
    
    # Botones de herramientas externas
    st.link_button(f"📈 Ver Gráfico en TradingView", tv_url)
    st.link_button("📅 Ver Calendario Económico (Investing)", investing_url)
    
    # Detección de Par JPY
    es_jpy = "JPY" in par_seleccionado
    divisor_pip = 100.0 if es_jpy else 10000.0
    valor_pip_sugerido = 7.0 if es_jpy else 10.0
    
    balance = st.number_input("Balance de la Cuenta ($)", value=200.0, step=10.0)
    riesgo_pct = st.number_input("Porcentaje de Riesgo (%)", value=5.0, step=0.5)
    sl_pips = st.number_input("Tamaño del Stop Loss (Pips)", value=15.0, step=1.0)

with col2:
    tipo_orden = st.selectbox("Tipo de Orden", ["Compra", "Venta"])
    
    # Configuración precisa de decimales
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

# Cartel informativo dinámico
if es_jpy:
    st.info("💡 **Modo Par JPY Detectado:** Valor del pip ajustado a **$7.00 USD** y precios con 3 decimales.")
else:
    st.info("💡 **Modo Par Estándar Detectado:** Valor del pip ajustado a **$10.00 USD** y precios con 5 decimales.")

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
else: # Venta
    precio_sl = precio_entrada + distancia_sl_precio
    precio_tp = precio_entrada - distancia_tp_precio

st.divider()

# --- SECCIÓN 3: RESULTADOS EN TARJETAS ---
st.subheader("📊 Resultados de Ejecución")

res_col1, res_col2 = st.columns(2)

# Formateo de precios exacto
str_sl = f"{precio_sl:.3f}" if es_jpy else f"{precio_sl:.5f}"
str_tp = f"{precio_tp:.3f}" if es_jpy else f"{precio_tp:.5f}"

with res_col1:
    st.metric(label="Riesgo Máximo ($)", value=f"${dinero_arriesgar:.2f}")
    st.metric(label="Lotaje Exacto", value=f"{lotaje:.2f}")
    st.metric(label="Precio Stop Loss", value=str_sl)

with res_col2:
    st.metric(label="Ganancia Potencial ($)", value=f"${ganancia:.2f}")
    st.metric(label="Tamaño TP (PIPS)", value=f"{tp_pips:.0f} pips")
    st.metric(label="Precio Take Profit", value=str_tp)

st.caption("© ALEMA Trading Academy. Reservados todos los derechos.")
