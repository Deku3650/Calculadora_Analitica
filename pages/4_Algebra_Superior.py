# pages/4_Algebra_Superior.py
import math
import numpy as np
import pandas as pd
import streamlit as st
import sympy as sp
from matplotlib.figure import Figure
from sympy.ntheory.modular import crt

# 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO)
st.set_page_config(page_title="Álgebra Superior - MATHESIS", page_icon="🔢", layout="wide")

from estilos import cargar_estilos_globales  # noqa: E402
from utils import inicializar_estado, leer_expresion_st  # noqa: E402

try:
    from teclado_matematico import teclado_matematico
    from interprete_latex import latex_a_sympy, ErrorLatex
    _TIENE_TECLADO = True
except Exception:
    _TIENE_TECLADO = False

cargar_estilos_globales()
inicializar_estado()

AZUL = "#0284c7"
NARANJA = "#ea580c"
VERDE = "#16a34a"
ROJO = "#dc2626"
GRIS = "#6b7280"


def header_tarjeta(texto: str):
    st.markdown(f'<div class="card-header-title">{texto}</div>', unsafe_allow_html=True)


def subheader_tarjeta(texto: str):
    st.markdown(f'<div class="card-subheader-title">{texto}</div>', unsafe_allow_html=True)


def _formatear_factores(n: int) -> str:
    if n == 1:
        return "1"
    factores = sp.factorint(n)
    return " \\cdot ".join([f"{p}^{{{e}}}" if e > 1 else f"{p}" for p, e in factores.items()])


def _fig_argand(complejos_lista, titulo="Plano Complejo de Argand"):
    """Grafica una lista de tuplas (etiqueta, valor_sympy, color) con el estilo limpio de Mathesis."""
    fig = Figure(figsize=(5.6, 4.4), dpi=110, layout="constrained")
    fig.patch.set_alpha(0.0)
    ax = fig.add_subplot(111)
    ax.patch.set_alpha(0.0)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25, linestyle="--")
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRIS)
        ax.spines[lado].set_alpha(0.6)
    ax.axhline(0, color=GRIS, lw=0.8, alpha=0.6)
    ax.axvline(0, color=GRIS, lw=0.8, alpha=0.6)
    ax.tick_params(colors=GRIS, labelsize=8.5)

    max_r = 1.0
    for etiq, z_val, col in complejos_lista:
        zc = complex(sp.N(z_val))
        re_v, im_v = zc.real, zc.imag
        max_r = max(max_r, abs(re_v), abs(im_v))
        ax.annotate(
            "",
            xy=(re_v, im_v),
            xytext=(0, 0),
            arrowprops=dict(arrowstyle="->", color=col, lw=2.0),
        )
        ax.plot([re_v], [im_v], "o", color=col, ms=6, label=etiq)

    lim = max_r * 1.35
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xlabel("Re(z)", color=GRIS, fontsize=9)
    ax.set_ylabel("Im(z)", color=GRIS, fontsize=9)
    ax.set_title(titulo, fontsize=10.5, fontweight="bold", color=AZUL)
    ax.legend(fontsize=8, frameon=False, loc="upper right")
    return fig


# ==============================================================================
# ENCABEZADO PRINCIPAL
# ==============================================================================
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">🔢 Módulo de Álgebra Superior</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("Teoría de Números, Algoritmo de Euclides, Aritmética Modular, Variable Compleja y Polinomios.")

# ==============================================================================
# BARRA LATERAL (INVENTARIO DE COMPLEJOS)
# ==============================================================================
with st.sidebar:
    subheader_tarjeta("📦 Inventario de Complejos")
    if st.session_state.mis_complejos:
        for nom, val in st.session_state.mis_complejos.items():
            with st.expander(f"Complejo: {nom}"):
                st.latex(f"{nom} = {sp.latex(val)}")
    else:
        st.info("No hay números complejos en memoria.")

    st.divider()
    if st.button("🗑️ Borrar todos los complejos", use_container_width=True):
        st.session_state.mis_complejos.clear()
        st.session_state.pop("temp_res_comp", None)
        st.rerun()

