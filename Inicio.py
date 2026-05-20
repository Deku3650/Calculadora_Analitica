import streamlit as st

st.set_page_config(page_title="Calculadora Integral", page_icon="🧮", layout="centered")

st.title("🧮 Calculadora Matemática Integral")
st.subheader("Desarrollado por: Fernández José y Rebeca Ortega")

st.markdown("""
¡Bienvenidos! Esta herramienta ha sido diseñada para asistir en cálculos complejos 
de nivel universitario. 

### ¿Cómo navegar?
Utilice el **menú lateral a la izquierda** para acceder a los distintos módulos:

* 📐 **Geometría:** Áreas, volúmenes y visualización 3D.
* 🧮 **Matrices:** Operaciones lineales, determinantes, Hessianas y análisis espectral.
* 🔄 **Transformaciones Lineales:** Núcleo, imagen, isomorfismos y cambios de base.
* 🔢 **Álgebra Superior:** Aritmética modular, Bézout y números complejos.
* ↗️ **Vectores y Sistemas:** Proyecciones, ángulos, Gram-Schmidt y resolución de sistemas $[A|b]$.

*Nota: La memoria de las variables (como sus matrices guardadas) se mantendrá activa mientras navega entre las diferentes páginas de esta sesión.*
""")