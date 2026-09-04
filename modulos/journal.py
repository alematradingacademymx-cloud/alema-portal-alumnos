# modulos/journal.py
import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Configuración de conexión a Google Sheets y Google Forms
SHEET_ID = "1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA"
URL_JOURNAL_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Journal"
URL_FORM_RESPONSE = "https://docs.google.com/forms/d/e/1FAIpQLSf9mOAhtFyAcjxJ2WK2mwCbPOtDa_9dSnsz9gHNPbOJ8M51cQ/formResponse"

@st.cache_data(ttl=3)
def cargar_journal_persiste(matricula_usuario):
    """Consulta la pestaña Journal en Google Sheets en tiempo real."""
    try:
        df = pd.read_csv(URL_JOURNAL_CSV, dtype=str)
        df.columns = df.columns.str.strip()
        
        col_mat = [c for c in df.columns if 'Matricula' in c or 'Matrícula' in c]
        if col_mat:
            nombre_col_mat = col_mat[0]
            df_user = df[df[nombre_col_mat].str.strip().str.upper() == str(matricula_usuario).strip().upper()].copy()
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

def render_trading_journal():
    """Módulo 3: Trading Journal Institucional & Bitácora Psicológica"""
    st.markdown('<div class="main-title" style="text-align: left;">ALEMA TRADING ACADEMY</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title" style="text-align: left;">Journal Institucional de Operaciones y Bitácora Psicológica</div>', unsafe_allow_html=True)

    usuario_actual = st.session_state.get("usuario_actual", st.session_state.get("nombre_usuario", "DIRALEX"))

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
                if res.status_code in [200, 0]:
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
