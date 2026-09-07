import streamlit as st

import estilos


def inicializar_configuracion():
    autenticado = st.session_state.get("usuario_autenticado", False)
    st.set_page_config(
        page_title="ALEMA Trading Academy",
        page_icon="📈",
        layout="wide" if autenticado else "centered",
        initial_sidebar_state="expanded" if autenticado else "collapsed",
    )
    estilos.inyectar_estilos()


def inicializar_session_state():
    if "usuario_autenticado" not in st.session_state:
        st.session_state["usuario_autenticado"] = False
    if "rol_usuario" not in st.session_state:
        st.session_state["rol_usuario"] = "Estudiante"
    if "nombre_usuario" not in st.session_state:
        st.session_state["nombre_usuario"] = ""
    if "menu_navegacion_principal" not in st.session_state:
        st.session_state["menu_navegacion_principal"] = "Mi Avance Académico"
