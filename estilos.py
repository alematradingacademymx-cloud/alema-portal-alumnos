import base64

import streamlit as st


def inyectar_estilos():
    """Inyecta una sola vez el sistema de diseño global de ALEMA Trading Academy."""
    st.markdown(
        """
        <style>
        /* ============================================
           TIPOGRAFÍA MODERNA (Inter, vía Google Fonts)
           ============================================ */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"], .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        /* ============================================
           OCULTAR SOLO BOTONES DE STREAMLIT CLOUD
           (Share/⭐/✏️/GitHub/menú) SIN TAPAR EL
           CONTROL DE ABRIR/CERRAR EL SIDEBAR
           ============================================ */
        [data-testid="stToolbarActions"],
        [data-testid="stToolbar"] button,
        #MainMenu,
        footer,
        .stAppDeployButton {
            display: none !important;
        }
        header[data-testid="stHeader"] {
            background: transparent !important;
            box-shadow: none !important;
        }

        /* Logo del sidebar (st.logo) centrado horizontalmente */
        [data-testid="stLogo"] {
            display: block;
            margin: 0 auto;
        }

        /* ============================================
           TÍTULOS UNIFICADOS
           ============================================ */
        .main-title {
            font-size: 1.9rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #F1F5F9;
            margin-bottom: 0.1rem;
        }
        .sub-title {
            font-size: 0.95rem;
            font-weight: 500;
            color: #94A3B8;
            margin-bottom: 1rem;
        }

        /* Título de marca en la pantalla de login: centrado, naranja oscuro */
        .login-brand-title {
            text-align: center;
            font-size: 1.9rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #C2410C;
            margin-bottom: 0.1rem;
        }
        .login-brand-subtitle {
            text-align: center;
            font-size: 0.95rem;
            font-weight: 500;
            color: #94A3B8;
            margin-bottom: 1rem;
        }

        /* ============================================
           TARJETAS UNIFICADAS (.app-card)
           ============================================ */
        .app-card {
            background: linear-gradient(155deg, #16213A 0%, #131C30 100%);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px;
            padding: 18px 22px;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
            margin-bottom: 12px;
        }
        .app-card-label {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #94A3B8;
            margin-bottom: 4px;
        }
        .app-card-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: #F1F5F9;
            line-height: 1.2;
        }
        .app-card-delta-up { color: #26A69A; font-size: 0.85rem; font-weight: 600; }
        .app-card-delta-down { color: #EF5350; font-size: 0.85rem; font-weight: 600; }

        /* Botones con esquinas un poco más suaves y consistentes */
        .stButton > button, .stDownloadButton > button {
            border-radius: 10px !important;
            font-weight: 600 !important;
        }

        /* Separadores más discretos */
        hr {
            border-color: rgba(255, 255, 255, 0.08) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def cargar_imagen_base64(nombre_archivo, alternativas_prefijo=None):
    """Busca y codifica una imagen en base64. Si no existe el nombre exacto,
    intenta con archivos que empiecen igual (por si el nombre real difiere un poco)."""
    import os

    ruta = nombre_archivo
    if not os.path.exists(ruta) and alternativas_prefijo:
        coincidencias = [
            f
            for f in os.listdir(".")
            if any(f.lower().startswith(p) for p in alternativas_prefijo)
        ]
        if coincidencias:
            ruta = coincidencias[0]

    if not os.path.exists(ruta):
        return None

    with open(ruta, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def logo_esquina_superior_derecha(nombre_archivo="alema_iso.png", alto_px=42):
    """Coloca el logo fijo en la esquina superior derecha de la página."""
    img_b64 = cargar_imagen_base64(nombre_archivo, alternativas_prefijo=["alema_iso", "alema_a"])
    if not img_b64:
        return
    st.markdown(
        f"""
        <style>
        .logo-esquina-superior {{
            position: fixed;
            top: 12px;
            right: 20px;
            z-index: 999999;
        }}
        .logo-esquina-superior img {{
            height: {alto_px}px;
            width: auto;
        }}
        </style>
        <div class="logo-esquina-superior">
            <img src="data:image/png;base64,{img_b64}" />
        </div>
        """,
        unsafe_allow_html=True,
    )


def tarjeta(label, value, delta=None, delta_positivo=True):
    """Genera el HTML de una tarjeta de métrica con el estilo unificado (.app-card)."""
    delta_html = ""
    if delta is not None:
        clase = "app-card-delta-up" if delta_positivo else "app-card-delta-down"
        signo = "▲" if delta_positivo else "▼"
        delta_html = f'<div class="{clase}">{signo} {delta}</div>'

    return f"""
        <div class="app-card">
            <div class="app-card-label">{label}</div>
            <div class="app-card-value">{value}</div>
            {delta_html}
        </div>
    """
