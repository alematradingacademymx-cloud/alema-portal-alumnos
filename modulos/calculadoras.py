import plotly.graph_objects as go
import streamlit as st



    """Módulo 2: Calculadoras de Lotes y Riesgo Institucional"""
    st.markdown(
        '<div class="main-title" style="text-align: left;">ALEMA TRADING'
        " ACADEMY</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-title" style="text-align: left;">Módulo Institucional'
        " de Gestión de Riesgo y Lotajes</div>",
        unsafe_allow_html=True,
    )

    tab_operativa, tab_rapida = st.tabs([
        "⚡ Calculadora Operativa Completa",
        "🛡️ Calculadora de Lotes Rápidos (Riesgo)",
    ])

    # =========================================================
    # PESTAÑA 1: CALCULADORA OPERATIVA COMPLETA
    # =========================================================
    with tab_operativa:
        st.subheader("⚡ Calculadora Operativa & Multi-Activo")

        with st.expander("📖 Guía Rápida de Uso"):
            st.markdown("""
            1. **Ingresa el activo:** Escribe el par (ej. `EUR/USD` o `USD/JPY`).
            2. **Define tu riesgo:** Mantén el riesgo por operación preferentemente entre **1% y 2%**.
            3. **Ingresa tu Stop Loss:** Mide los pips en TradingView y colócalos en la casilla.
            4. **Copia tus datos:** Usa el bloque inferior para copiar el lotaje, SL y TP exactos a tu MetaTrader o cTrader.
            """)

        st.divider()

        st.subheader("⚙️ Parámetros de la Operación")
        col1, col2 = st.columns(2)

        with col1:
            par_seleccionado = (
                st.text_input(
                    "Par de Divisas / Activo", value="EUR/USD", key="op_par"
                )
                .strip()
                .upper()
            )

            symbol_tv = (
                par_seleccionado.replace("/", "")
                .replace("-", "")
                .replace(" ", "")
            )
            tv_url = f"https://es.tradingview.com/chart/?symbol=FX:{symbol_tv}"
            investing_url = "https://es.investing.com/economic-calendar/"

            st.link_button("📈 Ver Gráfico en TradingView", tv_url)
            st.link_button(
                "📅 Ver Calendario Económico (Investing)", investing_url
            )

            es_jpy = "JPY" in par_seleccionado
            divisor_pip = 100.0 if es_jpy else 10000.0
            valor_pip_sugerido = 7.0 if es_jpy else 10.0

            if es_jpy:
                st.warning(
                    "⚠️ **Par JPY Detectado:**\n"
                    "• El valor del pip se ajustó a **$7.0 USD/lote**.\n"
                    "• 📌 **Importante:** Verifica el **Precio de Entrada**"
                    " actual en TradingView."
                )

            balance = st.number_input(
                "Balance de la Cuenta ($)",
                value=200.0,
                step=10.0,
                key="op_balance",
            )
            riesgo_pct = st.number_input(
                "Porcentaje de Riesgo (%)",
                value=2.0,
                step=0.5,
                key="op_riesgo",
            )
            sl_pips = st.number_input(
                "Tamaño del Stop Loss (Pips)",
                value=15.0,
                step=1.0,
                key="op_sl_pips",
            )

        with col2:
            tipo_orden = st.selectbox(
                "Tipo de Orden", ["Compra", "Venta"], key="op_tipo_orden"
            )

            precio_defecto = 155.200 if es_jpy else 1.08500
            paso_precio = 0.001 if es_jpy else 0.00001
            formato_precio = "%.3f" if es_jpy else "%.5f"

            precio_entrada = st.number_input(
                "Precio de Entrada",
                value=precio_defecto,
                step=paso_precio,
                format=formato_precio,
                key=f"op_entrada_{es_jpy}",
            )

            valor_pip = st.number_input(
                "Valor del Pip por Lote Estándar ($)",
                value=valor_pip_sugerido,
                step=0.5,
                key=f"op_val_pip_{es_jpy}",
            )
            ratio = st.number_input(
                "Ratio (Riesgo:Beneficio)",
                value=3.0,
                step=0.5,
                key="op_ratio",
            )

        dinero_arriesgar = balance * (riesgo_pct / 100.0)
        lotaje = (
            dinero_arriesgar / (sl_pips * valor_pip)
            if sl_pips > 0 and valor_pip > 0
            else 0.0
        )
        tp_pips = sl_pips * ratio
        ganancia = lotaje * tp_pips * valor_pip

        distancia_sl_precio = sl_pips / divisor_pip
        distancia_tp_precio = tp_pips / divisor_pip

        if tipo_orden == "Compra":
            precio_sl = precio_entrada - distancia_sl_precio
            precio_tp = precio_entrada + distancia_tp_precio
        else:
            precio_sl = precio_entrada + distancia_sl_precio
            precio_tp = precio_entrada - distancia_tp_precio

        str_sl = f"{precio_sl:.3f}" if es_jpy else f"{precio_sl:.5f}"
        str_tp = f"{precio_tp:.3f}" if es_jpy else f"{precio_tp:.5f}"

        st.divider()

        if riesgo_pct <= 2.0:
            st.success(
                f"🟢 **Gestión Institucional Excelente ({riesgo_pct}%):** Riesgo"
                " controlado."
            )
        elif riesgo_pct <= 5.0:
            st.warning(
                f"🟠 **Riesgo Moderado ({riesgo_pct}%):** Requiere confirmación"
                " de alta probabilidad."
            )
        else:
            st.error(
                f"🔴 **Alerta de Sobrerriesgo ({riesgo_pct}%):** Reduce la"
                " exposición."
            )

        st.subheader("📊 Resultados de Ejecución")
        res_col1, res_col2 = st.columns(2)

        with res_col1:
            st.metric(
                label="Riesgo Máximo ($)", value=f"${dinero_arriesgar:.2f}"
            )
            st.metric(label="Lotaje Exacto", value=f"{lotaje:.2f}")
            st.metric(label="Precio Stop Loss", value=str_sl)

        with res_col2:
            st.metric(
                label="Ganancia Potencial ($)", value=f"${ganancia:.2f}"
            )
            st.metric(label="Tamaño TP (PIPS)", value=f"{tp_pips:.0f} pips")
            st.metric(label="Precio Take Profit", value=str_tp)

        st.subheader("📋 Datos Listos para Ejecutar")
        st.markdown(
            f"""
        <div class="copy-box" style="padding:15px; border-radius:10px; background-color:#1E293B; border:1px solid #334155;">
        <b>{par_seleccionado}</b> | <b>{tipo_orden.upper()}</b><br>
        🔹 Lotaje: <b>{lotaje:.2f}</b><br>
        🛑 Stop Loss: <b>{str_sl}</b><br>
        🎯 Take Profit: <b>{str_tp}</b>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.subheader("📉 Distribución de Balance")
        capital_seguro = max(0.0, balance - dinero_arriesgar)

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=["Capital Seguro", "Capital en Riesgo"],
                    values=[capital_seguro, dinero_arriesgar],
                    hole=0.5,
                    marker_colors=["#10B981", "#FF6B00"],
                )
            ]
        )

        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            height=220,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#F1F5F9"),
            showlegend=True,
        )

        st.plotly_chart(fig, use_container_width=True)

    # =========================================================
    # PESTAÑA 2: CALCULADORA RÁPIDA DE LOTES
    # =========================================================
    with tab_rapida:
        st.subheader("🛡️ Calculadora Rápida de Lotaje y Riesgo")
        st.write(
            "Calcula de forma inmediata el lotaje exacto según tu capital y"
            " tolerancia de riesgo."
        )

        col_r1, col_r2 = st.columns(2)

        with col_r1:
            bal_r = st.number_input(
                "Balance Total de la Cuenta ($)",
                value=500.0,
                step=50.0,
                key="rap_balance",
            )
            riesgo_r = st.number_input(
                "Porcentaje de Riesgo a Arriesgar (%)",
                value=1.0,
                step=0.5,
                key="rap_riesgo",
            )

        with col_r2:
            sl_r = st.number_input(
                "Stop Loss en Pips / Puntos",
                value=20.0,
                step=1.0,
                key="rap_sl",
            )
            val_pip_r = st.number_input(
                "Valor por Pip (1 Lote Estándar $)",
                value=10.0,
                step=0.5,
                key="rap_pip_val",
            )

        monto_arriesgar = bal_r * (riesgo_r / 100.0)
        lotaje_rapido = (
            monto_arriesgar / (sl_r * val_pip_r)
            if sl_r > 0 and val_pip_r > 0
            else 0.0
        )

        st.divider()

        st.subheader("🎯 Resultado de Lotaje Recomendado")

        c_res1, c_res2 = st.columns(2)
        with c_res1:
            st.metric(
                label="Monto Máximo a Arriesgar",
                value=f"${monto_arriesgar:.2f}",
            )
        with c_res2:
            st.metric(
                label="Lote Exacto a Operar", value=f"{lotaje_rapido:.2f} Lotes"
            )

        st.markdown(
            f"""
        <div class="copy-box" style="text-align: center; font-size: 18px; padding:15px; border-radius:10px; background-color:#1E293B; border:1px solid #334155;">
        💡 <b>LOTAGE SUGERIDO:</b> <span style="color:#FF6B00; font-size: 22px;"><b>{lotaje_rapido:.2f}</b></span>
        </div>
        """,
            unsafe_allow_html=True,
        )


# Alias de compatibilidad
render_calculadoras_lotes = render_calculadoras
