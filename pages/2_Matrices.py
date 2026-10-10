import streamlit as st
import sympy as sp
import numpy as np

try:
    from utils import Crear_Matriz_Simbolica_UI, imprimir_matriz_simbolica, calcular_con_limite, evaluar_numerico, leer_expresion_st
except ImportError:
    st.error("Error al cargar utils.py. Asegúrese de ejecutar la aplicación correctamente.")

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Álgebra Lineal: Matrices - MATHESIS", page_icon="🧮", layout="wide")

# ==============================================================================
# INYECCIÓN DIRECTA DE CSS (FORMATO AZUL INSTITUCIONAL + MENÚ VISIBLE)
# ==============================================================================
st.markdown("""
    <style>
    /* 1. ASEGURAR QUE EL MENÚ PRINCIPAL DE TRES PUNTOS SEA VISIBLE */
    #MainMenu {
        visibility: visible !important;
    }

    footer {
        visibility: hidden;
    }

    .block-container {
        padding-top: 1.5rem;
    }

    /* 2. REESCRIBIR VARIABLES GLOBALES DE ROJO A AZUL */
    :root, html, body, [data-testid="stAppViewContainer"] {
        --primary-color: #0284c7 !important;
        --stConfig-primaryColor: #0284c7 !important;
    }

    /* 3. BANNER / CONTENEDOR DEL TÍTULO PRINCIPAL */
    .title-container {
        padding: 1.2rem 1.5rem;
        border-radius: 16px;
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.18) 0%, rgba(79, 70, 229, 0.18) 100%);
        border: 1px solid rgba(56, 189, 248, 0.35);
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(2, 132, 199, 0.12);
    }
    
    .title-text {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0284c7 0%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }

    /* 4. ESTILOS Y COLORES DE PESTAÑAS (ST.TABS) */
    [data-baseweb="tab-highlight"],
    [data-baseweb="tab-border"] {
        background-color: #38bdf8 !important;
    }

    button[data-baseweb="tab"] {
        border-radius: 10px 10px 0px 0px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        color: #94a3b8 !important;
        background-color: transparent !important;
        border: none !important;
        transition: all 0.25s ease-in-out !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom-color: #38bdf8 !important;
        background: rgba(2, 132, 199, 0.15) !important;
    }

    button[data-baseweb="tab"] p, 
    button[data-baseweb="tab"] span {
        font-size: 15px !important;
        font-weight: 700 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span {
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }

    /* 5. BARRA LATERAL (SIDEBAR) Y CONTENEDORES DE TARJETAS */
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(2, 132, 199, 0.2) !important;
    }

    [data-testid="stSidebarNav"] ul li div a[aria-current="page"] {
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.25) 0%, rgba(79, 70, 229, 0.25) 100%) !important;
        border: 1px solid #38bdf8 !important;
    }

    [data-testid="stSidebarNav"] ul li div a[aria-current="page"] span {
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        border: 1px solid rgba(2, 132, 199, 0.25) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Inicialización de estados de sesión
if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}
if 'mis_transformaciones' not in st.session_state:
    st.session_state.mis_transformaciones = {}
if 'mis_vectores' not in st.session_state:
    st.session_state.mis_vectores = {}

# ==============================================================================
# ENCABEZADO CON BANNER ESTILIZADO
# ==============================================================================
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">🧮 Álgebra Lineal: Matrices</h1>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# BARRA LATERAL (INVENTARIO LIMPIO Y EXPANDIBLE)
# ==============================================================================
with st.sidebar:
    st.header("📦 Inventario de Matrices")
    
    if st.session_state.mis_matrices:
        for nombre, mat in st.session_state.mis_matrices.items():
            with st.expander(f"Matriz: {nombre}"):
                imprimir_matriz_simbolica(mat)
    else:
        st.info("No hay matrices en memoria.")
        
    st.divider()
    if st.button("🗑️ Borrar todas las matrices", use_container_width=True):
        st.session_state.mis_matrices.clear()
        if 'temp_matriz' in st.session_state:
            st.session_state.pop("temp_matriz", None)
        if 'temp_prop_matriz' in st.session_state:
            st.session_state.pop("temp_prop_matriz", None)
        if 'temp_avanzada' in st.session_state:
            st.session_state.pop("temp_avanzada", None)
        st.rerun()

# ==============================================================================
# ÁREA PRINCIPAL (PESTAÑAS INTERACTIVAS)
# ==============================================================================
tab_gestion, tab_basicas, tab_propiedades, tab_avanzadas, tab_espectral = st.tabs([
    "📥 Gestión y Creación", 
    "Operaciones Básicas", 
    "Propiedades y Reducción", 
    "Cálculo Multivariable", 
    "Análisis Espectral"
])

# --------------------------------------------------------------------------
# PESTAÑA 0: Constructor, Creación Manual y Puentes
# --------------------------------------------------------------------------
with tab_gestion:
    st.subheader("Constructor y Puentes de Datos")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        with st.container(border=True):
            st.markdown("### ➕ Nueva Matriz Manual")
            
            # Entrada de Nombre y Dimensiones
            nombre_nueva = st.text_input("Asignar nombre de la matriz (Ej: A, M1):", key="input_nom_manual").upper().strip()
            
            col_m, col_n = st.columns(2)
            with col_m:
                filas = st.number_input("Número de filas:", min_value=1, max_value=10, value=2, step=1, key="num_filas_mat")
            with col_n:
                columnas = st.number_input("Número de columnas:", min_value=1, max_value=10, value=2, step=1, key="num_cols_mat")
                
            st.divider()
            
            st.markdown("#### Componentes de la Matriz")
            
            matriz_elementos = []
            error_sintaxis = False
            
            # Generación de la cuadrícula interactiva celda por celda (a_ij)
            for i in range(filas):
                cols = st.columns(columnas)
                fila_vals = []
                for j in range(columnas):
                    with cols[j]:
                        val_str = st.text_input(
                            f"Elemento ({i+1}, {j+1}):", 
                            value="0", 
                            key=f"celda_{i}_{j}_{filas}_{columnas}"
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
                
                # Vista previa previa al guardado
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
            st.markdown("### 🔀 Importación y Exportación")
            fuente_import = st.selectbox("¿De dónde desea importar?", ["Seleccione...", "De una Transformación Activa", "De un Conjunto de Vectores"])
            
            if fuente_import == "De una Transformación Activa":
                if st.session_state.get('mis_transformaciones'):
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
                if st.session_state.get('mis_vectores'):
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
            st.markdown("### 📤 Exportar a Transformación")
            if st.session_state.mis_matrices:
                mat_export = st.selectbox("Matriz a exportar:", list(st.session_state.mis_matrices.keys()), key="exp_mat_tl_main")
                nombre_tl = st.text_input("Nombre de la nueva T.L. (Ej. T1):", key="nombre_tl_main").upper().strip()
                
                if st.button("Crear Transformación", key="btn_crear_tl_main", use_container_width=True):
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
                        st.success(f"T.L. '{nombre_tl}' creada exitosamente en el módulo de Transformaciones.")
                    else:
                        st.error("Ingrese un nombre para la T.L.")

# --------------------------------------------------------------------------
# PESTAÑA 1: Operaciones Básicas
# --------------------------------------------------------------------------
with tab_basicas:
    if not st.session_state.mis_matrices:
        st.info("👈 Comience creando o importando una matriz en la pestaña 'Gestión y Creación'.")
    else:
        with st.container(border=True):
            st.subheader("Operaciones Álgebraicas Básicas")
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
                        esc = leer_expresion_st(escalar_str)
                        if esc is not None:
                            res = esc * matA
                        else:
                            st.error("Escalar inválido.")
                    except Exception:
                        st.error("Escalar inválido.")
                else:
                    matB = st.session_state.mis_matrices[mat_B_nombre]
                    if operacion in ["+", "-"] and matA.shape != matB.shape:
                        st.error("Error: Las matrices deben tener la misma dimensión.")
                    elif operacion == "*" and matA.shape[1] != matB.shape[0]:
                        st.error("Error: Las dimensiones no son compatibles para multiplicar.")
                    else:
                        if operacion == "+": res = matA + matB
                        elif operacion == "-": res = matA - matB
                        elif operacion == "*": res = matA * matB
                
                if res is not None:
                    st.session_state.temp_matriz = res

            if 'temp_matriz' in st.session_state:
                st.success("Resultado de la operación:")
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
            st.subheader("Análisis Estructural y Reducción Gaussiana")
            mat_sel_nombre = st.selectbox("Seleccione Matriz a analizar:", list(st.session_state.mis_matrices.keys()), key="prop_mat")
            M = st.session_state.mis_matrices[mat_sel_nombre]
            
            prop_elegida = st.radio("Propiedad a evaluar:", [
                "Determinante", "Traza", "Inversa", "Adjunta Clásica", "Transpuesta Conjugada", 
                "Rango y Subespacios", "Matriz Reducida (RREF)"
            ], horizontal=True)
            
            if st.button("Analizar Propiedad", key="btn_prop"):
                res_matriz = None 
                
                if prop_elegida == "Determinante":
                    if M.is_square: 
                        try:
                            det_val = calcular_con_limite(M.det, timeout=5)
                            st.success(f"**Determinante:** {det_val}")
                        except TimeoutError as e:
                            st.error(str(e))
                    else: st.error("La matriz debe ser cuadrada.")
                
                elif prop_elegida == "Traza":
                    if M.is_square: st.success(f"**Traza:** {M.trace()}")
                    else: st.error("La matriz debe ser cuadrada.")
                        
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
                            st.error("La matriz es singular (Determinante = 0) o no se puede invertir numéricamente.")
                    else: st.error("La matriz debe ser cuadrada.")
                        
                elif prop_elegida == "Adjunta Clásica":
                    if M.is_square:
                        try:
                            res_matriz = calcular_con_limite(M.adjugate, timeout=5)
                            st.write("Matriz Adjunta Clásica (Matriz de Cofactores Transpuesta):")
                        except TimeoutError as e:
                            st.error(str(e))
                    else: st.error("La matriz debe ser cuadrada.")
                        
                elif prop_elegida == "Transpuesta Conjugada":
                    res_matriz = M.H
                    st.write("Matriz Transpuesta Conjugada ($A^*$ o $A^H$):")
                    if not M.has(sp.I):
                        st.info("No contiene complejos; la Transpuesta Conjugada es igual a la Transpuesta normal.")
                    
                elif prop_elegida == "Matriz Reducida (RREF)":
                    try:
                        rref_sp, pivotes = calcular_con_limite(M.rref, timeout=5)
                        res_matriz = rref_sp
                        st.write("Forma Escalonada Reducida por Renglones:")
                        st.info(f"Pivotes encontrados en las columnas: {pivotes}")
                    except TimeoutError as e:
                        st.error(str(e))
                    
                elif prop_elegida == "Rango y Subespacios":
                    try:
                        rref_sp, pivotes = calcular_con_limite(M.rref, timeout=5)
                        st.success(f"**Rango de la matriz:** {len(pivotes)}")
                        
                        col_sub1, col_sub2 = st.columns(2)
                        with col_sub1:
                            st.write("**Base del Espacio Renglón ($L_r(A)$):**")
                            renglones = [rref_sp.row(i) for i in range(rref_sp.rows) if rref_sp.row(i) != sp.zeros(1, rref_sp.cols)]
                            if renglones: imprimir_matriz_simbolica(sp.Matrix(renglones))
                            else: st.write("Trivial")
                            
                        with col_sub2:
                            st.write("**Base del Espacio Columna ($L_c(A)$):**")
                            columnas = [M.col(j) for j in pivotes]
                            if columnas: imprimir_matriz_simbolica(sp.Matrix.hstack(*columnas))
                            else: st.write("Trivial")
                            
                        st.divider()
                        st.write("**Base del Kernel (Espacio Nulo):**")
                        base_kernel = calcular_con_limite(M.nullspace, timeout=5)
                        if base_kernel:
                            for i, vec in enumerate(base_kernel): imprimir_matriz_simbolica(vec)
                            st.write(f"**Nulidad:** {len(base_kernel)}")
                        else:
                            st.write("El Kernel es trivial (vector cero).")
                    except TimeoutError as e:
                        st.error(str(e))

                if res_matriz is not None:
                    st.session_state.temp_prop_matriz = res_matriz

            if 'temp_prop_matriz' in st.session_state:
                imprimir_matriz_simbolica(st.session_state.temp_prop_matriz)
                c1, c2 = st.columns([2, 1])
                with c1:
                    nombre_save = st.text_input("Guardar esta matriz como:", key="name_prop").upper().strip()
                with c2:
                    st.write("")
                    if st.button("💾 Guardar", key="save_prop", use_container_width=True):
                        if nombre_save:
                            st.session_state.mis_matrices[nombre_save] = st.session_state.temp_prop_matriz
                            st.session_state.pop("temp_prop_matriz", None)
                            st.rerun()
                        else:
                            st.error("Ingrese un nombre.")

# --------------------------------------------------------------------------
# PESTAÑA 3: Cálculo Multivariable (Hessiana / Jacobiana)
# --------------------------------------------------------------------------
with tab_avanzadas:
    if not st.session_state.mis_matrices:
        st.info("👈 Comience creando o importando una matriz en la pestaña 'Gestión y Creación'.")
    else:
        with st.container(border=True):
            st.subheader("Cálculo Diferencial Matricial")
            
            st.markdown("#### 1. Matriz Hessiana")
            expr_str = st.text_input("Ingrese la función escalar $f$ (Ej: 2*x**2 + 12*x*y):")
            
            if st.button("Calcular Hessiana"):
                try:
                    f = leer_expresion_st(expr_str)
                    if f is not None:
                        vars_list = list(f.free_symbols)
                        if not vars_list:
                            st.error("La función es constante.")
                        else:
                            vars_list.sort(key=lambda v: v.name)
                            H = calcular_con_limite(sp.hessian, args=(f, vars_list), timeout=5)
                            st.success(f"Función detectada: $f({', '.join([v.name for v in vars_list])})$")
                            st.session_state.temp_avanzada = H
                except TimeoutError as e:
                    st.error(str(e))
                except Exception:
                    st.error("Error matemático o de sintaxis.")
                    
            st.divider()
            
            st.markdown("#### 2. Matriz Jacobiana")
            mat_jac_nombre = st.selectbox("Seleccione Vector base:", list(st.session_state.mis_matrices.keys()), key="jac_mat")
            
            if st.button("Calcular Jacobiana"):
                M_jac = st.session_state.mis_matrices[mat_jac_nombre]
                variables = list(M_jac.free_symbols)
                
                if not variables:
                    st.error("La matriz no contiene variables simbólicas.")
                elif M_jac.shape[0] != 1 and M_jac.shape[1] != 1:
                    st.error(f"Error Matemático: La Jacobiana está definida estrictamente para funciones vectoriales. La matriz mide {M_jac.shape[0]}x{M_jac.shape[1]}.")
                else:
                    variables.sort(key=lambda v: v.name)
                    try:
                        J = calcular_con_limite(M_jac.jacobian, args=(variables,), timeout=5)
                        st.success(f"Jacobiana evaluada respecto a: {variables}")
                        st.session_state.temp_avanzada = J
                    except TimeoutError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Error inesperado al procesar la Jacobiana: {e}")

            if 'temp_avanzada' in st.session_state:
                imprimir_matriz_simbolica(st.session_state.temp_avanzada)
                c1, c2 = st.columns([2, 1])
                with c1: nom_av = st.text_input("Guardar matriz como:", key="name_av").upper().strip()
                with c2:
                    st.write("")
                    if st.button("💾 Guardar", key="save_av", use_container_width=True):
                        if nom_av:
                            st.session_state.mis_matrices[nom_av] = st.session_state.temp_avanzada
                            st.session_state.pop("temp_avanzada", None)
                            st.rerun()

# --------------------------------------------------------------------------
# PESTAÑA 4: Análisis Espectral
# --------------------------------------------------------------------------
with tab_espectral:
    with st.container(border=True):
        st.subheader("Valores y Vectores Propios (Eigen-Análisis)")
        mat_esp_nombre = st.selectbox("Seleccione Matriz:", list(st.session_state.mis_matrices.keys()), key="esp_mat")
        
        if st.button("Ejecutar Análisis Espectral", use_container_width=True):
            A = st.session_state.mis_matrices[mat_esp_nombre]
            
            if not A.is_square:
                st.error("El análisis espectral requiere una matriz cuadrada.")
            else:
                try:
                    lamda = sp.Symbol('lambda')
                    polinomio = calcular_con_limite(A.charpoly, args=(lamda,), timeout=5)
                    
                    st.markdown("#### 1. Polinomio Característico")
                    st.latex(f"p(\\lambda) = \\det(A - \\lambda I) = {sp.latex(polinomio.as_expr())}")
                    
                    A_num = evaluar_numerico(A)
                    if A_num is not None and A.shape[0] >= 4:
                        st.info("💡 Matriz numérica grande detectada: Evaluando con motor NumPy para prevenir colapsos.")
                        w, v = np.linalg.eig(A_num)
                        
                        st.divider()
                        st.markdown("#### 2. Espectro y Bases (Aproximación Numérica)")
                        columnas_P = []

                        for i in range(len(w)):
                            val_propio = np.round(w[i], 4)
                            val_str = str(val_propio).replace('j', 'i').replace('(', '').replace(')', '')
                            
                            st.markdown(rf"##### $\lambda \approx {val_str}$")
                            vec_propio = sp.Matrix(np.round(v[:, i], 4))
                            columnas_P.append(vec_propio)
                            st.latex(rf"v_{{{i+1}}} = {sp.latex(vec_propio)}")
                        
                        st.divider()
                        st.markdown("#### 3. Diagonalización")
                        
                        rango_P = np.linalg.matrix_rank(v, tol=1e-5)
                        
                        if rango_P == A.shape[0]:
                            st.success("La matriz **SÍ** es diagonalizable (Aproximación Numérica).")
                            st.warning("⚠️ **Nota:** Estos resultados son aproximaciones de punto flotante. Debido al redondeo, $P \\cdot D \\cdot P^{-1}$ podría diferir ligeramente de $A$.")
                            
                            P = sp.Matrix.hstack(*columnas_P)
                            D = sp.diag(*[np.round(val, 4) for val in w])
                            
                            try:
                                P_inv = sp.Matrix(np.round(np.linalg.inv(v), 4))
                            except Exception:
                                P_inv = calcular_con_limite(P.inv, timeout=5)
                            
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
                            st.error(f"La matriz **NO** es diagonalizable numéricamente. La matriz de vectores propios es defectuosa (Rango numérico de P es {rango_P} de {A.shape[0]}).")
                            
                    else:
                        vectores_propios = calcular_con_limite(A.eigenvects, timeout=8)
                        
                        try:
                            vectores_propios.sort(key=lambda x: sp.re(x[0]), reverse=True)
                        except Exception:
                            pass
                        
                        st.divider()
                        st.markdown("#### 2. Espectro y Bases")
                        
                        columnas_P, valores_D = [], []
                        
                        for val, mult_alg, vects in vectores_propios:
                            st.markdown(f"##### $\\lambda = {sp.latex(val)}$")
                            st.caption(f"Multiplicidad Algebraica: {mult_alg} | Multiplicidad Geométrica: {len(vects)}")
                            
                            for i, v in enumerate(vects):
                                try:
                                    denominadores = [sp.fraction(e)[1] for e in v]
                                    mcm = 1
                                    for d in denominadores: mcm = sp.lcm(mcm, d)
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
                                
                        st.divider()
                        st.markdown("#### 3. Diagonalización")
                        if len(columnas_P) == A.shape[0]:
                            st.success("La matriz **SÍ** es diagonalizable.")
                            P = sp.Matrix.hstack(*columnas_P)
                            D = sp.diag(*valores_D)
                            P_inv = calcular_con_limite(P.inv, timeout=5)
                            
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
                            
                except TimeoutError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error procesando el análisis espectral: {e}")
