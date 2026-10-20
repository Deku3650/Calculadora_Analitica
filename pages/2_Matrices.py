# pages/2_Matrices.py
import numpy as np
import streamlit as st
import sympy as sp

st.set_page_config(page_title="Álgebra Lineal: Matrices - MATHESIS", page_icon="🧮", layout="wide")

from estilos import cargar_estilos_globales, encabezado_pagina, header_tarjeta, subheader_tarjeta  # noqa: E402
from utils import (  # noqa: E402
    calcular_con_limite,
    evaluar_numerico,
    gestionar_inventario_sidebar,
    imprimir_matriz_simbolica,
    inicializar_estado,
    leer_expresion_st,
)

try:
    from teclado_matematico import teclado_matematico
    from interprete_latex import latex_a_sympy, leer_en_espanol, ErrorLatex
    _TIENE_TECLADO = True
except Exception:
    _TIENE_TECLADO = False

cargar_estilos_globales()
inicializar_estado()


def _leer_seguro(texto: str):
    if texto is None or not str(texto).strip():
        return None
    try:
        return leer_expresion_st(str(texto).strip())
    except Exception:
        st.error("La expresión ingresada no es válida.")
        return None


# ==============================================================================
# ENCABEZADO Y BARRA LATERAL (GESTIÓN INDIVIDUAL DE INVENTARIO)
# ==============================================================================
encabezado_pagina(
    "🧮 Álgebra Lineal: Matrices y Descomposiciones",
    "Operaciones matriciales, reducción Gauss-Jordan, subespacios, factorización LU, SVD, pseudoinversa, análisis espectral y formas cuadráticas.",
)

gestionar_inventario_sidebar(
    clave_estado="mis_matrices",
    titulo="📦 Inventario de Matrices",
    etiqueta_item="Matriz:",
    claves_temporales=("temp_matriz", "temp_prop_matriz", "temp_avanzada", "temp_espectral"),
)

# ==============================================================================
# PESTAÑAS PRINCIPALES
# ==============================================================================
tab_gestion, tab_basicas, tab_propiedades, tab_descomp, tab_espectral, tab_avanzadas = st.tabs([
    "📥 1. Gestión y Creación",
    "➕ 2. Operaciones Básicas",
    "🔎 3. Propiedades y Subespacios",
    "🧩 4. LU, SVD y Formas Cuadráticas",
    "🌈 5. Análisis Espectral",
    "📐 6. Hessiana y Jacobiana",
])

