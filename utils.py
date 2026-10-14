# Programa: utils.py
# Objetivo: Utilidades compartidas de Álgebra Lineal, parser seguro y constructores de UI
# Autores: Fernández José y Rebeca Ortega
# ---------------------------------------------------------- #

import multiprocessing
import re
import numpy as np
import streamlit as st
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from interprete_latex import ErrorLatex, ascii_a_sympy, latex_a_sympy, leer_en_espanol
from teclado_matematico import teclado_matematico


# ==============================================================================
# 1. INICIALIZACIÓN SEGURA DE MEMORIA (SESSION STATE)
# ==============================================================================
def inicializar_estado():
    """Inicializa los diccionarios globales de trabajo en st.session_state."""
    for clave in ("mis_matrices", "mis_vectores", "mis_transformaciones", "mis_complejos"):
        if clave not in st.session_state:
            st.session_state[clave] = {}


# Inicialización automática al importar (sin llamar a st.set_page_config)
try:
    inicializar_estado()
except Exception:
    pass


# ==============================================================================
# 2. FUNCIONES DE APOYO Y PARSER SEGURO
# ==============================================================================
def parse_seguro(entrada_str, transformaciones=None, local_dict=None):
    """
    Analizador matemático seguro.
    Si no se requiere un local_dict especial (como funciones de EDO o polinomios),
    delega directamente en ascii_a_sympy (AST puro sin eval).
    """
    if entrada_str is None or not str(entrada_str).strip():
        return None
    texto = str(entrada_str).strip()

    # 1. Bloqueo de métodos y atributos (ej. os.system), permitiendo decimales (3.14)
    if re.search(r"\.[a-zA-Z_]", texto):
        raise ValueError("El acceso a atributos (.) no está permitido por seguridad.")

    # 2. Bloqueo estricto de variables ocultas (dunders)
    if "__" in texto:
        raise ValueError("El uso de dunders (__) no está permitido.")

    # 3. Bloqueo de funciones nativas peligrosas de Python
    palabras_prohibidas = r"\b(import|eval|exec|compile|open|globals|locals|getattr|setattr|delattr|os|sys|subprocess)\b"
    if re.search(palabras_prohibidas, texto):
        raise ValueError("Uso de comandos de sistema no permitidos.")

    # Si el diccionario local solo tiene i/j/I o está vacío, usamos nuestro AST parser seguro
    solo_imag = not local_dict or set(local_dict.keys()) <= {"i", "j", "I"}
    if solo_imag:
        usa_imag = bool(local_dict and ("i" in local_dict or "I" in local_dict))
        texto_norm = re.sub(r"\bj\b", "I", texto) if usa_imag else texto
        try:
            return ascii_a_sympy(texto_norm, reales=not usa_imag, i_imaginaria=usa_imag)
        except ErrorLatex:
            pass

    if transformaciones is None:
        transformaciones = standard_transformations + (implicit_multiplication_application, convert_xor)
    if local_dict is None:
        local_dict = {}

    return parse_expr(texto, transformations=transformaciones, local_dict=local_dict)


def evaluar_numerico(matriz_sp):
    """
    Verifica si la matriz de SymPy es puramente numérica y real, y la convierte a
    NumPy (float64) para cálculos rápidos. Retorna None si hay variables o complejos.
    """
    if matriz_sp.free_symbols or matriz_sp.has(sp.I):
        return None
    try:
        return np.array(matriz_sp, dtype=np.float64)
    except Exception:
        return None


def calcular_con_limite(func, args=(), kwargs=None, timeout=6):
    """
    Ejecuta una función pesada de SymPy en un proceso separado y lo termina
    si excede el timeout. Evita congelar el servidor.
    """
    if kwargs is None:
        kwargs = {}
    ctx = multiprocessing.get_context("spawn")
    pool = ctx.Pool(processes=1)
    resultado_async = pool.apply_async(func, args, kwargs)

    try:
        resultado = resultado_async.get(timeout=timeout)
        pool.close()
        pool.join()
        return resultado
    except multiprocessing.TimeoutError:
        pool.terminate()
        pool.join()
        raise TimeoutError(
            f"El cálculo matemático superó el tiempo máximo de {timeout} segundos. "
            "Simplifique la matriz o evalúela numéricamente."
        )
    except Exception as e:
        pool.terminate()
        pool.join()
        raise e


