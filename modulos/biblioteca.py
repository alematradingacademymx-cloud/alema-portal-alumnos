import pandas as pd
import requests
import streamlit as st

import estilos

SHEET_ID = "1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA"
URL_GUIAS_EXCLUSIVAS_CSV = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Guias_Exclusivas"
)
URL_USUARIOS_CSV = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
)

NUMERO_WHATSAPP_VENTAS = "528136462129"


@st.cache_data(ttl=15)
def cargar_paquetes_exclusivos():
    """Lee la pestaña Guias_Exclusivas y agrupa los archivos por paquete."""
    paquetes = {}
    try:
        df = pd.read_csv(URL_GUIAS_EXCLUSIVAS_CSV, dtype=str)
        df.columns = df.columns.str.strip()
        for _, row in df.iterrows():
            nombre_archivo = str(row.get("Nombre de la guia", "")).strip()
            paquete = str(row.get("Paquete", "")).strip()
            precio = str(row.get("Precio", "")).strip()
            if not paquete or paquete.lower() == "nan":
                continue
            if paquete not in paquetes:
                paquetes[paquete] = {"precio": precio, "archivos": []}
            if nombre_archivo and nombre_archivo.lower() != "nan":
                paquetes[paquete]["archivos"].append(nombre_archivo)
    except Exception:
        pass
    return paquetes


@st.cache_data(ttl=15)
def cargar_guias_desbloqueadas(matricula):
    """Lee qué paquetes tiene desbloqueados un alumno específico."""
    try:
        df = pd.read_csv(URL_USUARIOS_CSV, dtype=str)
        df.columns = df.columns.str.strip()
        filtro = df[
            df["Matricula"].astype(str).str.strip().str.upper()
            == str(matricula).strip().upper()
        ]
        if filtro.empty or "Guias_Desbloqueadas" not in df.columns:
            return []
        valor = str(filtro["Guias_Desbloqueadas"].values[0]).strip()
        if not valor or valor.lower() == "nan":
            return []
        return [p.strip() for p in valor.split(",") if p.strip()]
    except Exception:
        return []


@st.cache_data(ttl=15)
def cargar_lista_matriculas_biblioteca():
    """Lee todas las matrículas registradas (para el selector del admin)."""
    try:
        df = pd.read_csv(URL_USUARIOS_CSV, dtype=str)
        df.columns = df.columns.str.strip()
        matriculas = (
            df["Matricula"].dropna().astype(str).str.strip().str.upper().unique()
        )
        return sorted([m for m in matriculas if m])
    except Exception:
        return []


def actualizar_guias_desbloqueadas_sheet(matricula, guias_desbloqueadas_str):
    try:
        payload = {
            "token": st.secrets["APPS_SCRIPT_TOKEN"],
            "accion": "actualizar_guias_desbloqueadas",
            "matricula": matricula,
            "guias_desbloqueadas": guias_desbloqueadas_str,
        }
        resp = requests.post(st.secrets["APPS_SCRIPT_URL"], json=payload, timeout=15)
        data = resp.json()
        return data.get("success", False), data.get("error", "")
    except Exception as e:
        return False, str(e)


def obtener_link_guia(nombre_archivo):
    try:
        payload = {
            "token": st.secrets["APPS_SCRIPT_TOKEN"],
            "accion": "obtener_link_guia",
            "nombre_archivo": nombre_archivo,
        }
        resp = requests.post(st.secrets["APPS_SCRIPT_URL"], json=payload, timeout=15)
        data = resp.json()
        if data.get("success"):
            return True, data.get("url", "")
        return False, data.get("error", "Error desconocido")
    except Exception as e:
        return False, str(e)


def nombre_visible(nombre_archivo):
    """Quita la extensión .pdf para mostrarlo más limpio."""
    return nombre_archivo.rsplit(".", 1)[0] if "." in nombre_archivo else nombre_archivo


# ==========================================
# CÓDIGO DEL MÓDULO
# ==========================================
st.markdown(
    '<div class="main-title" style="text-align: left;">ALEMA TRADING'
    " ACADEMY</div>",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title" style="text-align: left;">Biblioteca Digital'
    " Exclusiva para Alumnos y Suscriptores</div>",
    unsafe_allow_html=True,
)

usuario_actual_biblioteca = st.session_state.get("nombre_usuario", "")
es_admin_biblioteca = st.session_state.get("tipo_usuario", "").upper() == "ADMIN"

# =============================================================
# SECCIÓN 1: MATERIAL DE APOYO EN CLASE (gratuito)
# =============================================================
st.subheader("📖 Material de Apoyo en Clase")
st.info(
    "Próximamente encontrarás aquí material de apoyo gratuito para"
    " complementar tus clases."
)

st.divider()

# =============================================================
# SECCIÓN 2: MATERIAL EXCLUSIVO (de pago, por paquete)
# =============================================================
st.subheader("🔒 Material Exclusivo")
st.caption(
    "Guías y paquetes premium — desbloqueados individualmente por Dirección"
    " tras confirmar tu pago."
)

paquetes = cargar_paquetes_exclusivos()

