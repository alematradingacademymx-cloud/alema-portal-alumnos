import json
import os
import time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:

    def st_autorefresh(interval=4000, key=None):
        pass


def cargar_datos_json(archivo, valor_defecto):
    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return valor_defecto
    return valor_defecto


def guardar_datos_json(archivo, datos):
    try:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


@st.cache_data(ttl=10)
def obtener_datos_usuario_desde_sheets(usuario_target):
    capital_defecto = 300.00
    nivel_defecto = "Nivel 1"
    try:
        sheet_url = "https://docs.google.com/spreadsheets/d/1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA/export?format=csv&gid=0"
        df = pd.read_csv(sheet_url)
        df.columns = [str(c).strip() for c in df.columns]

        col_user = next(
            (
                c
                for c in df.columns
                if any(k in c.lower() for k in ["usuario", "matricula", "user"])
            ),
            None,
        )
        col_cap = next(
            (
                c
                for c in df.columns
                if any(k in c.lower() for k in ["capital", "monto", "balance"])
            ),
            None,
        )
        col_challenge = next(
            (
                c
                for c in df.columns
                if any(k in c.lower() for k in ["challenge", "nivel", "level"])
            ),
            None,
        )

        if col_user:
            filtro = df[
                df[col_user].astype(str).str.strip().str.lower()
                == str(usuario_target).strip().lower()
            ]
            if not filtro.empty:
                if col_cap:
                    val_str = (
                        str(filtro[col_cap].values[0])
                        .replace("$", "")
                        .replace(",", "")
                        .strip()
                    )
                    capital_defecto = float(val_str)
                if col_challenge:
                    val_chal = str(filtro[col_challenge].values[0]).strip()
                    if val_chal and val_chal.lower() != "nan":
                        nivel_defecto = val_chal
    except Exception:
        pass
    return capital_defecto, nivel_defecto


def calcular_pnl_institucional(activo, tipo, entrada, salida, lotes):
    diferencia = (salida - entrada) if tipo == "BUY" else (entrada - salida)

    if "XAU" in activo:
        return diferencia * 100.0 * lotes
    elif "BTC" in activo:
        return diferencia * 1.0 * lotes
    elif "WTI" in activo or "BRENT" in activo:
        return diferencia * 1000.0 * lotes
    elif any(idx in activo for idx in ["US30", "SPX500", "NAS100", "GER40"]):
        return diferencia * 1.0 * lotes
    elif "JPY" in activo:
        valor_pip_usd_por_lote = 1000.0 / salida if salida != 0 else 6.80
        pips = diferencia * 100.0
        return pips * valor_pip_usd_por_lote * lotes
    else:
        return diferencia * 100000.0 * lotes


def obtener_config_activo(simbolo):
    if "JPY" in simbolo:
        return 3, "%.3f", 0.001, 0.100, 0.200, 0.015
    elif "XAU" in simbolo:
        return 2, "%.2f", 0.10, 2.00, 4.00, 0.35
    elif "WTI" in simbolo or "BRENT" in simbolo:
        return 2, "%.2f", 0.01, 0.30, 0.60, 0.04
    elif "BTC" in simbolo:
        return 2, "%.2f", 1.0, 100.0, 200.0, 25.00
    elif any(idx in simbolo for idx in ["US30", "NAS100", "GER40"]):
        return 2, "%.2f", 1.0, 20.0, 40.0, 2.00
    elif "SPX" in simbolo:
        return 2, "%.2f", 0.10, 4.00, 8.00, 0.40
    else:
        return 5, "%.5f", 0.00001, 0.00100, 0.00200, 0.00012

