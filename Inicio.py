import matplotlib
matplotlib.use('Agg')  # Configuración para evitar problemas de memoria/display en servidores
import matplotlib.pyplot as plt
import streamlit as st

# ==========================================
# 1. Configuración de la página
# ==========================================
st.set_page_config(page_title="MATHESIS", layout="centered")

# ============================================
# CSS ADAPTATIVO PARA EL MODO CLARO Y OSCURO
# ============================================
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1.5rem;}
    
    /* Adaptación dinámica de contenedores (Cards de módulos) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        transition: all 0.25s ease-in-out !important;
        border: 1px solid rgba(128, 128, 128, 0.25) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }
    
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #0284c7 !important;
        box-shadow: 0 6px 18px rgba(2, 132, 199, 0.2) !important;
        transform: translateY(-2px);
    }

    /* Enlaces st.page_link estilizados */
    [data-testid="stPageLink-NavLink"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    [data-testid="stPageLink-NavLink"] p {
        color: #0284c7 !important;
        font-size: 19px !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stPageLink-NavLink"]:hover p {
        color: #6366f1 !important;
        text-decoration: underline !important;
    }
    
    /* Badges / Etiquetas superiores de cada tarjeta */
    .module-badge {
        background: rgba(2, 132, 199, 0.12);
        color: #0284c7;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 8px;
        border: 1px solid rgba(2, 132, 199, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        display: inline-block;
        margin-bottom: 6px;
    }

    /* Subtítulo de Menú de Opciones */
    .menu-header-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 25px;
        margin-bottom: 20px;
    }

    .menu-header-title {
        background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%);
        color: #ffffff !important;
        font-size: 16px;
        font-weight: 800;
        letter-spacing: 1.5px;
        padding: 8px 18px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
        text-transform: uppercase;
    }

    .menu-header-line {
        flex-grow: 1;
        height: 2px;
        background: linear-gradient(90deg, rgba(2, 132, 199, 0.4), transparent);
        border-radius: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ENCABEZADO 
# ==========================================
st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 32px 24px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
        margin-bottom: 25px;
        text-align: center;
    ">
        <span style="
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
            padding: 6px 14px;
            border-radius: 20px;
            text-transform: uppercase;
            display: inline-block;
            margin-bottom: 12px;
            border: 1px solid rgba(56, 189, 248, 0.4);
        ">🏛️ UNAM • Facultad de Ciencias • Actuaría</span>
        <h1 style="
            font-size: 50px;
            font-weight: 900;
            margin: 0;
            letter-spacing: 4px;
            background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.1;
        ">MATHESIS</h1>
        <p style="
            color: #cbd5e1;
            font-size: 17px;
            font-weight: 500;
            margin-top: 10px;
            margin-bottom: 0px;
        ">Matemáticas que se calculan, se exploran y se visualizan.</p>
    </div>
""", unsafe_allow_html=True)

st.markdown(
    "¡Bienvenidos a **MATHESIS**! Aquí encontrarás distintas herramientas para explorar, resolver y visualizar problemas matemáticos de forma interactiva."
)

st.markdown(
    "Toca el **nombre de cualquiera de los módulos** para acceder directamente a la herramienta interactiva."
)

# ==========================================
#  MENÚ DE MÓDULOS
# ==========================================
st.markdown("""
    <div class="menu-header-container">
        <div class="menu-header-title">📌 Menú de Opciones</div>
        <div class="menu-header-line"></div>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:

    with st.container(border=True):
        st.markdown('<span class="module-badge">Visualización</span>', unsafe_allow_html=True)
        st.page_link("pages/1_Geometria.py", label="📐 Geometría")
        st.caption("Áreas, volúmenes, modelado y visualización 3D interactiva.")

    with st.container(border=True):
        st.markdown('<span class="module-badge">Álgebra Lineal</span>', unsafe_allow_html=True)
        st.page_link("pages/3_Transformaciones.py", label="🔄 Transformaciones Lineales")
        st.caption("Núcleo, imagen, isomorfismos y matrices de cambio de base.")

    with st.container(border=True):
        st.markdown('<span class="module-badge">Actuarial</span>', unsafe_allow_html=True)
        st.page_link("pages/6_Matematicas_Financieras.py", label="📈 Matemáticas Financieras")
        st.caption("Plataforma actuarial de valuación, tasas equivalentes, escenarios dinámicos y cuadros de amortización.")

    with st.container(border=True):
        st.markdown('<span class="module-badge">Análisis</span>', unsafe_allow_html=True)
        st.page_link("pages/8_Economia_microeconomia.py", label="💰 Economía y Microeconomía")
        st.caption("Precio y cantidad de equilibrio, elasticidad, funciones de oferta y demanda, excedentes y análisis microeconómico.")

with col2:

    with st.container(border=True):
        st.markdown('<span class="module-badge">Computación</span>', unsafe_allow_html=True)
        st.page_link("pages/2_Matrices.py", label="🧮 Matrices")
        st.caption("Operaciones lineales, determinantes, matrices Hessianas y análisis espectral.")

    with st.container(border=True):
        st.markdown('<span class="module-badge">Fundamentos</span>', unsafe_allow_html=True)
        st.page_link("pages/4_Algebra_Superior.py", label="🔢 Álgebra Superior")
        st.caption("Aritmética modular, identidad de Bézout y números complejos.")

    with st.container(border=True):
        st.markdown('<span class="module-badge">Sistemas A|b</span>', unsafe_allow_html=True)
        st.page_link("pages/5_Vectores_Ecuaciones.py", label="↗️ Vectores y Sistemas")
        st.caption("Proyecciones, ángulos, Gram-Schmidt y resolución de sistemas lineales.")

    with st.container(border=True):
        st.markdown('<span class="module-badge">Avanzado</span>', unsafe_allow_html=True)
        st.page_link("pages/7_Ecuaciones_Diferenciales.py", label="🌪️ Análisis Vectorial & Dinámico")
        st.caption("Sistemas lineales y no lineales, retratos de fase, isoclinas y linealización Jacobiana en ℝ².")

st.write("---")

# ==========================================
# ACERCA DE
# ==========================================

st.markdown("---")

st.markdown("""
    <style>
    /* Estilos formales y sobrios */
    .formal-card {
        background-color: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-left: 4px solid #1e3a8a; /* Azul Institucional */
        padding: 20px 24px;
        border-radius: 8px;
        margin-bottom: 24px;
    }
    
    .formal-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 14px;
        letter-spacing: 0.5px;
    }
    
    .author-card {
        background-color: rgba(128, 128, 128, 0.03);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 8px;
        padding: 18px 20px;
        height: 100%;
    }

    .author-name {
        font-size: 17px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .author-affiliation {
        font-size: 13px;
        opacity: 0.85;
        margin-bottom: 10px;
        line-height: 1.4;
    }

    .author-email {
        font-size: 13px;
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="formal-title">ℹ️ Acerca de MATHESIS</div>', unsafe_allow_html=True)

st.markdown("""
    <div class="formal-card">
        <p style="margin: 0; font-size: 15px; line-height: 1.6;">
            <b>MATHESIS</b> es un entorno computacional interactivo diseñado para facilitar el análisis, la exploración cuantitativa y la resolución práctica de modelos matemáticos aplicados en <b>Álgebra, Geometría, Análisis Vectorial, Economía y Matemáticas Financieras</b>.
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
                Licenciatura en Actuaría<br>
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
                Licenciatura en Actuaría<br>
                Facultad de Ciencias, UNAM
            </div>
            <div class="author-email">✉️ i.rebecaorfi@ciencias.unam.mx</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")

st.markdown("""
    <div style="text-align: center; font-size: 12px; opacity: 0.75; padding-top: 20px; border-top: 1px solid rgba(128, 128, 128, 0.2);">
        MATHESIS © 2026 • Universidad Nacional Autónoma de México • Facultad de Ciencias
    </div>
""", unsafe_allow_html=True)
