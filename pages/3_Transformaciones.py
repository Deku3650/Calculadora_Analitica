# pages/3_Transformaciones.py
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import sympy as sp
from matplotlib.patches import Polygon
from matplotlib.ticker import AutoMinorLocator

st.set_page_config(page_title="Transformaciones Lineales - MATHESIS", page_icon="🔄", layout="wide")

from estilos import cargar_estilos_globales, encabezado_pagina, header_tarjeta, subheader_tarjeta  # noqa: E402
from utils import (  # noqa: E402
    calcular_con_limite,
    crear_transformacion_ui,
    evaluar_numerico,
    gestionar_inventario_sidebar,
    imprimir_matriz_simbolica,
    inicializar_estado,
    leer_expresion_st,
    mostrar_detalle_tl,
    mostrar_figura_segura,
    parsear_base_matricial,
)

cargar_estilos_globales()
inicializar_estado()

AZUL = "#0369a1"
NARANJA = "#ea580c"
VERDE = "#15803d"
ROJO = "#dc2626"
OSCURO = "#1e293b"
CLARO = "#cbd5e1"
FONDO = "#ffffff"


def _fig_transformacion_2d(A_np):
    fig, ax = plt.subplots(figsize=(6.4, 5.2), dpi=110, facecolor=FONDO)
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
    ax.set_aspect("equal", adjustable="box")

    cuadrado = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
    transformado = (A_np @ cuadrado.T).T

    ax.add_patch(Polygon(cuadrado, closed=True, fc=AZUL, alpha=0.15, ec=AZUL, lw=1.8, ls="--", label="Cuadrado unitario original"))
    ax.add_patch(Polygon(transformado, closed=True, fc=NARANJA, alpha=0.25, ec=NARANJA, lw=2.4, label="Imagen T([0,1]²)"))

    e1_t = A_np[:, 0]
    e2_t = A_np[:, 1]
    ax.annotate("", xy=(e1_t[0], e1_t[1]), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=ROJO, lw=2.4))
    ax.annotate("", xy=(e2_t[0], e2_t[1]), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=VERDE, lw=2.4))
    ax.plot([], [], color=ROJO, lw=2.4, label=f"T(e₁) = ({e1_t[0]:.2f}, {e1_t[1]:.2f})")
    ax.plot([], [], color=VERDE, lw=2.4, label=f"T(e₂) = ({e2_t[0]:.2f}, {e2_t[1]:.2f})")

    pts_all = np.vstack([cuadrado, transformado, [[0, 0]]])
    xmin, ymin = pts_all.min(axis=0)
    xmax, ymax = pts_all.max(axis=0)
    m = max(xmax - xmin, ymax - ymin, 2.0) * 0.28
    ax.set_xlim(xmin - m, xmax + m)
    ax.set_ylim(ymin - m, ymax + m)
    ax.set_title("Acción Geométrica de T sobre el Cuadrado Unitario", fontsize=10.5, fontweight="bold", color=OSCURO)
    ax.legend(loc="upper right", fontsize=8.0, framealpha=0.92)
    return fig


# ==============================================================================
# ENCABEZADO Y BARRA LATERAL
# ==============================================================================
encabezado_pagina(
    "🔄 Módulo de Transformaciones Lineales",
    "Definición por regla u operador, núcleo, imagen, teorema del rango-nulidad, cambio de base, espacio dual, Cayley-Hamilton y acción geométrica 2D.",
)

gestionar_inventario_sidebar(
    clave_estado="mis_transformaciones",
    titulo="📦 Inventario de T.L.",
    etiqueta_item="T.L.:",
    claves_temporales=("temp_tl_mat", "temp_tl_reg", "temp_b1", "temp_b2", "temp_dom_str", "temp_cod_str"),
)

# ==============================================================================
# PESTAÑAS PRINCIPALES
# ==============================================================================
tab_crear, tab_nucleo, tab_bases, tab_geom = st.tabs([
    "🛠️ 1. Definir Transformación",
    "🔬 2. Núcleo, Imagen y Clasificación",
    "🔄 3. Cambio de Base y Espacio Dual",
    "🎨 4. Geometría 2D y Cayley-Hamilton",
])

