import streamlit as st

# Configuración de página con estética de la Academia
st.set_page_config(page_title="ALEMA Trading Academy", page_icon="📈", layout="centered")

# Estilos CSS personalizados para la marca
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        color: #1E293B;
        margin-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        font-size: 18px;
        color: #64748B;
        margin-bottom: 25px;
    }
    .stButton>button {
        width: 100%;
        background-color: #00E676;
        color: black;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado principal
st.markdown('<div class="main-title">ALEMA Trading Academy</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Calculadora Operativa & Gestión de Riesgo</div>', unsafe_allow_html=True)

st.divider()

# --- SECCIÓN 1: ENTRADA DE DATOS ---
st.subheader("⚙️ Parámetros de la Operación")

col1, col2 = st.columns(2)

with col1:
    balance = st.number_input("Balance de la Cuenta ($)", value=200.0, step=10.0)
    riesgo_pct = st.number_input("Porcentaje de Riesgo (%)", value=5.0, step=0.5)
    sl_pips = st.number_input("Tamaño del Stop Loss (Pips)", value=15.0, step=1.0)
    valor_pip = st.number_input("Valor del Pip por Lote Estándar ($)", value=10.0, step=1.0)

with col2:
    precio_entrada = st.number_input("Precio de Entrada", value=1.1522, format="%.5f")
    ratio = st.number_input("Ratio (Riesgo:Beneficio)", value=3.0, step=0.5)
    tipo_orden = st.selectbox("Tipo de Orden", ["Venta", "Compra"])

# --- SECCIÓN 2: CÁLCULOS MATEMÁTICOS ---
# 1. Dinero máximo a arriesgar
dinero_arriesgar = balance * (riesgo_pct / 100.0)

# 2. Lotaje Exacto
lotaje = dinero_arriesgar / (sl_pips * valor_pip) if sl_pips > 0 and valor_pip > 0 else 0.0

# 3. Pips de TP
tp_pips = sl_pips * ratio

# 4. Ganancia ($) -> Fórmula original: Lotaje * TP Pips * Valor Pip
ganancia = lotaje * tp_pips * valor_pip

# 5. Precios de Salida
if tipo_orden == "Venta":
    precio_sl = precio_entrada + (sl_pips * 0.0001)
    precio_tp = precio_entrada - (tp_pips * 0.0001)
else:
    precio_sl = precio_entrada - (sl_pips * 0.0001)
    precio_tp = precio_entrada + (tp_pips * 0.0001)

st.divider()

# --- SECCIÓN 3: RESULTADOS EN TARJETAS ---
st.subheader("📊 Resultados de Ejecución")

res_col1, res_col2 = st.columns(2)

with res_col1:
    st.metric(label="Riesgo Máximo ($)", value=f"${dinero_arriesgar:.2f}")
    st.metric(label="Lotaje Exacto", value=f"{lotaje:.2f}")
    st.metric(label="Precio Stop Loss", value=f"{precio_sl:.5f}")

with res_col2:
    st.metric(label="Ganancia Potencial ($)", value=f"${ganancia:.2f}")
    st.metric(label="Tamaño TP (PIPS)", value=f"{tp_pips:.0f} pips")
    st.metric(label="Precio Take Profit", value=f"{precio_tp:.5f}")

st.caption("© ALEMA Trading Academy. Reservados todos los derechos.")
