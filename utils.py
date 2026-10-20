# utils.py
# Programa: Mathesis V0.3 — Núcleo de Utilidades, Parser Seguro y Constructores UI
# Autores: José Alberto Fernández Cendejas e Ingrid Rebeca Ortega Flores
# -------------------------------------------------------------------------------- #

import multiprocessing
import re
from types import MappingProxyType

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from estilos import subheader_tarjeta

try:
    from teclado_matematico import teclado_matematico
    from interprete_latex import latex_a_sympy, ErrorLatex
    _TIENE_TECLADO = True
except Exception:
    _TIENE_TECLADO = False


# ==============================================================================
# 1. INICIALIZACIÓN DE MEMORIA (SESSION STATE SEGURO PARA PYTEST)
# ==============================================================================
def _en_ejecucion_streamlit() -> bool:
    """Devuelve True solo si hay una sesión activa de Streamlit (evita errores en pytest)."""
    try:
        return bool(st.runtime.exists())
    except Exception:
        return False


def inicializar_estado():
    """Inicializa de forma segura todas las estructuras persistentes en st.session_state."""
    if not _en_ejecucion_streamlit():
        return
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


if _en_ejecucion_streamlit():
    inicializar_estado()


# ==============================================================================
# 2. LÓGICA PURA: PARSER SEGURO, TIMEOUTS Y EVALUACIÓN NUMÉRICA
# ==============================================================================
_SAFE_GLOBALS = MappingProxyType({
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
})

