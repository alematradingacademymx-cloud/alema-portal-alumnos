from datetime import datetime
import base64
import io
import json
import os
import pandas as pd
import requests
import streamlit as st

# Módulos oficiales de la academia
LISTA_MODULOS = [
    "Básico",
    "Básico Intermedio",
    "Intermedio",
    "Intermedio Avanzado",
    "Avanzado",
    "Práctico",
]

# Carpeta local (solo para subida general de Excel, no crítica de migrar)
FOLDER_EXCEL_UPLOADS = "archivos_excel_evaluaciones"

SHEET_ID_USUARIOS = "1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA"
URL_USUARIOS_CSV = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID_USUARIOS}/export?format=csv&gid=0"
)
URL_ARCHIVOS_ALUMNOS_CSV = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID_USUARIOS}/gviz/tq?tqx=out:csv&sheet=Archivos_Alumnos"
)
URL_BANCO_EXAMENES_CSV = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID_USUARIOS}/gviz/tq?tqx=out:csv&sheet=Banco_Examenes"
)
URL_RESPUESTAS_CSV = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID_USUARIOS}/gviz/tq?tqx=out:csv&sheet=Respuestas_Examenes"
)


@st.cache_data(ttl=10)
def cargar_banco_examenes():
    """Lee la pestaña Banco_Examenes y arma el diccionario {key_examen: {...}}."""
    banco = {}
    try:
        df = pd.read_csv(URL_BANCO_EXAMENES_CSV, dtype=str)
        df.columns = df.columns.str.strip()
        for _, row in df.iterrows():
            key_examen = str(row.get("Key_Examen", "")).strip()
            if not key_examen or key_examen.lower() == "nan":
                continue
            try:
                preguntas = json.loads(row.get("Preguntas_JSON", "[]") or "[]")
            except Exception:
                preguntas = []
            banco[key_examen] = {
                "titulo": row.get("Titulo", ""),
                "descripcion": row.get("Descripcion", ""),
                "preguntas": preguntas,
            }
    except Exception:
        pass
    return banco


def guardar_examen_sheet(key_examen, titulo, descripcion, preguntas):
    """Crea o actualiza un examen en la pestaña Banco_Examenes vía Apps Script."""
    try:
        payload = {
            "token": st.secrets["APPS_SCRIPT_TOKEN"],
            "accion": "guardar_examen",
            "key_examen": key_examen,
            "titulo": titulo,
            "descripcion": descripcion,
            "preguntas_json": json.dumps(preguntas, ensure_ascii=False),
        }
        resp = requests.post(st.secrets["APPS_SCRIPT_URL"], json=payload, timeout=15)
        data = resp.json()
        return data.get("success", False), data.get("error", "")
    except Exception as e:
        return False, str(e)


def _limpiar_valor(val):
    """Convierte NaN de pandas (celdas vacías) en cadena vacía real."""
    try:
        if val is None or pd.isna(val):
            return ""
    except (TypeError, ValueError):
        pass
    return str(val).strip()


@st.cache_data(ttl=10)
def cargar_respuestas_examenes():
    """Lee la pestaña Respuestas_Examenes y arma la lista de respuestas."""
    respuestas = []
    try:
        df = pd.read_csv(URL_RESPUESTAS_CSV, dtype=str)
        df.columns = df.columns.str.strip()
        for _, row in df.iterrows():
            id_val = _limpiar_valor(row.get("ID", ""))
            if not id_val:
                continue
            try:
                respuestas_dict = json.loads(
                    _limpiar_valor(row.get("Respuestas_JSON", "")) or "{}"
                )
            except Exception:
                respuestas_dict = {}
            try:
                calificacion_val = float(_limpiar_valor(row.get("Calificacion", "0")) or 0)
            except Exception:
                calificacion_val = 0.0
            respuestas.append({
                "id": id_val,
                "matricula": _limpiar_valor(row.get("Matricula", "")),
                "key_examen": _limpiar_valor(row.get("Key_Examen", "")),
                "modulo": _limpiar_valor(row.get("Modulo", "")),
                "fecha": _limpiar_valor(row.get("Fecha", "")),
                "calificacion": calificacion_val,
                "evidencia_tv": _limpiar_valor(row.get("Evidencia_TV", "")),
                "justificacion": _limpiar_valor(row.get("Justificacion", "")),
                "respuestas": respuestas_dict,
                "estatus": _limpiar_valor(row.get("Estatus", "")),
                "observaciones_director": _limpiar_valor(row.get("Observaciones_Director", "")),
                "archivo_certificados": _limpiar_valor(row.get("Archivo_Certificados", "")),
            })
    except Exception:
        pass
    return respuestas