def imprimir_matriz_simbolica(matriz_sp):
    """Renderiza una matriz o vector de SymPy usando st.latex."""
    if matriz_sp is not None:
        st.latex(sp.latex(matriz_sp))


def leer_expresion_st(entrada_str, solo_reales=False):
    """
    Analiza una cadena ingresada en un widget y la convierte en un objeto SymPy.
    Retorna el objeto SymPy si es válido, o None (mostrando st.error) si falla.
    """
    if entrada_str is None or not str(entrada_str).strip():
        return None

    transformaciones = standard_transformations + (implicit_multiplication_application, convert_xor)
    diccionario_imaginario = {"i": sp.I, "j": sp.I, "I": sp.I}

    try:
        expresion = parse_seguro(
            str(entrada_str),
            transformaciones=transformaciones,
            local_dict={} if solo_reales else diccionario_imaginario,
        )

        if not isinstance(expresion, sp.Expr):
            st.error(f"'{entrada_str}' no es una expresión algebraica válida.")
            return None
        if solo_reales and expresion.has(sp.I):
            st.error("Esta operación requiere números reales.")
            return None
        if expresion.has(sp.oo, sp.zoo, sp.nan, -sp.oo):
            st.error("Error matemático: Evaluación a infinito o división por cero.")
            return None

        return expresion
    except ValueError as ve:
        st.error(str(ve))
        return None
    except Exception:
        st.error(f"La expresión '{entrada_str}' no es válida matemáticamente.")
        return None


# ==============================================================================
# 3. MÓDULOS DE CREACIÓN DE MATRICES Y TRANSFORMACIONES
# ==============================================================================
def Crear_Matriz_Simbolica_UI(nombre_matriz=""):
    """Crea una matriz simbólica celda por celda dentro de un contenedor visual."""
    if not nombre_matriz:
        st.info("Escriba un nombre para la matriz arriba para comenzar.")
        return None

    st.markdown(f"### Crear Matriz: {nombre_matriz}")

    col_m, col_n = st.columns(2)
    with col_m:
        filas = st.number_input("Renglones", min_value=1, max_value=6, value=3, step=1, key=f"f_{nombre_matriz}")
    with col_n:
        columnas = st.number_input("Columnas", min_value=1, max_value=6, value=3, step=1, key=f"c_{nombre_matriz}")

    st.caption("Ingrese las componentes individuales de la matriz (admite números, fracciones y variables como 'x', '2*y'):")

    with st.container(border=True):
        st.markdown("#### Componentes de la Matriz")

        matriz_elementos = []
        error_sintaxis = False

        for i in range(filas):
            cols = st.columns(columnas)
            fila_vals = []
            for j in range(columnas):
                with cols[j]:
                    val_str = st.text_input(
                        f"Componente ({i+1}, {j+1}):",
                        value="0",
                        key=f"celda_{nombre_matriz}_{i}_{j}_{filas}_{columnas}",
                    ).strip()

                    try:
                        val_sym = parse_seguro(
                            val_str,
                            transformaciones=standard_transformations + (implicit_multiplication_application, convert_xor),
                            local_dict={"i": sp.I, "j": sp.I, "I": sp.I},
                        )
                        if val_sym is None:
                            error_sintaxis = True
                        else:
                            fila_vals.append(val_sym)
                    except Exception:
                        error_sintaxis = True
            matriz_elementos.append(fila_vals)

        st.write("")
        if error_sintaxis:
            st.error("⚠ Ingrese expresiones matemáticas o números válidos en todas las celdas.")
            return None

        matriz_temp = sp.Matrix(matriz_elementos)

        st.markdown("**Vista previa:**")
        st.latex(f"{nombre_matriz} = {sp.latex(matriz_temp)}")

        if st.button("Guardar Matriz", key=f"btn_save_{nombre_matriz}", use_container_width=True):
            return matriz_temp

    return None


def _etiqueta_espacio(tipo: str, dim: int, m: int = 0, n: int = 0) -> str:
    if tipo == "R^n":
        return rf"\mathbb{{R}}^{{{dim}}}"
    if tipo == "C^n":
        return rf"\mathbb{{C}}^{{{dim}}}"
    if tipo == "Polinomios (Pn)":
        return rf"P_{{{dim - 1}}}(\mathbb{{R}})"
    return rf"M_{{{m}\times {n}}}(\mathbb{{R}})"


