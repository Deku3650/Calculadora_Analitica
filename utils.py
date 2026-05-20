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
    st.header("⚙️ Definir Transformación Lineal")
    
    # ==============================================================================
    # 1. SOLICITUD DE ESPACIOS (DOMINIO Y CODOMINIO)
    # ==============================================================================
    st.subheader("1. Dominio (V)")
    tipo_dom = st.selectbox("Espacio Vectorial del Dominio", ["R^n", "Polinomios (Pn)", "Matrices (mxn)"], key="tl_tipo_dom")
    if tipo_dom == "R^n":
        dim_v = st.number_input("Dimensión n (Dominio):", min_value=1, value=3, key="tl_dim_v_rn")
    elif tipo_dom == "Polinomios (Pn)":
        grado = st.number_input("Grado n (Dominio):", min_value=0, value=2, key="tl_dim_v_pn")
        dim_v = grado + 1
    else:
        m = st.number_input("Filas m (Dominio):", min_value=1, value=2, key="tl_m1")
        n = st.number_input("Columnas n (Dominio):", min_value=1, value=2, key="tl_n1")
        dim_v = m * n

    st.subheader("2. Co-Dominio (W)")
    tipo_cod = st.selectbox("Espacio Vectorial del Codominio", ["R^n", "Polinomios (Pn)", "Matrices (mxn)"], key="tl_tipo_cod")
    if tipo_cod == "R^n":
        dim_w = st.number_input("Dimensión n (Codominio):", min_value=1, value=3, key="tl_dim_w_rn")
    elif tipo_cod == "Polinomios (Pn)":
        grado_cod = st.number_input("Grado n (Codominio):", min_value=0, value=2, key="tl_dim_w_pn")
        dim_w = grado_cod + 1
    else:
        m2 = st.number_input("Filas m (Codominio):", min_value=1, value=2, key="tl_m2")
        n2 = st.number_input("Columnas n (Codominio):", min_value=1, value=2, key="tl_n2")
        dim_w = m2 * n2

    # Definimos bases canónicas estables para este flujo inicial
    Base1 = sp.eye(dim_v)
    Base2 = sp.eye(dim_w)

    st.divider()

    # ==============================================================================
    # 2. CAPTURA PREVIA DE VARIABLES
    # ==============================================================================
    st.subheader("3. Variables del Dominio (Coordenadas)")
    
    # Generador de sugerencias inteligentes según el espacio y dimensión
    if tipo_dom == "Polinomios (Pn)":
        if dim_v == 3:
            default_vars = "a, b, c"
        elif dim_v == 2:
            default_vars = "m, b"
        else:
            default_vars = ",".join([f"a{i}" for i in range(dim_v - 1, -1, -1)])
        st.caption(f"Para un polinomio de grado {dim_v-1}, necesita definir {dim_v} coeficientes.")
    else:
        if dim_v <= 4:
            default_vars = ",".join(["x", "y", "z", "w"][:dim_v])
        else:
            default_vars = ",".join([f"x{i+1}" for i in range(dim_v)])
        st.caption(f"Defina las {dim_v} variables de su vector de entrada.")

    # Captura universal para cualquier espacio
    vars_str = st.text_input("Ingrese las variables separadas por comas:", value=default_vars, key="tl_vars_input")
    lista_vars = [v.strip() for v in vars_str.split(',') if v.strip()]
    
    if len(lista_vars) != dim_v:
        st.warning(f"Por favor ingrese exactamente {dim_v} variables para poder continuar.")
        return
        
    variables_simbolicas = tuple(sp.symbols(v) for v in lista_vars)

    st.divider()

    # ==============================================================================
    # 3. MÉTODOS DE DEFINICIÓN (MENÚ PRINCIPAL DE 3 OPCIONES)
    # ==============================================================================
    st.subheader("4. Configuración de la Regla")
    metodo = st.radio(
        "Seleccione el método para definir la transformación:",
        ["1. Dar Regla de Correspondencia / Operador", "2. Definir una Matriz Nueva", "3. Importar una Matriz Preexistente"],
        key="tl_metodo_def"
    )

    # Inicializamos estados de cálculo vacíos
    matriz_asociada_calculada = None
    matriz_regla_calculada = None

    # --- OPCIÓN 1: REGLA DE CORRESPONDENCIA / OPERADOR ---
    if "1. Dar Regla de Correspondencia" in metodo:
        if tipo_dom == "Polinomios (Pn)" and tipo_cod == "Polinomios (Pn)":
            st.markdown("""
            Escriba el operador aplicando operaciones sobre el polinomio **`p`**. Use **`x`** como variable y **`t`** como auxiliar.
            * *Ejemplo:* `2*diff(p, x, 2) + 3*integrate(p.subs(x, t), (t, 0, x))`
            """)
            regla_str = st.text_input("Ingrese el operador T(p) =", value="diff(p, x)", key="tl_regla_op")
            
            if st.button("Construir desde Operador"):
                x_sym, t_sym = sp.symbols('x t')
                p_poly = sum(variables_simbolicas[i] * x_sym**(dim_v - 1 - i) for i in range(dim_v))
                diccionario_local = {'p': p_poly, 'x': x_sym, 't': t_sym, 'diff': sp.diff, 'integrate': sp.integrate}
                
                try:
                    expr_evaluada = sp.expand(parse_expr(regla_str, local_dict=diccionario_local))
                    st.success("Operador evaluado con éxito:")
                    st.latex(f"T(p(x)) = {sp.latex(expr_evaluada)}")
                    
                    vector_columna = []
                    for grado_idx in range(dim_w - 1, 0, -1):
                        vector_columna.append(expr_evaluada.coeff(x_sym, grado_idx))
                    vector_columna.append(expr_evaluada.subs(x_sym, 0))
                    
                    matriz_regla_calculada = sp.Matrix(vector_columna)
                    matriz_asociada_calculada = matriz_regla_calculada.jacobian(variables_simbolicas)
                    
                    st.session_state.temp_tl_mat = matriz_asociada_calculada
                    st.session_state.temp_tl_reg = matriz_regla_calculada
                except Exception as e:
                    st.error(f"Error de sintaxis en el operador: {e}")
        else:
            st.write("Ingrese las funciones componentes del vector de salida:")
            with st.form("form_regla_tl"):
                eqs_input = [st.text_input(f"Componente {i+1}:", value="0", key=f"comp_val_{i}") for i in range(dim_w)]
                submit_regla = st.form_submit_button("Procesar Regla de Correspondencia")
            
            if submit_regla:
                vector_columna = []
                error_parsing = False
                
                # 1. Usamos nuestra función blindada en lugar de parse_expr crudo
                for eq in eqs_input:
                    val = leer_expresion_st(eq)
                    if val is None:
                        error_parsing = True
                        break
                    vector_columna.append(val)
                
                if not error_parsing:
                    try:
                        matriz_regla_calculada = sp.Matrix(vector_columna)
                        
                        # 2. Verificamos linealidad básica: T(0) = 0
                        sustitucion_cero = {v: 0 for v in variables_simbolicas}
                        eval_cero = matriz_regla_calculada.subs(sustitucion_cero)
                        
                        if not all(e == 0 for e in eval_cero):
                            st.error("Error Matemático: La transformación NO es lineal (T(0) ≠ 0). Revise si agregó constantes sueltas.")
                        else:
                            # 3. Calculamos la Jacobiana
                            matriz_asociada_calculada = matriz_regla_calculada.jacobian(variables_simbolicas)
                            
                            st.session_state.temp_tl_mat = matriz_asociada_calculada
                            st.session_state.temp_tl_reg = matriz_regla_calculada
                            
                    except Exception as e:
                        st.error(f"Error matemático al construir la matriz: {e}")

    # --- OPCIÓN 2: DEFINIR MATRIZ NUEVA ---
    elif "2. Definir una Matriz Nueva" in metodo:
        st.write(f"Construya la matriz asociada de dimensiones ({dim_w}x{dim_v}):")
        with st.form("form_nueva_matriz_tl"):
            matriz_elementos = []
            for i in range(dim_w):
                cols_input = st.columns(dim_v)
                fila_actual = []
                for j in range(dim_v):
                    with cols_input[j]:
                        valor = st.text_input(f"M({i+1},{j+1})", value="0", key=f"mat_tl_{i}_{j}")
                        fila_actual.append(valor)
                matriz_elementos.append(fila_actual)
            submit_mat = st.form_submit_button("Generar Transformación desde Matriz")
            
        if submit_mat:
            try:
                matriz_asociada_calculada = sp.Matrix([[parse_expr(cell) for cell in row] for row in matriz_elementos])
                matriz_regla_calculada = matriz_asociada_calculada * sp.Matrix(variables_simbolicas)
                st.session_state.temp_tl_mat = matriz_asociada_calculada
                st.session_state.temp_tl_reg = matriz_regla_calculada
            except Exception as e:
                st.error(f"Error al parsear los elementos de la matriz: {e}")

    # --- OPCIÓN 3: IMPORTAR MATRIZ PREEXISTENTE ---
    elif "3. Importar una Matriz Preexistente" in metodo:
        if st.session_state.mis_matrices:
            mat_seleccionada = st.selectbox("Seleccione una matriz de su inventario global:", list(st.session_state.mis_matrices.keys()))
            M_imp = st.session_state.mis_matrices[mat_seleccionada]
            
            # Validación estricta antes de importar
            if M_imp.shape != (dim_w, dim_v):
                st.error(f"Incompatibilidad de dimensiones: La matriz '{mat_seleccionada}' mide {M_imp.shape[0]}x{M_imp.shape[1]}, pero el espacio configurado requiere una matriz de {dim_w}x{dim_v}.")
            else:
                if st.button("Vincular Matriz Seleccionada"):
                    st.session_state.temp_tl_mat = M_imp
                    st.session_state.temp_tl_reg = M_imp * sp.Matrix(variables_simbolicas)
                    st.success(f"Matriz '{mat_seleccionada}' vinculada correctamente como matriz asociada.")
        else:
            st.warning("No hay ninguna matriz guardada en el inventario actual de la sesión. Vaya al módulo de Matrices y cree una primero.")

    # ==============================================================================
    # 4. BLOQUE DE CONFIRMACIÓN Y GUARDADO PERSISTENTE
    # ==============================================================================
    if 'temp_tl_mat' in st.session_state:
        st.divider()
        st.write("**Matriz Asociada resultante:**")
        imprimir_matriz_simbolica(st.session_state.temp_tl_mat)
        st.write("**Regla de correspondencia analítica:**")
        imprimir_matriz_simbolica(st.session_state.temp_tl_reg)
        
        nombre_tl = st.text_input("Asigne un nombre para guardar esta T.L. (Ej. T1):", key="save_tl_final").upper().strip()
        if st.button("💾 Almacenar Transformación Lineal"):
            if nombre_tl:
                st.session_state.mis_transformaciones[nombre_tl] = {
                    "dim_V": dim_v,
                    "dim_W": dim_w,
                    "variables": variables_simbolicas,
                    "matriz_asociada": st.session_state.temp_tl_mat,
                    "regla": st.session_state.temp_tl_reg,
                    "base_dominio": Base1,
                    "base_codominio": Base2
                }
                # Limpieza de variables temporales para evitar duplicados en la UI
                del st.session_state.temp_tl_mat
                del st.session_state.temp_tl_reg
                st.success(f"¡Transformación '{nombre_tl}' guardada con éxito!")
                st.rerun()
            else:
                st.error("Por favor proporcione un nombre válido antes de guardar.")