def guardar_respuesta_sheet(respuesta_dict):
    """Agrega una nueva respuesta de examen en la pestaña Respuestas_Examenes vía Apps Script."""
    try:
        payload = {
            "token": st.secrets["APPS_SCRIPT_TOKEN"],
            "accion": "guardar_respuesta",
            "id": respuesta_dict["id"],
            "matricula": respuesta_dict["matricula"],
            "key_examen": respuesta_dict["key_examen"],
            "modulo": respuesta_dict["modulo"],
            "fecha": respuesta_dict["fecha"],
            "calificacion": respuesta_dict["calificacion"],
            "evidencia_tv": respuesta_dict.get("evidencia_tv", ""),
            "justificacion": respuesta_dict.get("justificacion", ""),
            "respuestas_json": json.dumps(
                respuesta_dict.get("respuestas", {}), ensure_ascii=False
            ),
        }
        resp = requests.post(st.secrets["APPS_SCRIPT_URL"], json=payload, timeout=15)
        data = resp.json()
        return data.get("success", False), data.get("error", "")
    except Exception as e:
        return False, str(e)


def actualizar_dictamen_sheet(id_respuesta, estatus, observaciones, archivo_certificados):
    """Actualiza estatus/observaciones/certificado de una respuesta ya existente."""
    try:
        payload = {
            "token": st.secrets["APPS_SCRIPT_TOKEN"],
            "accion": "actualizar_dictamen",
            "id": id_respuesta,
            "estatus": estatus,
            "observaciones_director": observaciones,
            "archivo_certificados": archivo_certificados or "",
        }
        resp = requests.post(st.secrets["APPS_SCRIPT_URL"], json=payload, timeout=15)
        data = resp.json()
        return data.get("success", False), data.get("error", "")
    except Exception as e:
        return False, str(e)


def subir_archivo_drive(matricula, nombre_archivo, contenido_bytes, tipo_mime, categoria="Documento"):
    """Sube un archivo a Drive (vía Apps Script) y registra la referencia en Sheets."""
    try:
        contenido_b64 = base64.b64encode(contenido_bytes).decode("utf-8")
        payload = {
            "token": st.secrets["APPS_SCRIPT_TOKEN"],
            "accion": "subir_archivo",
            "matricula": matricula,
            "nombre_archivo": nombre_archivo,
            "tipo_mime": tipo_mime,
            "categoria": categoria,
            "archivo_base64": contenido_b64,
        }
        resp = requests.post(st.secrets["APPS_SCRIPT_URL"], json=payload, timeout=30)
        data = resp.json()
        if data.get("success"):
            return True, construir_url_descarga(data.get("file_id", "")), None
        return False, None, data.get("error", "Error desconocido")
    except Exception as e:
        return False, None, str(e)


def construir_url_descarga(file_id):
    """Link que descarga el archivo vía el propio Apps Script, sin depender del sharing de Drive."""
    if not file_id:
        return None
    return f"{st.secrets['APPS_SCRIPT_URL']}?file_id={file_id}"


@st.cache_data(ttl=10)
def cargar_archivos_alumno(matricula_target):
    """Lee la pestaña Archivos_Alumnos y filtra por matrícula."""
    try:
        df = pd.read_csv(URL_ARCHIVOS_ALUMNOS_CSV, dtype=str)
        df.columns = df.columns.str.strip()
        filtro = df[
            df["Matricula"].astype(str).str.strip().str.upper()
            == str(matricula_target).strip().upper()
        ]
        return filtro.to_dict("records")
    except Exception:
        return []


