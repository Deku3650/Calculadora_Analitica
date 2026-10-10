import streamlit as st
import sympy as sp
import re

try:
    from utils import imprimir_matriz_simbolica, leer_expresion_st, Crear_Transformacion_UI, mostrar_detalle_tl
except ImportError:
    st.error("Error al cargar utils.py. Asegúrese de ejecutar la aplicación correctamente.")

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Transformaciones Lineales - MATHESIS", page_icon="🔄", layout="wide")

# Inicialización de estados de sesión
if 'mis_transformaciones' not in st.session_state:
    st.session_state.mis_transformaciones = {}
if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}

# ==============================================================================
# INYECCIÓN DIRECTA DE CSS (ESTILIZACIÓN INTEGRAL DE SUBTÍTULOS Y MÓDULO)
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

    /* 4. ESTILIZADO AUTOMÁTICO DE SUBTÍTULOS NATIVOS Y DINÁMICOS */
    .stMarkdown h1, .stMarkdown h2, [data-testid="stHeader"] h2 {
        color: #38bdf8 !important;
        font-size: 1.35rem !important;
        font-weight: 800 !important;
        border-bottom: 2px solid rgba(56, 189, 248, 0.25) !important;
        padding-bottom: 6px !important;
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
        letter-spacing: -0.3px !important;
    }

    .stMarkdown h3, .stMarkdown h4, [data-testid="stSubheader"] h3 {
        color: #38bdf8 !important;
        font-size: 1.12rem !important;
        font-weight: 700 !important;
        border-left: 4px solid #0284c7 !important;
        padding-left: 10px !important;
        margin-top: 0.8rem !important;
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

    /* 6. TÍTULOS Y SUBTÍTULOS RESALTADOS EN TARJETAS */
    .card-header-title {
        background: linear-gradient(135deg, #0284c7 0%, #6366f1 100%);
        color: #ffffff !important;
        font-size: 17px;
        font-weight: 800;
        padding: 8px 16px;
        border-radius: 10px;
        display: inline-block;
        margin-bottom: 16px;
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

    .section-badge-title {
        color: #e0f2fe !important;
        background: rgba(2, 132, 199, 0.2);
        font-size: 14px;
        font-weight: 700;
        padding: 6px 12px;
        border-radius: 8px;
        border: 1px solid rgba(56, 189, 248, 0.3);
        display: inline-block;
        margin-bottom: 10px;
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
        <h1 class="title-text">🔄 Transformaciones Lineales</h1>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# PANEL LATERAL (INVENTARIO DE T.L.)
# ==============================================================================
with st.sidebar:
    st.markdown('<div class="card-subheader-title">📦 Gestión de T.L.</div>', unsafe_allow_html=True)
    if st.session_state.mis_transformaciones:
        st.write("Transformaciones activas:")
        for nombre in st.session_state.mis_transformaciones.keys():
            st.write(f"• **{nombre}**")
    else:
        st.info("No hay transformaciones guardadas.")
        
    st.divider()
    if st.button("🗑️ Borrar todas las T.L.", use_container_width=True):
        st.session_state.mis_transformaciones.clear()
        st.session_state.pop('temp_inv_res', None)
        st.session_state.pop('temp_comp_res', None)
        st.rerun()

# ==============================================================================
# ÁREA PRINCIPAL (PESTAÑAS INTERACTIVAS)
# ==============================================================================
tab_crear, tab_analisis, tab_evaluacion, tab_composicion, tab_bases = st.tabs([
    "📥 Definir T.L.", 
    "🔎 Detalles y Núcleo/Imagen", 
    "🎯 Evaluar Vector", 
    "⚙️ Composición e Inversa", 
    "📐 Cambio de Base"
])

# --------------------------------------------------------------------------
# PESTAÑA 1: Definir T.L.
# --------------------------------------------------------------------------
with tab_crear:
    with st.container(border=True):
        st.markdown('<div class="card-header-title">⚙️ Construir Nueva Transformación Lineal</div>', unsafe_allow_html=True)
        Crear_Transformacion_UI()

# --------------------------------------------------------------------------
# PESTAÑA 2: Análisis (Ker/Im)
# --------------------------------------------------------------------------
with tab_analisis:
    if st.session_state.mis_transformaciones:
        with st.container(border=True):
            st.markdown('<div class="card-header-title">📊 Análisis de Estructura (Kernel e Imagen)</div>', unsafe_allow_html=True)
            tl_sel = st.selectbox("Seleccione Transformación:", list(st.session_state.mis_transformaciones.keys()), key="ana_tl")
            paquete = st.session_state.mis_transformaciones[tl_sel]
            
            st.markdown('<div class="card-subheader-title">Propiedades Generales de T.L.</div>', unsafe_allow_html=True)
            mostrar_detalle_tl(tl_sel, paquete)
            
            st.divider()
            if st.button("🚀 Ejecutar Análisis Completo (Ker/Im)", use_container_width=True):
                A = paquete["matriz_asociada"]
                col1, col2 = st.columns(2)
                
                with col1:
                    with st.container(border=True):
                        st.markdown('<div class="card-subheader-title">Nullspace / Núcleo (Ker T)</div>', unsafe_allow_html=True)
                        base_ker = A.nullspace()
                        if not base_ker: 
                            st.write(r"El núcleo es trivial: $\{ \mathbf{0} \}$")
                        else: 
                            imprimir_matriz_simbolica(sp.Matrix.hstack(*base_ker))
                        st.info(f"Nulidad (dim Ker T): {len(base_ker)}")
                        
                with col2:
                    with st.container(border=True):
                        st.markdown('<div class="card-subheader-title">Columnspace / Imagen (Im T)</div>', unsafe_allow_html=True)
                        base_im = A.columnspace()
                        if not base_im: 
                            st.write(r"La imagen es trivial: $\{ \mathbf{0} \}$")
                        else: 
                            imprimir_matriz_simbolica(sp.Matrix.hstack(*base_im))
                        st.info(f"Rango (dim Im T): {len(base_im)}")
    else:
        st.info("👈 Primero defina o importe una transformación en la pestaña 'Definir T.L.'.")

# --------------------------------------------------------------------------
# PESTAÑA 3: Evaluar Vector
# --------------------------------------------------------------------------
with tab_evaluacion:
    if st.session_state.mis_transformaciones:
        with st.container(border=True):
            st.markdown('<div class="card-header-title">🎯 Evaluación de Vectores</div>', unsafe_allow_html=True)
            tl_eval = st.selectbox("Seleccione Transformación:", list(st.session_state.mis_transformaciones.keys()), key="eval_tl")
            paquete = st.session_state.mis_transformaciones[tl_eval]
            
            st.markdown(f'<div class="card-subheader-title">Ingrese los componentes del vector (Dimensión {paquete["dim_V"]}):</div>', unsafe_allow_html=True)
            
            with st.form("form_eval"):
                comp = [st.text_input(f"Componente v_{i+1}:", value="0", key=f"eval_comp_{i}") for i in range(paquete['dim_V'])]
                submit_eval = st.form_submit_button("Calcula Imagen T(v)", use_container_width=True)
                
                if submit_eval:
                    try:
                        V = sp.Matrix([leer_expresion_st(c) for c in comp])
                        res = sp.simplify(paquete["matriz_asociada"] * V)
                        st.markdown('<div class="section-badge-title">Resultado de la evaluación T(v)</div>', unsafe_allow_html=True)
                        imprimir_matriz_simbolica(res)
                    except Exception as e:
                        st.error(f"Error al evaluar el vector: {e}")
    else:
        st.info("👈 No hay transformaciones definidas. Cree una en la pestaña 'Definir T.L.'.")

# --------------------------------------------------------------------------
# PESTAÑA 4: Composición e Inversa
# --------------------------------------------------------------------------
with tab_composicion:
    if not st.session_state.mis_transformaciones:
        st.info("👈 No hay transformaciones definidas. Cree una en la pestaña 'Definir T.L.'.")
    else:
        # --- SECCIÓN 1: INVERSA ---
        with st.container(border=True):
            st.markdown('<div class="card-header-title">🔄 1. Inversa de una Transformación Lineal ($T^{-1}$)</div>', unsafe_allow_html=True)
            tl_inv = st.selectbox("Transformación a invertir:", list(st.session_state.mis_transformaciones.keys()), key="inv_tl")
            
            if st.button("🧮 Calcular Inversa Analítica", key="btn_inv_calc", use_container_width=True):
                paq_inv = st.session_state.mis_transformaciones[tl_inv]
                A = paq_inv["matriz_asociada"]
                
                if paq_inv["dim_V"] != paq_inv["dim_W"]:
                    st.error("La matriz asociada no es cuadrada. Solo los endomorfismos admiten operador inverso.")
                else:
                    try:
                        M_inversa = sp.simplify(A.inv())
                        vars_inv = tuple(sp.symbols(f"w_{i+1}") for i in range(paq_inv["dim_W"]))
                        regla_inv = sp.simplify(M_inversa * sp.Matrix(vars_inv))
                        
                        st.session_state.temp_inv_res = {
                            "matriz": M_inversa, "regla": regla_inv, "variables": vars_inv,
                            "dv": paq_inv["dim_W"], "dw": paq_inv["dim_V"],
                            "b1": paq_inv["base_codominio"], "b2": paq_inv["base_dominio"]
                        }
                        st.success("¡Estructura invertible calculada con éxito!")
                    except Exception:
                        st.error("La transformación no es un Isomorfismo (Determinante = 0). No admite operador inverso.")

            if 'temp_inv_res' in st.session_state:
                st.divider()
                inv_d = st.session_state.temp_inv_res
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<div class="card-subheader-title">Matriz Asociada ($[T^{-1}]$)</div>', unsafe_allow_html=True)
                    imprimir_matriz_simbolica(inv_d["matriz"])
                with c2:
                    st.markdown('<div class="card-subheader-title">Regla de Correspondencia ($T^{-1}(\\mathbf{w})$)</div>', unsafe_allow_html=True)
                    st.latex(sp.latex(inv_d["regla"]))
                
                col_btn1, col_btn2 = st.columns([2, 1])
                with col_btn1:
                    nombre_inv = st.text_input("Guardar operador inverso como:", value=f"{tl_inv}_INV", key="inp_nom_inv").upper().strip()
                with col_btn2:
                    st.write("")
                    if st.button("💾 Guardar Inversa", key="btn_save_inv", use_container_width=True):
                        if nombre_inv:
                            st.session_state.mis_transformaciones[nombre_inv] = {
                                "dim_V": inv_d["dv"], "dim_W": inv_d["dw"], "variables": inv_d["variables"],
                                "matriz_asociada": inv_d["matriz"], "regla": inv_d["regla"],
                                "base_dominio": inv_d["b1"], "base_codominio": inv_d["b2"]
                            }
                            st.session_state.pop("temp_inv_res", None)
                            st.success(f"Operador guardado como '{nombre_inv}'.")
                            st.rerun()

        # --- SECCIÓN 2: COMPOSICIÓN ---
        with st.container(border=True):
            st.markdown('<div class="card-header-title">🔗 2. Composición de Transformaciones ($S \\circ T$)</div>', unsafe_allow_html=True)
            st.latex(r"(S \circ T)(\vec{v}) = S(T(\vec{v}))")
            
            col_t, col_s = st.columns(2)
            with col_t: 
                T = st.selectbox("1º Se aplica (Interna T):", list(st.session_state.mis_transformaciones.keys()), key="comp_t")
            with col_s: 
                S = st.selectbox("2º Se aplica (Externa S):", list(st.session_state.mis_transformaciones.keys()), key="comp_s")
            
            if st.button("🧮 Efectuar Composición", key="btn_comp_calc", use_container_width=True):
                paq_T = st.session_state.mis_transformaciones[T]
                paq_S = st.session_state.mis_transformaciones[S]
                
                if paq_T["dim_W"] != paq_S["dim_V"]:
                    st.error(f"Incompatibilidad: El codominio de {T} (dim={paq_T['dim_W']}) no coincide con el dominio de {S} (dim={paq_S['dim_V']}).")
                else:
                    MT = paq_T["matriz_asociada"]
                    MS = paq_S["matriz_asociada"]
                    M_comp = sp.simplify(MS * MT)
                    regla_comp = sp.simplify(M_comp * sp.Matrix(paq_T["variables"]))
                    
                    st.session_state.temp_comp_res = {
                        "matriz": M_comp, "regla": regla_comp, "variables": paq_T["variables"],
                        "dv": paq_T["dim_V"], "dw": paq_S["dim_W"],
                        "b1": paq_T["base_dominio"], "b2": paq_S["base_codominio"]
                    }
                    st.success("¡Composición calculada analíticamente!")

            if 'temp_comp_res' in st.session_state:
                st.divider()
                comp_d = st.session_state.temp_comp_res
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<div class="card-subheader-title">Matriz Asociada Resultante ($[S \\circ T]$)</div>', unsafe_allow_html=True)
                    imprimir_matriz_simbolica(comp_d["matriz"])
                with c2:
                    st.markdown('<div class="card-subheader-title">Regla de Correspondencia ($(S \\circ T)(\\mathbf{v})$)</div>', unsafe_allow_html=True)
                    st.latex(sp.latex(comp_d["regla"]))
                
                col_btn1, col_btn2 = st.columns([2, 1])
                with col_btn1:
                    nombre_comp = st.text_input("Guardar composición como:", value=f"{S}_COMP_{T}", key="inp_nom_comp").upper().strip()
                with col_btn2:
                    st.write("")
                    if st.button("💾 Guardar Composición", key="btn_save_comp", use_container_width=True):
                        if nombre_comp:
                            st.session_state.mis_transformaciones[nombre_comp] = {
                                "dim_V": comp_d["dv"], "dim_W": comp_d["dw"], "variables": comp_d["variables"],
                                "matriz_asociada": comp_d["matriz"], "regla": comp_d["regla"],
                                "base_dominio": comp_d["b1"], "base_codominio": comp_d["b2"]
                            }
                            st.session_state.pop("temp_comp_res", None)
                            st.success(f"Composición guardada como '{nombre_comp}'.")
                            st.rerun()

# --------------------------------------------------------------------------
# PESTAÑA 5: Bases y Espacio Dual
# --------------------------------------------------------------------------
with tab_bases:
    if st.session_state.mis_transformaciones:
        with st.container(border=True):
            st.markdown('<div class="card-header-title">📐 Cambio de Base y Espacio Dual</div>', unsafe_allow_html=True)
            tl_base = st.selectbox("Seleccione T.L. activa para operar:", list(st.session_state.mis_transformaciones.keys()), key="base_tl")
            paquete = st.session_state.mis_transformaciones[tl_base]
            
            st.markdown('<div class="card-subheader-title">Bases Actuales Configuradas</div>', unsafe_allow_html=True)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.write(r"**Base del Dominio ($\beta$):**")
                imprimir_matriz_simbolica(paquete['base_dominio'])
            with col_b2:
                st.write(r"**Base del Codominio ($\gamma$):**")
                imprimir_matriz_simbolica(paquete['base_codominio'])
                
            st.divider()
            st.markdown('<div class="card-subheader-title">Cambio de Base General</div>', unsafe_allow_html=True)
            st.caption("Ingrese los vectores de las nuevas bases. Ejemplo: `[2,0,0], [0,-1,0], [0,0,-2]`. Si deja un campo vacío, se asumirá la base canónica.")
            
            with st.form("form_cambio_base"):
                col_nb1, col_nb2 = st.columns(2)
                with col_nb1:
                    nb1_input = st.text_area(r"Nueva Base Dominio ($\beta'$):", value="", key="new_b1")
                with col_nb2:
                    nb2_input = st.text_area(r"Nueva Base Codominio ($\gamma'$):", value="", key="new_b2")
                    
                submit_bases = st.form_submit_button("Calcular Matriz en Nuevas Bases", use_container_width=True)
                
            if submit_bases:
                def procesar_base(texto, dim):
                    if not texto.strip(): return sp.eye(dim)
                    bloques = re.findall(r'\[(.*?)\]', texto)
                    if not bloques: return sp.eye(dim)
                    matriz = []
                    for b in bloques:
                        matriz.append([leer_expresion_st(c) for c in b.split(',')])
                    return sp.Matrix(matriz).T
                    
                try:
                    Q = procesar_base(nb1_input, paquete["dim_V"]) 
                    P = procesar_base(nb2_input, paquete["dim_W"]) 
                    
                    if Q.det() == 0 or P.det() == 0:
                        st.error("Error: Las bases ingresadas no son linealmente independientes.")
                    else:
                        A_can = paquete["matriz_asociada"]
                        P_inv = sp.simplify(P.inv())
                        M_nueva = sp.simplify(P_inv * A_can * Q)
                        
                        st.success("¡Cambio de base matemático exitoso!")
                        
                        st.markdown('<div class="card-subheader-title">Desglose del Teorema de Cambio de Base</div>', unsafe_allow_html=True)
                        st.latex(r"[T]_{\beta'}^{\gamma'} = P^{-1} \cdot [T]_{\beta}^{\gamma} \cdot Q")
                        
                        col_mat1, col_mat2, col_mat3 = st.columns(3)
                        with col_mat1:
                            st.write(r"**Paso del Dominio ($Q$):**")
                            imprimir_matriz_simbolica(Q)
                        with col_mat2:
                            st.write(r"**Paso del Codominio ($P$):**")
                            imprimir_matriz_simbolica(P)
                        with col_mat3:
                            st.write(r"**Inversa de P ($P^{-1}$):**")
                            imprimir_matriz_simbolica(P_inv)
                            
                        st.write("**Comprobación de la fórmula matricial:**")
                        st.latex(rf"{sp.latex(P_inv)} \cdot {sp.latex(A_can)} \cdot {sp.latex(Q)} = {sp.latex(M_nueva)}")
                        
                        st.markdown('<div class="card-subheader-title">Nueva Matriz Asociada $[T]_{\\beta\'}^{\\gamma\'}$</div>', unsafe_allow_html=True)
                        imprimir_matriz_simbolica(M_nueva)
                        
                        st.divider()
                        st.markdown('<div class="card-subheader-title">Espacio Dual ($V^*$)</div>', unsafe_allow_html=True)
                        st.write(r"Matriz de Transición de la Base Dual ($\mathcal{B}^*$) asociada a la nueva base del dominio $\beta'$:")
                        imprimir_matriz_simbolica(sp.simplify(Q.inv()))
                        
                except Exception as e:
                    st.error(f"Error al procesar el cambio de base. Verifique la sintaxis. Detalle: {e}")
    else:
        st.info("👈 Defina una transformación primero en la pestaña 'Definir T.L.'.")
