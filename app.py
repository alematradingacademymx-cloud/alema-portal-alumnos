import streamlit as st
import config

# Importamos las funciones de renderizado desde la carpeta modulos
from modulos.avance_academico import render_avance_academico
from modulos.calculadoras import render_calculadoras
from modulos.journal import render_trading_journal
from modulos.simulador import render_simulador_alema_live
from modulos.biblioteca import render_biblioteca_guias
from modulos.evaluaciones import render_evaluaciones_control

# 1. Configuración de pantalla y variables globales
config.inicializar_configuracion()
config.inicializar_session_state()

# 2. Control de Login (Simulado / Módulo de Autenticación)
if not st.session_state.get("usuario_autenticado", False):
    st.title("🔐 ALEMA Trading Academy - Acceso")

    with st.form("form_login"):
        usuario = st.text_input("Usuario / Correo")
        password = st.text_input("Contraseña", type="password")
        btn_ingresar = st.form_submit_button("Ingresar a la Plataforma")

        if btn_ingresar:
            if usuario and password:
                st.session_state["usuario_autenticado"] = True
                st.session_state["nombre_usuario"] = usuario
                st.success("¡Bienvenido!")
                st.rerun()
            else:
                st.error("Por favor, ingresa tu usuario y contraseña.")
    st.stop()

# 3. Menú Lateral (Sidebar)
with st.sidebar:
    st.title("🧭 Menú Principal")
    st.caption(f"Usuario: **{st.session_state.get('nombre_usuario', 'Usuario')}**")

    opciones_menu = [
        "Mi Avance Académico",
        "Calculadoras de Lotes",
        "Trading Journal",
        "Simulador Institucional",
        "Biblioteca de Guías",
        "Evaluaciones y Control Académico"
    ]

    seccion_activa = st.radio(
        "Selecciona una sección:", 
        opciones_menu, 
        key="menu_navegacion_principal"
    )

    st.sidebar.divider()
    if st.sidebar.button("🚪 Cerrar Sesión", key="btn_logout_main", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 4. Enrutador Principal Aislado (Contenedor Limpio)
main_container = st.container()

with main_container:
    if seccion_activa == "Mi Avance Académico":
        render_avance_academico()

    elif seccion_activa == "Calculadoras de Lotes":
        render_calculadoras()

    elif seccion_activa == "Trading Journal":
        render_trading_journal()

    elif seccion_activa == "Simulador Institucional":
        render_simulador_alema_live()

    elif seccion_activa == "Biblioteca de Guías":
        render_biblioteca_guias()

    elif seccion_activa == "Evaluaciones y Control Académico":
        render_evaluaciones_control()