# --------------------------------------------------------------------------
# PESTAÑA 1: Constructor, Creación Manual y Puentes
# --------------------------------------------------------------------------
with tab_gestion:
    col_g1, col_g2 = st.columns(2, gap="large")

    with col_g1:
        with st.container(border=True):
            header_tarjeta("➕ Nueva Matriz Manual")
            nombre_nueva = st.text_input("Asignar nombre de la matriz (Ej: A, M1):", key="input_nom_manual").upper().strip()

            col_m, col_n = st.columns(2)
            with col_m:
                filas = int(st.number_input("Número de filas:", min_value=1, max_value=8, value=2, step=1, key="num_filas_mat"))
            with col_n:
                columnas = int(st.number_input("Número de columnas:", min_value=1, max_value=8, value=2, step=1, key="num_cols_mat"))

            st.divider()
            subheader_tarjeta("🧩 Componentes de la Matriz")

            matriz_elementos = []
            error_sintaxis = False

            for i in range(filas):
                cols = st.columns(columnas)
                fila_vals = []
                for j in range(columnas):
                    with cols[j]:
                        val_str = st.text_input(
                            f"({i + 1}, {j + 1}):",
                            value="1" if i == j else "0",
                            key=f"celda_{i}_{j}_{filas}_{columnas}",
                        ).strip()
                        val_sym = _leer_seguro(val_str)
                        if val_sym is not None:
                            fila_vals.append(val_sym)
                        else:
                            error_sintaxis = True
                matriz_elementos.append(fila_vals)

            if error_sintaxis:
                st.error("⚠️ Ingrese expresiones matemáticas o números válidos en todas las celdas.")
            else:
                matriz_temp = sp.Matrix(matriz_elementos)
                st.markdown("**Vista previa:**")
                st.latex((nombre_nueva if nombre_nueva else "M") + " = " + sp.latex(matriz_temp))

                if st.button("💾 Guardar Matriz", key="btn_guardar_mat_manual", use_container_width=True):
                    if not nombre_nueva:
                        st.error("Por favor, asigna un nombre a la matriz.")
                    else:
                        st.session_state.mis_matrices[nombre_nueva] = matriz_temp
                        st.success("¡Matriz '" + nombre_nueva + "' guardada exitosamente!")
                        st.rerun()

    with col_g2:
        with st.container(border=True):
            header_tarjeta("🔀 Constructores Rápidos y Puentes")
            t_esp, t_puente = st.tabs(["⚡ Matrices Especiales", "🔗 Importar / Exportar"])

            with t_esp:
                tipo_esp = st.selectbox(
                    "Generar matriz especial:",
                    ["Identidad (Iₙ)", "Diagonal a partir de lista", "Simétrica de Hilbert (Hₙ)", "Vandermonde"],
                    key="mat_esp_tipo",
                )
                nom_esp = st.text_input("Nombre para guardar:", value="E1", key="nom_mat_esp").upper().strip()
                if tipo_esp == "Identidad (Iₙ)":
                    n_id = int(st.number_input("Dimensión n:", 1, 8, 3, key="n_id_esp"))
                    M_gen = sp.eye(n_id)
                elif tipo_esp == "Diagonal a partir de lista":
                    diag_str = st.text_input("Elementos diagonales separados por comas:", value="2, -1, 4", key="diag_in_esp")
                    partes_d = [_leer_seguro(x) for x in diag_str.split(",") if x.strip()]
                    M_gen = sp.diag(*partes_d) if partes_d and None not in partes_d else sp.eye(2)
                elif tipo_esp.startswith("Simétrica"):
                    n_hil = int(st.number_input("Dimensión n:", 1, 6, 3, key="n_hil_esp"))
                    M_gen = sp.Matrix(n_hil, n_hil, lambda i, j: sp.Rational(1, i + j + 1))
                else:
                    van_str = st.text_input("Nodos x₁, x₂, … separados por comas:", value="1, 2, 3", key="van_in_esp")
                    nodos = [_leer_seguro(x) for x in van_str.split(",") if x.strip()]
                    M_gen = sp.Matrix(len(nodos), len(nodos), lambda i, j: nodos[i] ** j) if nodos and None not in nodos else sp.eye(2)

                imprimir_matriz_simbolica(M_gen)
                if st.button("💾 Guardar Matriz Especial", use_container_width=True):
                    if nom_esp:
                        st.session_state.mis_matrices[nom_esp] = M_gen
                        st.rerun()

            with t_puente:
                fuente_import = st.selectbox(
                    "¿De dónde desea importar?",
                    ["De una Transformación Activa", "De un Conjunto de Vectores"],
                )
                if fuente_import == "De una Transformación Activa":
                    if st.session_state.get("mis_transformaciones"):
                        tl_import = st.selectbox("Seleccione la T.L.:", list(st.session_state.mis_transformaciones.keys()), key="imp_tl_main")
                        nom_mat_tl = st.text_input("Guardar como (Ej. M_T1):", key="nom_mat_tl_main").upper().strip()
                        if st.button("⬇️ Importar Matriz Asociada", use_container_width=True):
                            if nom_mat_tl:
                                st.session_state.mis_matrices[nom_mat_tl] = st.session_state.mis_transformaciones[tl_import]["matriz_asociada"]
                                st.rerun()
                    else:
                        st.info("No hay transformaciones definidas en memoria.")
                else:
                    if st.session_state.get("mis_vectores"):
                        vecs_import = st.multiselect("Seleccione vectores columna:", list(st.session_state.mis_vectores.keys()), key="imp_vecs_main")
                        nom_mat_vec = st.text_input("Guardar como (Ej. BASE1):", key="nom_mat_vec_main").upper().strip()
                        if st.button("⬇️ Construir Matriz por Columnas", use_container_width=True):
                            if vecs_import and nom_mat_vec:
                                try:
                                    lista_vectores = [st.session_state.mis_vectores[v] for v in vecs_import]
                                    st.session_state.mis_matrices[nom_mat_vec] = sp.Matrix.hstack(*lista_vectores)
                                    st.rerun()
                                except Exception as e:
                                    st.error("Error: Los vectores deben tener la misma dimensión. " + str(e))
                    else:
                        st.info("No hay vectores definidos en memoria.")

                st.divider()
                subheader_tarjeta("📤 Exportar a Transformación Lineal")
                if st.session_state.mis_matrices:
                    mat_export = st.selectbox("Matriz a exportar:", list(st.session_state.mis_matrices.keys()), key="exp_mat_tl_main")
                    nombre_tl = st.text_input("Nombre de la nueva T.L. (Ej. T1):", key="nombre_tl_main").upper().strip()
                    if st.button("Crear Transformación", key="btn_crear_tl_main", use_container_width=True):
                        if nombre_tl:
                            A_export = st.session_state.mis_matrices[mat_export]
                            filas_e, columnas_e = A_export.shape
                            vars_input = sp.symbols("x1:" + str(columnas_e + 1))
                            regla_correspondencia = A_export * sp.Matrix(vars_input)
                            st.session_state.mis_transformaciones[nombre_tl] = {
                                "matriz_asociada": A_export,
                                "regla": regla_correspondencia,
                                "variables": vars_input,
                                "dim_V": columnas_e,
                                "dim_W": filas_e,
                                "espacio_V": r"\mathbb{R}^{" + str(columnas_e) + "}",
                                "espacio_W": r"\mathbb{R}^{" + str(filas_e) + "}",
                                "base_dominio": sp.eye(columnas_e),
                                "base_codominio": sp.eye(filas_e),
                            }
                            st.success("T.L. '" + nombre_tl + "' creada en el módulo de Transformaciones.")

