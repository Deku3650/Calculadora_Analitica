# pages/2_Matrices.py
import numpy as np
import streamlit as st
import sympy as sp

# 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO)
st.set_page_config(page_title="Álgebra Lineal: Matrices - MATHESIS", page_icon="🧮", layout="wide")

from estilos import cargar_estilos_globales, encabezado_pagina, titulo_tarjeta  # noqa: E402
from utils import (  # noqa: E402
    calcular_con_limite,
    evaluar_numerico,
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

# ==============================================================================
# ENCABEZADO PRINCIPAL
# ==============================================================================
encabezado_pagina("🧮 Álgebra Lineal: Matrices")

# ==============================================================================
# BARRA LATERAL (INVENTARIO)
# ==============================================================================
with st.sidebar:
    st.header("📦 Inventario de Matrices")

    if st.session_state.mis_matrices:
        for nombre, mat in st.session_state.mis_matrices.items():
            with st.expander(f"Matriz: {nombre} ({mat.shape[0]}×{mat.shape[1]})"):
                imprimir_matriz_simbolica(mat)
    else:
        st.info("No hay matrices en memoria.")

    st.divider()
    if st.button("🗑️ Borrar todas las matrices", use_container_width=True):
        st.session_state.mis_matrices.clear()
        for k_tmp in ("temp_matriz", "temp_prop_matriz", "temp_avanzada"):
            st.session_state.pop(k_tmp, None)
        st.rerun()

# ==============================================================================
# ÁREA PRINCIPAL (PESTAÑAS INTERACTIVAS)
# ==============================================================================
tab_gestion, tab_basicas, tab_propiedades, tab_avanzadas, tab_espectral = st.tabs([
    "📥 Gestión y Creación",
    "➕ Operaciones Básicas",
    "🔎 Propiedades y Reducción",
    "📐 Cálculo Multivariable",
    "🌈 Análisis Espectral",
])

# --------------------------------------------------------------------------
# PESTAÑA 0: Constructor, Creación Manual y Puentes
# --------------------------------------------------------------------------
with tab_gestion:
    st.subheader("Constructor y Puentes de Datos")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        with st.container(border=True):
            titulo_tarjeta("➕ Nueva Matriz Manual")

            nombre_nueva = st.text_input("Asignar nombre de la matriz (Ej: A, M1):", key="input_nom_manual").upper().strip()

            col_m, col_n = st.columns(2)
            with col_m:
                filas = st.number_input("Número de filas:", min_value=1, max_value=10, value=2, step=1, key="num_filas_mat")
            with col_n:
                columnas = st.number_input("Número de columnas:", min_value=1, max_value=10, value=2, step=1, key="num_cols_mat")

            st.divider()
            titulo_tarjeta("🧩 Componentes de la Matriz", sub=True)

            matriz_elementos = []
            error_sintaxis = False

            for i in range(filas):
                cols = st.columns(columnas)
                fila_vals = []
                for j in range(columnas):
                    with cols[j]:
                        val_str = st.text_input(
                            f"Elemento ({i+1}, {j+1}):",
                            value="1" if i == j else "0",
                            key=f"celda_{i}_{j}_{filas}_{columnas}",
                        ).strip()

                        try:
                            val_sym = leer_expresion_st(val_str)
                            if val_sym is not None:
                                fila_vals.append(val_sym)
                            else:
                                error_sintaxis = True
                        except Exception:
                            error_sintaxis = True
                matriz_elementos.append(fila_vals)

            st.write("")
            if error_sintaxis:
                st.error("⚠️ Ingrese expresiones matemáticas o números válidos en todas las celdas.")
            else:
                matriz_temp = sp.Matrix(matriz_elementos)

                st.markdown("**Vista previa:**")
                st.latex(f"{nombre_nueva if nombre_nueva else 'M'} = {sp.latex(matriz_temp)}")

                if st.button("💾 Guardar Matriz", key="btn_guardar_mat_manual", use_container_width=True):
                    if not nombre_nueva:
                        st.error("Por favor, asigna un nombre a la matriz.")
                    else:
                        if nombre_nueva in st.session_state.mis_matrices:
                            st.warning(f"La matriz '{nombre_nueva}' fue sobreescrita.")
                        st.session_state.mis_matrices[nombre_nueva] = matriz_temp
                        st.success(f"¡Matriz '{nombre_nueva}' guardada exitosamente!")
                        st.rerun()

    with col_g2:
        with st.container(border=True):
            titulo_tarjeta("🔀 Importación y Exportación")

            fuente_import = st.selectbox(
                "¿De dónde desea importar?",
                ["Seleccione...", "De una Transformación Activa", "De un Conjunto de Vectores"],
            )

            if fuente_import == "De una Transformación Activa":
                if st.session_state.get("mis_transformaciones"):
                    tl_import = st.selectbox("Seleccione la T.L.:", list(st.session_state.mis_transformaciones.keys()), key="imp_tl_main")
                    nom_mat_tl = st.text_input("Guardar matriz asociada como (Ej. M_T1):", key="nom_mat_tl_main").upper().strip()

                    if st.button("⬇️ Importar Matriz Asociada", use_container_width=True):
                        if nom_mat_tl:
                            st.session_state.mis_matrices[nom_mat_tl] = st.session_state.mis_transformaciones[tl_import]["matriz_asociada"]
                            st.success(f"Matriz '{nom_mat_tl}' importada con éxito.")
                            st.rerun()
                        else:
                            st.error("Ingrese un nombre para guardar la matriz.")
                else:
                    st.info("No hay transformaciones definidas en memoria.")

            elif fuente_import == "De un Conjunto de Vectores":
                if st.session_state.get("mis_vectores"):
                    vecs_import = st.multiselect("Seleccione vectores para formar las columnas:", list(st.session_state.mis_vectores.keys()), key="imp_vecs_main")
                    nom_mat_vec = st.text_input("Guardar matriz generada como (Ej. BASE1):", key="nom_mat_vec_main").upper().strip()

                    if st.button("⬇️ Construir e Importar Matriz", key="btn_build_vec", use_container_width=True):
                        if not vecs_import or not nom_mat_vec:
                            st.error("Complete los campos obligatorios.")
                        else:
                            try:
                                lista_vectores = [st.session_state.mis_vectores[v] for v in vecs_import]
                                matriz_armada = sp.Matrix.hstack(*lista_vectores)
                                st.session_state.mis_matrices[nom_mat_vec] = matriz_armada
                                st.success(f"Matriz '{nom_mat_vec}' construida e importada.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: Los vectores deben tener la misma dimensión. Detalle: {e}")
                else:
                    st.info("No hay vectores definidos en memoria.")

            st.divider()
            titulo_tarjeta("📤 Exportar a Transformación", sub=True)
            if st.session_state.mis_matrices:
                mat_export = st.selectbox("Matriz a exportar:", list(st.session_state.mis_matrices.keys()), key="exp_mat_tl_main")
                nombre_tl = st.text_input("Nombre de la nueva T.L. (Ej. T1):", key="nombre_tl_main").upper().strip()

                if st.button("Crear Transformación", key="btn_crear_tl_main", use_container_width=True):
                    if nombre_tl:
                        A_export = st.session_state.mis_matrices[mat_export]
                        filas_e, columnas_e = A_export.shape
                        vars_input = sp.symbols(f"x1:{columnas_e+1}")
                        regla_correspondencia = A_export * sp.Matrix(vars_input)

                        st.session_state.mis_transformaciones[nombre_tl] = {
                            "matriz_asociada": A_export,
                            "regla": regla_correspondencia,
                            "variables": vars_input,
                            "dim_V": columnas_e,
                            "dim_W": filas_e,
                            "espacio_V": rf"\mathbb{{R}}^{{{columnas_e}}}",
                            "espacio_W": rf"\mathbb{{R}}^{{{filas_e}}}",
                            "base_dominio": sp.eye(columnas_e),
                            "base_codominio": sp.eye(filas_e),
                        }
                        st.success(f"T.L. '{nombre_tl}' creada exitosamente en el módulo de Transformaciones.")
                    else:
                        st.error("Ingrese un nombre para la T.L.")
            else:
                st.caption("Guarde al menos una matriz para exportarla como Transformación Lineal.")

# --------------------------------------------------------------------------
# PESTAÑA 1: Operaciones Básicas
# --------------------------------------------------------------------------
with tab_basicas:
    if not st.session_state.mis_matrices:
        st.info("👈 Comience creando o importando una matriz en la pestaña 'Gestión y Creación'.")
    else:
        with st.container(border=True):
            titulo_tarjeta("➕ Operaciones Algebraicas Básicas")
            st.caption("Realice suma, resta, multiplicación, potencia entera y producto escalar entre las matrices en memoria.")

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                mat_A_nombre = st.selectbox("Matriz A", list(st.session_state.mis_matrices.keys()), key="op_matA")
            with col2:
                operacion = st.selectbox("Operación", ["+", "-", "*", "* Escalar", "Potencia A^k"])
            with col3:
                if operacion == "* Escalar":
                    escalar_str = st.text_input("Ingrese Escalar (Ej: 2, x, 1/2):", value="2")
                elif operacion == "Potencia A^k":
                    pot_k = int(st.number_input("Exponente entero k:", min_value=0, max_value=20, value=2, step=1))
                else:
                    mat_B_nombre = st.selectbox("Matriz B", list(st.session_state.mis_matrices.keys()), key="op_matB")

            if st.button("🧮 Calcular Resultado", key="btn_basicas", use_container_width=True):
                matA = st.session_state.mis_matrices[mat_A_nombre]
                res = None

                if operacion == "* Escalar":
                    esc = leer_expresion_st(escalar_str)
                    if esc is not None:
                        res = sp.simplify(esc * matA)
                elif operacion == "Potencia A^k":
                    if not matA.is_square:
                        st.error("Error: Solo las matrices cuadradas pueden elevarse a una potencia.")
                    else:
                        res = sp.simplify(matA**pot_k)
                else:
                    matB = st.session_state.mis_matrices[mat_B_nombre]
                    if operacion in ["+", "-"] and matA.shape != matB.shape:
                        st.error("Error: Las matrices deben tener la misma dimensión para sumar o restar.")
                    elif operacion == "*" and matA.shape[1] != matB.shape[0]:
                        st.error("Error: Las dimensiones no son compatibles para multiplicar.")
                    else:
                        if operacion == "+":
                            res = matA + matB
                        elif operacion == "-":
                            res = matA - matB
                        elif operacion == "*":
                            res = matA * matB

                if res is not None:
                    st.session_state.temp_matriz = res

        if "temp_matriz" in st.session_state:
            with st.container(border=True):
                titulo_tarjeta("🎯 Resultado de la Operación", sub=True)
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
                            st.success(f"Matriz '{nombre_save}' guardada exitosamente.")
                            st.rerun()
                        else:
                            st.error("Ingrese un nombre.")

# --------------------------------------------------------------------------
# PESTAÑA 2: Propiedades y Reducción Gaussiana
# --------------------------------------------------------------------------
with tab_propiedades:
    if not st.session_state.mis_matrices:
        st.info("👈 Comience creando o importando una matriz en la pestaña 'Gestión y Creación'.")
    else:
        with st.container(border=True):
            titulo_tarjeta("🔎 Análisis Estructural y Reducción Gaussiana")

            mat_sel_nombre = st.selectbox("Seleccione Matriz a analizar:", list(st.session_state.mis_matrices.keys()), key="prop_mat")
            M = st.session_state.mis_matrices[mat_sel_nombre]

            titulo_tarjeta("⚙️ Propiedad o Transformación a Evaluar", sub=True)
            prop_elegida = st.radio(
                "Seleccione el análisis:",
                [
                    "Diagnóstico Estructural Completo",
                    "Determinante",
                    "Traza",
                    "Inversa",
                    "Adjunta Clásica",
                    "Transpuesta Conjugada",
                    "Rango y Subespacios",
                    "Matriz Reducida (RREF)",
                ],
                horizontal=True,
            )

            if st.button("🚀 Analizar Propiedad", key="btn_prop", use_container_width=True):
                res_matriz = None

                if prop_elegida == "Diagnóstico Estructural Completo":
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Dimensiones", f"{M.rows} × {M.cols}")
                    c2.metric("¿Es Cuadrada?", "Sí" if M.is_square else "No")
                    if M.is_square:
                        det_v = calcular_con_limite(M.det, timeout=5)
                        es_inv = sp.simplify(det_v) != 0
                        es_sim = sp.simplify(M - M.T) == sp.zeros(M.rows, M.cols)
                        es_antisim = sp.simplify(M + M.T) == sp.zeros(M.rows, M.cols)
                        es_ort = es_inv and (sp.simplify(M.T * M - sp.eye(M.rows)) == sp.zeros(M.rows, M.cols))
                        c3.metric("¿Es Invertible?", "Sí (No singular)" if es_inv else "No (Singular)")
                        st.markdown(
                            f"- **Determinante:** ${sp.latex(det_v)}$ | **Traza:** ${sp.latex(M.trace())}$\n"
                            f"- **Simétrica ($A^T = A$):** {'✅ Sí' if es_sim else '❌ No'} | "
                            f"**Antisimétrica ($A^T = -A$):** {'✅ Sí' if es_antisim else '❌ No'} | "
                            f"**Ortogonal ($A^T A = I$):** {'✅ Sí' if es_ort else '❌ No'}"
                        )

                elif prop_elegida == "Determinante":
                    if M.is_square:
                        try:
                            det_val = calcular_con_limite(M.det, timeout=5)
                            st.success(f"**Determinante:** ${sp.latex(det_val)}$")
                        except TimeoutError as e:
                            st.error(str(e))
                    else:
                        st.error("La matriz debe ser cuadrada.")

                elif prop_elegida == "Traza":
                    if M.is_square:
                        st.success(f"**Traza:** ${sp.latex(M.trace())}$")
                    else:
                        st.error("La matriz debe ser cuadrada.")

                elif prop_elegida == "Inversa":
                    if M.is_square:
                        try:
                            M_num = evaluar_numerico(M)
                            if M_num is not None and M.shape[0] >= 4:
                                st.info("💡 Matriz numérica grande: Evaluando con motor NumPy para mayor velocidad.")
                                inv_np = np.linalg.inv(M_num)
                                res_matriz = sp.Matrix(np.round(inv_np, 4))
                            else:
                                res_matriz = calcular_con_limite(M.inv, timeout=5)
                            st.write("Matriz Inversa ($A^{-1}$):")
                        except TimeoutError as e:
                            st.error(str(e))
                        except Exception:
                            st.error("La matriz es singular (Determinante = 0) o no se puede invertir.")
                    else:
                        st.error("La matriz debe ser cuadrada.")

                elif prop_elegida == "Adjunta Clásica":
                    if M.is_square:
                        try:
                            res_matriz = calcular_con_limite(M.adjugate, timeout=5)
                            st.write("Matriz Adjunta Clásica (Matriz de Cofactores Transpuesta):")
                        except TimeoutError as e:
                            st.error(str(e))
                    else:
                        st.error("La matriz debe ser cuadrada.")

                elif prop_elegida == "Transpuesta Conjugada":
                    res_matriz = M.H
                    st.write("Matriz Transpuesta Conjugada ($A^*$ o $A^H$):")
                    if not M.has(sp.I):
                        st.info("No contiene complejos; la Transpuesta Conjugada coincide con la Transpuesta normal ($A^T$).")

                elif prop_elegida == "Matriz Reducida (RREF)":
                    try:
                        rref_sp, pivotes = calcular_con_limite(M.rref, timeout=5)
                        res_matriz = rref_sp
                        st.write("Forma Escalonada Reducida por Renglones:")
                        st.info(f"Columnas pivote (índices desde 0): {pivotes}")
                    except TimeoutError as e:
                        st.error(str(e))

                elif prop_elegida == "Rango y Subespacios":
                    try:
                        rref_sp, pivotes = calcular_con_limite(M.rref, timeout=5)
                        base_kernel = calcular_con_limite(M.nullspace, timeout=5)
                        st.success(
                            f"**Rango $\\operatorname{{rg}}(A) = {len(pivotes)}$** | "
                            f"**Nulidad $\\nu(A) = {len(base_kernel)}$** | "
                            f"**Teorema Rango-Nulidad:** ${len(pivotes)} + {len(base_kernel)} = {M.cols}$ columnas"
                        )

                        col_sub1, col_sub2 = st.columns(2)
                        with col_sub1:
                            st.write("**Base del Espacio Renglón ($L_r(A)$):**")
                            renglones = [rref_sp.row(i) for i in range(rref_sp.rows) if rref_sp.row(i) != sp.zeros(1, rref_sp.cols)]
                            if renglones:
                                imprimir_matriz_simbolica(sp.Matrix(renglones))
                            else:
                                st.write("Trivial $\\{\\mathbf{0}\\}$")

                        with col_sub2:
                            st.write("**Base del Espacio Columna ($L_c(A)$):**")
                            columnas = [M.col(j) for j in pivotes]
                            if columnas:
                                imprimir_matriz_simbolica(sp.Matrix.hstack(*columnas))
                            else:
                                st.write("Trivial $\\{\\mathbf{0}\\}$")

                        st.divider()
                        st.write("**Base del Kernel (Espacio Nulo $\\ker A$):**")
                        if base_kernel:
                            imprimir_matriz_simbolica(sp.Matrix.hstack(*base_kernel))
                        else:
                            st.write("El Kernel es trivial $\\{\\mathbf{0}\\}$.")
                    except TimeoutError as e:
                        st.error(str(e))

                if res_matriz is not None:
                    st.session_state.temp_prop_matriz = res_matriz

        if "temp_prop_matriz" in st.session_state:
            with st.container(border=True):
                titulo_tarjeta("🎯 Matriz Resultante", sub=True)
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
                            st.success(f"Matriz '{nombre_save}' guardada exitosamente.")
                            st.rerun()
                        else:
                            st.error("Ingrese un nombre.")

# --------------------------------------------------------------------------
# PESTAÑA 3: Cálculo Multivariable (Hessiana siempre activa + Jacobiana)
# --------------------------------------------------------------------------
with tab_avanzadas:
    col_av1, col_av2 = st.columns(2)

    with col_av1:
        with st.container(border=True):
            titulo_tarjeta("📐 1. Matriz Hessiana (Función Escalar)")
            st.caption("Derivadas parciales de segundo orden $H_f(x_1, \\dots, x_n)$. No requiere tener matrices previas.")

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
                btn_h = st.button("🧮 Calcular Hessiana", key="btn_hessian_kb", use_container_width=True)
                if btn_h:
                    if not lat_hess:
                        st.warning("Confirma la función en el teclado pulsando ↵.")
                    else:
                        try:
                            f = latex_a_sympy(lat_hess)
                            st.caption(f"Entiendo: {leer_en_espanol(f)}")
                            vars_list = sorted(list(f.free_symbols), key=lambda v: v.name)
                            if not vars_list:
                                st.error("La función es constante.")
                            else:
                                H = calcular_con_limite(sp.hessian, args=(f, vars_list), timeout=5)
                                st.success(f"Función detectada: $f({', '.join([v.name for v in vars_list])})$")
                                st.session_state.temp_avanzada = H
                        except ErrorLatex as e:
                            st.error(f"Error al interpretar la expresión: {e}")
                        except Exception as e:
                            st.error(f"Error al calcular la Hessiana: {e}")
            else:
                expr_str = st.text_input("Ingrese la función escalar $f$ (Ej: 2*x^2 + 12*x*y):", value="2*x^2 + 12*x*y", key="input_hessian")
                if st.button("🧮 Calcular Hessiana", key="btn_hessian_txt", use_container_width=True):
                    f = leer_expresion_st(expr_str)
                    if f is not None:
                        vars_list = sorted(list(f.free_symbols), key=lambda v: v.name)
                        if not vars_list:
                            st.error("La función es constante.")
                        else:
                            try:
                                H = calcular_con_limite(sp.hessian, args=(f, vars_list), timeout=5)
                                st.success(f"Función detectada: $f({', '.join([v.name for v in vars_list])})$")
                                st.session_state.temp_avanzada = H
                            except TimeoutError as e:
                                st.error(str(e))

    with col_av2:
        with st.container(border=True):
            titulo_tarjeta("🔄 2. Matriz Jacobiana (Campo Vectorial)")
            st.caption("Matriz de derivadas parciales de primer orden para un vector simbólico guardado.")

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
                        st.error(f"Error Matemático: La Jacobiana requiere un vector ($1\\times n$ o $n\\times 1$). La matriz mide {M_jac.shape[0]}×{M_jac.shape[1]}.")
                    else:
                        try:
                            vec_col = M_jac if M_jac.shape[1] == 1 else M_jac.T
                            J = calcular_con_limite(vec_col.jacobian, args=(variables,), timeout=5)
                            st.success(f"Jacobiana evaluada respecto a: `{', '.join(str(v) for v in variables)}`")
                            st.session_state.temp_avanzada = J
                        except TimeoutError as e:
                            st.error(str(e))
                        except Exception as e:
                            st.error(f"Error inesperado al procesar la Jacobiana: {e}")

    if "temp_avanzada" in st.session_state:
        with st.container(border=True):
            titulo_tarjeta("🎯 Resultado del Cálculo Diferencial", sub=True)
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
                        st.success(f"Matriz '{nom_av}' guardada exitosamente.")
                        st.rerun()
                    else:
                        st.error("Ingrese un nombre para guardar la matriz.")

# --------------------------------------------------------------------------
# PESTAÑA 4: Análisis Espectral
# --------------------------------------------------------------------------
with tab_espectral:
    if not st.session_state.mis_matrices:
        st.info("👈 Comience creando o importando una matriz en la pestaña 'Gestión y Creación'.")
    else:
        with st.container(border=True):
            titulo_tarjeta("🌈 Valores y Vectores Propios (Eigen-Análisis)")
            st.caption("Cálculo del polinomio característico, subespacios propios y diagonalización $A = P D P^{-1}$.")

            mat_esp_nombre = st.selectbox("Seleccione Matriz a analizar:", list(st.session_state.mis_matrices.keys()), key="esp_mat")
            btn_espectral = st.button("🚀 Ejecutar Análisis Espectral", key="btn_exec_espectral", use_container_width=True)

        if btn_espectral:
            A = st.session_state.mis_matrices[mat_esp_nombre]

            if not A.is_square:
                st.error("El análisis espectral requiere una matriz cuadrada.")
            else:
                try:
                    lamda = sp.Symbol("lambda")
                    polinomio = calcular_con_limite(A.charpoly, args=(lamda,), timeout=5)

                    with st.container(border=True):
                        titulo_tarjeta("1. Polinomio Característico", sub=True)
                        st.latex(f"p(\\lambda) = \\det(A - \\lambda I) = {sp.latex(polinomio.as_expr())}")

                    A_num = evaluar_numerico(A)
                    if A_num is not None and A.shape[0] >= 4:
                        st.info("💡 Matriz numérica grande detectada: Evaluando con motor NumPy.")
                        w, v = np.linalg.eig(A_num)

                        with st.container(border=True):
                            titulo_tarjeta("2. Espectro y Bases (Aproximación Numérica)", sub=True)
                            columnas_P = []
                            for i in range(len(w)):
                                val_propio = np.round(w[i], 4)
                                val_str = str(val_propio).replace("j", "i").replace("(", "").replace(")", "")
                                st.markdown(rf"##### $\lambda \approx {val_str}$")
                                vec_propio = sp.Matrix(np.round(v[:, i], 4))
                                columnas_P.append(vec_propio)
                                st.latex(rf"v_{{{i+1}}} = {sp.latex(vec_propio)}")

                        with st.container(border=True):
                            titulo_tarjeta("3. Diagonalización", sub=True)
                            rango_P = np.linalg.matrix_rank(v, tol=1e-5)

                            if rango_P == A.shape[0]:
                                st.success("La matriz **SÍ** es diagonalizable (Aproximación Numérica).")
                                P = sp.Matrix.hstack(*columnas_P)
                                D = sp.diag(*[np.round(val, 4) for val in w])
                                try:
                                    P_inv = sp.Matrix(np.round(np.linalg.inv(v), 4))
                                except Exception:
                                    P_inv = calcular_con_limite(P.inv, timeout=5)

                                col_p, col_d, col_pinv = st.columns(3)
                                with col_p:
                                    st.write("**Matriz de Paso ($P$)**")
                                    imprimir_matriz_simbolica(P)
                                with col_d:
                                    st.write("**Matriz Diagonal ($D$)**")
                                    imprimir_matriz_simbolica(D)
                                with col_pinv:
                                    st.write("**Inversa ($P^{-1}$)**")
                                    imprimir_matriz_simbolica(P_inv)
                            else:
                                st.error(f"La matriz **NO** es diagonalizable numéricamente (Rango de $P = {rango_P} < {A.shape[0]}$).")
                    else:
                        vectores_propios = calcular_con_limite(A.eigenvects, timeout=8)
                        try:
                            vectores_propios.sort(key=lambda x: sp.re(x[0]), reverse=True)
                        except Exception:
                            pass

                        with st.container(border=True):
                            titulo_tarjeta("2. Espectro y Subespacios Propios", sub=True)
                            columnas_P, valores_D = [], []

                            for val, mult_alg, vects in vectores_propios:
                                st.markdown(f"##### $\\lambda = {sp.latex(val)}$")
                                st.caption(f"Multiplicidad Algebraica ($m_a$): {mult_alg} | Multiplicidad Geométrica ($m_g$): {len(vects)}")

                                for i, v in enumerate(vects):
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
                                    st.latex(f"v_{{{i+1}}} = {sp.latex(v_entero)}")

                        with st.container(border=True):
                            titulo_tarjeta("3. Diagonalización ($A = P D P^{-1}$)", sub=True)
                            if len(columnas_P) == A.shape[0]:
                                st.success("La matriz **SÍ** es diagonalizable ($\\sum m_g = n$).")
                                P = sp.Matrix.hstack(*columnas_P)
                                D = sp.diag(*valores_D)
                                P_inv = calcular_con_limite(P.inv, timeout=5)

                                col_p, col_d, col_pinv = st.columns(3)
                                with col_p:
                                    st.write("**Matriz de Paso ($P$)**")
                                    imprimir_matriz_simbolica(P)
                                with col_d:
                                    st.write("**Matriz Diagonal ($D$)**")
                                    imprimir_matriz_simbolica(D)
                                with col_pinv:
                                    st.write("**Inversa ($P^{-1}$)**")
                                    imprimir_matriz_simbolica(P_inv)

                                st.session_state.mis_matrices[f"P_{mat_esp_nombre}"] = P
                                st.session_state.mis_matrices[f"D_{mat_esp_nombre}"] = D
                                st.caption(f"💡 Se guardaron automáticamente `P_{mat_esp_nombre}` y `D_{mat_esp_nombre}` en tu inventario lateral.")
                            else:
                                st.error("La matriz **NO** es diagonalizable (alguna multiplicidad geométrica es menor que su multiplicidad algebraica).")

                except TimeoutError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error procesando el análisis espectral: {e}")
