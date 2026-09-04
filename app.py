import config
import streamlit as st

# 1. Configuración de pantalla y variables globales
config.inicializar_configuracion()
config.inicializar_session_state()

# 2. Control de Autenticación con IF / ELSE Estricto
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

else:
    # 3. SISTEMA NATIVO DE NAVEGACIÓN (Solo visible tras iniciar sesión)
    
    # Declaramos las páginas apuntando a los archivos de tus módulos
    page_avance = st.Page("modulos/avance_academico.py", title="Mi Avance Académico", icon="🎓")
    page_calculadoras = st.Page("modulos/calculadoras.py", title="Calculadoras de Lotes", icon="🧮")
    page_journal = st.Page("modulos/journal.py", title="Trading Journal", icon="✍️")
    page_simulador = st.Page("modulos/simulador.py", title="Simulador Institucional", icon="📊")
    page_biblioteca = st.Page("modulos/biblioteca.py", title="Biblioteca de Guías", icon="📚")
    page_evaluaciones = st.Page("modulos/evaluaciones.py", title="Evaluaciones y Control Académico", icon="📝")

    # Inicializamos la navegación nativa en la barra lateral
    pg = st.navigation([
        page_avance,
        page_calculadoras,
        page_journal,
        page_simulador,
        page_biblioteca,
        page_evaluaciones
    ])

    # Elementos personalizados en la barra lateral (encima del menú)
    with st.sidebar:
        st.title("🧭 Menú Principal")
        st.caption(f"Usuario: **{st.session_state.get('nombre_usuario', 'Usuario')}**")
        st.divider()

    # Ejecutamos la página activa de forma 100% aislada
    pg.run()

    # Botón de Cerrar Sesión fijo al final de la barra lateral
    with st.sidebar:
        st.divider()
        if st.button("🚪 Cerrar Sesión", key="btn_logout_main", use_container_width=True):
            st.session_state.clear()
            st.rerun()
