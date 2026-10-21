# pages/6_Matematicas_Financieras.py
import datetime
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.ticker import AutoMinorLocator, FuncFormatter

st.set_page_config(page_title="Matemáticas Financieras - MATHESIS", page_icon="📈", layout="wide")

from estilos import cargar_estilos_globales, encabezado_pagina, header_tarjeta, subheader_tarjeta  # noqa: E402
from utils import gestionar_inventario_sidebar, inicializar_estado, mostrar_figura_segura  # noqa: E402

cargar_estilos_globales()
inicializar_estado()

AZUL = "#0369a1"
NARANJA = "#ea580c"
VERDE = "#15803d"
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

NOMBRE_PERIODO = {
    "Anual": ("año", "años"),
    "Semestral": ("semestre", "semestres"),
    "Cuatrimestral": ("cuatrimestre", "cuatrimestres"),
    "Trimestral": ("trimestre", "trimestres"),
    "Bimestral": ("bimestre", "bimestres"),
    "Mensual": ("mes", "meses"),
    "Quincenal": ("quincena", "quincenas"),
    "Semanal": ("semana", "semanas"),
    "Diaria (360)": ("día", "días"),
    "Diaria (365)": ("día", "días"),
}


def _crear_fig_fin(w=7.0, h=4.3, titulo="", xlabel="Periodo", ylabel="Monto ($)"):
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
    ax.tick_params(colors=OSCURO, labelsize=8.5)
    ax.set_xlabel(xlabel, color=OSCURO, fontweight="bold", fontsize=9.5)
    ax.set_ylabel(ylabel, color=OSCURO, fontweight="bold", fontsize=9.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:,.0f}"))
    if titulo:
        ax.set_title(titulo, color=OSCURO, fontweight="bold", fontsize=10.5, pad=10)
    return fig, ax


def _dias_30_360_isda(d1: datetime.date, d2: datetime.date) -> int:
    """Convención estándar 30/360 (ISDA / US Bond Basis): corrige bordes de día 31 y fin de febrero."""
    y1, m1, day1 = d1.year, d1.month, d1.day
    y2, m2, day2 = d2.year, d2.month, d2.day

    # Ajuste de fin de febrero
     es_feb1 = m1 == 2 and (day1 == 29 or (day1 == 28 and not (y1 % 4 == 0 and (y1 % 100 != 0 or y1 % 400 == 0))))
    es_feb2 = m2 == 2 and (day2 == 29 or (day2 == 28 and not (y2 % 4 == 0 and (y2 % 100 != 0 or y2 % 400 == 0))))
    if es_feb1 and es_feb2:
        day2 = 30
    if es_feb1:
        day1 = 30

    if day1 == 31:
        day1 = 30
    if day2 == 31 and day1 == 30:
        day2 = 30

    return (y2 - y1) * 360 + (m2 - m1) * 30 + (day2 - day1)


def _render_escenario_sidebar(nom, datos):
    st.caption(f"Tipo: {datos['tipo']} | Capital: ${datos['C']:,.2f} | Tasa: {datos['tasa']*100:.2f}% | Plazo: {datos['n']}")


# ==============================================================================
# ENCABEZADO Y BARRA LATERAL
# ==============================================================================
encabezado_pagina(
    "📈 Módulo de Matemáticas Financieras y Valuación Actuarial",
    "Interés simple, compuesto y continuo, tasas equivalentes, anualidades constantes y variables, amortización, bonos (Duración y Convexidad) y VPN/TIR.",
)

gestionar_inventario_sidebar(
    clave_estado="mis_inversiones",
    titulo="💼 Escenarios Guardados",
    etiqueta_item="Escenario:",
    render_fn=_render_escenario_sidebar,
)

