import streamlit as st
import sympy as sp
import math
from sympy.ntheory.modular import crt

try:
    from utils import leer_expresion_st 
except ImportError:
    st.error("Error crítico: No se pudo cargar el analizador matemático desde utils.py. Asegúrate de ejecutar la app desde el directorio raíz.")
    st.stop()

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Álgebra Superior - MATHESIS", page_icon="🔢", layout="wide")

if 'mis_complejos' not in st.session_state:
    st.session_state.mis_complejos = {}

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
        margin-bottom: 1rem !important;
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
        <h1 class="title-text">🔢 Módulo de Álgebra Superior</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("Teoría de Números, Aritmética Modular y Variable Compleja.")

tab_mcd, tab_euclides, tab_congruencias, tab_complejos = st.tabs([
    "MCD, mcm y Primos", 
    "Algoritmo de Euclides", 
    "Congruencias Lineales", 
    "Números Complejos"
])

# ==============================================================================
# PESTAÑA 1: MCD, mcm y Descomposición
# ==============================================================================
with tab_mcd:
    with st.container(border=True):
        st.markdown('<div class="card-header-title">Máximo Común Divisor y Mínimo Común Múltiplo</div>', unsafe_allow_html=True)
        
        entrada_nums = st.text_input("Ingrese un conjunto de números enteros positivos separados por comas (Ej: 12, 18, 24):")
        
        if st.button("Calcular MCD y mcm", use_container_width=True):
            if entrada_nums:
                try:
                    lista_numeros = [int(x.strip()) for x in entrada_nums.split(',') if int(x.strip()) != 0]
                    conjunto_limpio = list(set(lista_numeros))
                    
                    if len(conjunto_limpio) < 2:
                        st.error("Necesita al menos 2 números diferentes para operar.")
                    else:
                        resultado_mcd = math.gcd(*conjunto_limpio)
                        resultado_mcm = math.lcm(*conjunto_limpio)
                        
                        st.success(f"**Conjunto procesado:** {conjunto_limpio}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Máximo Común Divisor (MCD)", resultado_mcd)
                        with col2:
                            st.metric("Mínimo Común Múltiplo (mcm)", resultado_mcm)
                            
                        st.divider()
                        st.markdown('<div class="card-subheader-title">Descomposición en Factores Primos</div>', unsafe_allow_html=True)
                        
                        st.write("**Elementos del conjunto:**")
                        for n in conjunto_limpio:
                            factores = sp.factorint(n)
                            cadena_factores = " \\cdot ".join([f"{p}^{{{e}}}" if e > 1 else f"{p}" for p, e in factores.items()])
                            if n == 1: cadena_factores = "1"
                            st.latex(f"{n} = {cadena_factores}")
                            
                        st.write("**Resultados:**")
                        factores_mcd = sp.factorint(resultado_mcd)
                        cad_mcd = " \\cdot ".join([f"{p}^{{{e}}}" if e > 1 else f"{p}" for p, e in factores_mcd.items()])
                        st.latex(f"\\text{{MCD}} = {cad_mcd}")
                        
                        factores_mcm = sp.factorint(resultado_mcm)
                        cad_mcm = " \\cdot ".join([f"{p}^{{{e}}}" if e > 1 else f"{p}" for p, e in factores_mcm.items()])
                        st.latex(f"\\text{{mcm}} = {cad_mcm}")
                        
                except ValueError:
                    st.error("Error: Asegúrese de ingresar únicamente números enteros separados por comas.")

# ==============================================================================
# PESTAÑA 2: Algoritmo de Euclides
# ==============================================================================
with tab_euclides:
    with st.container(border=True):
        st.markdown('<div class="card-header-title">Algoritmo de Euclides Extendido</div>', unsafe_allow_html=True)
        st.markdown("Encuentra el MCD de $(a, b)$ y su Identidad de Bézout: $ax + by = \\text{MCD}$")
        
        col1, col2 = st.columns(2)
        with col1:
            a = st.number_input("Valor de 'a':", min_value=0, value=12, step=1)
        with col2:
            b = st.number_input("Valor de 'b':", min_value=0, value=8, step=1)
            
        if st.button("Aplicar Algoritmo", use_container_width=True):
            if a == 0 and b == 0:
                st.error("Ambos números no pueden ser cero.")
            else:
                x, y, mcd = sp.gcdex(a, b)
                st.success("Cálculo completado.")
                st.latex(f"\\text{{MCD}}({a}, {b}) = {mcd}")
                
                st.markdown('<div class="card-subheader-title">Identidad de Bézout (Mínima Combinación Lineal)</div>', unsafe_allow_html=True)
                signo_y = "+" if y >= 0 else "-"
                st.latex(f"({a})({x}) {signo_y} ({b})({abs(y)}) = {mcd}")

