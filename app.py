import streamlit as st
import base64
import os

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="ALEMA Trading Academy - Portal de Alumnos",
    page_icon="📈",
    layout="wide"
)

# ---------------------------------------------------------
# 2. BASE DE DATOS DE USUARIOS AUTORIZADOS
# ---------------------------------------------------------
USERS = {
    "admin": "alema2026",
    "alumno1": "alema123",
    "invitado": "suite150"
}

# ---------------------------------------------------------
# 3. CONTROL DE SESIÓN (LOGIN)
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def login():
    st.title("🔒 Portal de Alumnos - ALEMA Trading Academy")
    st.write("Bienvenido al ecosistema operativo de **ALEMA Trading Academy**.")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("Acceso a la Plataforma")
        username_input = st.text_input("Usuario / Matrícula")
        password_input = st.text_input("Contraseña", type="password")
        
        if st.button("Iniciar Sesión", use_container_width=True):
            if username_input in USERS and USERS[username_input] == password_input:
                st.session_state["authenticated"] = True
                st.session_state["user"] = username_input
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")
                
    with col2:
        # --- SECCIÓN DE VENTA / SUSCRIPCIÓN ---
        st.subheader("🚀 ¿Aún no tienes tu acceso?")
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

if not st.session_state["authenticated"]:
    login()
    st.stop()

# ---------------------------------------------------------
# 4. BARRA LATERAL (NAVEGACIÓN Y USUARIO)
# ---------------------------------------------------------
st.sidebar.title("📈 ALEMA Portal")
st.sidebar.write(f"Usuario activo: **{st.session_state.get('user', 'Alumno')}**")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state["authenticated"] = False
    st.rerun()

st.sidebar.markdown("---")

opcion = st.sidebar.radio(
    "Selecciona una herramienta:",
    ["🧮 Calculadora Avanzada", "⚡ Lotaje Rápido", "📚 Biblioteca de Guías"]
)

