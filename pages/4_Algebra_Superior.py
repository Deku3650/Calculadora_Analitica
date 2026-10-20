# pages/4_Algebra_Superior.py
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import sympy as sp
from matplotlib.ticker import AutoMinorLocator
from sympy.ntheory.modular import crt

st.set_page_config(page_title="Álgebra Superior - MATHESIS", page_icon="🔢", layout="wide")

from estilos import cargar_estilos_globales, encabezado_pagina, header_tarjeta, subheader_tarjeta  # noqa: E402
from utils import (  # noqa: E402
    calcular_con_limite,
    gestionar_inventario_sidebar,
    inicializar_estado,
    leer_expresion_st,
    mostrar_figura_segura,
)

try:
    from teclado_matematico import teclado_matematico
    from interprete_latex import latex_a_sympy
    _TIENE_TECLADO = True
except Exception:
    _TIENE_TECLADO = False

cargar_estilos_globales()
inicializar_estado()

AZUL = "#0369a1"
NARANJA = "#ea580c"
VERDE = "#15803d"
ROJO = "#dc2626"
OSCURO = "#1e293b"
CLARO = "#cbd5e1"
FONDO = "#ffffff"


def _leer_seguro(texto: str):
    if texto is None or not str(texto).strip():
        return None
    try:
        return leer_expresion_st(str(texto).strip())
    except Exception:
        st.error("La expresión ingresada no es válida.")
        return None


def _formatear_factores(n: int) -> str:
    if n == 1:
        return r"1 \;\text{(unidad / coprimos)}"
    factores = sp.factorint(n)
    partes = []
    for p, e in factores.items():
        if e > 1:
            partes.append(str(p) + "^{" + str(e) + "}")
        else:
            partes.append(str(p))
    return r" \cdot ".join(partes)


def _fig_argand(complejos_lista, titulo="Plano Complejo de Argand", dibujar_circulo_r=None):
    fig, ax = plt.subplots(figsize=(6.2, 4.8), dpi=110, facecolor=FONDO)
    ax.set_facecolor("#fbfdff")
    ax.set_aspect("equal", adjustable="box")
    ax.minorticks_on()
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.grid(True, which="major", color=CLARO, lw=0.9, alpha=0.9)
    ax.grid(True, which="minor", color="#e2e8f0", lw=0.5, alpha=0.8)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(OSCURO)
        ax.spines[lado].set_linewidth(1.4)
    ax.axhline(0, color=OSCURO, lw=1.0, alpha=0.7)
    ax.axvline(0, color=OSCURO, lw=1.0, alpha=0.7)
    ax.tick_params(colors=OSCURO, labelsize=8.5)

    max_r = 1.0
    if dibujar_circulo_r is not None and dibujar_circulo_r > 0:
        ts = np.linspace(0, 2 * np.pi, 240)
        ax.plot(dibujar_circulo_r * np.cos(ts), dibujar_circulo_r * np.sin(ts), color=CLARO, ls="--", lw=1.4, zorder=2)
        max_r = max(max_r, float(dibujar_circulo_r))

    for etiq, z_val, col in complejos_lista:
        zc = complex(sp.N(z_val))
        re_v, im_v = zc.real, zc.imag
        max_r = max(max_r, abs(re_v), abs(im_v))
        ax.annotate(
            "",
            xy=(re_v, im_v),
            xytext=(0, 0),
            arrowprops=dict(arrowstyle="-|>", color=col, lw=2.2),
            zorder=5,
        )
        ax.plot([re_v], [im_v], "o", color=col, mec="white", mew=1.2, ms=7.5, label=str(etiq), zorder=6)

    lim = max_r * 1.35
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xlabel("Re(z)", color=OSCURO, fontsize=9.5, fontweight="bold")
    ax.set_ylabel("Im(z)", color=OSCURO, fontsize=9.5, fontweight="bold")
    ax.set_title(titulo, fontsize=10.5, fontweight="bold", color=OSCURO)
    ax.legend(fontsize=8.0, frameon=True, framealpha=0.92, edgecolor=CLARO, loc="upper right")
    return fig