if es_admin_biblioteca:
    matricula_vista_admin = None
    with st.expander("👑 Vista de administrador: consultar como un alumno"):
        lista_mat_bib = cargar_lista_matriculas_biblioteca()
        opciones_mat_bib = ["-- Ver todo desbloqueado (vista admin) --"] + lista_mat_bib
        seleccion_mat_bib = st.selectbox(
            "Consultar biblioteca como:", opciones_mat_bib, key="select_ver_como_bib"
        )
        if seleccion_mat_bib != "-- Ver todo desbloqueado (vista admin) --":
            matricula_vista_admin = seleccion_mat_bib

    if matricula_vista_admin:
        guias_desbloqueadas_usuario = cargar_guias_desbloqueadas(matricula_vista_admin)
    else:
        guias_desbloqueadas_usuario = list(paquetes.keys())
else:
    guias_desbloqueadas_usuario = cargar_guias_desbloqueadas(usuario_actual_biblioteca)

for nombre_paquete, info_paquete in paquetes.items():
    archivos_paquete = info_paquete["archivos"]
    precio_paquete = info_paquete["precio"]
    desbloqueado = nombre_paquete in guias_desbloqueadas_usuario

    with st.container():
        st.markdown(
            estilos.tarjeta(
                nombre_paquete.upper(),
                f"${precio_paquete} MXN" if precio_paquete else "Próximamente",
            ),
            unsafe_allow_html=True,
        )

        if not archivos_paquete:
            st.caption("📦 Este paquete aún no tiene guías cargadas.")
        elif desbloqueado:
            st.success(f"✅ Ya tienes acceso a **{nombre_paquete}**")
            for archivo in archivos_paquete:
                col_g1, col_g2 = st.columns([3, 1])
                with col_g1:
                    st.markdown(f"📄 {nombre_visible(archivo)}")
                with col_g2:
                    if st.button(
                        "📖 Abrir",
                        key=f"btn_abrir_{nombre_paquete}_{archivo}",
                        use_container_width=True,
                    ):
                        exito_link, resultado_link = obtener_link_guia(archivo)
                        if exito_link:
                            st.link_button(
                                "🔗 Abrir en nueva pestaña",
                                resultado_link,
                                key=f"link_abrir_{nombre_paquete}_{archivo}",
                            )
                        else:
                            st.error(f"⚠️ {resultado_link}")
        else:
            st.warning(f"🔒 Bloqueado — {len(archivos_paquete)} guía(s) en este paquete")
            mensaje_wa = (
                f"¡Hola! 👋 Me interesa comprar el {nombre_paquete} de ALEMA"
                f" Trading Academy (${precio_paquete} MXN). ¿Me pueden ayudar"
                " con el proceso de pago?"
            )
            url_wa_paquete = (
                f"https://wa.me/{NUMERO_WHATSAPP_VENTAS}"
                f"?text={requests.utils.quote(mensaje_wa)}"
            )
            st.link_button(
                f"💳 Comprar ({('$' + precio_paquete + ' MXN') if precio_paquete else 'Consultar precio'})",
                url_wa_paquete,
                key=f"btn_comprar_{nombre_paquete}",
            )

        st.markdown("---")

# =============================================================
# PANEL DE ADMIN: DESBLOQUEAR PAQUETES POR ALUMNO
# =============================================================
if es_admin_biblioteca:
    st.divider()
    st.subheader("🔓 Desbloquear Material Exclusivo")

    lista_mat_desbloqueo = cargar_lista_matriculas_biblioteca()
    opciones_desbloqueo = ["-- Selecciona una matrícula --"] + lista_mat_desbloqueo
    seleccion_desbloqueo = st.selectbox(
        "Matrícula del Alumno:", opciones_desbloqueo, key="select_mat_desbloqueo_guias"
    )

    if seleccion_desbloqueo != "-- Selecciona una matrícula --":
        guias_actuales_alumno = cargar_guias_desbloqueadas(seleccion_desbloqueo)

        with st.form(f"form_desbloqueo_guias_{seleccion_desbloqueo}"):
            nuevos_paquetes_desbloqueados = []
            for nombre_paquete in paquetes.keys():
                marcado = st.checkbox(
                    f"🔓 Desbloquear: {nombre_paquete}",
                    value=(nombre_paquete in guias_actuales_alumno),
                    key=f"chk_guia_{seleccion_desbloqueo}_{nombre_paquete}",
                )
                if marcado:
                    nuevos_paquetes_desbloqueados.append(nombre_paquete)

            if st.form_submit_button("💾 Guardar Desbloqueos", use_container_width=True):
                exito_gd, error_gd = actualizar_guias_desbloqueadas_sheet(
                    seleccion_desbloqueo, ",".join(nuevos_paquetes_desbloqueados)
                )
                if exito_gd:
                    st.cache_data.clear()
                    st.toast(
                        f"✅ Material actualizado para {seleccion_desbloqueo}.",
                        icon="✅",
                    )
                    st.rerun()
                else:
                    st.error(f"⚠️ No se pudo guardar: {error_gd}")
