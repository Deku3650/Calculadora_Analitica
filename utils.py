# Programa: Calculadora_Avanzada.py
# Objetivo: Ayudar con calculos geometricos o de algebra lineal
# Autores: Fernández José y Rebeca Ortega
# Fecha: 04/03/26
# ---------------------------------------------------------- #

import math
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, \
    convert_xor
import streamlit as st

# ==============================================================================
# 1. CONFIGURACIÓN INICIAL DE LA PÁGINA Y MEMORIA (SESSION STATE)
# ==============================================================================
# Esto reemplaza el diccionario global. En Streamlit, la memoria se borra en cada recarga
# a menos que la guardemos en el "Session State".
st.set_page_config(page_title="Calculadora Avanzada", layout="wide")

if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}
if 'mis_vectores' not in st.session_state:
    st.session_state.mis_vectores = {}
if 'mis_transformaciones' not in st.session_state:
    st.session_state.mis_transformaciones = {}
if 'mis_complejos' not in st.session_state:
    st.session_state.mis_complejos = {}


# Funciones como limpiar_pantalla() y los diccionarios de colores (C) ya no son
# necesarios en Streamlit, ya que la interfaz no es una consola de texto.

# ==============================================================================
# 2. FUNCIONES DE APOYO (Adaptadas a Streamlit)
# ==============================================================================

def imprimir_matriz_simbolica(matriz_sp):
    """
    Reemplaza a los prints con ASCII de colores.
    Usa el renderizador LaTeX nativo de Streamlit.
    """
    if matriz_sp:
        # SymPy tiene una función que convierte matrices a formato LaTeX
        latex_str = sp.latex(matriz_sp)
        # Streamlit renderiza matemáticas usando st.latex
        st.latex(latex_str)


def leer_expresion_st(entrada_str, solo_reales=False):
    """
    Analiza una cadena (texto ingresado en un widget) y la convierte en un objeto SymPy.
    Retorna el objeto SymPy si es válido, o None (y un mensaje de error) si no lo es.
    """
    transformaciones = standard_transformations + (implicit_multiplication_application, convert_xor)
    diccionario_imaginario = {"i": sp.I, "j": sp.I, "I": sp.I}

    if not entrada_str.strip():
        return None

    try:
        expresion = parse_expr(entrada_str, transformations=transformaciones, local_dict=diccionario_imaginario)

        if not isinstance(expresion, sp.Expr):
            st.error(f"'{entrada_str}' es una palabra reservada, no una expresión.")
            return None

        if solo_reales and expresion.has(sp.I):
            st.error("Esta operación requiere números reales.")
            return None

        if expresion.has(sp.oo, sp.zoo, sp.nan, -sp.oo):
            st.error("Error matemático: Evaluación a infinito o división por cero.")
            return None

        return expresion
    except Exception:
        st.error(f"La expresión '{entrada_str}' no es válida matemáticamente.")
        return None


# ==============================================================================
# 3. MÓDULOS DE CREACIÓN DE MATRICES Y TRANSFORMACIONES (Adaptados)
# ==============================================================================
# En Streamlit, las funciones largas que interactúan con el usuario deben
# estructurarse usando contenedores, columnas y formularios (st.form).

def Crear_Matriz_Simbolica_UI(nombre_clave):
    """
    Genera la interfaz gráfica (UI) para crear una matriz.
    Retorna la matriz de SymPy cuando el usuario oprime "Guardar".
    """
    st.subheader(f"Crear Matriz: {nombre_clave}")

    # Configuradores de tamaño (reemplazan los input numéricos)
    col1, col2 = st.columns(2)
    with col1:
        filas = st.number_input("Renglones", min_value=1, max_value=10, value=3, key=f"R_{nombre_clave}")
    with col2:
        columnas = st.number_input("Columnas", min_value=1, max_value=10, value=3, key=f"C_{nombre_clave}")

    st.write("Ingrese los elementos (números o variables como 'x', 'x**2', etc.):")

    # Creamos un bloque (Form) para que la matriz no intente recalcularse
    # por cada tecla que presione el usuario.
    with st.form(f"form_matriz_{nombre_clave}"):
        matriz_elementos = []
        for i in range(filas):
            # Creamos una columna visual por cada elemento de la fila
            cols_input = st.columns(columnas)
            fila_actual = []
            for j in range(columnas):
                with cols_input[j]:
                    # El widget text_input reemplaza al input() de consola
                    valor = st.text_input(f"E({i + 1},{j + 1})", value="0", key=f"elem_{nombre_clave}_{i}_{j}")
                    fila_actual.append(valor)
            matriz_elementos.append(fila_actual)

        submit = st.form_submit_button("Construir Matriz")

    if submit:
        matriz_sympy = sp.zeros(filas, columnas)
        error = False
        for i in range(filas):
            for j in range(columnas):
                obj = leer_expresion_st(matriz_elementos[i][j])
                if obj is None:
                    error = True
                    break
                matriz_sympy[i, j] = obj
            if error:
                break

        if not error:
            st.success("¡Matriz creada exitosamente!")
            imprimir_matriz_simbolica(matriz_sympy)
            return matriz_sympy
    return None