# ==============================================================================
# PESTAÑAS PRINCIPALES
# ==============================================================================
tab_mcd, tab_euclides, tab_congruencias, tab_complejos, tab_polinomios = st.tabs([
    "1. MCD, mcm y Primos",
    "2. Algoritmo de Euclides",
    "3. Congruencias Lineales",
    "4. Números Complejos",
    "5. Polinomios y Raíces",
])

# ==============================================================================
# PESTAÑA 1: MCD, mcm y Descomposición
# ==============================================================================
with tab_mcd:
    with st.container(border=True):
        header_tarjeta("Máximo Común Divisor y Mínimo Común Múltiplo")

        entrada_nums = st.text_input(
            "Ingrese números enteros positivos separados por comas (Ej: 12, 18, 24):",
            value="12, 18, 24",
        )

        if st.button("🧮 Calcular MCD, mcm y Factorización Prima", use_container_width=True):
            try:
                partes = [p.strip() for p in entrada_nums.split(",") if p.strip()]
                lista_numeros = [abs(int(x)) for x in partes if int(x) != 0]
                conjunto_limpio = sorted(list(set(lista_numeros)))

                if len(conjunto_limpio) < 2:
                    st.error("Ingrese al menos 2 números enteros distintos de cero.")
                else:
                    resultado_mcd = math.gcd(*conjunto_limpio)
                    resultado_mcm = math.lcm(*conjunto_limpio)

                    st.success(f"**Conjunto analizado:** {conjunto_limpio}" + (" (Son coprimos entre sí)" if resultado_mcd == 1 else ""))

                    col1, col2 = st.columns(2, gap="large")
                    with col1:
                        st.metric("Máximo Común Divisor (MCD)", f"{resultado_mcd:,}")
                    with col2:
                        st.metric("Mínimo Común Múltiplo (mcm)", f"{resultado_mcm:,}")

                    st.divider()
                    c_f1, c_f2 = st.columns(2, gap="large")
                    with c_f1:
                        subheader_tarjeta("Descomposición de cada número")
                        for n in conjunto_limpio:
                            st.latex(f"{n} = {_formatear_factores(n)}")
                    with c_f2:
                        subheader_tarjeta("Factorización de MCD y mcm")
                        st.latex(f"\\operatorname{{MCD}} = {_formatear_factores(resultado_mcd)}")
                        st.latex(f"\\operatorname{{mcm}} = {_formatear_factores(resultado_mcm)}")
            except ValueError:
                st.error("Error: Asegúrese de ingresar únicamente números enteros separados por comas.")

# ==============================================================================
# PESTAÑA 2: Algoritmo de Euclides Extendido (con tabla paso a paso)
# ==============================================================================
with tab_euclides:
    with st.container(border=True):
        header_tarjeta("Algoritmo de Euclides e Identidad de Bézout")
        st.markdown(r"Calcula el $\operatorname{MCD}(a, b)$, la tabla de divisiones sucesivas ($a = bq + r$) y los coeficientes de Bézout tales que $ax + by = \operatorname{MCD}(a,b)$.")

        col1, col2 = st.columns(2, gap="large")
        with col1:
            a = int(st.number_input("Valor entero de 'a':", min_value=0, value=252, step=1))
        with col2:
            b = int(st.number_input("Valor entero de 'b':", min_value=0, value=198, step=1))

        if st.button("🚀 Ejecutar Algoritmo Paso a Paso", use_container_width=True):
            if a == 0 and b == 0:
                st.error("Ambos números no pueden ser cero simultáneamente.")
            else:
                x_bez, y_bez, mcd = sp.gcdex(a, b)
                x_bez, y_bez, mcd = int(x_bez), int(y_bez), int(mcd)

                c_r1, c_r2 = st.columns(2, gap="large")
                with c_r1:
                    subheader_tarjeta("Resultado del MCD")
                    st.latex(f"\\operatorname{{MCD}}({a}, {b}) = {mcd}")
                with c_r2:
                    subheader_tarjeta("Identidad de Bézout")
                    signo_y = "+" if y_bez >= 0 else "-"
                    st.latex(f"({a})({x_bez}) {signo_y} ({b})({abs(y_bez)}) = {mcd}")

                # Construir tabla paso a paso de divisiones euclidianas
                if a > 0 and b > 0:
                    pasos_euclides = []
                    r_prev, r_curr = a, b
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
                            "División (D = d·q + r)": f"{r_prev} = {r_curr} · ({q}) + {r_next}",
                            "Cociente (q)": q,
                            "Residuo (r)": r_next,
                            "Coef. x": s_curr,
                            "Coef. y": t_curr,
                        })
                        r_prev, r_curr = r_curr, r_next
                        s_prev, s_curr = s_curr, s_next
                        t_prev, t_curr = t_curr, t_next
                        paso_idx += 1

                    st.divider()
                    subheader_tarjeta("Tabla de Divisiones Sucesivas")
                    st.dataframe(pd.DataFrame(pasos_euclides), use_container_width=True, hide_index=True)

