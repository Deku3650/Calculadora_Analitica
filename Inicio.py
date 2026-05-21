import streamlit as st

# 1. Configuración de la página con el nuevo nombre formal
st.set_page_config(page_title="Calculadora Lineal", page_icon="🧮", layout="centered")

# CSS Limpio: Quitamos el bloqueo del header para que SIEMPRE aparezca la flecha del menú en celulares
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1.5rem;}
    </style>
""", unsafe_allow_html=True)

# 2. Encabezados Corregidos (Con el espacio necesario después del '#' para que se vean grandes)
st.markdown("# Calculadora Lineal")
st.markdown("## Plataforma Computacional para Análisis Lineal y Geometría")
st.markdown("### Desarrollado por: José Fernández y Rebeca Ortega")

st.write("") 

st.markdown("""
¡Bienvenidos! Esta herramienta ha sido diseñada como un entorno computacional riguroso para 
asistir en cálculos complejos de nivel universitario.

*📱 **Nota para celular:** Si no ve el menú de páginas, toque la pequeña flecha **( > )** en la esquina superior izquierda para desplegar los módulos.*
""")

st.write("")
st.write("")

# 3. Estructura de Viñetas en Dos Columnas (Evita que se rompa el diseño)
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
            <strong style="font-size: 17px;">↗️ Vectores & Sistemas:</strong><br>
            <span style="color: #b0b3b8; font-size: 14px; display: block; margin-top: 4px;">
                Proyecciones, ángulos, Gram-Schmidt y resolución de sistemas lineales $[A|b]$.
            </span>
        </li>
    </ul>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

# 4. Nota de Sesión
st.markdown("""
<p style="color: #8a8d93; font-size: 13px;">
    ***Nota de Sesión:** La persistencia de variables (como matrices guardadas) se mantendrá activa mientras navega entre los módulos.*
</p>
""", unsafe_allow_html=True)