# --------------------------------------------------------------------------
# PESTAÑA 2: Operaciones Básicas (con Timeout)
# --------------------------------------------------------------------------
with tab_basicas:
    if not st.session_state.mis_matrices:
        st.info("👈 Comience creando o importando una matriz en la pestaña 'Gestión y Creación'.")
    else:
        with st.container(border=True):
            header_tarjeta("➕ Operaciones Algebraicas Matriciales")
            col1, col2, col3 = st.columns([1, 1.2, 1.5], gap="medium")

            with col1:
                mat_A_nombre = st.selectbox("Matriz A", list(st.session_state.mis_matrices.keys()), key="op_matA")
            with col2:
                operacion = st.selectbox(
                    "Operación",
                    ["Suma (A + B)", "Resta (A − B)", "Producto (A · B)", "Escalar (k · A)", "Potencia (A^k)", "Conmutador [A, B] = AB − BA"],
                )
            with col3:
                if operacion.startswith("Escalar"):
                    escalar_str = st.text_input("Ingrese Escalar k (Ej: 2, x, 1/2):", value="2")
                elif operacion.startswith("Potencia"):
                    pot_k = int(st.number_input("Exponente entero k:", min_value=-10, max_value=25, value=2, step=1))
                else:
                    mat_B_nombre = st.selectbox("Matriz B", list(st.session_state.mis_matrices.keys()), key="op_matB")

            if st.button("🧮 Calcular Operación", key="btn_basicas", use_container_width=True):
                matA = st.session_state.mis_matrices[mat_A_nombre]
                res_op = None
                try:
                    with st.spinner("Ejecutando operación matricial…"):
                        if operacion.startswith("Escalar"):
                            esc = _leer_seguro(escalar_str)
                            if esc is not None:
                                res_op = calcular_con_limite(lambda: sp.simplify(esc * matA), timeout=6)
                        elif operacion.startswith("Potencia"):
                            if not matA.is_square:
                                st.error("Error: Solo las matrices cuadradas pueden elevarse a una potencia.")
                            elif pot_k < 0 and calcular_con_limite(matA.det, timeout=5) == 0:
                                st.error("Error: La matriz es singular (det = 0); no admite potencias negativas.")
                            else:
                                res_op = calcular_con_limite(lambda: sp.simplify(matA ** pot_k), timeout=6)
                        else:
                            matB = st.session_state.mis_matrices[mat_B_nombre]
                            if operacion.startswith(("Suma", "Resta")):
                                if matA.shape != matB.shape:
                                    st.error("Error: Las matrices deben tener la misma dimensión para sumar o restar.")
                                else:
                                    res_op = calcular_con_limite(
                                        lambda: sp.simplify(matA + matB if operacion.startswith("Suma") else matA - matB),
                                        timeout=6,
                                    )
                            elif operacion.startswith("Producto"):
                                if matA.shape[1] != matB.shape[0]:
                                    st.error("Error: El número de columnas de A debe coincidir con el de filas de B.")
                                else:
                                    res_op = calcular_con_limite(lambda: sp.simplify(matA * matB), timeout=6)
                            else:
                                if matA.shape != matB.shape or not matA.is_square:
                                    st.error("El conmutador [A, B] requiere dos matrices cuadradas del mismo orden.")
                                else:
                                    res_op = calcular_con_limite(lambda: sp.simplify(matA * matB - matB * matA), timeout=6)
                                    if res_op == sp.zeros(*matA.shape):
                                        st.info("✅ [A, B] = 0: Las matrices A y B **conmutan** (AB = BA).")
                except TimeoutError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error("Error al ejecutar la operación: " + str(e))

                if res_op is not None:
                    st.session_state.temp_matriz = res_op

        if "temp_matriz" in st.session_state:
            with st.container(border=True):
                subheader_tarjeta("🎯 Resultado de la Operación")
                imprimir_matriz_simbolica(st.session_state.temp_matriz)
                col_save1, col_save2 = st.columns([2, 1])
                with col_save1:
                    nombre_save = st.text_input("Guardar este resultado como (Ej. R1):", key="save_name_basicas").upper().strip()
                with col_save2:
                    st.write("")
                    if st.button("💾 Guardar Matriz", key="save_basicas", use_container_width=True):
                        if nombre_save:
                            st.session_state.mis_matrices[nombre_save] = st.session_state.temp_matriz
                            st.session_state.pop("temp_matriz", None)
                            st.rerun()

