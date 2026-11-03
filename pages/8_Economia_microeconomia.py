# pages/8_Economia_microeconomia.py
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import sympy as sp
from matplotlib.ticker import AutoMinorLocator

# 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO)
st.set_page_config(
    page_title="Microeconomía y Organización Industrial - MATHESIS",
    page_icon="📊",
    layout="wide",
)

from estilos import cargar_estilos_globales, encabezado_pagina, header_tarjeta, subheader_tarjeta  # noqa: E402
from utils import inicializar_estado, leer_expresion_st, mostrar_figura_segura  # noqa: E402

try:
    from teclado_matematico import LAYOUTS, teclado_matematico
    from interprete_latex import ErrorLatex, ErrorNoSoportado, latex_a_sympy, leer_en_espanol
    _TIENE_TECLADO = True
    if "economia" not in LAYOUTS and "calculo" in LAYOUTS:
        LAYOUTS["economia"] = {
            "tabs": [t for t in LAYOUTS["calculo"]["tabs"] if t.get("id") in ("123", "fx", "abc")]
        }
except Exception:
    _TIENE_TECLADO = False

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
SIMB_PESO = chr(36)


def _moneda(val: float) -> str:
    return f"{SIMB_PESO}{val:,.2f}"


def _lienzo_econ(w=6.8, h=5.0, xlabel="Cantidad (Q)", ylabel="Precio (P)", titulo=""):
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
    if titulo:
        ax.set_title(titulo, color=OSCURO, fontweight="bold", fontsize=10.5, pad=10)
    return fig, ax


# ==============================================================================
# ENCABEZADO PRINCIPAL
# ==============================================================================
encabezado_pagina(
    "📊 Módulo de Teoría Económica, Microeconomía y Organización Industrial",
    "Equilibrio de Marshall, bienestar e impuestos, teoría del consumidor (Slutsky), teoría del productor, estructura de costos y competencia imperfecta (Monopolio, Cournot y Stackelberg).",
)

tab_mercado, tab_consumidor, tab_productor, tab_costos, tab_estructuras = st.tabs([
    "⚖️ 1. Equilibrio, Excedentes e Impuestos",
    "🛒 2. Consumidor y Efecto Slutsky",
    "🏭 3. Producción e Isocuantas",
    "📉 4. Estructura de Costos",
    "🏛️ 5. Monopolio y Oligopolio (Cournot/Stackelberg)",
])


