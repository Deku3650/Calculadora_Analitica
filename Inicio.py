import streamlit as st

# 1. Configuración de la página
st.set_page_config(page_title="MATHESIS", layout="centered")

# CSS ligero para ajustar márgenes y estilo general (opcional)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1.5rem;}
    
    /* Estilo para ajustar el botón de redirección en Python */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
#  ENCABEZADO 
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
¡Bienvenidos a Mathesis! Selecciona cualquiera de los módulos para acceder directamente a la herramienta interactiva.

*📱 **Nota para celular:** Si no ves el menú de páginas, toca la pequeña flecha **( > )** en la esquina superior izquierda para desplegar los módulos.*
""")

st.write("")

# ==========================================
# MENÚ DE MÓDULOS 
# ==========================================
st.markdown("### MODULOS DISPONIBLES")

col1, col2 = st.columns(2)

with col1:
    # Módulo 1
    with st.container(border=True):
        st.caption("VISUALIZACIÓN")
        st.subheader("📐 Geometría")
        st.write("Áreas, volúmenes, modelado y visualización 3D interactiva.")
        if st.button("Abrir módulo", key="btn_geom", use_container_width=True):
            st.switch_page("pages/1_Geometria.py")

    # Módulo 2
    with st.container(border=True):
        st.caption("ÁLGEBRA LINEAL")
        st.subheader("🔄 Transformaciones Lineales")
        st.write("Núcleo, imagen, isomorfismos y matrices de cambio de base.")
        if st.button("Abrir módulo", key="btn_transf", use_container_width=True):
            st.switch_page("pages/2_Transformaciones.py")

    # Módulo 3
    with st.container(border=True):
        st.caption("ACTUARIAL")
        st.subheader("📈 Matemáticas Financieras")
        st.write("Plataforma actuarial de valuación, tasas equivalentes, escenarios dinámicos y cuadros de amortización.")
        if st.button("Abrir módulo", key="btn_fin", use_container_width=True):
            st.switch_page("pages/3_Financieras.py")

    # Módulo 4
    with st.container(border=True):
        st.caption("ANÁLISIS")
        st.subheader("💰 Economía y Microeconomía")
        st.write("Precio y cantidad de equilibrio, elasticidad, funciones de oferta y demanda, excedentes y análisis microeconómico.")
        if st.button("Abrir módulo", key="btn_econ", use_container_width=True):
            st.switch_page("pages/4_Economia.py")

with col2:
    # Módulo 5
    with st.container(border=True):
        st.caption("COMPUTACIÓN")
        st.subheader("🧮 Matrices")
        st.write("Operaciones lineales, determinantes, matrices Hessianas y análisis espectral.")
        if st.button("Abrir módulo", key="btn_mat", use_container_width=True):
            st.switch_page("pages/5_Matrices.py")

    # Módulo 6
    with st.container(border=True):
        st.caption("FUNDAMENTOS")
        st.subheader("🔢 Álgebra Superior")
        st.write("Aritmética modular, identidad de Bézout y números complejos.")
        if st.button("Abrir módulo", key="btn_alg_sup", use_container_width=True):
            st.switch_page("pages/6_Algebra_Superior.py")

    # Módulo 7
    with st.container(border=True):
        st.caption("SISTEMAS A|b")
        st.subheader("↗️ Vectores y Sistemas")
        st.write("Proyecciones, ángulos, Gram-Schmidt y resolución de sistemas lineales.")
        if st.button("Abrir módulo", key="btn_vect", use_container_width=True):
            st.switch_page("pages/7_Vectores.py")

    # Módulo 8
    with st.container(border=True):
        st.caption("AVANZADO")
        st.subheader("🌪️ Análisis Vectorial & Dinámico")
        st.write("Sistemas lineales y no lineales, retratos de fase, isoclinas y linealización Jacobiana en ℝ².")
        if st.button("Abrir módulo", key="btn_vec_dyn", use_container_width=True):
            st.switch_page("pages/8_Analisis_Vectorial.py")

st.write("---")

# ==========================================
# SECCIÓN ACERCA DE (100% PYTHON CONTENEDORES)
# ==========================================
st.markdown("## ℹ️ Acerca de MATHESIS")

st.markdown("""
**MATHESIS** es un proyecto computacional interactivo desarrollado para facilitar el análisis, 
la exploración intuitiva y la resolución práctica de modelos cuantitativos en **Álgebra, Geometría, 
Análisis Vectorial, Economía y Matemáticas Financieras**.
""")

st.markdown("#### Desarrolladores y Contacto")
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
