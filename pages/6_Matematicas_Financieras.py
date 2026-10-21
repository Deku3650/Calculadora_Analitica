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
SIMB_PESO = chr(36)


def _moneda(valor: float) -> str:
    return f"{SIMB_PESO}{valor:,.2f}"


# Periodos por año para frecuencias de tasas y unidades de tiempo
FRECUENCIAS_TASA = {
    "Anual": 1.0,
    "Semestral": 2.0,
    "Cuatrimestral": 3.0,
    "Trimestral": 4.0,
    "Bimestral": 6.0,
    "Mensual": 12.0,
    "Quincenal": 24.0,
    "Semanal": 52.0,
    "Diaria (Base 360)": 360.0,
    "Diaria (Base 365)": 365.0,
}

UNIDADES_TIEMPO = {
    "Años": 1.0,
    "Semestres": 2.0,
    "Cuatrimestres": 3.0,
    "Trimestres": 4.0,
    "Bimestres": 6.0,
    "Meses": 12.0,
    "Quincenas": 24.0,
    "Semanas": 52.0,
    "Días (Base 360)": 360.0,
    "Días (Base 365)": 365.0,
}

# Diccionario limpio para textos explicativos (corrige bug "Semono" / "Diori")
INFO_FRECUENCIA = {
    "Anual": ("año", "años", "anual"),
    "Semestral": ("semestre", "semestres", "semestral"),
    "Cuatrimestral": ("cuatrimestre", "cuatrimestres", "cuatrimestral"),
    "Trimestral": ("trimestre", "trimestres", "trimestral"),
    "Bimestral": ("bimestre", "bimestres", "bimestral"),
    "Mensual": ("mes", "meses", "mensual"),
    "Quincenal": ("quincena", "quincenas", "quincenal"),
    "Semanal": ("semana", "semanas", "semanal"),
    "Diaria (Base 360)": ("día comercial", "días comerciales", "diaria (base 360)"),
    "Diaria (Base 365)": ("día natural", "días naturales", "diaria (base 365)"),
}


def _dias_30_360_isda(d1: datetime.date, d2: datetime.date) -> int:
    """Conteo de días bajo la convención estándar 30/360 (ISDA / US Bond Basis)."""
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


def _crear_grafica_amplia(w=10.5, h=4.3, titulo="", xlabel="Tiempo (Años)", ylabel="Monto"):
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
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{SIMB_PESO}{x:,.0f}"))
    if titulo:
        ax.set_title(titulo, color=OSCURO, fontweight="bold", fontsize=11.5, pad=12)
    return fig, ax


def _render_inversion_sidebar(nombre, datos):
    st.markdown(
        f"**Régimen:** {datos['tipo']}  \n"
        f"**Capital (C):** `{_moneda(datos['C'])}`  \n"
        f"**Monto (M):** `{_moneda(datos['M'])}`  \n"
        f"**Tasa Efectiva Anual:** `{datos['tea'] * 100:.2f}%`  \n"
        f"**Plazo:** `{datos['t_anios']:.2f}` años"
    )


# ==============================================================================
# ENCABEZADO Y BARRA LATERAL
# ==============================================================================
encabezado_pagina(
    "📈 Módulo de Matemáticas Financieras",
    "Interés simple y compuesto con homologación automática de tasas y plazos, comparador gráfico, conversión de tasas, conteo 30/360, anualidades, amortización y bonos.",
)

gestionar_inventario_sidebar(
    clave_estado="mis_inversiones",
    titulo="💼 Inversiones Guardadas",
    etiqueta_item="Inversión:",
    render_fn=_render_inversion_sidebar,
)