# ==============================================================================
# PESTAÑA 1: EQUILIBRIO DE MARSHALL, EXCEDENTES E INTERVENCIÓN ESTATAL
# ==============================================================================
with tab_mercado:
    col_m1, col_m2 = st.columns([1.05, 1.3], gap="large")

    with col_m1:
        with st.container(border=True):
            header_tarjeta("1. Funciones Inversas de Demanda P_d(Q) y Oferta P_s(Q)")
            st.caption("Convención estándar de Marshall: Cantidad (Q) en el eje horizontal y Precio (P) en el eje vertical.")

            d1, d2 = st.columns(2)
            a_dem = d1.number_input("Ordenada de Demanda P_máx (a):", min_value=1.0, value=120.0, step=5.0, key="m_a")
            b_dem = d2.number_input("Pendiente de Demanda (−b, b > 0):", min_value=0.05, value=2.0, step=0.25, key="m_b")

            s1, s2 = st.columns(2)
            c_of = s1.number_input("Ordenada de Oferta P_mín (c ≥ 0):", min_value=0.0, value=20.0, step=5.0, key="m_c")
            d_of = s2.number_input("Pendiente de Oferta (+d, d > 0):", min_value=0.05, value=3.0, step=0.25, key="m_d")

            subheader_tarjeta("2. Política de Intervención Estatal")
            politica = st.selectbox(
                "Seleccione el escenario regulatorio:",
                [
                    "Libre Mercado (Sin intervención)",
                    "Impuesto Unitario (t por unidad vendida)",
                    "Subsidio Unitario (s por unidad vendida)",
                    "Precio Máximo (Control de precios / Tope)",
                    "Precio Mínimo (Precio de garantía)",
                ],
                key="m_pol",
            )

            valor_pol = 0.0
            if politica.startswith("Impuesto"):
                valor_pol = st.slider("Monto del impuesto unitario (t):", min_value=0.0, max_value=float(max(a_dem - c_of, 10.0)), value=15.0, step=1.0, key="m_t")
            elif politica.startswith("Subsidio"):
                valor_pol = st.slider("Monto del subsidio unitario (s):", min_value=0.0, max_value=50.0, value=15.0, step=1.0, key="m_s")
            elif politica.startswith("Precio Máximo"):
                valor_pol = st.slider("Precio Máximo legal (P_max):", min_value=float(c_of), max_value=float(a_dem), value=50.0, step=1.0, key="m_pmax")
            elif politica.startswith("Precio Mínimo"):
                valor_pol = st.slider("Precio Mínimo legal (P_min):", min_value=float(c_of), max_value=float(a_dem), value=80.0, step=1.0, key="m_pmin")

    if a_dem <= c_of:
        st.error("⛔ La disponibilidad máxima a pagar (a) debe ser mayor que el precio mínimo de oferta (c) para que exista intercambio positivo.")
    else:
        # Equilibrio competitivo libre: a - b*Q = c + d*Q
        q_eq = (a_dem - c_of) / (b_dem + d_of)
        p_eq = a_dem - b_dem * q_eq

        ec_libre = 0.5 * (a_dem - p_eq) * q_eq
        ep_libre = 0.5 * (p_eq - c_of) * q_eq
        w_libre = ec_libre + ep_libre

        # Elasticidades punto en el equilibrio libre: (dQ/dP)*(P/Q)
        elast_d = -(1.0 / b_dem) * (p_eq / q_eq)
        elast_s = (1.0 / d_of) * (p_eq / q_eq)

        # Cálculos con intervención
        q_int = q_eq
        p_cons = p_eq
        p_prod = p_eq
        recaudacion = 0.0
        pie_dwl = 0.0
        nota_pol = "El mercado opera en equilibrio competitivo eficiente (Pérdida de eficiencia = 0)."

        if politica.startswith("Impuesto"):
            q_int = max(0.0, (a_dem - c_of - valor_pol) / (b_dem + d_of))
            p_cons = a_dem - b_dem * q_int
            p_prod = c_of + d_of * q_int
            recaudacion = valor_pol * q_int
            pie_dwl = 0.5 * valor_pol * (q_eq - q_int)
            carga_c = ((p_cons - p_eq) / valor_pol * 100.0) if valor_pol > 0 else 0.0
            carga_p = 100.0 - carga_c if valor_pol > 0 else 0.0
            nota_pol = (
                f"**Incidencia Fiscal:** El consumidor absorbe el **{carga_c:.1f}%** del impuesto "
                f"($P_c = {_moneda(p_cons)}$) y el productor absorbe el **{carga_p:.1f}%** ($P_v = {_moneda(p_prod)}$)."
            )
        elif politica.startswith("Subsidio"):
            q_int = (a_dem - c_of + valor_pol) / (b_dem + d_of)
            p_cons = max(0.0, a_dem - b_dem * q_int)
            p_prod = c_of + d_of * q_int
            recaudacion = -valor_pol * q_int
            pie_dwl = 0.5 * valor_pol * (q_int - q_eq)
            nota_pol = f"**Costo Fiscal del Subsidio:** `{_moneda(abs(recaudacion))}` · Sobreproducción: `{q_int - q_eq:.2f}` unidades."
        elif politica.startswith("Precio Máximo"):
            if valor_pol < p_eq:
                q_int = max(0.0, (valor_pol - c_of) / d_of)
                q_dem_tope = (a_dem - valor_pol) / b_dem
                p_prod = valor_pol
                p_cons_reserva = a_dem - b_dem * q_int
                p_cons = valor_pol
                pie_dwl = 0.5 * (p_cons_reserva - p_prod) * (q_eq - q_int)
                nota_pol = f"**Precio Máximo Vinculante:** Genera una **escasez (exceso de demanda)** de `{q_dem_tope - q_int:.2f}` unidades."
            else:
                nota_pol = "El precio máximo es superior al equilibrio competitivo: **no es vinculante**."
        elif politica.startswith("Precio Mínimo"):
            if valor_pol > p_eq:
                q_int = max(0.0, (a_dem - valor_pol) / b_dem)
                q_of_min = (valor_pol - c_of) / d_of
                p_cons = valor_pol
                p_prod_costo = c_of + d_of * q_int
                p_prod = valor_pol
                pie_dwl = 0.5 * (p_cons - p_prod_costo) * (q_eq - q_int)
                nota_pol = f"**Precio Mínimo Vinculante:** Genera un **excedente de oferta** de `{q_of_min - q_int:.2f}` unidades."
            else:
                nota_pol = "El precio mínimo es inferior al equilibrio competitivo: **no es vinculante**."

        ec_int = 0.5 * (a_dem - (a_dem - b_dem * q_int)) * q_int if not politica.startswith("Precio Máximo") else (0.5 * (a_dem + (a_dem - b_dem * q_int) - 2 * p_cons) * q_int)
        ep_int = 0.5 * ((c_of + d_of * q_int) - c_of) * q_int if not politica.startswith("Precio Mínimo") else (0.5 * (2 * p_prod - c_of - (c_of + d_of * q_int)) * q_int)

        with col_m2:
            with st.container(border=True):
                header_tarjeta("Gráfica de Equilibrio de Marshall (Q en X, P en Y)")
                q_max_plot = max(a_dem / b_dem, q_int * 1.3, q_eq * 1.4)
                qs = np.linspace(0, q_max_plot, 300)
                p_dem_vec = a_dem - b_dem * qs
                p_of_vec = c_of + d_of * qs

                fig, ax = _lienzo_econ(titulo="Mercado, Excedentes y Pérdida de Eficiencia")
                ax.plot(qs, p_dem_vec, color=AZUL, lw=2.5, label=f"Demanda: P = {a_dem:g} − {b_dem:g}Q")
                ax.plot(qs, p_of_vec, color=NARANJA, lw=2.5, label=f"Oferta: P = {c_of:g} + {d_of:g}Q")

                # Sombrear Excedente del Consumidor y del Productor hasta q_int
                qs_sub = np.linspace(0, min(q_int, q_eq), 120)
                ax.fill_between(
                    qs_sub,
                    p_cons if politica != "Precio Máximo (Control de precios / Tope)" else valor_pol,
                    a_dem - b_dem * qs_sub,
                    color=AZUL,
                    alpha=0.18,
                    label=f"Excedente Consumidor ({_moneda(ec_int)})",
                )
                ax.fill_between(
                    qs_sub,
                    c_of + d_of * qs_sub,
                    p_prod if politica != "Precio Mínimo (Precio de garantía)" else valor_pol,
                    color=VERDE,
                    alpha=0.18,
                    label=f"Excedente Productor ({_moneda(ep_int)})",
                )

                # Sombrear Pérdida Irrecuperable de Eficiencia (Peso Muerto)
                if abs(q_int - q_eq) > 1e-5:
                    q_lo, q_hi = min(q_int, q_eq), max(q_int, q_eq)
                    qs_dwl = np.linspace(q_lo, q_hi, 80)
                    ax.fill_between(
                        qs_dwl,
                        c_of + d_of * qs_dwl,
                        a_dem - b_dem * qs_dwl,
                        color=ROJO,
                        alpha=0.32,
                        label=f"Peso Muerto / PIE ({_moneda(pie_dwl)})",
                    )

                ax.plot([q_eq], [p_eq], "o", color=OSCURO, ms=8, zorder=7, label=f"Eq. Libre (Q*={q_eq:.2f}, P*={_moneda(p_eq)})")
                ax.plot([q_eq, q_eq], [0, p_eq], color=OSCURO, ls=":", lw=1.2)
                ax.plot([0, q_eq], [p_eq, p_eq], color=OSCURO, ls=":", lw=1.2)

                ax.set_xlim(0, q_max_plot)
                ax.set_ylim(0, max(a_dem, p_prod, p_cons) * 1.12)
                ax.legend(loc="upper right", fontsize=8.0, framealpha=0.94)
                mostrar_figura_segura(fig)

        with st.container(border=True):
            subheader_tarjeta("Análisis de Bienestar, Elasticidades e Incidencia")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Equilibrio Libre (Q*, P*)", f"{q_eq:.2f} u.  ·  {_moneda(p_eq)}")
            m2.metric("Excedente Consumidor (EC)", _moneda(ec_int), delta=f"{ec_int - ec_libre:+,.2f} vs. libre" if abs(ec_int - ec_libre) > 1e-2 else None)
            m3.metric("Excedente Productor (EP)", _moneda(ep_int), delta=f"{ep_int - ep_libre:+,.2f} vs. libre" if abs(ep_int - ep_libre) > 1e-2 else None)
            m4.metric("Pérdida de Eficiencia (PIE)", _moneda(pie_dwl))

            st.info(nota_pol)
            st.markdown(
                f"| Indicador en el Equilibrio Competitivo | Fórmula | Valor | Clasificación |\n|---|---|---|---|\n"
                f"| **Elasticidad Precio de la Demanda ($\\varepsilon_d$)** | $\\frac{{dQ_d}}{{dP}}\\frac{{P^*}}{{Q^*}}$ | `{elast_d:.4f}` | {'Elástica (|ε| > 1)' if abs(elast_d) > 1.001 else 'Inelástica (|ε| < 1)' if abs(elast_d) < 0.999 else 'Unitaria (|ε| = 1)'} |\n"
                f"| **Elasticidad Precio de la Oferta ($\\varepsilon_s$)** | $\\frac{{dQ_s}}{{dP}}\\frac{{P^*}}{{Q^*}}$ | `{elast_s:.4f}` | {'Elástica (ε > 1)' if elast_s > 1.001 else 'Inelástica (ε < 1)'} |\n"
                f"| **Bienestar Social Máximo ($W^* = EC + EP$)** | $\\int_0^{{Q^*}}(P_d - P_s)dQ$ | `{_moneda(w_libre)}` | Óptimo de Pareto (1.er Teorema del Bienestar) |"
            )