# --------------------------------------------------------------------------
# PESTAÑA 3: Propiedades, Reducción Gauss-Jordan y Subespacios
# --------------------------------------------------------------------------
with tab_propiedades:
    if not st.session_state.mis_matrices:
        st.info("👈 Comience creando o importando una matriz en la pestaña 'Gestión y Creación'.")
    else:
        with st.container(border=True):
            header_tarjeta("🔎 Propiedades Estructurales, RREF y Subespacios Fundamentales")
            mat_sel_nombre = st.selectbox("Seleccione Matriz a analizar:", list(st.session_state.mis_matrices.keys()), key="prop_mat")
            M_prop = st.session_state.mis_matrices[mat_sel_nombre]

            t_diag, t_inv, t_sub = st.tabs([
                "📋 1. Diagnóstico, Determinante y Traza",
                "🔄 2. Inversa, Adjunta y Transpuestas",
                "🏛️ 3. RREF y Los 4 Subespacios Fundamentales",
            ])

            with t_diag:
                if st.button("🚀 Ejecutar Diagnóstico Estructural", key="btn_diag_est", use_container_width=True):
                    try:
                        with st.spinner("Analizando estructura matricial…"):
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Dimensiones", f"{M_prop.rows} × {M_prop.cols}")
                            c2.metric("¿Es Cuadrada?", "Sí" if M_prop.is_square else "No")
                            if M_prop.is_square:
                                det_v = calcular_con_limite(M_prop.det, timeout=6)
                                traza_v = M_prop.trace()
                                es_inv = sp.simplify(det_v) != 0
                                es_sim = sp.simplify(M_prop - M_prop.T) == sp.zeros(M_prop.rows, M_prop.cols)
                                es_antisim = sp.simplify(M_prop + M_prop.T) == sp.zeros(M_prop.rows, M_prop.cols)
                                es_ort = es_inv and (sp.simplify(M_prop.T * M_prop - sp.eye(M_prop.rows)) == sp.zeros(M_prop.rows, M_prop.cols))
                                es_idem = sp.simplify(M_prop * M_prop - M_prop) == sp.zeros(M_prop.rows, M_prop.cols)
                                c3.metric("¿Es Invertible?", "Sí (No singular)" if es_inv else "No (Singular)")

                                st.latex(r"\det(" + mat_sel_nombre + ") = " + sp.latex(det_v) + r", \qquad \operatorname{tr}(" + mat_sel_nombre + ") = " + sp.latex(traza_v))
                                st.markdown(
                                    f"| Propiedad | Veredicto | Criterio |\n|---|---|---|\n"
                                    f"| **Simétrica** | {'✅ Sí' if es_sim else '❌ No'} | $A^T = A$ |\n"
                                    f"| **Antisimétrica** | {'✅ Sí' if es_antisim else '❌ No'} | $A^T = -A$ |\n"
                                    f"| **Ortogonal** | {'✅ Sí' if es_ort else '❌ No'} | $A^T A = I$ |\n"
                                    f"| **Idempotente (Proyección)** | {'✅ Sí' if es_idem else '❌ No'} | $A^2 = A$ |"
                                )
                            else:
                                c3.metric("Invertible", "No (No es cuadrada)")
                    except TimeoutError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error("Error durante el diagnóstico: " + str(e))

            with t_inv:
                op_inv = st.radio(
                    "Seleccione transformación matricial:",
                    ["Matriz Inversa (A⁻¹)", "Matriz Adjunta Clásica adj(A)", "Transpuesta (Aᵀ)", "Transpuesta Conjugada / Hermitiana (A*)"],
                    horizontal=True,
                )
                if st.button("🧮 Calcular Matriz", key="btn_calc_inv_tab", use_container_width=True):
                    try:
                        with st.spinner("Calculando…"):
                            if op_inv.startswith("Matriz Inversa"):
                                if not M_prop.is_square:
                                    st.error("La matriz debe ser cuadrada.")
                                else:
                                    M_num = evaluar_numerico(M_prop)
                                    if M_num is not None and M_prop.shape[0] >= 5:
                                        inv_np = np.linalg.inv(M_num)
                                        st.session_state.temp_prop_matriz = sp.Matrix(np.round(inv_np, 5))
                                    else:
                                        st.session_state.temp_prop_matriz = calcular_con_limite(M_prop.inv, timeout=6)
                            elif op_inv.startswith("Matriz Adjunta"):
                                if not M_prop.is_square:
                                    st.error("La matriz debe ser cuadrada.")
                                else:
                                    st.session_state.temp_prop_matriz = calcular_con_limite(M_prop.adjugate, timeout=6)
                            elif op_inv.startswith("Transpuesta ("):
                                st.session_state.temp_prop_matriz = M_prop.T
                            else:
                                st.session_state.temp_prop_matriz = M_prop.H
                    except TimeoutError as e:
                        st.error(str(e))
                    except Exception:
                        st.error("La matriz es singular (Determinante = 0) o no admite esta operación.")

            with t_sub:
                if st.button("🏛️ Analizar RREF y los 4 Subespacios de Strang", key="btn_sub_strang", use_container_width=True):
                    try:
                        with st.spinner("Calculando RREF y bases de subespacios…"):
                            rref_sp, pivotes = calcular_con_limite(M_prop.rref, timeout=6)
                            base_ker = calcular_con_limite(M_prop.nullspace, timeout=6)
                            base_ker_izq = calcular_con_limite(M_prop.T.nullspace, timeout=6)
                            rango_m = len(pivotes)
                            nulidad_m = len(base_ker)

                            st.success(
                                f"**Teorema del Rango-Nulidad:** Rango $\\operatorname{{rg}}(A) = {rango_m}$ + "
                                f"Nulidad $\\nu(A) = {nulidad_m}$ = {M_prop.cols} columnas."
                            )
                            st.markdown("**Forma Escalonada Reducida por Renglones (RREF):** (Columnas pivote: `" + str(pivotes) + "`)")
                            imprimir_matriz_simbolica(rref_sp)
                            st.session_state.temp_prop_matriz = rref_sp

                            s1, s2 = st.columns(2)
                            with s1:
                                st.markdown("**1. Base del Espacio Columna $\\operatorname{Col}(A) \\subseteq \\mathbb{R}^{" + str(M_prop.rows) + "}$:**")
                                cols_b = [M_prop.col(j) for j in pivotes]
                                if cols_b:
                                    imprimir_matriz_simbolica(sp.Matrix.hstack(*cols_b))
                                else:
                                    st.caption("Subespacio trivial {0}")

                                st.markdown("**2. Base del Núcleo $\\ker(A) \\subseteq \\mathbb{R}^{" + str(M_prop.cols) + "}$:**")
                                if base_ker:
                                    imprimir_matriz_simbolica(sp.Matrix.hstack(*base_ker))
                                else:
                                    st.caption("Subespacio trivial {0} (Columnas L.I.)")
                            with s2:
                                st.markdown("**3. Base del Espacio Renglón $\\operatorname{Fil}(A) \\subseteq \\mathbb{R}^{" + str(M_prop.cols) + "}$:**")
                                filas_b = [rref_sp.row(i).T for i in range(rref_sp.rows) if rref_sp.row(i) != sp.zeros(1, rref_sp.cols)]
                                if filas_b:
                                    imprimir_matriz_simbolica(sp.Matrix.hstack(*filas_b))
                                else:
                                    st.caption("Subespacio trivial {0}")

                                st.markdown("**4. Base del Núcleo Izquierdo $\\ker(A^T) \\subseteq \\mathbb{R}^{" + str(M_prop.rows) + "}$:**")
                                if base_ker_izq:
                                    imprimir_matriz_simbolica(sp.Matrix.hstack(*base_ker_izq))
                                else:
                                    st.caption("Subespacio trivial {0}")
                    except TimeoutError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error("Error al calcular subespacios: " + str(e))

        if "temp_prop_matriz" in st.session_state:
            with st.container(border=True):
                subheader_tarjeta("🎯 Matriz Resultante")
                imprimir_matriz_simbolica(st.session_state.temp_prop_matriz)
                c1, c2 = st.columns([2, 1])
                with c1:
                    nombre_save = st.text_input("Guardar esta matriz como:", key="name_prop").upper().strip()
                with c2:
                    st.write("")
                    if st.button("💾 Guardar Matriz", key="save_prop", use_container_width=True):
                        if nombre_save:
                            st.session_state.mis_matrices[nombre_save] = st.session_state.temp_prop_matriz
                            st.session_state.pop("temp_prop_matriz", None)
                            st.rerun()

