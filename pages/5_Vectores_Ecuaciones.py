import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

try:
    from utils import imprimir_matriz_simbolica, leer_expresion_st
except ImportError:
    st.error("Error al cargar utils.py. Asegúrate de ejecutar la aplicación desde la raíz.")
    st.stop()

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Vectores y Sistemas - MATHESIS", page_icon="↗️", layout="wide")

if 'mis_vectores' not in st.session_state:
    st.session_state.mis_vectores = {}
if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}

# ==============================================================================
# INYECCIÓN DIRECTA DE CSS (ESTILOS UNIFICADOS, SUBTÍTULOS Y TARJETAS)
# ==============================================================================
st.markdown("""
    <style>
    /* 1. VISIBILIDAD DE MENÚ SUPERIOR */
    #MainMenu { visibility: visible !important; }
    footer { visibility: hidden; }
    .block-container { padding-top: 1.5rem; }

    /* 2. VARIABLES GLOBALES DE TEMA EN AZUL */
    :root, html, body, [data-testid="stAppViewContainer"] {
        --primary-color: #0284c7 !important;
        --stConfig-primaryColor: #0284c7 !important;
    }

    /* 3. BANNER PRINCIPAL */
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

    /* 4. ESTILIZADO GLOBAL PARA SUBTÍTULOS (H2, H3, ST.HEADER, ST.SUBHEADER) */
    .stMarkdown h2, [data-testid="stHeader"] h2 {
        color: #38bdf8 !important;
        font-size: 1.35rem !important;
        font-weight: 800 !important;
        border-bottom: 2px solid rgba(56, 189, 248, 0.3) !important;
        padding-bottom: 6px !important;
        margin-top: 1.2rem !important;
        margin-bottom: 1.0rem !important;
        letter-spacing: -0.3px !important;
    }

    .stMarkdown h3, [data-testid="stSubheader"] h3 {
        color: #38bdf8 !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        border-left: 4px solid #0284c7 !important;
        padding-left: 10px !important;
        margin-top: 1rem !important;
        margin-bottom: 0.8rem !important;
    }

    /* 5. CONTENEDORES NATIVOS AZULES (ELIMINA RECUADROS FANTASMA) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.35) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 15px rgba(2, 132, 199, 0.08) !important;
        margin-bottom: 1rem !important;
    }

    /* 6. TÍTULOS Y SUBTÍTULOS RESALTADOS DENTRO DE LAS TARJETAS */
    .card-header-title {
        background: linear-gradient(135deg, #0284c7 0%, #6366f1 100%);
        color: #ffffff !important;
        font-size: 17px;
        font-weight: 800;
        padding: 8px 16px;
        border-radius: 10px;
        display: inline-block;
        margin-bottom: 14px;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
    }

    .card-subheader-title {
        color: #38bdf8 !important;
        font-size: 15px;
        font-weight: 700;
        border-bottom: 2px solid rgba(56, 189, 248, 0.3);
        padding-bottom: 6px;
        margin-top: 10px;
        margin-bottom: 12px;
    }

    /* 7. DISEÑO MODERNO DE PESTAÑAS (ST.TABS) */
    [data-baseweb="tab-list"] {
        gap: 10px !important;
        background-color: rgba(2, 132, 199, 0.05) !important;
        padding: 8px 10px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        margin-bottom: 20px !important;
    }

    button[data-baseweb="tab"] {
        border-radius: 12px !important;
        padding: 10px 22px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        color: #94a3b8 !important;
        background-color: transparent !important;
        border: 1px solid transparent !important;
        transition: all 0.25s ease-in-out !important;
    }

    button[data-baseweb="tab"]:hover {
        color: #38bdf8 !important;
        background: rgba(2, 132, 199, 0.12) !important;
        border: 1px solid rgba(56, 189, 248, 0.25) !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
        background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%) !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35) !important;
        border: 1px solid #38bdf8 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* 8. ESTILOS DE BARRA LATERAL (SIDEBAR UNIFICADO) */
    [data-testid="stSidebar"], section[data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 320px !important;
        border-right: 1px solid rgba(2, 132, 199, 0.2) !important;
    }

    [data-testid="stSidebarNav"] ul li div a, [data-testid="stSidebarNav"] a {
        border-radius: 12px !important;
        padding: 10px 14px !important;
        margin: 4px 8px !important;
        border: 1px solid rgba(2, 132, 199, 0.18) !important;
        background-color: rgba(2, 132, 199, 0.03) !important;
        transition: all 0.25s ease-in-out !important;
        white-space: nowrap !important;
    }

    [data-testid="stSidebarNav"] ul li div a:hover, [data-testid="stSidebarNav"] a:hover {
        border-color: #0284c7 !important;
        background: rgba(2, 132, 199, 0.12) !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2) !important;
        transform: translateX(4px);
    }

    [data-testid="stSidebarNav"] ul li div a[aria-current="page"], [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.25) 0%, rgba(79, 70, 229, 0.25) 100%) !important;
        border: 1px solid #38bdf8 !important;
        box-shadow: 0 4px 14px rgba(56, 189, 248, 0.25) !important;
    }

    [data-testid="stSidebarNav"] ul li div a[aria-current="page"] span, [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# ENCABEZADO CON BANNER ESTILIZADO
# ==============================================================================
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">↗️ Vectores y Sistemas de Ecuaciones</h1>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# PANEL LATERAL (INVENTARIO LIMPIO DE VECTORES)
# ==============================================================================
with st.sidebar:
    st.markdown('<div class="card-subheader-title">📦 Inventario de Vectores</div>', unsafe_allow_html=True)
    if st.session_state.mis_vectores:
        for nombre, vec in st.session_state.mis_vectores.items():
            with st.expander(f"Vector {nombre} (R^{vec.shape[0]})"):
                imprimir_matriz_simbolica(vec)
    else:
        st.info("No hay vectores en memoria.")

    st.divider()
    if st.button("🗑️ Borrar todos los vectores", use_container_width=True):
        st.session_state.mis_vectores.clear()
        st.rerun()

# ==============================================================================
# ÁREA PRINCIPAL (PESTAÑAS)
# ==============================================================================
tab_gestion, tab_ops, tab_graficas, tab_sistemas, tab_analisis_conjunto = st.tabs([
    "📥 Gestión y Creación", 
    "⚙️ Operaciones", 
    "📈 Graficación (R2 y R3)", 
    "📐 Sistemas de Ecuaciones", 
    "🔍 Análisis de Conjuntos"
])

# ------------------------------------------------------------------------------
# TAB 0: GESTIÓN Y CREACIÓN
# ------------------------------------------------------------------------------
with tab_gestion:
    with st.container(border=True):
        st.markdown('<div class="card-header-title">Constructor de Vectores</div>', unsafe_allow_html=True)
        
        col_v1, col_v2 = st.columns([1, 2])
        
        with col_v1:
            st.markdown('<div class="card-subheader-title">➕ Nuevo Vector</div>', unsafe_allow_html=True)
            nombre_nuevo = st.text_input("Asignar nombre (Ej: u, v, w):", key="input_nom_vector").upper().strip()
            dim = st.number_input("Dimensión del vector (Rn):", min_value=2, max_value=10, value=3, key="dim_vector_input")
            
            with st.form("form_vector_main"):
                componentes = [st.text_input(f"Componente {i + 1}:", value="0", key=f"comp_{i}_main") for i in range(dim)]
                if st.form_submit_button("Guardar Vector", use_container_width=True):
                    try:
                        vec_nums = [leer_expresion_st(c) for c in componentes]
                        if None not in vec_nums and nombre_nuevo:
                            st.session_state.mis_vectores[nombre_nuevo] = sp.Matrix(vec_nums)
                            st.success(f"Vector {nombre_nuevo} guardado.")
                            st.rerun()
                        elif not nombre_nuevo:
                            st.error("Por favor, asigna un nombre al vector.")
                        else:
                            st.error("Error al procesar componentes.")
                    except Exception:
                        st.error("Error al procesar componentes.")

        with col_v2:
            st.markdown('<div class="card-subheader-title">📋 Vista Previa del Espacio de Trabajo</div>', unsafe_allow_html=True)
            if st.session_state.mis_vectores:
                st.info("Tus vectores actuales están listos para usarse en operaciones, sistemas de ecuaciones y graficación.")
                for nom, v in st.session_state.mis_vectores.items():
                    st.write(f"**{nom}** =")
                    imprimir_matriz_simbolica(v)
            else:
                st.warning("Aún no has creado ningún vector. Utiliza el formulario de la izquierda para comenzar.")

# ------------------------------------------------------------------------------
# TAB 1: OPERACIONES VECTORIALES
# ------------------------------------------------------------------------------
with tab_ops:
    if st.session_state.mis_vectores:
        with st.container(border=True):
            st.markdown('<div class="card-header-title">Operaciones Vectoriales Avanzadas</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                v1_nombre = st.selectbox("Vector 1 (v):", list(st.session_state.mis_vectores.keys()), key="v1")

            operacion = st.radio("Operación:", [
                "Suma (+)", "Resta (-)", "Escalar * v", "Distancia",
                "Norma", "Producto Punto", "Producto Cruz (R3)", "Ángulo", "Proyección", "Gram-Schmidt (Vector unitario)"
            ], horizontal=True)

            # Campos dinámicos dependiendo de la operación
            if operacion == "Escalar * v":
                escalar_str = st.text_input("Ingrese el escalar:", value="2")
            elif operacion not in ["Norma", "Gram-Schmidt (Vector unitario)"]:
                with col2:
                    v2_nombre = st.selectbox("Vector 2 (u):", list(st.session_state.mis_vectores.keys()), key="v2")

            if st.button("Calcular Operación", use_container_width=True):
                v1 = st.session_state.mis_vectores[v1_nombre]
                res = None  

                if operacion == "Escalar * v":
                    try:
                        esc = sp.sympify(escalar_str)
                        res = sp.simplify(esc * v1)
                        st.success("Resultado:")
                        imprimir_matriz_simbolica(res)
                    except Exception:
                        st.error("Escalar inválido.")

                elif operacion == "Norma":
                    st.latex(rf"||{v1_nombre}|| = {sp.latex(sp.simplify(v1.norm()))}")

                elif operacion == "Gram-Schmidt (Vector unitario)":
                    try:
                        v_ortho = sp.GramSchmidt([v1], orthonormal=True)
                        res = v_ortho[0]
                        st.success("Vector normalizado:")
                        imprimir_matriz_simbolica(res)
                    except ValueError:
                        st.error("Error: No se puede normalizar el vector nulo. El algoritmo de Gram-Schmidt requiere vectores linealmente independientes.")
                
                else:
                    v2 = st.session_state.mis_vectores[v2_nombre]

                    if operacion == "Suma (+)":
                        if v1.shape == v2.shape:
                            res = sp.simplify(v1 + v2)
                            imprimir_matriz_simbolica(res)
                        else: st.error("Diferente dimensión.")

                    elif operacion == "Resta (-)":
                        if v1.shape == v2.shape:
                            res = sp.simplify(v1 - v2)
                            imprimir_matriz_simbolica(res)
                        else: st.error("Diferente dimensión.")

                    elif operacion == "Distancia":
                        if v1.shape == v2.shape:
                            dist = sp.simplify((v1 - v2).norm())
                            st.latex(rf"d({v1_nombre}, {v2_nombre}) = {sp.latex(dist)}")
                        else: st.error("Diferente dimensión.")

                    elif operacion == "Producto Punto":
                        if v1.shape == v2.shape:
                            dot = sp.simplify(v1.dot(v2.conjugate()))
                            st.latex(rf"{v1_nombre} \cdot {v2_nombre} = {sp.latex(dot)}")
                        else: st.error("Diferente dimensión.")

                    elif operacion == "Producto Cruz (R3)":
                        if v1.rows == 3 and v2.rows == 3:
                            res = sp.simplify(v1.cross(v2))
                            imprimir_matriz_simbolica(res)
                        else: st.error("Ambos vectores deben estar en R3.")

                    elif operacion == "Ángulo":
                        if v1.shape == v2.shape:
                            cos_theta = sp.simplify(v1.dot(v2) / (v1.norm() * v2.norm()))
                            ang = sp.acos(cos_theta)
                            st.latex(rf"\theta = {sp.latex(ang)} \approx {sp.N(ang * 180 / sp.pi, 5)}^\circ")
                        else: st.error("Diferente dimensión.")

                    elif operacion == "Proyección":
                        if v1.shape == v2.shape:
                            res = sp.simplify((v1.dot(v2.conjugate()) / v2.dot(v2.conjugate())) * v2)
                            st.write(f"Proyección de {v1_nombre} sobre {v2_nombre}:")
                            imprimir_matriz_simbolica(res)
                        else: st.error("Diferente dimensión.")

                # Activador de guardado
                if res is not None:
                    st.session_state.ultimo_res_vec = res
                    st.session_state.mostrar_guardado_vec = True
                else:
                    st.session_state.mostrar_guardado_vec = False

            # Interfaz de guardado persistente
            if st.session_state.get('mostrar_guardado_vec') and 'ultimo_res_vec' in st.session_state:
                st.divider()
                col_g1, col_g2 = st.columns([2, 1])
                with col_g1:
                    nombre_guardar = st.text_input("Asignar nombre para guardar este vector:", key="save_vec_input").upper().strip()
                with col_g2:
                    st.write("")
                    if st.button("💾 Guardar Vector", use_container_width=True):
                        if nombre_guardar:
                            st.session_state.mis_vectores[nombre_guardar] = st.session_state.ultimo_res_vec
                            st.session_state.mostrar_guardado_vec = False
                            st.rerun()
                        else:
                            st.error("Ingrese un nombre válido.")
    else:
        st.info("Defina vectores en la pestaña 'Gestión y Creación'.")

# ------------------------------------------------------------------------------
# TAB 2: GRAFICACIÓN
# ------------------------------------------------------------------------------
with tab_graficas:
    with st.container(border=True):
        st.markdown('<div class="card-header-title">Graficador Espacial ($R^2$ y $R^3$)</div>', unsafe_allow_html=True)
        if st.session_state.mis_vectores:
            seleccionados = st.multiselect("Seleccione vectores a graficar:", list(st.session_state.mis_vectores.keys()))
            if st.button("Generar Gráfica", use_container_width=True) and seleccionados:
                vecs = [st.session_state.mis_vectores[n] for n in seleccionados]
                dim = vecs[0].rows

                if all(v.rows == dim for v in vecs) and dim in [2, 3] and not any(
                        v.free_symbols or v.has(sp.I) for v in vecs):
                    fig = plt.figure()
                    colores = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
                    if dim == 2:
                        ax = fig.add_subplot(111)
                        max_val = 1
                        for i, v in enumerate(vecs):
                            x, y = float(v[0]), float(v[1])
                            ax.quiver(0, 0, x, y, angles='xy', scale_units='xy', scale=1, color=colores[i % len(colores)],
                                      label=seleccionados[i])
                            max_val = max(max_val, abs(x), abs(y))
                        ax.set_xlim(-max_val - 1, max_val + 1); ax.set_ylim(-max_val - 1, max_val + 1)
                        ax.grid(True); ax.legend(); ax.axhline(0, color='black'); ax.axvline(0, color='black')
                    else:
                        ax = fig.add_subplot(111, projection='3d')
                        max_val = 1
                        for i, v in enumerate(vecs):
                            x, y, z = float(v[0]), float(v[1]), float(v[2])
                            ax.quiver(0, 0, 0, x, y, z, color=colores[i % len(colores)], label=seleccionados[i])
                            max_val = max(max_val, abs(x), abs(y), abs(z))
                        ax.set_xlim([-max_val, max_val]); ax.set_ylim([-max_val, max_val]); ax.set_zlim([-max_val, max_val])
                        ax.legend()
                    st.pyplot(fig)
                else:
                    st.error("Todos los vectores deben ser puramente numéricos y pertenecer al mismo espacio (R2 o R3).")
        else:
            st.info("No hay vectores disponibles para graficar.")

# ------------------------------------------------------------------------------
# TAB 3: SISTEMAS DE ECUACIONES
# ------------------------------------------------------------------------------
with tab_sistemas:
    with st.container(border=True):
        st.markdown('<div class="card-header-title">Resolución de Sistemas de Ecuaciones Lineales</div>', unsafe_allow_html=True)
        
        n_vars = int(st.number_input("Número de incógnitas:", min_value=2, max_value=10, value=3, step=1))
        st.markdown(f"Ingrese la matriz aumentada $[A|b]$ de tamaño ${n_vars} \\times {n_vars+1}$:")
        
        with st.form("form_sistema"):
            elementos = []
            for i in range(n_vars):
                cols = st.columns(n_vars + 1)
                fila = []
                for j in range(n_vars + 1):
                    with cols[j]:
                        label = f"x_{j+1}" if j < n_vars else "b"
                        fila.append(st.text_input(label, value="0", key=f"sys_{n_vars}_{i}_{j}"))
                elementos.append(fila)
                
            if st.form_submit_button("Resolver Sistema", use_container_width=True):
                M_aug = sp.zeros(n_vars, n_vars + 1)
                error_parser = False
                
                for i in range(n_vars):
                    for j in range(n_vars + 1):
                        val = leer_expresion_st(elementos[i][j])
                        if val is None: error_parser = True
                        else: M_aug[i, j] = val
                        
                if not error_parser:
                    st.markdown('<div class="card-subheader-title">Matriz Aumentada</div>', unsafe_allow_html=True)
                    imprimir_matriz_simbolica(M_aug)
                    
                    variables = sp.symbols(f'x1:{n_vars+1}')
                    solucion = sp.linsolve(M_aug, variables)
                    
                    if not solucion:
                        st.error("Sistema Incompatible (S.I.). No tiene solución (El conjunto solución está vacío).")
                    else:
                        sol_lista = list(solucion)[0]
                        hay_parametros = any(val.free_symbols for val in sol_lista if hasattr(val, 'free_symbols'))
                        
                        if not hay_parametros:
                            st.success("Sistema Compatible Determinado (S.C.D.). Solución única:")
                            for i, var in enumerate(variables):
                                st.latex(rf"{var} = {sp.latex(sol_lista[i])}")
                        else:
                            st.warning("Sistema Compatible Indeterminado (S.C.I.). Infinitas soluciones paramétricas:")
                            for i, var in enumerate(variables):
                                st.latex(rf"{var} = {sp.latex(sol_lista[i])}")

# ------------------------------------------------------------------------------
# TAB 4: ANÁLISIS DE CONJUNTOS
# ------------------------------------------------------------------------------
with tab_analisis_conjunto:
    with st.container(border=True):
        st.markdown('<div class="card-header-title">Análisis de Conjuntos (L.I. y Bases)</div>', unsafe_allow_html=True)
        seleccion = st.multiselect("Seleccione vectores para analizar:", list(st.session_state.mis_vectores.keys()))
        
        if seleccion:
            vectores = [st.session_state.mis_vectores[n] for n in seleccion]
            mat_conjunto = sp.Matrix.hstack(*vectores)
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown('<div class="card-subheader-title">Matriz formada</div>', unsafe_allow_html=True)
                imprimir_matriz_simbolica(mat_conjunto)
            
            with col_c2:
                n_vecs = len(vectores)
                dim = vectores[0].rows
                rank = mat_conjunto.rank()
                
                es_li = (rank == n_vecs)
                st.markdown(f'<div class="card-subheader-title">Propiedades del Conjunto</div>', unsafe_allow_html=True)
                st.write(f"¿Es Linealmente Independiente?: {'✅ Sí' if es_li else '❌ No'}")
                st.markdown(f"¿Es Base para $R^{dim}$?: {'✅ Sí' if (es_li and n_vecs == dim) else '❌ No'}")

            st.divider()
            st.markdown('<div class="card-subheader-title">Acciones sobre el conjunto</div>', unsafe_allow_html=True)
            
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("Crear Matriz", use_container_width=True):
                    nombre_mat = "MAT_" + "_".join(seleccion)[:10] 
                    st.session_state.mis_matrices[nombre_mat] = mat_conjunto
                    st.success(f"Guardado como '{nombre_mat}' en Matrices")
                
            with col_btn2:
                ortonormal = st.checkbox("¿Base Ortonormal? (Vectores unitarios)", value=True)
                if st.button("Aplicar Gram-Schmidt", use_container_width=True):
                    try:
                        base_ortho = sp.GramSchmidt(vectores, orthonormal=ortonormal)
                        mat_ortho = sp.Matrix.hstack(*base_ortho)
                        
                        if ortonormal:
                            st.write("**Base Ortonormal resultante:**")
                        else:
                            st.write("**Base Ortogonal resultante:**")
                            
                        imprimir_matriz_simbolica(mat_ortho)
                        st.session_state.mis_matrices["GS_MAT"] = mat_ortho
                        st.success("Guardado temporalmente como 'GS_MAT' en Matrices.")
                    except Exception as e:
                        st.error(f"Error al aplicar Gram-Schmidt: {e}")
                
            with col_btn3:
                if st.button("Calcular Base Dual (V*)", use_container_width=True):
                    if not (es_li and n_vecs == dim):
                        st.error("Error: El conjunto seleccionado no es una base válida (debe ser cuadrada y L.I.).")
                    else:
                        try:
                            base_dual = sp.simplify(mat_conjunto.inv())
                            st.write(r"**Matriz de Transición de la Base Dual ($\mathcal{B}^*$):**")
                            st.info(r"💡 **Nota:** Cada renglón representa los coeficientes del funcional lineal $f_i$.")
                            imprimir_matriz_simbolica(base_dual)
                            st.session_state.mis_matrices["DUAL_MAT"] = base_dual
                            st.success("Guardado temporalmente como 'DUAL_MAT' en Matrices.")
                        except Exception as e:
                            st.error(f"Error al calcular la base dual: {e}")

        st.divider()
        st.markdown('<div class="card-subheader-title">Extraer filas/columnas como vectores</div>', unsafe_allow_html=True)
        if st.session_state.mis_matrices:
            mat_nombre = st.selectbox("Elegir matriz:", list(st.session_state.mis_matrices.keys()))
            if mat_nombre:
                M = st.session_state.mis_matrices[mat_nombre]
                tipo_ext = st.radio("Extraer:", ["Renglones", "Columnas"], horizontal=True)
                if st.button("Extraer a Inventario de Vectores", use_container_width=True):
                    for i in range(M.rows if tipo_ext == "Renglones" else M.cols):
                        vec = M.row(i).T if tipo_ext == "Renglones" else M.col(i)
                        nombre = f"{mat_nombre}_{tipo_ext[0]}{i+1}"
                        st.session_state.mis_vectores[nombre] = vec
                        st.write(f"Guardado: {nombre}")
        else:
            st.info("No hay matrices guardadas en el inventario global.")
