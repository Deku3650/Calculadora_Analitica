import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import scipy.integrate as spi
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor

try:
    from utils import leer_expresion_st, imprimir_matriz_simbolica
    try:
        from utils import parse_seguro
    except ImportError:
        parse_seguro = parse_expr
except ImportError:
    st.error("Error crítico: No se pudo cargar el analizador matemático desde utils.py. Asegúrese de ejecutar la app desde la raíz.")
    st.stop()

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ecuaciones Diferenciales - MATHESIS", page_icon="🌪️", layout="wide")

# ==============================================================================
# INYECCIÓN DIRECTA DE CSS (ESTILOS UNIFICADOS Y LIMPIOS DE MATHESIS)
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
# INICIALIZACIÓN DE MEMORIA PERSISTENTE
# ==============================================================================
if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}
if 'sys_P' not in st.session_state:
    st.session_state.sys_P = None
if 'sys_Q' not in st.session_state:
    st.session_state.sys_Q = None
if 'sys_R' not in st.session_state:
    st.session_state.sys_R = None

# ==============================================================================
# ENCABEZADO CON BANNER ESTILIZADO
# ==============================================================================
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">🌪️ Análisis de Campos Vectoriales y Sistemas Dinámicos</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown(r"Estudio de sistemas lineales y no lineales, retratos de fase, diagonalización, límites asintóticos e isoclinas en $\mathbb{R}^2$ y $\mathbb{R}^3$.")

tab_sistemas, tab_edo1 = st.tabs([
    "Sistemas y Plano Fase",
    "Resolutor de EDOs (1er Orden)"
])

# Símbolos base globales
t_sym = sp.Symbol('t', real=True)
x_sym, y_sym, z_sym = sp.symbols('x y z', real=True)
c1_sym, c2_sym, c3_sym = sp.symbols('C_1 C_2 C_3', real=True)
transf = standard_transformations + (implicit_multiplication_application, convert_xor)
dicc_loc = {'x': x_sym, 'y': y_sym, 'z': z_sym, 't': t_sym, 'sin': sp.sin, 'cos': sp.cos, 'exp': sp.exp}