# ==============================================================================
# PESTAÑA 2: TEORÍA DEL CONSUMIDOR Y DESCOMPOSICIÓN DE SLUTSKY
# ==============================================================================
with tab_consumidor:
    col_u1, col_u2 = st.columns([1.05, 1.3], gap="large")

    with col_u1:
        with st.container(border=True):
            header_tarjeta("Preferencias del Consumidor y Restricción Presupuestaria")
            tipo_util = st.selectbox(
                "Familia de función de utilidad U(x₁, x₂):",
                [
                    "1. Cobb-Douglas: U(x₁, x₂) = x₁^α · x₂^β",
                    "2. Sustitutos Perfectos: U(x₁, x₂) = α·x₁ + β·x₂",
                    "3. Complementos Perfectos (Leontief): U(x₁, x₂) = mín{α·x₁, β·x₂}",
                ],
                key="u_tipo",
            )
            u_c1, u_c2 = st.columns(2)
            alpha_u = u_c1.number_input("Parámetro α (> 0):", min_value=0.05, value=0.6, step=0.1, key="u_alpha")
            beta_u = u_c2.number_input("Parámetro β (> 0):", min_value=0.05, value=0.4, step=0.1, key="u_beta")

            subheader_tarjeta("Precios e Ingreso Nominal (p₁·x₁ + p₂·x₂ = M)")
            p_c1, p_c2, p_c3 = st.columns(3)
            p1_u = p_c1.number_input("Precio p₁ ($):", min_value=0.1, value=4.0, step=0.5, key="u_p1")
            p2_u = p_c2.number_input("Precio p₂ ($):", min_value=0.1, value=5.0, step=0.5, key="u_p2")
            M_ing = p_c3.number_input("Ingreso M ($):", min_value=1.0, value=100.0, step=10.0, key="u_M")

            subheader_tarjeta("Análisis de Estática Comparativa (Ecuación de Slutsky)")
            p1_nuevo = st.number_input("Nuevo precio p₁′ (para descomponer Efecto Sustitución e Ingreso):", min_value=0.1, value=8.0, step=0.5, key="u_p1_new")

    def _demanda_marshalliana(tipo, a, b, p1, p2, M):
        if tipo.startswith("1."):
            x1 = (a / (a + b)) * (M / p1)
            x2 = (b / (a + b)) * (M / p2)
            u_val = (x1 ** a) * (x2 ** b)
        elif tipo.startswith("2."):
            if a / p1 > b / p2 + 1e-9:
                x1, x2 = M / p1, 0.0
            elif a / p1 < b / p2 - 1e-9:
                x1, x2 = 0.0, M / p2
            else:
                x1, x2 = M / (2 * p1), M / (2 * p2)
            u_val = a * x1 + b * x2
        else:
            # a*x1 = b*x2 => x2 = (a/b)*x1 => p1*x1 + p2*(a/b)*x1 = M
            x1 = M / (p1 + p2 * (a / b))
            x2 = (a / b) * x1
            u_val = min(a * x1, b * x2)
        return x1, x2, u_val

    # Cesta inicial A (con p1), Cesta final C (con p1_nuevo) y Cesta intermedia de Slutsky B (ingreso compensado M_comp = p1'*x1_A + p2*x2_A)
    x1_A, x2_A, U_A = _demanda_marshalliana(tipo_util, alpha_u, beta_u, p1_u, p2_u, M_ing)
    x1_C, x2_C, U_C = _demanda_marshalliana(tipo_util, alpha_u, beta_u, p1_nuevo, p2_u, M_ing)
    M_slutsky = p1_nuevo * x1_A + p2_u * x2_A
    x1_B, x2_B, _ = _demanda_marshalliana(tipo_util, alpha_u, beta_u, p1_nuevo, p2_u, M_slutsky)

    efecto_sustitucion = x1_B - x1_A
    efecto_ingreso = x1_C - x1_B
    efecto_total = x1_C - x1_A

    with col_u2:
        with st.container(border=True):
            header_tarjeta("Mapa de Indiferencia, Recta Presupuestaria y Slutsky")
            fig_u, ax_u = _lienzo_econ(xlabel="Bien 1 (x₁)", ylabel="Bien 2 (x₂)", titulo="Elección Óptima del Consumidor y Cambio en p₁")
            max_x1 = max(M_ing / p1_u, M_ing / p1_nuevo, M_slutsky / p1_nuevo) * 1.15
            max_x2 = max(M_ing / p2_u, M_slutsky / p2_u) * 1.15
            xs_b = np.linspace(0.01, max_x1, 300)

            # Recta presupuestaria inicial, final y compensada de Slutsky
            ax_u.plot([0, M_ing / p1_u], [M_ing / p2_u, 0], color=AZUL, lw=2.3, label=f"Presupuesto Inicial (p₁={p1_u:g})")
            if abs(p1_nuevo - p1_u) > 1e-6:
                ax_u.plot([0, M_ing / p1_nuevo], [M_ing / p2_u, 0], color=ROJO, lw=2.2, label=f"Presupuesto Final (p₁′={p1_nuevo:g})")
                ax_u.plot([0, M_slutsky / p1_nuevo], [M_slutsky / p2_u, 0], color=VERDE, lw=1.6, ls="--", label="Recta Compensada (Slutsky)")

            # Curva de indiferencia U_A
            if tipo_util.startswith("1.") and U_A > 0:
                ys_ind_A = (U_A / (xs_b ** alpha_u)) ** (1.0 / beta_u)
                mask_ind = ys_ind_A <= max_x2
                ax_u.plot(xs_b[mask_ind], ys_ind_A[mask_ind], color=AZUL, ls=":", lw=1.8, label=f"Curva Indiferencia U₀ = {U_A:.2f}")
            elif tipo_util.startswith("2."):
                ax_u.plot([0, U_A / alpha_u], [U_A / beta_u, 0], color=AZUL, ls=":", lw=1.8, label=f"Curva Indiferencia U₀ = {U_A:.2f}")
            else:
                vx_l, vy_l = U_A / alpha_u, U_A / beta_u
                ax_u.plot([vx_l, max_x1], [vy_l, vy_l], color=AZUL, ls=":", lw=1.8, label=f"Indiferencia Leontief U₀ = {U_A:.2f}")
                ax_u.plot([vx_l, vx_l], [vy_l, max_x2], color=AZUL, ls=":", lw=1.8)

            ax_u.plot([x1_A], [x2_A], "o", color=AZUL, ms=8.5, zorder=8, label=f"Cesta Inicial A ({x1_A:.2f}, {x2_A:.2f})")
            if abs(p1_nuevo - p1_u) > 1e-6:
                ax_u.plot([x1_B], [x2_B], "s", color=VERDE, ms=7.5, zorder=8, label=f"Cesta Compensada B ({x1_B:.2f}, {x2_B:.2f})")
                ax_u.plot([x1_C], [x2_C], "^", color=ROJO, ms=8.5, zorder=8, label=f"Cesta Final C ({x1_C:.2f}, {x2_C:.2f})")

            ax_u.set_xlim(0, max_x1)
            ax_u.set_ylim(0, max_x2)
            ax_u.legend(loc="upper right", fontsize=8.0, framealpha=0.94)
            mostrar_figura_segura(fig_u)

    with st.container(border=True):
        subheader_tarjeta("Demandas Óptimas y Descomposición de la Ecuación de Slutsky")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Cesta Óptima Inicial (x₁*, x₂*)", f"({x1_A:.2f},  {x2_A:.2f})")
        k2.metric("Efecto Sustitución (Δx₁ˢ)", f"{efecto_sustitucion:+.3f}")
        k3.metric("Efecto Ingreso (Δx₁ᴹ)", f"{efecto_ingreso:+.3f}")
        k4.metric("Efecto Total (Δx₁ = Δx₁ˢ + Δx₁ᴹ)", f"{efecto_total:+.3f}")

        st.latex(
            r"\text{Condición de Tangencia: } \operatorname{RMS}_{1,2} = \frac{\partial U / \partial x_1}{\partial U / \partial x_2} = \frac{p_1}{p_2}, "
            r"\qquad \underbrace{\Delta x_1}_{\text{Efecto Total}} = \underbrace{\Delta x_1^S}_{\text{Efecto Sustitución}} + \underbrace{\Delta x_1^M}_{\text{Efecto Ingreso}}"
        )