# --------------------------------------------------------------------------
# PESTAÑA 4: Factorización LU, SVD, Moore-Penrose y Formas Cuadráticas
# --------------------------------------------------------------------------
with tab_descomp:
    if not st.session_state.mis_matrices:
        st.info("👈 Comience creando o importando una matriz en la pestaña 'Gestión y Creación'.")
    else:
        with st.container(border=True):
            header_tarjeta("🧩 Factorizaciones Matriciales y Formas Cuadráticas")
            mat_d_nom = st.selectbox("Seleccione Matriz:", list(st.session_state.mis_matrices.keys()), key="desc_mat_sel")
            M_d = st.session_state.mis_matrices[mat_d_nom]

            t_lu, t_svd, t_cuad = st.tabs([
                "📐 1. Factorización PA = LU",
                "🔬 2. Valores Singulares (SVD) y Pseudoinversa A⁺",
                "⛰️ 3. Formas Cuadráticas (Criterio de Sylvester)",
            ])

            with t_lu:
                st.caption("Descompone la matriz en una triangular inferior $L$ (con 1 en la diagonal) y una triangular superior $U$.")
                if st.button("🧮 Calcular Factorización LU", key="btn_lu_calc", use_container_width=True):
                    try:
                        with st.spinner("Calculando factorización LU…"):
                            L_m, U_m, perm = calcular_con_limite(M_d.LUdecomposition, timeout=6)
                            c_l, c_u = st.columns(2)
                            with c_l:
                                st.markdown("**Matriz Triangular Inferior ($L$):**")
                                imprimir_matriz_simbolica(L_m)
                            with c_u:
                                st.markdown("**Matriz Triangular Superior ($U$):**")
                                imprimir_matriz_simbolica(U_m)
                            if perm:
                                st.info(f"Se aplicaron permutaciones de renglón: {perm}")
                            else:
                                st.success("Factorización directa sin permutación de filas ($A = L \\cdot U$).")
                    except Exception as e:
                        st.error("No fue posible realizar la factorización LU: " + str(e))

            with t_svd:
                st.caption("Calcula la Descomposición en Valores Singulares $A = U \\Sigma V^T$, el número de condición $\\kappa(A)$ y la Pseudoinversa de Moore-Penrose $A^+$.")
                if st.button("🔬 Calcular SVD y Pseudoinversa A⁺", key="btn_svd_calc", use_container_width=True):
                    M_num = evaluar_numerico(M_d)
                    if M_num is None:
                        st.error("La descomposición SVD requiere una matriz con entradas numéricas reales.")
                    else:
                        U_np, S_np, Vt_np = np.linalg.svd(M_num, full_matrices=False)
                        pinv_np = np.linalg.pinv(M_num)
                        s_pos = S_np[S_np > 1e-10]
                        cond_num = float(s_pos[0] / s_pos[-1]) if len(s_pos) > 0 else float("inf")
                        norma_2 = float(S_np[0]) if len(S_np) > 0 else 0.0
                        norma_frob = float(np.linalg.norm(M_num, "fro"))

                        m1, m2, m3 = st.columns(3)
                        m1.metric("Norma Espectral ‖A‖₂ = σ_máx", f"{norma_2:.4f}")
                        m2.metric("Norma de Frobenius ‖A‖_F", f"{norma_frob:.4f}")
                        m3.metric("Número de Condición κ₂(A)", f"{cond_num:.4f}" if np.isfinite(cond_num) else "∞ (Rango deficiente)")

                        st.markdown("**Valores Singulares ($\\sigma_i$):** `" + ", ".join(f"{v:.4f}" for v in S_np) + "`")
                        c_u, c_s, c_v = st.columns(3)
                        with c_u:
                            st.markdown("**Matriz Ortogonal $U$:**")
                            imprimir_matriz_simbolica(sp.Matrix(np.round(U_np, 4)))
                        with c_s:
                            st.markdown("**Matriz Diagonal $\\Sigma$:**")
                            imprimir_matriz_simbolica(sp.Matrix(np.round(np.diag(S_np), 4)))
                        with c_v:
                            st.markdown("**Matriz Ortogonal $V^T$:**")
                            imprimir_matriz_simbolica(sp.Matrix(np.round(Vt_np, 4)))

                        st.divider()
                        st.markdown("**Pseudoinversa de Moore-Penrose ($A^+$):**")
                        mat_pinv = sp.Matrix(np.round(pinv_np, 4))
                        imprimir_matriz_simbolica(mat_pinv)
                        st.session_state.temp_prop_matriz = mat_pinv

            with t_cuad:
                st.caption("Analiza la forma cuadrática $Q(\\mathbf{x}) = \\mathbf{x}^T A \\mathbf{x}$ usando la parte simétrica $A_s = \\frac{1}{2}(A + A^T)$ y los menores principales líderes.")
                if not M_d.is_square:
                    st.warning("Seleccione una matriz cuadrada para analizar su forma cuadrática asociada.")
                elif st.button("⛰️ Evaluar Forma Cuadrática y Criterio de Sylvester", key="btn_sylv_calc", use_container_width=True):
                    try:
                        n_q = M_d.rows
                        A_sim = sp.simplify((M_d + M_d.T) / 2)
                        vars_q = sp.symbols("x1:" + str(n_q + 1))
                        vec_x = sp.Matrix(vars_q)
                        pol_q = sp.expand((vec_x.T * A_sim * vec_x)[0])

                        st.markdown("**Polinomio Cuadrático $Q(\\mathbf{x}) = \\mathbf{x}^T A \\mathbf{x}$:**")
                        st.latex("Q(" + ", ".join(sp.latex(v) for v in vars_q) + ") = " + sp.latex(pol_q))

                        menores = []
                        for k in range(1, n_q + 1):
                            sub_k = A_sim[:k, :k]
                            det_k = calcular_con_limite(sub_k.det, timeout=5)
                            menores.append((k, sp.simplify(det_k)))

                        st.markdown("**Menores Principales Líderes ($\\Delta_k = \\det(A_{1:k, 1:k})$):**")
                        for k_idx, d_val in menores:
                            st.latex(r"\Delta_{" + str(k_idx) + "} = " + sp.latex(d_val))

                        A_num_s = evaluar_numerico(A_sim)
                        if A_num_s is not None:
                            evs = np.linalg.eigvalsh(A_num_s)
                            tol = 1e-9
                            n_pos = int(np.sum(evs > tol))
                            n_neg = int(np.sum(evs < -tol))
                            n_cer = n_q - n_pos - n_neg
                            if n_pos == n_q:
                                veredicto_q = "DEFINIDA POSITIVA (todos los Δₖ > 0 y λᵢ > 0) → Mínimo global estricto en el origen"
                            elif n_neg == n_q:
                                veredicto_q = "DEFINIDA NEGATIVA ((−1)ᵏ Δₖ > 0 y λᵢ < 0) → Máximo global estricto en el origen"
                            elif n_pos > 0 and n_neg > 0:
                                veredicto_q = "INDEFINIDA (valores propios de signos opuestos) → Punto Silla"
                            elif n_pos > 0 and n_cer > 0:
                                veredicto_q = "SEMIDEFINIDA POSITIVA (λᵢ ≥ 0 con algún λ = 0)"
                            elif n_neg > 0 and n_cer > 0:
                                veredicto_q = "SEMIDEFINIDA NEGATIVA (λᵢ ≤ 0 con algún λ = 0)"
                            else:
                                veredicto_q = "NULA"
                            st.success(f"**Clasificación:** {veredicto_q} · **Ley de Inercia de Sylvester (n₊, n₋, n₀):** `({n_pos}, {n_neg}, {n_cer})`")
                    except Exception as e:
                        st.error("Error al clasificar la forma cuadrática: " + str(e))

