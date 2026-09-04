import streamlit as st

def inicializar_configuracion():
    st.set_page_config(
        page_title="ALEMA Trading Academy",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def inicializar_session_state():
    if "usuario_autenticado" not in st.session_state:
        st.session_state["usuario_autenticado"] = False
    if "rol_usuario" not in st.session_state:
        st.session_state["rol_usuario"] = "Estudiante"
    if "nombre_usuario" not in st.session_state:
        st.session_state["nombre_usuario"] = ""
    if "menu_navegacion_principal" not in st.session_state:
        st.session_state["menu_navegacion_principal"] = "Mi Avance Académico"
