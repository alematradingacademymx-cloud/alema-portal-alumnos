from datetime import datetime
import io
import json
import os
import pandas as pd
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

# Rutas de almacenamiento local
FILE_BANCO_EXAMENES = "bd_banco_examenes.json"
FILE_DESBLOQUEOS = "bd_desbloqueos_alumnos.json"
FILE_RESPUESTAS = "bd_respuestas_evaluaciones.json"
FOLDER_EXCEL_UPLOADS = "archivos_excel_evaluaciones"
FOLDER_CERTIFICADOS = "certificados_oficiales"


# --- FUNCIONES DE PERSISTENCIA JSON ---
def cargar_json_local(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def guardar_json_local(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


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
es_admin = usuario_actual.upper() == "DIRALEX"

# Crear carpetas si no existen
for folder in [FOLDER_EXCEL_UPLOADS, FOLDER_CERTIFICADOS]:
    if not os.path.exists(folder):
        os.makedirs(folder)

banco_examenes = cargar_json_local(FILE_BANCO_EXAMENES, {})
permisos_alumnos = cargar_json_local(FILE_DESBLOQUEOS, {})
respuestas_evals = cargar_json_local(FILE_RESPUESTAS, [])

# Permiso inicial por defecto para alumnos nuevos
if usuario_actual not in permisos_alumnos:
    permisos_alumnos[usuario_actual] = ["Básico"]
    guardar_json_local(FILE_DESBLOQUEOS, permisos_alumnos)

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

    modulos_desbloqueados = permisos_alumnos.get(
        usuario_actual, ["Básico"]
    )

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
                                    "matricula": usuario_actual,
                                    "key_examen": key_examen,
                                    "modulo": modulo,
                                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "calificacion": round(calificacion, 2),
                                    "evidencia_tv": link_tv,
                                    "justificacion": justificacion,
                                    "respuestas": respuestas_alumno
                                }
                                
                                respuestas_evals.append(nueva_respuesta)
                                guardar_json_local(FILE_RESPUESTAS, respuestas_evals)
                                
                                st.success(f"🎉 ¡Examen enviado con éxito! Tu calificación preliminar es: {calificacion:.2f}/10")
                                st.session_state[f"modo_examen_{key_examen}"] = False
                                st.rerun()

# =============================================================
# PESTAÑA 2: HISTORIAL Y MUESTRA DE RESULTADOS
# =============================================================
with tab_historial:
    st.subheader("📊 Historial de Calificaciones")
    mis_examenes = [r for r in respuestas_evals if r["matricula"].upper() == usuario_actual.upper()]
    if mis_examenes:
        df_historial = pd.DataFrame(mis_examenes)
        st.dataframe(df_historial[["fecha", "modulo", "key_examen", "calificacion"]], use_container_width=True)
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
                    "correcta": correcta,
                })
                st.markdown("---")

            if st.button(
                "💾 Guardar Examen Completo",
                use_container_width=True,
                key=f"btn_save_ex_{key_target}",
            ):
                banco_examenes[key_target] = {
                    "titulo": titulo_ex,
                    "descripcion": desc_ex,
                    "preguntas": preguntas_recopiladas,
                }
                guardar_json_local(FILE_BANCO_EXAMENES, banco_examenes)
                st.success(f"✅ Examen **{key_target}** guardado con éxito.")
                st.rerun()

        # ---------------------------------------------------------
        # PESTAÑA 4: GESTOR DE CANDADOS (ADMIN)
        # ---------------------------------------------------------
        with tab_permisos:
            st.subheader("🔓 Gestor de Candados por Alumno")
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
                permisos_actuales_alumno = permisos_alumnos.get(
                    alumno_mat_permiso, ["Básico"]
                )
                st.markdown(
                    "#### Configurando Módulos y Herramientas para:"
                    f" `{alumno_mat_permiso}`"
                )

                with st.form(f"form_permisos_{alumno_mat_permiso}"):
                    nuevos_permisos = []
                    st.markdown("##### **1. Módulos Teóricos Académicos:**")
                    for m in LISTA_MODULOS:
                        check = st.checkbox(
                            f"🔓 Habilitar Módulo: {m}",
                            value=(m in permisos_actuales_alumno),
                            key=f"chk_perm_{alumno_mat_permiso}_{m}",
                        )
                        if check:
                            nuevos_permisos.append(m)

                    st.markdown("---")
                    st.markdown("##### **2. Herramientas Avanzadas:**")
                    check_sim = st.checkbox(
                        "🚀 Habilitar Acceso al Simulador Institucional",
                        value=(
                            "Simulador Institucional"
                            in permisos_actuales_alumno
                        ),
                        key=f"chk_sim_{alumno_mat_permiso}",
                    )
                    if check_sim:
                        nuevos_permisos.append("Simulador Institucional")

                    if st.form_submit_button(
                        "💾 Guardar Permisos", use_container_width=True
                    ):
                        permisos_alumnos[alumno_mat_permiso] = nuevos_permisos
                        guardar_json_local(
                            FILE_DESBLOQUEOS, permisos_alumnos
                        )
                        st.success(
                            "✅ Permisos actualizados para"
                            f" **{alumno_mat_permiso}**."
                        )
                        st.rerun()

        # ---------------------------------------------------------
        # PESTAÑA 5: REVISIÓN, DICTAMEN Y CARGA DE CERTIFICADO (ADMIN)
        # ---------------------------------------------------------
        with tab_coordinacion:
            st.subheader(
                "👑 Panel de Dictamen y Carga de Certificados (DIRALEX)"
            )

            if respuestas_evals:
                lista_pendientes = [
                    f"ID: {r['id']} | Alumno: {r['matricula']} | Examen:"
                    f" {r['key_examen']}"
                    for r in respuestas_evals
                ]
                sel_dictamen = st.selectbox(
                    "Selecciona Evaluación a Revisar:",
                    lista_pendientes,
                    key="select_eval_dictamen",
                )

                id_target = int(
                    sel_dictamen.split("|")[0].replace("ID:", "").strip()
                )
                target_resp = next(
                    (r for r in respuestas_evals if r["id"] == id_target), None
                )

                if target_resp:
                    st.divider()
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        st.markdown(
                            f"**Alumno:** `{target_resp['matricula']}`"
                        )
                        st.markdown(f"**Examen:** {target_resp['titulo']}")
                        st.markdown(f"**Fecha:** {target_resp['fecha']}")
                        st.markdown(
                            "**Puntaje Teórico:**"
                            f" {target_resp['score_teorico']} pts"
                        )
                        if target_resp["link_tv"]:
                            st.markdown(
                                f"🔗 [Abrir Gráfico TradingView]({target_resp['link_tv']})"
                            )
                        st.text_area(
                            "Justificación del Alumno:",
                            value=target_resp["justificacion"],
                            disabled=True,
                            key=f"txt_just_admin_{id_target}",
                        )

                    with col_d2:
                        with st.form(f"form_dictamen_admin_{id_target}"):
                            e_dictamen = st.selectbox(
                                "Asignar Estatus Académico:",
                                [
                                    "🟢 Aprobado",
                                    "🟡 A revisión en vivo",
                                    "🔴 No aprobado / No presentado",
                                ],
                                index=(
                                    0
                                    if "Aprobado" in target_resp["estatus"]
                                    else (
                                        1
                                        if "revisión"
                                        in target_resp["estatus"]
                                        else 2
                                    )
                                ),
                                key=f"sel_estatus_admin_{id_target}",
                            )

                            obs_dictamen = st.text_area(
                                "Observaciones del Mentor / Coordinación:",
                                value=target_resp["observaciones_director"],
                                key=f"txt_obs_admin_{id_target}",
                            )

                            st.markdown("---")
                            st.markdown(
                                "📜 **Adjuntar Reconocimiento Oficial (PDF, PNG,"
                                " JPG):**"
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

                                if up_cert is not None:
                                    ext_cert = up_cert.name.split(".")[-1]
                                    file_cert_name = (
                                        f"Certificado_{target_resp['matricula']}_{target_resp['key_examen']}.{ext_cert}"
                                    )
                                    path_save_cert = os.path.join(
                                        FOLDER_CERTIFICADOS, file_cert_name
                                    )
                                    with open(path_save_cert, "wb") as f_out:
                                        f_out.write(up_cert.getbuffer())

                                for idx, r in enumerate(respuestas_evals):
                                    if r["id"] == id_target:
                                        respuestas_evals[idx]["estatus"] = (
                                            e_dictamen
                                        )
                                        respuestas_evals[idx][
                                            "observaciones_director"
                                        ] = obs_dictamen
                                        respuestas_evals[idx][
                                            "archivo_certificados"
                                        ] = file_cert_name
                                        break

                                guardar_json_local(
                                    FILE_RESPUESTAS, respuestas_evals
                                )
                                st.success(
                                    "✅ Dictamen y Reconocimiento Oficial"
                                    " guardados exitosamente."
                                )
                                st.rerun()
            else:
                st.info("💡 No hay evaluaciones pendientes registradas.")

        # ---------------------------------------------------------
        # PESTAÑA 6: ARCHIVOS Y EXCEL (ADMIN)
        # ---------------------------------------------------------
        with tab_archivos:
            st.subheader("📁 Archivos y Reportes Generales")

            st.markdown(
                "#### **1. Subir Archivo Excel / Hoja de Retroalimentación**"
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
            st.markdown("#### **2. Exportar Respuestas de Exámenes a Excel**")
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
