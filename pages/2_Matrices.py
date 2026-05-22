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
if 'mis_transformaciones' not in st.session_state:
    st.session_state.mis_transformaciones = {}

st.title("🧮 Álgebra Lineal: Matrices")

# ==============================================================================
# PANEL LATERAL (INVENTARIO Y PUENTES)
# ==============================================================================
with st.sidebar:
    st.header("Inventario de Matrices")
    
    if st.session_state.mis_matrices:
        for nombre, mat in st.session_state.mis_matrices.items():
            st.write(f"**{nombre}**:")
            imprimir_matriz_simbolica(mat)
    else:
        st.info("No hay matrices en memoria.")
        
    st.divider()
    
    st.subheader("Nueva Matriz Manual")
    nombre_nueva = st.text_input("Asignar nombre (Ej: A, M1):").upper().strip()
    
    if nombre_nueva:
        if nombre_nueva in st.session_state.mis_matrices:
            st.warning("Ese nombre ya existe. Se sobreescribirá.")
            
        matriz_creada = Crear_Matriz_Simbolica_UI(nombre_nueva)
        
        if matriz_creada is not None:
            st.session_state.mis_matrices[nombre_nueva] = matriz_creada
            st.success(f"Matriz {nombre_nueva} guardada.")
            st.rerun() 
            
    st.divider()

    # --- PUENTE DE IMPORTACIÓN ---
    st.subheader("Importar a Matrices")
    fuente_import = st.selectbox("¿De dónde desea importar?", ["Seleccione...", "De una Transformación Activa", "De un Conjunto de Vectores"])
    
    if fuente_import == "De una Transformación Activa":
        if st.session_state.get('mis_transformaciones'):
            tl_import = st.selectbox("Seleccione la T.L.:", list(st.session_state.mis_transformaciones.keys()), key="imp_tl")
            nom_mat_tl = st.text_input("Guardar matriz asociada como (Ej. M_T1):").upper().strip()
            
            if st.button("⬇️ Importar Matriz Asociada"):
                if nom_mat_tl:
                    st.session_state.mis_matrices[nom_mat_tl] = st.session_state.mis_transformaciones[tl_import]["matriz_asociada"]
                    st.success(f"Matriz '{nom_mat_tl}' importada con éxito.")
                    st.rerun()
                else:
                    st.error("Ingrese un nombre para guardar la matriz.")
        else:
            st.info("No hay transformaciones definidas en memoria.")
            
    elif fuente_import == "De un Conjunto de Vectores":
        if st.session_state.get('mis_vectores'):
            vecs_import = st.multiselect("Seleccione vectores para formar las columnas:", list(st.session_state.mis_vectores.keys()), key="imp_vecs")
            nom_mat_vec = st.text_input("Guardar matriz generada como (Ej. BASE1):").upper().strip()
            
            if st.button("⬇️ Construir e Importar Matriz"):
                if not vecs_import:
                    st.error("Debe seleccionar al menos un vector.")
                elif not nom_mat_vec:
                    st.error("Ingrese un nombre para guardar la matriz.")
                else:
                    try:
                        # Une los vectores elegidos como columnas de una sola matriz
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
    
    # --- PUENTE DE EXPORTACIÓN A T.L. ---
    st.subheader("Exportar a Transformación")
    if st.session_state.mis_matrices:
        mat_export = st.selectbox("Matriz a exportar:", list(st.session_state.mis_matrices.keys()), key="exp_mat_tl")
        nombre_tl = st.text_input("Nombre de la nueva T.L. (Ej. T1):").upper().strip()
        
        if st.button("Crear Transformación"):
            if nombre_tl:
                A_export = st.session_state.mis_matrices[mat_export]
                filas, columnas = A_export.shape
                vars_input = sp.symbols(f'x1:{columnas+1}')
                regla_correspondencia = A_export * sp.Matrix(vars_input)
                
                st.session_state.mis_transformaciones[nombre_tl] = {
                    "matriz_asociada": A_export,
                    "regla": regla_correspondencia,
                    "variables": vars_input,
                    "dim_V": columnas,
                    "dim_W": filas,
                    "base_dominio": sp.eye(columnas),
                    "base_codominio": sp.eye(filas)
                }
                st.success(f"T.L. '{nombre_tl}' creada exitosamente en el otro módulo.")
            else:
                st.error("Ingrese un nombre para la T.L.")
                
    st.divider()
    if st.button("🗑️ Borrar todas las matrices"):
        st.session_state.mis_matrices.clear()
        if 'temp_matriz' in st.session_state:
            del st.session_state.temp_matriz
        st.rerun()

