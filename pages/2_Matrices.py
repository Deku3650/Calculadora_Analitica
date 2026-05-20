import streamlit as st
import sympy as sp

# Intentamos importar las herramientas base
try:
    from utils import Crear_Matriz_Simbolica_UI, imprimir_matriz_simbolica
except ImportError:
    st.error("Error al cargar utils.py. Asegúrese de ejecutar la aplicación correctamente.")

st.set_page_config(page_title="Matrices", layout="wide")

if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}

st.title("🧮 Álgebra Lineal: Matrices")

# ==============================================================================
# PANEL LATERAL (CREACIÓN DE MATRICES)
# ==============================================================================
with st.sidebar:
    st.header("Inventario de Matrices")

    # 1. Mostrar matrices guardadas
    if st.session_state.mis_matrices:
        for nombre, mat in st.session_state.mis_matrices.items():
            st.write(f"**{nombre}**:")
            imprimir_matriz_simbolica(mat)
    else:
        st.info("No hay matrices en memoria.")

    st.divider()

    # 2. Creador de matrices
    st.subheader("Nueva Matriz")
    nombre_nueva = st.text_input("Asignar nombre (Ej: A, M1):").upper().strip()

    if nombre_nueva:
        if nombre_nueva in st.session_state.mis_matrices:
            st.warning("Ese nombre ya existe. Se sobreescribirá.")

        # Llamamos a la función UI que programamos en utils.py
        matriz_creada = Crear_Matriz_Simbolica_UI(nombre_nueva)

        if matriz_creada is not None:
            st.session_state.mis_matrices[nombre_nueva] = matriz_creada
            st.success(f"Matriz {nombre_nueva} guardada.")
            # Forzamos recarga para que aparezca arriba en el inventario
            st.rerun()

    st.divider()
    if st.button("🗑️ Borrar todas las matrices"):
        st.session_state.mis_matrices.clear()
        st.rerun()

# ==============================================================================
# ÁREA PRINCIPAL (OPERACIONES MATEMÁTICAS)
# ==============================================================================
# Solo mostramos las operaciones si hay al menos una matriz
if not st.session_state.mis_matrices:
    st.info("👈 Comience creando una matriz en el panel lateral.")
