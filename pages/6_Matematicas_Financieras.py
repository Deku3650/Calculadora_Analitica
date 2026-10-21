# pages/6_Matematicas_Financieras.py
import datetime
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.ticker import AutoMinorLocator, FuncFormatter

# 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO)
st.set_page_config(
    page_title="Matemáticas Financieras - MATHESIS",
    page_icon="📈",
    layout="wide",
)

from estilos import cargar_estilos_globales, encabezado_pagina, header_tarjeta, subheader_tarjeta  # noqa: E402
from utils import gestionar_inventario_sidebar, inicializar_estado, mostrar_figura_segura  # noqa: E402

cargar_estilos_globales()
inicializar_estado()

AZUL = "#0284c7"
NARANJA = "#ea580c"
VERDE = "#16a34a"
ROJO = "#dc2626"
MORADO = "#7c3aed"
OSCURO = "#1e293b"
CLARO = "#cbd5e1"
FONDO = "#ffffff"

FRECUENCIAS = {
    "Anual": 1,
    "Semestral": 2,
    "Cuatrimestral": 3,
    "Trimestral": 4,
    "Bimestral": 6,
    "Mensual": 12,
    "Quincenal": 24,
    "Semanal": 52,
    "Diaria (360)": 360,
    "Diaria (365)": 365,
}

# Diccionario explícito para evitar textos corruptos ("Semono", "Diori")
NOMBRE_PERIODO = {
    "Anual": ("año", "años", "anual"),
    "Semestral": ("semestre", "semestres", "semestral"),
    "Cuatrimestral": ("cuatrimestre", "cuatrimestres", "cuatrimestral"),
    "Trimestral": ("trimestre", "trimestres", "trimestral"),
    "Bimestral": ("bimestre", "bimestres", "bimestral"),
    "Mensual": ("mes", "meses", "mensual"),
    "Quincenal": ("quincena", "quincenas", "quincenal"),
    "Semanal": ("semana", "semanas", "semanal"),
    "Diaria (360)": ("día comercial", "días comerciales", "diaria (base 360)"),
    "Diaria (365)": ("día natural", "días naturales", "diaria (base 365)"),
}


def _dias_30_360_isda(d1: datetime.date, d2: datetime.date) -> int:
    """Calcula días bajo la convención estándar 30/360 (ISDA / US Bond Basis)."""
    y1, m1, day1 = d1.year, d1.month, d1.day
    y2, m2, day2 = d2.year, d2.month, d2.day

    es_bisiesto1 = y1 % 4 == 0 and (y1 % 100 != 0 or y1 % 400 == 0)
    es_bisiesto2 = y2 % 4 == 0 and (y2 % 100 != 0 or y2 % 400 == 0)
    es_feb1 = m1 == 2 and (day1 == 29 or (day1 == 28 and not es_bisiesto1))
    es_feb2 = m2 == 2 and (day2 == 29 or (day2 == 28 and not es_bisiesto2))

    if es_feb1 and es_feb2:
        day2 = 30
    if es_feb1:
        day1 = 30
    if day1 == 31:
        day1 = 30
    if day2 == 31 and day1 == 30:
        day2 = 30

    return (y2 - y1) * 360 + (m2 - m1) * 30 + (day2 - day1)