_TRANSFORMACIONES_ESTANDAR = standard_transformations + (implicit_multiplication_application, convert_xor)


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
        transformaciones = _TRANSFORMACIONES_ESTANDAR

    if local_dict is None:
        local_dict = {}

    return parse_expr(
        entrada_str,
        transformations=transformaciones,
        global_dict=dict(_SAFE_GLOBALS),
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

import concurrent.futures

def calcular_con_limite(func, args=(), kwargs=None, timeout=10):
    """
    Ejecuta una función de SymPy con límite de tiempo usando un hilo trabajador.
    Evita errores de serialización (PicklingError con lambdas/métodos) y elimina
    los 5 segundos de penalización por arranque de subprocesos en Streamlit Cloud.
    """
    if kwargs is None:
        kwargs = {}
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    futuro = executor.submit(func, *args, **kwargs)
    try:
        return futuro.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        executor.shutdown(wait=False, cancel_futures=True)
        raise TimeoutError(
            "El cálculo matemático superó el tiempo máximo de " + str(timeout) + " segundos. "
            "Simplifique la expresión o evalúela numéricamente."
        )
    except Exception as e:
        executor.shutdown(wait=False, cancel_futures=True)
        raise e
    finally:
        executor.shutdown(wait=False)


def parsear_base_matricial(texto: str, dim: int):
    """
    Convierte una cadena de vectores como '[1, 0], [0, 1]' en una matriz de base por columnas.
    Lanza ValueError con mensaje explicativo si el formato o la dimensión son incorrectos o si no es L.I.
    """
    if not texto or not texto.strip():
        return sp.eye(dim)
    bloques = re.findall(r"\[(.*?)\]", texto)
    if not bloques:
        raise ValueError("Formato inválido: encierre cada vector entre corchetes, por ejemplo [1, 0], [0, 1].")
    if len(bloques) != dim:
        raise ValueError("Se requieren exactamente " + str(dim) + " vectores para formar la base (ingresaste " + str(len(bloques)) + ").")

    filas = []
    for idx, b in enumerate(bloques):
        partes = [p.strip() for p in b.split(",") if p.strip()]
        if len(partes) != dim:
            raise ValueError("El vector " + str(idx + 1) + " tiene " + str(len(partes)) + " componentes, pero debe tener " + str(dim) + ".")
        vec_parsed = []
        for c in partes:
            expr = parse_seguro(c, local_dict={"i": sp.I, "j": sp.I, "I": sp.I})
            if expr is None or not isinstance(expr, sp.Expr):
                raise ValueError("Componente inválida '" + str(c) + "' en el vector " + str(idx + 1) + ".")
            vec_parsed.append(expr)
        filas.append(vec_parsed)

    M_base = sp.Matrix(filas).T
    if sp.simplify(M_base.det()) == 0:
        raise ValueError("Los vectores ingresados son linealmente dependientes (Determinante = 0): no forman una base.")
    return M_base


# ==============================================================================
# 3. UTILIDADES DE INTERFAZ Y GRÁFICAS (STREAMLIT)
# ==============================================================================
def imprimir_matriz_simbolica(matriz_sp):
    """Renderiza una matriz de SymPy usando LaTeX nativo de Streamlit."""
    if matriz_sp is not None:
        st.latex(sp.latex(matriz_sp))


def mostrar_figura_segura(fig):
    """Muestra una figura de Matplotlib en Streamlit y la cierra inmediatamente para evitar memory leaks."""
    if fig is not None:
        st.pyplot(fig)
        try:
            plt.close(fig)
        except Exception:
            pass


def leer_expresion_st(entrada_str, solo_reales=False):
    """
    Analiza una cadena ingresada en un widget y la convierte en un objeto SymPy.
    Retorna el objeto SymPy si es válido, o None (mostrando error) si no lo es.
    """
    if entrada_str is None or not str(entrada_str).strip():
        return None

    diccionario_imaginario = {"i": sp.I, "j": sp.I, "I": sp.I}

    try:
        expresion = parse_seguro(
            entrada_str,
            transformaciones=_TRANSFORMACIONES_ESTANDAR,
            local_dict=diccionario_imaginario,
        )

        if not isinstance(expresion, sp.Expr):
            st.error("'" + str(entrada_str) + "' no es una expresión matemática válida.")
            return None
        if solo_reales and expresion.has(sp.I):
            st.error("Esta operación requiere números reales.")
            return None
        if expresion.has(sp.oo, sp.zoo, sp.nan, -sp.oo):
            st.error("Error matemático: Evaluación a infinito o división por cero.")
            return None

        return expresion
    except (SyntaxError, ValueError, TypeError) as ve:
        st.error(str(ve))
        return None
    except Exception:
        st.error("La expresión '" + str(entrada_str) + "' no es válida matemáticamente.")
        return None


def gestionar_inventario_sidebar(
    clave_estado: str,
    titulo: str,
    etiqueta_item: str,
    claves_temporales: tuple = (),
    render_fn=None,
):
    """
    Renderiza en st.sidebar un inventario interactivo con renombrado y eliminación individual.
    """
    with st.sidebar:
        subheader_tarjeta(titulo)
        inventario = st.session_state.get(clave_estado, {})

        if inventario:
            for nombre, obj in list(inventario.items()):
                sub_info = ""
                if isinstance(obj, sp.MatrixBase):
                    sub_info = " (" + str(obj.shape[0]) + "×" + str(obj.shape[1]) + ")"
                elif isinstance(obj, dict) and "dim_V" in obj and "dim_W" in obj:
                    sub_info = " (dim " + str(obj["dim_V"]) + " → " + str(obj["dim_W"]) + ")"

                with st.expander(etiqueta_item + " " + str(nombre) + sub_info):
                    if render_fn is not None:
                        render_fn(nombre, obj)
                    elif isinstance(obj, sp.MatrixBase):
                        imprimir_matriz_simbolica(obj)
                    elif isinstance(obj, dict) and "matriz_asociada" in obj:
                        st.caption("Matriz asociada:")
                        imprimir_matriz_simbolica(obj["matriz_asociada"])
                    else:
                        st.latex(str(nombre) + " = " + sp.latex(obj))

                    nuevo_nom = st.text_input(
                        "Renombrar a:",
                        value=str(nombre),
                        key="ren_in_" + clave_estado + "_" + str(nombre),
                    ).upper().strip()

                    c_ren, c_del = st.columns(2)
                    with c_ren:
                        if st.button("✏️ Nombre", key="btn_ren_" + clave_estado + "_" + str(nombre), use_container_width=True):
                            if not nuevo_nom:
                                st.error("Nombre vacío.")
                            elif nuevo_nom == nombre:
                                st.info("Mismo nombre.")
                            elif nuevo_nom in inventario:
                                st.error("Ya existe.")
                            else:
                                nuevo_dict = {}
                                for k, v in inventario.items():
                                    nuevo_dict[nuevo_nom if k == nombre else k] = v
                                st.session_state[clave_estado] = nuevo_dict
                                st.rerun()
                    with c_del:
                        if st.button("🗑️ Borrar", key="btn_del_" + clave_estado + "_" + str(nombre), use_container_width=True):
                            st.session_state[clave_estado].pop(nombre, None)
                            st.rerun()
        else:
            st.info("No hay elementos guardados en memoria.")

        st.divider()
        if st.button("🗑️ Vaciar inventario", key="btn_clear_" + clave_estado, use_container_width=True):
            st.session_state[clave_estado].clear()
            for k_tmp in claves_temporales:
                st.session_state.pop(k_tmp, None)
            st.rerun()


def _etiqueta_espacio(tipo: str, dim: int, grado: int = 0, m: int = 0, n: int = 0) -> str:
    if tipo == "R^n":
        return r"\mathbb{R}^{" + str(dim) + "}"
    if tipo == "C^n":
        return r"\mathbb{C}^{" + str(dim) + "}"
    if tipo == "Polinomios (Pn)":
        return r"P_{" + str(grado) + r"}(\mathbb{R})"
    return r"M_{" + str(m) + r"\times " + str(n) + r"}(\mathbb{R})"


# ==============================================================================
# 4. CONSTRUCTORES DE INTERFAZ (MATRICES Y TRANSFORMACIONES LINEALES)
# ==============================================================================
def crear_matriz_simbolica_ui(nombre_matriz=""):
    """Crea una matriz simbólica celda por celda dentro de un contenedor con borde."""
    if not nombre_matriz:
        st.info("Escriba un nombre para la matriz arriba para comenzar.")
        return None

    st.markdown("### Crear Matriz: " + str(nombre_matriz))

    col_m, col_n = st.columns(2)
    with col_m:
        filas = int(st.number_input("Renglones", min_value=1, max_value=6, value=3, step=1, key="f_" + str(nombre_matriz)))
    with col_n:
        columnas = int(st.number_input("Columnas", min_value=1, max_value=6, value=3, step=1, key="c_" + str(nombre_matriz)))

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
                        "Componente (" + str(i + 1) + ", " + str(j + 1) + "):",
                        value="0",
                        key="celda_" + str(nombre_matriz) + "_" + str(i) + "_" + str(j) + "_" + str(filas) + "_" + str(columnas),
                    ).strip()

                    try:
                        val_sym = parse_seguro(
                            val_str,
                            transformaciones=_TRANSFORMACIONES_ESTANDAR,
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
        st.latex(str(nombre_matriz) + " = " + sp.latex(matriz_temp))

        if st.button("💾 Guardar Matriz", key="btn_save_" + str(nombre_matriz), use_container_width=True):
            return matriz_temp

    return None


def crear_transformacion_ui():
    st.subheader("1. Dominio (V) y Codominio (W)")
    col_dom, col_cod = st.columns(2)

    grado_dom = m_dom = n_dom = 0
    grado_cod = m_cod = n_cod = 0

    with col_dom:
        st.markdown("**Dominio (V)**")
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
        st.markdown("**Codominio (W)**")
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

    # 2. CAPTURA PREVIA DE VARIABLES
    st.subheader("2. Variables del Dominio (Coordenadas)")

    if tipo_dom == "Polinomios (Pn)":
        if dim_v == 3:
            default_vars = "a, b, c"
            poly_ejemplo = "ax² + bx + c"
        elif dim_v == 2:
            default_vars = "m, b"
            poly_ejemplo = "mx + b"
        elif dim_v == 1:
            default_vars = "c"
            poly_ejemplo = "c"
        else:
            default_vars = ", ".join(["a" + str(i) for i in range(dim_v - 1, -1, -1)])
            vars_list = [v.strip() for v in default_vars.split(",")]
            poly_ejemplo = vars_list[0] + "x^" + str(dim_v - 1) + " + ... + " + vars_list[-1]

        st.info(
            "💡 **Notación Polinomial:** Cada variable representa un coeficiente ordenado de mayor a menor grado. "
            "Para `" + default_vars + "`, el polinomio es p(x) = " + poly_ejemplo + "."
        )
    else:
        if dim_v <= 4:
            default_vars = ", ".join(["x", "y", "z", "w"][:dim_v])
        else:
            default_vars = ", ".join(["x" + str(i + 1) for i in range(dim_v)])
        st.caption("Defina las " + str(dim_v) + " variables de su vector de entrada.")

    vars_str = st.text_input("Ingrese las variables separadas por comas:", value=default_vars, key="tl_vars_input")
    lista_vars = [v.strip() for v in vars_str.split(",") if v.strip()]

    if len(lista_vars) != dim_v or len(set(lista_vars)) != dim_v:
        st.warning("Por favor ingrese exactamente " + str(dim_v) + " variables distintas para continuar.")
        return

    variables_simbolicas = tuple(sp.Symbol(v) for v in lista_vars)

    st.divider()

    # 3. ENTRADA DIRECTA DE BASES NO CANÓNICAS (SIN FALLBACK SILENCIOSO)
    st.subheader("3. Bases del Dominio y Codominio")
    Base1 = sp.eye(dim_v)
    Base2 = sp.eye(dim_w)
    bases_validas = True

    with st.expander("¿Desea ingresar bases no canónicas explícitas?"):
        st.markdown(
            "💡 **¿Cómo introducir los vectores de la base?**\n"
            "Todo elemento debe ingresarse como su **vector de coordenadas** encerrado en corchetes `[...]` y separado por comas:\n"
            "* **Para ℝⁿ:** Ej. en ℝ²: `[1, 2], [-1, 1]`\n"
            "* **Para Polinomios (Pₙ):** Coeficientes de mayor a menor grado. Ej. en P₂: `[1,0,1], [0,1,0], [0,0,1]`\n"
            "* **Para Matrices:** Aplane la matriz fila por fila."
        )

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            b1_input = st.text_area("Base Dominio (V):", value="", placeholder="Vacío = base canónica", key="base_v")
        with col_b2:
            b2_input = st.text_area("Base Codominio (W):", value="", placeholder="Vacío = base canónica", key="base_w")

        if b1_input.strip():
            try:
                Base1 = parsear_base_matricial(b1_input, dim_v)
            except ValueError as err_b1:
                st.error("⛔ Error en Base del Dominio: " + str(err_b1))
                bases_validas = False

        if b2_input.strip():
            try:
                Base2 = parsear_base_matricial(b2_input, dim_w)
            except ValueError as err_b2:
                st.error("⛔ Error en Base del Codominio: " + str(err_b2))
                bases_validas = False

        if bases_validas and (b1_input.strip() or b2_input.strip()):
            st.success("✅ Bases no canónicas validadas (son linealmente independientes).")

    if not bases_validas:
        st.warning("Corrija los errores en las bases ingresadas arriba antes de definir la regla de la transformación.")
        return

    st.divider()

    # 4. MÉTODOS DE DEFINICIÓN
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
                st.info("💡 Escriba el operador usando **`p`** para el polinomio y **`x`** como variable (ej. pulse d/dx y escriba d/dx p + x·p).")
                latex_op = teclado_matematico(
                    "tl_op_poly_kb",
                    valor_inicial=r"\frac{\mathrm{d}}{\mathrm{d}x}p",
                    placeholder="Escribe T(p) y pulsa ↵",
                    acoplado=True,
                )
                ejecutar_op = st.button("🧮 Construir desde Teclado Matemático", use_container_width=True)
            else:
                st.markdown(
                    "💡 **Sintaxis de texto:** Use **`p`** para el polinomio y **`x`** como variable:\n"
                    "* **Derivada:** `diff(p, x)` | **Segunda derivada:** `diff(p, x, 2)`\n"
                    "* **Integral Indefinida:** `integrate(p, x)`"
                )
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
                            "Error Matemático: El polinomio resultante tiene grado " + str(poly_obj.degree()) + ", "
                            "que excede el grado máximo del codominio (" + str(dim_w - 1) + ")."
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
                        st.latex("T(p(x)) = " + sp.latex(expr_evaluada))
                        M_asociada = calcular_con_limite(lambda: sp.simplify(Base2.inv() * A_can * Base1), timeout=6)
                        st.session_state.temp_tl_mat = M_asociada
                        st.session_state.temp_tl_reg = matriz_regla
                        st.session_state.temp_b1 = Base1
                        st.session_state.temp_b2 = Base2
                        st.session_state.temp_dom_str = etiqueta_dom
                        st.session_state.temp_cod_str = etiqueta_cod
                except Exception as e:
                    st.error("Error al construir el operador: " + str(e))

        else:
            st.write("Defina cada una de las " + str(dim_w) + " componentes de salida en términos de `" + ", ".join(lista_vars) + "`:")
            eqs_parsed = []
            error_parsing = False

            if usar_teclado:
                st.caption("Escriba cada componente en su campo y pulse **↵** (o salga del recuadro) antes de procesar:")
                for i in range(dim_w):
                    lat_i = teclado_matematico(
                        "tl_comp_kb_" + str(dim_v) + "_" + str(dim_w) + "_" + str(i),
                        valor_inicial=lista_vars[i] if i < len(lista_vars) else "0",
                        placeholder="Componente " + str(i + 1),
                        acoplado=True,
                        en_vivo=True,
                    )
                    if lat_i:
                        try:
                            eqs_parsed.append(latex_a_sympy(lat_i, reales=(tipo_dom != "C^n"), i_imaginaria=True))
                        except ErrorLatex as err_l:
                            st.error("Componente " + str(i + 1) + ": " + str(err_l))
                            error_parsing = True
                    else:
                        eqs_parsed.append(sp.Integer(0))
                submit_regla = st.button("🧮 Procesar Regla de Correspondencia", use_container_width=True)
            else:
                with st.form("form_regla_tl"):
                    eqs_input = [
                        st.text_input(
                            "Componente " + str(i + 1) + ":",
                            value=lista_vars[i] if i < len(lista_vars) else "0",
                            key="comp_val_" + str(i),
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
                            "Error: Usaste variables que no pertenecen al dominio (" + ", ".join(sorted(vars_extra)) + "). "
                            "Variables válidas: " + ", ".join(lista_vars) + "."
                        )
                    else:
                        matriz_regla = sp.Matrix(eqs_norm)
                        sustitucion_cero = {v: 0 for v in variables_simbolicas}
                        A_can = matriz_regla.jacobian(variables_simbolicas)

                        es_cero_en_origen = all(sp.simplify(e) == 0 for e in matriz_regla.subs(sustitucion_cero))
                        es_jacobiano_constante = A_can.free_symbols.isdisjoint(set(variables_simbolicas))

                        if not es_cero_en_origen:
                            st.error("Error Matemático: La transformación NO es lineal porque T(0) ≠ 0 (tiene términos constantes).")
                        elif not es_jacobiano_constante:
                            st.error("Error Matemático: La transformación NO es lineal (su matriz Jacobiana no es constante).")
                        else:
                            M_asociada = calcular_con_limite(lambda: sp.simplify(Base2.inv() * A_can * Base1), timeout=6)
                            st.session_state.temp_tl_mat = M_asociada
                            st.session_state.temp_tl_reg = matriz_regla
                            st.session_state.temp_b1 = Base1
                            st.session_state.temp_b2 = Base2
                            st.session_state.temp_dom_str = etiqueta_dom
                            st.session_state.temp_cod_str = etiqueta_cod
                            st.rerun()
                except Exception as e:
                    st.error("Error matemático al construir la matriz: " + str(e))

    elif "2. Definir una Matriz Nueva" in metodo:
        st.write("Construya la matriz asociada de dimensiones (" + str(dim_w) + "×" + str(dim_v) + "):")
        with st.form("form_nueva_matriz_tl"):
            matriz_elementos = []
            for i in range(dim_w):
                cols_input = st.columns(dim_v)
                fila_actual = []
                for j in range(dim_v):
                    with cols_input[j]:
                        valor = st.text_input("M(" + str(i + 1) + "," + str(j + 1) + ")", value="0", key="mat_tl_" + str(i) + "_" + str(j))
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
                    A_can = calcular_con_limite(lambda: sp.simplify(Base2 * matriz_asoc * Base1.inv()), timeout=6)
                    regla_canonica = sp.simplify(A_can * sp.Matrix(variables_simbolicas))

                    st.session_state.temp_tl_mat = matriz_asoc
                    st.session_state.temp_tl_reg = regla_canonica
                    st.session_state.temp_b1 = Base1
                    st.session_state.temp_b2 = Base2
                    st.session_state.temp_dom_str = etiqueta_dom
                    st.session_state.temp_cod_str = etiqueta_cod
                    st.rerun()
            except Exception as e:
                st.error("Error al procesar los elementos de la matriz: " + str(e))

    elif "3. Importar una Matriz Preexistente" in metodo:
        if st.session_state.mis_matrices:
            mat_sel = st.selectbox("Seleccione una matriz de su inventario global:", list(st.session_state.mis_matrices.keys()))
            M_imp = st.session_state.mis_matrices[mat_sel]

            if M_imp.shape != (dim_w, dim_v):
                st.error(
                    "Incompatibilidad de dimensiones: La matriz mide " + str(M_imp.shape[0]) + "×" + str(M_imp.shape[1]) + ", "
                    "pero el espacio requiere " + str(dim_w) + "×" + str(dim_v) + "."
                )
            else:
                if st.button("🔗 Vincular Matriz Seleccionada", use_container_width=True):
                    A_can = calcular_con_limite(lambda: sp.simplify(Base2 * M_imp * Base1.inv()), timeout=6)
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

    # 5. BLOQUE DE CONFIRMACIÓN Y GUARDADO PERSISTENTE
    if "temp_tl_mat" in st.session_state:
        st.divider()
        st.subheader("Resultados Previos a Guardar")
        c_prev1, c_prev2 = st.columns(2)
        with c_prev1:
            st.write("**Matriz Asociada:**")
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
                        "espacio_V": st.session_state.get("temp_dom_str", r"\mathbb{R}^{" + str(dim_v) + "}"),
                        "espacio_W": st.session_state.get("temp_cod_str", r"\mathbb{R}^{" + str(dim_w) + "}"),
                        "variables": variables_simbolicas,
                        "matriz_asociada": st.session_state.temp_tl_mat,
                        "regla": st.session_state.temp_tl_reg,
                        "base_dominio": st.session_state.temp_b1,
                        "base_codominio": st.session_state.temp_b2,
                    }
                    for temp_var in ["temp_tl_mat", "temp_tl_reg", "temp_b1", "temp_b2", "temp_dom_str", "temp_cod_str"]:
                        st.session_state.pop(temp_var, None)
                    st.success("¡Transformación '" + str(nombre_tl) + "' guardada con éxito!")
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
    esp_v = tl_data.get("espacio_V", r"\mathbb{R}^{" + str(tl_data["dim_V"]) + "}")
    esp_w = tl_data.get("espacio_W", r"\mathbb{R}^{" + str(tl_data["dim_W"]) + "}")

    st.info("### Transformación Lineal: " + str(nombre))
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Dominio (V):** (dim = " + str(tl_data["dim_V"]) + ")")
        st.latex(esp_v)
        st.write("**Codominio (W):** (dim = " + str(tl_data["dim_W"]) + ")")
        st.latex(esp_w)
    with col2:
        st.markdown("**Coordenadas de entrada:** `" + ", ".join([str(v) for v in tl_data["variables"]]) + "`")

    c_r, c_m = st.columns(2)
    with c_r:
        st.write("**Regla de Correspondencia Canónica:**")
        st.latex(sp.latex(tl_data["regla"]))
    with c_m:
        st.write("**Matriz Asociada:**")
        imprimir_matriz_simbolica(tl_data["matriz_asociada"])


# Alias retrocompatibles con páginas anteriores
Crear_Matriz_Simbolica_UI = crear_matriz_simbolica_ui
Crear_Transformacion_UI = crear_transformacion_ui
