import streamlit as st

# 1. Configuración de la página
st.set_page_config(page_title="MATHESIS", layout="centered")

# CSS para darle el estilo neón/oscuro a los st.container nativos de Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1.5rem;}
    
    /* Personalizar los contenedores nativos de Streamlit para darles aspecto neón/oscuro */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%) !important;
        border: 1px solid #334155 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.25s ease-in-out !important;
    }
    
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #38bdf8 !important;
        box-shadow: 0 8px 22px rgba(56, 189, 248, 0.25) !important;
    }

    /* Estilar el enlace nativo st.page_link para que parezca el título interactivo */
    [data-testid="stPageLink-NavLink"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    [data-testid="stPageLink-NavLink"] p {
        color: #38bdf8 !important;
        font-size: 20px !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stPageLink-NavLink"]:hover p {
        color: #818cf8 !important;
        text-decoration: underline !important;
    }
    
    /* Estilo del Badge/Etiqueta superior */
    .module-badge {
        background: linear-gradient(90deg, rgba(56, 189, 248, 0.15), rgba(129, 140, 248, 0.15));
        color: #38bdf8;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 8px;
        border: 1px solid rgba(56, 189, 248, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        display: inline-block;
        margin-bottom: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
#  ENCABEZADO DESTACADO (HERO BANNER)
# ==========================================
st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f172a 100%);
        padding: 35px 25px;
        border-radius: 20px;
        border: 1px solid #334155;
        border-left: 6px solid #38bdf8;
        box-shadow: 0 12px 28px -6px rgba(0, 0, 0, 0.6);
        margin-bottom: 25px;
        text-align: center;
    ">
        <span style="
            background: linear-gradient(90deg, #0284c7, #0369a1);
            color: #f0f9ff;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.8px;
            padding: 5px 14px;
            border-radius: 20px;
            text-transform: uppercase;
            display: inline-block;
            margin-bottom: 14px;
            border: 1px solid #38bdf8;
        ">🏛️ UNAM • Facultad de Ciencias • Actuaría</span>
        <h1 style="
            font-size: 52px;
            font-weight: 900;
            margin: 0;
            letter-spacing: 4px;
            background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.1;
        ">MATHESIS</h1>
        <p style="
            color: #e2e8f0;
            font-size: 18px;
            font-weight: 500;
            margin-top: 12px;
            margin-bottom: 0px;
        ">Matemáticas que se calculan, se exploran y se visualizan.</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
¡Bienvenidos a Mathesis! Toca el **nombre de cualquiera de los módulos** para acceder directamente a la herramienta interactiva.
""")

st.write("")

# ==========================================
# MENÚ DE MÓDULOS (COMPATIBLE AL 100% CON MÓVILES)
# ==========================================
st.markdown("### 🛠️ Módulos Disponibles")

col1, col2 = st.columns(2)

with col1:
    # Módulo 1
    with st.container(border=True):
        st.markdown('<span class="module-badge">Visualización</span>', unsafe_allow_html=True)
        st.page_link("pages/1_Geometria.py", label="📐 Geometría")
        st.caption("Áreas, volúmenes, modelado y visualización 3D interactiva.")

    # Módulo 2
    with st.container(border=True):
        st.markdown('<span class="module-badge">Álgebra Lineal</span>', unsafe_allow_html=True)
        st.page_link("pages/3_Transformaciones.py", label="🔄 Transformaciones Lineales")
        st.caption("Núcleo, imagen, isomorfismos y matrices de cambio de base.")

    # 
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
# SECCIÓN ACERCA DE
# ==========================================
st.markdown("## ℹ️ Acerca de MATHESIS")

st.markdown("""
**MATHESIS** es un proyecto computacional interactivo desarrollado para facilitar el análisis, 
la exploración intuitiva y la resolución práctica de modelos cuantitativos en **Álgebra, Geometría, 
Análisis Vectorial, Economía y Matemáticas Financieras**.
""")

st.markdown("#### 🏛️ Desarrolladores y Contacto")
st.markdown("Estudiantes de la Licenciatura en **Actuaría** | **Facultad de Ciencias, UNAM**")

col_dev1, col_dev2 = st.columns(2)

with col_dev1:
    with st.container(border=True):
        st.markdown("#### José Alberto Fernández Cendejas")
        st.caption("Licenciatura en Actuaría — UNAM")
        st.write("✉️ **Correo:** jose.fernandezcendejas@ciencias.unam.mx")

with col_dev2:
    with st.container(border=True):
        st.markdown("#### Ingrid Rebeca Ortega Flores")
        st.caption("Licenciatura en Actuaría — UNAM")
        st.write("✉️ **Correo:** i.rebecaorfi@ciencias.unam.mx")

st.caption("MATHESIS © 2026 — Facultad de Ciencias, UNAM")
