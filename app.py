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
    """Convierte cadenas o marcas de tiempo a objetos datetime.date validos."""
    if pd.isna(valor_fecha) or not valor_fecha or str(valor_fecha).strip() == "":
        return datetime.date.today()
    try:
        return pd.to_datetime(valor_fecha).date()
    except Exception:
        return datetime.date.today()


# ==========================================
# PARTE 3: 🔑 BASE DE DATOS DE USUARIOS (GOOGLE SHEETS)
# ==========================================
SHEET_ID = "1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA"
# Se añade &gid=0 para asegurar la lectura de la primera pestaña
GDATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=30)
def cargar_base_datos_sheets():
    """Conecta con Google Sheets, limpia espacios en encabezados y valores."""
    try:
        df = pd.read_csv(GDATA_URL)
        # Limpieza estricta de nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo de columnas principales
        if "Matricula" in df.columns:
            df["Matricula"] = df["Matricula"].fillna("").astype(str).str.strip()
        if "Password" in df.columns:
            df["Password"] = df["Password"].fillna("").astype(str).str.strip()
            
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

# Control de acceso y verificación
if not st.session_state.get("autenticado", False):
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>ALEMA TRADING ACADEMY</h2>", unsafe_allow_html=True)
        st.caption("Portal Institucional de Alumnos y Coordinación")
        
        with st.form("form_login_principal"):
            usr_input = st.text_input("Matrícula / Usuario", key="input_usr").strip()
            pwd_input = st.text_input("Contraseña", type="password", key="input_pwd").strip()
            btn_login = st.form_submit_button("🔑 Iniciar Sesión", use_container_width=True)
            
            if btn_login:
                df_usuarios = cargar_base_datos_sheets()
                
                if not df_usuarios.empty and "Matricula" in df_usuarios.columns:
                    # Búsqueda coincidente sin distinguir mayúsculas/minúsculas
                    usuario_row = df_usuarios[df_usuarios["Matricula"].str.upper() == usr_input.upper()]
                    
                    if not usuario_row.empty:
                        pass_real = str(usuario_row.iloc[0]["Password"])
                        
                        if pwd_input == pass_real:
                            datos = usuario_row.iloc[0]
                            
                            st.session_state["autenticado"] = True
                            st.session_state["usuario_actual"] = str(datos["Matricula"])
                            st.session_state["tipo_usuario"] = str(datos.get("Tipo_Usuario", "ALUMNO")).upper()
                            
                            # Captura de variables financieras
                            try:
                                st.session_state["capital_inicial"] = float(datos.get("Capital", 0.0))
                            except (ValueError, TypeError):
                                st.session_state["capital_inicial"] = 0.0

                            st.session_state["challenge_nivel"] = str(datos.get("Challenge", "Nivel 1")) if pd.notna(datos.get("Challenge")) else "Nivel 1"
                            st.session_state["simulador_habilitado"] = str(datos.get("Simulador_Habilitado", "NO")).strip().upper() == "SI"
                            st.session_state["fecha_vencimiento"] = parsear_fecha(datos.get("Fecha_Vencimiento"))
                            
                            st.rerun()
                        else:
                            st.error("❌ Contraseña incorrecta.")
                    else:
                        st.error("❌ La matrícula ingresada no se encuentra registrada.")
                else:
                    st.error("❌ No se pudo validar la estructura de la base de datos.")

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
# ENRUTADOR PRINCIPAL DE CONTENIDO
# ==========================================

# ------------------------------------------
# PARTE 6: MI AVANCE ACADÉMICO
# ------------------------------------------
if seccion_activa == "Mi Avance Académico":
    st.title("📈 Mi Avance Académico")
    st.info("Resumen de trayectoria, estatus de beca y matrícula.")

# ------------------------------------------
# PARTE 7: CALCULADORAS DE LOTES
# ------------------------------------------
elif seccion_activa == "Calculadoras de Lotes":
    import plotly.graph_objects as go

    st.markdown("""
        <style>
            .copy-box {
                background-color: #1E293B;
                border-left: 4px solid #FF6B00;
                padding: 12px 16px;
                border-radius: 6px;
                margin: 10px 0;
                color: #F8FAFC;
                font-family: monospace;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("ALEMA TRADING ACADEMY")
    st.caption("Módulo Institucional de Gestión de Riesgo y Lotajes")

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
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                st.link_button("📈 TradingView", tv_url, use_container_width=True)
            with c_btn2:
                st.link_button("📅 Calendario", investing_url, use_container_width=True)
            
            es_jpy = "JPY" in par_seleccionado
            divisor_pip = 100.0 if es_jpy else 10000.0
            valor_pip_sugerido = 7.0 if es_jpy else 10.0

            if es_jpy:
                st.warning(
                    "⚠️ **Par JPY Detectado:**\n"
                    "• El valor del pip se ajustó a **$7.0 USD/lote**.\n"
                    "• 📌 **Importante:** Verifica el **Precio de Entrada** actual en TradingView."
                )
            
            capital_defecto = float(st.session_state.get("capital_inicial", 200.0))
            balance = st.number_input("Balance de la Cuenta ($)", value=max(10.0, capital_defecto), step=10.0, key="op_balance")
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
            capital_defecto_r = float(st.session_state.get("capital_inicial", 500.0))
            bal_r = st.number_input("Balance Total de la Cuenta ($)", value=max(10.0, capital_defecto_r), step=50.0, key="rap_balance")
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

# ------------------------------------------
# PARTE 8: TRADING JOURNAL
# ------------------------------------------
elif seccion_activa == "Trading Journal":
    st.title("📓 Bitácora de Operaciones (Trading Journal)")
    st.info("Módulo de registro de trades en desarrollo.")


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