# ==============================================================================
# PESTAÑA 3: Congruencias
# ==============================================================================
with tab_congruencias:
    with st.container(border=True):
        st.markdown('<div class="card-header-title">Sistemas de Congruencias Lineales</div>', unsafe_allow_html=True)
        st.markdown("Resuelve sistemas de la forma: $cx \\equiv a \\pmod m$")
        
        cantidad_ec = st.number_input("¿Cuántas ecuaciones tiene su sistema?", min_value=1, max_value=10, value=2)
        
        residuos = []
        modulos = []
        sistema_valido = True
        
        with st.form("form_congruencias"):
            st.markdown('<div class="card-subheader-title">Parámetros del Sistema</div>', unsafe_allow_html=True)
            for i in range(int(cantidad_ec)):
                st.write(f"**Ecuación {i+1}**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    coef = st.number_input(f"Coeficiente (c)", value=1, key=f"c_{i}")
                with c2:
                    res = st.number_input(f"Residuo (a)", value=1, key=f"a_{i}")
                with c3:
                    mod = st.number_input(f"Módulo (m) [>1]", min_value=2, value=2, key=f"m_{i}")
                    
                d = math.gcd(coef, mod)
                if res % d != 0:
                    st.error(f"¡Alerta! La ecuación {i+1} no tiene solución. El sistema es incompatible.")
                    sistema_valido = False
                else:
                    c_simp, a_simp, m_simp = coef // d, res // d, mod // d
                    try:
                        inverso = pow(c_simp, -1, m_simp)
                        a_final = (a_simp * inverso) % m_simp
                        residuos.append(a_final)
                        modulos.append(m_simp)
                    except ValueError:
                        st.error(f"Error al calcular inverso en la ecuación {i+1}.")
                        sistema_valido = False
                        
            submit_cong = st.form_submit_button("Resolver Sistema", use_container_width=True)
            
        if submit_cong and sistema_valido:
            if cantidad_ec == 1:
                st.success("Solución de la congruencia única:")
                st.latex(f"x \\equiv {residuos[0]} \\pmod {{{modulos[0]}}}")
            else:
                resultado = crt(modulos, residuos)
                if resultado is None:
                    st.error("El sistema es INCOMPATIBLE.")
                else:
                    solucion_x, modulo_M = resultado
                    st.success("Solución general del sistema (Teorema Chino del Resto):")
                    st.latex(f"x \\equiv {solucion_x} \\pmod {{{modulo_M}}}")
                    st.info(f"Mínima solución positiva: x = {solucion_x}")

# ==============================================================================
# PESTAÑA 4: Números Complejos
# ==============================================================================
with tab_complejos:
    with st.container(border=True):
        st.markdown('<div class="card-header-title">Análisis de Variable Compleja</div>', unsafe_allow_html=True)
        
        col_def, col_op = st.columns(2)
        
        with col_def:
            st.markdown('<div class="card-subheader-title">1. Definir Nuevo Complejo</div>', unsafe_allow_html=True)
            with st.form("form_complejo"):
                nombre_c = st.text_input("Nombre de la variable (Ej: Z1):").upper().strip()
                expr_c = st.text_input("Expresión (Ej: 3 + 4*I):")
                
                if st.form_submit_button("Guardar Complejo", use_container_width=True):
                    if not nombre_c:
                        st.error("El nombre no puede estar vacío.")
                    else:
                        obj = leer_expresion_st(expr_c)
                        if obj is not None:
                            if not obj.has(sp.I):
                                st.warning("La expresión no contiene la unidad imaginaria 'I'.")
                            st.session_state.mis_complejos[nombre_c] = obj
                            st.success(f"Guardado: {nombre_c}")
                            
            st.markdown('<div class="card-subheader-title">Complejos en Memoria</div>', unsafe_allow_html=True)
            if st.session_state.mis_complejos:
                for nom, val in st.session_state.mis_complejos.items():
                    st.latex(f"{nom} = {sp.latex(val)}")
            else:
                st.caption("No hay complejos guardados aún.")
                
        with col_op:
            st.markdown('<div class="card-subheader-title">2. Operaciones</div>', unsafe_allow_html=True)
            if st.session_state.mis_complejos:
                complejo_seleccionado = st.selectbox("Seleccione un complejo:", list(st.session_state.mis_complejos.keys()))
                operacion_comp = st.radio("Operación:", ["Inverso", "Raíz Cuadrada", "Argumento", "Forma Polar", "Forma Trigonométrica"])
                
                if st.button("Calcular Operación", use_container_width=True):
                    z = st.session_state.mis_complejos[complejo_seleccionado]
                    
                    if operacion_comp == "Inverso":
                        res = sp.simplify(1/z)
                        st.latex(f"{complejo_seleccionado}^{{-1}} = {sp.latex(res)}")
                        
                    elif operacion_comp == "Raíz Cuadrada":
                        res = sp.simplify(sp.sqrt(z))
                        st.latex(f"\\sqrt{{{complejo_seleccionado}}} = {sp.latex(res)}")
                        
                    elif operacion_comp == "Argumento":
                        arg_rad = sp.simplify(sp.arg(z))
                        st.latex(f"\\theta = {sp.latex(arg_rad)} \\text{{ rad}}")
                        st.latex(f"\\theta = {sp.latex(sp.simplify(sp.deg(arg_rad)))}^{{\\circ}}")
                        
                    elif operacion_comp == "Forma Polar":
                        mod = sp.simplify(sp.Abs(z))
                        arg_rad = sp.simplify(sp.arg(z))
                        st.latex(f"{complejo_seleccionado} = {sp.latex(mod)} e^{{{sp.latex(arg_rad)} i}}")
                        
                    elif operacion_comp == "Forma Trigonométrica":
                        mod = sp.simplify(sp.Abs(z))
                        arg_rad = sp.simplify(sp.arg(z))
                        st.latex(f"{complejo_seleccionado} = {sp.latex(mod)} (\\cos({sp.latex(arg_rad)}) + i \\sin({sp.latex(arg_rad)}))")
            else:
                st.info("Defina un complejo a la izquierda para poder operar.")