# --- PERMISOS (CANDADOS): LECTURA DESDE GOOGLE SHEETS ---
@st.cache_data(ttl=10)
def cargar_permisos_sheet(matricula_target):
    """Lee Modulos_Habilitados y Simulador_Habilitado de la pestaña Usuarios."""
    modulos_desbloqueados = []
    simulador_habilitado = False
    try:
        df = pd.read_csv(URL_USUARIOS_CSV)
        df.columns = df.columns.str.strip()

        filtro = df[
            df["Matricula"].astype(str).str.strip().str.upper()
            == str(matricula_target).strip().upper()
        ]
        if not filtro.empty:
            val_mod = str(filtro["Modulos_Habilitados"].values[0]).strip()
            if val_mod and val_mod.lower() != "nan":
                if val_mod == "Completo":
                    modulos_desbloqueados = LISTA_MODULOS.copy()
                else:
                    modulos_desbloqueados = [
                        m.strip() for m in val_mod.split(",") if m.strip()
                    ]

            val_sim = str(filtro["Simulador_Habilitado"].values[0]).strip().upper()
            simulador_habilitado = val_sim == "SI"
    except Exception:
        pass

    if not modulos_desbloqueados:
        modulos_desbloqueados = ["Básico"]

    return modulos_desbloqueados, simulador_habilitado


def actualizar_permisos_sheet(matricula, modulos_habilitados_str, simulador_habilitado_bool):
    """Envía la actualización de permisos al Apps Script (Web App) conectado al Sheet."""
    try:
        payload = {
            "token": st.secrets["APPS_SCRIPT_TOKEN"],
            "matricula": matricula,
            "modulos_habilitados": modulos_habilitados_str,
            "simulador_habilitado": "SI" if simulador_habilitado_bool else "NO",
        }
        resp = requests.post(st.secrets["APPS_SCRIPT_URL"], json=payload, timeout=10)
        data = resp.json()
        return data.get("success", False), data.get("error", "")
    except Exception as e:
        return False, str(e)


# ==========================================
# CÓDIGO DEL MÓDULO RENDERIZADO DIRECTO
# ==========================================
st.markdown(
    '<div class="main-title" style="text-align: left;">ALEMA TRADING'
    ' ACADEMY</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title" style="text-align: left;">Sistema Progresivo de'
    " Evaluaciones y Certificaciones Oficiales</div>",
    unsafe_allow_html=True,
)

usuario_actual = st.session_state.get("nombre_usuario", "DIRALEX")
es_admin = (
    st.session_state.get("tipo_usuario", "").upper() == "ADMIN"
    or usuario_actual.upper() == "DIRALEX"
)

# Crear carpetas si no existen
if not os.path.exists(FOLDER_EXCEL_UPLOADS):
    os.makedirs(FOLDER_EXCEL_UPLOADS)

banco_examenes = cargar_banco_examenes()
respuestas_evals = cargar_respuestas_examenes()

# --- PESTAÑAS DE NAVEGACIÓN AISLADAS SEGÚN ROL ---
if es_admin:
    (
        tab_alumnos,
        tab_historial,
        tab_crear,
        tab_permisos,
        tab_coordinacion,
        tab_archivos,
    ) = st.tabs([
        "📚 Ruta Académica",
        "📊 Mis Resultados",
        "➕ Cargar Exámenes (ADMIN)",
        "🔓 Gestor Candados (ADMIN)",
        "👑 Revisión / Dictamen (ADMIN)",
        "📁 Archivos y Excel (ADMIN)",
    ])
else:
    tab_alumnos, tab_historial = st.tabs(
        ["📚 Ruta Académica", "📊 Mis Resultados y Certificados"]
    )

