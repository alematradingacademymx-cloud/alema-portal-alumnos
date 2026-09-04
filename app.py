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

# ==========================================
# MÓDULO 2: CALCULADORAS DE LOTES
# ==========================================
def render_calculadoras():
    """Módulo aislado para el cálculo de gestión de riesgo y lotaje."""
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

# ==========================================
# MÓDULO 3: TRADING JOURNAL
# ==========================================
def render_trading_journal():
    """Módulo aislado para la bitácora de operaciones y control psicotrading."""
    import pandas as pd
    import requests
    from datetime import datetime

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

    usuario_actual = st.session_state.get("usuario_actual", "").strip().upper()
    df_user_journal = cargar_journal_persiste(usuario_actual)
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
                "entry.990498500": usuario_actual,
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
# PARTE 9: SIMULADOR INSTITUCIONAL ALEMA TRADING ACADEMY
# ==========================================
DATA_DIR_SIMULADOR = "data_persistencia"
os.makedirs(DATA_DIR_SIMULADOR, exist_ok=True)

def _get_user_filepaths(usuario: str):
    """Genera rutas de archivos aisladas por usuario para evitar colisiones."""
    usr_clean = str(usuario).strip().lower()
    return (
        os.path.join(DATA_DIR_SIMULADOR, f"posiciones_activas_{usr_clean}.json"),
        os.path.join(DATA_DIR_SIMULADOR, f"historial_cerradas_{usr_clean}.json")
    )

def cargar_datos_json(archivo: str, valor_defecto: list) -> list:
    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return valor_defecto
    return valor_defecto

def guardar_datos_json(archivo: str, datos: list):
    try:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

@st.cache_data(ttl=10)
def obtener_datos_usuario_desde_sheets(usuario_target: str):
    capital_defecto = float(st.session_state.get("capital_inicial", 300.00))
    nivel_defecto = str(st.session_state.get("challenge_nivel", "Nivel 1"))
    
    try:
        df = pd.read_csv(GDATA_URL)
        df.columns = [str(c).strip() for c in df.columns]
        
        col_user = next((c for c in df.columns if any(k in c.lower() for k in ["matricula", "usuario", "user"])), None)
        col_cap = next((c for c in df.columns if any(k in c.lower() for k in ["capital", "monto", "balance"])), None)
        col_challenge = next((c for c in df.columns if any(k in c.lower() for k in ["challenge", "nivel", "level"])), None)
        
        if col_user:
            filtro = df[df[col_user].astype(str).str.strip().str.lower() == str(usuario_target).strip().lower()]
            if not filtro.empty:
                if col_cap:
                    val_str = str(filtro[col_cap].values[0]).replace("$", "").replace(",", "").strip()
                    capital_defecto = float(val_str)
                if col_challenge:
                    val_chal = str(filtro[col_challenge].values[0]).strip()
                    if val_chal and val_chal.lower() != "nan":
                        nivel_defecto = val_chal
    except Exception:
        pass
        
    return capital_defecto, nivel_defecto

def obtener_config_activo(simbolo: str):
    if "JPY" in simbolo: return 3, "%.3f", 0.001, 0.100, 0.200, 0.015
    elif "XAU" in simbolo: return 2, "%.2f", 0.10, 2.00, 4.00, 0.35
    elif "WTI" in simbolo or "BRENT" in simbolo: return 2, "%.2f", 0.01, 0.30, 0.60, 0.04
    elif "BTC" in simbolo: return 2, "%.2f", 1.0, 100.0, 200.0, 25.00
    elif any(idx in simbolo for idx in ["US30", "NAS100", "GER40"]): return 2, "%.2f", 1.0, 20.0, 40.0, 2.00
    elif "SPX" in simbolo: return 2, "%.2f", 0.10, 4.00, 8.00, 0.40
    else: return 5, "%.5f", 0.00001, 0.00100, 0.00200, 0.00012

def calcular_pnl_institucional(activo: str, tipo: str, entrada: float, salida: float, lotes: float) -> float:
    diferencia = (salida - entrada) if tipo == "BUY" else (entrada - salida)
    
    if "XAU" in activo: return diferencia * 100.0 * lotes
    elif "BTC" in activo: return diferencia * 1.0 * lotes
    elif "WTI" in activo or "BRENT" in activo: return diferencia * 1000.0 * lotes
    elif any(idx in activo for idx in ["US30", "SPX500", "NAS100", "GER40"]): return diferencia * 1.0 * lotes
    elif "JPY" in activo:
        valor_pip_usd = 1000.0 / salida if salida != 0 else 6.80
        return diferencia * 100.0 * valor_pip_usd * lotes
    else:
        return diferencia * 100000.0 * lotes

