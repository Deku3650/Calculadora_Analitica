# Programa: Calculadora_Avanzada.py
# Objetivo: Ayudar con calculos geometricos o de algebra lineal
# Autores: Fernández José y Rebeca Ortega
# Fecha: 04/03/26
# ---------------------------------------------------------- #

import math
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
import streamlit as st
import re

# ==============================================================================
# 1. CONFIGURACIÓN INICIAL DE LA PÁGINA Y MEMORIA (SESSION STATE)
# ==============================================================================
st.set_page_config(page_title="Calculadora Avanzada", layout="wide")

if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}
if 'mis_vectores' not in st.session_state:
    st.session_state.mis_vectores = {}
if 'mis_transformaciones' not in st.session_state:
    st.session_state.mis_transformaciones = {}
if 'mis_complejos' not in st.session_state:
    st.session_state.mis_complejos = {}

# ==============================================================================
# 2. FUNCIONES DE APOYO (Adaptadas a Streamlit)
# ==============================================================================

def imprimir_matriz_simbolica(matriz_sp):
    """
    Reemplaza a los prints con ASCII de colores.
    Usa el renderizador LaTeX nativo de Streamlit.
    """
    if matriz_sp is not None:
        latex_str = sp.latex(matriz_sp)
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

def Crear_Matriz_Simbolica_UI(nombre_clave):
    """
    Genera la interfaz gráfica (UI) para crear una matriz.
    Retorna la matriz de SymPy cuando el usuario oprime "Guardar".
    """
    st.subheader(f"Crear Matriz: {nombre_clave}")

    col1, col2 = st.columns(2)
    with col1:
        filas = st.number_input("Renglones", min_value=1, max_value=10, value=3, key=f"R_{nombre_clave}")
    with col2:
        columnas = st.number_input("Columnas", min_value=1, max_value=10, value=3, key=f"C_{nombre_clave}")

    st.write("Ingrese los elementos (números o variables como 'x', 'x**2', etc.):")

    with st.form(f"form_matriz_{nombre_clave}"):
        matriz_elementos = []
        for i in range(filas):
            cols_input = st.columns(columnas)
            fila_actual = []
            for j in range(columnas):
                with cols_input[j]:
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
    # 1. SOLICITUD DE ESPACIOS
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

    st.divider()

    # ==============================================================================
    # 2. CAPTURA PREVIA DE VARIABLES
    # ==============================================================================
    st.subheader("3. Variables del Dominio (Coordenadas)")
    
    if tipo_dom == "Polinomios (Pn)":
        if dim_v == 3: default_vars = "a, b, c"
        elif dim_v == 2: default_vars = "m, b"
        else: default_vars = ",".join([f"a{i}" for i in range(dim_v - 1, -1, -1)])
        st.info(rf"💡 **Notación Polinomial:** Cada variable representa un coeficiente ordenado de mayor a menor grado. Ejemplo: Para variables '{default_vars}', el polinomio evaluado será $p(x) = { 'x^2 + '.join(default_vars.split(', ')) if dim_v==3 else 'x + '.join(default_vars.split(', ')) if dim_v==2 else '...' }$")
    else:
        if dim_v <= 4: default_vars = ",".join(["x", "y", "z", "w"][:dim_v])
        else: default_vars = ",".join([f"x{i+1}" for i in range(dim_v)])
        st.caption(f"Defina las {dim_v} variables de su vector de entrada.")

    vars_str = st.text_input("Ingrese las variables separadas por comas:", value=default_vars, key="tl_vars_input")
    lista_vars = [v.strip() for v in vars_str.split(',') if v.strip()]
    
    if len(lista_vars) != dim_v:
        st.warning(f"Por favor ingrese exactamente {dim_v} variables para poder continuar.")
        return
        
    variables_simbolicas = tuple(sp.symbols(v) for v in lista_vars)

    st.divider()

    # ==============================================================================
    # 2.5. ENTRADA DIRECTA DE BASES 
    # ==============================================================================
    st.subheader("Bases no canónicas")
    with st.expander("¿Desea usar bases no canónicas?"):
        st.info("Escriba cada vector columna encerrado en corchetes `[...]` y separado por comas. El sistema extraerá los vectores automáticamente.")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.write("Base Dominio (V):")
            b1_input = st.text_area("Vectores (ej: [1,0], [1,1])", value="", key="base_v")
        with col_b2:
            st.write("Base Codominio (W):")
            b2_input = st.text_area("Vectores (ej: [1,0,0], [0,1,0], [0,0,1])", value="", key="base_w")
            
        try:
            vecs_b1 = re.findall(r'\[(.*?)\]', b1_input)
            Base1 = sp.Matrix([[parse_expr(c) for c in v.split(',')] for v in vecs_b1]).T if vecs_b1 else sp.eye(dim_v)
            
            vecs_b2 = re.findall(r'\[(.*?)\]', b2_input)
            Base2 = sp.Matrix([[parse_expr(c) for c in v.split(',')] for v in vecs_b2]).T if vecs_b2 else sp.eye(dim_w)
            
            if vecs_b1 or vecs_b2:
                if Base1.det() == 0 or Base2.det() == 0:
                    st.error("Error: Las bases ingresadas tienen determinante 0 (No son L.I.).")
                    Base1, Base2 = sp.eye(dim_v), sp.eye(dim_w)
                else:
                    st.success("Bases procesadas y vinculadas correctamente.")
        except Exception as e:
            st.error("Error en formato de vectores. Usando canónica.")
            Base1 = sp.eye(dim_v)
            Base2 = sp.eye(dim_w)

    st.divider()

    # ==============================================================================
    # 3. MÉTODOS DE DEFINICIÓN (MENÚ PRINCIPAL)
    # ==============================================================================
    st.subheader("4. Configuración de la Regla")
    metodo = st.radio(
        "Seleccione el método para definir la transformación:",
        ["1. Dar Regla de Correspondencia / Operador", "2. Definir una Matriz Nueva", "3. Importar una Matriz Preexistente"],
        key="tl_metodo_def"
    )

    if "1. Dar Regla de Correspondencia" in metodo:
        if tipo_dom == "Polinomios (Pn)" and tipo_cod == "Polinomios (Pn)":
            st.markdown("""
            💡 **Sintaxis del Motor de Cálculo (SymPy):** Use **`p`** para referirse al polinomio, **`x`** como variable principal y **`t`** como auxiliar.
            * **Derivada ($p'(x)$):** `diff(p, x)` | Segunda derivada: `diff(p, x, 2)`
            * **Integral Indefinida ($\int p(x)dx$):** `integrate(p, x)`
            * **Integral Definida ($\int_0^x p(t)dt$):** `integrate(p.subs(x, t), (t, 0, x))`
            * **Combinaciones Lineales:** `2*diff(p,x) + x*p`
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
                    
                    matriz_regla = sp.Matrix(vector_columna)
                    st.session_state.temp_tl_mat = matriz_regla.jacobian(variables_simbolicas)
                    st.session_state.temp_tl_reg = matriz_regla
                    st.session_state.temp_b1 = Base1
                    st.session_state.temp_b2 = Base2
                    st.rerun()
                except Exception as e:
                    st.error(f"Error de sintaxis en el operador: {e}")
        else:
            if tipo_dom == "Polinomios (Pn)":
                st.info(f"📝 Cada entrada representa la componente del vector de salida calculada a partir de los coeficientes: {variables_simbolicas}")
            st.write("Ingrese las funciones componentes del vector de salida:")
            with st.form("form_regla_tl"):
                eqs_input = [st.text_input(f"Componente {i+1}:", value="0", key=f"comp_val_{i}") for i in range(dim_w)]
                submit_regla = st.form_submit_button("Procesar Regla de Correspondencia")
            
            if submit_regla:
                vector_columna = []
                error_parsing = False
                for eq in eqs_input:
                    val = leer_expresion_st(eq)
                    if val is None:
                        error_parsing = True
                        break
                    vector_columna.append(val)
                
                if not error_parsing:
                    try:
                        matriz_regla = sp.Matrix(vector_columna)
                        sustitucion_cero = {v: 0 for v in variables_simbolicas}
                        
                        if not all(e == 0 for e in matriz_regla.subs(sustitucion_cero)):
                            st.error("Error Matemático: La transformación NO es lineal (T(0) ≠ 0).")
                        else:
                            st.session_state.temp_tl_mat = matriz_regla.jacobian(variables_simbolicas)
                            st.session_state.temp_tl_reg = matriz_regla
                            st.session_state.temp_b1 = Base1
                            st.session_state.temp_b2 = Base2
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error matemático al construir la matriz: {e}")

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
                matriz_asoc = sp.Matrix([[parse_expr(cell) for cell in row] for row in matriz_elementos])
                st.session_state.temp_tl_mat = matriz_asoc
                st.session_state.temp_tl_reg = matriz_asoc * sp.Matrix(variables_simbolicas)
                st.session_state.temp_b1 = Base1
                st.session_state.temp_b2 = Base2
                st.rerun()
            except Exception as e:
                st.error(f"Error al parsear los elementos de la matriz: {e}")

    elif "3. Importar una Matriz Preexistente" in metodo:
        if st.session_state.mis_matrices:
            mat_sel = st.selectbox("Seleccione una matriz de su inventario global:", list(st.session_state.mis_matrices.keys()))
            M_imp = st.session_state.mis_matrices[mat_sel]
            
            if M_imp.shape != (dim_w, dim_v):
                st.error(f"Incompatibilidad de dimensiones: La matriz mide {M_imp.shape[0]}x{M_imp.shape[1]}, el espacio requiere {dim_w}x{dim_v}.")
            else:
                if st.button("Vincular Matriz Seleccionada"):
                    st.session_state.temp_tl_mat = M_imp
                    st.session_state.temp_tl_reg = M_imp * sp.Matrix(variables_simbolicas)
                    st.session_state.temp_b1 = Base1
                    st.session_state.temp_b2 = Base2
                    st.success("Matriz vinculada. Vea el resumen abajo.")
                    st.rerun()
        else:
            st.warning("No hay matrices guardadas en el inventario actual.")

    # ==============================================================================
    # 4. BLOQUE DE CONFIRMACIÓN Y GUARDADO PERSISTENTE
    # ==============================================================================
    if 'temp_tl_mat' in st.session_state:
        st.divider()
        st.subheader("Resultados Previos a Guardar")
        st.write("**Matriz Asociada resultante:**")
        imprimir_matriz_simbolica(st.session_state.temp_tl_mat)
        st.write("**Regla de correspondencia analítica:**")
        imprimir_matriz_simbolica(st.session_state.temp_tl_reg)
        
        nombre_tl = st.text_input("Asigne un nombre para guardar esta T.L. (Ej. T1):", key="save_tl_final").upper().strip()
        
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("💾 Almacenar Transformación"):
                if nombre_tl:
                    st.session_state.mis_transformaciones[nombre_tl] = {
                        "dim_V": dim_v,
                        "dim_W": dim_w,
                        "variables": variables_simbolicas,
                        "matriz_asociada": st.session_state.temp_tl_mat,
                        "regla": st.session_state.temp_tl_reg,
                        "base_dominio": st.session_state.temp_b1,
                        "base_codominio": st.session_state.temp_b2
                    }
                    for temp_var in ['temp_tl_mat', 'temp_tl_reg', 'temp_b1', 'temp_b2']:
                        del st.session_state[temp_var]
                    st.success(f"¡Transformación '{nombre_tl}' guardada con éxito!")
                    st.rerun()
                else:
                    st.error("Por favor proporcione un nombre válido antes de guardar.")
        with col_btn2:
            if st.button("❌ Cancelar"):
                for temp_var in ['temp_tl_mat', 'temp_tl_reg', 'temp_b1', 'temp_b2']:
                    del st.session_state[temp_var]
                st.rerun()

def mostrar_detalle_tl(nombre, tl_data):
    """Muestra un resumen profesional de la transformación."""
    st.info(f"### Detalles: {nombre}")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Dominio:** R^{tl_data['dim_V']}")
        st.write(f"**Codominio:** R^{tl_data['dim_W']}")
    with col2:
        st.write(f"**Variables:** {', '.join([str(v) for v in tl_data['variables']])}")
    
    st.write("**Regla de Correspondencia:**")
    st.latex(sp.latex(tl_data['regla']))
    st.write("**Matriz Asociada:**")
    imprimir_matriz_simbolica(tl_data['matriz_asociada'])