# ==============================================================================
# PESTAÑA 3: Congruencias Lineales y Teorema Chino del Resto
# ==============================================================================
with tab_congruencias:
    with st.container(border=True):
        header_tarjeta("Sistemas de Congruencias Lineales")
        st.markdown(r"Resuelve congruencias individuales o sistemas de la forma $c_i x \equiv a_i \pmod{m_i}$.")

        cantidad_ec = int(st.number_input("¿Cuántas ecuaciones tiene su sistema?", min_value=1, max_value=8, value=2, step=1))

        ecuaciones_crudas = []
        with st.form("form_congruencias"):
            subheader_tarjeta("Parámetros del Sistema")
            for i in range(cantidad_ec):
                c1, c2, c3 = st.columns(3, gap="medium")
                with c1:
                    coef = int(st.number_input(f"Ecuación {i+1} • Coeficiente (c_{i+1})", value=1, step=1, key=f"c_{i}"))
                with c2:
                    res_i = int(st.number_input(f"Ecuación {i+1} • Residuo (a_{i+1})", value=i + 2, step=1, key=f"a_{i}"))
                with c3:
                    mod = int(st.number_input(f"Ecuación {i+1} • Módulo (m_{i+1} ≥ 2)", min_value=2, value=2 * i + 3, step=1, key=f"m_{i}"))
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
                        f"⛔ La ecuación {idx+1} (${coef}x \\equiv {res_i} \\pmod{{{mod}}}$) **no tiene solución** "
                        f"porque $\\operatorname{{MCD}}({coef}, {mod}) = {d}$ no divide a ${res_i}$."
                    )
                    sistema_valido = False
                else:
                    c_simp, a_simp, m_simp = coef // d, res_i // d, mod // d
                    inverso = pow(c_simp, -1, m_simp)
                    a_final = (a_simp * inverso) % m_simp
                    residuos.append(a_final)
                    modulos.append(m_simp)
                    st.latex(
                        rf"\text{{Ec. {idx+1}: }} {coef}x \equiv {res_i} \pmod{{{mod}}} \implies "
                        rf"x \equiv {a_final} \pmod{{{m_simp}}}"
                    )

            if sistema_valido:
                st.divider()
                if cantidad_ec == 1:
                    st.success("Solución general de la congruencia:")
                    st.latex(f"x \\equiv {residuos[0]} \\pmod{{{modulos[0]}}} \\quad (x = {residuos[0]} + {modulos[0]}k,\\; k \\in \\mathbb{{Z}})")
                else:
                    resultado = crt(modulos, residuos)
                    if resultado is None:
                        st.error("⛔ El sistema es **INCOMPATIBLE** (las condiciones modulares se contradicen entre sí).")
                    else:
                        solucion_x, modulo_M = int(resultado[0]), int(resultado[1])
                        st.success("¡Solución general encontrada (Teorema Chino del Resto)!")
                        st.latex(f"x \\equiv {solucion_x} \\pmod{{{modulo_M}}}")
                        st.info(f"**Mínima solución entera no negativa:** $x = {solucion_x}$ | **Familia de soluciones:** $x = {solucion_x} + {modulo_M}k$")

