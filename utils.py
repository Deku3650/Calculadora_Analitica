# utils.py
# Programa: Calculadora_Avanzada / Mathesis V0.2
# Objetivo: Funciones compartidas para Álgebra Lineal, Geometría y Análisis
# Autores: José Alberto Fernández Cendejas e Ingrid Rebeca Ortega Flores
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

try:
    from teclado_matematico import teclado_matematico
    from interprete_latex import latex_a_sympy, ErrorLatex
    _TIENE_TECLADO = True
except Exception:
    _TIENE_TECLADO = False


# ==============================================================================
# 1. INICIALIZACIÓN DE MEMORIA (SESSION STATE)
# ==============================================================================
def inicializar_estado():
    """Inicializa de forma segura todas las estructuras persistentes en st.session_state."""
    defaults = {
        "mis_matrices": {},
        "mis_vectores": {},
        "mis_transformaciones": {},
        "mis_complejos": {},
        "mis_inversiones": {},
        "sys_P": None,
        "sys_Q": None,
        "sys_R": None,
    }
    for clave, valor_inicial in defaults.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor_inicial.copy() if isinstance(valor_inicial, dict) else valor_inicial


# Se ejecuta al importar para proteger páginas que no llamen explícitamente a inicializar_estado()
inicializar_estado()


# ==============================================================================
# 2. FUNCIONES DE APOYO Y PARSER SEGURO
# ==============================================================================
_SAFE_GLOBALS = {
    "__builtins__": {},
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Symbol": sp.Symbol,
    "pi": sp.pi,
    "E": sp.E,
    "e": sp.E,
    "I": sp.I,
    "oo": sp.oo,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "cot": sp.cot,
    "sec": sp.sec,
    "csc": sp.csc,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "exp": sp.exp,
    "log": sp.log,
    "ln": sp.log,
    "sqrt": sp.sqrt,
    "Abs": sp.Abs,
    "abs": sp.Abs,
    "factorial": sp.factorial,
}


def parse_seguro(entrada_str, transformaciones=None, local_dict=None):
    """
    Analizador matemático seguro.
    Bloquea inyección de código y evalúa en un entorno global sin __builtins__.
    """
    if entrada_str is None or not str(entrada_str).strip():
        return None

    entrada_str = str(entrada_str).strip()

    # 1. Bloqueo de métodos y atributos (ej. os.system), permitiendo decimales (3.14)
    if re.search(r"\.[a-zA-Z_]", entrada_str):
        raise ValueError("El acceso a atributos (.) no está permitido por seguridad.")

    # 2. Bloqueo estricto de dunders (__)
    if "__" in entrada_str:
        raise ValueError("El uso de dunders (__) no está permitido.")

    # 3. Bloqueo de funciones nativas de sistema
    palabras_prohibidas = r"\b(import|eval|exec|compile|open|globals|locals|getattr|setattr|delattr|os|sys|subprocess)\b"
    if re.search(palabras_prohibidas, entrada_str):
        raise ValueError("Uso de comandos de sistema no permitidos.")

    if transformaciones is None:
        transformaciones = standard_transformations + (implicit_multiplication_application, convert_xor)

    if local_dict is None:
        local_dict = {}

    return parse_expr(
        entrada_str,
        transformations=transformaciones,
        global_dict=_SAFE_GLOBALS.copy(),
        local_dict=local_dict,
    )


def evaluar_numerico(matriz_sp):
    """
    Verifica si la matriz de SymPy es puramente numérica real y la convierte a
    NumPy (float64) para cálculos rápidos. Retorna None si hay variables o complejos.
    """
    if matriz_sp.free_symbols or matriz_sp.has(sp.I):
        return None
    try:
        return np.array(matriz_sp.tolist(), dtype=np.float64)
    except Exception:
        return None


