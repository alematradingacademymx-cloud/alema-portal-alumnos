import base64
import hashlib
import os
from datetime import datetime

import bcrypt
import config
import estilos
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# 1. Configuración de pantalla y variables globales
config.inicializar_configuracion()
config.inicializar_session_state()

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
        if "Sesion_Version" in df.columns:
            df["Sesion_Version"] = df["Sesion_Version"].fillna("1").str.strip()
        else:
            df["Sesion_Version"] = "1"

        dict_usuarios = {}
        for _, row in df.iterrows():
            if row["Matricula"]:
                dict_usuarios[row["Matricula"]] = {
                    "password": row["Password"],
                    "tipo": row["Tipo_Usuario"],
                    "vencimiento": row["Fecha_Vencimiento"],
                    "capital_base": float(row["Capital"]),
                    "sesion_version": row["Sesion_Version"] or "1",
                }
        return dict_usuarios
    except Exception:
        return {}


USUARIOS_AUTORIZADOS = cargar_usuarios_desde_sheets()


def _es_hash_bcrypt(valor):
    """Detecta si un valor ya es un hash bcrypt (empieza con $2a$, $2b$ o $2y$)."""
    return isinstance(valor, str) and valor.startswith(("$2a$", "$2b$", "$2y$"))


def verificar_password(password_ingresado, password_almacenado):
    """Verifica la contraseña. Soporta hashes bcrypt y contraseñas antiguas en texto plano."""
    if _es_hash_bcrypt(password_almacenado):
        try:
            return bcrypt.checkpw(
                password_ingresado.encode("utf-8"), password_almacenado.encode("utf-8")
            )
        except Exception:
            return False
    # Contraseña antigua en texto plano
    return password_almacenado == password_ingresado