with tab_crear:
    with st.container(border=True):
        header_tarjeta("Constructor de Transformaciones Lineales")
        crear_transformacion_ui()

with tab_nucleo:
    if not st.session_state.mis_transformaciones:
        st.info("👈 Defina primero una Transformación Lineal en la pestaña '1. Definir Transformación'.")
    else:
        with st.container(border=True):
            header_tarjeta("Análisis de Subespacios: Núcleo (Kernel) e Imagen (Recorrido)")
            tl_sel = st.selectbox("Seleccione la Transformación Lineal:", list(st.session_state.mis_transformaciones.keys()), key="tl_nuc_sel")
            tl_data = st.session_state.mis_transformaciones[tl_sel]
            mostrar_detalle_tl(tl_sel, tl_data)

            if st.button("🚀 Analizar Núcleo, Imagen e Inyectividad/Sobreyectividad", use_container_width=True):
                A = tl_data["matriz_asociada"]
                dim_v = tl_data["dim_V"]
                dim_w = tl_data["dim_W"]
                try:
                    with st.spinner("Calculando subespacios de la transformación…"):
                        base_ker = calcular_con_limite(A.nullspace, timeout=6)
                        base_im = calcular_con_limite(A.columnspace, timeout=6)
                        nulidad = len(base_ker)
                        rango = len(base_im)

                        es_inyectiva = nulidad == 0
                        es_sobreyectiva = rango == dim_w
                        es_isomorfismo = es_inyectiva and es_sobreyectiva and (dim_v == dim_w)

                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Nulidad ν(T) = dim(Ker T)", str(nulidad))
                        m2.metric("Rango ρ(T) = dim(Im T)", str(rango))
                        m3.metric("¿Inyectiva (Monomorfismo)?", "✅ Sí" if es_inyectiva else "❌ No")
                        m4.metric("¿Sobreyectiva (Epimorfismo)?", "✅ Sí" if es_sobreyectiva else "❌ No")

                        st.info(
                            f"**Teorema de las Dimensiones (Rango-Nulidad):** "
                            f"$\\dim(\\ker T) + \\dim(\\operatorname{{Im}} T) = {nulidad} + {rango} = {dim_v} = \\dim(V)$."
                        )

                        if es_isomorfismo:
                            st.success("🏆 **Isomorfismo Lineal:** La transformación es biyectiva ($V \\cong W$) y admite transformación inversa $T^{-1}$.")

                        c_k, c_i = st.columns(2)
                        with c_k:
                            subheader_tarjeta("Base del Núcleo Ker(T)")
                            if base_ker:
                                mat_ker = sp.Matrix.hstack(*base_ker)
                                imprimir_matriz_simbolica(mat_ker)
                            else:
                                st.write("Núcleo trivial: $\\ker(T) = \\{\\mathbf{0}_V\\}$.")
                        with c_i:
                            subheader_tarjeta("Base de la Imagen Im(T)")
                            if base_im:
                                mat_im = sp.Matrix.hstack(*base_im)
                                imprimir_matriz_simbolica(mat_im)
                            else:
                                st.write("Imagen trivial: $\\operatorname{Im}(T) = \\{\\mathbf{0}_W\\}$.")
                except TimeoutError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error("Error al analizar la transformación: " + str(e))

            st.divider()
            subheader_tarjeta("Evaluar Transformación T(v) en un Vector")
            vec_in_str = st.text_input(
                f"Ingrese las {tl_data['dim_V']} coordenadas del vector v separadas por comas:",
                value=", ".join(["1"] * tl_data["dim_V"]),
                key="eval_tl_vec_in",
            )
            if st.button("🧮 Evaluar T(v)", use_container_width=True):
                partes_v = [leer_expresion_st(x.strip()) for x in vec_in_str.split(",") if x.strip()]
                if len(partes_v) != tl_data["dim_V"] or None in partes_v:
                    st.error(f"Ingrese exactamente {tl_data['dim_V']} expresiones válidas.")
                else:
                    v_col = sp.Matrix(partes_v)
                    img_v = sp.simplify(tl_data["matriz_asociada"] * v_col)
                    st.latex("T" + sp.latex(v_col) + " = " + sp.latex(img_v))

