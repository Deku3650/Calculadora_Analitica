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

st.markdown("# MATHESIS")
st.markdown("## Matemáticas que se calculan, se exploran y se visualizan.")
st.markdown("### Desarrollado por: José Fernández y Rebeca Ortega")

st.write("") 

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

# 4. Acerca de MATHESIS
st.markdown("## ℹ️ Acerca de MATHESIS")

st.markdown("""
**MATHESIS** es un proyecto computacional interactivo desarrollado para facilitar el análisis, 
la exploración intuitiva y la resolución práctica de modelos cuantitativos en **Álgebra, Geometría, 
Análisis Vectorial, Economía y Matemáticas Financieras**.
""")

st.markdown("#### 🏛️ Desarrolladores & Contacto")
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