# ---------------------------------------------------------
# MÓDULO 1: CALCULADORA OPERATIVA AVANZADA Y COMPLETA
# ---------------------------------------------------------
if opcion == "🧮 Calculadora Avanzada":
    st.title("🧮 Calculadora Completa de Gestión de Riesgo")
    st.write("Selecciona el tipo de activo y calcula la posición exacta según las especificaciones de tu broker.")

    tab_forex, tab_cripto, tab_indices, tab_commodities = st.tabs([
        "💱 Forex (Divisas)", 
        "🪙 Criptomonedas", 
        "📊 Índices / Acciones", 
        "🥇 Commodities (Oro / Petróleo)"
    ])

    # --- TAB 1: FOREX ---
    with tab_forex:
        st.subheader("Gestión para Pares de Divisas (EUR, GBP, USD, JPY, etc.)")
        col1, col2 = st.columns(2)
        
        with col1:
            cap_fx = st.number_input("Capital de la Cuenta ($ USD)", min_value=1.0, value=1000.0, step=100.0, key="cap_fx")
            riesgo_fx_pct = st.number_input("Porcentaje de Riesgo (%)", min_value=0.1, max_value=100.0, value=1.0, step=0.1, key="r_fx")
            monto_riesgo_fx = cap_fx * (riesgo_fx_pct / 100)
            st.info(f"💵 Riesgo Máximo Autorizado: **${monto_riesgo_fx:.2f} USD**")

        with col2:
            sl_pips_fx = st.number_input("Stop Loss (en Pips)", min_value=0.1, value=20.0, step=1.0, key="sl_fx")
            tp_pips_fx = st.number_input("Take Profit (en Pips)", min_value=0.0, value=40.0, step=1.0, key="tp_fx")
            par_tipo = st.selectbox("Tipo de Par", ["Pares Estándar ($10 / pip por lote)", "Pares JPY ($10 approx)", "Pares Exóticos / Micro Lotes"], key="par_tipo")
            
            if par_tipo == "Pares Estándar ($10 / pip por lote)":
                val_pip = 10.0
            elif par_tipo == "Pares JPY ($10 approx)":
                val_pip = 9.5
            else:
                val_pip = st.number_input("Valor personalizado por Pip/Lote ($)", value=10.0, step=0.5, key="val_custom")

        if sl_pips_fx > 0 and val_pip > 0:
            lote_fx = monto_riesgo_fx / (sl_pips_fx * val_pip)
            beneficio_fx = (tp_pips_fx * val_pip) * lote_fx if tp_pips_fx > 0 else 0.0
            ratio_fx = (tp_pips_fx / sl_pips_fx) if sl_pips_fx > 0 else 0.0

            st.markdown("---")
            st.success(f"🎯 **Lote Estándar a ingresar:** `{lote_fx:.2f}` Lotes")
            
            col_res1, col_res2, col_res3 = st.columns(3)
            col_res1.metric("Riesgo (SL)", f"-${monto_riesgo_fx:.2f} USD")
            col_res2.metric("Beneficio (TP)", f"+${beneficio_fx:.2f} USD")
            col_res3.metric("Ratio R:B", f"1 : {ratio_fx:.2f}")

    # --- TAB 2: CRIPTOMONEDAS ---
    with tab_cripto:
        st.subheader("Gestión para BTC, ETH, SOL y Criptoactivos")
        col1, col2 = st.columns(2)

        with col1:
            cap_crypto = st.number_input("Capital ($ USD)", min_value=1.0, value=1000.0, step=100.0, key="cap_cr")
            riesgo_cr_pct = st.number_input("Riesgo (%)", min_value=0.1, value=1.0, step=0.1, key="r_cr")
            monto_riesgo_cr = cap_crypto * (riesgo_cr_pct / 100)
            st.info(f"💵 Riesgo Máximo: **${monto_riesgo_cr:.2f} USD**")

        with col2:
            p_entrada_cr = st.number_input("Precio de Entrada ($)", min_value=0.0001, value=60000.0, format="%.2f", key="pe_cr")
            p_sl_cr = st.number_input("Precio de Stop Loss ($)", min_value=0.0001, value=59000.0, format="%.2f", key="psl_cr")
            p_tp_cr = st.number_input("Precio de Take Profit ($)", min_value=0.0001, value=63000.0, format="%.2f", key="ptp_cr")

        dist_sl_cr = abs(p_entrada_cr - p_sl_cr)
        dist_tp_cr = abs(p_entrada_cr - p_tp_cr)

        if dist_sl_cr > 0:
            unidades_cr = monto_riesgo_cr / dist_sl_cr
            gain_cr = unidades_cr * dist_tp_cr
            ratio_cr = dist_tp_cr / dist_sl_cr

            st.markdown("---")
            st.success(f"🎯 **Posición a operar:** `{unidades_cr:.4f}` Unidades / Monedas")
            
            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.metric("Pérdida (SL)", f"-${monto_riesgo_cr:.2f} USD")
            col_r2.metric("Ganancia (TP)", f"+${gain_cr:.2f} USD")
            col_r3.metric("Ratio R:B", f"1 : {ratio_cr:.2f}")

    # --- TAB 3: ÍNDICES / ACCIONES ---
    with tab_indices:
        st.subheader("Gestión para US30, NAS100, SP500, GER40 y Acciones")
        col1, col2 = st.columns(2)

        with col1:
            cap_ind = st.number_input("Capital ($ USD)", min_value=1.0, value=2000.0, step=100.0, key="cap_ind")
            riesgo_ind_pct = st.number_input("Riesgo (%)", min_value=0.1, value=1.0, step=0.1, key="r_ind")
            monto_riesgo_ind = cap_ind * (riesgo_ind_pct / 100)
            st.info(f"💵 Riesgo Máximo: **${monto_riesgo_ind:.2f} USD**")

        with col2:
            puntos_sl = st.number_input("Puntos de Stop Loss", min_value=0.1, value=30.0, step=1.0, key="pts_sl")
            puntos_tp = st.number_input("Puntos de Take Profit", min_value=0.0, value=90.0, step=1.0, key="pts_tp")
            valor_punto = st.number_input("Valor del punto por Lote ($)", min_value=0.1, value=1.0, step=0.1, key="v_punto")

        if puntos_sl > 0 and valor_punto > 0:
            lote_ind = monto_riesgo_ind / (puntos_sl * valor_punto)
            gain_ind = (puntos_tp * valor_punto) * lote_ind if puntos_tp > 0 else 0.0
            ratio_ind = puntos_tp / puntos_sl

            st.markdown("---")
            st.success(f"🎯 **Lote recomendado en Índices:** `{lote_ind:.2f}` Lotes")
            
            col_i1, col_i2, col_i3 = st.columns(3)
            col_i1.metric("Pérdida (SL)", f"-${monto_riesgo_ind:.2f} USD")
            col_i2.metric("Ganancia (TP)", f"+${gain_ind:.2f} USD")
            col_i3.metric("Ratio R:B", f"1 : {ratio_ind:.2f}")

    # --- TAB 4: COMMODITIES ---
    with tab_commodities:
        st.subheader("Gestión para Oro (XAUUSD) y Petróleo (WTI)")
        col1, col2 = st.columns(2)

        with col1:
            cap_gold = st.number_input("Capital ($ USD)", min_value=1.0, value=1000.0, step=100.0, key="cap_g")
            riesgo_g_pct = st.number_input("Riesgo (%)", min_value=0.1, value=1.0, step=0.1, key="r_g")
            monto_riesgo_g = cap_gold * (riesgo_g_pct / 100)
            st.info(f"💵 Riesgo Máximo: **${monto_riesgo_g:.2f} USD**")

        with col2:
            p_entrada_g = st.number_input("Precio Entrada Oro", value=2400.00, format="%.2f", key="pe_g")
            p_sl_g = st.number_input("Precio Stop Loss", value=2395.00, format="%.2f", key="psl_g")
            p_tp_g = st.number_input("Precio Take Profit", value=2415.00, format="%.2f", key="ptp_g")

        dist_g_sl = abs(p_entrada_g - p_sl_g)
        dist_g_tp = abs(p_entrada_g - p_tp_g)

        if dist_g_sl > 0:
            # 1 lote estándar de Oro = 100 onzas ( $1 de movimiento = $100 dólares por lote )
            lotes_oro = monto_riesgo_g / (dist_g_sl * 100)
            gain_oro = (dist_g_tp * 100) * lotes_oro
            ratio_g = dist_g_tp / dist_g_sl

            st.markdown("---")
            st.success(f"🎯 **Lotes sugeridos en XAUUSD:** `{lotes_oro:.2f}` Lotes")
            
            col_g1, col_g2, col_g3 = st.columns(3)
            col_g1.metric("Pérdida (SL)", f"-${monto_riesgo_g:.2f} USD")
            col_g2.metric("Ganancia (TP)", f"+${gain_oro:.2f} USD")
            col_g3.metric("Ratio R:B", f"1 : {ratio_g:.2f}")

