# Inicio.py
import os
import streamlit as st

st.set_page_config(
    page_title="MATHESIS - Plataforma Interactiva",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from estilos import cargar_estilos_globales  # noqa: E402
from utils import inicializar_estado  # noqa: E402

cargar_estilos_globales()
inicializar_estado()


def _enlace_modulo(ruta: str, titulo: str):
    """Muestra st.page_link si el archivo existe en disco, o el título estilizado si está próximo a integrarse."""
    if os.path.exists(ruta):
        st.page_link(ruta, label=titulo)
    else:
        st.markdown("**" + titulo + "** *(Próximo módulo V0.3)*")


# ==============================================================================
# 1. BANNER PRINCIPAL (HERO)
# ==============================================================================
st.markdown(
    """
    <div class="hero-banner">
        <div class="hero-badge">FACULTAD DE CIENCIAS • UNAM</div>
        <h1 class="hero-title">MATHESIS</h1>
        <p class="hero-subtitle">Plataforma Interactiva de Matemáticas, Finanzas, Economía y Ciencias Actuariales</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# 2. CATÁLOGO DE MÓDULOS INTERACTIVOS
# ==============================================================================
st.markdown(
    """
    <div class="menu-header-container">
        <span class="menu-header-title">Explorar Módulos Interactivos</span>
        <div class="menu-header-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Fila 1 de módulos (Módulos 1, 2 y 3)
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Módulo 01 • Geometría Analítica I y II</span>', unsafe_allow_html=True)
        _enlace_modulo("pages/1_Geometria.py", "📐 Geometría y Analítica")
        st.caption(
            "Triángulos con puntos notables y recta de Euler, sólidos 3D, rectas, cónicas con rotación de ejes y geometría en ℝ³."
        )

with col2:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Módulo 02 • Álgebra Lineal I</span>', unsafe_allow_html=True)
        _enlace_modulo("pages/2_Matrices.py", "🔢 Matrices y Factorizaciones")
        st.caption(
            "Álgebra matricial simbólica, determinantes, eigenvalores, diagonalización, factorización LU, SVD y formas cuadráticas."
        )

with col3:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Módulo 03 • Álgebra Lineal I y II</span>', unsafe_allow_html=True)
        _enlace_modulo("pages/3_Transformaciones.py", "🔄 Transformaciones Lineales")
        st.caption(
            "Núcleo, imagen, teorema de la dimensión, cambio de base, base dual, geometría 2D y polinomio característico."
        )

# Fila 2 de módulos (Módulos 4, 5 y 6)
col4, col5, col6 = st.columns(3)

with col4:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Módulo 04 • Álgebra Superior I y II</span>', unsafe_allow_html=True)
        _enlace_modulo("pages/4_Algebra_Superior.py", "🔣 Álgebra Superior")
        st.caption(
            "Combinatoria y Binomio de Newton, teoría de números (Euclides), números complejos (De Moivre) y polinomios."
        )

with col5:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Módulo 05 • Geometría Analítica y Lineal</span>', unsafe_allow_html=True)
        _enlace_modulo("pages/5_Vectores_Ecuaciones.py", "🧭 Vectores y Sistemas Lineales")
        st.caption(
            "Álgebra vectorial, producto mixto, ortogonalización de Gram-Schmidt, proyección a subespacios y Rouché-Frobenius."
        )

with col6:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Módulo 06 • Matemáticas Financieras</span>', unsafe_allow_html=True)
        _enlace_modulo("pages/6_Matematicas_Financieras.py", "💰 Matemáticas Financieras")
        st.caption(
            "Tasas equivalentes, anualidades constantes y variables, amortización, valuación de bonos (duración/convexidad) y VPN/TIR."
        )

# Fila 3 de módulos (Módulos 7, 8 y 9)
col7, col8, col9 = st.columns(3)

with col7:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Módulo 07 • Ecuaciones Diferenciales I</span>', unsafe_allow_html=True)
        _enlace_modulo("pages/7_Ecuaciones_Diferenciales.py", "📈 Ecuaciones Diferenciales")
        st.caption(
            "Sistemas dinámicos 2D, retrato de fase, diagrama traza-determinante, EDOs de 1.º y 2.º orden y Transformada de Laplace."
        )

with col8:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Módulo 08 • Teoría Económica</span>', unsafe_allow_html=True)
        _enlace_modulo("pages/8_Economia_microeconomia.py", "⚖️ Economía y Microeconomía")
        st.caption(
            "Equilibrio de Marshall, excedentes, impuestos y peso muerto, estructura de costos y optimización del consumidor."
        )

with col9:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Módulo 09 • Cálculo I a IV</span>', unsafe_allow_html=True)
        _enlace_modulo("pages/9_Calculo.py", "∑ Cálculo, Conjuntos y Lógica")
        st.caption(
            "Teclado matemático interactivo: análisis de funciones en ℝ y ℝⁿ, límites, derivadas, integrales, series, topología y lógica."
        )

# Fila 4 de módulos (Módulos 10 y 11)
col10, col11, col12 = st.columns(3)

with col10:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Módulo 10 • Probabilidad I y II</span>', unsafe_allow_html=True)
        _enlace_modulo("pages/10_Probabilidad.py", "🎲 Probabilidad y Distribuciones")
        st.caption(
            "Distribuciones discretas y continuas, momentos, cuantiles, vectores aleatorios y simulación Monte Carlo."
        )

with col11:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Módulo 11 • Cálculo Actuarial I</span>', unsafe_allow_html=True)
        _enlace_modulo("pages/11_Calculo_Actuarial.py", "🛡️ Cálculo Actuarial (Vida)")
        st.caption(
            "Tablas de mortalidad (Makeham/CNSF), valores conmutados, seguros de vida, anualidades contingentes y reservas."
        )

with col12:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Memoria Compartida • Sesión Activa</span>', unsafe_allow_html=True)
        st.markdown("**🔗 Ecosistema Integrado**")
        n_mat = len(st.session_state.get("mis_matrices", {}))
        n_vec = len(st.session_state.get("mis_vectores", {}))
        n_tl = len(st.session_state.get("mis_transformaciones", {}))
        st.caption(
            f"Inventario activo en memoria: {n_mat} matriz(ces), {n_vec} vector(es) y {n_tl} transformación(es) disponibles entre módulos."
        )

st.write("")


# ==============================================================================
# 3. PRESENTACIÓN Y CRÉDITOS INSTITUCIONALES
# ==============================================================================
st.markdown(
    """
    <div class="formal-card">
        <div class="formal-title">Acerca de Mathesis</div>
        <p style="margin-bottom: 10px;">
            <strong>MATHESIS</strong> es una herramienta computacional interactiva desarrollada en la
            <strong>Facultad de Ciencias de la Universidad Nacional Autónoma de México (UNAM)</strong>.
        </p>
        <p style="margin-bottom: 0;">
            Es un entorno computacional interactivo diseñado para facilitar el análisis, la exploración cuantitativa y 
            la resolución práctica de modelos matemáticos aplicados en <b>Cálculo, Álgebra Lineal, Geometría, Sistemas Dinámicos, Economía y Matemáticas Financieras.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### 👥 Autores y Desarrolladores")
c_aut1, c_aut2 = st.columns(2)

with c_aut1:
    st.markdown(
        """
        <div class="author-card">
            <div class="author-name">José Alberto Fernández Cendejas</div>
            <div class="author-affiliation">
                Estudiante de Actuaría<br>
                Facultad de Ciencias, UNAM
            </div>
            <div class="author-email">🏛️ Universidad Nacional Autónoma de México</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c_aut2:
    st.markdown(
        """
        <div class="author-card">
            <div class="author-name">Ingrid Rebeca Ortega Flores</div>
            <div class="author-affiliation">
                Estudiante de Actuaría<br>
                Facultad de Ciencias, UNAM
            </div>
            <div class="author-email">🏛️ Universidad Nacional Autónoma de México</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
st.markdown(
    """
    <div class="footer-copy">
        MATHESIS V0.3 • Facultad de Ciencias, UNAM • Desarrollado con Python, SymPy, NumPy, SciPy, Matplotlib y Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