def migrar_password_a_hash(matricula, password_en_texto_plano):
    """Convierte una contraseña en texto plano a hash bcrypt y la guarda en el Sheet."""
    try:
        nuevo_hash = bcrypt.hashpw(
            password_en_texto_plano.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        payload = {
            "token": st.secrets["APPS_SCRIPT_TOKEN"],
            "accion": "actualizar_password",
            "matricula": matricula,
            "nuevo_hash": nuevo_hash,
        }
        requests.post(st.secrets["APPS_SCRIPT_URL"], json=payload, timeout=15)
    except Exception:
        pass  # Si falla la migración, no interrumpe el login; se reintentará en el próximo inicio de sesión


def guardar_sesion_local_storage(matricula, token):
    """Guarda el token también en localStorage del navegador (sobrevive refresh en cualquier sub-página)."""
    components.html(
        f"""
        <script>
        try {{
            window.localStorage.setItem('alema_u', {matricula!r});
            window.localStorage.setItem('alema_t', {token!r});
        }} catch (e) {{}}
        </script>
        """,
        height=0,
    )


def limpiar_sesion_local_storage():
    """Borra el token guardado en localStorage al cerrar sesión."""
    components.html(
        """
        <script>
        try {
            window.localStorage.removeItem('alema_u');
            window.localStorage.removeItem('alema_t');
        } catch (e) {}
        </script>
        """,
        height=0,
    )


def restaurar_sesion_desde_local_storage():
    """Si la URL no trae el token pero localStorage sí, redirige agregándolo a la URL.
    Esto evita que un refresh en cualquier sub-página pierda la sesión."""
    components.html(
        """
        <script>
        try {
            var params = new URLSearchParams(window.top.location.search);
            if (!params.has('u') || !params.has('t')) {
                var storedU = window.localStorage.getItem('alema_u');
                var storedT = window.localStorage.getItem('alema_t');
                if (storedU && storedT) {
                    params.set('u', storedU);
                    params.set('t', storedT);
                    var nuevaUrl = window.top.location.pathname + '?' + params.toString();
                    window.top.location.replace(nuevaUrl);
                }
            }
        } catch (e) {}
        </script>
        """,
        height=0,
    )


def generar_token_sesion(matricula, sesion_version):
    """Genera un token firmado. Si sesion_version cambia, todos los tokens viejos dejan de ser válidos."""
    secreto = st.secrets.get("SESSION_SECRET", "alema_cambia_este_secreto_por_defecto")
    base = f"{matricula}:{sesion_version}:{secreto}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]


def iniciar_sesion_usuario(matricula, user_info):
    """Deja al usuario autenticado en session_state y persiste el login en la URL + localStorage."""
    st.session_state["usuario_autenticado"] = True
    st.session_state["nombre_usuario"] = matricula
    st.session_state["usuario_actual"] = matricula
    st.session_state["tipo_usuario"] = user_info["tipo"]
    st.session_state["balance_pedagogico"] = float(user_info["capital_base"])
    st.session_state["sesion_version_usada"] = user_info["sesion_version"]

    token = generar_token_sesion(matricula, user_info["sesion_version"])
    st.query_params["u"] = matricula
    st.query_params["t"] = token
    # Nota: no escribimos localStorage aquí — el bloque de "reafirmación" que
    # corre justo después (en el mismo rerun, o en el siguiente si hay
    # st.rerun() de por medio) ya se encarga de eso una sola vez.


def cerrar_sesion_usuario():
    """Limpia la sesión, la URL y localStorage."""
    st.session_state.clear()
    st.query_params.clear()
    limpiar_sesion_local_storage()


def resolver_archivo_logo():
    """Encuentra el archivo del logo aunque el nombre exacto varíe un poco."""
    archivo_iso = "alema_iso.png"
    if not os.path.exists(archivo_iso):
        coincidencias = [
            f
            for f in os.listdir(".")
            if f.lower().startswith("alema_iso") or f.lower().startswith("alema_a")
        ]
        if coincidencias:
            archivo_iso = coincidencias[0]
    return archivo_iso if os.path.exists(archivo_iso) else None

# 2. Control de Autenticación con IF / ELSE Estricto

# 🔁 Si la URL no trae el token, intenta restaurarlo desde localStorage
if not st.session_state.get("usuario_autenticado", False):
    if not (st.query_params.get("u") and st.query_params.get("t")):
        restaurar_sesion_desde_local_storage()

# 🔁 Intento de auto-login vía token en la URL (para que un refresh no cierre la sesión)
if not st.session_state.get("usuario_autenticado", False):
    qp_matricula = st.query_params.get("u")
    qp_token = st.query_params.get("t")
    if qp_matricula and qp_token and qp_matricula in USUARIOS_AUTORIZADOS:
        info_qp = USUARIOS_AUTORIZADOS[qp_matricula]
        token_esperado = generar_token_sesion(qp_matricula, info_qp["sesion_version"])
        if qp_token == token_esperado:
            fecha_venc_qp = parsear_fecha(info_qp["vencimiento"])
            if datetime.now().date() <= fecha_venc_qp:
                iniciar_sesion_usuario(qp_matricula, info_qp)

if not st.session_state.get("usuario_autenticado", False):
    # 🖼️ ISOTIPO CENTRADO
    archivo_iso = resolver_archivo_logo()

    if archivo_iso:
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

    st.markdown('<div class="login-brand-title">ALEMA TRADING ACADEMY</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="login-brand-subtitle">Portal Exclusivo para Alumnos Certificados y'
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
            usuario_encontrado = matricula_input in USUARIOS_AUTORIZADOS
            password_almacenado = (
                USUARIOS_AUTORIZADOS[matricula_input]["password"]
                if usuario_encontrado
                else None
            )
            password_correcto = usuario_encontrado and verificar_password(
                password_input, password_almacenado
            )

            if usuario_encontrado and password_correcto:
                # Migración transparente: si la contraseña aún estaba en texto
                # plano, se convierte a hash bcrypt en este mismo inicio de sesión.
                if not _es_hash_bcrypt(password_almacenado):
                    migrar_password_a_hash(matricula_input, password_input)

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
                    iniciar_sesion_usuario(matricula_input, user_info)
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

    # 🔄 Verificación periódica: vencimiento de suscripción o sesión revocada por el admin
    try:
        from streamlit_autorefresh import st_autorefresh
    except ImportError:
        def st_autorefresh(interval=60000, key=None):
            pass

    st_autorefresh(interval=60000, key="chequeo_sesion_activa")

    nombre_usuario_sesion = st.session_state.get("nombre_usuario", "")
    info_usuario_sesion = USUARIOS_AUTORIZADOS.get(nombre_usuario_sesion)

    if info_usuario_sesion is None:
        # El usuario ya no existe en el Sheet
        cerrar_sesion_usuario()
        st.rerun()

    fecha_venc_sesion = parsear_fecha(info_usuario_sesion["vencimiento"])
    version_actual_sesion = info_usuario_sesion["sesion_version"]
    version_usada_sesion = st.session_state.get("sesion_version_usada")

    if datetime.now().date() > fecha_venc_sesion:
        cerrar_sesion_usuario()
        st.rerun()

    if version_usada_sesion != version_actual_sesion:
        # El admin reinició la sesión de este alumno desde el panel
        cerrar_sesion_usuario()
        st.rerun()

    # 🔁 Reafirmar el token en la URL y localStorage en cada carga — la
    # navegación entre páginas (st.Page) puede limpiar los query params,
    # así que lo volvemos a poner siempre para que un refresh nunca lo pierda.
    token_reafirmado = generar_token_sesion(nombre_usuario_sesion, version_actual_sesion)
    st.query_params["u"] = nombre_usuario_sesion
    st.query_params["t"] = token_reafirmado
    guardar_sesion_local_storage(nombre_usuario_sesion, token_reafirmado)

    page_avance = st.Page("modulos/avance_academico.py", title="Mi Avance Académico", icon="🎓")
    page_calculadoras = st.Page("modulos/calculadoras.py", title="Calculadoras de Lotes", icon="🧮")
    page_pivotes = st.Page("modulos/calculadora_pivotes.py", title="Calculadora de Pivotes", icon="📐")
    page_journal = st.Page("modulos/journal.py", title="Trading Journal", icon="✍️")
    page_simulador = st.Page("modulos/simulador.py", title="Terminal ALEMA", icon="📊")
    page_biblioteca = st.Page("modulos/biblioteca.py", title="Biblioteca de Guías", icon="📚")
    page_evaluaciones = st.Page("modulos/evaluaciones.py", title="Evaluaciones y Control Académico", icon="📝")

    tipo_usuario_actual = st.session_state.get("tipo_usuario", "ALUMNO").upper()

    if tipo_usuario_actual in ["ADMIN", "ALUMNO"]:
        paginas_disponibles = [
            page_avance,
            page_calculadoras,
            page_pivotes,
            page_journal,
            page_simulador,
            page_biblioteca,
            page_evaluaciones,
        ]
    else:  # SUSCRIPTOR u otros roles con acceso limitado
        paginas_disponibles = [page_calculadoras, page_pivotes, page_biblioteca]

    pg = st.navigation(paginas_disponibles)

    archivo_logo_sidebar = resolver_archivo_logo()
    if archivo_logo_sidebar:
        st.logo(archivo_logo_sidebar, size="large")
        estilos.logo_esquina_superior_derecha(archivo_logo_sidebar, alto_px=42)

    with st.sidebar:
        st.title("🧭 Menú Principal")
        st.caption(f"Usuario: **{st.session_state.get('nombre_usuario', 'Usuario')}**")
        st.caption(f"Perfil: {tipo_usuario_actual}")
        st.divider()

    pg.run()

    with st.sidebar:
        st.divider()
        if st.button("🚪 Cerrar Sesión", key="btn_logout_main", use_container_width=True):
            cerrar_sesion_usuario()
            components.html("<script>window.parent.location.reload();</script>", height=0)
            st.stop()
