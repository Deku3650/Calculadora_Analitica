import streamlit as st

# 1. Configuración de la página 
st.set_page_config(page_title="MATHESIS", layout="centered")

# Quitamos el bloqueo del header para que SIEMPRE aparezca la flecha del menú en celulares
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1.5rem;}
    .about-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 18px;
        margin-top: 10px;
        margin-bottom: 15px;
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
        margin-bottom: 30px;
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
            margin-bottom: 16px;
        ">Matemáticas que se calculan, se exploran y se visualizan.</p>
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background-color: rgba(15, 23, 42, 0.7);
            padding: 6px 16px;
            border-radius: 12px;
            border: 1px solid #334155;
            color: #94a3b8;
            font-size: 13px;
        ">
            👨‍💻 Desarrollado por: <strong style="color: #38bdf8;">José Fernández</strong> y <strong style="color: #38bdf8;">Rebeca Ortega</strong>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
¡Bienvenidos a Mathesis! Aquí encontrarás distintas herramientas para explorar, resolver y visualizar problemas matemáticos de forma interactiva.

*📱 **Nota para celular:** Si no ve el menú de páginas, toque la pequeña flecha **( > )** en la esquina superior izquierda para desplegar los módulos.*
""")

st.write("")
st.write("")

# 3. Menús con los que contamos
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <ul style="list-style-type: disc; margin-left: 15px; padding-left: 0;">
        <li style="color: #ffffff; margin-bottom: 25px;">
            <strong style="font-size: 17px;">📐 Geometría:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 4px;">
                Áreas, volúmenes, modelado y visualización 3D interactiva.
            </span>
        </li>
        <li style="color: #ffffff; margin-bottom: 25px;">
            <strong style="font-size: 17px;">🔄 Transformaciones Lineales:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 4px;">
                Núcleo, imagen, isomorfismos y matrices de cambio de base.
            </span>
        </li>
        <li style="color: #ffffff; margin-bottom: 25px;">
            <strong style="font-size: 17px;">📈 Matemáticas Financieras:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 4px;">
                Plataforma actuarial de valuación, tasas equivalentes, escenarios dinámicos y cuadros de amortización.
            </span>
        </li>
         <li style="color: #ffffff; margin-bottom: 25px;"> 
            <strong style="font-size: 17px;">💰 Economía y Microeconomía:</strong><br> 
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 4px;"> 
                Cálculo del precio y cantidad de equilibrio, elasticidad, funciones de oferta y demanda, excedentes y análisis microeconómico. </span> 
        </li>
    </ul>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <ul style="list-style-type: disc; margin-left: 15px; padding-left: 0;">
        <li style="color: #ffffff; margin-bottom: 25px;">
            <strong style="font-size: 17px;">🧮 Matrices:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 4px;">
                Operaciones lineales, determinantes, matrices Hessianas y análisis espectral.
            </span>
        </li>
        <li style="color: #ffffff; margin-bottom: 25px;">
            <strong style="font-size: 17px;">🔢 Álgebra Superior:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 4px;">
                Aritmética modular, identidad de Bézout y números complejos.
            </span>
        </li>
        <li style="color: #ffffff; margin-bottom: 25px;">
            <strong style="font-size: 17px;">↗️ Vectores y Sistemas:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 4px;">
                Proyecciones, ángulos, Gram-Schmidt y resolución de sistemas lineales [A|b].
            </span>
        </li>
        <li style="color: #ffffff; margin-bottom: 25px;">
            <strong style="font-size: 17px;">🌪️ Análisis Vectorial y Sistemas Dinámicos:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 4px;">
                Estudio de sistemas lineales y no lineales, retratos de fase, isoclinas y linealización Jacobiana en R<sup>2</sup>.
            </span>
        </li>
    </ul>
    """, unsafe_allow_html=True)

st.write("---")

# 4. Sección "Acerca de MATHESIS"
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