def calcular_con_limite(func, args=(), kwargs=None, timeout=5):
    """
    Ejecuta una función pesada de SymPy en un proceso separado y lo termina
    si excede el timeout. Evita que se congele el servidor.
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
    """Renderiza una matriz de SymPy usando LaTeX nativo de Streamlit."""
    if matriz_sp is not None:
        st.latex(sp.latex(matriz_sp))


def leer_expresion_st(entrada_str, solo_reales=False):
    """
    Analiza una cadena ingresada en un widget y la convierte en un objeto SymPy.
    Retorna el objeto SymPy si es válido, o None (mostrando error) si no lo es.
    """
    if entrada_str is None or not str(entrada_str).strip():
        return None

    transformaciones = standard_transformations + (implicit_multiplication_application, convert_xor)
    diccionario_imaginario = {"i": sp.I, "j": sp.I, "I": sp.I}

    try:
        expresion = parse_seguro(
            entrada_str,
            transformaciones=transformaciones,
            local_dict=diccionario_imaginario,
        )

        if not isinstance(expresion, sp.Expr):
            st.error(f"'{entrada_str}' no es una expresión matemática válida.")
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


def _etiqueta_espacio(tipo: str, dim: int, grado: int = 0, m: int = 0, n: int = 0) -> str:
    if tipo == "R^n":
        return rf"\mathbb{{R}}^{{{dim}}}"
    if tipo == "C^n":
        return rf"\mathbb{{C}}^{{{dim}}}"
    if tipo == "Polinomios (Pn)":
        return rf"P_{{{grado}}}(\mathbb{{R}})"
    return rf"M_{{{m}\times {n}}}(\mathbb{{R}})"


# ==============================================================================
# 3. MÓDULOS DE CREACIÓN DE MATRICES Y TRANSFORMACIONES
# ==============================================================================
def Crear_Matriz_Simbolica_UI(nombre_matriz=""):
    """Crea una matriz simbólica celda por celda dentro de un contenedor con borde."""
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
            st.error("⚠️ Ingrese expresiones matemáticas o números válidos en todas las celdas.")
            return None

        matriz_temp = sp.Matrix(matriz_elementos)

        st.markdown("**Vista previa:**")
        st.latex(f"{nombre_matriz} = {sp.latex(matriz_temp)}")

        if st.button("💾 Guardar Matriz", key=f"btn_save_{nombre_matriz}", use_container_width=True):
            return matriz_temp

    return None


def Crear_Transformacion_UI():
    st.subheader("1. Dominio ($V$) y Codominio ($W$)")
    col_dom, col_cod = st.columns(2)

    grado_dom = m_dom = n_dom = 0
    grado_cod = m_cod = n_cod = 0

    with col_dom:
        st.markdown("**Dominio ($V$)**")
        tipo_dom = st.selectbox(
            "Espacio Vectorial del Dominio",
            ["R^n", "C^n", "Polinomios (Pn)", "Matrices (mxn)"],
            key="tl_tipo_dom",
        )
        if tipo_dom in ["R^n", "C^n"]:
            dim_v = int(st.number_input("Dimensión n (Dominio):", min_value=1, max_value=8, value=3, key="tl_dim_v_rn"))
        elif tipo_dom == "Polinomios (Pn)":
            grado_dom = int(st.number_input("Grado máximo n (Dominio):", min_value=0, max_value=6, value=2, key="tl_dim_v_pn"))
            dim_v = grado_dom + 1
        else:
            m_dom = int(st.number_input("Filas m (Dominio):", min_value=1, max_value=4, value=2, key="tl_m1"))
            n_dom = int(st.number_input("Columnas n (Dominio):", min_value=1, max_value=4, value=2, key="tl_n1"))
            dim_v = m_dom * n_dom

    with col_cod:
        st.markdown("**Codominio ($W$)**")
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
            m_cod = int(st.number_input("Filas m (Codominio):", min_value=1, max_value=4, value=2, key="tl_m2"))
            n_cod = int(st.number_input("Columnas n (Codominio):", min_value=1, max_value=4, value=2, key="tl_n2"))
            dim_w = m_cod * n_cod

    etiqueta_dom = _etiqueta_espacio(tipo_dom, dim_v, grado_dom, m_dom, n_dom)
    etiqueta_cod = _etiqueta_espacio(tipo_cod, dim_w, grado_cod, m_cod, n_cod)

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
        elif dim_v == 1:
            default_vars = "c"
            poly_ejemplo = "c"
        else:
            default_vars = ", ".join([f"a{i}" for i in range(dim_v - 1, -1, -1)])
            vars_list = [v.strip() for v in default_vars.split(",")]
            poly_ejemplo = f"{vars_list[0]}x^{dim_v-1} + {vars_list[1]}x^{dim_v-2} + \\dots + {vars_list[-1]}"

        st.info(
            rf"💡 **Notación Polinomial:** Cada variable representa un coeficiente ordenado de mayor a menor grado. "
            rf"Para `{default_vars}`, el polinomio es $p(x) = {poly_ejemplo}$."
        )
    else:
        if dim_v <= 4:
            default_vars = ", ".join(["x", "y", "z", "w"][:dim_v])
        else:
            default_vars = ", ".join([f"x{i+1}" for i in range(dim_v)])
        st.caption(f"Defina las {dim_v} variables de su vector de entrada.")

    vars_str = st.text_input("Ingrese las variables separadas por comas:", value=default_vars, key="tl_vars_input")
    lista_vars = [v.strip() for v in vars_str.split(",") if v.strip()]

    if len(lista_vars) != dim_v or len(set(lista_vars)) != dim_v:
        st.warning(f"Por favor ingrese exactamente {dim_v} variables distintas para continuar.")
        return

    variables_simbolicas = tuple(sp.Symbol(v) for v in lista_vars)

    st.divider()

    # ==============================================================================
    # 3. ENTRADA DIRECTA DE BASES NO CANÓNICAS
    # ==============================================================================
    st.subheader("3. Bases del Dominio y Codominio")
    Base1 = sp.eye(dim_v)
    Base2 = sp.eye(dim_w)

    with st.expander("¿Desea ingresar bases no canónicas explícitas?"):
        st.markdown(r"""
        💡 **¿Cómo introducir los vectores de la base?**
        Todo elemento debe ingresarse como su **vector de coordenadas** encerrado en corchetes `[...]` y separado por comas:
        * **Para $\mathbb{R}^n$:** Ej. en $\mathbb{R}^2$: `[1, 2], [-1, 1]`
        * **Para Polinomios ($P_n$):** Coeficientes de mayor a menor grado. Ej. en $P_2$ ($ax^2+bx+c$), $\{x^2+1, x, 1\}$ se ingresa como: `[1,0,1], [0,1,0], [0,0,1]`
        * **Para Matrices ($M_{m \times n}$):** Aplane la matriz fila por fila.
        """)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            b1_input = st.text_area("Base Dominio (V):", value="", placeholder="Vacío = base canónica", key="base_v")
        with col_b2:
            b2_input = st.text_area("Base Codominio (W):", value="", placeholder="Vacío = base canónica", key="base_w")

        try:
            vecs_b1 = re.findall(r"\[(.*?)\]", b1_input)
            if vecs_b1:
                B1_cand = sp.Matrix([[leer_expresion_st(c) for c in v.split(",")] for v in vecs_b1]).T
                if B1_cand.shape != (dim_v, dim_v) or B1_cand.det() == 0:
                    st.error(f"Error: La base del dominio debe tener {dim_v} vectores de dimensión {dim_v} linealmente independientes.")
                else:
                    Base1 = B1_cand

            vecs_b2 = re.findall(r"\[(.*?)\]", b2_input)
            if vecs_b2:
                B2_cand = sp.Matrix([[leer_expresion_st(c) for c in v.split(",")] for v in vecs_b2]).T
                if B2_cand.shape != (dim_w, dim_w) or B2_cand.det() == 0:
                    st.error(f"Error: La base del codominio debe tener {dim_w} vectores de dimensión {dim_w} linealmente independientes.")
                else:
                    Base2 = B2_cand

            if vecs_b1 or vecs_b2:
                st.success("Bases procesadas correctamente.")
        except Exception:
            st.error("Error en formato de vectores de base. Usando bases canónicas.")
            Base1, Base2 = sp.eye(dim_v), sp.eye(dim_w)

    st.divider()

    # ==============================================================================
    # 4. MÉTODOS DE DEFINICIÓN
    # ==============================================================================
    st.subheader("4. Configuración de la Regla")
    metodo = st.radio(
        "Seleccione el método para definir la transformación:",
        [
            "1. Dar Regla de Correspondencia / Operador",
            "2. Definir una Matriz Nueva",
            "3. Importar una Matriz Preexistente",
        ],
        key="tl_metodo_def",
    )

    if "1. Dar Regla de Correspondencia" in metodo:
        usar_teclado = False
        if _TIENE_TECLADO:
            usar_teclado = st.toggle(
                "⌨️ Usar Teclado Matemático Interactivo",
                value=True,
                help="Permite escribir derivadas, integrales y expresiones con formato matemático directo.",
                key="tl_toggle_teclado",
            )

        if tipo_dom == "Polinomios (Pn)" and tipo_cod == "Polinomios (Pn)":
            x_sym = sp.Symbol("x", real=True)
            p_poly = sum(variables_simbolicas[i] * x_sym ** (dim_v - 1 - i) for i in range(dim_v))

            if usar_teclado:
                st.info(
                    "💡 Escriba el operador usando la letra **`p`** para el polinomio y **`x`** como variable "
                    "(ej. pulse la tecla $\\frac{d}{dx}$ y escriba $\\frac{d}{dx}p + x\\cdot p$)."
                )
                latex_op = teclado_matematico(
                    "tl_op_poly_kb",
                    valor_inicial=r"\frac{\mathrm{d}}{\mathrm{d}x}p",
                    placeholder="Escribe T(p) y pulsa ↵",
                    acoplado=True,
                )
                ejecutar_op = st.button("🧮 Construir desde Teclado Matemático", use_container_width=True)
            else:
                st.markdown("""
                💡 **Sintaxis de texto:** Use **`p`** para el polinomio y **`x`** como variable:
                * **Derivada:** `diff(p, x)` | **Segunda derivada:** `diff(p, x, 2)`
                * **Integral Indefinida:** `integrate(p, x)`
                """)
                regla_str = st.text_input("Ingrese el operador T(p) =", value="diff(p, x)", key="tl_regla_op")
                ejecutar_op = st.button("🧮 Construir desde Operador", use_container_width=True)

            if ejecutar_op:
                try:
                    if usar_teclado:
                        if not latex_op:
                            st.warning("Confirme la expresión en el teclado pulsando ↵.")
                            return
                        raw_expr = latex_a_sympy(latex_op)
                        p_sym = sp.Symbol("p", real=True)
                        expr_evaluada = sp.expand(raw_expr.subs(p_sym, p_poly).doit())
                    else:
                        diccionario_local = {
                            "p": p_poly,
                            "x": x_sym,
                            "diff": sp.diff,
                            "integrate": sp.integrate,
                        }
                        expr_evaluada = sp.expand(parse_seguro(regla_str, local_dict=diccionario_local))

                    poly_obj = sp.Poly(expr_evaluada, x_sym)
                    if poly_obj.degree() >= dim_w:
                        st.error(
                            f"Error Matemático: El polinomio resultante tiene grado {poly_obj.degree()}, "
                            f"que excede el grado máximo del codominio ({dim_w - 1})."
                        )
                        return

                    vector_columna = [expr_evaluada.coeff(x_sym, g) for g in range(dim_w - 1, 0, -1)]
                    vector_columna.append(expr_evaluada.subs(x_sym, 0))
                    matriz_regla = sp.Matrix(vector_columna)

                    sustitucion_cero = {v: 0 for v in variables_simbolicas}
                    A_can = matriz_regla.jacobian(variables_simbolicas)

                    if not all(sp.simplify(e) == 0 for e in matriz_regla.subs(sustitucion_cero)) or (
                        A_can.free_symbols & set(variables_simbolicas)
                    ):
                        st.error("Error Matemático: El operador definido NO es lineal.")
                    else:
                        st.success("Operador lineal evaluado con éxito:")
                        st.latex(f"T(p(x)) = {sp.latex(expr_evaluada)}")
                        M_asociada = sp.simplify(Base2.inv() * A_can * Base1)
                        st.session_state.temp_tl_mat = M_asociada
                        st.session_state.temp_tl_reg = matriz_regla
                        st.session_state.temp_b1 = Base1
                        st.session_state.temp_b2 = Base2
                        st.session_state.temp_dom_str = etiqueta_dom
                        st.session_state.temp_cod_str = etiqueta_cod
                except Exception as e:
                    st.error(f"Error al construir el operador: {e}")

        else:
            st.write(f"Defina cada una de las {dim_w} componentes de salida en términos de `{', '.join(lista_vars)}`:")
            eqs_parsed = []
            error_parsing = False

            if usar_teclado:
                st.caption("Escriba cada componente en su campo y pulse **↵** (o salga del recuadro) antes de procesar:")
                for i in range(dim_w):
                    lat_i = teclado_matematico(
                        f"tl_comp_kb_{dim_v}_{dim_w}_{i}",
                        valor_inicial=lista_vars[i] if i < len(lista_vars) else "0",
                        placeholder=f"Componente {i+1}",
                        acoplado=True,
                        en_vivo=True,
                    )
                    if lat_i:
                        try:
                            eqs_parsed.append(latex_a_sympy(lat_i, reales=(tipo_dom != "C^n"), i_imaginaria=True))
                        except ErrorLatex as err_l:
                            st.error(f"Componente {i+1}: {err_l}")
                            error_parsing = True
                    else:
                        eqs_parsed.append(sp.Integer(0))
                submit_regla = st.button("🧮 Procesar Regla de Correspondencia", use_container_width=True)
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
                    submit_regla = st.form_submit_button("🧮 Procesar Regla de Correspondencia", use_container_width=True)
                if submit_regla:
                    for eq in eqs_input:
                        val = leer_expresion_st(eq)
                        if val is None:
                            error_parsing = True
                            break
                        eqs_parsed.append(val)

            if submit_regla and not error_parsing:
                try:
                    # Normalizar símbolos por nombre para que coincidan con variables_simbolicas
                    mapa_syms = {s.name: s for s in variables_simbolicas}
                    eqs_norm = []
                    vars_extra = set()
                    for expr_c in eqs_parsed:
                        reemp = {}
                        for s in expr_c.free_symbols:
                            if s.name in mapa_syms:
                                reemp[s] = mapa_syms[s.name]
                            else:
                                vars_extra.add(s.name)
                        eqs_norm.append(expr_c.subs(reemp))

                    if vars_extra:
                        st.error(
                            f"Error: Usaste variables que no pertenecen al dominio ({', '.join(sorted(vars_extra))}). "
                            f"Variables válidas: {', '.join(lista_vars)}."
                        )
                    else:
                        matriz_regla = sp.Matrix(eqs_norm)
                        sustitucion_cero = {v: 0 for v in variables_simbolicas}
                        A_can = matriz_regla.jacobian(variables_simbolicas)

                        es_cero_en_origen = all(sp.simplify(e) == 0 for e in matriz_regla.subs(sustitucion_cero))
                        es_jacobiano_constante = A_can.free_symbols.isdisjoint(set(variables_simbolicas))

                        if not es_cero_en_origen:
                            st.error("Error Matemático: La transformación NO es lineal porque $T(\\mathbf{0}) \\neq \\mathbf{0}$ (tiene términos constantes).")
                        elif not es_jacobiano_constante:
                            st.error(
                                "Error Matemático: La transformación NO es lineal (contiene potencias, productos entre variables "
                                "o funciones no lineales, por lo que su matriz Jacobiana no es constante)."
                            )
                        else:
                            M_asociada = sp.simplify(Base2.inv() * A_can * Base1)
                            st.session_state.temp_tl_mat = M_asociada
                            st.session_state.temp_tl_reg = matriz_regla
                            st.session_state.temp_b1 = Base1
                            st.session_state.temp_b2 = Base2
                            st.session_state.temp_dom_str = etiqueta_dom
                            st.session_state.temp_cod_str = etiqueta_cod
                            st.rerun()
                except Exception as e:
                    st.error(f"Error matemático al construir la matriz: {e}")

    elif "2. Definir una Matriz Nueva" in metodo:
        st.write(f"Construya la matriz asociada $[T]_\\beta^\\gamma$ de dimensiones ({dim_w}×{dim_v}):")
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
                filas_parsed = [[leer_expresion_st(cell) for cell in row] for row in matriz_elementos]
                if any(cell is None for row in filas_parsed for cell in row):
                    st.error("Corrija las celdas con expresiones inválidas.")
                else:
                    matriz_asoc = sp.Matrix(filas_parsed)
                    A_can = sp.simplify(Base2 * matriz_asoc * Base1.inv())
                    regla_canonica = sp.simplify(A_can * sp.Matrix(variables_simbolicas))

                    st.session_state.temp_tl_mat = matriz_asoc
                    st.session_state.temp_tl_reg = regla_canonica
                    st.session_state.temp_b1 = Base1
                    st.session_state.temp_b2 = Base2
                    st.session_state.temp_dom_str = etiqueta_dom
                    st.session_state.temp_cod_str = etiqueta_cod
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
                if st.button("🔗 Vincular Matriz Seleccionada", use_container_width=True):
                    A_can = sp.simplify(Base2 * M_imp * Base1.inv())
                    regla_canonica = sp.simplify(A_can * sp.Matrix(variables_simbolicas))

                    st.session_state.temp_tl_mat = M_imp
                    st.session_state.temp_tl_reg = regla_canonica
                    st.session_state.temp_b1 = Base1
                    st.session_state.temp_b2 = Base2
                    st.session_state.temp_dom_str = etiqueta_dom
                    st.session_state.temp_cod_str = etiqueta_cod
                    st.rerun()
        else:
            st.warning("No hay matrices guardadas en el inventario actual.")

    # ==============================================================================
    # 5. BLOQUE DE CONFIRMACIÓN Y GUARDADO PERSISTENTE
    # ==============================================================================
    if "temp_tl_mat" in st.session_state:
        st.divider()
        st.subheader("Resultados Previos a Guardar")
        c_prev1, c_prev2 = st.columns(2)
        with c_prev1:
            st.write("**Matriz Asociada ($[T]_\\beta^\\gamma$):**")
            imprimir_matriz_simbolica(st.session_state.temp_tl_mat)
        with c_prev2:
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
                        "espacio_V": st.session_state.get("temp_dom_str", rf"\mathbb{{R}}^{{{dim_v}}}"),
                        "espacio_W": st.session_state.get("temp_cod_str", rf"\mathbb{{R}}^{{{dim_w}}}"),
                        "variables": variables_simbolicas,
                        "matriz_asociada": st.session_state.temp_tl_mat,
                        "regla": st.session_state.temp_tl_reg,
                        "base_dominio": st.session_state.temp_b1,
                        "base_codominio": st.session_state.temp_b2,
                    }
                    for temp_var in ["temp_tl_mat", "temp_tl_reg", "temp_b1", "temp_b2", "temp_dom_str", "temp_cod_str"]:
                        st.session_state.pop(temp_var, None)
                    st.success(f"¡Transformación '{nombre_tl}' guardada con éxito!")
                    st.rerun()
                else:
                    st.error("Por favor proporcione un nombre válido antes de guardar.")
        with col_btn2:
            if st.button("❌ Cancelar", use_container_width=True):
                for temp_var in ["temp_tl_mat", "temp_tl_reg", "temp_b1", "temp_b2", "temp_dom_str", "temp_cod_str"]:
                    st.session_state.pop(temp_var, None)
                st.rerun()


def mostrar_detalle_tl(nombre, tl_data):
    """Muestra un resumen formal de la transformación lineal."""
    esp_v = tl_data.get("espacio_V", rf"\mathbb{{R}}^{{{tl_data['dim_V']}}}")
    esp_w = tl_data.get("espacio_W", rf"\mathbb{{R}}^{{{tl_data['dim_W']}}}")

    st.info(f"### Transformación Lineal: {nombre}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Dominio ($V$):** ${esp_v}$ (dim $= {tl_data['dim_V']}$)")
        st.markdown(f"**Codominio ($W$):** ${esp_w}$ (dim $= {tl_data['dim_W']}$)")
    with col2:
        st.markdown(f"**Coordenadas de entrada:** `{', '.join([str(v) for v in tl_data['variables']])}`")

    c_r, c_m = st.columns(2)
    with c_r:
        st.write("**Regla de Correspondencia Canónica:**")
        st.latex(sp.latex(tl_data["regla"]))
    with c_m:
        st.write("**Matriz Asociada ($[T]_\\beta^\\gamma$):**")
        imprimir_matriz_simbolica(tl_data["matriz_asociada"])