with tab_bases:
    if not st.session_state.mis_transformaciones:
        st.info("👈 Defina primero una Transformación Lineal en la pestaña '1. Definir Transformación'.")
    else:
        with st.container(border=True):
            header_tarjeta("Cambio de Base y Transformación Transpuesta (Espacio Dual)")
            tl_b_sel = st.selectbox("Seleccione la Transformación Lineal:", list(st.session_state.mis_transformaciones.keys()), key="tl_bas_sel")
            tl_b = st.session_state.mis_transformaciones[tl_b_sel]
            A_asoc = tl_b["matriz_asociada"]
            dim_v = tl_b["dim_V"]
            dim_w = tl_b["dim_W"]

            st.markdown(
                "Ingrese las nuevas bases $\\beta'$ (de $V$, con " + str(dim_v) + " vectores) y "
                "$\\gamma'$ (de $W$, con " + str(dim_w) + " vectores) usando corchetes `[v1, v2], ...`:"
            )
            cb1, cb2 = st.columns(2)
            def_b_v = ", ".join(["[" + ", ".join("1" if i == j else "0" for j in range(dim_v)) + "]" for i in range(dim_v)])
            def_b_w = ", ".join(["[" + ", ".join("1" if i == j else "0" for j in range(dim_w)) + "]" for i in range(dim_w)])
            with cb1:
                str_b_dom = st.text_area("Nueva Base β′ del Dominio (V):", value=def_b_v, key="cambio_b_dom")
            with cb2:
                str_b_cod = st.text_area("Nueva Base γ′ del Codominio (W):", value=def_b_w, key="cambio_b_cod")

            if st.button("🔄 Calcular Matriz en las Nuevas Bases y Matriz Dual", use_container_width=True):
                try:
                    P_dom = parsear_base_matricial(str_b_dom, dim_v)
                    Q_cod = parsear_base_matricial(str_b_cod, dim_w)

                    with st.spinner("Calculando cambio de base y bases duales…"):
                        # Matriz en las nuevas bases: [T]_{beta'}^{gamma'} = Q^{-1} * A * P
                        Q_inv = calcular_con_limite(Q_cod.inv, timeout=6)
                        P_inv = calcular_con_limite(P_dom.inv, timeout=6)
                        M_nueva = calcular_con_limite(lambda: sp.simplify(Q_inv * A_asoc * P_dom), timeout=6)

                        # CORRECCIÓN CRÍTICA: La base dual ( matriz de transición dual ) es la TRANSPUESTA de la inversa: (P^{-1})^T y (Q^{-1})^T
                        P_dual = sp.simplify(P_inv.T)
                        Q_dual = sp.simplify(Q_inv.T)
                        M_transpuesta_dual = sp.simplify(M_nueva.T)

                        t_cb, t_du = st.tabs(["📐 1. Cambio de Base Directo", "🪞 2. Espacio Dual (V* y W*) y Operador Transpuesto T*"])

                        with t_cb:
                            st.latex(r"[T]_{\beta'}^{\gamma'} = Q^{-1} \cdot [T] \cdot P")
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                st.write("**Matriz de paso P (Dominio):**")
                                imprimir_matriz_simbolica(P_dom)
                            with c2:
                                st.write("**Inversa Q⁻¹ (Codominio):**")
                                imprimir_matriz_simbolica(Q_inv)
                            with c3:
                                st.write("**Nueva Matriz Asociada:**")
                                imprimir_matriz_simbolica(M_nueva)

                        with t_du:
                            st.info(
                                "💡 **Propiedad Dual:** Si las columnas de $Q$ forman una base de $W$, los vectores de su **base dual** $\\gamma^*$ son las columnas de $(Q^{-1})^T$. "
                                "Además, la matriz de la transformación transpuesta $T^*: W^* \\to V^*$ es $[T^*]_{\\gamma^*}^{\\beta^*} = ([T]_{\\beta'}^{\\gamma'})^T$."
                            )
                            d1, d2, d3 = st.columns(3)
                            with d1:
                                st.write("**Base Dual del Dominio (P⁻¹)ᵀ:**")
                                imprimir_matriz_simbolica(P_dual)
                            with d2:
                                st.write("**Base Dual del Codominio (Q⁻¹)ᵀ:**")
                                imprimir_matriz_simbolica(Q_dual)
                            with d3:
                                st.write("**Matriz de T* en bases duales:**")
                                imprimir_matriz_simbolica(M_transpuesta_dual)
                except ValueError as ve:
                    st.error("⛔ Error en las bases ingresadas: " + str(ve))
                except TimeoutError as te:
                    st.error(str(te))
                except Exception as e:
                    st.error("Error inesperado en el cambio de base: " + str(e))

