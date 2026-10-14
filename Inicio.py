import streamlit as st
from estilos import cargar_estilos_globales
from utils import inicializar_estado

# ==========================================
# 1. Configuración de la página y estilos
# ==========================================
st.set_page_config(page_title="MATHESIS", page_icon="🏛️", layout="centered")
cargar_estilos_globales()
inicializar_estado()

# ==========================================
# ENCABEZADO ADAPTATIVO
# ==========================================
st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%);
        padding: 32px 24px;
        border-radius: 20px;
        border: 1px solid rgba(2, 132, 199, 0.25);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        margin-bottom: 25px;
        text-align: center;
    ">
        <span style="
            background: rgba(56, 189, 248, 0.15);
            color: #0284c7;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
            padding: 6px 14px;
            border-radius: 20px;
            text-transform: uppercase;
            display: inline-block;
            margin-bottom: 12px;
            border: 1px solid rgba(2, 132, 199, 0.3);
        ">🏛️ UNAM • Facultad de Ciencias • Actuaría</span>
        <h1 style="
            font-size: 50px;
            font-weight: 900;
            margin: 0;
            letter-spacing: 4px;
            background: linear-gradient(90deg, #0284c7, #6366f1, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.1;
        ">MATHESIS</h1>
        <p style="
            font-size: 17px;
            font-weight: 600;
            margin-top: 10px;
            margin-bottom: 0px;
            opacity: 0.85;
        ">Matemáticas que se calculan, se exploran y se visualizan.</p>
    </div>
""", unsafe_allow_html=True)

st.markdown(
    "¡Bienvenidos a **MATHESIS**! Aquí encontrarás distintas herramientas para explorar, resolver y visualizar problemas matemáticos y actuariales de forma interactiva."
)
st.markdown(
    "Toca el **nombre de cualquiera de los módulos** para acceder directamente a la herramienta interactiva."
)

# ==========================================
# MENÚ DE MÓDULOS
# ==========================================
st.markdown("""
    <div class="menu-header-container">
        <div class="menu-header-title">📌 Menú de Opciones</div>
        <div class="menu-header-line"></div>
    </div>
""", unsafe_allow_html=True)

# Tarjeta destacada de Cálculo (Nuevo en V0.2)
with st.container(border=True):
    st.markdown('<span class="module-badge">✨ Nuevo en V0.2 • Con Teclado Matemático</span>', unsafe_allow_html=True)
    st.page_link("pages/9_Calculo.py", label="∑ Cálculo Diferencial, Integral y Multivariable")
    st.caption(
        "Intérprete en español con teclado interactivo: dominio, límites 1D y multivariable, continuidad, derivadas, "
        "gradiente, Hessiana, multiplicadores de Lagrange, integrales múltiples, series, Taylor y superficies 3D."
    )

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Geometría 2D / 3D</span>', unsafe_allow_html=True)
        st.page_link("pages/1_Geometria.py", label="📐 Geometría")
        st.caption("Áreas, volúmenes, geometría analítica y visualización 3D interactiva.")

    with st.container(border=True):
        st.markdown('<span class="module-badge">Álgebra Lineal</span>', unsafe_allow_html=True)
        st.page_link("pages/3_Transformaciones.py", label="🔄 Transformaciones Lineales")
        st.caption("Núcleo, imagen, isomorfismos, composición, espacio dual y matrices de cambio de base.")

    with st.container(border=True):
        st.markdown('<span class="module-badge">Finanzas y Actuaría</span>', unsafe_allow_html=True)
        st.page_link("pages/6_Matematicas_Financieras.py", label="📈 Matemáticas Financieras")
        st.caption("Plataforma actuarial de valuación, tasas equivalentes, escenarios dinámicos y cuadros de amortización.")

    with st.container(border=True):
        st.markdown('<span class="module-badge">Teoría Económica</span>', unsafe_allow_html=True)
        st.page_link("pages/8_Economia_microeconomia.py", label="📊 Economía y Microeconomía")
        st.caption("Precio y cantidad de equilibrio, excedentes, elasticidad, impuestos y óptimo del consumidor.")

with col2:
    with st.container(border=True):
        st.markdown('<span class="module-badge">Álgebra Lineal</span>', unsafe_allow_html=True)
        st.page_link("pages/2_Matrices.py", label="🧮 Matrices")
        st.caption("Operaciones lineales, determinantes, RREF, matrices Hessianas, Jacobianas y análisis espectral.")

    with st.container(border=True):
        st.markdown('<span class="module-badge">Fundamentos</span>', unsafe_allow_html=True)
        st.page_link("pages/4_Algebra_Superior.py", label="🔢 Álgebra Superior")
        st.caption("Teoría de números, algoritmo de Euclides, identidad de Bézout, congruencias y números complejos.")

    with st.container(border=True):
        st.markdown('<span class="module-badge">Álgebra Lineal</span>', unsafe_allow_html=True)
        st.page_link("pages/5_Vectores_Ecuaciones.py", label="↗️ Vectores y Sistemas")
        st.caption("Proyecciones, ángulos, ortogonalización de Gram-Schmidt y sistemas de ecuaciones lineales.")

    with st.container(border=True):
        st.markdown('<span class="module-badge">Sistemas Dinámicos</span>', unsafe_allow_html=True)
        st.page_link("pages/7_Ecuaciones_Diferenciales.py", label="🌪️ Ecuaciones Diferenciales")
        st.caption("Sistemas lineales y no lineales, retratos de fase, ceroclinas, plano Traza-Det y EDOs de 1er orden.")

# ==========================================
# ACERCA DE
# ==========================================
st.markdown("---")
st.markdown('<div class="formal-title">ℹ️ Acerca de MATHESIS</div>', unsafe_allow_html=True)

st.markdown("""
    <div class="formal-card">
        <p style="margin: 0; font-size: 15px; line-height: 1.6;">
            <b>MATHESIS</b> es un entorno computacional interactivo diseñado para facilitar el análisis, la exploración cuantitativa y la resolución práctica de modelos matemáticos aplicados en <b>Cálculo, Álgebra, Geometría, Sistemas Dinámicos, Economía y Matemáticas Financieras</b>.
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("##### **Desarrolladores del Programa**")

col_dev1, col_dev2 = st.columns(2)

with col_dev1:
    st.markdown("""
        <div class="author-card">
            <div class="author-name">José Alberto Fernández Cendejas</div>
            <div class="author-affiliation">
                Estudiante de Actuaría<br>
                Facultad de Ciencias, UNAM
            </div>
            <div class="author-email">✉️ jose.fernandezcendejas@ciencias.unam.mx</div>
        </div>
    """, unsafe_allow_html=True)

with col_dev2:
    st.markdown("""
        <div class="author-card">
            <div class="author-name">Ingrid Rebeca Ortega Flores</div>
            <div class="author-affiliation">
                Estudiante de Actuaría<br>
                Facultad de Ciencias, UNAM
            </div>
            <div class="author-email">✉️ i.rebecaorfi@ciencias.unam.mx</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")
st.markdown("""
    <div style="text-align: center; font-size: 12px; opacity: 0.75; padding-top: 20px; border-top: 1px solid rgba(2, 132, 199, 0.2);">
        MATHESIS © 2026 • Universidad Nacional Autónoma de México • Facultad de Ciencias
    </div>
""", unsafe_allow_html=True)
