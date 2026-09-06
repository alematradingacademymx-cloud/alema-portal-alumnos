import base64
import os
from datetime import datetime

import config
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# 1. Configuración de pantalla y variables globales
config.inicializar_configuracion()
config.inicializar_session_state()

# 🎛️ Forzar modo "embed" para ocultar la barra de Streamlit Cloud (Share/⭐/✏️/GitHub)
if st.query_params.get("embed") != "true":
    st.query_params["embed"] = "true"
    st.rerun()

# ==========================================
# 🔑 FUNCIÓN PARA CONVERTIR CUALQUIER FECHA
# ==========================================
def parsear_fecha(fecha_str):
    if not fecha_str or str(fecha_str).strip() == "":
        return datetime(2030, 12, 31).date()

    fecha_clean = str(fecha_str).strip()
    formatos = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
        "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y", "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formatos:
        try:
            return datetime.strptime(fecha_clean, fmt).date()
        except ValueError:
            pass
    return datetime(2030, 12, 31).date()


# ==========================================
# 🔑 BASE DE DATOS DE USUARIOS (GOOGLE SHEETS)
# ==========================================
SHEET_ID = "1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA"
URL_USUARIOS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Usuarios"


@st.cache_data(ttl=10)
def cargar_usuarios_desde_sheets():
    try:
        df = pd.read_csv(URL_USUARIOS, dtype=str)
        df.columns = df.columns.str.strip()
        df["Matricula"] = df["Matricula"].fillna("").str.strip().str.upper()
        df["Password"] = df["Password"].fillna("").str.strip()
        df["Tipo_Usuario"] = df["Tipo_Usuario"].fillna("ALUMNO").str.strip().str.upper()
        df["Fecha_Vencimiento"] = df["Fecha_Vencimiento"].fillna("2030-12-31").str.strip()
        df["Capital"] = pd.to_numeric(df["Capital"].fillna("300"), errors="coerce").fillna(300.0)

        dict_usuarios = {}
        for _, row in df.iterrows():
            if row["Matricula"]:
                dict_usuarios[row["Matricula"]] = {
                    "password": row["Password"],
                    "tipo": row["Tipo_Usuario"],
                    "vencimiento": row["Fecha_Vencimiento"],
                    "capital_base": float(row["Capital"]),
                }
        return dict_usuarios
    except Exception:
        return {}


USUARIOS_AUTORIZADOS = cargar_usuarios_desde_sheets()