else:
    # Usamos pestañas para agrupar las operaciones por "tipo"
    tab_basicas, tab_propiedades, tab_avanzadas, tab_espectral = st.tabs([
        "Operaciones Básicas", "Propiedades y Reducción", "Cálculo Multivariable", "Análisis Espectral"
    ])

    # --------------------------------------------------------------------------
    # PESTAÑA 1: Operaciones Básicas (Suma, Resta, Mult)
    # --------------------------------------------------------------------------
    with tab_basicas:
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            mat_A_nombre = st.selectbox("Matriz A", list(st.session_state.mis_matrices.keys()), key="op_matA")
        with col2:
            operacion = st.selectbox("Operación", ["+", "-", "*", "* Escalar"])
        with col3:
            if operacion == "* Escalar":
                escalar_str = st.text_input("Ingrese Escalar (Ej: 2, x, 1/2):", value="1")
            else:
                mat_B_nombre = st.selectbox("Matriz B", list(st.session_state.mis_matrices.keys()), key="op_matB")

        if st.button("Calcular Resultado", key="btn_basicas"):
            matA = st.session_state.mis_matrices[mat_A_nombre]

            if operacion == "* Escalar":
                try:
                    esc = sp.sympify(escalar_str)
                    res = sp.simplify(esc * matA)
                    st.success("Resultado:")
                    imprimir_matriz_simbolica(res)
                except Exception:
                    st.error("Escalar inválido.")
            else:
                matB = st.session_state.mis_matrices[mat_B_nombre]

                if operacion in ["+", "-"] and matA.shape != matB.shape:
                    st.error("Error: Las matrices deben tener la misma dimensión.")
                elif operacion == "*" and matA.shape[1] != matB.shape[0]:
                    st.error("Error: Las dimensiones no son compatibles para multiplicar.")
                else:
                    if operacion == "+":
                        res = sp.simplify(matA + matB)
                    elif operacion == "-":
                        res = sp.simplify(matA - matB)
                    elif operacion == "*":
                        res = sp.simplify(matA * matB)

                    st.success("Resultado:")
                    imprimir_matriz_simbolica(res)

                    # Interfaz para guardar el resultado dinámicamente
                    # (Nota: En Streamlit puro, guardar desde un botón anidado requiere
                    # trucos con session_state, por lo que aquí solo mostramos el resultado
                    # para mantener el código limpio en esta iteración).

    # --------------------------------------------------------------------------
    # PESTAÑA 2: Propiedades y Reducción Gaussiana
    # --------------------------------------------------------------------------
    with tab_propiedades:
        mat_sel_nombre = st.selectbox("Seleccione Matriz a analizar:", list(st.session_state.mis_matrices.keys()),
                                      key="prop_mat")
        M = st.session_state.mis_matrices[mat_sel_nombre]

        prop_elegida = st.radio("Análisis:", [
            "Determinante", "Inversa", "Transpuesta / Adjunta",
            "Rango y Subespacios", "Matriz Reducida (RREF)"
        ], horizontal=True)

        if st.button("Analizar", key="btn_prop"):
            if prop_elegida == "Determinante":
                if M.is_square:
                    st.success(f"**Determinante:** {sp.simplify(M.det())}")
                else:
                    st.error("La matriz debe ser cuadrada.")

            elif prop_elegida == "Inversa":
                if M.is_square:
                    try:
                        st.write("Matriz Inversa ($A^{-1}$):")
                        imprimir_matriz_simbolica(sp.simplify(M.inv()))
                    except Exception:
                        st.error("La matriz es singular (Determinante = 0).")
                else:
                    st.error("La matriz debe ser cuadrada.")

            elif prop_elegida == "Transpuesta / Adjunta":
                st.write("Matriz Adjunta ($A^*$):")
                if not M.has(sp.I):
                    st.info("La matriz no contiene complejos, por lo que la Adjunta es igual a la Transpuesta.")
                imprimir_matriz_simbolica(M.H)

            elif prop_elegida == "Rango y Subespacios":
                rref_sp, pivotes = M.rref()
                st.write(f"**Rango de la matriz:** {M.rank()}")

                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    st.write("**Base del Espacio Renglón $L_r(A)$:**")
                    renglones = [rref_sp.row(i) for i in range(rref_sp.rows) if
                                 rref_sp.row(i) != sp.zeros(1, rref_sp.cols)]
                    if renglones:
                        imprimir_matriz_simbolica(sp.Matrix(renglones))
                    else:
                        st.write("Trivial (Matriz nula)")

                with col_sub2:
                    st.write("**Base del Espacio Columna $L_c(A)$:**")
                    columnas = [M.col(j) for j in pivotes]
                    if columnas:
                        imprimir_matriz_simbolica(sp.Matrix.hstack(*columnas))
                    else:
                        st.write("Trivial (Matriz nula)")

                st.divider()
                st.write("**Base del Kernel (Espacio Nulo):**")
                base_kernel = M.nullspace()
                if base_kernel:
                    for i, vec in enumerate(base_kernel):
                        imprimir_matriz_simbolica(vec)
                    st.write(f"**Nulidad:** {len(base_kernel)}")
                else:
                    st.write("El Kernel es trivial (vector cero).")

            elif prop_elegida == "Matriz Reducida (RREF)":
                rref_sp, pivotes = M.rref()
                st.write("Forma Escalonada Reducida por Renglones:")
                imprimir_matriz_simbolica(rref_sp)
                st.info(f"Pivotes encontrados en las columnas: {pivotes}")

    # --------------------------------------------------------------------------
    # PESTAÑA 3: Cálculo Multivariable (Hessiana / Jacobiana)
    # --------------------------------------------------------------------------
    with tab_avanzadas:
        st.subheader("Cálculo Diferencial Matricial")

        # Hessiana
        st.markdown("**1. Matriz Hessiana** (Para una función escalar)")
        expr_str = st.text_input("Ingrese la función escalar $f$ (Ej: 2*x**2 + 12*x*y):")

        if st.button("Calcular Hessiana"):
            try:
                f = sp.sympify(expr_str)
                vars_list = list(f.free_symbols)
                if not vars_list:
                    st.error("La función es constante.")
                else:
                    vars_list.sort(key=lambda v: v.name)
                    H = sp.hessian(f, vars_list)
                    st.success(f"Función detectada: $f({', '.join([v.name for v in vars_list])})$")
                    imprimir_matriz_simbolica(H)
            except Exception:
                st.error("Error matemático o de sintaxis.")

        st.divider()

        # Jacobiana
        st.markdown("**2. Matriz Jacobiana** (A partir de un vector o matriz)")
        mat_jac_nombre = st.selectbox("Seleccione Matriz/Vector base:", list(st.session_state.mis_matrices.keys()), key="jac_mat")
        
        if st.button("Calcular Jacobiana"):
            M_jac = st.session_state.mis_matrices[mat_jac_nombre]
            variables = list(M_jac.free_symbols)
            if not variables:
                st.error("La matriz seleccionada no contiene variables simbólicas.")
            else:
                variables.sort(key=lambda v: v.name)
                try:
                    J = M_jac.jacobian(variables)
                    st.success(f"Jacobiana evaluada respecto a: {variables}")
                    imprimir_matriz_simbolica(J)
                except TypeError:
                     st.error(f"Error Matemático: La matriz Jacobiana está definida para vectores columna o fila. La matriz que elegiste tiene dimensión {M_jac.shape[0]}x{M_jac.shape[1]}.")
                except AttributeError:
                     st.error("Error: Ocurrió un problema con el formato de la matriz.")
                    
    # --------------------------------------------------------------------------
    # PESTAÑA 4: Análisis Espectral
    # --------------------------------------------------------------------------
    with tab_espectral:
        st.subheader("Valores y Vectores Propios")
        mat_esp_nombre = st.selectbox("Seleccione Matriz:", list(st.session_state.mis_matrices.keys()), key="esp_mat")

        if st.button("Ejecutar Análisis Espectral"):
            A = st.session_state.mis_matrices[mat_esp_nombre]

            if not A.is_square:
                st.error("El análisis espectral requiere una matriz cuadrada.")
            else:
                lamda = sp.Symbol('lambda')
                polinomio = A.charpoly(lamda)

                st.write("**1. Polinomio Característico**")
                st.latex(f"p(\lambda) = \det(A - \lambda I) = {sp.latex(polinomio.as_expr())}")

                vectores_propios = A.eigenvects()
                try:
                    vectores_propios.sort(key=lambda x: sp.re(x[0]), reverse=True)
                except Exception:
                    pass

                st.divider()
                st.write("**2. Espectro y Bases**")

                columnas_P, valores_D = [], []

                for val, mult_alg, vects in vectores_propios:
                    st.markdown(f"### $\lambda = {sp.latex(val)}$")
                    st.write(f"Multiplicidad Algebraica: {mult_alg} | Multiplicidad Geométrica: {len(vects)}")

                    for i, v in enumerate(vects):
                        denominadores = [sp.fraction(sp.simplify(e))[1] for e in v]
                        mcm = 1
                        for d in denominadores: mcm = sp.lcm(mcm, d)
                        v_entero = sp.simplify(v * mcm)

                        for e in v_entero:
                            if e != 0:
                                if e < 0: v_entero = v_entero * -1
                                break

                        columnas_P.append(v_entero)
                        valores_D.append(val)

                        st.latex(f"v_{{{i + 1}}} = {sp.latex(v_entero)}")

                st.divider()
                st.write("**3. Diagonalización**")
                if A.is_diagonalizable():
                    st.success("La matriz **SÍ** es diagonalizable.")
                    P = sp.Matrix.hstack(*columnas_P)
                    D = sp.diag(*valores_D)
                    P_inv = sp.simplify(P.inv())

                    col_p, col_d, col_pinv = st.columns(3)
                    with col_p:
                        st.write("Matriz de Paso ($P$)")
                        imprimir_matriz_simbolica(P)
                    with col_d:
                        st.write("Matriz Diagonal ($D$)")
                        imprimir_matriz_simbolica(D)
                    with col_pinv:
                        st.write("Inversa ($P^{-1}$)")
                        imprimir_matriz_simbolica(P_inv)
                else:
                    st.error("La matriz **NO** es diagonalizable (no hay suficientes vectores propios independientes).")