# ==============================================================================
# PESTAÑAS PRINCIPALES
# ==============================================================================
tab_interes, tab_comparador, tab_tasas, tab_plazos, tab_anualidades, tab_bonos = st.tabs([
    "💰 1. Interés Simple y Compuesto",
    "📊 2. Comparador Gráfico",
    "🔄 3. Conversión de Tasas",
    "📅 4. Cálculo de Plazos",
    "🏦 5. Anualidades y Amortización",
    "📜 6. Bonos y Proyectos (VPN / TIR)",
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: INTERÉS SIMPLE Y COMPUESTO (REACTIVO Y CON UNIDADES DE TASA Y TIEMPO)
# ------------------------------------------------------------------------------
with tab_interes:
    with st.container(border=True):
        header_tarjeta("Configuración de la Operación Financiera")

        c_reg, c_inc = st.columns(2, gap="large")
        with c_reg:
            regimen = st.radio(
                "Régimen de Interés:",
                ["Interés Compuesto", "Interés Simple"],
                horizontal=True,
                key="int_regimen",
            )
        with c_inc:
            incognita = st.selectbox(
                "Variable a calcular (se actualiza automáticamente):",
                [
                    "Monto Futuro / Valor Final (M)",
                    "Capital Inicial / Valor Presente (C)",
                    "Tasa de Interés (i)",
                    "Tiempo / Plazo (n)",
                ],
                key="int_incognita",
            )

        st.divider()
        subheader_tarjeta("Datos de Capital, Tasa y Plazo")

        col_cap, col_tasa, col_tiempo = st.columns(3, gap="large")

        with col_cap:
            st.markdown("**1. Capitales**")
            if incognita != "Capital Inicial / Valor Presente (C)":
                C_val = st.number_input("Capital Inicial C:", min_value=0.01, value=10000.0, step=500.0, format="%.2f", key="in_C")
            else:
                C_val = 0.0
                st.info("El **Capital Inicial (C)** se calculará automáticamente.")

            if incognita != "Monto Futuro / Valor Final (M)":
                M_val = st.number_input("Monto Futuro M:", min_value=0.01, value=15000.0, step=500.0, format="%.2f", key="in_M")
            else:
                M_val = 0.0
                st.info("El **Monto Futuro (M)** se calculará automáticamente.")

        with col_tasa:
            st.markdown("**2. Tasa de Interés**")
            if regimen == "Interés Compuesto":
                tipo_tasa = st.selectbox(
                    "Tipo de tasa:",
                    ["Efectiva", "Nominal Anual Capitalizable"],
                    key="in_tipo_tasa",
                )
            else:
                tipo_tasa = "Simple Proporcional"
                st.caption("En Interés Simple toda tasa es proporcional a su periodo.")

            frec_tasa = st.selectbox(
                "Periodo / Capitalización de la tasa:",
                list(FRECUENCIAS_TASA.keys()),
                index=0,
                key="in_frec_tasa",
            )

            if incognita != "Tasa de Interés (i)":
                tasa_pct = st.number_input("Valor de la tasa (%):", min_value=0.0, value=12.0, step=0.5, format="%.4f", key="in_tasa_val")
            else:
                tasa_pct = 0.0
                st.info("La **Tasa de Interés** se calculará en el periodo seleccionado.")

        with col_tiempo:
            st.markdown("**3. Plazo / Tiempo**")
            unidad_tiempo = st.selectbox(
                "Unidad de tiempo del plazo:",
                list(UNIDADES_TIEMPO.keys()),
                index=0,
                key="in_uni_tiempo",
            )
            if incognita != "Tiempo / Plazo (n)":
                tiempo_val = st.number_input(f"Cantidad de {unidad_tiempo.lower()}:", min_value=0.0001, value=3.0, step=1.0, format="%.4f", key="in_tiempo_val")
            else:
                tiempo_val = 0.0
                st.info(f"El **Plazo** se calculará en **{unidad_tiempo.lower()}**.")

    # --- CÁLCULO AUTOMÁTICO Y HOMOLOGACIÓN DE UNIDADES ---
    m_tasa = FRECUENCIAS_TASA[frec_tasa]
    m_tiempo = UNIDADES_TIEMPO[unidad_tiempo]
    sust_tasa, plur_tasa, adj_tasa = INFO_FRECUENCIA[frec_tasa]

    calculo_valido = True
    mensaje_error = ""

    # Convertir tiempo a años y al número de periodos de la tasa (n_per)
    if incognita != "Tiempo / Plazo (n)":
        t_anios = tiempo_val / m_tiempo
        n_per = t_anios * m_tasa
    else:
        t_anios = 0.0
        n_per = 0.0

    # Convertir la tasa ingresada a tasa efectiva por periodo de capitalización (i_per)
    if incognita != "Tasa de Interés (i)":
        r_dec = tasa_pct / 100.0
        if regimen == "Interés Compuesto" and tipo_tasa == "Nominal Anual Capitalizable":
            i_per = r_dec / m_tasa
        else:
            i_per = r_dec
    else:
        i_per = 0.0

    # Resolver la incógnita seleccionada
    if incognita == "Monto Futuro / Valor Final (M)":
        if regimen == "Interés Compuesto":
            M_val = C_val * ((1.0 + i_per) ** n_per)
        else:
            M_val = C_val * (1.0 + i_per * n_per)

    elif incognita == "Capital Inicial / Valor Presente (C)":
        if regimen == "Interés Compuesto":
            C_val = M_val / ((1.0 + i_per) ** n_per)
        else:
            C_val = M_val / (1.0 + i_per * n_per)

    elif incognita == "Tasa de Interés (i)":
        if M_val < C_val:
            calculo_valido = False
            mensaje_error = "⛔ El Monto Futuro (M) debe ser mayor o igual al Capital Inicial (C) para obtener una tasa no negativa."
        else:
            if regimen == "Interés Compuesto":
                i_per = (M_val / C_val) ** (1.0 / n_per) - 1.0
                tasa_pct = (i_per * m_tasa * 100.0) if tipo_tasa == "Nominal Anual Capitalizable" else (i_per * 100.0)
            else:
                i_per = (M_val / C_val - 1.0) / n_per
                tasa_pct = i_per * 100.0

    elif incognita == "Tiempo / Plazo (n)":
        if i_per <= 0:
            calculo_valido = False
            mensaje_error = "⛔ Para despejar el plazo (n) la tasa de interés debe ser mayor que 0%."
        elif M_val < C_val:
            calculo_valido = False
            mensaje_error = "⛔ El Monto Futuro (M) debe ser mayor o igual al Capital Inicial (C)."
        else:
            if regimen == "Interés Compuesto":
                n_per = math.log(M_val / C_val) / math.log(1.0 + i_per)
            else:
                n_per = (M_val / C_val - 1.0) / i_per
            t_anios = n_per / m_tasa
            tiempo_val = t_anios * m_tiempo

    if not calculo_valido:
        st.error(mensaje_error)
    else:
        I_generado = M_val - C_val
        tea_equiv = ((1.0 + i_per) ** m_tasa - 1.0) if regimen == "Interés Compuesto" else (i_per * m_tasa)

        with st.container(border=True):
            header_tarjeta("Resultados y Homologación de Unidades")

            m1, m2, m3, m4 = st.columns(4, gap="medium")
            m1.metric("Capital Inicial (C)", _moneda(C_val))
            m2.metric("Monto Futuro (M)", _moneda(M_val))
            m3.metric("Interés Generado (I)", _moneda(I_generado))
            if incognita == "Tiempo / Plazo (n)":
                m4.metric(f"Plazo en {unidad_tiempo}", f"{tiempo_val:,.4f}")
            else:
                m4.metric(f"Tasa ({tipo_tasa[:8]}. {frec_tasa})", f"{tasa_pct:,.4f}%")

            st.info(
                f"🔄 **Homologación de unidades:** El plazo de **{tiempo_val:,.4f} {unidad_tiempo.lower()}** equivale a "
                f"**{t_anios:,.4f} años** (**{n_per:,.4f} {plur_tasa}**). "
                f"La tasa aplicada por cada {sust_tasa} es **i = {i_per * 100:.6f}%** "
                f"(equivalente a una tasa anual efectiva de **{tea_equiv * 100:.4f}%**)."
            )

            if regimen == "Interés Compuesto":
                st.latex(
                    r"M = C(1 + i)^n \implies "
                    + f"{M_val:,.2f} = {C_val:,.2f}\\left(1 + {i_per:.6f}\\right)^{{{n_per:.4f}}}"
                )
            else:
                st.latex(
                    r"M = C(1 + i \cdot n) \implies "
                    + f"{M_val:,.2f} = {C_val:,.2f}\\left(1 + {i_per:.6f} \\times {n_per:.4f}\\right)"
                )

            st.divider()
            col_s1, col_s2 = st.columns([2.5, 1])
            with col_s1:
                nom_inv = st.text_input(
                    "Asignar nombre para guardar en el Comparador (Ej: INV_1, CETES, PAGARE):",
                    value=f"INV_{len(st.session_state.mis_inversiones) + 1}",
                    key="nom_save_inv",
                ).upper().strip()
            with col_s2:
                st.write("")
                if st.button("💾 Guardar en el Comparador", use_container_width=True):
                    if nom_inv:
                        st.session_state.mis_inversiones[nom_inv] = {
                            "tipo": regimen,
                            "C": C_val,
                            "M": M_val,
                            "I": I_generado,
                            "tasa": i_per,
                            "m_tasa": m_tasa,
                            "frec_tasa": frec_tasa,
                            "n": n_per,
                            "t_anios": t_anios,
                            "tea": tea_equiv,
                        }
                        st.success(f"Inversión '{nom_inv}' guardada en la barra lateral.")
                        st.rerun()

# ------------------------------------------------------------------------------
# PESTAÑA 2: COMPARADOR GRÁFICO (ANCHO COMPLETO)
# ------------------------------------------------------------------------------
with tab_comparador:
    with st.container(border=True):
        header_tarjeta("Comparador Gráfico de Inversiones Guardadas")
        if not st.session_state.mis_inversiones:
            st.info("👈 Guarde una o más inversiones en la Pestaña 1 para compararlas aquí.")
        else:
            c_sel, c_uni = st.columns([2.2, 1])
            with c_sel:
                seleccion_inv = st.multiselect(
                    "Seleccione las inversiones a graficar:",
                    list(st.session_state.mis_inversiones.keys()),
                    default=list(st.session_state.mis_inversiones.keys()),
                )
            with c_uni:
                eje_x_uni = st.radio("Unidad del eje horizontal:", ["Años", "Meses"], horizontal=True, key="comp_eje_x")

            if seleccion_inv:
                factor_x = 12.0 if eje_x_uni == "Meses" else 1.0
                max_anios = max(max(float(st.session_state.mis_inversiones[k]["t_anios"]) for k in seleccion_inv), 0.1)

                fig_comp, ax_comp = _crear_grafica_amplia(
                    w=11.0,
                    h=4.6,
                    titulo="Crecimiento Comparativo de las Inversiones en el Tiempo",
                    xlabel=f"Tiempo ({eje_x_uni})",
                    ylabel=f"Monto Acumulado ({SIMB_PESO})",
                )
                paleta = [AZUL, NARANJA, VERDE, ROJO, MORADO, "#0891b2", "#be185d"]
                filas_comp = []

                for idx, nom_k in enumerate(seleccion_inv):
                    d_k = st.session_state.mis_inversiones[nom_k]
                    t_anios_vec = np.linspace(0, float(d_k["t_anios"]), 200)
                    n_per_vec = t_anios_vec * float(d_k.get("m_tasa", 1.0))

                    if d_k["tipo"] == "Interés Compuesto":
                        y_vec = d_k["C"] * ((1.0 + d_k["tasa"]) ** n_per_vec)
                    else:
                        y_vec = d_k["C"] * (1.0 + d_k["tasa"] * n_per_vec)

                    col_k = paleta[idx % len(paleta)]
                    x_plot = t_anios_vec * factor_x
                    ax_comp.plot(x_plot, y_vec, color=col_k, lw=2.5, label=f"{nom_k} ({d_k['tipo']} → {_moneda(d_k['M'])})")
                    ax_comp.plot([d_k["t_anios"] * factor_x], [d_k["M"]], "o", color=col_k, ms=7.5)

                    filas_comp.append({
                        "Inversión": nom_k,
                        "Régimen": d_k["tipo"],
                        "Capital Inicial (C)": d_k["C"],
                        "Tasa Periódica": f"{d_k['tasa'] * 100:.4f}% ({d_k.get('frec_tasa', 'Anual')})",
                        "Plazo (Años)": f"{d_k['t_anios']:.2f}",
                        "Interés Generado (I)": d_k["I"],
                        "Monto Final (M)": d_k["M"],
                    })

                ax_comp.set_xlim(0, max_anios * factor_x * 1.05)
                ax_comp.legend(fontsize=9.5, loc="upper left")
                mostrar_figura_segura(fig_comp)

                subheader_tarjeta("Resumen Comparativo")
                df_c = pd.DataFrame(filas_comp)
                st.dataframe(
                    df_c.style.format({
                        "Capital Inicial (C)": f"{SIMB_PESO}{{:,.2f}}",
                        "Interés Generado (I)": f"{SIMB_PESO}{{:,.2f}}",
                        "Monto Final (M)": f"{SIMB_PESO}{{:,.2f}}",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )

# ------------------------------------------------------------------------------
# PESTAÑA 3: CONVERSIÓN DE TASAS (AUTOMÁTICA)
# ------------------------------------------------------------------------------
with tab_tasas:
    with st.container(border=True):
        header_tarjeta("Conversión de Tasas Equivalentes (Nominal ↔ Efectiva ↔ Continua y Tasa Real)")

        c1, c2, c3, c4 = st.columns(4, gap="medium")
        with c1:
            tasa_in_pct = st.number_input("Tasa de interés (%):", min_value=0.0, value=12.0, step=0.25, format="%.4f", key="tc_val")
        with c2:
            tipo_tasa_in = st.selectbox(
                "Tipo de la tasa ingresada:",
                ["Nominal Anual Capitalizable j^(m)", "Efectiva del Periodo i_m", "Efectiva Anual (TEA / i)"],
                key="tc_tipo",
            )
        with c3:
            frec_origen = st.selectbox("Frecuencia de origen (m):", list(FRECUENCIAS_TASA.keys()), index=5, key="tc_orig")
        with c4:
            frec_destino = st.selectbox("Convertir a frecuencia destino (k):", list(FRECUENCIAS_TASA.keys()), index=3, key="tc_dest")

        inflacion_pct = st.number_input("Tasa de inflación anual π (%) [Opcional, para Tasa Real de Fisher]:", min_value=0.0, value=4.5, step=0.25, format="%.2f", key="tc_inf")

        m_or = FRECUENCIAS_TASA[frec_origen]
        m_de = FRECUENCIAS_TASA[frec_destino]
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
        tasa_real = (1.0 + tea) / (1.0 + inflacion_pct / 100.0) - 1.0

        sust_or, _, adj_or = INFO_FRECUENCIA[frec_origen]
        sust_de, _, adj_de = INFO_FRECUENCIA[frec_destino]

        st.divider()
        k1, k2, k3, k4 = st.columns(4, gap="medium")
        k1.metric(f"Efectiva {frec_destino}", f"{i_per_dest * 100:.4f}% por {sust_de}")
        k2.metric(f"Nominal Anual Cap. {frec_destino}", f"{j_nom_dest * 100:.4f}% anual")
        k3.metric("Tasa Efectiva Anual (TEA)", f"{tea * 100:.4f}% anual")
        k4.metric("Fuerza de Interés δ / Tasa Real", f"δ={delta_cont * 100:.3f}% · Real={tasa_real * 100:.3f}%")

        st.latex(
            r"1 + i = \left(1 + \frac{j^{(m)}}{m}\right)^m = \left(1 + i_k\right)^k = e^{\delta}"
        )
        st.success(
            f"**Explicación:** Una tasa {adj_or} efectiva de **{i_per_or * 100:.4f}%** por {sust_or} "
            f"produce el mismo rendimiento que una tasa efectiva {adj_de} de **{i_per_dest * 100:.4f}%** por {sust_de}, "
            f"o una tasa nominal anual de **{j_nom_dest * 100:.4f}%** capitalizable {frec_destino.lower()}."
        )

        with st.expander("📋 Ver tabla de equivalencias en todas las frecuencias de capitalización"):
            filas_eq = []
            for nom_f, m_f in FRECUENCIAS_TASA.items():
                i_f = (1.0 + tea) ** (1.0 / m_f) - 1.0
                j_f = i_f * m_f
                filas_eq.append({
                    "Frecuencia": nom_f,
                    "Periodos por Año (m)": int(m_f),
                    "Tasa Efectiva del Periodo (i_m)": f"{i_f * 100:.6f}%",
                    "Tasa Nominal Anual (j^(m))": f"{j_f * 100:.6f}%",
                })
            st.dataframe(pd.DataFrame(filas_eq), use_container_width=True, hide_index=True)

# ------------------------------------------------------------------------------
# PESTAÑA 4: CÁLCULO DE PLAZOS ENTRE FECHAS (EXACTO Y 30/360 ISDA)
# ------------------------------------------------------------------------------
with tab_plazos:
    with st.container(border=True):
        header_tarjeta("Cálculo de Plazos entre Fechas (Tiempo Exacto vs. Tiempo Comercial 30/360 ISDA)")

        c_f1, c_f2 = st.columns(2, gap="large")
        with c_f1:
            f_ini = st.date_input("Fecha Inicial:", value=datetime.date(2026, 3, 31), key="pl_f_ini")
        with c_f2:
            f_fin = st.date_input("Fecha Final:", value=datetime.date(2026, 4, 1), key="pl_f_fin")

        if f_fin < f_ini:
            st.error("⛔ La Fecha Final debe ser posterior o igual a la Fecha Inicial.")
        else:
            dias_exactos = (f_fin - f_ini).days
            dias_360 = _dias_30_360_isda(f_ini, f_fin)

            st.divider()
            d1, d2, d3 = st.columns(3, gap="medium")
            d1.metric("Tiempo Exacto (Actual)", f"{dias_exactos:,} días")
            d2.metric("Tiempo Comercial (30/360 ISDA)", f"{dias_360:,} días")
            d3.metric("Años Equivalentes (Exacto/365 vs 30/360)", f"{dias_exactos / 365.0:.4f}  |  {dias_360 / 360.0:.4f}")

            st.markdown(
                f"| Convención | Días Contabilizados | Base Anual | Fracción de Año ($t$) |\n"
                f"|---|---|---|---|\n"
                f"| **Exacto / Exacto (Actual/365)** | `{dias_exactos}` días reales | `365` días | `{dias_exactos / 365.0:.6f}` |\n"
                f"| **Bancario / Comercial (Actual/360)** | `{dias_exactos}` días reales | `360` días | `{dias_exactos / 360.0:.6f}` |\n"
                f"| **30 / 360 (ISDA Bond Basis)** | `{dias_360}` días comerciales | `360` días | `{dias_360 / 360.0:.6f}` |"
            )

# ------------------------------------------------------------------------------
# PESTAÑA 5: ANUALIDADES Y TABLAS DE AMORTIZACIÓN (AUTOMÁTICO)
# ------------------------------------------------------------------------------
with tab_anualidades:
    sub_an1, sub_an2 = st.tabs([
        "🏦 1. Anualidades Constantes y Tabla de Amortización",
        "📈 2. Anualidades Variables (Aritmética, Geométrica y Perpetuidad)",
    ])

    with sub_an1:
        with st.container(border=True):
            header_tarjeta("Calculadora de Anualidades y Tabla de Amortización")

            c1, c2, c3 = st.columns(3, gap="medium")
            with c1:
                modalidad_an = st.radio("Modalidad de pago:", ["Vencida (Ordinaria)", "Anticipada"], horizontal=True, key="an_mod")
            with c2:
                incog_an = st.selectbox(
                    "Variable a calcular:",
                    [
                        "Valor Presente (VP) y Valor Futuro (VF)",
                        "Renta / Pago Periódico (R) dado el Valor Presente",
                        "Renta / Pago Periódico (R) dado el Valor Futuro",
                    ],
                    key="an_incog",
                )
            with c3:
                frec_an = st.selectbox("Frecuencia de los pagos:", list(FRECUENCIAS_TASA.keys()), index=5, key="an_frec")

            p1, p2, p3, p4 = st.columns(4, gap="medium")
            with p1:
                if incog_an.startswith("Valor Presente"):
                    R_in = st.number_input("Renta Periódica R:", min_value=0.01, value=2500.0, step=100.0, format="%.2f", key="an_R")
                elif "Valor Presente" in incog_an:
                    VP_in = st.number_input("Valor Presente / Deuda VP:", min_value=0.01, value=50000.0, step=1000.0, format="%.2f", key="an_VP")
                else:
                    VF_in = st.number_input("Valor Futuro Objetivo VF:", min_value=0.01, value=50000.0, step=1000.0, format="%.2f", key="an_VF")
            with p2:
                tipo_tasa_an = st.selectbox("La tasa ingresada es:", ["Efectiva del periodo de pago", "Nominal Anual Capitalizable"], key="an_tipo_i")
            with p3:
                tasa_an_pct = st.number_input("Valor de la tasa (%):", min_value=0.0, value=12.0 if tipo_tasa_an.startswith("Nominal") else 1.5, step=0.25, format="%.4f", key="an_i")
            with p4:
                n_an = int(st.number_input("Número total de pagos (n):", min_value=1, max_value=360, value=12, step=1, key="an_n"))

            m_an = FRECUENCIAS_TASA[frec_an]
            i_an = (tasa_an_pct / 100.0 / m_an) if tipo_tasa_an.startswith("Nominal") else (tasa_an_pct / 100.0)
            factor_ant = (1.0 + i_an) if modalidad_an.startswith("Anticipada") else 1.0

            # Soporte exacto para tasa = 0% (Fix de auditoría)
            if abs(i_an) < 1e-12:
                if incog_an.startswith("Valor Presente"):
                    R_calc = R_in
                    vp_calc = R_in * n_an
                    vf_calc = R_in * n_an
                elif "Valor Presente" in incog_an:
                    R_calc = VP_in / n_an
                    vp_calc = VP_in
                    vf_calc = VP_in
                else:
                    R_calc = VF_in / n_an
                    vp_calc = VF_in
                    vf_calc = VF_in
            else:
                a_ni = (1.0 - (1.0 + i_an) ** (-n_an)) / i_an
                s_ni = (((1.0 + i_an) ** n_an) - 1.0) / i_an
                if incog_an.startswith("Valor Presente"):
                    R_calc = R_in
                    vp_calc = R_in * a_ni * factor_ant
                    vf_calc = R_in * s_ni * factor_ant
                elif "Valor Presente" in incog_an:
                    R_calc = VP_in / (a_ni * factor_ant)
                    vp_calc = VP_in
                    vf_calc = R_calc * s_ni * factor_ant
                else:
                    R_calc = VF_in / (s_ni * factor_ant)
                    vf_calc = VF_in
                    vp_calc = R_calc * a_ni * factor_ant

            st.divider()
            m1, m2, m3, m4 = st.columns(4, gap="medium")
            m1.metric("Pago Periódico / Renta (R)", _moneda(R_calc))
            m2.metric("Valor Presente (VP)", _moneda(vp_calc))
            m3.metric("Valor Futuro / Monto (VF)", _moneda(vf_calc))
            m4.metric("Tasa Efectiva por Periodo", f"{i_an * 100:.4f}%")

            # Tabla de amortización automática sobre el Valor Presente
            subheader_tarjeta("Tabla de Amortización de la Deuda (VP)")
            filas_am = [{
                "Periodo": 0,
                "Pago Periódico": 0.0,
                "Intereses": 0.0,
                "Abono a Capital": 0.0,
                "Capital Amortizado Acum.": 0.0,
                "Saldo Insoluto": float(vp_calc),
            }]
            saldo = float(vp_calc)
            acum_cap = 0.0
            for k in range(1, n_an + 1):
                if modalidad_an.startswith("Anticipada") and k == 1:
                    int_k = 0.0
                else:
                    int_k = saldo * i_an
                abono_k = R_calc - int_k
                saldo = max(0.0, saldo - abono_k)
                acum_cap += abono_k
                filas_am.append({
                    "Periodo": k,
                    "Pago Periódico": R_calc,
                    "Intereses": int_k,
                    "Abono a Capital": abono_k,
                    "Capital Amortizado Acum.": acum_cap,
                    "Saldo Insoluto": saldo,
                })

            df_am = pd.DataFrame(filas_am)
            fig_am, ax_am = _crear_grafica_amplia(
                titulo="Evolución del Saldo Insoluto vs. Capital Amortizado Acumulado",
                xlabel=f"Periodo ({frec_an})",
                ylabel=f"Monto ({SIMB_PESO})",
            )
            ax_am.plot(df_am["Periodo"], df_am["Saldo Insoluto"], "o-", color=AZUL, lw=2.4, ms=5, label="Saldo Insoluto")
            ax_am.plot(df_am["Periodo"], df_am["Capital Amortizado Acum."], "s--", color=VERDE, lw=2.2, ms=4.5, label="Capital Amortizado Acumulado")
            ax_am.legend(fontsize=9.5, loc="center right")
            mostrar_figura_segura(fig_am)

            st.dataframe(
                df_am.style.format({
                    "Pago Periódico": f"{SIMB_PESO}{{:,.2f}}",
                    "Intereses": f"{SIMB_PESO}{{:,.2f}}",
                    "Abono a Capital": f"{SIMB_PESO}{{:,.2f}}",
                    "Capital Amortizado Acum.": f"{SIMB_PESO}{{:,.2f}}",
                    "Saldo Insoluto": f"{SIMB_PESO}{{:,.2f}}",
                }),
                use_container_width=True,
                hide_index=True,
            )

    with sub_an2:
        with st.container(border=True):
            header_tarjeta("Anualidades Variables (Progresión Aritmética, Geométrica) y Perpetuidades")
            tipo_var = st.radio(
                "Seleccione el modelo actuarial:",
                [
                    "1. Progresión Aritmética (Primer pago P, incremento constante Q por periodo)",
                    "2. Progresión Geométrica (Primer pago R₁, tasa de crecimiento g % por periodo)",
                    "3. Perpetuidad (Pagos infinitos constantes o crecientes)",
                ],
                key="an_var_tipo",
            )
            cv1, cv2, cv3, cv4 = st.columns(4, gap="medium")
            p_base = cv1.number_input("Primer pago P / R₁:", min_value=0.01, value=1000.0, step=100.0, format="%.2f", key="av_P")
            i_v = cv2.number_input("Tasa efectiva por periodo i (%):", min_value=0.01, value=2.0, step=0.25, format="%.4f", key="av_i") / 100.0
            if not tipo_var.startswith("3."):
                n_v = int(cv3.number_input("Número de pagos (n):", min_value=1, max_value=360, value=12, step=1, key="av_n"))

            if tipo_var.startswith("1."):
                Q_inc = cv4.number_input("Incremento constante Q:", value=200.0, step=50.0, format="%.2f", key="av_Q")
                a_ni = (1.0 - (1.0 + i_v) ** (-n_v)) / i_v
                vp_var = p_base * a_ni + (Q_inc / i_v) * (a_ni - n_v * ((1.0 + i_v) ** (-n_v)))
                vf_var = vp_var * ((1.0 + i_v) ** n_v)
                st.divider()
                v1, v2, v3 = st.columns(3, gap="medium")
                v1.metric("Valor Presente (VP)", _moneda(vp_var))
                v2.metric("Valor Futuro (VF)", _moneda(vf_var))
                v3.metric("Último Pago en t = n", _moneda(p_base + (n_v - 1) * Q_inc))
                st.latex(r"VP = P\,a_{\overline{n}|i} + \frac{Q}{i}\left(a_{\overline{n}|i} - n(1+i)^{-n}\right)")

            elif tipo_var.startswith("2."):
                g_v = cv4.number_input("Crecimiento geométrico g (%):", value=1.0, step=0.25, format="%.4f", key="av_g") / 100.0
                if abs(i_v - g_v) < 1e-10:
                    vp_var = n_v * p_base / (1.0 + i_v)
                else:
                    vp_var = p_base * (1.0 - ((1.0 + g_v) / (1.0 + i_v)) ** n_v) / (i_v - g_v)
                vf_var = vp_var * ((1.0 + i_v) ** n_v)
                st.divider()
                v1, v2, v3 = st.columns(3, gap="medium")
                v1.metric("Valor Presente (VP)", _moneda(vp_var))
                v2.metric("Valor Futuro (VF)", _moneda(vf_var))
                v3.metric("Último Pago en t = n", _moneda(p_base * ((1.0 + g_v) ** (n_v - 1))))
                st.latex(r"VP = R_1 \cdot \frac{1 - \left(\frac{1+g}{1+i}\right)^n}{i - g}")

            else:
                g_perp = cv3.number_input("Crecimiento perpetuo g (% < i):", min_value=0.0, value=0.5, step=0.1, format="%.4f", key="av_gp") / 100.0
                if g_perp >= i_v:
                    st.error("⛔ En una perpetuidad creciente, la tasa de descuento i debe ser mayor que g.")
                else:
                    vp_perp = p_base / (i_v - g_perp)
                    st.divider()
                    v1, v2 = st.columns(2, gap="medium")
                    v1.metric("Valor Presente Perpetuidad Vencida", _moneda(vp_perp))
                    v2.metric("Valor Presente Perpetuidad Anticipada", _moneda(vp_perp * (1.0 + i_v)))
                    st.latex(r"VP_{\infty} = \frac{R_1}{i - g}")

# ------------------------------------------------------------------------------
# PESTAÑA 6: VALUACIÓN DE BONOS Y PROYECTOS (VPN / TIR) (AUTOMÁTICO)
# ------------------------------------------------------------------------------
with tab_bonos:
    t_bono, t_vpn = st.tabs([
        "📜 1. Valuación de Bonos, Duración y Convexidad",
        "🚀 2. Evaluación de Proyectos (VPN y TIR)",
    ])

    with t_bono:
        with st.container(border=True):
            header_tarjeta("Valuación de Bonos / Obligaciones, Duración de Macaulay y Convexidad")
            b1, b2, b3, b4 = st.columns(4, gap="medium")
            vn_bono = b1.number_input("Valor Nominal F:", min_value=10.0, value=1000.0, step=100.0, format="%.2f", key="bn_F")
            tasa_cupon_pct = b2.number_input("Tasa Cupón por periodo r (%):", min_value=0.0, value=5.0, step=0.25, format="%.4f", key="bn_r")
            ytm_pct = b3.number_input("Tasa de Rendimiento YTM por periodo y (%):", min_value=0.01, value=4.0, step=0.25, format="%.4f", key="bn_y")
            n_cupones = int(b4.number_input("Cupones por pagar (n):", min_value=1, max_value=120, value=10, step=1, key="bn_n"))

            cupon_C = vn_bono * (tasa_cupon_pct / 100.0)
            y_b = ytm_pct / 100.0

            ts_b = np.arange(1, n_cupones + 1, dtype=float)
            flujos_b = np.full(n_cupones, cupon_C, dtype=float)
            flujos_b[-1] += vn_bono
            vp_flujos = flujos_b * ((1.0 + y_b) ** (-ts_b))

            precio_bono = float(np.sum(vp_flujos))
            dur_macaulay = float(np.sum(ts_b * vp_flujos) / precio_bono)
            dur_modificada = dur_macaulay / (1.0 + y_b)
            convexidad = float(np.sum(ts_b * (ts_b + 1.0) * vp_flujos) / (precio_bono * ((1.0 + y_b) ** 2)))

            st.divider()
            m1, m2, m3, m4 = st.columns(4, gap="medium")
            m1.metric("Precio del Bono (P)", _moneda(precio_bono))
            m2.metric("Duración de Macaulay", f"{dur_macaulay:.4f} per.")
            m3.metric("Duración Modificada (D*)", f"{dur_modificada:.4f}")
            m4.metric("Convexidad", f"{convexidad:.4f}")

            ys_grid = np.linspace(max(0.002, y_b * 0.25), y_b * 2.5, 160)
            precios_grid = [
                sum(flujos_b[k] * ((1.0 + y_g) ** (-(k + 1))) for k in range(n_cupones))
                for y_g in ys_grid
            ]
            fig_b, ax_b = _crear_grafica_amplia(
                titulo="Curva Precio vs. Rendimiento (P vs. YTM)",
                xlabel="Tasa de Rendimiento por Periodo YTM (%)",
                ylabel=f"Precio ({SIMB_PESO})",
            )
            ax_b.plot(ys_grid * 100, precios_grid, color=AZUL, lw=2.5, label="Precio P(y)")
            ax_b.plot([ytm_pct], [precio_bono], "o", color=ROJO, ms=8, label=f"Precio actual ({_moneda(precio_bono)})")
            ax_b.axhline(vn_bono, color=OSCURO, ls=":", lw=1.2, label=f"Valor Nominal ({_moneda(vn_bono)})")
            ax_b.legend(fontsize=9.5)
            mostrar_figura_segura(fig_b)

    with t_vpn:
        with st.container(border=True):
            header_tarjeta("Valor Presente Neto (VPN) y Tasa Interna de Retorno (TIR)")
            v1, v2, v3 = st.columns([1, 2, 1], gap="medium")
            with v1:
                inv_ini = st.number_input("Inversión Inicial CF₀:", min_value=0.0, value=10000.0, step=500.0, format="%.2f", key="vpn_cf0")
            with v2:
                flujos_str = st.text_input("Flujos netos CF₁, CF₂, …, CFₙ separados por comas:", value="3000, 4000, 4500, 5000", key="vpn_cfs")
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
                p1.metric("Valor Presente Neto (VPN)", _moneda(vpn_val), delta="Viable (VPN > 0)" if vpn_val > 0 else "No Viable")
                p2.metric("Tasa Interna de Retorno (TIR)", f"{tir_val * 100:.4f}%" if tir_val is not None else "N/D")
                p3.metric("Índice de Rentabilidad (IR)", f"{ir_val:.4f}")

                tasas_grid = np.linspace(0.0, 0.50, 180)
                vpns_grid = [sum(cf / ((1.0 + r_g) ** t) for t, cf in enumerate(cfs)) for r_g in tasas_grid]
                fig_v, ax_v = _crear_grafica_amplia(
                    titulo="Perfil del Valor Presente Neto (VPN vs. Tasa de Descuento k)",
                    xlabel="Tasa de Descuento k (%)",
                    ylabel=f"VPN ({SIMB_PESO})",
                )
                ax_v.plot(tasas_grid * 100, vpns_grid, color=AZUL, lw=2.5, label="VPN(k)")
                ax_v.axhline(0, color=OSCURO, lw=1.3, ls="--")
                ax_v.plot([tasa_k_pct], [vpn_val], "o", color=VERDE if vpn_val >= 0 else ROJO, ms=8.5, label=f"TREMA ({tasa_k_pct:.2f}% → {_moneda(vpn_val)})")
                if tir_val is not None and 0 <= tir_val <= 0.50:
                    ax_v.plot([tir_val * 100], [0], "o", color=NARANJA, ms=8.5, label=f"TIR = {tir_val * 100:.2f}%")
                ax_v.legend(fontsize=9.5)
                mostrar_figura_segura(fig_v)
            except Exception as e:
                st.error("Verifique el formato de los flujos de efectivo separados por comas: " + str(e))