def Crear_Transformacion_UI():
    """
    Interfaz paso a paso para definir una T.L. en Streamlit.
    """
    st.header("⚙️ Definir Transformación Lineal")

    st.subheader("1. Dominio (V)")
    tipo_dom = st.selectbox("Espacio Vectorial", ["R^n", "Polinomios (Pn)", "Matrices (mxn)"], key="tipo_dom")
    dim_v = st.number_input("Dimensión del Dominio:", min_value=1, value=3, key="dim_v")

    usar_canonica_v = st.checkbox("Usar Base Canónica para el Dominio", value=True, key="canon_v")

    if usar_canonica_v:
        Base1 = sp.eye(dim_v)
    else:
        st.info("Seleccione una matriz del inventario para usarla como Base del Dominio. (Debe ser cuadrada y L.I.)")
        if st.session_state.mis_matrices:
            mat_base1 = st.selectbox("Matriz para Base Dominio:", list(st.session_state.mis_matrices.keys()),
                                     key="sel_base1")
            Base1 = st.session_state.mis_matrices[mat_base1]
            if Base1.shape != (dim_v, dim_v) or Base1.det() == 0:
                st.error("La matriz seleccionada no es válida como base (Dimensiones incorrectas o determinante cero).")
                return None
        else:
            st.warning("Debe crear una matriz en el panel lateral primero.")
            return None

    # --- CODOMINIO ---
    st.subheader("2. Co-Dominio (W)")
    tipo_cod = st.selectbox("Espacio Vectorial", ["R^n", "Polinomios (Pn)", "Matrices (mxn)"], key="tipo_cod")
    dim_w = st.number_input("Dimensión del Codominio:", min_value=1, value=3, key="dim_w")

    usar_canonica_w = st.checkbox("Usar Base Canónica para el Co-Dominio", value=True, key="canon_w")

    if usar_canonica_w:
        Base2 = sp.eye(dim_w)
    else:
        st.info("Seleccione una matriz del inventario para usarla como Base del Codominio.")
        if st.session_state.mis_matrices:
            mat_base2 = st.selectbox("Matriz para Base Codominio:", list(st.session_state.mis_matrices.keys()),
                                     key="sel_base2")
            Base2 = st.session_state.mis_matrices[mat_base2]
            if Base2.shape != (dim_w, dim_w) or Base2.det() == 0:
                st.error("La matriz seleccionada no es válida como base.")
                return None
        else:
            st.warning("Debe crear una matriz en el panel lateral primero.")
            return None

    st.divider()

    # --- VARIABLES ---
    st.subheader("3. Variables del Dominio")
    vars_str = st.text_input(f"Ingrese {dim_v} variables separadas por comas (Ej. x, y, z):", value="x,y,z")
    lista_vars = [v.strip() for v in vars_str.split(',')]

    if len(lista_vars) != dim_v:
        st.warning(f"Debe ingresar exactamente {dim_v} variables.")
        return None

    variables_simbolicas = tuple(sp.symbols(v) for v in lista_vars)

    # --- REGLA O MATRIZ ---
    st.subheader("4. Definición de la Transformación")
    
    # Si el dominio y codominio son polinomios, activamos el Motor de Operadores
    if tipo_dom == "Polinomios (Pn)" and tipo_cod == "Polinomios (Pn)":
        st.info("💡 **Modo de Operador Diferencial/Integral Activado**")
        st.markdown("""
        Escriba la regla matemática aplicando operaciones sobre el polinomio **`p`**. Use **`x`** como variable y **`t`** como variable auxiliar de integración.
        * **Derivada ($p'(x)$):** `diff(p, x)` o `diff(p, x, 2)` para la segunda derivada.
        * **Integral Indefinida ($\int p(x)dx$):** `integrate(p, x)`
        * **Integral Definida ($\int_0^x p(t)dt$):** `integrate(p.subs(x, t), (t, 0, x))`
        * **Multiplicación ($x \cdot p(x)$):** `x * p`
        """)
        
        # El ejemplo exacto que pediste como valor por defecto
        regla_str = st.text_input(
            "Ingrese el operador $T(p) = $", 
            value="2*diff(p, x, 2) + 3*integrate(p.subs(x, t), (t, 0, x))"
        )
        
        if st.button("Construir Matriz del Operador"):
            x, t = sp.symbols('x t')
            
            # 1. Construimos el polinomio abstracto p(x) basado en la dimensión
            # Usamos la convención de mayor a menor grado: c2*x^2 + c1*x + c0
            variables_simbolicas = sp.symbols(f'c{dim_v-1}:-1:-1') 
            p = sum(variables_simbolicas[i] * x**(dim_v - 1 - i) for i in range(dim_v))
            
            # 2. Diccionario de contexto para que SymPy entienda los comandos de cálculo
            diccionario_local = {
                'p': p, 'x': x, 't': t,
                'diff': sp.diff, 'integrate': sp.integrate
            }
            
            try:
                # 3. Evaluamos la regla ingresada por el usuario
                expr_evaluada = parse_expr(regla_str, local_dict=diccionario_local)
                expr_expandida = sp.expand(expr_evaluada)
                
                st.success("Operador evaluado con éxito:")
                st.latex(f"T(p(x)) = {sp.latex(expr_expandida)}")
                
                # 4. Extracción de coordenadas para el codominio
                vector_columna = []
                for grado in range(dim_w - 1, 0, -1):
                    vector_columna.append(expr_expandida.coeff(x, grado))
                vector_columna.append(expr_expandida.subs(x, 0)) # El término independiente
                
                Matriz_Regla = sp.Matrix(vector_columna)
                
                # 5. Calculamos la Matriz Asociada derivando (Jacobiano) respecto a c2, c1, c0
                Matriz_Asociada = Matriz_Regla.jacobian(variables_simbolicas)
                
                st.write("**Matriz Asociada a la Transformación Lineal:**")
                imprimir_matriz_simbolica(Matriz_Asociada)
                
                # Guardado en memoria
                nombre_tl = st.text_input("Guardar transformación como (Ej. T_Int):").upper().strip()
                if st.button("💾 Guardar Operador en Memoria"):
                    if nombre_tl:
                        st.session_state.mis_transformaciones[nombre_tl] = {
                            "dim_V": dim_v,
                            "dim_W": dim_w,
                            "variables": variables_simbolicas,
                            "matriz_asociada": Matriz_Asociada,
                            "regla": Matriz_Regla,
                            "base_dominio": Base1, # Previamente extraídas del bloque superior
                            "base_codominio": Base2
                        }
                        st.rerun()
                    else:
                        st.error("Debe proporcionar un nombre válido.")
                        
            except Exception as e:
                st.error(f"Error al analizar la regla de cálculo: Revisa la sintaxis. Detalle: {e}")

    # --- FLUJO ESTÁNDAR PARA R^n Y MATRICES ---
    else:
        metodo = st.radio("Definir a partir de:", ["Regla de Correspondencia", "Matriz Asociada"], horizontal=True)
        
        if metodo == "Matriz Asociada":
            Matriz_Asociada = Crear_Matriz_Simbolica_UI("T_Asociada")
            
            if Matriz_Asociada:
                if Matriz_Asociada.shape != (dim_w, dim_v):
                    st.error(f"La matriz debe ser de dimensiones ({dim_w} x {dim_v}).")
                else:
                    vector_variables = sp.Matrix(variables_simbolicas)
                    Matriz_Regla = Matriz_Asociada * vector_variables
                    
                    st.success("Transformación válida.")
                    st.write("Regla de Correspondencia resultante:")
                    imprimir_matriz_simbolica(Matriz_Regla)
                    
                    nombre_tl = st.text_input("Guardar transformación como (Ej. T1):").upper().strip()
                    if st.button("Guardar en Memoria"):
                        st.session_state.mis_transformaciones[nombre_tl] = {
                            "dim_V": dim_v,
                            "dim_W": dim_w,
                            "variables": variables_simbolicas,
                            "matriz_asociada": Matriz_Asociada,
                            "regla": Matriz_Regla,
                            "base_dominio": Base1,
                            "base_codominio": Base2
                        }
                        st.rerun()
                        
        elif metodo == "Regla de Correspondencia":
            st.write("Ingrese los componentes del vector resultante:")
            with st.form("form_regla"):
                eqs_input = []
                for i in range(dim_w):
                    eq = st.text_input(f"Componente {i+1}:", key=f"comp_{i}")
                    eqs_input.append(eq)
                sub = st.form_submit_button("Procesar Regla")
                
            if sub:
                vector_columna = []
                error = False
                for val in eqs_input:
                    obj = leer_expresion_st(val)
                    if obj is None:
                        error = True; break
                    vector_columna.append(obj)
                    
                if not error:
                    Matriz_Regla = sp.Matrix(vector_columna)
                    sustitucion_cero = {v: 0 for v in variables_simbolicas}
                    evaluacion_cero = Matriz_Regla.subs(sustitucion_cero)
                    es_cero = all(e == 0 for e in evaluacion_cero)
                    
                    if not es_cero:
                        st.error("La transformación NO es lineal: T(0) ≠ 0")
                    else:
                        Jacobiano = Matriz_Regla.jacobian(variables_simbolicas)
