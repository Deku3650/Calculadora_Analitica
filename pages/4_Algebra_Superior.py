import streamlit as st
import sympy as sp
import math
from sympy.ntheory.modular import crt

# Importamos nuestra herramienta de lectura robusta desde el archivo base
try:
    from utils import leer_expresion_st
except ImportError:
    # Fallback temporal por si lo estás probando en el mismo archivo
    def leer_expresion_st(val, solo_reales=False):
        try:
            return sp.sympify(val)
        except:
            return None

st.set_page_config(page_title="Álgebra Superior", layout="wide")

if 'mis_complejos' not in st.session_state:
    st.session_state.mis_complejos = {}

st.title("🔢 Módulo de Álgebra Superior")
st.markdown("Teoría de Números, Aritmética Modular y Variable Compleja.")

# Creamos las 4 pestañas principales
tab_mcd, tab_euclides, tab_congruencias, tab_complejos = st.tabs([
    "MCD, mcm y Primos",
    "Algoritmo de Euclides",
    "Congruencias Lineales",
    "Números Complejos"
])

# ==============================================================================
# PESTAÑA 1: MCD, mcm y Descomposición
# ==============================================================================
with tab_mcd:
    st.subheader("Máximo Común Divisor y Mínimo Común Múltiplo")

    # UX Mejorada: Una sola línea separada por comas
    entrada_nums = st.text_input(
        "Ingrese un conjunto de números enteros positivos separados por comas (Ej: 12, 18, 24):")

    if st.button("Calcular MCD y mcm"):
        if entrada_nums:
            try:
                # Convertimos el texto en una lista de enteros limpios y sin ceros
                lista_numeros = [int(x.strip()) for x in entrada_nums.split(',') if int(x.strip()) != 0]
                conjunto_limpio = list(set(lista_numeros))

                if len(conjunto_limpio) < 2:
                    st.error("Necesita al menos 2 números diferentes para operar.")
                else:
                    resultado_mcd = math.gcd(*conjunto_limpio)
                    resultado_mcm = math.lcm(*conjunto_limpio)

                    st.success(f"**Conjunto procesado:** {conjunto_limpio}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Máximo Común Divisor (MCD)", resultado_mcd)
                    with col2:
                        st.metric("Mínimo Común Múltiplo (mcm)", resultado_mcm)

                    st.divider()
                    st.subheader("Descomposición en Factores Primos")

                    # Elementos originales
                    st.write("**Elementos del conjunto:**")
                    for n in conjunto_limpio:
                        factores = sp.factorint(n)
                        cadena_factores = " \cdot ".join(
                            [f"{p}^{{{e}}}" if e > 1 else f"{p}" for p, e in factores.items()])
                        if n == 1: cadena_factores = "1"
                        st.latex(f"{n} = {cadena_factores}")

                    # Resultados
                    st.write("**Resultados:**")
                    factores_mcd = sp.factorint(resultado_mcd)
                    cad_mcd = " \cdot ".join([f"{p}^{{{e}}}" if e > 1 else f"{p}" for p, e in factores_mcd.items()])
                    st.latex(f"\text{{MCD}} = {cad_mcd}")

                    factores_mcm = sp.factorint(resultado_mcm)
                    cad_mcm = " \cdot ".join([f"{p}^{{{e}}}" if e > 1 else f"{p}" for p, e in factores_mcm.items()])
                    st.latex(f"\text{{mcm}} = {cad_mcm}")

            except ValueError:
                st.error("Error: Asegúrese de ingresar únicamente números enteros separados por comas.")

# ==============================================================================
# PESTAÑA 2: Algoritmo de Euclides
# ==============================================================================
with tab_euclides:
    st.subheader("Algoritmo de Euclides Extendido")
    st.markdown("Encuentra el MCD de $(a, b)$ y su Identidad de Bézout: $ax + by = \text{MCD}$")

    col1, col2 = st.columns(2)
    with col1:
        a = st.number_input("Valor de 'a':", min_value=0, value=12, step=1)
    with col2:
        b = st.number_input("Valor de 'b':", min_value=0, value=8, step=1)

    if st.button("Aplicar Algoritmo"):
        if a == 0 and b == 0:
            st.error("Ambos números no pueden ser cero.")
        else:
            x, y, mcd = sp.gcdex(a, b)
            st.success("Cálculo completado.")
            st.latex(f"\text{{MCD}}({a}, {b}) = {mcd}")

            st.write("**Identidad de Bézout (Mínima Combinación Lineal):**")
            signo_y = "+" if y >= 0 else "-"
            st.latex(f"({a})({x}) {signo_y} ({b})({abs(y)}) = {mcd}")

# ==============================================================================
# PESTAÑA 3: Congruencias (Teorema Chino del Resto)
# ==============================================================================
with tab_congruencias:
    st.subheader("Sistemas de Congruencias Lineales")
    st.markdown("Resuelve sistemas de la forma: $cx \equiv a \pmod m$")

    cantidad_ec = st.number_input("¿Cuántas ecuaciones tiene su sistema?", min_value=1, max_value=10, value=2)

    residuos = []
    modulos = []
    sistema_valido = True

    with st.form("form_congruencias"):
        st.write("Ingrese los parámetros para cada ecuación:")
        for i in range(int(cantidad_ec)):
            st.markdown(f"**Ecuación {i + 1}**")
            c1, c2, c3 = st.columns(3)
            with c1:
                coef = st.number_input(f"Coeficiente (c)", value=1, key=f"c_{i}")
            with c2:
                res = st.number_input(f"Residuo (a)", value=1, key=f"a_{i}")
            with c3:
                mod = st.number_input(f"Módulo (m) [>1]", min_value=2, value=2, key=f"m_{i}")

            # Motor de purificación integrado
            d = math.gcd(coef, mod)
            if res % d != 0:
                st.error(f"¡Alerta! La ecuación {i + 1} ($ {coef}x \equiv {res} \pmod {mod