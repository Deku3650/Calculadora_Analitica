import streamlit as st

# 1. Configuración de la página 
st.set_page_config(page_title="MATHESIS", layout="centered")

# CSS personalizado para la estética general y las tarjetas de módulos
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1.5rem;}
    
    /* Estilo de tarjeta para los módulos */
    .module-card {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
        height: 100%;
    }
    
    .module-card:hover {
        border-color: #38bdf8;
        transform: translateY(-2px);
    }
    
    .module-title {
        color: #f8fafc;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .module-desc {
        color: #94a3b8;
        font-size: 14px;
        line-height: 1.5;
        margin: 0;
    }

    .module-badge {
        background-color: rgba(56, 189, 248, 0.1);
        color: #38bdf8;
        font-size: 10px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid rgba(56, 189, 248, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        float: right;
    }

    /* Tarjetas de desarrolladores */
    .about-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        margin-top: 10px;
        margin-bottom: 15px;
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
¡Bienvenidos a Mathesis! Aquí encontrarás distintas herramientas para explorar, resolver y visualizar problemas matemáticos de forma interactiva.

*📱 **Nota para celular:** Si no ves el menú de páginas, toca la pequeña flecha **( > )** en la esquina superior izquierda para desplegar los módulos.*
""")

st.write("")

# ==========================================
# MENU DE MODULOS
# ==========================================
st.markdown("### Módulos Disponibles")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="module-card">
        <span class="module-badge">Visualización</span>
        <div class="module-title">📐 Geometría</div>
        <p class="module-desc">Áreas, volúmenes, modelado y visualización 3D interactiva.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="module-card">
        <span class="module-badge">Álgebra Lineal</span>
        <div class="module-title">🔄 Transformaciones Lineales</div>
        <p class="module-desc">Núcleo, imagen, isomorfismos y matrices de cambio de base.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="module-card">
        <span class="module-badge">Actuarial</span>
        <div class="module-title">📈 Matemáticas Financieras</div>
        <p class="module-desc">Plataforma actuarial de valuación, tasas equivalentes, escenarios dinámicos y cuadros de amortización.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="module-card">
        <span class="module-badge">Análisis</span>
        <div class="module-title">💰 Economía y Microeconomía</div>
        <p class="module-desc">Precio y cantidad de equilibrio, elasticidad, funciones de oferta y demanda, excedentes y análisis microeconómico.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="module-card">
        <span class="module-badge">Computación</span>
        <div class="module-title">🧮 Matrices</div>
        <p class="module-desc">Operaciones lineales, determinantes, matrices Hessianas y análisis espectral.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="module-card">
        <span class="module-badge">Fundamentos</span>
        <div class="module-title">🔢 Álgebra Superior</div>
        <p class="module-desc">Aritmética modular, identidad de Bézout y números complejos.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="module-card">
        <span class="module-badge">Sistemas A|b</span>
        <div class="module-title">↗️ Vectores y Sistemas</div>
        <p class="module-desc">Proyecciones, ángulos, Gram-Schmidt y resolución de sistemas lineales.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="module-card">
        <span class="module-badge">Avanzado</span>
        <div class="module-title">🌪️ Análisis Vectorial & Dinámico</div>
        <p class="module-desc">Sistemas lineales y no lineales, retratos de fase, isoclinas y linealización Jacobiana en ℝ².</p>
    </div>
    """, unsafe_allow_html=True)

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
    st.markdown("""
    <div class="about-card">
        <h4 style="margin: 0; color: #38bdf8;">👨‍💻 José Alberto Fernández Cendejas</h4>
        <p style="color: #94a3b8; font-size: 13px; margin-top: 5px; margin-bottom: 10px;">Licenciatura en Actuaría — UNAM</p>
        <p style="font-size: 13px; color: #cbd5e1; margin: 0;">
            ✉️ <b>Correo:</b> <a href="mailto:jose.fernandezcendejas@ciencias.unam.mx" style="color: #38bdf8; text-decoration: none;">jose.fernandezcendejas@ciencias.unam.mx</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_dev2:
    st.markdown("""
    <div class="about-card">
        <h4 style="margin: 0; color: #38bdf8;">👩‍💻 Ingrid Rebeca Ortega Flores</h4>
        <p style="color: #94a3b8; font-size: 13px; margin-top: 5px; margin-bottom: 10px;">Licenciatura en Actuaría — UNAM</p>
        <p style="font-size: 13px; color: #cbd5e1; margin: 0;">
            ✉️ <b>Correo:</b> <a href="mailto:i.rebecaorfi@ciencias.unam.mx" style="color: #38bdf8; text-decoration: none;">i.rebecaorfi@ciencias.unam.mx</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

st.caption("MATHESIS © 2026 — Facultad de Ciencias, UNAM")