# 2. Control de Autenticación con IF / ELSE Estricto
if not st.session_state.get("usuario_autenticado", False):
    # 🖼️ ISOTIPO CENTRADO
    archivo_iso = "alema_iso.png"
    if not os.path.exists(archivo_iso):
        coincidencias = [
            f
            for f in os.listdir(".")
            if f.lower().startswith("alema_iso") or f.lower().startswith("alema_a")
        ]
        if coincidencias:
            archivo_iso = coincidencias[0]

    if os.path.exists(archivo_iso):
        with open(archivo_iso, "rb") as img_file:
            img_b64 = base64.b64encode(img_file.read()).decode()
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 15px;">
                <img src="data:image/png;base64,{img_b64}" style="width: 95px; height: auto;">
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="main-title">ALEMA TRADING ACADEMY</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Portal Exclusivo para Alumnos Certificados y'
        " Suscriptores</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### 👋 ¡Bienvenido al Portal Institucional!")
    st.write(
        "Este es tu ecosistema de herramientas operativas, calculadoras de gestión"
        " de riesgo, journal de operaciones y biblioteca digital. Ingresa tus"
        " credenciales para comenzar."
    )
    st.markdown("---")
    st.subheader("🔒 Acceso al Portal Privado")
    st.write("Ingresa tus credenciales institucionales:")

    matricula_input = st.text_input("Matrícula / Usuario", key="login_user").strip().upper()
    password_input = st.text_input("Contraseña", type="password", key="login_pass")

    col_btn, _ = st.columns([1, 1])
    with col_btn:
        if st.button("🔑 Iniciar Sesión", use_container_width=True):
            if (
                matricula_input in USUARIOS_AUTORIZADOS
                and USUARIOS_AUTORIZADOS[matricula_input]["password"] == password_input
            ):
                user_info = USUARIOS_AUTORIZADOS[matricula_input]
                fecha_venc = parsear_fecha(user_info["vencimiento"])
                hoy = datetime.now().date()

                if hoy > fecha_venc:
                    st.error(
                        "⛔ **Suscripción Vencida:** Tu acceso venció el"
                        f" {fecha_venc.strftime('%d/%m/%Y')}. Por favor, renueva tu"
                        " suscripción para volver a ingresar."
                    )
                else:
                    st.session_state["usuario_autenticado"] = True
                    st.session_state["nombre_usuario"] = matricula_input
                    st.session_state["usuario_actual"] = matricula_input
                    st.session_state["tipo_usuario"] = user_info["tipo"]
                    st.session_state["balance_pedagogico"] = float(user_info["capital_base"])
                    st.success("¡Acceso concedido!")
                    st.rerun()
            else:
                st.error("❌ Matrícula o contraseña incorrecta. Verifica con administración.")

    st.markdown("---")
    st.markdown("### ¿Aún no tienes tu acceso al Portal?")
    st.write(
        "Obtén acceso a las **Calculadoras Operativas**, **Biblioteca de Guías en"
        " PDF** y **Cápsulas de Psicotrading** por solo **$150 MXN / mes**."
    )

    num_whatsapp = "528136462129"
    mensaje_preset_1 = (
        "¡Hola Daniela! 👋 Vengo del portal web y me gustaría adquirir mi"
        " suscripción a la Membresía Mensual Alema ($150 MXN/mes) para obtener mis"
        " credenciales de acceso."
    )
    url_wa_1 = f"https://wa.me/{num_whatsapp}?text={requests.utils.quote(mensaje_preset_1)}"

    st.markdown(
        f"""
        <a href="{url_wa_1}" target="_blank" style="text-decoration: none;">
            <div style="
                background-color: #25D366;
                color: #FFFFFF;
                padding: 12px 20px;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 1rem;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
                margin: 10px 0;">
                📲 Solicitar Membresía por WhatsApp
            </div>
        </a>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<h2 style='text-align: center;'>¿Deseas Formarte como Trader en"
        " ALEMA?</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #a0aec0; font-size: 1.1rem;'>"
        "Conoce nuestro programa educativo integral, herramientas operativas y"
        " acompañamiento personalizado.</p>",
        unsafe_allow_html=True,
    )

    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.markdown("### 📚 Ruta Académica Oficial")
        st.markdown(
            """
        * **Módulo Básico:** Fundamentos de mercados financieros, estructura de precios y lectura de velas.
        * **Módulo Intermedio:** Metodología institucional, zonas de oferta/demanda y Fibonacci.
        * **Módulo Avanzado:** Wyckoff, liquidez de mercado y modelos de entrada de alta probabilidad.
        * **Módulo Práctico & Psicotrading:** Gestión de riesgo matemática, bitácora y control emocional.
        """
        )
    with col_info2:
        st.markdown("### 💡 Beneficios del Portal Privado")
        st.markdown(
            """
        * **Calculadoras Operativas:** Gestión exacta de lotaje y riesgo por operación.
        * **Evaluaciones Progresivas:** Exámenes técnicos revisados directamente por Dirección General.
        * **Constancia Institucional:** Reconocimiento con validez interna al aprobar cada nivel.
        * **Biblioteca y Reportes:** Descarga de manuales en PDF y retroalimentación personalizada.
        """
        )

    st.divider()
    st.markdown(
        "<h3 style='text-align: center;'>💳 Cuota e Inscripciones</h3>",
        unsafe_allow_html=True,
    )

    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p2:
        st.info(
            "📌 **Membresía Elite ALEMA / Acceso al Portal:** **$1890 MXN /"
            " mes**\n\n**Incluye:**\n* Acceso completo al portal de alumnos\n*"
            " Calculadoras de gestión\n* Biblioteca digital\n* Clases"
            " personalizadas en vivo vía Zoom\n* Plataforma Educativa\n* Journal"
            " Alema\n* Evaluaciones"
        )

        mensaje_preset_2 = (
            "¡Hola Daniela! 👋 Vengo del portal web y me gustaría solicitar"
            " información e inscribirme a ALEMA Trading Academy. ¿Me podrías"
            " compartir los datos de pago y requisitos?"
        )
        url_wa_2 = f"https://wa.me/{num_whatsapp}?text={requests.utils.quote(mensaje_preset_2)}"

        st.markdown(
            f"""
            <a href="{url_wa_2}" target="_blank" style="text-decoration: none;">
                <button style="
                    width: 100%;
                    background-color: #25D366;
                    color: white;
                    padding: 14px 20px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 16px;
                    font-weight: bold;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;">
                    📲 ¡Quiero Inscribirme! (Contactar a Daniela por WhatsApp)
                </button>
            </a>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "<br><p style='text-align: center; color: #718096;'>© ALEMA Trading"
        " Academy. Reservados todos los derechos.</p>",
        unsafe_allow_html=True,
    )

else:
    # 3. SISTEMA NATIVO DE NAVEGACIÓN (Solo visible tras iniciar sesión)
    page_avance = st.Page("modulos/avance_academico.py", title="Mi Avance Académico", icon="🎓")
    page_calculadoras = st.Page("modulos/calculadoras.py", title="Calculadoras de Lotes", icon="🧮")
    page_journal = st.Page("modulos/journal.py", title="Trading Journal", icon="✍️")
    page_simulador = st.Page("modulos/simulador.py", title="Simulador Institucional", icon="📊")
    page_biblioteca = st.Page("modulos/biblioteca.py", title="Biblioteca de Guías", icon="📚")
    page_evaluaciones = st.Page("modulos/evaluaciones.py", title="Evaluaciones y Control Académico", icon="📝")

    tipo_usuario_actual = st.session_state.get("tipo_usuario", "ALUMNO").upper()

    if tipo_usuario_actual in ["ADMIN", "ALUMNO"]:
        paginas_disponibles = [
            page_avance,
            page_calculadoras,
            page_journal,
            page_simulador,
            page_biblioteca,
            page_evaluaciones,
        ]
    else:  # SUSCRIPTOR u otros roles con acceso limitado
        paginas_disponibles = [page_calculadoras, page_biblioteca]

    pg = st.navigation(paginas_disponibles)

    with st.sidebar:
        st.title("🧭 Menú Principal")
        st.caption(f"Usuario: **{st.session_state.get('nombre_usuario', 'Usuario')}**")
        st.caption(f"Perfil: {tipo_usuario_actual}")
        st.divider()

    pg.run()

    with st.sidebar:
        st.divider()
        if st.button("🚪 Cerrar Sesión", key="btn_logout_main", use_container_width=True):
            st.session_state.clear()
            components.html("<script>window.parent.location.reload();</script>", height=0)
            st.stop()