# ==============================================================================
# PESTAÑA 4: Números Complejos y Plano de Argand
# ==============================================================================
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
                        obj = leer_expresion_st(expr_c)
                        if obj is not None:
                            st.session_state.mis_complejos[nombre_c] = sp.simplify(obj)
                            st.success(f"Complejo '{nombre_c}' guardado en memoria.")
                            st.rerun()

    with col_op:
        with st.container(border=True):
            header_tarjeta("2. Operaciones y Forma Polar / De Moivre")
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
                            st.latex(rf"\text{{Forma Binómica: }} {z_nom} = {sp.latex(re_z)} + ({sp.latex(im_z)})i, \quad \overline{{{z_nom}}} = {sp.latex(conj_z)}")
                            st.latex(rf"\text{{Módulo }} |{z_nom}| = {sp.latex(mod_z)} \approx {float(sp.N(mod_z)):.4f}, \quad \arg({z_nom}) = {sp.latex(arg_z)} \text{{ rad}} \approx {float(sp.N(arg_z * 180 / sp.pi)):.2f}^\circ")
                            st.latex(rf"\text{{Forma Polar: }} {sp.latex(mod_z)}\,e^{{i\left({sp.latex(arg_z)}\right)}} = {sp.latex(mod_z)}\left(\cos\left({sp.latex(arg_z)}\right) + i\sin\left({sp.latex(arg_z)}\right)\right)")
                            st.pyplot(_fig_argand([(z_nom, z, AZUL), (f"Conj({z_nom})", conj_z, NARANJA)]))

                        elif "Inverso" in op_unaria:
                            if z == 0:
                                st.error("El complejo 0 no tiene inverso multiplicativo.")
                            else:
                                inv_z = sp.expand_complex(1 / z)
                                st.session_state.temp_res_comp = inv_z
                                st.latex(rf"{z_nom}^{{-1}} = {sp.latex(inv_z)}")
                                st.pyplot(_fig_argand([(z_nom, z, AZUL), (f"{z_nom}⁻¹", inv_z, VERDE)]))

                        elif "Potencia" in op_unaria:
                            pot_z = sp.expand_complex(z**n_val)
                            st.session_state.temp_res_comp = pot_z
                            st.latex(rf"{z_nom}^{{{n_val}}} = {sp.latex(pot_z)}")
                            st.pyplot(_fig_argand([(z_nom, z, AZUL), (f"{z_nom}^{n_val}", pot_z, VERDE)]))

                        elif "Raíces" in op_unaria:
                            if z == 0:
                                st.info("La única raíz de 0 es 0.")
                            else:
                                r_float = float(sp.N(mod_z)) ** (1.0 / n_val)
                                theta_float = float(sp.N(arg_z))
                                st.markdown(f"**Las {n_val} raíces {n_val}-ésimas de ${z_nom}$ ($w_k$ para $k=0,\\dots,{n_val-1}$):**")
                                pts_raices = []
                                cols_c = [AZUL, NARANJA, VERDE, ROJO]
                                for k in range(n_val):
                                    ang_k = (theta_float + 2 * math.pi * k) / n_val
                                    wk = complex(r_float * math.cos(ang_k), r_float * math.sin(ang_k))
                                    signo_im = "+" if wk.imag >= 0 else "-"
                                    st.latex(rf"w_{{{k}}} \approx {wk.real:.4f} {signo_im} {abs(wk.imag):.4f}i \quad \left(\theta_{{{k}}} = {math.degrees(ang_k):.2f}^\circ\right)")
                                    pts_raices.append((f"w_{k}", wk, cols_c[k % len(cols_c)]))
                                st.pyplot(_fig_argand(pts_raices, titulo=f"Polígono Regular de las {n_val} Raíces"))

                else:
                    c1, c2, c3 = st.columns(3)
                    z1_n = c1.selectbox("Complejo Z₁:", list(st.session_state.mis_complejos.keys()), key="c_z1")
                    op_b = c2.selectbox("Operación:", ["+", "-", "*", "/"], key="c_opb")
                    z2_n = c3.selectbox("Complejo Z₂:", list(st.session_state.mis_complejos.keys()), key="c_z2")

                    if st.button("🧮 Calcular Operación Binaria", use_container_width=True):
                        z1 = st.session_state.mis_complejos[z1_n]
                        z2 = st.session_state.mis_complejos[z2_n]
                        if op_b == "/" and z2 == 0:
                            st.error("Error: División entre cero.")
                        else:
                            res_b = {"+": z1 + z2, "-": z1 - z2, "*": z1 * z2, "/": z1 / z2}[op_b]
                            res_b = sp.expand_complex(res_b)
                            st.session_state.temp_res_comp = res_b
                            st.latex(rf"{z1_n} {op_b} {z2_n} = {sp.latex(res_b)}")
                            st.pyplot(_fig_argand([(z1_n, z1, AZUL), (z2_n, z2, NARANJA), ("Resultado", res_b, VERDE)]))

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

