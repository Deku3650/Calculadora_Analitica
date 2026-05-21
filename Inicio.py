import streamlit as st

# 1. Configuración de la página con el nuevo nombre formal
st.set_page_config(page_title="Espacio Vectorial", page_icon="📐", layout="centered")

# CORRECCIÓN DE CSS: Quitamos 'header {visibility: hidden;}' para que NO rompa el botón del menú en celular
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    </style>
""", unsafe_allow_html=True)

# 2. Encabezado Principal de la Plataforma
st.markdown("Calculadora Lineal")
st.markdown("Plataforma Computacional para Análisis Lineal y Geometría")
st.markdown("**Desarrollado por: José Fernández y Rebeca Ortega**")

st.write("") 

# Añadimos una breve instrucción para los usuarios en móvil
st.markdown("""
¡Bienvenidos! Esta herramienta ha sido diseñada como un entorno computacional riguroso para 
asistir en cálculos complejos de nivel universitario.

*📱 Si está navegando desde un dispositivo móvil, presione la flecha **( > )** en la esquina superior izquierda para desplegar el menú de módulos.*
""")

st.write("")
st.write("")

# 3. Módulos distribuidos en Columnas con Viñetas (Layout exacto de la imagen)
col1, col2 = st.columns(2)

with col1:
    # Módulo: Geometría
    st.markdown("""
    <ul style="list-style-type: disc; margin-left: 20px; padding-left: 0;">
        <li style="color: #ffffff; margin-bottom: 25px;">
            <strong style="font-size: 18px;">📐 Geometría:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 5px;">
                Áreas, volúmenes, modelado y visualización 3D interactiva.
            </span>
        </li>
        <li style="color: #ffffff;">
            <strong style="font-size: 18px;">🔄 Transformaciones Lineales:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 5px;">
                Núcleo, imagen, isomorfismos y matrices de cambio de base.
            </span>
        </li>
    </ul>
    """, unsafe_allow_html=True)

with col2:
    # Módulos del lado derecho
    st.markdown("""
    <ul style="list-style-type: disc; margin-left: 20px; padding-left: 0;">
        <li style="color: #ffffff; margin-bottom: 25px;">
            <strong style="font-size: 18px;">🧮 Matrices:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 5px;">
                Operaciones lineales, determinantes, matrices Hessianas y análisis espectral.
            </span>
        </li>
        <li style="color: #ffffff; margin-bottom: 25px;">
            <strong style="font-size: 18px;">🔢 Álgebra Superior:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 5px;">
                Aritmética modular, identidad de Bézout y números complejos.
            </span>
        </li>
        <li style="color: #ffffff;">
            <strong style="font-size: 18px;">↗️ Vectores & Sistemas:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 5px;">
                Proyecciones, ángulos, Gram-Schmidt y resolución de sistemas lineales $[A|b]$.
            </span>
        </li>
    </ul>
    """, unsafe_allow_html=True)

st.write("")
st.write("")
st.write("")

# 4. Nota de Sesión en la parte inferior
st.markdown("""
<p style="color: #8a8d93; font-size: 13px;">
    ***Nota de Sesión:** La persistencia de variables (como matrices guardadas) se mantendrá activa mientras navega entre los módulos.*
</p>
""", unsafe_allow_html=True)