# =============================================================
# PESTAÑA 1: RUTA ACADÉMICA Y PRESENTACIÓN DE EXÁMENES
# =============================================================
with tab_alumnos:
    st.subheader("🗺️ Ruta Institucional de Aprendizaje")
    st.caption(
        "Selecciona tu módulo actual para presentar tus exámenes"
        " programados."
    )

    modulos_desbloqueados, _ = cargar_permisos_sheet(usuario_actual)

    for modulo in LISTA_MODULOS:
        esta_desbloqueado = modulo in modulos_desbloqueados
        icono_modulo = "🔓" if esta_desbloqueado else "🔒"

        with st.expander(
            f"{icono_modulo} Módulo: {modulo}", expanded=esta_desbloqueado
        ):
            if not esta_desbloqueado:
                st.warning(
                    "🔒 **Módulo Bloqueado.** Este nivel se activará cuando"
                    " Dirección apruebe tu avance."
                )
            else:
                st.markdown(f"#### Exámenes Disponibles - Nivel {modulo}")

                for num_ex in range(1, 4):
                    key_examen = f"{modulo}_Examen_{num_ex}"
                    examen_datos = banco_examenes.get(key_examen, None)

                    col_e1, col_e2 = st.columns([3, 1])
                    with col_e1:
                        st.markdown(
                            f"**📝 Examen {num_ex}:**"
                            f" {examen_datos['titulo'] if examen_datos else 'Sin examen cargado aún'}"
                        )
                    with col_e2:
                        if not examen_datos:
                            st.caption("⏳ En preparación")
                        else:
                            ya_presento = any(
                                r
                                for r in respuestas_evals
                                if r["matricula"].upper() == usuario_actual.upper()
                                and r["key_examen"] == key_examen
                            )
                            if ya_presento:
                                st.success("✅ Presentado")
                            else:
                                if st.button(
                                    f"Presentar Examen {num_ex}",
                                    key=f"btn_pres_{key_examen}",
                                ):
                                    st.session_state[f"modo_examen_{key_examen}"] = True

                    # Despliegue aislado del formulario del examen
                    if (
                        st.session_state.get(f"modo_examen_{key_examen}", False)
                        and examen_datos
                    ):
                        with st.form(f"form_responder_{key_examen}"):
                            st.info(f"### {examen_datos['titulo']}")
                            st.write(examen_datos["descripcion"])
                            st.caption(f"Total de preguntas: {len(examen_datos['preguntas'])}")
                            st.divider()

                            respuestas_alumno = {}
                            for idx_q, q in enumerate(examen_datos["preguntas"]):
                                st.markdown(f"**Pregunta {idx_q+1}:** {q['pregunta']}")
                                respuestas_alumno[f"p_{idx_q}"] = st.radio(
                                    f"Selecciona tu respuesta ({idx_q+1}):",
                                    q["opciones"],
                                    key=f"radio_{key_examen}_{idx_q}",
                                )
                                st.markdown("---")

                            link_tv = st.text_input(
                                "Enlace de Evidencia en TradingView:",
                                placeholder="https://www.tradingview.com/x/...",
                            )
                            justificacion = st.text_area(
                                "Justificación Técnica de tu Análisis:",
                                placeholder="Explica tu confirmación, zona POI y gestión...",
                            )

                            if st.form_submit_button(
                                "💾 Enviar Examen a Dirección",
                                use_container_width=True,
                            ):
                                # Cálculo matemático reconstruido del examen
                                total_preguntas = len(examen_datos["preguntas"])
                                correctas = 0
                                for idx_q, q in enumerate(examen_datos["preguntas"]):
                                    if respuestas_alumno[f"p_{idx_q}"] == q.get("respuesta_correcta"):
                                        correctas += 1
                                
                                calificacion = (correctas / total_preguntas) * 10.0 if total_preguntas > 0 else 0.0
                                
                                nueva_respuesta = {
                                    "id": int(datetime.now().timestamp() * 1000),
                                    "matricula": usuario_actual,
                                    "key_examen": key_examen,
                                    "modulo": modulo,
                                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "calificacion": round(calificacion, 2),
                                    "evidencia_tv": link_tv,
                                    "justificacion": justificacion,
                                    "respuestas": respuestas_alumno
                                }
                                
                                exito_resp, error_resp = guardar_respuesta_sheet(
                                    nueva_respuesta
                                )

                                if exito_resp:
                                    st.cache_data.clear()
                                    st.success(
                                        "🎉 ¡Examen enviado con éxito! Tu"
                                        f" calificación preliminar es: {calificacion:.2f}/10"
                                    )
                                    st.session_state[f"modo_examen_{key_examen}"] = False
                                    st.rerun()
                                else:
                                    st.error(
                                        "⚠️ No se pudo guardar tu examen, intenta"
                                        f" de nuevo: {error_resp}"
                                    )