# ==============================================================================
# PESTAÑA 1: CAMPOS VECTORIALES (LINEALES Y NO LINEALES)
# ==============================================================================
with tab_sistemas:
    col_input, col_info = st.columns([1, 1.5])
    
    with col_input:
        with st.container(border=True):
            st.markdown('<div class="card-header-title">Definición del Campo Vectorial</div>', unsafe_allow_html=True)
            st.info(r"💡 Exprese su campo $V(x, y)$ o $V(x, y, z)$.")
            
            fuente_matriz = st.radio("Entrada:", ["Ecuaciones Explícitas", "Matriz $2\\times2$ (Lineal)", "Matriz $3\\times3$ (Lineal)", "Importar del Módulo de Matrices"])
            
            if fuente_matriz == "Ecuaciones Explícitas":
                with st.form("form_ecuaciones"):
                    str_P = st.text_input("dx/dt = P(x, y, z, t)", value="-x*(y^2 - x^6)")
                    str_Q = st.text_input("dy/dt = Q(x, y, z, t)", value="0")
                    str_R = st.text_input("dz/dt = R(x, y, z, t) [Opcional para 3D]", value="")
                    
                    if st.form_submit_button("Analizar Campo Vectorial", use_container_width=True):
                        try:
                            st.session_state.sys_P = parse_seguro(str_P, transformaciones=transf, local_dict=dicc_loc)
                            st.session_state.sys_Q = parse_seguro(str_Q, transformaciones=transf, local_dict=dicc_loc)
                            if str_R.strip():
                                st.session_state.sys_R = parse_seguro(str_R, transformaciones=transf, local_dict=dicc_loc)
                            else:
                                st.session_state.sys_R = None
                        except Exception as e:
                            st.error(f"Error de sintaxis o seguridad: {e}. Revise los caracteres ingresados.")
                            
            elif fuente_matriz == "Matriz $2\\times2$ (Lineal)":
                with st.form("form_matriz_sist"):
                    c1, c2 = st.columns(2)
                    with c1: 
                        a11 = st.text_input("a:", value="1")
                        a21 = st.text_input("c:", value="3")
                    with c2: 
                        a12 = st.text_input("b:", value="-1")
                        a22 = st.text_input("d:", value="5")
                    if st.form_submit_button("Cargar Sistema Lineal", use_container_width=True):
                        try:
                            st.session_state.sys_P = leer_expresion_st(a11)*x_sym + leer_expresion_st(a12)*y_sym
                            st.session_state.sys_Q = leer_expresion_st(a21)*x_sym + leer_expresion_st(a22)*y_sym
                            st.session_state.sys_R = None
                        except: st.error("Error en las entradas.")
                        
            elif fuente_matriz == "Matriz $3\\times3$ (Lineal)":
                with st.form("form_matriz_sist_3x3"):
                    c1, c2, c3 = st.columns(3)
                    with c1: 
                        a11 = st.text_input("a11:", value="1")
                        a21 = st.text_input("a21:", value="0")
                        a31 = st.text_input("a31:", value="0")
                    with c2: 
                        a12 = st.text_input("a12:", value="0")
                        a22 = st.text_input("a22:", value="-1")
                        a32 = st.text_input("a32:", value="0")
                    with c3: 
                        a13 = st.text_input("a13:", value="0")
                        a23 = st.text_input("a23:", value="0")
                        a33 = st.text_input("a33:", value="-2")
                    if st.form_submit_button("Cargar Sistema Lineal 3x3", use_container_width=True):
                        try:
                            st.session_state.sys_P = leer_expresion_st(a11)*x_sym + leer_expresion_st(a12)*y_sym + leer_expresion_st(a13)*z_sym
                            st.session_state.sys_Q = leer_expresion_st(a21)*x_sym + leer_expresion_st(a22)*y_sym + leer_expresion_st(a23)*z_sym
                            st.session_state.sys_R = leer_expresion_st(a31)*x_sym + leer_expresion_st(a32)*y_sym + leer_expresion_st(a33)*z_sym
                        except: st.error("Error en las entradas.")

            elif fuente_matriz == "Importar del Módulo de Matrices":
                matrices_compatibles = {k: v for k, v in st.session_state.mis_matrices.items() if v.shape in [(2, 2), (3, 3)]}
                if not matrices_compatibles:
                    st.warning(r"No hay matrices $2 \times 2$ o $3 \times 3$ guardadas.")
                else:
                    nombre_mat = st.selectbox("Seleccione Matriz:", list(matrices_compatibles.keys()))
                    mat = matrices_compatibles[nombre_mat]
                    imprimir_matriz_simbolica(mat)
                    if st.button("Analizar Matriz Importada", use_container_width=True):
                        st.session_state.sys_P = mat[0,0]*x_sym + mat[0,1]*y_sym + (mat[0,2]*z_sym if mat.shape == (3,3) else 0)
                        st.session_state.sys_Q = mat[1,0]*x_sym + mat[1,1]*y_sym + (mat[1,2]*z_sym if mat.shape == (3,3) else 0)
                        if mat.shape == (3,3):
                            st.session_state.sys_R = mat[2,0]*x_sym + mat[2,1]*y_sym + mat[2,2]*z_sym
                        else:
                            st.session_state.sys_R = None

            if st.button("🗑️ Limpiar Sistema", use_container_width=True):
                st.session_state.sys_P = None
                st.session_state.sys_Q = None
                st.session_state.sys_R = None
                st.rerun()

    # ================= PROCESAMIENTO MATEMÁTICO CENTRAL =================
    if st.session_state.sys_P is not None and st.session_state.sys_Q is not None:
        P_expr = st.session_state.sys_P
        Q_expr = st.session_state.sys_Q
        es_3d = st.session_state.sys_R is not None
        Lambda_sym = None 
        
        if es_3d:
            R_expr = st.session_state.sys_R
            es_autonomo = not (P_expr.has(t_sym) or Q_expr.has(t_sym) or R_expr.has(t_sym))
        else:
            es_autonomo = not (P_expr.has(t_sym) or Q_expr.has(t_sym))
        
        with col_info:
            with st.container(border=True):
                st.markdown('<div class="card-header-title">1. Campo Vectorial Interpretado</div>', unsafe_allow_html=True)
                if es_3d:
                    st.latex(rf"V(x, y, z) = \begin{{bmatrix}} x' \\ y' \\ z' \end{{bmatrix}} = \begin{{bmatrix}} {sp.latex(P_expr)} \\ {sp.latex(Q_expr)} \\ {sp.latex(R_expr)} \end{{bmatrix}}")
                else:
                    st.latex(rf"V(x, y) = \begin{{bmatrix}} x' \\ y' \end{{bmatrix}} = \begin{{bmatrix}} {sp.latex(P_expr)} \\ {sp.latex(Q_expr)} \end{{bmatrix}}")
                
                t_eval = 0.0
                if not es_autonomo:
                    st.warning("El campo es **No Autónomo**. Seleccione un instante de evaluación $t$:")
                    t_eval = st.slider("Evaluar espacio en t =", min_value=-10.0, max_value=10.0, value=0.0, step=0.5)
                    
                P_f = P_expr.subs(t_sym, t_eval)
                Q_f = Q_expr.subs(t_sym, t_eval)
                if es_3d: R_f = R_expr.subs(t_sym, t_eval)
                
                st.markdown('<div class="card-subheader-title">2. Matriz Jacobiana (Linealización)</div>', unsafe_allow_html=True)
                if es_3d:
                    J_sym = sp.Matrix([
                        [sp.diff(P_f, x_sym), sp.diff(P_f, y_sym), sp.diff(P_f, z_sym)],
                        [sp.diff(Q_f, x_sym), sp.diff(Q_f, y_sym), sp.diff(Q_f, z_sym)],
                        [sp.diff(R_f, x_sym), sp.diff(R_f, y_sym), sp.diff(R_f, z_sym)]
                    ])
                else:
                    J_sym = sp.Matrix([
                        [sp.diff(P_f, x_sym), sp.diff(P_f, y_sym)],
                        [sp.diff(Q_f, x_sym), sp.diff(Q_f, y_sym)]
                    ])
                    
                if es_3d:
                    es_lineal = not bool(J_sym.free_symbols.intersection({x_sym, y_sym, z_sym}))
                else:
                    es_lineal = not bool(J_sym.free_symbols.intersection({x_sym, y_sym}))
                
                x0_val, y0_val, z0_val = 0.0, 0.0, 0.0
                es_equilibrio = True 
                
                if not es_lineal:
                    st.info("💡 El sistema es **No Lineal**. Evalúe la matriz Jacobiana en un punto crítico para aplicar Hartman-Grobman.")
                    st.latex(rf"J = {sp.latex(J_sym)}")
                    if es_3d:
                        c_pt1, c_pt2, c_pt3 = st.columns(3)
                        with c_pt1: x0_val = st.number_input("x_0:", value=0.0)
                        with c_pt2: y0_val = st.number_input("y_0:", value=0.0)
                        with c_pt3: z0_val = st.number_input("z_0:", value=0.0)
                    else:
                        c_pt1, c_pt2 = st.columns(2)
                        with c_pt1: x0_val = st.number_input("x_0:", value=0.0)
                        with c_pt2: y0_val = st.number_input("y_0:", value=0.0)
                        
                    sust_pto = {x_sym: x0_val, y_sym: y0_val, z_sym: z0_val} if es_3d else {x_sym: x0_val, y_sym: y0_val}
                    val_P = float(P_f.subs(sust_pto))
                    val_Q = float(Q_f.subs(sust_pto))
                    val_R = float(R_f.subs(sust_pto)) if es_3d else 0.0
                    
                    es_equilibrio = np.isclose(val_P, 0, atol=1e-5) and np.isclose(val_Q, 0, atol=1e-5) and (not es_3d or np.isclose(val_R, 0, atol=1e-5))
                    if not es_equilibrio:
                        st.warning(rf"⚠️ El punto evaluado **NO es un punto de equilibrio** ($V \approx [{val_P:.3f}, {val_Q:.3f}{', '+str(round(val_R, 3)) if es_3d else ''}]$).")
                else:
                    st.write("El sistema es **Lineal**. El Jacobiano es la matriz constante $A$:")

                if es_3d:
                    A_eval = J_sym.subs({x_sym: x0_val, y_sym: y0_val, z_sym: z0_val})
                else:
                    A_eval = J_sym.subs({x_sym: x0_val, y_sym: y0_val})
                
                try:
                    traza = sp.simplify(A_eval.trace())
                    det = sp.simplify(A_eval.det())
                    
                    if es_3d:
                        c_eig1, c_eig2 = st.columns(2)
                        with c_eig1: st.latex(rf"\tau = {sp.latex(traza)}")
                        with c_eig2: st.latex(rf"\Delta = {sp.latex(det)}")
                    else:
                        disc = sp.simplify(traza**2 - 4*det)
                        c_eig1, c_eig2, c_eig3 = st.columns(3)
                        with c_eig1: st.latex(rf"\tau = {sp.latex(traza)}")
                        with c_eig2: st.latex(rf"\Delta = {sp.latex(det)}")
                        with c_eig3: st.latex(rf"\tau^2 - 4\Delta = {sp.latex(disc)}")

                    vectores_propios = A_eval.eigenvects()
                    real_parts = [float(sp.re(v[0])) for v in vectores_propios for _ in range(v[1])]
                    es_hiperbolico = all(not np.isclose(r, 0, atol=1e-5) for r in real_parts)
                    
                    if not es_lineal and es_equilibrio and not es_hiperbolico:
                        st.warning("⚠️ **Punto No Hiperbólico:** Al menos un valor propio tiene parte real cero.")

                    if not es_3d:
                        if np.isclose(float(det), 0, atol=1e