# ==============================================================================
# PESTAÑA 3: TEORÍA DEL PRODUCTOR (ISOCUANTAS, ISOCOSTOS Y RENDIMIENTOS A ESCALA)
# ==============================================================================
with tab_productor:
    c_pr1, c_pr2 = st.columns([1.05, 1.3], gap="large")
    with c_pr1:
        with st.container(border=True):
            header_tarjeta("Función de Producción Cobb-Douglas: Q(L, K) = A · L^α · K^β")
            p1, p2, p3 = st.columns(3)
            A_tfp = p1.number_input("Productividad Total (A):", min_value=0.1, value=10.0, step=1.0, key="pr_A")
            a_prod = p2.number_input("Elasticidad Trabajo (α):", min_value=0.05, value=0.5, step=0.1, key="pr_a")
            b_prod = p3.number_input("Elasticidad Capital (β):", min_value=0.05, value=0.5, step=0.1, key="pr_b")

            f1, f2, f3 = st.columns(3)
            w_sal = f1.number_input("Salario por unidad de L (w):", min_value=0.1, value=20.0, step=2.0, key="pr_w")
            r_cap = f2.number_input("Renta por unidad de K (r):", min_value=0.1, value=20.0, step=2.0, key="pr_r")
            Q_meta = f3.number_input("Nivel de Producción Meta (Q₀):", min_value=1.0, value=100.0, step=10.0, key="pr_Q")

            grado_hom = a_prod + b_prod
            rend_escala = (
                "Rendimientos Constantes a Escala (α + β = 1)" if abs(grado_hom - 1.0) < 1e-6
                else "Rendimientos Crecientes a Escala (α + β > 1)" if grado_hom > 1.0
                else "Rendimientos Decrecientes a Escala (α + β < 1)"
            )

            # Minimización de costos: K = (beta * w) / (alpha * r) * L
            razon_KL = (b_prod * w_sal) / (a_prod * r_cap)
            L_opt = ((Q_meta / A_tfp) * ((razon_KL) ** (-b_prod))) ** (1.0 / grado_hom)
            K_opt = razon_KL * L_opt
            costo_min = w_sal * L_opt + r_cap * K_opt

            st.info(f"**Diagnóstico Tecnológico ($\alpha + \beta = {grado_hom:.2f}$):** {rend_escala}")
            st.markdown(
                f"| Métrica de Eficiencia Productiva | Valor Óptimo |\n|---|---|\n"
                f"| **Demanda Condicionada de Trabajo ($L^*$)** | `{L_opt:.4f}` unidades |\n"
                f"| **Demanda Condicionada de Capital ($K^*$)** | `{K_opt:.4f}` unidades |\n"
                f"| **Costo Mínimo de Producción $C(w, r, Q_0)$** | **`{_moneda(costo_min)}`** |\n"
                f"| **Ecuación de la Senda de Expansión** | $K = {razon_KL:.4f}\\,L$ ($\\text{{RMST}}_{{L,K}} = w/r = {w_sal/r_cap:.3f}$) |"
            )

    with c_pr2:
        with st.container(border=True):
            header_tarjeta("Isocuanta, Recta de Isocosto y Senda de Expansión")
            fig_p, ax_p = _lienzo_econ(xlabel="Trabajo (L)", ylabel="Capital (K)", titulo=f"Minimización de Costos para Q₀ = {Q_meta:g}")
            lim_L = L_opt * 2.3
            lim_K = K_opt * 2.3
            Ls = np.linspace(0.05 * L_opt, lim_L, 300)

            # Isocuanta Q = Q_meta
            Ks_iso = ((Q_meta / A_tfp) / (Ls ** a_prod)) ** (1.0 / b_prod)
            mask_k = Ks_iso <= lim_K
            ax_p.plot(Ls[mask_k], Ks_iso[mask_k], color=AZUL, lw=2.5, label=f"Isocuanta Q₀ = {Q_meta:g}")

            # Recta de Isocosto wL + rK = costo_min
            ax_p.plot([0, costo_min / w_sal], [costo_min / r_cap, 0], color=NARANJA, lw=2.2, label=f"Isocosto Mínimo ({_moneda(costo_min)})")

            # Senda de expansión K = razon_KL * L
            ax_p.plot([0, lim_L], [0, razon_KL * lim_L], color=VERDE, ls="--", lw=1.8, label=f"Senda de Expansión (K = {razon_KL:.2f}L)")
            ax_p.plot([L_opt], [K_opt], "o", color=ROJO, ms=8.5, zorder=8, label=f"Óptimo Técnico ({L_opt:.2f}, {K_opt:.2f})")

            ax_p.set_xlim(0, lim_L)
            ax_p.set_ylim(0, lim_K)
            ax_p.legend(loc="upper right", fontsize=8.0, framealpha=0.94)
            mostrar_figura_segura(fig_p)


