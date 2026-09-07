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
           OCULTAR BARRA SUPERIOR, GITHUB Y MENÚS
           ============================================ */
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stHeaderActionElements"],
        header,
        .stAppHeader {
            display: none !important;
            visibility: hidden !important;
            height: 0px !important;
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
