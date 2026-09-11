from datetime import datetime

import requests
import streamlit as st

import estilos

# Misma API que ya usa el Simulador (Terminal ALEMA) — sin costo adicional
API_KEY_TWELVEDATA = "6223c6d78f7a43b2872fc3acbb3f578e"

LISTA_ACTIVOS = [
    "EURUSD", "GBPUSD", "USDJPY", "EURJPY", "AUDUSD", "USDCAD", "USDCHF",
    "GBPJPY", "XAUUSD", "WTIUSD", "BRENTUSD", "US30", "SPX500", "NAS100",
    "GER40", "BTCUSD",
]

SIMBOLOS_MAP = {
    "EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "USDJPY": "USD/JPY",
    "EURJPY": "EUR/JPY", "AUDUSD": "AUD/USD", "USDCAD": "USD/CAD",
    "USDCHF": "USD/CHF", "GBPJPY": "GBP/JPY", "XAUUSD": "XAU/USD",
    "WTIUSD": "WTI/USD", "BRENTUSD": "BRENT/USD", "US30": "US30",
    "SPX500": "SPX", "NAS100": "NDX", "GER40": "DAX", "BTCUSD": "BTC/USD",
}


@st.cache_data(ttl=900)
def obtener_vela_anterior(simbolo):
    """Obtiene Máximo, Mínimo y Cierre del último día completo (no el de hoy)."""
    simbolo_api = SIMBOLOS_MAP.get(simbolo, "EUR/USD")
    try:
        url = (
            "https://api.twelvedata.com/time_series"
            f"?symbol={simbolo_api}&interval=1day&outputsize=3&apikey={API_KEY_TWELVEDATA}"
        )
        res = requests.get(url, timeout=6)
        data = res.json()
        valores = data.get("values", [])
        if len(valores) >= 2:
            # [0] es la vela de hoy (aún incompleta) — usamos [1], la del último día cerrado
            vela = valores[1]
            return {
                "high": float(vela["high"]),
                "low": float(vela["low"]),
                "close": float(vela["close"]),
                "fecha": vela["datetime"],
            }
    except Exception:
        pass
    return None


def calcular_pivotes_clasicos(high, low, close):
    """Fórmulas de Pivotes Clásicos (Floor Trader Pivots)."""
    pp = (high + low + close) / 3
    r1 = (2 * pp) - low
    s1 = (2 * pp) - high
    r2 = pp + (high - low)
    s2 = pp - (high - low)
    r3 = high + 2 * (pp - low)
    s3 = low - 2 * (high - pp)
    return {
        "R3": r3, "R2": r2, "R1": r1,
        "PP": pp,
        "S1": s1, "S2": s2, "S3": s3,
    }


def formato_decimales(simbolo):
    if "JPY" in simbolo:
        return "%.3f"
    if simbolo in ("XAUUSD", "WTIUSD", "BRENTUSD", "US30", "SPX500", "NAS100", "GER40", "BTCUSD"):
        return "%.2f"
    return "%.5f"


# ==========================================
# CÓDIGO DEL MÓDULO
# ==========================================
st.markdown(
    '<div class="main-title" style="text-align: left;">📐 Calculadora de'
    " Pivotes</div>",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title" style="text-align: left;">Pivotes Clásicos'
    " calculados con la vela del último día cerrado — soportes y"
    " resistencias exactos.</div>",
    unsafe_allow_html=True,
)

par_activo_pivote = st.selectbox(
    "Símbolo de Mercado", LISTA_ACTIVOS, key="select_pivote_activo"
)

col_btn_pivote, _ = st.columns([1, 2])
with col_btn_pivote:
    calcular_en_vivo = st.button(
        "🔄 Calcular con Datos en Vivo", use_container_width=True
    )

vela = None
if calcular_en_vivo:
    with st.spinner("Consultando la vela del último día cerrado..."):
        vela = obtener_vela_anterior(par_activo_pivote)
    if vela is None:
        st.error(
            "⚠️ No se pudo obtener la vela en vivo en este momento. Puedes"
            " ingresar los valores manualmente abajo."
        )

if vela:
    fmt = formato_decimales(par_activo_pivote)
    st.success(
        f"✅ Vela del {vela['fecha']} — Máximo: **{fmt % vela['high']}** |"
        f" Mínimo: **{fmt % vela['low']}** | Cierre: **{fmt % vela['close']}**"
    )

    niveles = calcular_pivotes_clasicos(vela["high"], vela["low"], vela["close"])

    st.markdown("#### 🎯 Niveles de Pivote")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(estilos.tarjeta("Resistencia 3", fmt % niveles["R3"]), unsafe_allow_html=True)
        st.markdown(estilos.tarjeta("Resistencia 2", fmt % niveles["R2"]), unsafe_allow_html=True)
        st.markdown(estilos.tarjeta("Resistencia 1", fmt % niveles["R1"]), unsafe_allow_html=True)
    with col2:
        st.markdown(estilos.tarjeta("PUNTO PIVOTE (PP)", fmt % niveles["PP"]), unsafe_allow_html=True)
    with col3:
        st.markdown(estilos.tarjeta("Soporte 1", fmt % niveles["S1"]), unsafe_allow_html=True)
        st.markdown(estilos.tarjeta("Soporte 2", fmt % niveles["S2"]), unsafe_allow_html=True)
        st.markdown(estilos.tarjeta("Soporte 3", fmt % niveles["S3"]), unsafe_allow_html=True)

st.divider()

with st.expander("✍️ O ingresa los valores manualmente"):
    st.caption(
        "Útil si quieres calcular pivotes de una vela específica (otro"
        " timeframe, un activo no listado, o para practicar el cálculo a"
        " mano)."
    )
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        high_manual = st.number_input("Máximo (High)", value=0.0, format="%.5f", key="pivote_high_manual")
    with col_m2:
        low_manual = st.number_input("Mínimo (Low)", value=0.0, format="%.5f", key="pivote_low_manual")
    with col_m3:
        close_manual = st.number_input("Cierre (Close)", value=0.0, format="%.5f", key="pivote_close_manual")

    if st.button("📐 Calcular Pivotes Manuales", key="btn_calcular_manual"):
        if high_manual > 0 and low_manual > 0 and close_manual > 0 and high_manual >= low_manual:
            niveles_m = calcular_pivotes_clasicos(high_manual, low_manual, close_manual)
            st.markdown("#### 🎯 Niveles de Pivote (Manual)")
            colm1, colm2, colm3 = st.columns(3)
            with colm1:
                st.markdown(estilos.tarjeta("Resistencia 3", f"{niveles_m['R3']:.5f}"), unsafe_allow_html=True)
                st.markdown(estilos.tarjeta("Resistencia 2", f"{niveles_m['R2']:.5f}"), unsafe_allow_html=True)
                st.markdown(estilos.tarjeta("Resistencia 1", f"{niveles_m['R1']:.5f}"), unsafe_allow_html=True)
            with colm2:
                st.markdown(estilos.tarjeta("PUNTO PIVOTE (PP)", f"{niveles_m['PP']:.5f}"), unsafe_allow_html=True)
            with colm3:
                st.markdown(estilos.tarjeta("Soporte 1", f"{niveles_m['S1']:.5f}"), unsafe_allow_html=True)
                st.markdown(estilos.tarjeta("Soporte 2", f"{niveles_m['S2']:.5f}"), unsafe_allow_html=True)
                st.markdown(estilos.tarjeta("Soporte 3", f"{niveles_m['S3']:.5f}"), unsafe_allow_html=True)
        else:
            st.warning("Ingresa valores válidos (Máximo debe ser mayor o igual al Mínimo).")
