import streamlit as st
from streamlit_autorefresh import st_autorefresh

def render_simulador_alema_live():
    # Solo activa el auto-refresh si la sección activa realmente es el simulador
    if st.session_state.get("menu_navegacion_principal") == "Simulador Institucional":
        st_autorefresh(interval=4000, key="auto_refresh_terminal_forex_live")
        
    st.title("⚡ Simulador Institucional - Alema Trade Live")
    st.info("Terminal simulador en vivo.")
    # Aquí irá el código de tu simulador