# ==============================================================================
# PESTAÑA 4: ESTRUCTURA DE COSTOS DE LA EMPRESA (CFMe, CVMe, CTMe, CMg)
# ==============================================================================
with tab_costos:
    with st.container(border=True):
        header_tarjeta("Análisis Completo de Costos de Corto Plazo y Decisiones de Oferta")

        modo_costo = st.radio(
            "Modo de definición de la función de Costo Total CT(Q):",
            ["1. Modelo Cúbico Clásico: CT(Q) = CF + a·Q − b·Q² + c·Q³", "2. Función Simbólica Libre con Teclado Matemático"],
            horizontal=True,
            key="cost_modo",
        )

        q_sym = sp.Symbol("Q", positive=True)
        CT_expr = None

        if modo_costo.startswith("1."):
            cc1, cc2, cc3, cc4, cc5 = st.columns(5)
            cf_val = cc1.number_input("Costo Fijo (CF):", min_value=0.0, value=100.0, step=10.0, key="c_cf")
            a_c = cc2.number_input("Coeficiente lineal (a):", min_value=0.1, value=50.0, step=5.0, key="c_a")
            b_c = cc3.number_input("Coef. cuadrático (−b):", min_value=0.0, value=4.0, step=0.5, key="c_b")
            c_c = cc4.number_input("Coef. cúbico (+c):", min_value=0.01, value=0.2, step=0.05, key="c_c")
            p_merc = cc5.number_input("Precio de Mercado P ($):", min_value=0.1, value=35.0, step=2.0, key="c_pm")
            CT_expr = sp.nsimplify(cf_val) + sp.nsimplify(a_c) * q_sym - sp.nsimplify(b_c) * (q_sym ** 2) + sp.nsimplify(c_c) * (q_sym ** 3)
        else:
            p_merc = st.number_input("Precio de Mercado P ($):", min_value=0.1, value=35.0, step=2.0, key="c_pm_kb")
            if _TIENE_TECLADO:
                st.caption("Escribe $CT(Q)$ usando la variable $Q$ (o $x$) y pulsa **↵**:")
                lat_ct = teclado_matematico(
                    "kb_cost_ct",
                    layout="economia",
                    valor_inicial="100+50x-4x^{2}+0.2x^{3}",
                    placeholder="Escribe CT(x) y pulsa ↵",
                    acoplado=False,
                )
                if lat_ct:
                    try:
                        raw_ct = latex_a_sympy(lat_ct)
                        if isinstance(raw_ct, sp.Expr):
                            CT_expr = raw_ct.subs({s: q_sym for s in raw_ct.free_symbols if s.name in ("x", "q", "Q")})
                    except (ErrorLatex, ErrorNoSoportado) as e:
                        st.error("Error en CT(Q): " + str(e))
            else:
                txt_ct = st.text_input("Escriba CT(Q):", value="100 + 50*Q - 4*Q^2 + 0.2*Q^3")
                raw_ct = leer_expresion_st(txt_ct, solo_reales=True)
                if raw_ct is not None:
                    CT_expr = raw_ct.subs({s: q_sym for s in raw_ct.free_symbols if s.name in ("x", "q", "Q")})

        if CT_expr is not None:
            CF_sim = sp.simplify(CT_expr.subs(q_sym, 0))
            CV_sim = sp.simplify(CT_expr - CF_sim)
            CMg_sim = sp.simplify(sp.diff(CT_expr, q_sym))
            CFMe_sim = sp.simplify(CF_sim / q_sym)
            CVMe_sim = sp.simplify(CV_sim / q_sym)
            CTMe_sim = sp.simplify(CT_expr / q_sym)

            st.latex(
                "CT(Q) = " + sp.latex(CT_expr)
                + r", \quad CMg(Q) = " + sp.latex(CMg_sim)
                + r", \quad CTMe(Q) = " + sp.latex(CTMe_sim)
                + r", \quad CVMe(Q) = " + sp.latex(CVMe_sim)
            )

            # Evaluación vectorial numérica (integrando cfme_vector)
            q_vector = np.linspace(0.5, 22.0, 250)
            f_ct = sp.lambdify(q_sym, CT_expr, "numpy")
            f_cv = sp.lambdify(q_sym, CV_sim, "numpy")
            f_cmg = sp.lambdify(q_sym, CMg_sim, "numpy")

            cf_num = float(sp.N(CF_sim))
            ct_vector = np.broadcast_to(np.asarray(f_ct(q_vector), dtype=float), q_vector.shape)
            cv_vector = np.broadcast_to(np.asarray(f_cv(q_vector), dtype=float), q_vector.shape)
            cmg_vector = np.broadcast_to(np.asarray(f_cmg(q_vector), dtype=float), q_vector.shape)

            cfme_vector = cf_num / q_vector
            cvme_vector = cv_vector / q_vector
            ctme_vector = ct_vector / q_vector

            idx_cierre = int(np.argmin(cvme_vector))
            q_cierre, p_cierre = float(q_vector[idx_cierre]), float(cvme_vector[idx_cierre])

            idx_eq_emp = int(np.argmin(ctme_vector))
            q_eq_emp, p_eq_emp = float(q_vector[idx_eq_emp]), float(ctme_vector[idx_eq_emp])

            m1, m2, m3 = st.columns(3)
            m1.metric("Costo Fijo Total (CF)", _moneda(cf_num))
            m2.metric("Punto de Cierre (Mín CVMe)", f"Q = {q_cierre:.2f}  ·  P_cierre = {_moneda(p_cierre)}")
            m3.metric("Punto de Nivelación / Equilibrio (Mín CTMe)", f"Q = {q_eq_emp:.2f}  ·  P_eq = {_moneda(p_eq_emp)}")

            if p_merc < p_cierre:
                st.error(f"⛔ **Decisión a Corto Plazo ($P = {_moneda(p_merc)} < P_{{\\text{{cierre}}}}$):** La empresa **DEBE CERRAR** temporalmente ($Q^* = 0$) porque el precio no cubre ni siquiera los costos variables medios.")
            elif p_merc < p_eq_emp:
                st.warning(f"⚠️ **Decisión a Corto Plazo ($P_{{\\text{{cierre}}}} \\le P = {_moneda(p_merc)} < P_{{\\text{{eq}}}}$):** La empresa **PRODUCE CON PÉRDIDAS** porque cubre sus costos variables y amortiza parte de los costos fijos.")
            else:
                st.success(f"✅ **Decisión a Corto Plazo ($P = {_moneda(p_merc)} \\ge P_{{\\text{{eq}}}}$):** La empresa **OPERA CON BENEFICIOS ECONÓMICOS EXTRAORDINARIOS**.")

            cg1, cg2 = st.columns([1.3, 1])
            with cg1:
                fig_c, ax_c = _lienzo_econ(xlabel="Producción (Q)", ylabel="Costo Unitario / Marginal ($)", titulo="Curvas de Costos Medios y Marginal (CFMe, CVMe, CTMe, CMg)")
                ax_c.plot(q_vector, cmg_vector, color=ROJO, lw=2.5, label="Costo Marginal (CMg)")
                ax_c.plot(q_vector, ctme_vector, color=AZUL, lw=2.3, label="Costo Total Medio (CTMe)")
                ax_c.plot(q_vector, cvme_vector, color=VERDE, lw=2.1, ls="--", label="Costo Variable Medio (CVMe)")
                ax_c.plot(q_vector, cfme_vector, color=MORADO, lw=1.8, ls=":", label="Costo Fijo Medio (CFMe = CF/Q)")
                ax_c.axhline(p_merc, color=NARANJA, lw=1.6, ls="-.", label=f"Precio Mercado P = {_moneda(p_merc)}")
                ax_c.plot([q_cierre], [p_cierre], "o", color=VERDE, ms=8, zorder=7)
                ax_c.plot([q_eq_emp], [p_eq_emp], "o", color=AZUL, ms=8, zorder=7)
                ax_c.set_ylim(0, max(p_eq_emp * 2.2, p_merc * 1.4))
                ax_c.legend(loc="upper right", fontsize=8.0, framealpha=0.94)
                mostrar_figura_segura(fig_c)

            with cg2:
                q_tabla = np.arange(1, 21, 1, dtype=float)
                df_costos = pd.DataFrame({
                    "Q": q_tabla.astype(int),
                    "CFMe": cf_num / q_tabla,
                    "CVMe": np.asarray(f_cv(q_tabla), dtype=float) / q_tabla,
                    "CTMe": np.asarray(f_ct(q_tabla), dtype=float) / q_tabla,
                    "CMg": np.asarray(f_cmg(q_tabla), dtype=float),
                })
                st.dataframe(
                    df_costos.style.format({
                        "CFMe": f"{SIMB_PESO}{{:,.2f}}",
                        "CVMe": f"{SIMB_PESO}{{:,.2f}}",
                        "CTMe": f"{SIMB_PESO}{{:,.2f}}",
                        "CMg": f"{SIMB_PESO}{{:,.2f}}",
                    }),
                    use_container_width=True,
                    height=390,
                    hide_index=True,
                )