# --------------------------------------------------------------------------
# PESTAÑA 5: Análisis Espectral (Subíndices acumulativos + confirmación de guardado)
# --------------------------------------------------------------------------
with tab_espectral:
    if not st.session_state.mis_matrices:
        st.info("👈 Comience creando o importando una matriz en la pestaña 'Gestión y Creación'.")
    else:
        with st.container(border=True):
            header_tarjeta("🌈 Valores y Vectores Propios (Eigen-Análisis)")
            st.caption("Cálculo del polinomio característico, subespacios propios y diagonalización A = P · D · P⁻¹.")

            mat_esp_nombre = st.selectbox("Seleccione Matriz a analizar:", list(st.session_state.mis_matrices.keys()), key="esp_mat")
            btn_espectral = st.button("🚀 Ejecutar Análisis Espectral", key="btn_exec_espectral", use_container_width=True)

        if btn_espectral:
            A = st.session_state.mis_matrices[mat_esp_nombre]
            if not A.is_square:
                st.error("El análisis espectral requiere una matriz cuadrada.")
                st.session_state.pop("temp_espectral", None)
            else:
                try:
                    with st.spinner("Calculando polinomio característico y subespacios propios…"):
                        lamda = sp.Symbol("lambda")
                        polinomio = calcular_con_limite(A.charpoly, args=(lamda,), timeout=6)
                        datos_esp = {
                            "nombre": mat_esp_nombre,
                            "dim": A.shape[0],
                            "polinomio_latex": sp.latex(polinomio.as_expr()),
                            "numerico": False,
                            "espectro": [],
                            "diagonalizable": False,
                            "P": None,
                            "D": None,
                            "P_inv": None,
                        }

                        A_num = evaluar_numerico(A)
                        if A_num is not None and A.shape[0] >= 4:
                            datos_esp["numerico"] = True
                            w, v = np.linalg.eig(A_num)
                            columnas_P = []
                            for i in range(len(w)):
                                val_propio = np.round(w[i], 4)
                                val_str = str(val_propio).replace("j", "i").replace("(", "").replace(")", "")
                                vec_propio = sp.Matrix(np.round(v[:, i], 4))
                                columnas_P.append(vec_propio)
                                datos_esp["espectro"].append((val_str, 1, 1, [vec_propio]))

                            rango_P = np.linalg.matrix_rank(v, tol=1e-5)
                            if rango_P == A.shape[0]:
                                datos_esp["diagonalizable"] = True
                                P = sp.Matrix.hstack(*columnas_P)
                                D = sp.diag(*[np.round(val, 4) for val in w])
                                try:
                                    P_inv = sp.Matrix(np.round(np.linalg.inv(v), 4))
                                except Exception:
                                    P_inv = calcular_con_limite(P.inv, timeout=6)
                                datos_esp["P"], datos_esp["D"], datos_esp["P_inv"] = P, D, P_inv
                        else:
                            vectores_propios = calcular_con_limite(A.eigenvects, timeout=8)
                            try:
                                vectores_propios.sort(key=lambda x: sp.re(x[0]), reverse=True)
                            except Exception:
                                pass

                            columnas_P, valores_D = [], []
                            for val, mult_alg, vects in vectores_propios:
                                vects_limpios = []
                                for v in vects:
                                    try:
                                        denominadores = [sp.fraction(e)[1] for e in v]
                                        mcm = 1
                                        for d in denominadores:
                                            mcm = sp.lcm(mcm, d)
                                        v_entero = v * mcm
                                        for e in v_entero:
                                            if e != 0:
                                                if e.is_real and e < 0:
                                                    v_entero = v_entero * -1
                                                break
                                    except Exception:
                                        v_entero = v
                                    columnas_P.append(v_entero)
                                    valores_D.append(val)
                                    vects_limpios.append(v_entero)
                                datos_esp["espectro"].append((sp.latex(val), mult_alg, len(vects), vects_limpios))

                            if len(columnas_P) == A.shape[0]:
                                datos_esp["diagonalizable"] = True
                                P = sp.Matrix.hstack(*columnas_P)
                                D = sp.diag(*valores_D)
                                P_inv = calcular_con_limite(P.inv, timeout=6)
                                datos_esp["P"], datos_esp["D"], datos_esp["P_inv"] = P, D, P_inv

                        st.session_state.temp_espectral = datos_esp
                except TimeoutError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error("Error procesando el análisis espectral: " + str(e))

        if "temp_espectral" in st.session_state:
            esp = st.session_state.temp_espectral

            with st.container(border=True):
                subheader_tarjeta("1. Polinomio Característico")
                st.latex(r"p(\lambda) = \det(A - \lambda I) = " + esp["polinomio_latex"])

            with st.container(border=True):
                subheader_tarjeta("2. Espectro y Subespacios Propios (Numeración Continua)")
                if esp["numerico"]:
                    st.info("💡 Matriz numérica grande evaluada mediante aproximación de NumPy.")
                contador_vec = 1
                for val_ltx, m_a, m_g, vects_l in esp["espectro"]:
                    st.latex(r"\lambda = " + val_ltx)
                    if not esp["numerico"]:
                        st.caption(f"Multiplicidad Algebraica (mₐ): {m_a} | Multiplicidad Geométrica (m_g): {m_g}")
                    for vec_item in vects_l:
                        st.latex("v_{" + str(contador_vec) + "} = " + sp.latex(vec_item))
                        contador_vec += 1

            with st.container(border=True):
                subheader_tarjeta("3. Diagonalización (A = P · D · P⁻¹)")
                if esp["diagonalizable"]:
                    st.success("La matriz **SÍ** es diagonalizable (la suma de multiplicidades geométricas iguala al orden de la matriz).")
                    col_p, col_d, col_pinv = st.columns(3)
                    with col_p:
                        st.write("**Matriz de Paso (P)**")
                        imprimir_matriz_simbolica(esp["P"])
                    with col_d:
                        st.write("**Matriz Diagonal (D)**")
                        imprimir_matriz_simbolica(esp["D"])
                    with col_pinv:
                        st.write("**Inversa (P⁻¹)**")
                        imprimir_matriz_simbolica(esp["P_inv"])

                    st.divider()
                    desea_guardar = st.checkbox(
                        "💾 ¿Desea guardar alguna de las matrices generadas (P, D o P⁻¹) en su inventario?",
                        value=False,
                        key="chk_preguntar_guardar_esp",
                    )
                    if desea_guardar:
                        c_g1, c_g2, c_g3 = st.columns(3)
                        with c_g1:
                            g_p = st.checkbox("Guardar Matriz P", value=True, key="chk_g_p")
                            nom_p = st.text_input("Nombre para P:", value="P_" + esp["nombre"], key="in_nom_p").upper().strip()
                        with c_g2:
                            g_d = st.checkbox("Guardar Matriz D", value=True, key="chk_g_d")
                            nom_d = st.text_input("Nombre para D:", value="D_" + esp["nombre"], key="in_nom_d").upper().strip()
                        with c_g3:
                            g_pinv = st.checkbox("Guardar Matriz P⁻¹", value=False, key="chk_g_pinv")
                            nom_pinv = st.text_input("Nombre para P⁻¹:", value="PINV_" + esp["nombre"], key="in_nom_pinv").upper().strip()

                        if st.button("💾 Confirmar y Guardar Selección", key="btn_confirm_esp", use_container_width=True):
                            guardadas = []
                            if g_p and nom_p:
                                st.session_state.mis_matrices[nom_p] = esp["P"]
                                guardadas.append(nom_p)
                            if g_d and nom_d:
                                st.session_state.mis_matrices[nom_d] = esp["D"]
                                guardadas.append(nom_d)
                            if g_pinv and nom_pinv:
                                st.session_state.mis_matrices[nom_pinv] = esp["P_inv"]
                                guardadas.append(nom_pinv)
                            if guardadas:
                                st.success("Guardadas en el inventario: " + ", ".join(guardadas))
                                st.rerun()
                else:
                    st.error("La matriz **NO** es diagonalizable (alguna multiplicidad geométrica es menor que su multiplicidad algebraica).")