def Crear_Transformacion_UI():
    inicializar_estado()
    st.subheader("1. Espacios Vectoriales (Dominio y Codominio)")

    col_dom, col_cod = st.columns(2)
    m1 = n1 = m2 = n2 = 0

    with col_dom:
        st.markdown('<div class="card-subheader-title">Dominio (V)</div>', unsafe_allow_html=True)
        tipo_dom = st.selectbox(
            "Espacio Vectorial del Dominio",
            ["R^n", "C^n", "Polinomios (Pn)", "Matrices (mxn)"],
            key="tl_tipo_dom",
        )
        if tipo_dom in ["R^n", "C^n"]:
            dim_v = int(st.number_input("Dimensión n (Dominio):", min_value=1, max_value=8, value=3, key="tl_dim_v_rn"))
        elif tipo_dom == "Polinomios (Pn)":
            grado = int(st.number_input("Grado máximo n (Dominio):", min_value=0, max_value=6, value=2, key="tl_dim_v_pn"))
            dim_v = grado + 1
        else:
            c_m1, c_n1 = st.columns(2)
            with c_m1:
                m1 = int(st.number_input("Filas m (Dominio):", min_value=1, max_value=4, value=2, key="tl_m1"))
            with c_n1:
                n1 = int(st.number_input("Columnas n (Dominio):", min_value=1, max_value=4, value=2, key="tl_n1"))
            dim_v = m1 * n1

    with col_cod:
        st.markdown('<div class="card-subheader-title">Codominio (W)</div>', unsafe_allow_html=True)
        tipo_cod = st.selectbox(
            "Espacio Vectorial del Codominio",
            ["R^n", "C^n", "Polinomios (Pn)", "Matrices (mxn)"],
            key="tl_tipo_cod",
        )
        if tipo_cod in ["R^n", "C^n"]:
            dim_w = int(st.number_input("Dimensión m (Codominio):", min_value=1, max_value=8, value=3, key="tl_dim_w_rn"))
        elif tipo_cod == "Polinomios (Pn)":
            grado_cod = int(st.number_input("Grado máximo m (Codominio):", min_value=0, max_value=6, value=2, key="tl_dim_w_pn"))
            dim_w = grado_cod + 1
        else:
            c_m2, c_n2 = st.columns(2)
            with c_m2:
                m2 = int(st.number_input("Filas m (Codominio):", min_value=1, max_value=4, value=2, key="tl_m2"))
            with c_n2:
                n2 = int(st.number_input("Columnas n (Codominio):", min_value=1, max_value=4, value=2, key="tl_n2"))
            dim_w = m2 * n2

    desc_V = _etiqueta_espacio(tipo_dom, dim_v, m1, n1)
    desc_W = _etiqueta_espacio(tipo_cod, dim_w, m2, n2)
    st.latex(rf"T : {desc_V} \longrightarrow {desc_W}")

    st.divider()

    # ==============================================================================
    # 2. CAPTURA PREVIA DE VARIABLES
    # ==============================================================================
    st.subheader("2. Variables del Dominio (Coordenadas)")

    if tipo_dom == "Polinomios (Pn)":
        if dim_v == 3:
            default_vars = "a, b, c"
            poly_ejemplo = "ax^2 + bx + c"
        elif dim_v == 2:
            default_vars = "m, b"
            poly_ejemplo = "mx + b"
        else:
            default_vars = ", ".join([f"a_{i}" for i in range(dim_v - 1, -1, -1)])
            vars_list = [v.strip() for v in default_vars.split(",")]
            poly_ejemplo = f"{vars_list[0]}x^{dim_v-1} + ... + {vars_list[-1]}"

        st.info(
            rf"💡 **Notación Polinomial:** Cada variable representa un coeficiente ordenado de mayor a menor grado. "
            rf"Ejemplo: $p(x) = {poly_ejemplo}$"
        )
    else:
        if dim_v <= 4:
            default_vars = ", ".join(["x", "y", "z", "w"][:dim_v])
        else:
            default_vars = ", ".join([f"x_{i+1}" for i in range(dim_v)])
        st.caption(f"Defina las {dim_v} variables de su vector de entrada.")

    vars_str = st.text_input("Ingrese las variables separadas por comas:", value=default_vars, key="tl_vars_input")
    lista_vars = [v.strip() for v in vars_str.split(",") if v.strip()]

    if len(lista_vars) != dim_v:
        st.warning(f"Por favor ingrese exactamente {dim_v} variables para poder continuar.")
        return

    variables_simbolicas = tuple(sp.Symbol(v, real=(tipo_dom != "C^n")) for v in lista_vars)

    st.divider()

    # ==============================================================================
    # 2.5. ENTRADA DIRECTA DE BASES
    # ==============================================================================
    st.subheader("3. Bases del Dominio y Codominio")
    with st.expander("¿Desea ingresar bases no canónicas explícitas?"):
        st.markdown(r"""
        💡 **¿Cómo introducir los vectores de la base?**
        Todo elemento de un espacio vectorial debe ingresarse como su **vector de coordenadas (columna)** encerrado en corchetes `[...]` y separado por comas:
        * **Para $\mathbb{R}^n$:** Ingrese las componentes directamente. Ej. para $\mathbb{R}^2$: `[1, 2], [-1, 1]`
        * **Para Polinomios ($P_n$):** Ingrese los coeficientes ordenados según sus variables. Ej. para $P_2$ ($ax^2+bx+c$), la base $\{x^2+1, x, 1\}$ se ingresa como: `[1,0,1], [0,1,0], [0,0,1]`
        * **Para Matrices ($M_{m \times n}$):** Aplane la matriz fila por fila.
        """)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            b1_input = st.text_area("Base Dominio (V):", value="", placeholder="Deje en blanco para usar la canónica", key="base_v")
        with col_b2:
            b2_input = st.text_area("Base Codominio (W):", value="", placeholder="Deje en blanco para usar la canónica", key="base_w")

        Base1, Base2 = sp.eye(dim_v), sp.eye(dim_w)
        try:
            vecs_b1 = re.findall(r"\[(.*?)\]", b1_input)
            if vecs_b1:
                Base1 = sp.Matrix([[leer_expresion_st(c) for c in v.split(",")] for v in vecs_b1]).T
                if Base1.shape != (dim_v, dim_v) or Base1.det() == 0:
                    st.error(f"Error: La base del dominio debe tener {dim_v} vectores de dimensión {dim_v} linealmente independientes.")
                    Base1 = sp.eye(dim_v)

            vecs_b2 = re.findall(r"\[(.*?)\]", b2_input)
            if vecs_b2:
                Base2 = sp.Matrix([[leer_expresion_st(c) for c in v.split(",")] for v in vecs_b2]).T
                if Base2.shape != (dim_w, dim_w) or Base2.det() == 0:
                    st.error(f"Error: La base del codominio debe tener {dim_w} vectores de dimensión {dim_w} linealmente independientes.")
                    Base2 = sp.eye(dim_w)

            if (vecs_b1 and Base1 != sp.eye(dim_v)) or (vecs_b2 and Base2 != sp.eye(dim_w)):
                st.success("Bases no canónicas procesadas y vinculadas correctamente.")
        except Exception:
            st.error("Error en formato de vectores de la base. Usando base canónica.")
            Base1, Base2 = sp.eye(dim_v), sp.eye(dim_w)

    st.divider()

    # ==============================================================================
    # 3. MÉTODOS DE DEFINICIÓN
    # ==============================================================================
    st.subheader("4. Configuración de la Regla")
    metodo = st.radio(
        "Seleccione el método para definir la transformación:",
        ["1. Dar Regla de Correspondencia / Operador", "2. Definir una Matriz Nueva", "3. Importar una Matriz Preexistente"],
        key="tl_metodo_def",
    )

    if "1. Dar Regla de Correspondencia" in metodo:
        usar_teclado = st.toggle("🎹 Usar Teclado Matemático Interactivo (LaTeX)", value=True, key="tl_usar_teclado")

        if tipo_dom == "Polinomios (Pn)" and tipo_cod == "Polinomios (Pn)":
            x_sym = sp.Symbol("x", real=True)
            p_poly = sum(variables_simbolicas[i] * x_sym ** (dim_v - 1 - i) for i in range(dim_v))
            st.markdown(rf"**Polinomio genérico de entrada:** $p(x) = {sp.latex(p_poly)}$")

            expr_op_raw = None
            if usar_teclado:
                st.caption("Usa la letra `p` para el polinomio y `x` para la variable. Puedes usar las teclas `d/dx` o `∫` del teclado.")
                latex_op = teclado_matematico(
                    "tl_op_latex",
                    valor_inicial=r"\frac{\mathrm{d}}{\mathrm{d}x}p",
                    placeholder="Escribe el operador sobre p, ej. d/dx p + x*p",
                    acoplado=True,
                )
                if latex_op:
                    try:
                        expr_op_raw = latex_a_sympy(latex_op)
                        st.caption(f"**Entiendo:** `{leer_en_espanol(expr_op_raw)}`")
                    except ErrorLatex as e:
                        st.error(f"Error en la fórmula: {e}")
            else:
                st.caption("Sintaxis de texto: `diff(p, x)`, `diff(p, x, 2)`, `integrate(p, x)`, `2*diff(p,x) + x*p`.")
                regla_str = st.text_input("Ingrese el operador T(p) =", value="diff(p, x)", key="tl_regla_op")
                if regla_str.strip():
                    try:
                        diccionario_local = {"p": p_poly, "x": x_sym, "diff": sp.diff, "integrate": sp.integrate}
                        expr_op_raw = parse_seguro(regla_str, local_dict=diccionario_local)
                    except Exception as e:
                        st.error(f"Error de sintaxis en el operador: {e}")

            if st.button("🧮 Construir Transformación desde Operador", use_container_width=True):
                if expr_op_raw is None:
                    st.error("Primero escriba y confirme un operador válido.")
                else:
                    try:
                        p_sym = sp.Symbol("p", real=True)
                        expr_sust = expr_op_raw.subs(p_sym, p_poly).doit()
                        expr_evaluada = sp.expand(expr_sust)

                        poly_res = sp.Poly(expr_evaluada, x_sym)
                        if poly_res.degree() > dim_w - 1:
                            st.error(
                                f"Error Matemático: El operador produce un polinomio de grado {poly_res.degree()}, "
                                f"que excede el grado máximo del codominio ({dim_w - 1})."
                            )
                        else:
                            vector_columna = [expr_evaluada.coeff(x_sym, g) for g in range(dim_w - 1, 0, -1)]
                            vector_columna.append(expr_evaluada.subs(x_sym, 0))
                            matriz_regla = sp.Matrix(vector_columna)
                            sustitucion_cero = {v: 0 for v in variables_simbolicas}

                            A_can = matriz_regla.jacobian(variables_simbolicas)
                            if not all(sp.simplify(e) == 0 for e in matriz_regla.subs(sustitucion_cero)) or (
                                A_can.free_symbols & set(variables_simbolicas)
                            ):
                                st.error("Error Matemático: El operador definido NO es una transformación lineal.")
                            else:
                                M_asociada = sp.simplify(Base2.inv() * A_can * Base1)
                                st.session_state.temp_tl_mat = M_asociada
                                st.session_state.temp_tl_can = A_can
                                st.session_state.temp_tl_reg = matriz_regla
                                st.session_state.temp_b1 = Base1
                                st.session_state.temp_b2 = Base2
                                st.session_state.temp_desc_v = desc_V
                                st.session_state.temp_desc_w = desc_W
                                st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo evaluar como polinomio en x: {e}")

        else:
            st.write(f"Defina las **{dim_w}** funciones componentes del vector de salida en términos de $({', '.join(lista_vars)})$:")
            vector_columna = []
            error_parsing = False

            if usar_teclado:
                st.caption("Toca cada componente para editarla con el teclado matemático y pulsa **↵**.")
                for i in range(dim_w):
                    lat_i = teclado_matematico(
                        f"tl_comp_latex_{dim_v}_{dim_w}_{i}",
                        valor_inicial=lista_vars[i] if i < len(lista_vars) else "0",
                        placeholder=f"Componente {i+1}",
                        acoplado=True,
                        en_vivo=True,
                    )
                    if not lat_i.strip():
                        vector_columna.append(sp.Integer(0))
                    else:
                        try:
                            expr_i = latex_a_sympy(lat_i, reales=(tipo_dom != "C^n"), i_imaginaria=(tipo_dom == "C^n"))
                            vector_columna.append(expr_i)
                        except ErrorLatex as e:
                            st.error(f"Componente {i+1}: {e}")
                            error_parsing = True

                procesar_btn = st.button("🧮 Procesar Regla de Correspondencia", use_container_width=True)
            else:
                with st.form("form_regla_tl"):
                    eqs_input = [
                        st.text_input(
                            f"Componente {i+1}:",
                            value=lista_vars[i] if i < len(lista_vars) else "0",
                            key=f"comp_val_{i}",
                        )
                        for i in range(dim_w)
                    ]
                    procesar_btn = st.form_submit_button("🧮 Procesar Regla de Correspondencia", use_container_width=True)
                if procesar_btn:
                    for eq in eqs_input:
                        val = leer_expresion_st(eq, solo_reales=(tipo_dom != "C^n"))
                        if val is None:
                            error_parsing = True
                            break
                        vector_columna.append(val)

            if procesar_btn and not error_parsing:
                try:
                    matriz_regla = sp.Matrix(vector_columna)
                    vars_usadas = matriz_regla.free_symbols
                    vars_extra = vars_usadas - set(variables_simbolicas)
                    if vars_extra:
                        st.error(
                            "Error: Usaste variables que no pertenecen al dominio declarado: "
                            + ", ".join(str(s) for s in vars_extra)
                        )
                    else:
                        sustitucion_cero = {v: 0 for v in variables_simbolicas}
                        A_can = matriz_regla.jacobian(variables_simbolicas)

                        # Validación rigurosa de linealidad: T(0) = 0 y Jacobiano constante
                        pasa_por_origen = all(sp.simplify(e) == 0 for e in matriz_regla.subs(sustitucion_cero))
                        jacobiano_constante = not bool(A_can.free_symbols & set(variables_simbolicas))

                        if not pasa_por_origen:
                            st.error("Error Matemático: La transformación NO es lineal porque $T(\\mathbf{0}) \\neq \\mathbf{0}$ (contiene términos constantes).")
                        elif not jacobiano_constante:
                            st.error(
                                "Error Matemático: La transformación NO es lineal (contiene potencias no lineales, productos entre variables o funciones trascendentes)."
                            )
                        else:
                            M_asociada = sp.simplify(Base2.inv() * A_can * Base1)
                            st.session_state.temp_tl_mat = M_asociada
                            st.session_state.temp_tl_can = A_can
                            st.session_state.temp_tl_reg = matriz_regla
                            st.session_state.temp_b1 = Base1
                            st.session_state.temp_b2 = Base2
                            st.session_state.temp_desc_v = desc_V
                            st.session_state.temp_desc_w = desc_W
                            st.rerun()
                except Exception as e:
                    st.error(f"Error matemático al construir la matriz: {e}")

    elif "2. Definir una Matriz Nueva" in metodo:
        st.write(f"Construya la matriz asociada $[T]_\\beta^\\gamma$ de dimensiones $({dim_w}\\times {dim_v})$:")
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
            submit_mat = st.form_submit_button("Generar Transformación desde Matriz", use_container_width=True)

        if submit_mat:
            try:
                celdas_eval = [[leer_expresion_st(cell) for cell in row] for row in matriz_elementos]
                if any(c is None for row in celdas_eval for c in row):
                    st.error("Verifique que todas las celdas contengan valores válidos.")
                else:
                    matriz_asoc = sp.Matrix(celdas_eval)
                    A_can = sp.simplify(Base2 * matriz_asoc * Base1.inv())
                    regla_canonica = sp.simplify(A_can * sp.Matrix(variables_simbolicas))

                    st.session_state.temp_tl_mat = matriz_asoc
                    st.session_state.temp_tl_can = A_can
                    st.session_state.temp_tl_reg = regla_canonica
                    st.session_state.temp_b1 = Base1
                    st.session_state.temp_b2 = Base2
                    st.session_state.temp_desc_v = desc_V
                    st.session_state.temp_desc_w = desc_W
                    st.rerun()
            except Exception as e:
                st.error(f"Error al procesar los elementos de la matriz: {e}")

    elif "3. Importar una Matriz Preexistente" in metodo:
        if st.session_state.mis_matrices:
            mat_sel = st.selectbox("Seleccione una matriz de su inventario global:", list(st.session_state.mis_matrices.keys()))
            M_imp = st.session_state.mis_matrices[mat_sel]

            if M_imp.shape != (dim_w, dim_v):
                st.error(
                    f"Incompatibilidad de dimensiones: La matriz mide {M_imp.shape[0]}×{M_imp.shape[1]}, "
                    f"pero el espacio requiere {dim_w}×{dim_v}."
                )
            else:
                if st.button("Vincular Matriz Seleccionada", use_container_width=True):
                    A_can = sp.simplify(Base2 * M_imp * Base1.inv())
                    regla_canonica = sp.simplify(A_can * sp.Matrix(variables_simbolicas))

                    st.session_state.temp_tl_mat = M_imp
                    st.session_state.temp_tl_can = A_can
                    st.session_state.temp_tl_reg = regla_canonica
                    st.session_state.temp_b1 = Base1
                    st.session_state.temp_b2 = Base2
                    st.session_state.temp_desc_v = desc_V
                    st.session_state.temp_desc_w = desc_W
                    st.success("Matriz vinculada. Vea el resumen abajo.")
                    st.rerun()
        else:
            st.warning("No hay matrices guardadas en el inventario actual.")

    # ==============================================================================
    # 4. BLOQUE DE CONFIRMACIÓN Y GUARDADO PERSISTENTE
    # ==============================================================================
    if "temp_tl_mat" in st.session_state:
        st.divider()
        st.subheader("Resultados Previos a Guardar")
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.write("**Matriz Asociada ($[T]_\\beta^\\gamma$):**")
            imprimir_matriz_simbolica(st.session_state.temp_tl_mat)
        with col_res2:
            st.write("**Regla de correspondencia en coordenadas canónicas:**")
            imprimir_matriz_simbolica(st.session_state.temp_tl_reg)

        nombre_tl = st.text_input("Asigne un nombre para guardar esta T.L. (Ej. T1):", key="save_tl_final").upper().strip()

        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("💾 Almacenar Transformación", use_container_width=True):
                if nombre_tl:
                    st.session_state.mis_transformaciones[nombre_tl] = {
                        "dim_V": dim_v,
                        "dim_W": dim_w,
                        "desc_V": st.session_state.get("temp_desc_v", desc_V),
                        "desc_W": st.session_state.get("temp_desc_w", desc_W),
                        "variables": variables_simbolicas,
                        "matriz_asociada": st.session_state.temp_tl_mat,
                        "matriz_canonica": st.session_state.get("temp_tl_can", st.session_state.temp_tl_mat),
                        "regla": st.session_state.temp_tl_reg,
                        "base_dominio": st.session_state.temp_b1,
                        "base_codominio": st.session_state.temp_b2,
                    }
                    for temp_var in ("temp_tl_mat", "temp_tl_can", "temp_tl_reg", "temp_b1", "temp_b2", "temp_desc_v", "temp_desc_w"):
                        st.session_state.pop(temp_var, None)
                    st.success(f"¡Transformación '{nombre_tl}' guardada con éxito!")
                    st.rerun()
                else:
                    st.error("Por favor proporcione un nombre válido antes de guardar.")
        with col_btn2:
            if st.button("❌ Cancelar", use_container_width=True):
                for temp_var in ("temp_tl_mat", "temp_tl_can", "temp_tl_reg", "temp_b1", "temp_b2", "temp_desc_v", "temp_desc_w"):
                    st.session_state.pop(temp_var, None)
                st.rerun()


def mostrar_detalle_tl(nombre, tl_data):
    """Muestra un resumen formal y completo de la transformación lineal."""
    desc_v = tl_data.get("desc_V", rf"\mathbb{{R}}^{{{tl_data['dim_V']}}}")
    desc_w = tl_data.get("desc_W", rf"\mathbb{{R}}^{{{tl_data['dim_W']}}}")

    st.markdown(f"#### Transformación ${nombre} : {desc_v} \\longrightarrow {desc_w}$")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Dimensión del Dominio ($\dim V$):** {tl_data['dim_V']}")
        st.write(f"**Dimensión del Codominio ($\dim W$):** {tl_data['dim_W']}")
    with col2:
        st.write(f"**Variables:** {', '.join([f'${sp.latex(v)}$' for v in tl_data['variables']])}")

    c_r, c_m = st.columns(2)
    with c_r:
        st.write("**Regla de Correspondencia:**")
        st.latex(sp.latex(tl_data["regla"]))
    with c_m:
        st.write("**Matriz Asociada ($[T]_\\beta^\\gamma$):**")
        imprimir_matriz_simbolica(tl_data["matriz_asociada"])