# ---------------------------------------------------------
# MÓDULO 2: CALCULADORA RÁPIDA DE LOTES
# ---------------------------------------------------------
elif opcion == "⚡ Lotaje Rápido":
    st.title("⚡ Calculadora Rápida de Lotaje")
    st.write("Calcula tu lotaje en segundos seleccionando parámetros estándar de Forex.")

    cap = st.number_input("Capital ($ USD)", value=500.0, step=100.0)
    pct = st.slider("Riesgo por operación (%)", 0.5, 5.0, 1.0, 0.5)
    pips = st.number_input("Pips de Stop Loss", value=15.0, step=1.0)

    monto = cap * (pct / 100)
    
    if pips > 0:
        lotes_std = monto / (pips * 10)
        
        st.markdown("---")
        st.metric(label="⚡ Lote a colocar en MT4 / MT5 / cTrader", value=f"{lotes_std:.2f} Lotes")
        st.info(f"💵 Estás arriesgando exactamente **${monto:.2f} USD**")

# ---------------------------------------------------------
# MÓDULO 3: BIBLIOTECA DE GUÍAS Y MANUALES PDF
# ---------------------------------------------------------
elif opcion == "📚 Biblioteca de Guías":
    st.title("📚 Biblioteca Digital de Guías y Manuales")
    st.write("Consulta y descarga el material educativo exclusivo de **ALEMA Trading Academy**.")

    guias = {
        "Manual del Trader (Básico)": "Manual del Trader (Básico).pdf",
        "Nueva Guía Acción del Precio": "Nueva guia Accion del precio.pdf"
    }

    guia_seleccionada = st.selectbox("Selecciona la guía que deseas abrir:", list(guias.keys()))
    archivo_pdf = guias[guia_seleccionada]

    if os.path.exists(archivo_pdf):
        with open(archivo_pdf, "rb") as f:
            pdf_bytes = f.read()

        st.download_button(
            label=f"📥 Descargar {guia_seleccionada} (PDF)",
            data=pdf_bytes,
            file_name=archivo_pdf,
            mime="application/pdf",
            use_container_width=True
        )

        st.markdown("---")
        st.subheader(f"Vista previa: {guia_seleccionada}")
        
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ El archivo `{archivo_pdf}` aún no ha sido cargado al repositorio de GitHub.")
st.caption("© ALEMA Trading Academy. Reservados todos los derechos.")