def _crear_grafica_amplia(w=10.5, h=4.2, titulo="", xlabel="Periodo", ylabel="Monto ($)"):
    """Crea una figura amplia de ancho completo con formato monetario legible."""
    fig, ax = plt.subplots(figsize=(w, h), dpi=110, facecolor=FONDO)
    ax.set_facecolor("#fbfdff")
    ax.minorticks_on()
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.grid(True, which="major", color=CLARO, lw=0.9, alpha=0.9)
    ax.grid(True, which="minor", color="#e2e8f0", lw=0.5, alpha=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(OSCURO)
        ax.spines[s].set_linewidth(1.4)
    ax.tick_params(colors=OSCURO, labelsize=9)
    ax.set_xlabel(xlabel, color=OSCURO, fontweight="bold", fontsize=10)
    ax.set_ylabel(ylabel, color=OSCURO, fontweight="bold", fontsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:,.0f}"))
    if titulo:
        ax.set_title(titulo, color=OSCURO, fontweight="bold", fontsize=11.5, pad=12)
    return fig, ax


def _render_inversion_sidebar(nombre, datos):
    st.markdown(
        f"**Régimen:** {datos['tipo']}  \n"
        f"**Capital ($C$):** `${datos['C']:,.2f}`  \n"
        f"**Monto ($M$):** `${datos['M']:,.2f}`  \n"
        f"**Tasa ($i$):** `{datos['tasa'] * 100:.2f}%`  \n"
        f"**Plazo ($n$):** `{datos['n']:.2f}` periodos"
    )


# ==============================================================================
# ENCABEZADO Y BARRA LATERAL (INVENTARIO CON RENOMBRADO Y BORRADO INDIVIDUAL)
# ==============================================================================
encabezado_pagina(
    "📈 Módulo de Matemáticas Financieras y Valuación Actuarial",
    "Interés simple, compuesto y continuo, comparador de inversiones, conversión de tasas, conteo 30/360, anualidades, amortización, bonos y VPN/TIR.",
)

gestionar_inventario_sidebar(
    clave_estado="mis_inversiones",
    titulo="💼 Escenarios Guardados",
    etiqueta_item="Inversión:",
    claves_temporales=("ult_fin_res",),
    render_fn=_render_inversion_sidebar,
)

# ==============================================================================
# PESTAÑAS PRINCIPALES (DISEÑO AMPLIO DE ANCHO COMPLETO)
# ==============================================================================
tab_interes, tab_comparador, tab_tasas, tab_plazos, tab_anualidades, tab_bonos = st.tabs([
    "💰 1. Interés Simple y Compuesto",
    "📊 2. Comparador Gráfico",
    "🔄 3. Conversión de Tasas",
    "📅 4. Plazos y Fechas (30/360)",
    "🏦 5. Anualidades y Amortización",
    "📜 6. Bonos y Proyectos (VPN / TIR)",
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: INTERÉS SIMPLE, COMPUESTO Y CONTINUO (ANCHO COMPLETO)
# ------------------------------------------------------------------------------
with tab_interes:
    with st.container(border=True):
        header_tarjeta("Calculadora del Valor del Dinero en el Tiempo")

        col_reg, col_inc = st.columns(2, gap="large")
        with col_reg:
            regimen = st.radio(
                "Seleccione el régimen de capitalización:",
                ["Interés Compuesto", "Interés Simple", "Capitalización Continua (Fuerza δ)"],
                horizontal=True,
                key="fin_regimen",
            )
        with col_inc:
            incognita = st.selectbox(
                "Seleccione la variable a calcular:",
                [
                    "Monto Futuro (M)",
                    "Capital Inicial / Valor Presente (C)",
                    "Tasa de Interés por periodo (i / δ)",
                    "Número de periodos (n)",
                ],
                key="fin_incog",
            )

        st.divider()
        subheader_tarjeta("Parámetros de la Operación")

        c1, c2, c3 = st.columns(3, gap="large")
        C_val = M_val = i_val = n_val = 0.0

        if incognita == "Monto Futuro (M)":
            with c1:
                C_val = st.number_input("Capital Inicial C ($):", min_value=0.01, value=10000.0, step=500.0, format="%.2f")
            with c2:
                i_pct = st.number_input("Tasa por periodo (%):", min_value=0.0, value=8.0, step=0.5, format="%.4f")
                i_val = i_pct / 100.0
            with c3:
                n_val = st.number_input("Número de periodos (n):", min_value=0.01, value=6.0, step=1.0, format="%.2f")

        elif incognita == "Capital Inicial / Valor Presente (C)":
            with c1:
                M_val = st.number_input("Monto Futuro M ($):", min_value=0.01, value=16000.0, step=500.0, format="%.2f")
            with c2:
                i_pct = st.number_input("Tasa por periodo (%):", min_value=0.0, value=8.0, step=0.5, format="%.4f")
                i_val = i_pct / 100.0
            with c3:
                n_val = st.number_input("Número de periodos (n):", min_value=0.01, value=6.0, step=1.0, format="%.2f")

        elif incognita == "Tasa de Interés por periodo (i / δ)":
            with c1:
                C_val = st.number_input("Capital Inicial C ($):", min_value=0.01, value=10000.0, step=500.0, format="%.2f")
            with c2:
                M_val = st.number_input("Monto Futuro M ($):", min_value=0.01, value=16000.0, step=500.0, format="%.2f")
            with c3:
                n_val = st.number_input("Número de periodos (n):", min_value=0.01, value=6.0, step=1.0, format="%.2f")

        else:
            with c1:
                C_val = st.number_input("Capital Inicial C ($):", min_value=0.01, value=10000.0, step=500.0, format="%.2f")
            with c2:
                M_val = st.number_input("Monto Futuro M ($):", min_value=0.01, value=16000.0, step=500.0, format="%.2f")
            with c3:
                i_pct = st.number_input("Tasa por periodo (%):", min_value=0.01, value=8.0, step=0.5, format="%.4f")
                i_val = i_pct / 100.0

        if st.button("🧮 Calcular Operación Financiera", use_container_width=True, key="btn_calc_int"):
            error_fin = False
            if incognita == "Monto Futuro (M)":
                if regimen == "Interés Compuesto":
                    M_val = C_val * ((1.0 + i_val) ** n_val)
                elif regimen == "Interés Simple":
                    M_val = C_val * (1.0 + i_val * n_val)
                else:
                    M_val = C_val * math.exp(i_val * n_val)

            elif incognita == "Capital Inicial / Valor Presente (C)":
                if regimen == "Interés Compuesto":
                    C_val = M_val / ((1.0 + i_val) ** n_val)
                elif regimen == "Interés Simple":
                    C_val = M_val / (1.0 + i_val * n_val)
                else:
                    C_val = M_val * math.exp(-i_val * n_val)

            elif incognita == "Tasa de Interés por periodo (i / δ)":
                if M_val < C_val:
                    st.error("El Monto Futuro M debe ser mayor o igual al Capital Inicial C.")
                    error_fin = True
                else:
                    if regimen == "Interés Compuesto":
                        i_val = (M_val / C_val) ** (1.0 / n_val) - 1.0
                    elif regimen == "Interés Simple":
                        i_val = (M_val / C_val - 1.0) / n_val
                    else:
                        i_val = math.log(M_val / C_val) / n_val

            else:
                if i_val <= 0 or M_val <= C_val:
                    st.error("Para despejar el plazo n se requiere una tasa positiva y un Monto M mayor al Capital C.")
                    error_fin = True
                else:
                    if regimen == "Interés Compuesto":
                        n_val = math.log(M_val / C_val) / math.log(1.0 + i_val)
                    elif regimen == "Interés Simple":
                        n_val = (M_val / C_val - 1.0) / i_val
                    else:
                        n_val = math.log(M_val / C_val) / i_val

            if not error_fin:
                st.session_state["ult_fin_res"] = {
                    "tipo": regimen,
                    "C": C_val,
                    "M": M_val,
                    "tasa": i_val,
                    "n": n_val,
                    "I": M_val - C_val,
                }

    if "ult_fin_res" in st.session_state:
        r_f = st.session_state["ult_fin_res"]
        with st.container(border=True):
            subheader_tarjeta("🎯 Resultados de la Operación")

            # Métricas distribuidas a todo lo ancho para que jamás se trunquen los números
            m1, m2, m3, m4 = st.columns(4, gap="medium")
            m1.metric("Capital Inicial (C)", f"${r_f['C']:,.2f}")
            m2.metric("Monto Futuro (M)", f"${r_f['M']:,.2f}")
            m3.metric("Interés Generado (I = M − C)", f"${r_f['I']:,.2f}")
            m4.metric("Tasa / Plazo", f"{r_f['tasa'] * 100:.2f}%  ·  {r_f['n']:.2f} per.")

            if r_f["tipo"] == "Interés Compuesto":
                st.latex(
                    "M = C(1 + i)^n = "
                    + f"{r_f['C']:,.2f}(1 + {r_f['tasa']:.6f})^{{{r_f['n']:.2f}}} = \\mathbf{{\\${r_f['M']:,.2f}}}"
                )
            elif r_f["tipo"] == "Interés Simple":
                st.latex(
                    "M = C(1 + i \\cdot n) = "
                    + f"{r_f['C']:,.2f}(1 + {r_f['tasa']:.6f} \\times {r_f['n']:.2f}) = \\mathbf{{\\${r_f['M']:,.2f}}}"
                )
            else:
                st.latex(
                    "M = C \\cdot e^{\\delta n} = "
                    + f"{r_f['C']:,.2f} \\cdot e^{{{r_f['tasa']:.6f} \\times {r_f['n']:.2f}}} = \\mathbf{{\\${r_f['M']:,.2f}}}"
                )

            st.divider()
            subheader_tarjeta("📈 Evolución Temporal del Capital (Simple vs. Compuesto vs. Continuo)")
            ts = np.linspace(0, max(float(r_f["n"]), 1.0), 200)
            c0, i0 = r_f["C"], r_f["tasa"]
            fig_ev, ax_ev = _crear_grafica_amplia(
                titulo=f"Crecimiento del Capital (C = ${c0:,.2f}, Tasa = {i0 * 100:.2f}%, Plazo = {r_f['n']:.2f} periodos)"
            )
            ax_ev.plot(ts, c0 * (1.0 + i0 * ts), color=VERDE, lw=2.0, ls="--", label="Interés Simple: C(1 + i·t)")
            ax_ev.plot(ts, c0 * ((1.0 + i0) ** ts), color=AZUL, lw=2.6, label="Interés Compuesto: C(1 + i)ᵗ")
            ax_ev.plot(ts, c0 * np.exp(i0 * ts), color=NARANJA, lw=2.0, ls=":", label="Capitalización Continua: C·e^(δt)")
            ax_ev.legend(fontsize=9.5, loc="upper left")
            mostrar_figura_segura(fig_ev)

            st.divider()
            col_s1, col_s2 = st.columns([2.5, 1])
            with col_s1:
                nom_esc = st.text_input("Guardar este escenario en el inventario lateral como (Ej: INV_CETES, PAGARE_1):", value="INV_1", key="nom_esc_fin").upper().strip()
            with col_s2:
                st.write("")
                if st.button("💾 Guardar Escenario", key="btn_save_esc_fin", use_container_width=True):
                    if nom_esc:
                        st.session_state.mis_inversiones[nom_esc] = r_f.copy()
                        st.success(f"Escenario '{nom_esc}' guardado en la barra lateral.")
                        st.rerun()

# ------------------------------------------------------------------------------
# PESTAÑA 2: COMPARADOR GRÁFICO DE ESCENARIOS (ANCHO COMPLETO)
# ------------------------------------------------------------------------------
with tab_comparador:
    with st.container(border=True):
        header_tarjeta("Comparador Gráfico de Inversiones y Escenarios Guardados")
        if not st.session_state.mis_inversiones:
            st.info("👈 Guarde uno o más escenarios en la Pestaña 1 para compararlos gráficamente en pantalla completa.")
        else:
            seleccion_esc = st.multiselect(
                "Seleccione los escenarios a comparar:",
                list(st.session_state.mis_inversiones.keys()),
                default=list(st.session_state.mis_inversiones.keys()),
            )
            if seleccion_esc:
                horizonte_max = max(float(st.session_state.mis_inversiones[k]["n"]) for k in seleccion_esc)
                fig_comp, ax_comp = _crear_grafica_amplia(
                    w=11.0,
                    h=4.6,
                    titulo="Comparativa de Crecimiento de Escenarios de Inversión",
                )
                paleta = [AZUL, NARANJA, VERDE, ROJO, MORADO, "#0891b2", "#be185d"]
                filas_resumen = []

                for idx, nom_k in enumerate(seleccion_esc):
                    d_k = st.session_state.mis_inversiones[nom_k]
                    t_k = np.linspace(0, float(d_k["n"]), 200)
                    if d_k["tipo"] == "Interés Compuesto":
                        y_k = d_k["C"] * ((1.0 + d_k["tasa"]) ** t_k)
                    elif d_k["tipo"] == "Interés Simple":
                        y_k = d_k["C"] * (1.0 + d_k["tasa"] * t_k)
                    else:
                        y_k = d_k["C"] * np.exp(d_k["tasa"] * t_k)

                    col_k = paleta[idx % len(paleta)]
                    ax_comp.plot(t_k, y_k, color=col_k, lw=2.5, label=f"{nom_k} ({d_k['tipo']} → ${d_k['M']:,.2f})")
                    ax_comp.plot([d_k["n"]], [d_k["M"]], "o", color=col_k, ms=7)
                    filas_resumen.append({
                        "Escenario": nom_k,
                        "Régimen": d_k["tipo"],
                        "Capital Inicial (C)": d_k["C"],
                        "Tasa por Periodo": f"{d_k['tasa'] * 100:.4f}%",
                        "Plazo (n)": f"{d_k['n']:.2f}",
                        "Interés Generado (I)": d_k["I"],
                        "Monto Final (M)": d_k["M"],
                    })

                ax_comp.set_xlim(0, horizonte_max * 1.05)
                ax_comp.legend(fontsize=9.5, loc="upper left")
                mostrar_figura_segura(fig_comp)

                subheader_tarjeta("Tabla Comparativa de Escenarios")
                df_comp = pd.DataFrame(filas_resumen)
                st.dataframe(
                    df_comp.style.format({
                        "Capital Inicial (C)": "${:,.2f}",
                        "Interés Generado (I)": "${:,.2f}",
                        "Monto Final (M)": "${:,.2f}",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )

# ------------------------------------------------------------------------------
# PESTAÑA 3: CONVERSIÓN DE TASAS (NOMINAL, EFECTIVA, CONTINUA Y TASA REAL)
# ------------------------------------------------------------------------------
with tab_tasas:
    with st.container(border=True):
        header_tarjeta("Conversión de Tasas de Interés (Nominal ↔ Efectiva ↔ Continua y Ecuación de Fisher)")

        c1, c2, c3, c4 = st.columns(4, gap="medium")
        with c1:
            tasa_in_pct = st.number_input("Tasa de entrada (%):", min_value=0.0, value=12.0, step=0.25, format="%.4f", key="tasa_conv_in")
        with c2:
            tipo_tasa_in = st.selectbox(
                "Tipo de tasa ingresada:",
                ["Nominal Anual j^(m)", "Efectiva del Periodo i_m", "Efectiva Anual (TEA / i)"],
                key="tipo_tasa_in",
            )
        with c3:
            frec_origen = st.selectbox("Capitalización de origen (m):", list(FRECUENCIAS.keys()), index=5, key="frec_orig")
        with c4:
            frec_destino = st.selectbox("Convertir a frecuencia destino (k):", list(FRECUENCIAS.keys()), index=3, key="frec_dest")

        inflacion_pct = st.slider("Tasa de inflación anual π (%) [para calcular Tasa Real de Fisher]:", min_value=0.0, max_value=25.0, value=4.5, step=0.25, key="inf_fisher")

        m_or = FRECUENCIAS[frec_origen]
        m_de = FRECUENCIAS[frec_destino]
        t_in = tasa_in_pct / 100.0

        if tipo_tasa_in.startswith("Nominal"):
            i_per_or = t_in / m_or
            tea = (1.0 + i_per_or) ** m_or - 1.0
        elif tipo_tasa_in.startswith("Efectiva del Periodo"):
            i_per_or = t_in
            tea = (1.0 + i_per_or) ** m_or - 1.0
        else:
            tea = t_in
            i_per_or = (1.0 + tea) ** (1.0 / m_or) - 1.0

        i_per_dest = (1.0 + tea) ** (1.0 / m_de) - 1.0
        j_nom_dest = i_per_dest * m_de
        delta_cont = math.log(1.0 + tea)
        pi_inf = inflacion_pct / 100.0
        tasa_real = (1.0 + tea) / (1.0 + pi_inf) - 1.0

        sust_or, _, adj_or = NOMBRE_PERIODO[frec_origen]
        sust_de, _, adj_de = NOMBRE_PERIODO[frec_destino]

        st.divider()
        subheader_tarjeta("Tasas Equivalentes Obtenidas")

        k1, k2, k3, k4 = st.columns(4, gap="medium")
        k1.metric(f"Tasa Efectiva por {sust_de}", f"{i_per_dest * 100:.4f}%")
        k2.metric(f"Nominal Anual Cap. {frec_destino}", f"{j_nom_dest * 100:.4f}%")
        k3.metric("Tasa Efectiva Anual (TEA)", f"{tea * 100:.4f}%")
        k4.metric("Tasa Real Anual (Fisher)", f"{tasa_real * 100:.4f}%")

        st.latex(
            r"1 + i = \left(1 + \frac{j^{(m)}}{m}\right)^m = \left(1 + \frac{j^{(k)}}{k}\right)^k = e^{\delta}, \qquad "
            r"i_{\text{real}} = \frac{1 + i}{1 + \pi} - 1"
        )

        st.info(
            f"💡 **Interpretación:** Una tasa {adj_or} efectiva de **{i_per_or * 100:.4f}%** por {sust_or} "
            f"equivale exactamente a una tasa efectiva {adj_de} de **{i_per_dest * 100:.4f}%** por {sust_de} "
            f"(o una nominal anual $j^{{({m_de})}} = {j_nom_dest * 100:.4f}\\%$ capitalizable {frec_destino.lower()}), "
            f"y a una fuerza de interés continua $\\delta = {delta_cont * 100:.4f}\\%$."
        )

# ------------------------------------------------------------------------------
# PESTAÑA 4: CÁLCULO DE PLAZOS Y CONVENCIÓN 30/360 ISDA
# ------------------------------------------------------------------------------
with tab_plazos:
    with st.container(border=True):
        header_tarjeta("Cálculo de Plazos entre Fechas y Convenciones Bancarias (Exacto vs. 30/360 ISDA)")
        st.caption("Incluye el ajuste normativo ISDA para fines de mes (día 31 → 30), garantizando que del 31 de marzo al 1 de abril cuente exactamente 1 día.")

        c_f1, c_f2, c_f3 = st.columns(3, gap="large")
        with c_f1:
            f_ini = st.date_input("Fecha de inicio (Apertura / Emisión):", value=datetime.date(2026, 3, 31), key="f_ini_d")
        with c_f2:
            f_fin = st.date_input("Fecha de término (Vencimiento / Liquidación):", value=datetime.date(2026, 4, 1), key="f_fin_d")
        with c_f3:
            cap_plazo = st.number_input("Capital para estimar intereses en el plazo ($):", min_value=0.0, value=100000.0, step=5000.0, format="%.2f")
            tasa_anual_plazo = st.number_input("Tasa simple anual (%):", min_value=0.0, value=11.0, step=0.25) / 100.0

        if f_fin < f_ini:
            st.error("⛔ La fecha de vencimiento debe ser posterior o igual a la fecha de inicio.")
        else:
            dias_exactos = (f_fin - f_ini).days
            dias_360 = _dias_30_360_isda(f_ini, f_fin)

            st.divider()
            d1, d2, d3 = st.columns(3, gap="medium")
            d1.metric("Días Exactos (Calendario Real)", f"{dias_exactos:,} días")
            d2.metric("Días Comerciales (30/360 ISDA)", f"{dias_360:,} días")
            d3.metric("Diferencia entre Convenciones", f"{dias_exactos - dias_360:+,} días")

            int_act_365 = cap_plazo * tasa_anual_plazo * (dias_exactos / 365.0)
            int_act_360 = cap_plazo * tasa_anual_plazo * (dias_exactos / 360.0)
            int_30_360 = cap_plazo * tasa_anual_plazo * (dias_360 / 360.0)

            st.markdown(
                f"| Convención | Nombre Técnico | Fracción de Año ($t$) | Interés Simple Generado (`${cap_plazo:,.2f}` al `{tasa_anual_plazo*100:.2f}%`) |\n"
                f"|---|---|---|---|\n"
                f"| **Exacto / 365 (Actual/Actual)** | Interés Exacto con tiempo exacto | `{dias_exactos} / 365 = {dias_exactos / 365.0:.6f}` | **`${int_act_365:,.2f}`** |\n"
                f"| **Exacto / 360 (Actual/360)** | Regla del Banquero (Ordinario con tiempo exacto) | `{dias_exactos} / 360 = {dias_exactos / 360.0:.6f}` | **`${int_act_360:,.2f}`** |\n"
                f"| **30 / 360 (ISDA Bond Basis)** | Interés Ordinario con tiempo comercial | `{dias_360} / 360 = {dias_360 / 360.0:.6f}` | **`${int_30_360:,.2f}`** |"
            )

# ------------------------------------------------------------------------------
# PESTAÑA 5: ANUALIDADES (CONSTANTES Y VARIABLES) Y TABLA DE AMORTIZACIÓN
# ------------------------------------------------------------------------------
with tab_anualidades:
    sub_an1, sub_an2, sub_an3 = st.tabs([
        "📅 1. Anualidades Constantes",
        "📈 2. Anualidades Variables (Aritmética, Geométrica y Perpetuidad)",
        "🏦 3. Tabla de Amortización y Gráfica de Saldos",
    ])

    with sub_an1:
        with st.container(border=True):
            header_tarjeta("Valuación de Anualidades Ciertas Constantes (Vencidas, Anticipadas y Diferidas)")

            c1, c2 = st.columns(2, gap="large")
            with c1:
                modalidad_an = st.radio(
                    "Modalidad de los pagos:",
                    ["Vencida / Ordinaria (al final del periodo)", "Anticipada (al inicio del periodo)"],
                    horizontal=True,
                    key="an_mod",
                )
            with c2:
                incog_an = st.selectbox(
                    "Variable a calcular:",
                    ["Valor Presente (VP) y Valor Futuro (VF)", "Pago Periódico / Renta (R) dado el Valor Presente", "Pago Periódico / Renta (R) dado el Valor Futuro"],
                    key="an_incog",
                )

            p1, p2, p3, p4 = st.columns(4, gap="medium")
            with p1:
                if incog_an.startswith("Valor Presente"):
                    R_an = st.number_input("Renta periódica R ($):", min_value=0.01, value=2500.0, step=100.0, format="%.2f", key="an_R")
                elif "Valor Presente" in incog_an:
                    VP_conocido = st.number_input("Valor Presente VP ($):", min_value=0.01, value=25000.0, step=500.0, format="%.2f", key="an_VP_c")
                else:
                    VF_conocido = st.number_input("Valor Futuro VF ($):", min_value=0.01, value=35000.0, step=500.0, format="%.2f", key="an_VF_c")
            with p2:
                i_an_pct = st.number_input("Tasa por periodo i (%):", min_value=0.0, value=1.5, step=0.1, format="%.4f", key="an_i")
            with p3:
                n_an = int(st.number_input("Número de pagos (n):", min_value=1, max_value=600, value=12, step=1, key="an_n"))
            with p4:
                k_dif = int(st.number_input("Periodos de diferimiento (k ≥ 0):", min_value=0, max_value=120, value=0, step=1, key="an_k"))

            i_an = i_an_pct / 100.0
            factor_ant = (1.0 + i_an) if modalidad_an.startswith("Anticipada") else 1.0
            factor_dif = (1.0 + i_an) ** (-k_dif)

            # Manejo exacto de tasa = 0% (Fix de auditoría)
            if abs(i_an) < 1e-12:
                if incog_an.startswith("Valor Presente"):
                    R_res = R_an
                    vp_res = R_an * n_an
                    vf_res = R_an * n_an
                elif "Valor Presente" in incog_an:
                    R_res = VP_conocido / n_an
                    vp_res = VP_conocido
                    vf_res = VP_conocido
                else:
                    R_res = VF_conocido / n_an
                    vp_res = VF_conocido
                    vf_res = VF_conocido
            else:
                a_n_i = (1.0 - (1.0 + i_an) ** (-n_an)) / i_an
                s_n_i = (((1.0 + i_an) ** n_an) - 1.0) / i_an
                if incog_an.startswith("Valor Presente"):
                    R_res = R_an
                    vp_res = R_an * a_n_i * factor_ant * factor_dif
                    vf_res = R_an * s_n_i * factor_ant
                elif "Valor Presente" in incog_an:
                    R_res = VP_conocido / (a_n_i * factor_ant * factor_dif)
                    vp_res = VP_conocido
                    vf_res = R_res * s_n_i * factor_ant
                else:
                    R_res = VF_conocido / (s_n_i * factor_ant)
                    vf_res = VF_conocido
                    vp_res = R_res * a_n_i * factor_ant * factor_dif

            st.divider()
            m1, m2, m3, m4 = st.columns(4, gap="medium")
            m1.metric("Renta Periódica (R)", f"${R_res:,.2f}")
            m2.metric("Valor Presente (VP)", f"${vp_res:,.2f}")
            m3.metric("Valor Futuro / Monto (VF)", f"${vf_res:,.2f}")
            m4.metric("Total de Pagos (n · R)", f"${n_an * R_res:,.2f}")

            st.latex(
                r"VP = R \cdot \frac{1 - (1+i)^{-n}}{i}"
                + (r"(1+i)" if modalidad_an.startswith("Anticipada") else "")
                + (r"(1+i)^{-k}" if k_dif > 0 else "")
                + r", \qquad VF = R \cdot \frac{(1+i)^n - 1}{i}"
                + (r"(1+i)" if modalidad_an.startswith("Anticipada") else "")
            )

    with sub_an2:
        with st.container(border=True):
            header_tarjeta("Anualidades Variables (Progresión Aritmética, Geométrica) y Perpetuidades")
            tipo_var = st.radio(
                "Seleccione el modelo actuarial:",
                [
                    "1. Progresión Aritmética (Primer pago P, incremento constante Q en cada periodo)",
                    "2. Progresión Geométrica (Primer pago R₁, crecimiento porcentual g % en cada periodo)",
                    "3. Perpetuidad (Pagos infinitos constantes o crecientes a tasa g < i)",
                ],
                key="an_var_tipo",
            )
            cv1, cv2, cv3, cv4 = st.columns(4, gap="medium")
            p_base = cv1.number_input("Primer pago P / R₁ ($):", min_value=0.01, value=1000.0, step=100.0, format="%.2f", key="av_P")
            i_v = cv2.number_input("Tasa por periodo i (%):", min_value=0.01, value=2.0, step=0.25, format="%.4f", key="av_i") / 100.0
            if not tipo_var.startswith("3."):
                n_v = int(cv3.number_input("Número de pagos (n):", min_value=1, max_value=360, value=12, step=1, key="av_n"))

            if tipo_var.startswith("1."):
                Q_inc = cv4.number_input("Incremento aritmético Q ($):", value=200.0, step=50.0, format="%.2f", key="av_Q")
                a_ni = (1.0 - (1.0 + i_v) ** (-n_v)) / i_v
                vp_var = p_base * a_ni + (Q_inc / i_v) * (a_ni - n_v * ((1.0 + i_v) ** (-n_v)))
                vf_var = vp_var * ((1.0 + i_v) ** n_v)
                ult_pago = p_base + (n_v - 1) * Q_inc

                st.divider()
                v1, v2, v3 = st.columns(3, gap="medium")
                v1.metric("Valor Presente (VP)", f"${vp_var:,.2f}")
                v2.metric("Valor Futuro (VF)", f"${vf_var:,.2f}")
                v3.metric("Último Pago en t = n", f"${ult_pago:,.2f}")
                st.latex(r"VP = P\,a_{\overline{n}|i} + \frac{Q}{i}\left(a_{\overline{n}|i} - n(1+i)^{-n}\right)")

            elif tipo_var.startswith("2."):
                g_v = cv4.number_input("Crecimiento geométrico g (%):", value=1.0, step=0.25, format="%.4f", key="av_g") / 100.0
                if abs(i_v - g_v) < 1e-10:
                    vp_var = n_v * p_base / (1.0 + i_v)
                else:
                    vp_var = p_base * (1.0 - ((1.0 + g_v) / (1.0 + i_v)) ** n_v) / (i_v - g_v)
                vf_var = vp_var * ((1.0 + i_v) ** n_v)
                ult_pago = p_base * ((1.0 + g_v) ** (n_v - 1))

                st.divider()
                v1, v2, v3 = st.columns(3, gap="medium")
                v1.metric("Valor Presente (VP)", f"${vp_var:,.2f}")
                v2.metric("Valor Futuro (VF)", f"${vf_var:,.2f}")
                v3.metric("Último Pago en t = n", f"${ult_pago:,.2f}")
                st.latex(r"VP = R_1 \cdot \frac{1 - \left(\frac{1+g}{1+i}\right)^n}{i - g}")

            else:
                g_perp = cv3.number_input("Crecimiento perpetuo g (% < i):", min_value=0.0, value=0.5, step=0.1, format="%.4f", key="av_gp") / 100.0
                if g_perp >= i_v:
                    st.error("⛔ En una perpetuidad en crecimiento, la tasa de descuento i debe ser estrictamente mayor que g.")
                else:
                    vp_perp = p_base / (i_v - g_perp)
                    vp_perp_ant = vp_perp * (1.0 + i_v)
                    st.divider()
                    v1, v2 = st.columns(2, gap="medium")
                    v1.metric("Valor Presente Perpetuidad Vencida", f"${vp_perp:,.2f}")
                    v2.metric("Valor Presente Perpetuidad Anticipada", f"${vp_perp_ant:,.2f}")
                    st.latex(r"VP_{\infty} = \frac{R_1}{i - g}")

    with sub_an3:
        with st.container(border=True):
            header_tarjeta("Generador de Tabla de Amortización (Francés, Alemán y Americano)")
            ca1, ca2, ca3, ca4 = st.columns(4, gap="medium")
            monto_cred = ca1.number_input("Importe del Crédito ($):", min_value=1.0, value=50000.0, step=1000.0, format="%.2f", key="am_C")
            tasa_cred_pct = ca2.number_input("Tasa Efectiva por Periodo (%):", min_value=0.0, value=2.0, step=0.25, format="%.4f", key="am_i")
            plazo_cred = int(ca3.number_input("Plazo (n periodos):", min_value=1, max_value=360, value=12, step=1, key="am_n"))
            sistema_am = ca4.selectbox(
                "Sistema de Amortización:",
                ["Francés (Cuota Constante)", "Alemán (Amortización Constante)", "Americano (Intereses periódicos + Capital al final)"],
                key="am_sis",
            )

            i_c = tasa_cred_pct / 100.0
            filas_am = [{
                "Periodo": 0,
                "Pago Total ($)": 0.0,
                "Intereses ($)": 0.0,
                "Amortización de Capital ($)": 0.0,
                "Capital Amortizado Acum. ($)": 0.0,
                "Saldo Insoluto ($)": float(monto_cred),
            }]
            saldo = float(monto_cred)
            acum_cap = 0.0

            if sistema_am.startswith("Francés"):
                pago_fijo = (monto_cred / plazo_cred) if abs(i_c) < 1e-12 else (monto_cred * i_c / (1.0 - (1.0 + i_c) ** (-plazo_cred)))
                for k in range(1, plazo_cred + 1):
                    interes_k = saldo * i_c
                    abono_k = pago_fijo - interes_k
                    saldo = max(0.0, saldo - abono_k)
                    acum_cap += abono_k
                    filas_am.append({
                        "Periodo": k,
                        "Pago Total ($)": pago_fijo,
                        "Intereses ($)": interes_k,
                        "Amortización de Capital ($)": abono_k,
                        "Capital Amortizado Acum. ($)": acum_cap,
                        "Saldo Insoluto ($)": saldo,
                    })
            elif sistema_am.startswith("Alemán"):
                abono_fijo = monto_cred / plazo_cred
                for k in range(1, plazo_cred + 1):
                    interes_k = saldo * i_c
                    pago_k = abono_fijo + interes_k
                    saldo = max(0.0, saldo - abono_fijo)
                    acum_cap += abono_fijo
                    filas_am.append({
                        "Periodo": k,
                        "Pago Total ($)": pago_k,
                        "Intereses ($)": interes_k,
                        "Amortización de Capital ($)": abono_fijo,
                        "Capital Amortizado Acum. ($)": acum_cap,
                        "Saldo Insoluto ($)": saldo,
                    })
            else:
                for k in range(1, plazo_cred + 1):
                    interes_k = saldo * i_c
                    abono_k = monto_cred if k == plazo_cred else 0.0
                    pago_k = interes_k + abono_k
                    saldo = max(0.0, saldo - abono_k)
                    acum_cap += abono_k
                    filas_am.append({
                        "Periodo": k,
                        "Pago Total ($)": pago_k,
                        "Intereses ($)": interes_k,
                        "Amortización de Capital ($)": abono_k,
                        "Capital Amortizado Acum. ($)": acum_cap,
                        "Saldo Insoluto ($)": saldo,
                    })

            df_am = pd.DataFrame(filas_am)
            tot_pagado = float(df_am["Pago Total ($)"].sum())
            tot_int = float(df_am["Intereses ($)"].sum())

            st.divider()
            k1, k2, k3 = st.columns(3, gap="medium")
            k1.metric("Primera Cuota Periódica", f"${df_am.iloc[1]['Pago Total ($)']:,.2f}")
            k2.metric("Total de Intereses Pagados", f"${tot_int:,.2f}")
            k3.metric("Desembolso Total Acumulado", f"${tot_pagado:,.2f}")

            fig_am, ax_am = _crear_grafica_amplia(
                titulo="Evolución del Saldo Insoluto vs. Capital Amortizado Acumulado"
            )
            ax_am.plot(df_am["Periodo"], df_am["Saldo Insoluto ($)"], "o-", color=AZUL, lw=2.4, ms=5, label="Saldo Insoluto ($)")
            ax_am.plot(df_am["Periodo"], df_am["Capital Amortizado Acum. ($)"], "s--", color=VERDE, lw=2.2, ms=4.5, label="Capital Amortizado Acumulado ($)")
            ax_am.legend(fontsize=9.5, loc="center right")
            mostrar_figura_segura(fig_am)

            subheader_tarjeta("Tabla de Amortización Completa")
            st.dataframe(
                df_am.style.format({
                    "Pago Total ($)": "${:,.2f}",
                    "Intereses ($)": "${:,.2f}",
                    "Amortización de Capital ($)": "${:,.2f}",
                    "Capital Amortizado Acum. ($)": "${:,.2f}",
                    "Saldo Insoluto ($)": "${:,.2f}",
                }),
                use_container_width=True,
                hide_index=True,
            )
            csv_bytes = df_am.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Descargar Tabla de Amortización en CSV",
                data=csv_bytes,
                file_name="tabla_amortizacion_mathesis.csv",
                mime="text/csv",
                use_container_width=True,
            )

# ------------------------------------------------------------------------------
# PESTAÑA 6: VALUACIÓN ACTUARIAL DE BONOS Y EVALUACIÓN DE PROYECTOS (VPN / TIR)
# ------------------------------------------------------------------------------
with tab_bonos:
    t_bono, t_vpn = st.tabs([
        "📜 1. Valuación de Bonos, Duración de Macaulay y Convexidad",
        "🚀 2. Evaluación de Proyectos de Inversión (VPN y TIR)",
    ])

    with t_bono:
        with st.container(border=True):
            header_tarjeta("Valuación de Bonos / Obligaciones y Sensibilidad a Tasas de Interés")
            b1, b2, b3, b4 = st.columns(4, gap="medium")
            vn_bono = b1.number_input("Valor Nominal / Redención F ($):", min_value=10.0, value=1000.0, step=100.0, format="%.2f", key="bn_F")
            tasa_cupon_pct = b2.number_input("Tasa Cupón por periodo r (%):", min_value=0.0, value=5.0, step=0.25, format="%.4f", key="bn_r")
            ytm_pct = b3.number_input("Tasa de Rendimiento YTM por periodo y (%):", min_value=0.01, value=4.0, step=0.25, format="%.4f", key="bn_y")
            n_cupones = int(b4.number_input("Cupones restantes (n):", min_value=1, max_value=120, value=10, step=1, key="bn_n"))

            cupon_C = vn_bono * (tasa_cupon_pct / 100.0)
            y_b = ytm_pct / 100.0

            ts_b = np.arange(1, n_cupones + 1, dtype=float)
            flujos_b = np.full(n_cupones, cupon_C, dtype=float)
            flujos_b[-1] += vn_bono
            factores_desc = (1.0 + y_b) ** (-ts_b)
            vp_flujos = flujos_b * factores_desc

            precio_bono = float(np.sum(vp_flujos))
            dur_macaulay = float(np.sum(ts_b * vp_flujos) / precio_bono)
            dur_modificada = dur_macaulay / (1.0 + y_b)
            convexidad = float(np.sum(ts_b * (ts_b + 1.0) * vp_flujos) / (precio_bono * ((1.0 + y_b) ** 2)))

            tipo_compra = (
                "SOBRE PAR (Con Prima: Cupón > YTM)" if precio_bono > vn_bono + 1e-4
                else "BAJO PAR (Con Descuento: Cupón < YTM)" if precio_bono < vn_bono - 1e-4
                else "A LA PAR (Precio = Valor Nominal)"
            )

            st.divider()
            m1, m2, m3, m4 = st.columns(4, gap="medium")
            m1.metric("Precio del Bono (P)", f"${precio_bono:,.2f}")
            m2.metric("Duración de Macaulay (D)", f"{dur_macaulay:.4f} per.")
            m3.metric("Duración Modificada (D*)", f"{dur_modificada:.4f}")
            m4.metric("Convexidad (C)", f"{convexidad:.4f}")

            st.info(f"**Diagnóstico de Emisión:** El bono cotiza **{tipo_compra}** (Cupón periódico = `${cupon_C:,.2f}`).")
            st.latex(
                r"P = C\,a_{\overline{n}|y} + F(1+y)^{-n}, \qquad "
                r"D_{\text{Mac}} = \frac{1}{P}\sum_{t=1}^{n} t\,\frac{CF_t}{(1+y)^t}, \qquad "
                r"\frac{\Delta P}{P} \approx -D^* \Delta y + \frac{1}{2}\text{Conv}\cdot(\Delta y)^2"
            )

            # Curva Precio-Rendimiento a ancho completo
            ys_grid = np.linspace(max(0.002, y_b * 0.25), y_b * 2.5, 160)
            precios_grid = [
                sum(flujos_b[k] * ((1.0 + y_g) ** (-(k + 1))) for k in range(n_cupones))
                for y_g in ys_grid
            ]
            fig_b, ax_b = _crear_grafica_amplia(
                titulo="Curva Precio vs. Rendimiento (Convexidad del Bono)",
                xlabel="Tasa de Rendimiento por Periodo YTM (%)",
                ylabel="Precio del Bono ($)",
            )
            ax_b.plot(ys_grid * 100, precios_grid, color=AZUL, lw=2.5, label="Precio exacto P(y)")
            ax_b.plot([ytm_pct], [precio_bono], "o", color=ROJO, ms=8, label=f"Punto actual (y={ytm_pct:.2f}%, P=${precio_bono:,.2f})")
            ax_b.axhline(vn_bono, color=OSCURO, ls=":", lw=1.2, label=f"Valor Nominal (${vn_bono:,.0f})")
            ax_b.legend(fontsize=9.5)
            mostrar_figura_segura(fig_b)

    with t_vpn:
        with st.container(border=True):
            header_tarjeta("Evaluación de Proyectos de Inversión: Valor Presente Neto (VPN) y Tasa Interna de Retorno (TIR)")

            v1, v2, v3 = st.columns([1, 2, 1], gap="medium")
            with v1:
                inv_ini = st.number_input("Inversión Inicial CF₀ ($):", min_value=0.0, value=10000.0, step=500.0, format="%.2f", key="vpn_cf0")
            with v2:
                flujos_str = st.text_input("Flujos netos CF₁, CF₂, …, CFₙ separados por comas ($):", value="3000, 4000, 4500, 5000", key="vpn_cfs")
            with v3:
                tasa_k_pct = st.number_input("Tasa de descuento TREMA k (%):", min_value=0.0, value=12.0, step=0.5, format="%.2f", key="vpn_k")

            try:
                cfs = [-float(inv_ini)] + [float(x.strip()) for x in flujos_str.split(",") if x.strip()]
                k_d = tasa_k_pct / 100.0
                vpn_val = sum(cf / ((1.0 + k_d) ** t) for t, cf in enumerate(cfs))
                vp_ingresos = sum(cf / ((1.0 + k_d) ** t) for t, cf in enumerate(cfs) if t >= 1)
                ir_val = (vp_ingresos / inv_ini) if inv_ini > 0 else 0.0

                raices_poly = np.roots(cfs[::-1])
                raices_reales = [r.real for r in raices_poly if abs(r.imag) < 1e-7 and r.real > 0]
                tir_val = (1.0 / raices_reales[0] - 1.0) if raices_reales else None

                st.divider()
                p1, p2, p3 = st.columns(3, gap="medium")
                p1.metric("Valor Presente Neto (VPN)", f"${vpn_val:,.2f}", delta="Proyecto Viable (VPN > 0)" if vpn_val > 0 else "No Viable (VPN < 0)")
                p2.metric("Tasa Interna de Retorno (TIR)", f"{tir_val * 100:.4f}%" if tir_val is not None else "No única / N/D")
                p3.metric("Índice de Rentabilidad (IR = VP / CF₀)", f"{ir_val:.4f}")

                tasas_grid = np.linspace(0.0, 0.50, 180)
                vpns_grid = [sum(cf / ((1.0 + r_g) ** t) for t, cf in enumerate(cfs)) for r_g in tasas_grid]
                fig_v, ax_v = _crear_grafica_amplia(
                    titulo="Perfil del Valor Presente Neto (VPN vs. Tasa de Descuento k)",
                    xlabel="Tasa de Descuento k (%)",
                    ylabel="VPN ($)",
                )
                ax_v.plot(tasas_grid * 100, vpns_grid, color=AZUL, lw=2.5, label="Curva VPN(k)")
                ax_v.axhline(0, color=OSCURO, lw=1.3, ls="--")
                ax_v.plot([tasa_k_pct], [vpn_val], "o", color=VERDE if vpn_val >= 0 else ROJO, ms=8.5, label=f"TREMA ({tasa_k_pct:.2f}% → ${vpn_val:,.2f})")
                if tir_val is not None and 0 <= tir_val <= 0.50:
                    ax_v.plot([tir_val * 100], [0], "o", color=NARANJA, ms=8.5, label=f"TIR = {tir_val * 100:.2f}% (VPN = $0)")
                ax_v.legend(fontsize=9.5)
                mostrar_figura_segura(fig_v)
            except Exception as e:
                st.error("Verifique el formato de los flujos de efectivo separados por comas: " + str(e))
