import pandas as pd
import requests
import streamlit as st

import estilos

# URL de exportación a CSV de tu hoja de Google Sheets (GID: 2037302400)
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA/export?format=csv&gid=2037302400"


def actualizar_nota_larga_sheet(matricula, nota_larga):
    """Guarda la nota/horario extendido de un alumno en la hoja Avances vía Apps Script."""
    try:
        payload = {
            "token": st.secrets["APPS_SCRIPT_TOKEN"],
            "accion": "actualizar_nota_larga",
            "matricula": matricula,
            "nota_larga": nota_larga,
        }
        resp = requests.post(st.secrets["APPS_SCRIPT_URL"], json=payload, timeout=15)
        data = resp.json()
        return data.get("success", False), data.get("error", "")
    except Exception as e:
        return False, str(e)


@st.cache_data(ttl=30)
def cargar_datos_estudiantes():
    """Conecta con Google Sheets y descarga los registros actualizados."""
    try:
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        df.columns = (
            df.columns.str.strip()
        )  # Limpia espacios extra en los nombres de columnas
        return df
    except Exception as e:
        st.error(
            "Error de conexión con la base de datos de Google Sheets:"
            f" {e}"
        )
        return pd.DataFrame()


st.markdown('<div class="main-title">📈 Mi Avance Académico</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Consulta el estado de tu matrícula, mantenimiento de'
    " beca y progreso en tiempo real.</div>",
    unsafe_allow_html=True,
)
st.divider()

df = cargar_datos_estudiantes()

if df.empty:
    st.warning(
        "No se pudo obtener información de la base de datos en este"
        " momento."
    )
else:
    usuario_sesion = st.session_state.get("nombre_usuario", "")

    # Buscar al estudiante por coincidencia de Matrícula o Nombre con el usuario en sesión
    estudiante_df = df[
        (df["Matricula"].astype(str).str.upper() == str(usuario_sesion).upper())
        | (
            df["Nombre"]
            .astype(str)
            .str.contains(str(usuario_sesion), case=False, na=False)
        )
    ]

    # Si es Administrador/Director o no encuentra coincidencia directa, permite seleccionar alumno
    if estudiante_df.empty:
        st.info("ℹ️ Selecciona la matrícula o alumno para consultar los datos:")
        matricula_sel = st.selectbox(
            "Buscar por Matrícula / Alumno:", df["Matricula"].unique()
        )
        estudiante_row = df[df["Matricula"] == matricula_sel].iloc[0]
    else:
        estudiante_row = estudiante_df.iloc[0]

    # Datos extraídos dinámicamente del Excel
    matricula = estudiante_row.get("Matricula", "N/A")
    nombre = estudiante_row.get("Nombre", "N/A")
    modulo_actual = estudiante_row.get("Modulo_Actual", "N/A")
    porcentaje = estudiante_row.get("Porcentaje", "0%")
    estatus_beca = estudiante_row.get("Estatus_Beca", "N/A")
    notas = estudiante_row.get("Notas", "Sin observaciones registradas.")
    nota_larga_actual = estudiante_row.get("Notas_Extendidas", "")
    if pd.isna(nota_larga_actual):
        nota_larga_actual = ""

    st.subheader(f"Alumno: {nombre}")

    # 1. Tarjetas con datos reales desde Google Sheets (nuevo estilo unificado .app-card)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            estilos.tarjeta("🎓 Matrícula", str(matricula)),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            estilos.tarjeta("⭐ Estatus de Beca", str(estatus_beca)),
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            estilos.tarjeta("📊 Progreso General", str(porcentaje)),
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            estilos.tarjeta("📚 Módulo Actual", str(modulo_actual)),
            unsafe_allow_html=True,
        )

    st.info(f"📝 **Notas y Próximas Evaluaciones:** {notas}")

    es_admin_avance = st.session_state.get("tipo_usuario", "").upper() == "ADMIN"

    st.markdown("#### 🗒️ Notas y Horario Personalizado")
    if es_admin_avance:
        nueva_nota_larga = st.text_area(
            "Edita las notas/horario extendido de este alumno:",
            value=str(nota_larga_actual),
            height=160,
            key=f"nota_larga_{matricula}",
        )
        if st.button("💾 Guardar Notas y Horario", key=f"btn_guardar_nota_{matricula}"):
            exito_nota, error_nota = actualizar_nota_larga_sheet(matricula, nueva_nota_larga)
            if exito_nota:
                st.cache_data.clear()
                st.toast("✅ Notas y horario actualizados.", icon="✅")
                st.rerun()
            else:
                st.error(f"⚠️ No se pudo guardar: {error_nota}")
    else:
        if str(nota_larga_actual).strip():
            st.markdown(nota_larga_actual)
        else:
            st.caption("Aún no hay notas u horario personalizado registrado.")

    st.divider()

    # 2. Pestañas de soporte
    tab_reglamento, tab_horario = st.tabs([
        "📜 Términos & Mantenimiento de Beca",
        "📅 Horario de Clases",
    ])

    with tab_reglamento:
        st.markdown("""
            * **Asistencia a Clases:** Asistir al menos al 80% de las másterclass en vivo o revisar grabaciones en un plazo no mayor a 72 horas.
            * **Calificación Mínima:** Mantener un promedio ponderado igual o superior a **8.5 / 10** en las evaluaciones.
            * **Cumplimiento de Trading Journal:** Entregar semanalmente la bitácora de riesgo y análisis técnico revisada por coordinación.
            * **Puntualidad de Matrícula:** Mantener al día la cuota de mantenimiento de plataforma.
            """)

    with tab_horario:
        horario_data = {
            "Día": ["Lunes", "Miércoles", "Jueves", "Viernes"],
            "Horario (CDMX)": [
                "20:00 - 21:30",
                "20:00 - 21:30",
                "20:00 - 21:30",
                "19:00 - 20:30",
            ],
            "Sesión / Materia": [
                "Estructura de Mercado & Wyckoff",
                "Gestión de Riesgo & Lotaje Práctico",
                "Másterclass de Puntos Pivote & Fibonacci",
                "Revisión de Bitácora & Q&A",
            ],
            "Instructor": [
                "Alex Marroquín",
                "Alex Marroquín",
                "Alex Marroquín",
                "Coordinación Académica",
            ],
        }
        st.table(horario_data)