# =============================================================
# PESTAÑA 2: HISTORIAL Y MUESTRA DE RESULTADOS
# =============================================================
with tab_historial:
    st.subheader("📊 Historial de Calificaciones")
    mis_examenes = [r for r in respuestas_evals if r.get("matricula", "").upper() == usuario_actual.upper()]
    if mis_examenes:
        for examen in mis_examenes:
            with st.expander(
                f"{examen.get('key_examen', 'Examen')} —"
                f" {examen.get('fecha', '')}"
            ):
                st.markdown(f"**Módulo:** {examen.get('modulo', '')}")
                st.markdown(
                    f"**Calificación:** {examen.get('calificacion', 0)} / 10"
                )
                st.markdown(
                    "**Estatus:**"
                    f" {examen.get('estatus') or '⏳ Pendiente de revisión'}"
                )
                if examen.get("observaciones_director"):
                    st.markdown(
                        f"**Observaciones:** {examen['observaciones_director']}"
                    )
                if examen.get("archivo_certificados"):
                    st.markdown(
                        "📜"
                        f" [Descargar tu Reconocimiento Oficial]({examen['archivo_certificados']})"
                    )
    else:
        st.info("💡 Aún no has presentado ninguna evaluación en esta cuenta.")

    # =============================================================
    # PESTAÑAS DE ADMINISTRADOR (DIRALEX)
    # =============================================================
    if es_admin:
        # ---------------------------------------------------------
        # PESTAÑA 3: CREADOR DINÁMICO DE EXÁMENES (ADMIN)
        # ---------------------------------------------------------
        with tab_crear:
            st.subheader("➕ Cargar / Configurar Exámenes Dinámicos")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                mod_target = st.selectbox(
                    "Módulo a Configurar:", LISTA_MODULOS, key="select_mod_target"
                )
            with col_c2:
                num_ex_target = st.selectbox(
                    "Número de Examen:", [1, 2, 3], key="select_num_ex_target"
                )

            key_target = f"{mod_target}_Examen_{num_ex_target}"
            ex_existente = banco_examenes.get(key_target, {})

            titulo_ex = st.text_input(
                "Título del Examen:",
                value=ex_existente.get(
                    "titulo", f"Evaluación {mod_target} #{num_ex_target}"
                ),
                key=f"input_tit_{key_target}",
            )
            desc_ex = st.text_area(
                "Instrucciones:",
                value=ex_existente.get(
                    "descripcion",
                    "Responde las preguntas y adjunta tu enlace de TradingView.",
                ),
                key=f"input_desc_{key_target}",
            )

            st.divider()
            if f"num_preg_state_{key_target}" not in st.session_state:
                st.session_state[f"num_preg_state_{key_target}"] = (
                    len(ex_existente.get("preguntas", []))
                    if ex_existente.get("preguntas")
                    else 3
                )

            col_p_btn1, col_p_btn2, _ = st.columns([1, 1, 2])
            with col_p_btn1:
                if st.button("➕ Agregar Pregunta", key=f"btn_add_p_{key_target}"):
                    st.session_state[f"num_preg_state_{key_target}"] += 1
            with col_p_btn2:
                if (
                    st.button("➖ Quitar Pregunta", key=f"btn_del_p_{key_target}")
                    and st.session_state[f"num_preg_state_{key_target}"] > 1
                ):
                    st.session_state[f"num_preg_state_{key_target}"] -= 1

            total_p = st.session_state[f"num_preg_state_{key_target}"]
            st.info(f"Total de preguntas para este examen: **{total_p}**")

            preguntas_recopiladas = []
            for i in range(total_p):
                st.markdown(f"##### **Pregunta #{i+1}**")
                p_prev = (
                    ex_existente.get("preguntas", [])[i]
                    if i < len(ex_existente.get("preguntas", []))
                    else {}
                )

                txt_p = st.text_input(
                    f"Enunciado Pregunta #{i+1}:",
                    value=p_prev.get("pregunta", ""),
                    key=f"input_p_{key_target}_{i}",
                )

                c_op1, c_op2, c_op3 = st.columns(3)
                opts = p_prev.get("opciones", ["", "", ""])
                with c_op1:
                    op1 = st.text_input(
                        f"Opción A (P{i+1}):",
                        value=opts[0] if len(opts) > 0 else "",
                        key=f"op1_{key_target}_{i}",
                    )
                with c_op2:
                    op2 = st.text_input(
                        f"Opción B (P{i+1}):",
                        value=opts[1] if len(opts) > 1 else "",
                        key=f"op2_{key_target}_{i}",
                    )
                with c_op3:
                    op3 = st.text_input(
                        f"Opción C (P{i+1}):",
                        value=opts[2] if len(opts) > 2 else "",
                        key=f"op3_{key_target}_{i}",
                    )

                opciones_validas = [
                    o for o in [op1, op2, op3] if o.strip() != ""
                ]
                correcta = st.selectbox(
                    f"Respuesta Correcta Pregunta #{i+1}:",
                    (
                        opciones_validas
                        if opciones_validas
                        else ["Define opciones primero"]
                    ),
                    key=f"cor_{key_target}_{i}",
                )

                preguntas_recopiladas.append({
                    "pregunta": txt_p,
                    "opciones": [op1, op2, op3],
                    "respuesta_correcta": correcta,
                })
                st.markdown("---")

            if st.button(
                "💾 Guardar Examen Completo",
                use_container_width=True,
                key=f"btn_save_ex_{key_target}",
            ):
                exito_ex, error_ex = guardar_examen_sheet(
                    key_target, titulo_ex, desc_ex, preguntas_recopiladas
                )
                if exito_ex:
                    st.cache_data.clear()
                    st.toast(f"✅ Examen {key_target} guardado con éxito.", icon="✅")
                    st.rerun()
                else:
                    st.error(f"⚠️ No se pudo guardar el examen: {error_ex}")

        # ---------------------------------------------------------
        # PESTAÑA 4: GESTOR DE CANDADOS (ADMIN) — CONECTADO A GOOGLE SHEETS
        # ---------------------------------------------------------
        with tab_permisos:
            st.subheader("🔓 Gestor de Candados por Alumno")
            st.caption(
                "Los cambios se guardan directo en la base de datos de Google"
                " Sheets — persisten aunque el servidor se reinicie."
            )
            alumno_mat_permiso = (
                st.text_input(
                    "Matrícula del Alumno:",
                    value="",
                    key="input_mat_permisos",
                )
                .strip()
                .upper()
            )

            if alumno_mat_permiso:
                permisos_actuales_alumno, simulador_actual_bool = cargar_permisos_sheet(
                    alumno_mat_permiso
                )
                st.markdown(
                    "#### Configurando Módulos y Herramientas para:"
                    f" `{alumno_mat_permiso}`"
                )

                with st.form(f"form_permisos_{alumno_mat_permiso}"):
                    nuevos_permisos_modulos = []
                    st.markdown("##### **1. Módulos Teóricos Académicos:**")
                    for m in LISTA_MODULOS:
                        check = st.checkbox(
                            f"🔓 Habilitar Módulo: {m}",
                            value=(m in permisos_actuales_alumno),
                            key=f"chk_perm_{alumno_mat_permiso}_{m}",
                        )
                        if check:
                            nuevos_permisos_modulos.append(m)

                    st.markdown("---")
                    st.markdown("##### **2. Herramientas Avanzadas:**")
                    check_sim = st.checkbox(
                        "🚀 Habilitar Acceso al Simulador Institucional",
                        value=simulador_actual_bool,
                        key=f"chk_sim_{alumno_mat_permiso}",
                    )

                    if st.form_submit_button(
                        "💾 Guardar Permisos", use_container_width=True
                    ):
                        exito, error_msg = actualizar_permisos_sheet(
                            alumno_mat_permiso,
                            ",".join(nuevos_permisos_modulos),
                            check_sim,
                        )
                        if exito:
                            st.cache_data.clear()
                            st.toast(
                                f"✅ Permisos actualizados para {alumno_mat_permiso}.",
                                icon="✅",
                            )
                            st.rerun()
                        else:
                            st.error(
                                "⚠️ No se pudo guardar en Google Sheets:"
                                f" {error_msg}"
                            )

        # ---------------------------------------------------------
        # PESTAÑA 5: REVISIÓN, DICTAMEN Y CARGA DE CERTIFICADO (ADMIN)
        # ---------------------------------------------------------
        with tab_coordinacion:
            st.subheader(
                "👑 Panel de Dictamen y Carga de Certificados (DIRALEX)"
            )

            matricula_buscar_dictamen = (
                st.text_input(
                    "🔍 Buscar Alumno por Matrícula:",
                    key="input_buscar_matricula_dictamen",
                )
                .strip()
                .upper()
            )

            if matricula_buscar_dictamen:
                examenes_alumno = [
                    r
                    for r in respuestas_evals
                    if r.get("matricula", "").upper() == matricula_buscar_dictamen
                ]

                if not examenes_alumno:
                    st.info(
                        f"El alumno **{matricula_buscar_dictamen}** no ha"
                        " presentado ningún examen todavía."
                    )
                else:
                    opciones_examen = [
                        f"{r.get('key_examen', 'Examen')} — {r.get('fecha', '')}"
                        for r in examenes_alumno
                    ]
                    sel_idx = st.selectbox(
                        "Selecciona el examen a revisar:",
                        range(len(opciones_examen)),
                        format_func=lambda i: opciones_examen[i],
                        key="select_examen_dictamen",
                    )
                    target_resp = examenes_alumno[sel_idx]
                    id_target = target_resp["id"]

                    st.divider()
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        st.markdown(f"**Alumno:** `{target_resp.get('matricula', '')}`")
                        st.markdown(f"**Módulo:** {target_resp.get('modulo', '')}")
                        st.markdown(f"**Examen:** {target_resp.get('key_examen', '')}")
                        st.markdown(f"**Fecha:** {target_resp.get('fecha', '')}")
                        st.markdown(
                            f"**Calificación:** {target_resp.get('calificacion', 0)} / 10"
                        )
                        if target_resp.get("evidencia_tv"):
                            st.markdown(
                                "🔗"
                                f" [Abrir Gráfico TradingView]({target_resp['evidencia_tv']})"
                            )
                        st.text_area(
                            "Justificación del Alumno:",
                            value=target_resp.get("justificacion", ""),
                            disabled=True,
                            key=f"txt_just_admin_{id_target}",
                        )
                        if target_resp.get("archivo_certificados"):
                            st.markdown(
                                "📜"
                                f" [Ver certificado ya cargado]({target_resp['archivo_certificados']})"
                            )

                    with col_d2:
                        with st.form(f"form_dictamen_admin_{id_target}"):
                            estatus_opciones = [
                                "🟢 Aprobado",
                                "🟡 A revisión en vivo",
                                "🔴 No aprobado / No presentado",
                            ]
                            estatus_actual = target_resp.get("estatus", "")
                            index_estatus = 0
                            if "revisión" in estatus_actual:
                                index_estatus = 1
                            elif "No aprobado" in estatus_actual:
                                index_estatus = 2

                            e_dictamen = st.selectbox(
                                "Asignar Estatus Académico:",
                                estatus_opciones,
                                index=index_estatus,
                                key=f"sel_estatus_admin_{id_target}",
                            )

                            obs_dictamen = st.text_area(
                                "Observaciones del Mentor / Coordinación:",
                                value=target_resp.get("observaciones_director", ""),
                                key=f"txt_obs_admin_{id_target}",
                            )

                            st.markdown("---")
                            st.markdown(
                                "📜 **Adjuntar Reconocimiento Oficial (PDF, PNG,"
                                " JPG) — solo si el estatus es Aprobado:**"
                            )
                            up_cert = st.file_uploader(
                                "Sube el certificado emitido para este alumno:",
                                type=["pdf", "png", "jpg", "jpeg"],
                                key=f"file_cert_admin_{id_target}",
                            )

                            if st.form_submit_button(
                                "💾 Guardar Dictamen y Certificado",
                                use_container_width=True,
                            ):
                                file_cert_name = target_resp.get(
                                    "archivo_certificados", None
                                )
                                error_subida_cert = None

                                if up_cert is not None:
                                    ext_cert = up_cert.name.split(".")[-1]
                                    nombre_cert = (
                                        f"Certificado_{target_resp.get('matricula','')}_{target_resp.get('key_examen','examen')}.{ext_cert}"
                                    )
                                    exito_cert, url_cert, error_cert = subir_archivo_drive(
                                        target_resp.get("matricula", ""),
                                        nombre_cert,
                                        up_cert.getbuffer(),
                                        up_cert.type or "application/octet-stream",
                                        categoria="Certificado",
                                    )
                                    if exito_cert:
                                        file_cert_name = url_cert
                                    else:
                                        error_subida_cert = error_cert

                                if error_subida_cert:
                                    st.error(
                                        "⚠️ No se pudo subir el certificado a"
                                        f" Drive: {error_subida_cert}. El resto"
                                        " del dictamen no se guardó, intenta de"
                                        " nuevo."
                                    )
                                else:
                                    exito_dict, error_dict = actualizar_dictamen_sheet(
                                        id_target,
                                        e_dictamen,
                                        obs_dictamen,
                                        file_cert_name,
                                    )
                                    if exito_dict:
                                        st.cache_data.clear()
                                        st.toast(
                                            "✅ Dictamen y Reconocimiento Oficial"
                                            " guardados exitosamente.",
                                            icon="✅",
                                        )
                                        st.rerun()
                                    else:
                                        st.error(
                                            "⚠️ No se pudo guardar el dictamen:"
                                            f" {error_dict}"
                                        )
            else:
                st.info(
                    "Escribe la matrícula de un alumno arriba para ver y"
                    " calificar sus exámenes presentados."
                )

        # ---------------------------------------------------------
        # PESTAÑA 6: ARCHIVOS Y EXCEL (ADMIN)
        # ---------------------------------------------------------
        with tab_archivos:
            st.subheader("📁 Archivos y Reportes Generales")

            st.markdown("#### **1. Subir Documento a un Alumno Específico**")
            matricula_archivo = (
                st.text_input(
                    "🔍 Matrícula del Alumno:", key="input_matricula_archivo"
                )
                .strip()
                .upper()
            )

            if matricula_archivo:
                archivo_alumno = st.file_uploader(
                    f"Selecciona un archivo para **{matricula_archivo}** (Excel,"
                    " PDF, Word, imagen):",
                    type=["xlsx", "xls", "pdf", "docx", "png", "jpg", "jpeg"],
                    key=f"uploader_archivo_alumno_{matricula_archivo}",
                )
                if archivo_alumno is not None:
                    if st.button(
                        "⬆️ Subir a Drive",
                        key=f"btn_subir_drive_{matricula_archivo}",
                    ):
                        exito_up, url_up, error_up = subir_archivo_drive(
                            matricula_archivo,
                            archivo_alumno.name,
                            archivo_alumno.getbuffer(),
                            archivo_alumno.type or "application/octet-stream",
                            categoria="Documento",
                        )
                        if exito_up:
                            st.cache_data.clear()
                            st.toast(
                                f"✅ Archivo subido para {matricula_archivo}.",
                                icon="✅",
                            )
                            st.rerun()
                        else:
                            st.error(f"⚠️ No se pudo subir el archivo: {error_up}")

                archivos_existentes = cargar_archivos_alumno(matricula_archivo)
                if archivos_existentes:
                    st.caption(f"Archivos actuales de {matricula_archivo}:")
                    for archivo_reg in archivos_existentes:
                        url_desc = construir_url_descarga(
                            archivo_reg.get("File_ID")
                        ) or archivo_reg.get("URL_Drive", "#")
                        st.markdown(
                            f"📄 [{archivo_reg.get('Nombre_Archivo', 'archivo')}]"
                            f"({url_desc}) —"
                            f" _{archivo_reg.get('Categoria', '')}_,"
                            f" {archivo_reg.get('Fecha', '')}"
                        )
            else:
                st.info(
                    "Escribe una matrícula arriba para subir o revisar los"
                    " archivos de ese alumno."
                )

            st.divider()
            st.markdown(
                "#### **2. Subir Archivo General (visible para todos los"
                " alumnos)**"
            )
            uploaded_excel = st.file_uploader(
                "Selecciona un archivo Excel (.xlsx) para ponerlo a disposición"
                " de los alumnos:",
                type=["xlsx", "xls"],
                key="uploader_excel_admin",
            )
            if uploaded_excel is not None:
                save_path = os.path.join(
                    FOLDER_EXCEL_UPLOADS, uploaded_excel.name
                )
                with open(save_path, "wb") as f:
                    f.write(uploaded_excel.getbuffer())
                st.success(
                    f"✅ Archivo **{uploaded_excel.name}** subido"
                    " correctamente."
                )

            st.divider()
            st.markdown("#### **3. Exportar Respuestas de Exámenes a Excel**")
            if respuestas_evals:
                df_exp = pd.DataFrame(respuestas_evals)
                buffer_excel = io.BytesIO()
                with pd.ExcelWriter(
                    buffer_excel, engine="openpyxl"
                ) as writer:
                    df_exp.to_excel(
                        writer, index=False, sheet_name="Evaluaciones"
                    )

                st.download_button(
                    label="📊 Descargar Historial Completo (.xlsx)",
                    data=buffer_excel.getvalue(),
                    file_name=(
                        "Historial_Evaluaciones_ALEMA_"
                        f"{datetime.now().strftime('%Y%m%d')}.xlsx"
                    ),
                    mime=(
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ),
                    use_container_width=True,
                    key="btn_export_excel_admin",
                )

    st.caption("© ALEMA Trading Academy. Reservados todos los derechos.")