with tab_geom:
    if not st.session_state.mis_transformaciones:
        st.info("👈 Defina primero una Transformación Lineal en la pestaña '1. Definir Transformación'.")
    else:
        with st.container(border=True):
            header_tarjeta("Acción Geométrica en ℝ² y Teorema de Cayley-Hamilton")
            tl_g_sel = st.selectbox("Seleccione la Transformación Lineal:", list(st.session_state.mis_transformaciones.keys()), key="tl_geom_sel")
            tl_g = st.session_state.mis_transformaciones[tl_g_sel]
            A_g = tl_g["matriz_asociada"]

            if tl_g["dim_V"] != tl_g["dim_W"]:
                st.warning("Esta sección requiere un endomorfismo (operador lineal T: V → V donde dim(V) = dim(W)).")
            else:
                n_endo = tl_g["dim_V"]
                t_ch, t_v2d = st.tabs(["📜 Teorema de Cayley-Hamilton", "🎨 Visualizador Geométrico 2D (ℝ² → ℝ²)"])

                with t_ch:
                    if st.button("🧮 Verificar Teorema de Cayley-Hamilton", use_container_width=True):
                        try:
                            with st.spinner("Calculando polinomio característico y evaluando p(T)…"):
                                lam = sp.Symbol("lambda")
                                char_p = calcular_con_limite(A_g.charpoly, args=(lam,), timeout=6)
                                st.markdown("**Polinomio Característico $p(\\lambda) = \\det(A - \\lambda I)$:**")
                                st.latex("p(\\lambda) = " + sp.latex(char_p.as_expr()))

                                coeffs = char_p.all_coeffs()
                                acc_mat = sp.zeros(n_endo, n_endo)
                                grado_p = len(coeffs) - 1
                                for idx_c, c_val in enumerate(coeffs):
                                    pot_m = grado_p - idx_c
                                    acc_mat += c_val * (A_g ** pot_m if pot_m > 0 else sp.eye(n_endo))
                                acc_mat = sp.simplify(acc_mat)
                                st.markdown("**Evaluación matricial $p(A)$:**")
                                imprimir_matriz_simbolica(acc_mat)
                                st.success("✅ Se verifica el **Teorema de Cayley-Hamilton**: todo operador lineal anula su propio polinomio característico ($p(T) = 0$).")
                        except Exception as e:
                            st.error("Error al verificar Cayley-Hamilton: " + str(e))

                with t_v2d:
                    if n_endo != 2:
                        st.info("El visualizador geométrico del cuadrado unitario está disponible para operadores en ℝ² (dimensión 2×2).")
                    else:
                        A_num_2d = evaluar_numerico(A_g)
                        if A_num_2d is None:
                            st.warning("La matriz contiene variables simbólicas o complejos; asígnele valores numéricos reales para graficar su efecto 2D.")
                        else:
                            det_2d = float(np.linalg.det(A_num_2d))
                            c_g_izq, c_g_der = st.columns([1, 1.35])
                            with c_g_izq:
                                st.metric("Factor de Escala de Área |det(T)|", f"{abs(det_2d):.4f}")
                                orient_txt = (
                                    "Conserva la orientación (det > 0)" if det_2d > 1e-9
                                    else "Invierte la orientación / refleja (det < 0)" if det_2d < -1e-9
                                    else "Colapsa el plano a una recta o punto (det = 0)"
                                )
                                st.info("**Efecto geométrico:** " + orient_txt)
                                imprimir_matriz_simbolica(A_g)
                            with c_g_der:
                                fig_2d = _fig_transformacion_2d(A_num_2d)
                                mostrar_figura_segura(fig_2d)