# ==============================================================================
# PESTAÑAS PRINCIPALES
# ==============================================================================
tab_interes, tab_tasas, tab_anualidades, tab_amort, tab_bonos = st.tabs([
    "💰 1. Interés y Comparador",
    "🔄 2. Tasas y Conteo de Días",
    "📅 3. Anualidades (Constantes y Variables)",
    "🏦 4. Amortización y Fondos",
    "📜 5. Valuación de Bonos y VPN / TIR",
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: Interés Simple, Compuesto, Continuo y Comparador
# ------------------------------------------------------------------------------
with tab_interes:
    col_i1, col_i2 = st.columns([1.05, 1.3], gap="large")
    with col_i1:
        with st.container(border=True):
            header_tarjeta("1. Calculadora del Valor del Dinero en el Tiempo")
            regimen = st.radio(
                "Régimen de capitalización:",
                ["Interés Compuesto", "Interés Simple", "Capitalización Continua (Fuerza de Interés δ)"],
                horizontal=True,
                key="fin_regimen",
            )
            incognita = st.selectbox(
                "Variable a despejar:",
                ["Monto Futuro (M / VF)", "Capital Inicial / Valor Presente (C / VP)", "Tasa de Interés por periodo (i / δ)", "Número de periodos (n)"],
                key="fin_incog",
            )

            c_in1, c_in2 = st.columns(2)
            C_val = M_val = i_val = n_val = 0.0

            if incognita != "Capital Inicial / Valor Presente (C / VP)":
                C_val = c_in1.number_input("Capital Inicial C ($):", min_value=0.01, value=10000.0, step=500.0, key="fin_C")
            if incognita != "Monto Futuro (M / VF)":
                M_val = c_in1.number_input("Monto Futuro M ($):", min_value=0.01, value=16000.0, step=500.0, key="fin_M")
            if incognita != "Tasa de Interés por periodo (i / δ)":
                i_pct = c_in2.number_input("Tasa por periodo (%):", min_value=0.0, value=8.0, step=0.5, key="fin_i")
                i_val = i_pct / 100.0
            if incognita != "Número de periodos (n)":
                n_val = c_in2.number_input("Plazo (n periodos):", min_value=0.01, value=6.0, step=1.0, key="fin_n")

            if st.button("🧮 Calcular y Graficar Evolución", use_container_width=True, key="btn_calc_int"):
                error_fin = False
                if incognita == "Monto Futuro (M / VF)":
                    if regimen == "Interés Compuesto":
                        M_val = C_val * ((1.0 + i_val) ** n_val)
                    elif regimen == "Interés Simple":
                        M_val = C_val * (1.0 + i_val * n_val)
                    else:
                        M_val = C_val * math.exp(i_val * n_val)
                elif incognita == "Capital Inicial / Valor Presente (C / VP)":
                    if regimen == "Interés Compuesto":
                        C_val = M_val / ((1.0 + i_val) ** n_val)
                    elif regimen == "Interés Simple":
                        C_val = M_val / (1.0 + i_val * n_val)
                    else:
                        C_val = M_val * math.exp(-i_val * n_val)
                elif incognita == "Tasa de Interés por periodo (i / δ)":
                    if M_val < C_val:
                        st.error("El Monto Futuro debe ser mayor o igual al Capital Inicial para tasas no negativas.")
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
                        st.error("Para despejar el plazo n se requiere tasa > 0 y M > C.")
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
                st.divider()
                k1, k2, k3 = st.columns(3)
                k1.metric("Capital Inicial (C)", f"${r_f['C']:,.2f}")
                k2.metric("Monto Final (M)", f"${r_f['M']:,.2f}")
                k3.metric("Interés Generado (I)", f"${r_f['I']:,.2f}")
                st.caption(f"Tasa: **{r_f['tasa']*100:.4f}%** por periodo · Plazo: **{r_f['n']:.2f}** periodos ({r_f['tipo']})")

                c_s1, c_s2 = st.columns([2, 1])
                with c_s1:
                    nom_esc = st.text_input("Guardar escenario para comparar:", value="ESC_1", key="nom_esc_fin").upper().strip()
                with c_s2:
                    st.write("")
                    if st.button("💾 Guardar", key="btn_save_esc_fin", use_container_width=True):
                        if nom_esc:
                            st.session_state.mis_inversiones[nom_esc] = r_f.copy()
                            st.rerun()

    with col_i2:
        with st.container(border=True):
            header_tarjeta("2. Curva de Acumulación y Comparador de Escenarios")
            t_comp1, t_comp2 = st.tabs(["📈 Simple vs. Compuesto vs. Continuo", "⚖️ Comparador de Escenarios Guardados"])

            with t_comp1:
                r_base = st.session_state.get("ult_fin_res", {"C": 10000.0, "tasa": 0.08, "n": 6.0})
                ts = np.linspace(0, max(float(r_base["n"]), 1.0), 200)
                c0, i0 = r_base["C"], r_base["tasa"]
                y_simp = c0 * (1.0 + i0 * ts)
                y_comp = c0 * ((1.0 + i0) ** ts)
                y_cont = c0 * np.exp(i0 * ts)

                fig, ax = _crear_fig_fin(titulo=f"Comparación de Regímenes (C = ${c0:,.0f}, Tasa = {i0*100:.2f}%)")
                ax.plot(ts, y_simp, color=VERDE, lw=2.0, ls="--", label="Interés Simple: C(1 + i·t)")
                ax.plot(ts, y_comp, color=AZUL, lw=2.5, label="Interés Compuesto: C(1 + i)ᵗ")
                ax.plot(ts, y_cont, color=NARANJA, lw=2.0, ls=":", label="Capitalización Continua: C·e^(δt)")
                ax.legend(fontsize=8.5, loc="upper left")
                mostrar_figura_segura(fig)

            with t_comp2:
                if not st.session_state.mis_inversiones:
                    st.info("Guarde uno o más escenarios a la izquierda para compararlos gráficamente.")
                else:
                    fig_c, ax_c = _crear_fig_fin(titulo="Comparativa de Escenarios en Memoria")
                    colores_e = [AZUL, NARANJA, VERDE, ROJO, MORADO]
                    max_n = max(float(d["n"]) for d in st.session_state.mis_inversiones.values())
                    for idx_e, (nom_e, d_e) in enumerate(st.session_state.mis_inversiones.items()):
                        t_e = np.linspace(0, float(d_e["n"]), 150)
                        if d_e["tipo"] == "Interés Compuesto":
                            y_e = d_e["C"] * ((1.0 + d_e["tasa"]) ** t_e)
                        elif d_e["tipo"] == "Interés Simple":
                            y_e = d_e["C"] * (1.0 + d_e["tasa"] * t_e)
                        else:
                            y_e = d_e["C"] * np.exp(d_e["tasa"] * t_e)
                        col_e = colores_e[idx_e % len(colores_e)]
                        ax_c.plot(t_e, y_e, color=col_e, lw=2.3, label=f"{nom_e} (${d_e['M']:,.0f})")
                    ax_c.set_xlim(0, max_n * 1.05)
                    ax_c.legend(fontsize=8.5, loc="upper left")
                    mostrar_figura_segura(fig_c)

# ------------------------------------------------------------------------------
# PESTAÑA 2: Conversión de Tasas y Conteo Bancario de Días (30/360 ISDA)
# ------------------------------------------------------------------------------
with tab_tasas:
    c_t1, c_t2 = st.columns(2, gap="large")

    with c_t1:
        with st.container(border=True):
            header_tarjeta("1. Equivalencia de Tasas, Fuerza de Interés e Inflación")
            tasa_in_pct = st.number_input("Valor de la tasa de entrada (%):", min_value=0.0, value=12.0, step=0.25, key="tasa_conv_in")
            tipo_tasa_in = st.radio(
                "La tasa ingresada es:",
                ["Nominal Anual (j^(m))", "Efectiva del Periodo (i_m)", "Efectiva Anual (TEA / i)"],
                horizontal=True,
                key="tipo_tasa_in",
            )
            frec_origen = st.selectbox("Capitalización de origen (m):", list(FRECUENCIAS.keys()), index=5, key="frec_orig")
            frec_destino = st.selectbox("Convertir a frecuencia destino (k):", list(FRECUENCIAS.keys()), index=3, key="frec_dest")
            inflacion_pct = st.number_input("Tasa de inflación anual π (%) [para Tasa Real de Fisher]:", min_value=0.0, value=4.5, step=0.25, key="inf_fisher")

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

             sustantivo_or = NOMBRE_PERIODO[frec_origen][0]
            sustantivo_de = NOMBRE_PERIODO[frec_destino][0]

            st.markdown(
                f"| Medida Actuarial / Financiera | Valor Equivalente |\n|---|---|\n"
                f"| **Tasa Efectiva por {sustantivo_or} ($i_{{{m_or}}}$)** | `{i_per_or * 100:.6f}%` por {sustantivo_or} |\n"
                f"| **Tasa Efectiva Anual (TEA, $1+i = (1+i_m)^m$)** | **`{tea * 100:.6f}%` anual** |\n"
                f"| **Tasa Efectiva por {sustantivo_de} ($i_{{{m_de}}}$)** | **`{i_per_dest * 100:.6f}%` por {sustantivo_de}** |\n"
                f"| **Tasa Nominal Anual capitalizable {frec_destino.lower()} ($j^{{({m_de})}}$)** | **`{j_nom_dest * 100:.6f}%` anual** |\n"
                f"| **Fuerza de Interés instantánea ($\\delta = \\ln(1+i)$)** | `{delta_cont * 100:.6f}%` continua |\n"
                f"| **Tasa Real neta de inflación (Ecuación de Fisher)** | `{tasa_real * 100:.6f}%` real anual |"
            )

    with c_t2:
        with st.container(border=True):
            header_tarjeta("2. Cálculo de Plazos y Convenciones Bancarias de Días")
            st.caption("Comparación exacta entre tiempo real (Actual) y tiempo comercial 30/360 (Norma ISDA).")
            f_ini = st.date_input("Fecha de inicio de la operación:", value=datetime.date(2026, 3, 31), key="f_ini_d")
            f_fin = st.date_input("Fecha de vencimiento:", value=datetime.date(2026, 4, 1), key="f_fin_d")

            if f_fin < f_ini:
                st.error("La fecha de vencimiento debe ser posterior o igual a la fecha de inicio.")
            else:
                dias_exactos = (f_fin - f_ini).days
                dias_360 = _dias_30_360_isda(f_ini, f_fin)

                d_m1, d_m2 = st.columns(2)
                d_m1.metric("Días Exactos (Calendario Real)", f"{dias_exactos:,} días")
                d_m2.metric("Días Comerciales (30/360 ISDA)", f"{dias_360:,} días")

                st.markdown(
                    f"| Convención del Mercado | Fracción de Año ($t$) | Uso Habitual |\n|---|---|---|\n"
                    f"| **Actual / Actual (Exacto / 365)** | `{dias_exactos / 365.0:.6f}` | Bonos gubernamentales y pagarés bancarios |\n"
                    f"| **Actual / 360 ( Bancario / Mercado de Dinero )** | `{dias_exactos / 360.0:.6f}` | CETES, TIIE, créditos corporativos |\n"
                    f"| **30 / 360 (ISDA / Bonos Corporativos)** | `{dias_360 / 360.0:.6f}` | Obligaciones corporativas y swaps |"
                )

# ------------------------------------------------------------------------------
# PESTAÑA 3: Anualidades Constantes, Variables y Perpetuidades
# ------------------------------------------------------------------------------
with tab_anualidades:
    with st.container(border=True):
        header_tarjeta("Valuación de Anualidades Constantes, Variables y Perpetuidades")
        t_an_const, t_an_var = st.tabs([
            "📅 1. Anualidades Constantes (Vencidas, Anticipadas, Diferidas)",
            "📈 2. Anualidades Variables (Progresión Aritmética y Geométrica) y Perpetuidades",
        ])

        with t_an_const:
            c_a1, c_a2 = st.columns([1.05, 1.25])
            with c_a1:
                modalidad_an = st.radio("Modalidad de pago:", ["Vencida (Ordinaria)", "Anticipada (al inicio de cada periodo)"], horizontal=True, key="an_mod")
                incog_an = st.selectbox(
                    "Calcular:",
                    ["Valor Presente (VP / A)", "Valor Futuro / Monto (VF / S)", "Pago Periódico / Renta (R)"],
                    key="an_incog",
                )
                R_an = st.number_input("Renta periódica R ($):", min_value=0.01, value=2500.0, step=100.0, key="an_R") if incog_an != "Pago Periódico / Renta (R)" else 0.0
                VP_in = st.number_input("Capital / Valor Presente conocido ($):", min_value=0.01, value=25000.0, step=500.0, key="an_VP_in") if incog_an == "Pago Periódico / Renta (R)" else 0.0
                i_an_pct = st.number_input("Tasa efectiva por periodo i (%):", min_value=0.0, value=1.5, step=0.1, key="an_i")
                n_an = int(st.number_input("Número de pagos (n):", min_value=1, max_value=600, value=12, step=1, key="an_n"))
                k_dif = int(st.number_input("Periodos de gracia / diferimiento (k ≥ 0):", min_value=0, max_value=120, value=0, step=1, key="an_k"))

                i_an = i_an_pct / 100.0
                factor_ant = (1.0 + i_an) if modalidad_an.startswith("Anticipada") else 1.0
                factor_dif = (1.0 + i_an) ** (-k_dif)

                # Soporte exacto para tasa = 0% (Fix de auditoría)
                if abs(i_an) < 1e-12:
                    if incog_an == "Pago Periódico / Renta (R)":
                        R_res = VP_in / n_an
                        vp_res = VP_in
                        vf_res = VP_in
                    else:
                        R_res = R_an
                        vp_res = R_an * n_an
                        vf_res = R_an * n_an
                else:
                    a_n_i = (1.0 - (1.0 + i_an) ** (-n_an)) / i_an
                    s_n_i = (((1.0 + i_an) ** n_an) - 1.0) / i_an
                    if incog_an == "Pago Periódico / Renta (R)":
                        R_res = VP_in / (a_n_i * factor_ant * factor_dif)
                        vp_res = VP_in
                        vf_res = R_res * s_n_i * factor_ant
                    else:
                        R_res = R_an
                        vp_res = R_an * a_n_i * factor_ant * factor_dif
                        vf_res = R_an * s_n_i * factor_ant

            with c_a2:
                m1, m2, m3 = st.columns(3)
                m1.metric("Valor Presente (VP)", f"${vp_res:,.2f}")
                m2.metric("Valor Futuro (VF)", f"${vf_res:,.2f}")
                m3.metric("Renta Periódica (R)", f"${R_res:,.2f}")

                st.latex(
                    r"VP = R \cdot \frac{1 - (1+i)^{-n}}{i}"
                    + (r"\cdot (1+i)" if modalidad_an.startswith("Anticipada") else "")
                    + (r"\cdot (1+i)^{-k}" if k_dif > 0 else "")
                )
                st.info(
                    f"**Total desembolsado ($n \\cdot R$):** `${n_an * R_res:,.2f}` · "
                    f"**Intereses implícitos respecto a VP:** `${max(0.0, n_an * R_res - vp_res):,.2f}`"
                )

        with t_an_var:
            tipo_var = st.radio(
                "Seleccione el modelo de anualidad variable:",
                [
                    "1. Progresión Aritmética (Primer pago P, incremento constante Q por periodo)",
                    "2. Progresión Geométrica (Primer pago R₁, tasa de crecimiento g % por periodo)",
                    "3. Perpetuidad (Pagos infinitos constantes o crecientes)",
                ],
                key="an_var_tipo",
            )
            cv1, cv2, cv3, cv4 = st.columns(4)
            p_base = cv1.number_input("Primer pago P / R₁ ($):", min_value=0.01, value=1000.0, step=100.0, key="av_P")
            i_v = cv2.number_input("Tasa por periodo i (%):", min_value=0.01, value=2.0, step=0.25, key="av_i") / 100.0
            if not tipo_var.startswith("3."):
                n_v = int(cv3.number_input("Número de pagos (n):", min_value=1, max_value=360, value=12, step=1, key="av_n"))
            if tipo_var.startswith("1."):
                Q_inc = cv4.number_input("Incremento aritmético Q ($):", value=200.0, step=50.0, key="av_Q")
                a_ni = (1.0 - (1.0 + i_v) ** (-n_v)) / i_v
                vp_var = p_base * a_ni + (Q_inc / i_v) * (a_ni - n_v * ((1.0 + i_v) ** (-n_v)))
                vf_var = vp_var * ((1.0 + i_v) ** n_v)
                st.latex(r"VP = P\,a_{\overline{n}|i} + \frac{Q}{i}\left(a_{\overline{n}|i} - n(1+i)^{-n}\right)")
                st.success(f"**Valor Presente (VP):** `${vp_var:,.2f}` | **Valor Futuro (VF):** `${vf_var:,.2f}` | **Último pago ($P + (n-1)Q$):** `${p_base + (n_v-1)*Q_inc:,.2f}`")
            elif tipo_var.startswith("2."):
                g_v = cv4.number_input("Crecimiento geométrico g (%):", value=1.0, step=0.25, key="av_g") / 100.0
                if abs(i_v - g_v) < 1e-10:
                    vp_var = n_v * p_base / (1.0 + i_v)
                else:
                    vp_var = p_base * (1.0 - ((1.0 + g_v) / (1.0 + i_v)) ** n_v) / (i_v - g_v)
                vf_var = vp_var * ((1.0 + i_v) ** n_v)
                st.latex(r"VP = R_1 \cdot \frac{1 - \left(\frac{1+g}{1+i}\right)^n}{i - g}")
                st.success(f"**Valor Presente (VP):** `${vp_var:,.2f}` | **Valor Futuro (VF):** `${vf_var:,.2f}`")
            else:
                g_perp = cv3.number_input("Crecimiento perpetuo g (% < i):", min_value=0.0, value=0.5, step=0.1, key="av_gp") / 100.0
                if g_perp >= i_v:
                    st.error("En una perpetuidad creciente (Modelo de Gordon), la tasa de descuento i debe ser estrictamente mayor que el crecimiento g.")
                else:
                    vp_perp = p_base / (i_v - g_perp)
                    st.latex(r"VP_{\infty} = \frac{R_1}{i - g}")
                    st.success(f"**Valor Presente de la Perpetuidad:** `${vp_perp:,.2f}`")

# ------------------------------------------------------------------------------
# PESTAÑA 4: Tablas de Amortización (Francés, Alemán, Americano)
# ------------------------------------------------------------------------------
with tab_amort:
    with st.container(border=True):
        header_tarjeta("Generador de Tablas de Amortización de Créditos")
        ca1, ca2, ca3, ca4 = st.columns(4)
        monto_cred = ca1.number_input("Monto del Préstamo ($):", min_value=1.0, value=50000.0, step=1000.0, key="am_C")
        tasa_cred_pct = ca2.number_input("Tasa Efectiva por Periodo (%):", min_value=0.0, value=2.0, step=0.25, key="am_i")
        plazo_cred = int(ca3.number_input("Número de Periodos (n):", min_value=1, max_value=360, value=12, step=1, key="am_n"))
        sistema_am = ca4.selectbox(
            "Sistema de Amortización:",
            ["Francés (Pagos Iguales)", "Alemán (Abono a Capital Constante)", "Americano (Bullet / Intereses + Capital al final)"],
            key="am_sis",
        )

        i_c = tasa_cred_pct / 100.0
        filas_am = []
        saldo = float(monto_cred)

        if sistema_am.startswith("Francés"):
            pago_fijo = (monto_cred / plazo_cred) if abs(i_c) < 1e-12 else (monto_cred * i_c / (1.0 - (1.0 + i_c) ** (-plazo_cred)))
            for k in range(1, plazo_cred + 1):
                interes_k = saldo * i_c
                abono_k = pago_fijo - interes_k
                saldo = max(0.0, saldo - abono_k)
                filas_am.append({"Periodo": k, "Pago Total": pago_fijo, "Intereses": interes_k, "Abono a Capital": abono_k, "Saldo Insoluto": saldo})
        elif sistema_am.startswith("Alemán"):
            abono_fijo = monto_cred / plazo_cred
            for k in range(1, plazo_cred + 1):
                interes_k = saldo * i_c
                pago_k = abono_fijo + interes_k
                saldo = max(0.0, saldo - abono_fijo)
                filas_am.append({"Periodo": k, "Pago Total": pago_k, "Intereses": interes_k, "Abono a Capital": abono_fijo, "Saldo Insoluto": saldo})
        else:
            for k in range(1, plazo_cred + 1):
                interes_k = saldo * i_c
                abono_k = monto_cred if k == plazo_cred else 0.0
                pago_k = interes_k + abono_k
                saldo = max(0.0, saldo - abono_k)
                filas_am.append({"Periodo": k, "Pago Total": pago_k, "Intereses": interes_k, "Abono a Capital": abono_k, "Saldo Insoluto": saldo})

        df_am = pd.DataFrame(filas_am)
        tot_pagado = float(df_am["Pago Total"].sum())
        tot_int = float(df_am["Intereses"].sum())

        k1, k2, k3 = st.columns(3)
        k1.metric("Primer Pago", f"${df_am.iloc[0]['Pago Total']:,.2f}")
        k2.metric("Total de Intereses Pagados", f"${tot_int:,.2f}")
        k3.metric("Total Pagado (Capital + Intereses)", f"${tot_pagado:,.2f}")

        g_col1, g_col2 = st.columns([1.2, 1.1])
        with g_col1:
            fig_am, ax_am = _crear_fig_fin(titulo="Evolución del Saldo Insoluto y Desglose de Cuotas")
            ax_am.plot(df_am["Periodo"], df_am["Saldo Insoluto"], "o-", color=AZUL, lw=2.2, ms=4, label="Saldo Insoluto")
            ax_am.bar(df_am["Periodo"], df_am["Abono a Capital"], color=VERDE, alpha=0.45, label="Abono a Capital")
            ax_am.bar(df_am["Periodo"], df_am["Intereses"], bottom=df_am["Abono a Capital"], color=NARANJA, alpha=0.55, label="Intereses")
            ax_am.legend(fontsize=8.0)
            mostrar_figura_segura(fig_am)
        with g_col2:
            st.dataframe(
                df_am.style.format({
                    "Pago Total": "${:,.2f}",
                    "Intereses": "${:,.2f}",
                    "Abono a Capital": "${:,.2f}",
                    "Saldo Insoluto": "${:,.2f}",
                }),
                use_container_width=True,
                height=340,
                hide_index=True,
            )

# ------------------------------------------------------------------------------
# PESTAÑA 5: Valuación Actuarial de Bonos (Duración y Convexidad) y VPN / TIR
# ------------------------------------------------------------------------------
with tab_bonos:
    t_bono, t_vpn = st.tabs([
        "📜 1. Valuación de Bonos, Duración de Macaulay y Convexidad",
        "🚀 2. Evaluación de Proyectos (VPN y TIR)",
    ])

    with t_bono:
        with st.container(border=True):
            header_tarjeta("Valuación de Bonos / Obligaciones e Inmunización Actuarial")
            b1, b2, b3, b4 = st.columns(4)
            vn_bono = b1.number_input("Valor Nominal / Redención F ($):", min_value=10.0, value=1000.0, step=100.0, key="bn_F")
            tasa_cupon_pct = b2.number_input("Tasa Cupón por periodo r (%):", min_value=0.0, value=5.0, step=0.25, key="bn_r")
            ytm_pct = b3.number_input("Tasa de Rendimiento YTM por periodo y (%):", min_value=0.01, value=4.0, step=0.25, key="bn_y")
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

            m1, m2, m3, m4 = st.columns(4)
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

    with t_vpn:
        with st.container(border=True):
            header_tarjeta("Valor Presente Neto (VPN) y Tasa Interna de Retorno (TIR)")
            c_v1, c_v2 = st.columns([1.05, 1.25])
            with c_v1:
                inv_ini = st.number_input("Desembolso Inicial en t = 0 (CF₀ > 0, $):", min_value=0.0, value=10000.0, step=500.0, key="vpn_cf0")
                flujos_str = st.text_input("Flujos netos CF₁, CF₂, …, CFₙ separados por comas:", value="3000, 4000, 4500, 5000", key="vpn_cfs")
                tasa_k_pct = st.number_input("Tasa de descuento / TREMA k (%):", min_value=0.0, value=12.0, step=0.5, key="vpn_k")

                try:
                    cfs = [-float(inv_ini)] + [float(x.strip()) for x in flujos_str.split(",") if x.strip()]
                    k_d = tasa_k_pct / 100.0
                    vpn_val = sum(cf / ((1.0 + k_d) ** t) for t, cf in enumerate(cfs))

                    # Raíces del polinomio en u = 1/(1+TIR)
                    raices_poly = np.roots(cfs[::-1])
                    raices_reales = [r.real for r in raices_poly if abs(r.imag) < 1e-7 and r.real > 0]
                    tir_val = (1.0 / raices_reales[0] - 1.0) if raices_reales else None

                    st.metric("Valor Presente Neto (VPN)", f"${vpn_val:,.2f}", delta="Viable (VPN > 0)" if vpn_val > 0 else "No Viable")
                    if tir_val is not None:
                        st.metric("Tasa Interna de Retorno (TIR)", f"{tir_val * 100:.4f}%")
                except Exception as e:
                    st.error("Verifique el formato de los flujos de efectivo: " + str(e))
                    cfs = None

            with c_v2:
                if cfs is not None:
                    tasas_grid = np.linspace(0.0, 0.50, 150)
                    vpns_grid = [sum(cf / ((1.0 + r_g) ** t) for t, cf in enumerate(cfs)) for r_g in tasas_grid]
                    fig_v, ax_v = _crear_fig_fin(titulo="Perfil del Valor Presente Neto (VPN vs. Tasa k)", xlabel="Tasa de Descuento (%)", ylabel="VPN ($)")
                    ax_v.plot(tasas_grid * 100, vpns_grid, color=AZUL, lw=2.4, label="VPN(k)")
                    ax_v.axhline(0, color=OSCURO, lw=1.2, ls="--")
                    ax_v.plot([tasa_k_pct], [vpn_val], "o", color=VERDE if vpn_val >= 0 else ROJO, ms=8, label=f"TREMA ({tasa_k_pct:.1f}%)")
                    if tir_val is not None and 0 <= tir_val <= 0.50:
                        ax_v.plot([tir_val * 100], [0], "o", color=NARANJA, ms=8, label=f"TIR = {tir_val*100:.2f}%")
                    ax_v.legend(fontsize=8.5)
                    mostrar_figura_segura(fig_v)