# ==============================================================================
# PESTAÑA 5: Polinomios, Factorización y División Sintética (Ruffini)
# ==============================================================================
with tab_polinomios:
    with st.container(border=True):
        header_tarjeta("Polinomios en ℝ[x]: Factorización, Raíces y División Sintética")
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
            c_ruffini = st.number_input("Evaluar / Dividir entre (x - c) con c =", value=2.0, step=1.0)

        if st.button("🧮 Analizar Polinomio", use_container_width=True):
            try:
                if usar_kb_poly:
                    expr_p = latex_a_sympy(lat_p, reales=False) if lat_p else None
                else:
                    expr_p = leer_expresion_st(str_p)

                if expr_p is not None:
                    expr_p = expr_p.subs({s: x_sym for s in expr_p.free_symbols if s.name == "x"})
                    P = sp.Poly(sp.expand(expr_p), x_sym)
                    grado = P.degree()
                    coefs = P.all_coeffs()

                    c1, c2 = st.columns(2, gap="large")
                    with c1:
                        subheader_tarjeta("Forma Expandida y Factorizada")
                        st.latex(rf"P(x) = {sp.latex(P.as_expr())} \quad (\text{{Grado }} {grado})")
                        st.latex(rf"P(x) = {sp.latex(sp.factor(P.as_expr()))}")
                    with c2:
                        subheader_tarjeta("Raíces del Polinomio (P(x) = 0)")
                        raices_mult = sp.roots(P)
                        if raices_mult:
                            for r_val, mult in raices_mult.items():
                                st.latex(rf"x = {sp.latex(r_val)} \quad (\text{{multiplicidad }} {mult})")
                        else:
                            raices_num = P.nroots()
                            for rn in raices_num:
                                st.latex(rf"x \approx {sp.latex(sp.N(rn, 5))}")

                    # División sintética (Horner) para (x - c)
                    c_val = sp.nsimplify(c_ruffini)
                    b_horner = [coefs[0]]
                    for a_k in coefs[1:]:
                        b_horner.append(sp.simplify(a_k + c_val * b_horner[-1]))

                    resto = b_horner[-1]
                    cociente_expr = sum(b_horner[i] * x_sym ** (grado - 1 - i) for i in range(grado))

                    st.divider()
                    subheader_tarjeta(f"División Sintética (Regla de Ruffini) para c = {c_ruffini:g}")
                    st.latex(
                        rf"P(x) = \left(x - ({sp.latex(c_val)})\right)\left({sp.latex(cociente_expr)}\right) + ({sp.latex(resto)})"
                    )
                    if resto == 0:
                        st.success(f"✅ Como el residuo $P({c_ruffini:g}) = 0$, $x = {c_ruffini:g}$ **es raíz exacta** de $P(x)$ (Teorema del Residuo).")
                    else:
                        st.info(f"Por el Teorema del Residuo, $P({c_ruffini:g}) = {sp.latex(resto)}$.")
            except Exception as e:
                st.error(f"Error: Asegúrese de ingresar un polinomio válido únicamente en la variable x. ({e})")