# ==============================================================================
# ÁREA PRINCIPAL (OPERACIONES MATEMÁTICAS)
# ==============================================================================
if not st.session_state.mis_matrices:
    st.info("👈 Comience creando una matriz en el panel lateral.")
else:
    tab_basicas, tab_propiedades, tab_avanzadas, tab_espectral = st.tabs([
        "Operaciones Básicas", "Propiedades y Reducción", "Cálculo Multivariable", "Análisis Espectral"
    ])
    
    # --------------------------------------------------------------------------
    # PESTAÑA 1: Operaciones Básicas
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
            res = None
            
            if operacion == "* Escalar":
                try:
                    esc = sp.sympify(escalar_str)
                    res = sp.simplify(esc * matA)
                except Exception:
                    st.error("Escalar inválido.")
            else:
                matB = st.session_state.mis_matrices[mat_B_nombre]
                if operacion in ["+", "-"] and matA.shape != matB.shape:
                    st.error("Error: Las matrices deben tener la misma dimensión.")
                elif operacion == "*" and matA.shape[1] != matB.shape[0]:
                    st.error("Error: Las dimensiones no son compatibles para multiplicar.")
                else:
                    if operacion == "+": res = sp.simplify(matA + matB)
                    elif operacion == "-": res = sp.simplify(matA - matB)
                    elif operacion == "*": res = sp.simplify(matA * matB)
            
            if res is not None:
                st.session_state.temp_matriz = res # Guardamos en la memoria temporal

        # Bloque de guardado persistente (Aparece si hay un resultado congelado)
        if 'temp_matriz' in st.session_state:
            st.success("Resultado de la operación:")
            imprimir_matriz_simbolica(st.session_state.temp_matriz)
            
            col_save1, col_save2 = st.columns([2, 1])
            with col_save1:
                nombre_save = st.text_input("Guardar este resultado como (Ej. R1):").upper().strip()
            with col_save2:
                st.write("") # Espaciador
                if st.button("💾 Guardar Matriz", key="save_basicas"):
                    if nombre_save:
                        st.session_state.mis_matrices[nombre_save] = st.session_state.temp_matriz
                        del st.session_state.temp_matriz # Limpiamos la memoria temporal
                        st.rerun()
                    else:
                        st.error("Ingrese un nombre.")

    # --------------------------------------------------------------------------
    # PESTAÑA 2: Propiedades y Reducción Gaussiana
    # --------------------------------------------------------------------------
    with tab_propiedades:
        mat_sel_nombre = st.selectbox("Seleccione Matriz a analizar:", list(st.session_state.mis_matrices.keys()), key="prop_mat")
        M = st.session_state.mis_matrices[mat_sel_nombre]
        
        prop_elegida = st.radio("Análisis:", [
            "Determinante", "Traza", "Inversa", "Adjunta Clásica", "Transpuesta Conjugada", 
            "Rango y Subespacios", "Matriz Reducida (RREF)"
        ], horizontal=True)
        
        if st.button("Analizar", key="btn_prop"):
            res_matriz = None # Variable para atrapar matrices que se puedan guardar
            
            if prop_elegida == "Determinante":
                if M.is_square: st.success(f"**Determinante:** {sp.simplify(M.det())}")
                else: st.error("La matriz debe ser cuadrada.")
            
            elif prop_elegida == "Traza":
                if M.is_square: st.success(f"**Traza:** {sp.simplify(M.trace())}")
                else: st.error("La matriz debe ser cuadrada.")
                    
            elif prop_elegida == "Inversa":
                if M.is_square:
                    try:
                        res_matriz = sp.simplify(M.inv())
                        st.write("Matriz Inversa ($A^{-1}$):")
                    except Exception:
                        st.error("La matriz es singular (Determinante = 0).")
                else: st.error("La matriz debe ser cuadrada.")
            
            elif prop_elegida == "Adjunta Clásica":
                if M.is_square:
                    res_matriz = sp.simplify(M.adjugate())
                    st.write("Matriz Adjunta Clásica (Matriz de Cofactores Transpuesta):")
                else: st.error("La matriz debe ser cuadrada.")
                    
            elif prop_elegida == "Transpuesta Conjugada":
                res_matriz = M.H
                st.write("Matriz Transpuesta Conjugada ($A^*$ o $A^H$):")
                if not M.has(sp.I):
                    st.info("No contiene complejos; la Transpuesta Conjugada es igual a la Transpuesta normal.")
                
            elif prop_elegida == "Matriz Reducida (RREF)":
                rref_sp, pivotes = M.rref()
                res_matriz = rref_sp
                st.write("Forma Escalonada Reducida por Renglones:")
                st.info(f"Pivotes encontrados en las columnas: {pivotes}")
                
            elif prop_elegida == "Rango y Subespacios":
                rref_sp, pivotes = M.rref()
                st.write(f"**Rango de la matriz:** {M.rank()}")
                
                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    st.write("**Base del Espacio Renglón $L_r(A)$:**")
                    renglones = [rref_sp.row(i) for i in range(rref_sp.rows) if rref_sp.row(i) != sp.zeros(1, rref_sp.cols)]
                    if renglones: imprimir_matriz_simbolica(sp.Matrix(renglones))
                    else: st.write("Trivial")
                    
                with col_sub2:
                    st.write("**Base del Espacio Columna $L_c(A)$:**")
                    columnas = [M.col(j) for j in pivotes]
                    if columnas: imprimir_matriz_simbolica(sp.Matrix.hstack(*columnas))
                    else: st.write("Trivial")
                    
                st.divider()
                st.write("**Base del Kernel (Espacio Nulo):**")
                base_kernel = M.nullspace()
                if base_kernel:
                    for i, vec in enumerate(base_kernel): imprimir_matriz_simbolica(vec)
                    st.write(f"**Nulidad:** {len(base_kernel)}")
                else:
                    st.write("El Kernel es trivial (vector cero).")

            if res_matriz is not None:
                st.session_state.temp_prop_matriz = res_matriz

        # Bloque de guardado para propiedades que devuelven matrices (Inversa, Transpuesta, etc.)
        if 'temp_prop_matriz' in st.session_state:
            imprimir_matriz_simbolica(st.session_state.temp_prop_matriz)
            c1, c2 = st.columns([2, 1])
            with c1:
                nombre_save = st.text_input("Guardar esta matriz como:", key="name_prop").upper().strip()
            with c2:
                st.write("")
                if st.button("💾 Guardar", key="save_prop"):
                    if nombre_save:
                        st.session_state.mis_matrices[nombre_save] = st.session_state.temp_prop_matriz
                        del st.session_state.temp_prop_matriz
                        st.rerun()
                    else:
                        st.error("Ingrese un nombre.")

    # --------------------------------------------------------------------------
    # PESTAÑA 3: Cálculo Multivariable (Hessiana / Jacobiana)
    # --------------------------------------------------------------------------
    with tab_avanzadas:
        st.subheader("Cálculo Diferencial Matricial")
        
        st.markdown("**1. Matriz Hessiana**")
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
                    st.session_state.temp_avanzada = H
            except Exception:
                st.error("Error matemático o de sintaxis.")
                
        st.divider()
        
        st.markdown("**2. Matriz Jacobiana**")
        mat_jac_nombre = st.selectbox("Seleccione Vector base:", list(st.session_state.mis_matrices.keys()), key="jac_mat")
        
        if st.button("Calcular Jacobiana"):
            M_jac = st.session_state.mis_matrices[mat_jac_nombre]
            variables = list(M_jac.free_symbols)
            if not variables:
                st.error("La matriz no contiene variables simbólicas.")
            else:
                variables.sort(key=lambda v: v.name)
                try:
                    J = M_jac.jacobian(variables)
                    st.success(f"Jacobiana evaluada respecto a: {variables}")
                    st.session_state.temp_avanzada = J
                except TypeError:
                     st.error(f"Error Matemático: La Jacobiana está definida para vectores. Su matriz es de {M_jac.shape[0]}x{M_jac.shape[1]}.")
                except AttributeError:
                     st.error("Error de formato en SymPy.")

        if 'temp_avanzada' in st.session_state:
            imprimir_matriz_simbolica(st.session_state.temp_avanzada)
            c1, c2 = st.columns([2,1])
            with c1: nom_av = st.text_input("Guardar matriz como:", key="name_av").upper().strip()
            with c2:
                st.write("")
                if st.button("💾 Guardar", key="save_av"):
                    if nom_av:
                        st.session_state.mis_matrices[nom_av] = st.session_state.temp_avanzada
                        del st.session_state.temp_avanzada
                        st.rerun()

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
                                if e.is_real and e < 0: 
                                    v_entero = v_entero * -1
                                break
                                
                        columnas_P.append(v_entero)
                        valores_D.append(val)
                        st.latex(f"v_{{{i+1}}} = {sp.latex(v_entero)}")
                        
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