def render_simulador_alema_live():
    """Bloque totalmente aislado para la vista Alema Trade Live."""
    
    st_autorefresh(interval=4000, key="auto_refresh_terminal_forex_live")
    
    usuario = st.session_state.get("usuario_actual", "estudiante_demo")
    es_admin = st.session_state.get("tipo_usuario") == "ADMIN"
    arch_activas, arch_historial = _get_user_filepaths(usuario)

    posiciones_abiertas = cargar_datos_json(arch_activas, [])
    historial_cerradas = cargar_datos_json(arch_historial, [])

    capital_base, nivel_challenge = obtener_datos_usuario_desde_sheets(usuario)
    pnl_acumulado = sum(float(trade.get("Beneficio", 0.0)) for trade in historial_cerradas)
    balance_total = capital_base + pnl_acumulado

    if 'cache_precios_forex' not in st.session_state: st.session_state.cache_precios_forex = {}
    if 'ultimo_tiempo_api' not in st.session_state: st.session_state.ultimo_tiempo_api = {}
    if 'mercado_forex_df' not in st.session_state: st.session_state.mercado_forex_df = {}

    def obtener_cotizacion(simbolo):
        dec, _, step_val, _, _, spread_val = obtener_config_activo(simbolo)
        simbolos_map = {
            "EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "USDJPY": "USD/JPY", "EURJPY": "EUR/JPY",
            "AUDUSD": "AUD/USD", "USDCAD": "USD/CAD", "USDCHF": "USD/CHF", "GBPJPY": "GBP/JPY",
            "XAUUSD": "XAU/USD", "WTIUSD": "WTI/USD", "BRENTUSD": "BRENT/USD", "US30": "US30",
            "SPX500": "SPX", "NAS100": "NDX", "GER40": "DAX", "BTCUSD": "BTC/USD"
        }
        simbolo_api = simbolos_map.get(simbolo, "EUR/USD")
        ahora = time.time()
        
        if ahora - st.session_state.ultimo_tiempo_api.get(simbolo, 0) > 45:
            try:
                url = f"https://api.twelvedata.com/price?symbol={simbolo_api}&apikey=6223c6d78f7a43b2872fc3acbb3f578e"
                res = requests.get(url, timeout=3)
                if res.status_code == 200:
                    data = res.json()
                    if "price" in data:
                        st.session_state.cache_precios_forex[simbolo] = float(data["price"])
            except Exception:
                pass
            finally:
                st.session_state.ultimo_tiempo_api[simbolo] = ahora

        precio_base = st.session_state.cache_precios_forex.get(simbolo, 1.0000)
        ruido = np.random.normal(0, step_val * 1.2)
        precio_bid = round(precio_base + ruido, dec)
        precio_ask = round(precio_bid + spread_val, dec)
        return precio_bid, precio_ask, precio_bid

    precios_ticks = {}
    def get_precio(simbolo):
        if simbolo not in precios_ticks:
            precios_ticks[simbolo] = obtener_cotizacion(simbolo)
        return precios_ticks[simbolo]

    st.markdown("""
        <style>
            .mt5-terminal-card { background-color: #131722; border: 1px solid #2A2E39; padding: 10px 15px; border-radius: 4px; margin-bottom: 8px; font-family: sans-serif; }
            .live-ticker-price { color: #f59e0b; font-weight: 700; }
            .live-ticker-bid { color: #ef5350; font-weight: 700; }
            .live-ticker-ask { color: #26a69a; font-weight: 700; }
            .mt5-table-container { overflow-x: auto; border: 1px solid #2A2E39; border-radius: 4px; }
            .mt5-table { width: 100%; border-collapse: collapse; font-size: 13px; background-color: #131722; color: #d1d4dc; }
            .mt5-table th { background-color: #1e222d; color: #848e9c; padding: 8px; text-align: left; }
            .mt5-table td { padding: 7px 12px; border-bottom: 1px solid #1e222d; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size: 22px; font-weight: 700; margin-bottom: 10px;">ALEMA TRADING ACADEMY | Terminal Institucional</div>', unsafe_allow_html=True)

    lista_activos = ["EURUSD", "GBPUSD", "USDJPY", "EURJPY", "AUDUSD", "USDCAD", "USDCHF", "GBPJPY", "XAUUSD", "WTIUSD", "BRENTUSD", "US30", "SPX500", "NAS100", "GER40", "BTCUSD"]
    par_activo = st.selectbox("Símbolo de Mercado", lista_activos, key="select_chart_asset_forex")

    bid_actual, ask_actual, precio_vivo = get_precio(par_activo)

    if par_activo not in st.session_state.mercado_forex_df:
        fechas = [dt.now() - timedelta(minutes=15 * i) for i in range(50)][::-1]
        vol = precio_vivo * 0.0004
        closes = np.linspace(precio_vivo - (vol * 4), precio_vivo, 50) + np.random.normal(0, vol * 0.2, 50)
        opens = closes + np.random.normal(0, vol * 0.1, 50)
        highs = np.maximum(opens, closes) + abs(np.random.normal(0, vol * 0.2, 50))
        lows = np.minimum(opens, closes) - abs(np.random.normal(0, vol * 0.2, 50))
        st.session_state.mercado_forex_df[par_activo] = pd.DataFrame({'Open': opens, 'High': highs, 'Low': lows, 'Close': closes}, index=fechas)

    df_chart = st.session_state.mercado_forex_df[par_activo]
    df_chart.iloc[-1, df_chart.columns.get_loc('Close')] = precio_vivo

    posiciones_conservadas = []
    hubo_cierre_auto = False

    for pos in posiciones_abiertas:
        p_bid, p_ask, _ = get_precio(pos["activo"])
        dec_pos, _, _, _, _, _ = obtener_config_activo(pos["activo"])
        
        pos["bid_vela_actual"], pos["ask_vela_actual"] = p_bid, p_ask
        tp_exacto, sl_exacto = round(pos["tp"], dec_pos), round(pos["sl"], dec_pos)
        
        cierre_trigger = False
        p_salida = p_bid if pos["tipo"] == "BUY" else p_ask

        if pos["tipo"] == "BUY":
            if p_bid >= tp_exacto: cierre_trigger, p_salida = True, tp_exacto
            elif p_bid <= sl_exacto: cierre_trigger, p_salida = True, sl_exacto
        else:
            if p_ask <= tp_exacto: cierre_trigger, p_salida = True, tp_exacto
            elif p_ask >= sl_exacto: cierre_trigger, p_salida = True, sl_exacto

        if cierre_trigger:
            pnl_real = calcular_pnl_institucional(pos["activo"], pos["tipo"], pos["entrada"], p_salida, pos["lotes"])
            historial_cerradas.append({
                "Tipo": pos['tipo'].lower(), "Volumen": pos['lotes'], "Símbolo": pos["activo"],
                "S / L": sl_exacto, "T / P": tp_exacto, "Tiempo Cierre": dt.now().strftime("%Y.%m.%d %H:%M:%S"),
                "Precio Cierre": p_salida, "Beneficio": round(pnl_real, 2)
            })
            guardar_datos_json(arch_historial, historial_cerradas)
            hubo_cierre_auto = True
        else:
            posiciones_conservadas.append(pos)

    if hubo_cierre_auto:
        guardar_datos_json(arch_activas, posiciones_conservadas)
        st.rerun()

    col1, col2, col3, col4, *col_admin = st.columns(5 if es_admin else 4)
    with col1: st.metric("Balance Base", f"${balance_total:,.2f}")
    with col2:
        flotante = sum(calcular_pnl_institucional(p["activo"], p["tipo"], p["entrada"], p.get("bid_vela_actual", p["entrada"]) if p["tipo"] == "BUY" else p.get("ask_vela_actual", p["entrada"]), p["lotes"]) for p in posiciones_conservadas)
        st.metric("Beneficio Flotante", f"${flotante:,.2f}", delta=f"${flotante:,.2f}")
    with col3: st.metric("Posiciones Activas", f"{len(posiciones_conservadas)}")
    with col4: st.metric("Fase Challenge", nivel_challenge)
    if es_admin and col_admin:
        with col_admin[0]:
            if st.button("🔄 Sincronizar Sheets"):
                st.cache_data.clear()
                st.rerun()

    st.divider()

    col_graf, col_pan = st.columns([2.4, 1.0])
    dec_p, fmt_p, step_p, dist_sl, dist_tp, spread_p = obtener_config_activo(par_activo)

    with col_graf:
        st.markdown(f"Gráfico **{par_activo}** | BID: <span class='live-ticker-bid'>{fmt_p % bid_actual}</span> | ASK: <span class='live-ticker-ask'>{fmt_p % ask_actual}</span>", unsafe_allow_html=True)
        fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name=par_activo)])
        
        for pos in posiciones_conservadas:
            if pos["activo"] == par_activo:
                fig.add_hline(y=pos["entrada"], line_dash="dash", line_color="#2962FF")
                fig.add_hline(y=pos["tp"], line_dash="dot", line_color="#26a69a")
                fig.add_hline(y=pos["sl"], line_dash="dot", line_color="#ef5350")

        fig.update_layout(template="plotly_dark", paper_bgcolor="#131722", plot_bgcolor="#131722", height=400, margin=dict(l=5, r=5, t=5, b=5))
        st.plotly_chart(fig, use_container_width=True)

    with col_pan:
        st.markdown("### Nueva Orden")
        sim_tipo = st.radio("Dirección", ["BUY", "SELL"], horizontal=True, key="sim_dir_forex")
        sim_lotes = st.number_input("Volumen (Lotes)", value=0.10, min_value=0.01, step=0.01)
        p_ref = ask_actual if sim_tipo == "BUY" else bid_actual

        sim_sl = st.number_input("Stop Loss", value=float(round(p_ref - dist_sl if sim_tipo == "BUY" else p_ref + dist_sl, dec_p)), format=fmt_p, step=step_p)
        sim_tp = st.number_input("Take Profit", value=float(round(p_ref + dist_tp if sim_tipo == "BUY" else p_ref - dist_tp, dec_p)), format=fmt_p, step=step_p)

        if st.button("EJECUTAR ORDEN", use_container_width=True):
            nueva_orden = {
                "id": int(dt.now().timestamp()),
                "tiempo_apertura": dt.now().strftime("%Y.%m.%d %H:%M:%S"),
                "activo": par_activo, "tipo": sim_tipo, "lotes": float(sim_lotes),
                "entrada": float(p_ref), "sl": float(sim_sl), "tp": float(sim_tp)
            }
            posiciones_conservadas.append(nueva_orden)
            guardar_datos_json(arch_activas, posiciones_conservadas)
            st.rerun()

    st.markdown("### Posiciones Abiertas")
    if posiciones_conservadas:
        for idx, pos in enumerate(posiciones_conservadas):
            p_salida = pos.get("bid_vela_actual", pos["entrada"]) if pos["tipo"] == "BUY" else pos.get("ask_vela_actual", pos["entrada"])
            pnl_card = calcular_pnl_institucional(pos["activo"], pos["tipo"], pos["entrada"], p_salida, pos["lotes"])
            
            st.markdown(f'<div class="mt5-terminal-card"><b>{pos["activo"]}</b> | {pos["tipo"]} | Entrada: {pos["entrada"]} | PnL: <b>${pnl_card:,.2f} USD</b></div>', unsafe_allow_html=True)
            if st.button(f"Cerrar #{pos['id']}", key=f"close_{pos['id']}"):
                historial_cerradas.append({
                    "Tipo": pos['tipo'].lower(), "Volumen": pos['lotes'], "Símbolo": pos['activo'],
                    "S / L": pos['sl'], "T / P": pos['tp'], "Tiempo Cierre": dt.now().strftime("%Y.%m.%d %H:%M:%S"),
                    "Precio Cierre": p_salida, "Beneficio": round(pnl_card, 2)
                })
                posiciones_conservadas.pop(idx)
                guardar_datos_json(arch_historial, historial_cerradas)
                guardar_datos_json(arch_activas, posiciones_conservadas)
                st.rerun()
    else:
        st.info("No hay posiciones activas.")

    st.markdown("### Bitácora Histórica")
    if es_admin and st.button("🗑️ Limpiar Historial (Admin)"):
        guardar_datos_json(arch_historial, [])
        st.rerun()

    if historial_cerradas:
        df_hist = pd.DataFrame(historial_cerradas)
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("Sin registros históricos.")
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