# ==============================================================================
# PESTAÑA 5: MONOPOLIO Y OLIGOPOLIO (COURNOT, STACKELBERG Y COLUSIÓN)
# ==============================================================================
with tab_estructuras:
    sub_mon, sub_oli = st.tabs([
        "👑 1. Monopolio vs. Competencia Perfecta (Índice de Lerner y Peso Muerto)",
        "♟️ 2. Duopolio de Cournot, Stackelberg y Colusión (Curvas de Reacción)",
    ])

    with sub_mon:
        with st.container(border=True):
            header_tarjeta("Equilibrio de Monopolio (IMg = CMg) frente a Competencia Perfecta (P = CMg)")
            m_in1, m_in2, m_in3, m_in4 = st.columns(4)
            a_m = m_in1.number_input("Intercepto Demanda (a):", min_value=5.0, value=100.0, step=5.0, key="mon_a")
            b_m = m_in2.number_input("Pendiente Demanda (b > 0):", min_value=0.1, value=2.0, step=0.25, key="mon_b")
            c_m = m_in3.number_input("Costo Marginal base (c):", min_value=0.0, value=20.0, step=2.0, key="mon_c")
            d_m = m_in4.number_input("Pendiente de CMg (d ≥ 0):", min_value=0.0, value=1.0, step=0.25, key="mon_d")

            if a_m <= c_m:
                st.error("El intercepto de la demanda (a) debe ser mayor que el costo marginal inicial (c).")
            else:
                # IMg(Q) = a - 2*b*Q; CMg(Q) = c + d*Q
                q_mon = (a_m - c_m) / (2 * b_m + d_m)
                p_mon = a_m - b_m * q_mon
                cmg_mon = c_m + d_m * q_mon
                lerner = (p_mon - cmg_mon) / p_mon if p_mon > 0 else 0.0

                q_cp = (a_m - c_m) / (b_m + d_m)
                p_cp = a_m - b_m * q_cp
                pie_mon = 0.5 * (p_mon - cmg_mon) * (q_cp - q_mon)

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Óptimo Monopolio (Q_M, P_M)", f"{q_mon:.2f} u.  ·  {_moneda(p_mon)}")
                k2.metric("Competencia Perfecta (Q_CP, P_CP)", f"{q_cp:.2f} u.  ·  {_moneda(p_cp)}")
                k3.metric("Índice de Lerner L = (P − CMg)/P", f"{lerner:.4f} ({lerner*100:.1f}%)")
                k4.metric("Pérdida de Eficiencia del Monopolio", _moneda(pie_mon))

                qs_m = np.linspace(0, a_m / b_m, 250)
                fig_m, ax_m = _lienzo_econ(titulo="Equilibrio de Monopolio (IMg = CMg) y Pérdida de Bienestar")
                ax_m.plot(qs_m, a_m - b_m * qs_m, color=AZUL, lw=2.5, label="Demanda P(Q)")
                ax_m.plot(qs_m, a_m - 2 * b_m * qs_m, color=MORADO, lw=2.0, ls="--", label="Ingreso Marginal IMg(Q)")
                ax_m.plot(qs_m, c_m + d_m * qs_m, color=NARANJA, lw=2.4, label="Costo Marginal CMg(Q)")

                qs_dwl_m = np.linspace(q_mon, q_cp, 80)
                ax_m.fill_between(
                    qs_dwl_m,
                    c_m + d_m * qs_dwl_m,
                    a_m - b_m * qs_dwl_m,
                    color=ROJO,
                    alpha=0.30,
                    label=f"Peso Muerto Monopolio ({_moneda(pie_mon)})",
                )
                ax_m.plot([q_mon], [p_mon], "o", color=ROJO, ms=8.5, zorder=8, label=f"Precio Monopolio ({_moneda(p_mon)})")
                ax_m.plot([q_cp], [p_cp], "o", color=VERDE, ms=8.5, zorder=8, label=f"Eq. Competitivo ({_moneda(p_cp)})")
                ax_m.set_xlim(0, a_m / b_m)
                ax_m.set_ylim(0, a_m * 1.1)
                ax_m.legend(loc="upper right", fontsize=8.0, framealpha=0.94)
                mostrar_figura_segura(fig_m)

    with sub_oli:
        with st.container(border=True):
            header_tarjeta("Teoría de Juegos en Duopolio: Cournot (Simultáneo) vs. Stackelberg (Líder-Seguidor)")
            st.caption("Demanda de mercado $P(Q) = a - b(q_1 + q_2)$ con costos marginales constantes $c_1$ y $c_2$.")

            o1, o2, o3, o4 = st.columns(4)
            a_ol = o1.number_input("Tamaño de mercado (a):", min_value=10.0, value=120.0, step=5.0, key="ol_a")
            b_ol = o2.number_input("Pendiente inversa (b > 0):", min_value=0.1, value=1.0, step=0.25, key="ol_b")
            c1_ol = o3.number_input("Costo Marginal Empresa 1 (c₁):", min_value=0.0, value=30.0, step=2.0, key="ol_c1")
            c2_ol = o4.number_input("Costo Marginal Empresa 2 (c₂):", min_value=0.0, value=30.0, step=2.0, key="ol_c2")

            if a_ol <= max(c1_ol, c2_ol):
                st.error("El parámetro 'a' debe superar los costos marginales c₁ y c₂.")
            else:
                # Cournot: q1 = (a - 2*c1 + c2)/(3b), q2 = (a - 2*c2 + c1)/(3b)
                q1_cour = max(0.0, (a_ol - 2 * c1_ol + c2_ol) / (3.0 * b_ol))
                q2_cour = max(0.0, (a_ol - 2 * c2_ol + c1_ol) / (3.0 * b_ol))
                Q_cour = q1_cour + q2_cour
                P_cour = a_ol - b_ol * Q_cour
                pi1_cour = (P_cour - c1_ol) * q1_cour
                pi2_cour = (P_cour - c2_ol) * q2_cour

                # Stackelberg (Empresa 1 Líder, Empresa 2 Seguidora):
                q1_stack = max(0.0, (a_ol - 2 * c1_ol + c2_ol) / (2.0 * b_ol))
                q2_stack = max(0.0, (a_ol - c2_ol - b_ol * q1_stack) / (2.0 * b_ol))
                Q_stack = q1_stack + q2_stack
                P_stack = a_ol - b_ol * Q_stack
                pi1_stack = (P_stack - c1_ol) * q1_stack
                pi2_stack = (P_stack - c2_ol) * q2_stack

                # Cártel / Colusión simétrica (con costo promedio si c1=c2)
                c_med = 0.5 * (c1_ol + c2_ol)
                Q_col = (a_ol - c_med) / (2.0 * b_ol)
                P_col = a_ol - b_ol * Q_col

                co1, co2 = st.columns([1.15, 1.2])
                with co1:
                    st.markdown(
                        f"| Modelo de Mercado | $q_1^*$ | $q_2^*$ | Total $Q^*$ | Precio $P^*$ | Beneficio $\\Pi_1$ | Beneficio $\\Pi_2$ |\n"
                        f"|---|---|---|---|---|---|---|\n"
                        f"| **Cournot-Nash (Simultáneo)** | `{q1_cour:.2f}` | `{q2_cour:.2f}` | `{Q_cour:.2f}` | `{_moneda(P_cour)}` | `{_moneda(pi1_cour)}` | `{_moneda(pi2_cour)}` |\n"
                        f"| **Stackelberg (1 Líder, 2 Seguidora)** | `{q1_stack:.2f}` | `{q2_stack:.2f}` | `{Q_stack:.2f}` | `{_moneda(P_stack)}` | `{_moneda(pi1_stack)}` | `{_moneda(pi2_stack)}` |\n"
                        f"| **Cártel / Colusión (Monopolio)** | `{Q_col/2:.2f}` | `{Q_col/2:.2f}` | `{Q_col:.2f}` | `{_moneda(P_col)}` | `{_moneda((P_col-c1_ol)*Q_col/2)}` | `{_moneda((P_col-c2_ol)*Q_col/2)}` |"
                    )
                    st.latex(
                        r"R_1(q_2) = \frac{a - c_1 - b\,q_2}{2b}, \qquad R_2(q_1) = \frac{a - c_2 - b\,q_1}{2b}"
                    )

                with co2:
                    max_q_ax = max((a_ol - c1_ol) / b_ol, (a_ol - c2_ol) / b_ol) * 1.05
                    q_grid = np.linspace(0, max_q_ax, 200)
                    r2_curve = np.maximum(0.0, (a_ol - c2_ol - b_ol * q_grid) / (2.0 * b_ol))
                    q1_from_r1 = np.maximum(0.0, (a_ol - c1_ol - b_ol * q_grid) / (2.0 * b_ol))

                    fig_o, ax_o = _lienzo_econ(xlabel="Producción Empresa 1 (q₁)", ylabel="Producción Empresa 2 (q₂)", titulo="Funciones de Mejor Respuesta (Curvas de Reacción)")
                    ax_o.plot(q1_from_r1, q_grid, color=AZUL, lw=2.4, label="Reacción Empresa 1: q₁ = R₁(q₂)")
                    ax_o.plot(q_grid, r2_curve, color=NARANJA, lw=2.4, label="Reacción Empresa 2: q₂ = R₂(q₁)")
                    ax_o.plot([q1_cour], [q2_cour], "o", color=ROJO, ms=8.5, zorder=8, label=f"Equilibrio Cournot-Nash ({q1_cour:.1f}, {q2_cour:.1f})")
                    ax_o.plot([q1_stack], [q2_stack], "s", color=VERDE, ms=8.5, zorder=8, label=f"Equilibrio Stackelberg ({q1_stack:.1f}, {q2_stack:.1f})")
                    ax_o.plot([Q_col / 2], [Q_col / 2], "^", color=MORADO, ms=8.5, zorder=8, label=f"Colusión / Cártel ({Q_col/2:.1f}, {Q_col/2:.1f})")
                    ax_o.set_xlim(0, max_q_ax)
                    ax_o.set_ylim(0, max_q_ax)
                    ax_o.legend(loc="upper right", fontsize=8.0, framealpha=0.94)
                    mostrar_figura_segura(fig_o)