# ==============================================================================
# ENCABEZADO Y BARRA LATERAL
# ==============================================================================
encabezado_pagina(
    "🔢 Módulo de Álgebra Superior",
    "Combinatoria y Binomio de Newton, Teoría de Números, Algoritmo de Euclides, Congruencias, Números Complejos y Anillo de Polinomios.",
)

gestionar_inventario_sidebar(
    clave_estado="mis_complejos",
    titulo="📦 Inventario de Complejos",
    etiqueta_item="Complejo:",
    claves_temporales=("temp_res_comp",),
)

# ==============================================================================
# PESTAÑAS PRINCIPALES
# ==============================================================================
tab_comb, tab_mcd, tab_euclides, tab_congruencias, tab_complejos, tab_polinomios = st.tabs([
    "🎲 1. Combinatoria y Binomio",
    "🔍 2. MCD, mcm y Primos",
    "➗ 3. Algoritmo de Euclides",
    "🕰️ 4. Congruencias Lineales",
    "🧭 5. Números Complejos",
    "📈 6. Polinomios y Raíces",
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: Combinatoria y Teorema del Binomio de Newton
# ------------------------------------------------------------------------------
with tab_comb:
    c_cb1, c_cb2 = st.columns(2, gap="large")
    with c_cb1:
        with st.container(border=True):
            header_tarjeta("Calculadora de Análisis Combinatorio")
            n_comb = int(st.number_input("Total de elementos disponibles (n):", min_value=0, max_value=500, value=6, step=1, key="cb_n"))
            k_comb = int(st.number_input("Elementos a elegir / ordenar (k):", min_value=0, max_value=500, value=3, step=1, key="cb_k"))

            perm_n = math.factorial(n_comb) if n_comb <= 170 else None
            ord_nk = math.perm(n_comb, k_comb) if k_comb <= n_comb else 0
            comb_nk = math.comb(n_comb, k_comb) if k_comb <= n_comb else 0
            ord_rep = n_comb ** k_comb
            comb_rep = math.comb(n_comb + k_comb - 1, k_comb) if (n_comb > 0 or k_comb == 0) else 0

            st.markdown(
                f"| Modelo de Conteo | Fórmula | ¿Importa el orden? | ¿Con repetición? | Resultado |\n"
                f"|---|---|---|---|---|\n"
                f"| **Permutaciones ($P_n$)** | $n!$ | Sí | No | `{f'{perm_n:,}' if perm_n is not None else 'Muy grande'}` |\n"
                f"| **Ordenaciones ($O_n^k$)** | $\\frac{{n!}}{{(n-k)!}}$ | Sí | No | `{ord_nk:,}` |\n"
                f"| **Ordenaciones con rep.** | $n^k$ | Sí | Sí | `{ord_rep:,}` |\n"
                f"| **Combinaciones ($\\binom{{n}}{{k}}$)** | $\\frac{{n!}}{{k!(n-k)!}}$ | No | No | `{comb_nk:,}` |\n"
                f"| **Combinaciones con rep.** | $\\binom{{n+k-1}}{{k}}$ | No | Sí | `{comb_rep:,}` |"
            )

    with c_cb2:
        with st.container(border=True):
            header_tarjeta("Teorema del Binomio de Newton (a·x + b·y)ⁿ")
            b1, b2, b3 = st.columns(3)
            coef_a = b1.text_input("Coeficiente a:", value="2", key="bin_a")
            coef_b = b2.text_input("Coeficiente b:", value="-1", key="bin_b")
            exp_n = int(b3.number_input("Exponente entero n:", min_value=0, max_value=12, value=4, step=1, key="bin_n"))

            k_term = int(st.slider("Consultar término k-ésimo (k de 0 a n):", min_value=0, max_value=max(0, exp_n), value=min(2, exp_n), key="bin_k"))

            a_s, b_s = _leer_seguro(coef_a), _leer_seguro(coef_b)
            if a_s is not None and b_s is not None:
                x_s, y_s = sp.Symbol("x"), sp.Symbol("y")
                binom_expr = (a_s * x_s + b_s * y_s) ** exp_n
                desarrollo = sp.expand(binom_expr)
                termino_k = sp.simplify(sp.binomial(exp_n, k_term) * (a_s * x_s) ** (exp_n - k_term) * (b_s * y_s) ** k_term)

                st.markdown("**Desarrollo algebraico completo:**")
                st.latex(sp.latex(binom_expr) + " = " + sp.latex(desarrollo))
                st.markdown(f"**Término $T_{{{k_term + 1}}}$ (para $k = {k_term}$):**")
                st.latex(
                    "T_{" + str(k_term + 1) + r"} = \binom{" + str(exp_n) + "}{" + str(k_term) + "} ("
                    + sp.latex(a_s * x_s) + ")^{" + str(exp_n - k_term) + "} (" + sp.latex(b_s * y_s) + ")^{" + str(k_term) + "} = "
                    + sp.latex(termino_k)
                )

# ------------------------------------------------------------------------------
# PESTAÑA 2: MCD, mcm y Descomposición Prima
# ------------------------------------------------------------------------------
with tab_mcd:
    with st.container(border=True):
        header_tarjeta("Máximo Común Divisor, Mínimo Común Múltiplo y Teorema Fundamental de la Aritmética")
        entrada_nums = st.text_input(
            "Ingrese números enteros distintos de cero separados por comas (Ej: 12, 18, 24):",
            value="12, 18, 24",
        )

        if st.button("🧮 Calcular MCD, mcm y Factorización Prima", use_container_width=True):
            try:
                partes = [p.strip() for p in entrada_nums.split(",") if p.strip()]
                lista_numeros = [abs(int(x)) for x in partes if int(x) != 0]

                if len(lista_numeros) < 2:
                    st.error("Ingrese al menos 2 números enteros distintos de cero.")
                else:
                    resultado_mcd = math.gcd(*lista_numeros)
                    resultado_mcm = math.lcm(*lista_numeros)
                    unicos_ordenados = sorted(list(set(lista_numeros)))

                    nota_coprimos = " — ¡Son coprimos (primos relativos) entre sí!" if resultado_mcd == 1 else ""
                    st.success("**Números analizados:** `" + ", ".join(str(x) for x in lista_numeros) + "`" + nota_coprimos)

                    col1, col2 = st.columns(2, gap="large")
                    with col1:
                        st.metric("Máximo Común Divisor (MCD)", f"{resultado_mcd:,}")
                    with col2:
                        st.metric("Mínimo Común Múltiplo (mcm)", f"{resultado_mcm:,}")

                    st.divider()
                    c_f1, c_f2 = st.columns(2, gap="large")
                    with c_f1:
                        subheader_tarjeta("Descomposición canónica en primos")
                        for n_val in unicos_ordenados:
                            divs_n = sp.divisors(n_val)
                            st.latex(
                                str(n_val) + " = " + _formatear_factores(n_val)
                                + r" \quad \text{(" + str(len(divs_n)) + r" divisores, } \varphi(" + str(n_val) + ")=" + str(int(sp.totient(n_val))) + ")"
                            )
                    with c_f2:
                        subheader_tarjeta("Factorización de MCD y mcm")
                        st.latex(r"\operatorname{MCD} = " + _formatear_factores(resultado_mcd))
                        st.latex(r"\operatorname{mcm} = " + _formatear_factores(resultado_mcm))
            except ValueError:
                st.error("Error: Asegúrese de ingresar únicamente números enteros separados por comas.")

# ------------------------------------------------------------------------------
# PESTAÑA 3: Algoritmo de Euclides Extendido
# ------------------------------------------------------------------------------
with tab_euclides:
    with st.container(border=True):
        header_tarjeta("Algoritmo de Euclides Extendido e Identidad de Bézout")
        st.markdown("Calcula el **MCD(a, b)**, las divisiones sucesivas (**D = d·q + r**) y los coeficientes enteros $(x, y)$ tales que **a·x + b·y = MCD(a, b)**.")

        col1, col2 = st.columns(2, gap="large")
        with col1:
            a_euc = int(st.number_input("Valor entero de 'a':", min_value=0, value=252, step=1))
        with col2:
            b_euc = int(st.number_input("Valor entero de 'b':", min_value=0, value=198, step=1))

        if st.button("🚀 Ejecutar Algoritmo Paso a Paso", use_container_width=True):
            if a_euc == 0 and b_euc == 0:
                st.error("Ambos números no pueden ser cero simultáneamente.")
            else:
                x_bez, y_bez, mcd = sp.gcdex(a_euc, b_euc)
                x_bez, y_bez, mcd = int(x_bez), int(y_bez), int(mcd)

                c_r1, c_r2 = st.columns(2, gap="large")
                with c_r1:
                    subheader_tarjeta("Resultado del MCD")
                    st.latex(r"\operatorname{MCD}(" + str(a_euc) + ", " + str(b_euc) + ") = " + str(mcd))
                with c_r2:
                    subheader_tarjeta("Identidad de Bézout")
                    signo_y = "+" if y_bez >= 0 else "-"
                    st.latex("(" + str(a_euc) + ")(" + str(x_bez) + ") " + signo_y + " (" + str(b_euc) + ")(" + str(abs(y_bez)) + ") = " + str(mcd))

                if a_euc > 0 and b_euc > 0:
                    pasos_euclides = []
                    r_prev, r_curr = a_euc, b_euc
                    s_prev, s_curr = 1, 0
                    t_prev, t_curr = 0, 1
                    paso_idx = 1
                    while r_curr != 0:
                        q = r_prev // r_curr
                        r_next = r_prev % r_curr
                        s_next = s_prev - q * s_curr
                        t_next = t_prev - q * t_curr
                        pasos_euclides.append({
                            "Paso": paso_idx,
                            "División Euclídea (D = d·q + r)": f"{r_prev} = {r_curr} · ({q}) + {r_next}",
                            "Cociente (q)": q,
                            "Residuo (r)": r_next,
                            "Coeficiente xᵢ": s_curr,
                            "Coeficiente yᵢ": t_curr,
                        })
                        r_prev, r_curr = r_curr, r_next
                        s_prev, s_curr = s_curr, s_next
                        t_prev, t_curr = t_curr, t_next
                        paso_idx += 1

                    st.divider()
                    subheader_tarjeta("Tabla de Divisiones Sucesivas")
                    st.dataframe(pd.DataFrame(pasos_euclides), use_container_width=True, hide_index=True)

# ------------------------------------------------------------------------------
# PESTAÑA 4: Congruencias Lineales y Teorema Chino del Resto
# ------------------------------------------------------------------------------
with tab_congruencias:
    with st.container(border=True):
        header_tarjeta("Sistemas de Congruencias Lineales y Teorema Chino del Resto")
        st.markdown("Resuelve congruencias individuales o sistemas simultáneos de la forma **cᵢ·x ≡ aᵢ (mod mᵢ)**.")

        cantidad_ec = int(st.number_input("¿Cuántas ecuaciones tiene su sistema?", min_value=1, max_value=8, value=2, step=1))

        ecuaciones_crudas = []
        with st.form("form_congruencias"):
            subheader_tarjeta("Parámetros del Sistema")
            for i in range(cantidad_ec):
                c1, c2, c3 = st.columns(3, gap="medium")
                with c1:
                    coef = int(st.number_input(f"Ecuación {i + 1} • Coeficiente (c)", value=1, step=1, key=f"c_{i}"))
                with c2:
                    res_i = int(st.number_input(f"Ecuación {i + 1} • Residuo (a)", value=i + 2, step=1, key=f"a_{i}"))
                with c3:
                    mod = int(st.number_input(f"Ecuación {i + 1} • Módulo (m ≥ 2)", min_value=2, value=2 * i + 3, step=1, key=f"m_{i}"))
                ecuaciones_crudas.append((coef, res_i, mod))

            submit_cong = st.form_submit_button("🧮 Resolver Sistema de Congruencias", use_container_width=True)

        if submit_cong:
            residuos = []
            modulos = []
            sistema_valido = True

            subheader_tarjeta("Reducción de cada ecuación")
            for idx, (coef, res_i, mod) in enumerate(ecuaciones_crudas):
                d = math.gcd(coef, mod)
                if res_i % d != 0:
                    st.error(
                        f"⛔ La ecuación {idx + 1} **no tiene solución** "
                        f"porque MCD({coef}, {mod}) = {d} no divide a {res_i}."
                    )
                    sistema_valido = False
                else:
                    c_simp, a_simp, m_simp = coef // d, res_i // d, mod // d
                    inverso = pow(c_simp, -1, m_simp) if m_simp > 1 else 0
                    a_final = (a_simp * inverso) % m_simp if m_simp > 1 else 0
                    residuos.append(a_final)
                    modulos.append(m_simp)
                    st.latex(
                        r"\text{Ec. " + str(idx + 1) + r": } " + str(coef) + r"x \equiv " + str(res_i)
                        + r" \pmod{" + str(mod) + r"} \implies x \equiv " + str(a_final)
                        + r" \pmod{" + str(m_simp) + r"}"
                    )

            if sistema_valido:
                st.divider()
                if cantidad_ec == 1:
                    st.success("Solución general de la congruencia:")
                    st.latex("x \\equiv " + str(residuos[0]) + " \\pmod{" + str(modulos[0]) + "}")
                else:
                    resultado = crt(modulos, residuos)
                    if resultado is None:
                        st.error("⛔ El sistema es **INCOMPATIBLE** (las condiciones modulares se contradicen entre sí).")
                    else:
                        solucion_x, modulo_M = int(resultado[0]), int(resultado[1])
                        st.success("¡Solución general encontrada (Teorema Chino del Resto)!")
                        st.latex("x \\equiv " + str(solucion_x) + " \\pmod{" + str(modulo_M) + "}")
                        st.info(f"**Mínima solución entera no negativa:** x = {solucion_x} | **Familia de soluciones:** x = {solucion_x} + {modulo_M}k  (k ∈ ℤ)")

# ------------------------------------------------------------------------------
# PESTAÑA 5: Números Complejos y Plano de Argand
# ------------------------------------------------------------------------------
with tab_complejos:
    col_def, col_op = st.columns([1, 1.35], gap="large")

    with col_def:
        with st.container(border=True):
            header_tarjeta("1. Definir Número Complejo")
            st.caption("Puede escribir expresiones como `3 + 4*i`, `2*exp(pi*i/4)` o `1 - sqrt(3)*i`.")
            with st.form("form_complejo"):
                nombre_c = st.text_input("Nombre (Ej: Z1, W):", value="Z1").upper().strip()
                expr_c = st.text_input("Expresión:", value="3 + 4*i")

                if st.form_submit_button("💾 Guardar Complejo", use_container_width=True):
                    if not nombre_c:
                        st.error("El nombre no puede estar vacío.")
                    else:
                        obj = _leer_seguro(expr_c)
                        if obj is not None:
                            st.session_state.mis_complejos[nombre_c] = sp.simplify(obj)
                            st.success(f"Complejo '{nombre_c}' guardado en memoria.")
                            st.rerun()

    with col_op:
        with st.container(border=True):
            header_tarjeta("2. Operaciones, Forma Polar y Teorema de De Moivre")
            if not st.session_state.mis_complejos:
                st.info("👈 Guarde al menos un número complejo a la izquierda para comenzar.")
            else:
                modo_comp = st.radio(
                    "Tipo de operación:",
                    ["Análisis y Raíces de un Complejo (Z)", "Aritmética entre dos Complejos (Z₁ y Z₂)"],
                    horizontal=True,
                )

                if modo_comp.startswith("Análisis"):
                    c_sel, c_op = st.columns(2)
                    with c_sel:
                        z_nom = st.selectbox("Seleccione Z:", list(st.session_state.mis_complejos.keys()))
                    with c_op:
                        op_unaria = st.selectbox(
                            "Operación:",
                            [
                                "Propiedades Completas (Polar, Trigonométrica, Conjugado)",
                                "Inverso Multiplicativo (1/Z)",
                                "Potencia Entera (Z^n — De Moivre)",
                                "Raíces n-ésimas (ⁿ√Z — De Moivre)",
                            ],
                        )

                    n_val = 2
                    if "Potencia" in op_unaria:
                        n_val = int(st.number_input("Exponente entero n:", min_value=-20, max_value=20, value=3, step=1))
                    elif "Raíces" in op_unaria:
                        n_val = int(st.number_input("Índice de la raíz n (≥ 2):", min_value=2, max_value=12, value=3, step=1))

                    if st.button("🧮 Ejecutar Cálculo", use_container_width=True):
                        z = st.session_state.mis_complejos[z_nom]
                        re_z, im_z = sp.re(z), sp.im(z)
                        mod_z = sp.simplify(sp.Abs(z))
                        arg_z = sp.simplify(sp.arg(z))

                        if "Propiedades" in op_unaria:
                            conj_z = sp.conjugate(z)
                            st.latex(
                                r"\text{Forma Binómica: } " + str(z_nom) + " = " + sp.latex(re_z)
                                + " + (" + sp.latex(im_z) + r")i, \quad \overline{" + str(z_nom) + "} = " + sp.latex(conj_z)
                            )
                            st.latex(
                                r"\text{Módulo } \lvert " + str(z_nom) + r"\rvert = " + sp.latex(mod_z)
                                + r", \quad \arg(" + str(z_nom) + ") = " + sp.latex(arg_z) + r" \text{ rad}"
                            )
                            st.latex(
                                r"\text{Forma Polar / Euler: } " + sp.latex(mod_z) + r"\,e^{i(" + sp.latex(arg_z) + r")} = "
                                + sp.latex(mod_z) + r"\left(\cos(" + sp.latex(arg_z) + r") + i\sin(" + sp.latex(arg_z) + r")\right)"
                            )
                            mostrar_figura_segura(_fig_argand([(z_nom, z, AZUL), ("Conj(" + str(z_nom) + ")", conj_z, NARANJA)]))

                        elif "Inverso" in op_unaria:
                            if sp.simplify(z) == 0:
                                st.error("⛔ El número complejo 0 + 0i no tiene inverso multiplicativo.")
                            else:
                                inv_z = sp.expand_complex(1 / z)
                                st.session_state.temp_res_comp = inv_z
                                st.latex(str(z_nom) + "^{-1} = " + sp.latex(inv_z))
                                mostrar_figura_segura(_fig_argand([(z_nom, z, AZUL), (str(z_nom) + "⁻¹", inv_z, VERDE)]))

                        elif "Potencia" in op_unaria:
                            if sp.simplify(z) == 0 and n_val <= 0:
                                st.error("⛔ El complejo 0 no puede elevarse a una potencia nula o negativa.")
                            else:
                                pot_z = sp.expand_complex(z ** n_val)
                                st.session_state.temp_res_comp = pot_z
                                st.latex(str(z_nom) + "^{" + str(n_val) + "} = " + sp.latex(pot_z))
                                mostrar_figura_segura(_fig_argand([(z_nom, z, AZUL), (str(z_nom) + "^" + str(n_val), pot_z, VERDE)]))

                        elif "Raíces" in op_unaria:
                            if sp.simplify(z) == 0:
                                st.info("La única raíz de 0 es 0.")
                            else:
                                r_float = float(sp.N(mod_z)) ** (1.0 / n_val)
                                theta_float = float(sp.N(arg_z))
                                st.markdown(f"**Las {n_val} raíces {n_val}-ésimas de {z_nom} (sobre la circunferencia de radio R = {r_float:.4f}):**")
                                pts_raices = []
                                cols_c = [AZUL, NARANJA, VERDE, ROJO]
                                for k in range(n_val):
                                    ang_k = (theta_float + 2 * math.pi * k) / n_val
                                    wk = complex(r_float * math.cos(ang_k), r_float * math.sin(ang_k))
                                    signo_im = "+" if wk.imag >= 0 else "-"
                                    st.latex(
                                        "w_{" + str(k) + r"} \approx " + f"{wk.real:.4f} " + signo_im + f" {abs(wk.imag):.4f}i"
                                        + r" \quad (\theta_{" + str(k) + "} = " + f"{math.degrees(ang_k):.2f}" + r"^\circ)"
                                    )
                                    pts_raices.append(("w_" + str(k), wk, cols_c[k % len(cols_c)]))
                                mostrar_figura_segura(
                                    _fig_argand(pts_raices, titulo=f"Polígono Regular de las {n_val} Raíces", dibujar_circulo_r=r_float)
                                )

                else:
                    c1, c2, c3 = st.columns(3)
                    z1_n = c1.selectbox("Complejo Z₁:", list(st.session_state.mis_complejos.keys()), key="c_z1")
                    op_b = c2.selectbox("Operación:", ["+", "-", "*", "/"], key="c_opb")
                    z2_n = c3.selectbox("Complejo Z₂:", list(st.session_state.mis_complejos.keys()), key="c_z2")

                    if st.button("🧮 Calcular Operación Binaria", use_container_width=True):
                        z1 = st.session_state.mis_complejos[z1_n]
                        z2 = st.session_state.mis_complejos[z2_n]
                        if op_b == "/" and sp.simplify(z2) == 0:
                            st.error("⛔ Error: División entre el número complejo cero.")
                        else:
                            res_b = {"+": z1 + z2, "-": z1 - z2, "*": z1 * z2, "/": z1 / z2}[op_b]
                            res_b = sp.expand_complex(res_b)
                            st.session_state.temp_res_comp = res_b
                            st.latex(str(z1_n) + " " + str(op_b) + " " + str(z2_n) + " = " + sp.latex(res_b))
                            mostrar_figura_segura(_fig_argand([(z1_n, z1, AZUL), (z2_n, z2, NARANJA), ("Resultado", res_b, VERDE)]))

                if "temp_res_comp" in st.session_state:
                    st.divider()
                    cs1, cs2 = st.columns([2, 1])
                    with cs1:
                        nom_save_c = st.text_input("Guardar complejo resultante como:", value="W1", key="save_comp_nom").upper().strip()
                    with cs2:
                        st.write("")
                        if st.button("💾 Guardar en Inventario", key="btn_save_comp_res", use_container_width=True):
                            if nom_save_c:
                                st.session_state.mis_complejos[nom_save_c] = st.session_state.temp_res_comp
                                st.session_state.pop("temp_res_comp", None)
                                st.rerun()

# ------------------------------------------------------------------------------
# PESTAÑA 6: Polinomios, Ruffini, Descartes y Cardano-Vieta
# ------------------------------------------------------------------------------
with tab_polinomios:
    with st.container(border=True):
        header_tarjeta("Anillo de Polinomios ℝ[x]: Factorización, Ruffini, Descartes y Cardano-Vieta")
        x_sym = sp.Symbol("x")

        usar_kb_poly = False
        if _TIENE_TECLADO:
            usar_kb_poly = st.toggle("⌨️ Escribir polinomio con Teclado Matemático", value=False, key="poly_kb_tog")

        c_pol, c_div = st.columns([2, 1], gap="large")
        with c_pol:
            if usar_kb_poly:
                lat_p = teclado_matematico("kb_poly_alg", valor_inicial=r"x^{3}-6x^{2}+11x-6", acoplado=True)
            else:
                str_p = st.text_input("Polinomio P(x) en variable x:", value="x^3 - 6*x^2 + 11*x - 6")
        with c_div:
            c_ruffini = st.number_input("Evaluar / Dividir entre (x − c) con c =", value=2.0, step=1.0)

        if st.button("🧮 Analizar Polinomio Completo", use_container_width=True):
            try:
                if usar_kb_poly:
                    expr_p = latex_a_sympy(lat_p, reales=False) if lat_p else None
                else:
                    expr_p = _leer_seguro(str_p)

                if expr_p is not None:
                    expr_p = expr_p.subs({s: x_sym for s in expr_p.free_symbols if s.name == "x"})
                    P = sp.Poly(sp.expand(expr_p), x_sym)
                    grado = P.degree()
                    coefs = P.all_coeffs()

                    t_p_fac, t_p_ruf, t_p_desc = st.tabs([
                        "🧩 1. Factorización y Raíces",
                        "➗ 2. División Sintética (Ruffini)",
                        "🔍 3. Descartes y Cardano-Vieta",
                    ])

                    with t_p_fac:
                        c1, c2 = st.columns(2, gap="large")
                        with c1:
                            subheader_tarjeta("Forma Expandida y Factorizada")
                            st.latex("P(x) = " + sp.latex(P.as_expr()) + r" \quad (\text{Grado }" + str(grado) + ")")
                            st.latex("P(x) = " + sp.latex(sp.factor(P.as_expr())))
                        with c2:
                            subheader_tarjeta("Raíces del Polinomio (P(x) = 0)")
                            raices_mult = calcular_con_limite(sp.roots, args=(P,), timeout=6)
                            if raices_mult:
                                for r_val, mult in raices_mult.items():
                                    st.latex("x = " + sp.latex(r_val) + r" \quad (\text{multiplicidad }" + str(mult) + ")")
                            else:
                                raices_num = P.nroots()
                                for rn in raices_num:
                                    st.latex(r"x \approx " + sp.latex(sp.N(rn, 5)))

                    with t_p_ruf:
                        c_val = sp.nsimplify(c_ruffini)
                        b_horner = [coefs[0]]
                        for a_k in coefs[1:]:
                            b_horner.append(sp.simplify(a_k + c_val * b_horner[-1]))

                        resto = b_horner[-1]
                        cociente_expr = sum(b_horner[i] * x_sym ** (grado - 1 - i) for i in range(grado))

                        subheader_tarjeta(f"División Sintética (Regla de Ruffini) para c = {c_ruffini:g}")
                        st.latex(
                            r"P(x) = \left(x - (" + sp.latex(c_val) + r")\right)\left("
                            + sp.latex(cociente_expr) + r"\right) + (" + sp.latex(resto) + ")"
                        )
                        if resto == 0:
                            st.success(f"✅ Como el residuo P({c_ruffini:g}) = 0, x = {c_ruffini:g} **es raíz exacta** de P(x) (Teorema del Factor).")
                        else:
                            st.info(f"Por el Teorema del Residuo, el valor numérico P({c_ruffini:g}) es exactamente {resto}.")

                    with t_p_desc:
                        if grado >= 1 and all(c.is_real for c in coefs):
                            # Variaciones de signo para Descartes
                            def _cambios_signo(pol_expr):
                                p_poly = sp.Poly(sp.expand(pol_expr), x_sym)
                                cs_no_cero = [float(sp.N(c)) for c in p_poly.all_coeffs() if c != 0]
                                return sum(1 for u, w in zip(cs_no_cero[:-1], cs_no_cero[1:]) if u * w < 0)

                            cambios_pos = _cambios_signo(P.as_expr())
                            cambios_neg = _cambios_signo(P.as_expr().subs(x_sym, -x_sym))
                            pos_posibles = [cambios_pos - 2 * k for k in range(cambios_pos // 2 + 1)]
                            neg_posibles = [cambios_neg - 2 * k for k in range(cambios_neg // 2 + 1)]

                            suma_raices = sp.simplify(-coefs[1] / coefs[0])
                            prod_raices = sp.simplify(((-1) ** grado) * coefs[-1] / coefs[0])

                            st.markdown(
                                f"| Teorema / Propiedad | Resultado |\n|---|---|\n"
                                f"| **Regla de Descartes (Raíces Reales Positivas)** | {cambios_pos} cambio(s) de signo → puede tener `{pos_posibles}` raíz/raíces positivas |\n"
                                f"| **Regla de Descartes (Raíces Reales Negativas)** | {cambios_neg} cambio(s) en $P(-x)$ → puede tener `{neg_posibles}` raíz/raíces negativas |\n"
                                f"| **Cardano-Vieta: Suma de las {grado} raíces ($\\sum r_i$)** | `{-coefs[1] / coefs[0]}` ($-a_{{n-1}}/a_n$) |\n"
                                f"| **Cardano-Vieta: Producto de las {grado} raíces ($\\prod r_i$)** | `{prod_raices}` ($(-1)^n a_0 / a_n$) |"
                            )
                        else:
                            st.info("La Regla de Descartes y Cardano-Vieta requieren un polinomio de grado ≥ 1 con coeficientes reales.")
            except Exception as e:
                st.error("Error: Asegúrese de ingresar un polinomio válido únicamente en la variable x. (" + str(e) + ")")