# --------------------------------------------------------------------------
# PESTAÑA 6: Hessiana y Jacobiana
# --------------------------------------------------------------------------
with tab_avanzadas:
    col_av1, col_av2 = st.columns(2, gap="large")

    with col_av1:
        with st.container(border=True):
            header_tarjeta("📐 1. Matriz Hessiana (Función Escalar)")
            usar_kb_hess = False
            if _TIENE_TECLADO:
                usar_kb_hess = st.toggle("⌨️ Usar Teclado Matemático", value=True, key="hess_kb_toggle")

            if usar_kb_hess:
                lat_hess = teclado_matematico(
                    "hess_func_kb",
                    valor_inicial=r"2x^{2}+12xy+y^{3}",
                    placeholder="Escribe f(x, y) y pulsa ↵",
                    acoplado=True,
                )
                if st.button("🧮 Calcular Hessiana", key="btn_hessian_kb", use_container_width=True):
                    if not lat_hess:
                        st.warning("Confirma la función en el teclado pulsando ↵.")
                    else:
                        try:
                            f = latex_a_sympy(lat_hess)
                            st.caption("Entiendo: " + leer_en_espanol(f))
                            vars_list = sorted(list(f.free_symbols), key=lambda v: v.name)
                            if not vars_list:
                                st.error("La función es constante.")
                            else:
                                H = calcular_con_limite(sp.hessian, args=(f, vars_list), timeout=5)
                                st.session_state.temp_avanzada = H
                        except ErrorLatex as e:
                            st.error("Error al interpretar la expresión: " + str(e))
                        except Exception as e:
                            st.error("Error al calcular la Hessiana: " + str(e))
            else:
                expr_str = st.text_input("Ingrese la función escalar f (Ej: 2*x^2 + 12*x*y):", value="2*x^2 + 12*x*y", key="input_hessian")
                if st.button("🧮 Calcular Hessiana", key="btn_hessian_txt", use_container_width=True):
                    f = _leer_seguro(expr_str)
                    if f is not None:
                        vars_list = sorted(list(f.free_symbols), key=lambda v: v.name)
                        if not vars_list:
                            st.error("La función es constante.")
                        else:
                            try:
                                H = calcular_con_limite(sp.hessian, args=(f, vars_list), timeout=5)
                                st.session_state.temp_avanzada = H
                            except TimeoutError as e:
                                st.error(str(e))

    with col_av2:
        with st.container(border=True):
            header_tarjeta("🔄 2. Matriz Jacobiana (Campo Vectorial)")
            if not st.session_state.mis_matrices:
                st.info("Guarde primero una matriz columna o fila (vector simbólico) en 'Gestión y Creación' para calcular su Jacobiana.")
            else:
                mat_jac_nombre = st.selectbox("Seleccione Vector simbólico base:", list(st.session_state.mis_matrices.keys()), key="jac_mat")
                if st.button("🧮 Calcular Jacobiana", key="btn_jacobian", use_container_width=True):
                    M_jac = st.session_state.mis_matrices[mat_jac_nombre]
                    variables = sorted(list(M_jac.free_symbols), key=lambda v: v.name)
                    if not variables:
                        st.error("La matriz seleccionada no contiene variables simbólicas.")
                    elif M_jac.shape[0] != 1 and M_jac.shape[1] != 1:
                        st.error(f"La Jacobiana requiere un vector (1×n o n×1). La matriz mide {M_jac.shape[0]}×{M_jac.shape[1]}.")
                    else:
                        try:
                            vec_col = M_jac if M_jac.shape[1] == 1 else M_jac.T
                            J = calcular_con_limite(vec_col.jacobian, args=(variables,), timeout=5)
                            st.session_state.temp_avanzada = J
                        except TimeoutError as e:
                            st.error(str(e))
                        except Exception as e:
                            st.error("Error al procesar la Jacobiana: " + str(e))

    if "temp_avanzada" in st.session_state:
        with st.container(border=True):
            subheader_tarjeta("🎯 Resultado del Cálculo Diferencial")
            imprimir_matriz_simbolica(st.session_state.temp_avanzada)
            c1, c2 = st.columns([2, 1])
            with c1:
                nom_av = st.text_input("Guardar matriz resultante como:", key="name_av").upper().strip()
            with c2:
                st.write("")
                if st.button("💾 Guardar Matriz", key="save_av", use_container_width=True):
                    if nom_av:
                        st.session_state.mis_matrices[nom_av] = st.session_state.temp_avanzada
                        st.session_state.pop("temp_avanzada", None)
                        st.rerun()
