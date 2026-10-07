import streamlit as st

# 1. Configuración de la página
st.set_page_config(
    page_title="MATHESIS", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS optimizado para compatibilidad táctil móvil
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1.5rem;}
    
    /* Contenedor neón de las tarjetas */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%) !important;
        border: 1px solid #334155 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
        margin-bottom: 12px;
    }
    
    /* Botones nativos convertidos en enlaces neón de alto impacto táctil */
    div.stButton > button {
        width: 100% !important;
        background: transparent !important;
        color: #38bdf8 !important;
        border: 1px solid #38bdf8 !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        border-radius: 10px !important;
        padding: 10px 16px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        box-shadow: none !important;
    }

    div.stButton > button:active, div.stButton > button:focus {
        background-color: rgba(56, 189, 248, 0.2) !important;
        color: #818cf8 !important;
        border-color: #818cf8 !important;
    }

    /* Etiqueta / Badge superior */
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
        margin-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
#  ENCABEZADO DESTACADO (HERO BANNER)
# ==========================================
st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f172a 100%);
        padding: 30px 20px;
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
            font-size: 44px;
            font-weight: 900;
            margin: 0;
            letter-spacing: 3px;
            background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.1;
        ">MATHESIS</h1>
        <p style="
            color: #e2e8f0;
            font-size: 16px;
            font-weight: 500;
            margin-top: 12px;
            margin-bottom: 0px;
        ">Matemáticas que se calculan, se exploran y se visualizan.</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("¡Bienvenidos a Mathesis! Toca cualquiera de los módulos para acceder a la herramienta interactiva.")

st.write("")

# ==========================================
# MENÚ DE MÓDULOS (COMPATIBILIDAD MÓVIL TOTAL)
# ==========================================
st.markdown("### 🛠️ Módulos Disponibles")

col1, col2 = st.columns(2)

with col1:
    # Módulo 1
    with st.container(border=True):
        st.markdown('<span class="module-badge">Visualización</span>', unsafe_allow_html=True)
        if st.button("📐 Geometría", use_container_width=True, key="btn_geom"):
            st.switch_page("pages/1_Geometria.py")
        st.caption("Áreas, volúmenes, modelado y visualización 3D interactiva.")

    # Módulo 2
    with st.container(border=True):
        st.markdown('<span class="module-badge">Álgebra Lineal</span>', unsafe_allow_html=True)
        if st.button("🔄 Transformaciones Lineales", use_container_width=True, key="btn_trans"):
            st.switch_page("pages/3_Transformaciones.py")
        st.caption("Núcleo, imagen, isomorfismos y matrices de cambio de base.")

    # Módulo 3
    with st.container(border=True):
        st.markdown('<span class="module-badge">Actuarial</span>', unsafe_allow_html=True)
        if st.button("📈 Matemáticas Financieras", use_container_width=True, key="btn_fin"):
            st.switch_page("pages/6_Matematicas_Financieras.py")
        st.caption("Plataforma actuarial de valuación, tasas equivalentes, escenarios dinámicos y cuadros de amortización.")

    # Módulo 4
    with st.container(border=True):
        st.markdown('<span class="module-badge">Análisis</span>', unsafe_allow_html=True)
        if st.button("💰 Economía y Microeconomía", use_container_width=True, key="btn_econ"):
            st.switch_page("pages/8_Economia_microeconomia.py")
        st.caption("Precio y cantidad de equilibrio, elasticidad, funciones de oferta y demanda, excedentes y análisis microeconómico.")

with col2:
    # Módulo 5
    with st.container(border=True):
        st.markdown('<span class="module-badge">Computación</span>', unsafe_allow_html=True)
        if st.button("🧮 Matrices", use_container_width=True, key="btn_mat"):
            st.switch_page("pages/2_Matrices.py")
        st.caption("Operaciones lineales, determinantes, matrices Hessianas y análisis espectral.")

    # Módulo 6
    with st.container(border=True):
        st.markdown('<span class="module-badge">Fundamentos</span>', unsafe_allow_html=True)
        if st.button("🔢 Álgebra Superior", use_container_width=True, key="btn_alg"):
            st.switch_page("pages/4_Algebra_Superior.py")
        st.caption("Aritmética modular, identidad de Bézout y números complejos.")

    # Módulo 7
    with st.container(border=True):
        st.markdown('<span class="module-badge">Sistemas A|b</span>', unsafe_allow_html=True)
        if st.button("↗️ Vectores y Sistemas", use_container_width=True, key="btn_vec"):
            st.switch_page("pages/5_Vectores_Ecuaciones.py")
        st.caption("Proyecciones, ángulos, Gram-Schmidt y resolución de sistemas lineales.")

    # Módulo 8
    with st.container(border=True):
        st.markdown('<span class="module-badge">Avanzado</span>', unsafe_allow_html=True)
        if st.button("🌪️ Análisis Vectorial & Dinámico", use_container_width=True, key="btn_ec"):
            st.switch_page("pages/7_Ecuaciones_Diferenciales.py")
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
