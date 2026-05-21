import streamlit as st

# 1. Configuración de la página con el nuevo nombre formal
st.set_page_config(page_title="Espacio Vectorial", page_icon="📐", layout="centered")

# Ocultar el menú superior por defecto de Streamlit para mayor formalidad (Opcional)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Ajustar el espaciado superior */
    .block-container {padding-top: 2rem;}
    </style>
""", unsafe_allow_html=True)

# 2. Encabezado Principal de la Plataforma
st.markdown("# Espacio Vectorial")
st.markdown("## Plataforma Computacional para Análisis Lineal y Geometría")
st.markdown("**Desarrollado por: Fernández José y Rebeca Ortega**")

st.write("") # Espacio en blanco

st.markdown("""
¡Bienvenidos! Esta herramienta ha sido diseñada como un entorno computacional riguroso para 
asistir en cálculos complejos de nivel universitario.
""")

st.write("")
st.write("")

# 3. Módulos distribuidos en Columnas con Layout de Filas e Iconos (Estilo la imagen)
col1, col2 = st.columns(2)

with col1:
    # Módulo: Geometría
    st.markdown("""
    <table style="border: none; background: transparent; width: 100%;">
        <tr style="border: none; background: transparent;">
            <td style="border: none; width: 50px; vertical-align: top; padding-top: 5px;">
                <span style="font-size: 32px;">📐</span>
            </td>
            <td style="border: none; vertical-align: top;">
                <strong style="font-size: 18px;">Geometría:</strong><br>
                <span style="color: #b0b3b8; font-size: 14px;">Áreas, volúmenes, modelado y visualización 3D interactiva.</span>
            </td>
        </tr>
    </table>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.write("")

    # Módulo: Transformaciones Lineales
    st.markdown("""
    <table style="border: none; background: transparent; width: 100%;">
        <tr style="border: none; background: transparent;">
            <td style="border: none; width: 50px; vertical-align: top; padding-top: 5px;">
                <span style="font-size: 28px;">$\phi \rightarrow$</span>
            </td>
            <td style="border: none; vertical-align: top;">
                <strong style="font-size: 18px;">Transformaciones Lineales:</strong><br>
                <span style="color: #b0b3b8; font-size: 14px;">Núcleo, imagen, isomorfismos y matrices de cambio de base.</span>
            </td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

with col2:
    # Módulo: Matrices
    st.markdown("""
    <table style="border: none; background: transparent; width: 100%;">
        <tr style="border: none; background: transparent;">
            <td style="border: none; width: 50px; vertical-align: top; padding-top: 5px;">
                <span style="font-size: 32px;">🧮</span>
            </td>
            <td style="border: none; vertical-align: top;">
                <strong style="font-size: 18px;">Matrices:</strong><br>
                <span style="color: #b0b3b8; font-size: 14px;">Operaciones lineales, determinantes, matrices Hessianas y análisis espectral.</span>
            </td>
        </tr>
    </table>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.write("")

    # Módulo: Álgebra Superior
    st.markdown("""
    <table style="border: none; background: transparent; width: 100%;">
        <tr style="border: none; background: transparent;">
            <td style="border: none; width: 50px; vertical-align: top; padding-top: 5px;">
                <span style="font-size: 24px;">$\\frac{n'}{\\pi}$</span>
            </td>
            <td style="border: none; vertical-align: top;">
                <strong style="font-size: 18px;">Álgebra Superior:</strong><br>
                <span style="color: #b0b3b8; font-size: 14px;">Aritmética modular, identidad de Bézout y números complejos.</span>
            </td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

# 4. Quinto módulo (Vectores & Sistemas) alineado abajo a la derecha para respetar la cuadrícula exacta
_, colVectores = st.columns(2)
with colVectores:
    st.markdown("""
    <table style="border: none; background: transparent; width: 100%;">
        <tr style="border: none; background: transparent;">
            <td style="border: none; width: 50px; vertical-align: top; padding-top: 5px;">
                <span style="font-size: 32px;">↗️</span>
            </td>
            <td style="border: none; vertical-align: top;">
                <strong style="font-size: 18px;">Vectores & Sistemas:</strong><br>
                <span style="color: #b0b3b8; font-size: 14px;">Proyecciones, ángulos, Gram-Schmidt y resolución de sistemas lineales $[A|b]$.</span>
            </td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

st.write("")
st.write("")
st.write("")

# 5. Nota de Sesión en la parte inferior izquierda
st.markdown("""
<p style="color: #8a8d93; font-size: 13px;">
    ***Nota de Sesión:** La persistencia de variables (como matrices guardadas) se mantendrá activa mientras navega entre los módulos.*
</p>
""", unsafe_allow_html=True)