def render_simulador_alema_live():
    # --- IDENTIFICADOR DE USUARIO ---
    usuario = st.session_state.get(
        "nombre_usuario", st.session_state.get("usuario_actual", "DIRALEX")
    )

    # --- VERIFICACIÓN DE CANDADO / PERMISOS INSTITUCIONALES ---
    bd_desbloqueos = cargar_datos_json("bd_desbloqueos_alumnos.json", {})
    permisos_usuario = bd_desbloqueos.get(usuario, ["Básico"])

    if (
        usuario.upper() != "DIRALEX"
        and "Simulador Institucional" not in permisos_usuario
    ):
        st.warning("🔒 **Acceso Restringido al Simulador Institucional**")
        st.info(
            "Esta herramienta requiere autorización de Dirección General o"
            " desbloqueo progresivo según tu avance de módulos."
        )
        st.stop()

    # Recarga automática de la pantalla cada 4 segundos
    st_autorefresh(interval=4000, key="auto_refresh_terminal_forex_live")

    # --- RUTAS PERSISTENTES ---
    ARCH_PERSISTENCIA_ACTIVAS = f"posiciones_activas_{usuario}.json"
    ARCH_PERSISTENCIA_HISTORIAL = f"historial_cerradas_{usuario}.json"

    # Cargar operaciones activas e historial
    st.session_state.posiciones_abiertas = cargar_datos_json(
        ARCH_PERSISTENCIA_ACTIVAS, []
    )
    st.session_state.historial_cerradas = cargar_datos_json(
        ARCH_PERSISTENCIA_HISTORIAL, []
    )

    # CÁLCULO DINÁMICO DEL BALANCE Y ASIGNACIÓN DE NIVEL DE CHALLENGE
    capital_base_sheets, nivel_challenge_sheets = (
        obtener_datos_usuario_desde_sheets(usuario)
    )
    pnl_acumulado_historico = sum(
        float(trade.get("Beneficio", 0.0))
        for trade in st.session_state.historial_cerradas
    )
    st.session_state.balance_pedagogico = (
        capital_base_sheets + pnl_acumulado_historico
    )
    st.session_state.nivel_challenge = nivel_challenge_sheets
    st.session_state.current_loaded_user = usuario

    if "cache_precios_forex" not in st.session_state:
        st.session_state.cache_precios_forex = {}
    if "ultimo_tiempo_api" not in st.session_state:
        st.session_state.ultimo_tiempo_api = {}

    # Estilos CSS
    st.markdown(
        """
        <style>
            .mt5-terminal-card { background-color: #131722; border: 1px solid #2A2E39; padding: 10px 15px; border-radius: 4px; margin-bottom: 8px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .live-ticker-price { color: #f59e0b; font-weight: 700; font-size: 15px; }
            .live-ticker-bid { color: #ef5350; font-weight: 700; font-size: 15px; }
            .live-ticker-ask { color: #26a69a; font-weight: 700; font-size: 15px; }
            .mt5-table-container { overflow-x: auto; border: 1px solid #2A2E39; border-radius: 4px; margin-top: 10px; }
            .mt5-table { width: 100%; border-collapse: collapse; font-family: 'Segoe UI', Tahoma, sans-serif; font-size: 13px; background-color: #131722; color: #d1d4dc; }
            .mt5-table th { background-color: #1e222d; color: #848e9c; padding: 8px 12px; text-align: left; border-bottom: 1px solid #2A2E39; font-weight: 600; white-space: nowrap; }
            .mt5-table td { padding: 7px 12px; border-bottom: 1px solid #1e222d; white-space: nowrap; }
            .mt5-buy { color: #2962FF; font-weight: 600; }
            .mt5-sell { color: #ef5350; font-weight: 600; }
            .mt5-profit { color: #26a69a; font-weight: 600; }
            .mt5-loss { color: #ef5350; font-weight: 600; }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-title" style="text-align: left; font-size: 24px;'
        ' font-weight: 700;">ALEMA TRADING ACADEMY | Terminal'
        ' Institucional</div>',
        unsafe_allow_html=True,
    )

    lista_activos = [
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "EURJPY",
        "AUDUSD",
        "USDCAD",
        "USDCHF",
        "GBPJPY",
        "XAUUSD",
        "WTIUSD",
        "BRENTUSD",
        "US30",
        "SPX500",
        "NAS100",
        "GER40",
        "BTCUSD",
    ]

    par_activo = st.selectbox(
        "Símbolo de Mercado", lista_activos, key="select_chart_asset_forex"
    )

    # --- NÚCLEO DE PRECIOS CON PROTECCIÓN DE API ---
    def obtener_cotizacion_completa(simbolo):
        dec, _, step_val, _, _, spread_val = obtener_config_activo(simbolo)
        simbolos_map = {
            "EURUSD": "EUR/USD",
            "GBPUSD": "GBP/USD",
            "USDJPY": "USD/JPY",
            "EURJPY": "EUR/JPY",
            "AUDUSD": "AUD/USD",
            "USDCAD": "USD/CAD",
            "USDCHF": "USD/CHF",
            "GBPJPY": "GBP/JPY",
            "XAUUSD": "XAU/USD",
            "WTIUSD": "WTI/USD",
            "BRENTUSD": "BRENT/USD",
            "US30": "US30",
            "SPX500": "SPX",
            "NAS100": "NDX",
            "GER40": "DAX",
            "BTCUSD": "BTC/USD",
        }
        simbolo_api = simbolos_map.get(simbolo, "EUR/USD")
        api_key = "6223c6d78f7a43b2872fc3acbb3f578e"
        ahora = time.time()
        tiempo_ultimo = st.session_state.ultimo_tiempo_api.get(simbolo, 0)

        if ahora - tiempo_ultimo > 45:
            try:
                url = f"https://api.twelvedata.com/price?symbol={simbolo_api}&apikey={api_key}"
                res = requests.get(url, timeout=3)
                if res.status_code == 200:
                    data = res.json()
                    if "price" in data:
                        st.session_state.cache_precios_forex[simbolo] = float(data["price"])
            except Exception:
                pass
            finally:
                st.session_state.ultimo_tiempo_api[simbolo] = ahora

        if simbolo in st.session_state.cache_precios_forex:
            precio_base = st.session_state.cache_precios_forex[simbolo]
        else:
            precios_fallback = {
                "EURUSD": 1.15919,
                "GBPUSD": 1.31210,
                "USDJPY": 146.850,
                "EURJPY": 162.450,
                "XAUUSD": 2512.30,
                "US30": 41200.00,
                "BTCUSD": 62500.00,
            }
            precio_base = precios_fallback.get(simbolo, 1.0000)
            st.session_state.cache_precios_forex[simbolo] = precio_base

        ruido = np.random.normal(0, step_val * 1.2)
        precio_vivo = round(precio_base + ruido, dec)
        precio_bid = precio_vivo
        precio_ask = round(precio_bid + spread_val, dec)

        return precio_bid, precio_ask, precio_vivo

    precios_tick_actual = {}

    def get_precio_sincronizado(simbolo):
        if simbolo not in precios_tick_actual:
            precios_tick_actual[simbolo] = obtener_cotizacion_completa(simbolo)
        return precios_tick_actual[simbolo]

    bid_actual, ask_actual, precio_vivo_actual = get_precio_sincronizado(
        par_activo
    )

    if "mercado_forex_df" not in st.session_state:
        st.session_state.mercado_forex_df = {}

    def obtener_dataframe_forex(simbolo, precio_actual):
        if simbolo not in st.session_state.mercado_forex_df:
            fechas = [
                datetime.now() - timedelta(minutes=15 * i) for i in range(50)
            ][::-1]
            vol = precio_actual * 0.0004
            np.random.seed(123)
            closes = np.linspace(
                precio_actual - (vol * 4), precio_actual, 50
            ) + np.random.normal(0, vol * 0.2, 50)
            opens = closes + np.random.normal(0, vol * 0.1, 50)
            highs = np.maximum(opens, closes) + abs(
                np.random.normal(0, vol * 0.2, 50)
            )
            lows = np.minimum(opens, closes) - abs(np.random.normal(0, vol * 0.2, 50))

            df_init = pd.DataFrame(
                {"Open": opens, "High": highs, "Low": lows, "Close": closes},
                index=fechas,
            )
            st.session_state.mercado_forex_df[simbolo] = df_init

        df = st.session_state.mercado_forex_df[simbolo]
        df.iloc[-1, df.columns.get_loc("Close")] = precio_actual
        df.iloc[-1, df.columns.get_loc("High")] = max(
            df.iloc[-1]["Open"], max(df.iloc[-1]["High"], precio_actual)
        )
        df.iloc[-1, df.columns.get_loc("Low")] = min(
            df.iloc[-1]["Open"], min(df.iloc[-1]["Low"], precio_actual)
        )
        return df

    df_history = obtener_dataframe_forex(par_activo, bid_actual)

    # --- MONITOREO DE ORDENES ACTIVAS (CIERRE EXACTO ECN) ---
    if st.session_state.posiciones_abiertas:
        posiciones_conservadas = []
        hubo_cambios_auto = False

        for pos in st.session_state.posiciones_abiertas:
            sim_pos = pos["activo"]
            dec_pos, _, _, _, _, _ = obtener_config_activo(sim_pos)

            p_bid, p_ask, _ = get_precio_sincronizado(sim_pos)

            pos["bid_vela_actual"] = p_bid
            pos["ask_vela_actual"] = p_ask

            tp_exacto = round(pos["tp"], dec_pos)
            sl_exacto = round(pos["sl"], dec_pos)

            cierre_por_tp_sl = False
            precio_ejecucion_salida = p_bid if pos["tipo"] == "BUY" else p_ask

            if pos["tipo"] == "BUY":
                if p_bid >= tp_exacto:
                    cierre_por_tp_sl = True
                    precio_ejecucion_salida = tp_exacto
                elif p_bid <= sl_exacto:
                    cierre_por_tp_sl = True
                    precio_ejecucion_salida = sl_exacto
            else:  # SELL
                if p_ask <= tp_exacto:
                    cierre_por_tp_sl = True
                    precio_ejecucion_salida = tp_exacto
                elif p_ask >= sl_exacto:
                    cierre_por_tp_sl = True
                    precio_ejecucion_salida = sl_exacto

            if cierre_por_tp_sl:
                pnl_real = calcular_pnl_institucional(
                    sim_pos,
                    pos["tipo"],
                    pos["entrada"],
                    precio_ejecucion_salida,
                    pos["lotes"],
                )

                st.session_state.balance_pedagogico += pnl_real

                registro_historial = {
                    "Tipo": pos["tipo"].lower(),
                    "Volumen": pos["lotes"],
                    "Símbolo": sim_pos,
                    "S / L": sl_exacto,
                    "T / P": tp_exacto,
                    "Tiempo Cierre": datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
                    "Precio Cierre": precio_ejecucion_salida,
                    "Beneficio": round(pnl_real, 2),
                }
                st.session_state.historial_cerradas.append(registro_historial)
                guardar_datos_json(
                    ARCH_PERSISTENCIA_HISTORIAL, st.session_state.historial_cerradas
                )
                hubo_cambios_auto = True
            else:
                posiciones_conservadas.append(pos)

        if hubo_cambios_auto:
            st.session_state.posiciones_abiertas = posiciones_conservadas
            guardar_datos_json(
                ARCH_PERSISTENCIA_ACTIVAS, st.session_state.posiciones_abiertas
            )
            st.rerun()

    # --- DASHBOARD Y GRÁFICOS CON VISUALIZACIÓN DE CHALLENGE Y ROL ADMIN ---
    es_admin = (
        st.session_state.get("tipo_usuario") == "ADMIN" or usuario.upper() == "DIRALEX"
    )

    if es_admin:
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    else:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    with col_m1:
        st.metric("Balance Base", f"${st.session_state.balance_pedagogico:,.2f}")
    with col_m2:
        pnl_flotante_total = sum([
            calcular_pnl_institucional(
                p["activo"],
                p["tipo"],
                p["entrada"],
                (
                    p.get("bid_vela_actual", p["entrada"])
                    if p["tipo"] == "BUY"
                    else p.get("ask_vela_actual", p["entrada"])
                ),
                p["lotes"],
            )
            for p in st.session_state.posiciones_abiertas
        ])
        st.metric(
            "Beneficio Flotante",
            f"${pnl_flotante_total:,.2f}",
            delta=f"${pnl_flotante_total:,.2f}",
        )
    with col_m3:
        st.metric(
            "Posiciones Activas", f"{len(st.session_state.posiciones_abiertas)}"
        )
    with col_m4:
        st.metric(
            "Fase Challenge", st.session_state.get("nivel_challenge", "Nivel 1")
        )

    if es_admin:
        with col_m5:
            if st.button("🔄 Sincronizar Sheets"):
                st.cache_data.clear()
                st.rerun()

    st.divider()

    col_grafico, col_panel = st.columns([2.4, 1.0])
    n_decimals, formato_str, step_val, dist_sl, dist_tp, spread_val = (
        obtener_config_activo(par_activo)
    )

    with col_grafico:
        st.markdown(
            f"<div style='color: #94A3B8; font-size: 13px; margin-bottom: 4px;'>"
            f"Gráfico {par_activo} | Precio Actual: <span"
            f" class='live-ticker-price'>{formato_str % precio_vivo_actual}</span>"
            f" | BID: <span class='live-ticker-bid'>{formato_str % bid_actual}</span>"
            f" | ASK: <span class='live-ticker-ask'>{formato_str % ask_actual}</span>"
            f" | Spread: <b"
            f" style='color:#d1d4dc;'>{formato_str % spread_val}</b></div>",
            unsafe_allow_html=True,
        )

        fig = go.Figure()
        if not df_history.empty:
            fig.add_trace(
                go.Candlestick(
                    x=df_history.index,
                    open=df_history["Open"],
                    high=df_history["High"],
                    low=df_history["Low"],
                    close=df_history["Close"],
                    name=par_activo,
                    increasing_line_color="#26a69a",
                    decreasing_line_color="#ef5350",
                )
            )

        for pos in st.session_state.posiciones_abiertas:
            if pos["activo"] == par_activo:
                fig.add_hline(
                    y=pos["entrada"],
                    line_dash="dash",
                    line_color="#2962FF",
                    annotation_text=f"Entrada ({pos['entrada']})",
                )
                fig.add_hline(
                    y=pos["tp"],
                    line_dash="dot",
                    line_color="#26a69a",
                    annotation_text=f"TP ({pos['tp']})",
                )
                fig.add_hline(
                    y=pos["sl"],
                    line_dash="dot",
                    line_color="#ef5350",
                    annotation_text=f"SL ({pos['sl']})",
                )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#131722",
            plot_bgcolor="#131722",
            height=430,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(
                showgrid=True,
                gridcolor="#2A2E39",
                rangeslider=dict(visible=False),
            ),
            yaxis=dict(showgrid=True, gridcolor="#2A2E39", zeroline=False),
            dragmode="pan",
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "scrollZoom": True,
                "displayModeBar": True,
                "displaylogo": False,
            },
        )

    with col_panel:
        st.markdown("### Nueva Orden")
        sim_tipo = st.radio(
            "Dirección", ["BUY", "SELL"], horizontal=True, key="sim_dir_forex"
        )
        sim_lotes = st.number_input(
            "Volumen (Lotes)", value=0.10, min_value=0.01, step=0.01
        )

        precio_ref_orden = ask_actual if sim_tipo == "BUY" else bid_actual

        key_sl = f"sim_precio_sl_{par_activo}_{sim_tipo}"
        key_tp = f"sim_precio_tp_{par_activo}_{sim_tipo}"

        if key_sl not in st.session_state:
            st.session_state[key_sl] = float(
                round(
                    precio_ref_orden - dist_sl
                    if sim_tipo == "BUY"
                    else precio_ref_orden + dist_sl,
                    n_decimals,
                )
            )
        if key_tp not in st.session_state:
            st.session_state[key_tp] = float(
                round(
                    precio_ref_orden + dist_tp
                    if sim_tipo == "BUY"
                    else precio_ref_orden - dist_tp,
                    n_decimals,
                )
            )

        sim_precio_sl = st.number_input(
            "Stop Loss", format=formato_str, step=step_val, key=key_sl
        )
        sim_precio_tp = st.number_input(
            "Take Profit", format=formato_str, step=step_val, key=key_tp
        )

        texto_boton = (
            "🟢 EJECUTAR ORDEN DE COMPRA"
            if sim_tipo == "BUY"
            else "🔴 EJECUTAR ORDEN DE VENTA"
        )

        if st.button(texto_boton, use_container_width=True):
            nueva_orden = {
                "id": int(datetime.now().timestamp()),
                "tiempo_apertura": datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
                "activo": par_activo,
                "tipo": sim_tipo,
                "lotes": float(sim_lotes),
                "entrada": float(precio_ref_orden),
                "sl": float(sim_precio_sl),
                "tp": float(sim_precio_tp),
                "bid_vela_actual": float(bid_actual),
                "ask_vela_actual": float(ask_actual),
            }
            st.session_state.posiciones_abiertas.append(nueva_orden)
            guardar_datos_json(
                ARCH_PERSISTENCIA_ACTIVAS, st.session_state.posiciones_abiertas
            )
            st.rerun()

    # --- POSICIONES ACTIVAS ---
    st.markdown("### Posiciones Abiertas (Monitoreo ECN en Vivo)")
    if st.session_state.posiciones_abiertas:
        for idx, pos in enumerate(st.session_state.posiciones_abiertas):
            p_salida = (
                pos.get("bid_vela_actual", pos["entrada"])
                if pos["tipo"] == "BUY"
                else pos.get("ask_vela_actual", pos["entrada"])
            )
            dec_pos, fmt_pos, _, _, _, _ = obtener_config_activo(pos["activo"])
            pnl_card = calcular_pnl_institucional(
                pos["activo"], pos["tipo"], pos["entrada"], p_salida, pos["lotes"]
            )

            st.markdown(
                f"""
                    <div class="mt5-terminal-card">
                        <b>{pos['activo']}</b> | Tipo: <span style="color: {'#26a69a' if pos['tipo']=='BUY' else '#ef5350'}">{pos['tipo']}</span> | 
                        Entrada: <code>{fmt_pos % pos['entrada']}</code> | Salida Actual: <code style="color: #26a69a;">{fmt_pos % p_salida}</code> | 
                        TP: <span style="color:#26a69a;">{fmt_pos % pos['tp']}</span> | SL: <span style="color:#ef5350;">{fmt_pos % pos['sl']}</span> | 
                        PnL: <b style="color: {'#26a69a' if pnl_card>=0 else '#ef5350'}">${pnl_card:,.2f} USD</b>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Cerrar Manual #{pos['id']}", key=f"btn_close_{pos['id']}_{idx}"
            ):
                st.session_state.balance_pedagogico += pnl_card
                st.session_state.historial_cerradas.append({
                    "Tipo": pos["tipo"].lower(),
                    "Volumen": pos["lotes"],
                    "Símbolo": pos["activo"],
                    "S / L": pos["sl"],
                    "T / P": pos["tp"],
                    "Tiempo Cierre": datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
                    "Precio Cierre": round(p_salida, dec_pos),
                    "Beneficio": round(pnl_card, 2),
                })
                guardar_datos_json(
                    ARCH_PERSISTENCIA_HISTORIAL, st.session_state.historial_cerradas
                )
                st.session_state.posiciones_abiertas.pop(idx)
                guardar_datos_json(
                    ARCH_PERSISTENCIA_ACTIVAS, st.session_state.posiciones_abiertas
                )
                st.rerun()
    else:
        st.info("No hay posiciones activas.")

    # --- PANEL ADMIN: REINICIAR BITÁCORA DE CUALQUIER ALUMNO ---
    if es_admin:
        with st.expander("🛠️ Panel Admin: Reiniciar Bitácora de Alumno"):
            try:
                sheet_url_alumnos = "https://docs.google.com/spreadsheets/d/1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA/export?format=csv&gid=2037302400"
                df_alumnos_sheet = pd.read_csv(sheet_url_alumnos)
                df_alumnos_sheet.columns = df_alumnos_sheet.columns.str.strip()
                lista_matriculas = df_alumnos_sheet["Matricula"].dropna().unique().tolist()
            except Exception:
                lista_matriculas = []

            if lista_matriculas:
                matricula_reset = st.selectbox(
                    "Selecciona el alumno:",
                    lista_matriculas,
                    key="select_reset_bitacora_admin",
                )

                if st.button(
                    "🗑️ Reiniciar Bitácora de este Alumno",
                    key="btn_reset_bitacora_alumno",
                ):
                    archivo_historial_alumno = f"historial_cerradas_{matricula_reset}.json"
                    guardar_datos_json(archivo_historial_alumno, [])
                    st.success(
                        f"✅ Bitácora histórica de **{matricula_reset}** reiniciada"
                        " correctamente."
                    )
            else:
                st.warning(
                    "No se pudo cargar la lista de alumnos desde la base de datos."
                )

    # --- PANEL ADMIN: MONITOREO Y CIERRE DE OPERACIONES DE ALUMNOS ---
    if es_admin:
        with st.expander("🛡️ Monitoreo y Cierre de Operaciones de Alumnos"):
            try:
                sheet_url_alumnos_ops = "https://docs.google.com/spreadsheets/d/1v5qXHn1cA-nEJoRMi1txDjXnRurYVhxEd-47Y1oAjNA/export?format=csv&gid=2037302400"
                df_alumnos_ops = pd.read_csv(sheet_url_alumnos_ops)
                df_alumnos_ops.columns = df_alumnos_ops.columns.str.strip()
                lista_matriculas_ops = (
                    df_alumnos_ops["Matricula"].dropna().unique().tolist()
                )
            except Exception:
                lista_matriculas_ops = []

            if lista_matriculas_ops:
                matricula_monitoreo = st.selectbox(
                    "Selecciona el alumno a monitorear:",
                    lista_matriculas_ops,
                    key="select_monitoreo_alumno_admin",
                )

                archivo_activas_alumno = f"posiciones_activas_{matricula_monitoreo}.json"
                archivo_historial_alumno_mon = (
                    f"historial_cerradas_{matricula_monitoreo}.json"
                )
                posiciones_alumno = cargar_datos_json(archivo_activas_alumno, [])

                if posiciones_alumno:
                    st.caption(f"Operaciones activas de **{matricula_monitoreo}**:")
                    for idx_mon, pos_mon in enumerate(posiciones_alumno):
                        p_bid_mon, p_ask_mon, _ = get_precio_sincronizado(
                            pos_mon["activo"]
                        )
                        p_salida_mon = (
                            p_bid_mon if pos_mon["tipo"] == "BUY" else p_ask_mon
                        )
                        dec_mon, fmt_mon, _, _, _, _ = obtener_config_activo(
                            pos_mon["activo"]
                        )
                        pnl_mon = calcular_pnl_institucional(
                            pos_mon["activo"],
                            pos_mon["tipo"],
                            pos_mon["entrada"],
                            p_salida_mon,
                            pos_mon["lotes"],
                        )

                        col_info_mon, col_btn_mon = st.columns([3, 1])
                        with col_info_mon:
                            st.markdown(
                                f"""
                                    <div class="mt5-terminal-card">
                                        <b>{pos_mon['activo']}</b> | Tipo: <span style="color: {'#26a69a' if pos_mon['tipo']=='BUY' else '#ef5350'}">{pos_mon['tipo']}</span> | 
                                        Entrada: <code>{fmt_mon % pos_mon['entrada']}</code> | Actual: <code style="color: #26a69a;">{fmt_mon % p_salida_mon}</code> | 
                                        Lotes: {pos_mon['lotes']:.2f} | 
                                        PnL: <b style="color: {'#26a69a' if pnl_mon>=0 else '#ef5350'}">${pnl_mon:,.2f} USD</b>
                                    </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        with col_btn_mon:
                            if st.button(
                                "🔒 Cerrar (Admin)",
                                key=f"btn_close_admin_{matricula_monitoreo}_{pos_mon['id']}_{idx_mon}",
                                use_container_width=True,
                            ):
                                historial_alumno_mon = cargar_datos_json(
                                    archivo_historial_alumno_mon, []
                                )
                                historial_alumno_mon.append({
                                    "Tipo": pos_mon["tipo"].lower(),
                                    "Volumen": pos_mon["lotes"],
                                    "Símbolo": pos_mon["activo"],
                                    "S / L": pos_mon["sl"],
                                    "T / P": pos_mon["tp"],
                                    "Tiempo Cierre": datetime.now().strftime(
                                        "%Y.%m.%d %H:%M:%S"
                                    ),
                                    "Precio Cierre": round(p_salida_mon, dec_mon),
                                    "Beneficio": round(pnl_mon, 2),
                                    "cerrado_por": "ADMIN",
                                })
                                guardar_datos_json(
                                    archivo_historial_alumno_mon, historial_alumno_mon
                                )

                                posiciones_alumno.pop(idx_mon)
                                guardar_datos_json(
                                    archivo_activas_alumno, posiciones_alumno
                                )

                                st.success(
                                    f"✅ Operación de **{matricula_monitoreo}** cerrada"
                                    " correctamente."
                                )
                                st.rerun()
                else:
                    st.info(
                        f"El alumno **{matricula_monitoreo}** no tiene operaciones"
                        " activas."
                    )
            else:
                st.warning(
                    "No se pudo cargar la lista de alumnos desde la base de datos."
                )

    # --- BITÁCORA ---
    st.markdown("<br>", unsafe_allow_html=True)

    if es_admin:
        col_tit_bita, col_btn_bita = st.columns([3.0, 1.0])
        with col_tit_bita:
            st.markdown("### Bitácora Histórica")
        with col_btn_bita:
            if st.button("🗑️ Limpiar Historial"):
                st.session_state.historial_cerradas = []
                guardar_datos_json(ARCH_PERSISTENCIA_HISTORIAL, [])
                st.rerun()
    else:
        st.markdown("### Bitácora Histórica")

    if st.session_state.historial_cerradas:
        filas_html = []
        for item in reversed(st.session_state.historial_cerradas):
            _, fmt_pos, _, _, _, _ = obtener_config_activo(
                item.get("Símbolo", "EURUSD")
            )
            columna_origen_html = ""
            if es_admin:
                es_cierre_admin = item.get("cerrado_por") == "ADMIN"
                columna_origen_html = (
                    '<td><span style="color:#f59e0b; font-weight:600;">👑 Admin</span></td>'
                    if es_cierre_admin
                    else "<td>Alumno</td>"
                )
            filas_html.append(
                f'<tr><td>{item.get("Tiempo Cierre")}</td><td'
                f' class="{"mt5-buy" if item.get("Tipo")=="buy" else "mt5-sell"}">{item.get("Tipo")}</td>'
                f'<td>{item.get("Volumen"):.2f}</td><td>{item.get("Símbolo")}</td><td>{fmt_pos % item.get("S / L")}</td>'
                f'<td>{fmt_pos % item.get("T / P")}</td><td>{fmt_pos % item.get("Precio Cierre")}</td>'
                f'<td'
                f' class="{"mt5-profit" if item.get("Beneficio")>=0 else "mt5-loss"}">{item.get("Beneficio"):+.2f}</td>'
                f'{columna_origen_html}</tr>'
            )
        encabezado_origen = "<th>Origen</th>" if es_admin else ""
        st.markdown(
            '<div class="mt5-table-container"><table'
            ' class="mt5-table"><thead><tr><th>Tiempo</th><th>Tipo</th><th>Vol.</th><th>Símbolo</th><th>S/L</th><th>T/P</th><th>Precio'
            f' Cierre</th><th>Beneficio</th>{encabezado_origen}</tr></thead><tbody>'
            + "".join(filas_html)
            + "</tbody></table></div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("Aún no hay operaciones cerradas.")


# Aliases de compatibilidad para evitar errores de importación
render_simulador_live = render_simulador_alema_live
render_simulador = render_simulador_alema_live
render_simulador_alema_live()
