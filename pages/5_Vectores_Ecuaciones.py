import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

try:
    from utils import imprimir_matriz_simbolica, leer_expresion_st
except ImportError:
    st.error("Error al cargar utils.py. Asegúrate de ejecutar la aplicación desde la raíz.")
    st.stop()

st.set_page_config(page_title="Vectores y Sistemas", layout="wide")

if 'mis_vectores' not in st.session_state:
    st.session_state.mis_vectores = {}
if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}

st.title("↗️ Vectores y Sistemas de Ecuaciones")

# ==============================================================================
# PANEL LATERAL (INVENTARIO DE VECTORES)
# ==============================================================================
with st.sidebar:
    st.header("Inventario de Vectores")
    if st.session_state.mis_vectores:
        for nombre, vec in st.session_state.mis_vectores.items():
            st.write(f"**{nombre}**:")
            imprimir_matriz_simbolica(vec)
    else:
        st.info("No hay vectores en memoria.")

    st.divider()
    st.subheader("Nuevo Vector")
    nombre_nuevo = st.text_input("Asignar nombre (Ej: u, v, w):").upper().strip()

    if nombre_nuevo:
        dim = st.number_input("Dimensión del vector (Rn):", min_value=2, max_value=10, value=3)
        with st.form("form_vector"):
            componentes = [st.text_input(f"Componente {i + 1}:", value="0") for i in range(dim)]
            if st.form_submit_button("Guardar Vector"):
                try:
                    vec_nums = [leer_expresion_st(c) for c in componentes]
                    if None not in vec_nums:
                        st.session_state.mis_vectores[nombre_nuevo] = sp.Matrix(vec_nums)
                        st.success(f"Vector {nombre_nuevo} guardado.")
                        st.rerun()
                except Exception:
                    st.error("Error al procesar componentes.")

    if st.button("🗑️ Borrar todos los vectores"):
        st.session_state.mis_vectores.clear()
        st.rerun()

# ==============================================================================
# ÁREA PRINCIPAL
# ==============================================================================
tab_ops, tab_graficas, tab_sistemas, tab_analisis_conjunto = st.tabs(
    ["Operaciones", "Graficación (R2 y R3)", "Sistemas de Ecuaciones", "Análisis de Conjuntos"])

# ------------------------------------------------------------------------------
# TAB 1: OPERACIONES VECTORIALES
# ------------------------------------------------------------------------------
with tab_ops:
    if st.session_state.mis_vectores:
        st.subheader("Operaciones Vectoriales")
        col1, col2 = st.columns(2)
        with col1:
            v1_nombre = st.selectbox("Vector 1 (v):", list(st.session_state.mis_vectores.keys()), key="v1")

        operacion = st.radio("Operación:", [
            "Suma (+)", "Resta (-)", "Escalar * v", "Distancia",
            "Norma", "Producto Punto", "Producto Cruz (R3)", "Ángulo", "Proyección", "Gram-Schmidt (Vector unitario)"
        ], horizontal=True)

        # Campos dinámicos dependiendo de la operación
        if operacion == "Escalar * v":
            escalar_str = st.text_input("Ingrese el escalar:", value="2")
        elif operacion not in ["Norma", "Gram-Schmidt (Vector unitario)"]:
            with col2:
                v2_nombre = st.selectbox("Vector 2 (u):", list(st.session_state.mis_vectores.keys()), key="v2")

        if st.button("Calcular Operación"):
            v1 = st.session_state.mis_vectores[v1_nombre]
            res = None  # Variable para atrapar resultados que sean vectores

            if operacion == "Escalar * v":
                try:
                    esc = sp.sympify(escalar_str)
                    res = sp.simplify(esc * v1)
                    st.success("Resultado:")
                    imprimir_matriz_simbolica(res)
                except Exception:
                    st.error("Escalar inválido.")

            elif operacion == "Norma":
                st.latex(f"||{v1_nombre}|| = {sp.latex(sp.simplify(v1.norm()))}")

            elif operacion == "Gram-Schmidt (Vector unitario)":
                v_ortho = sp.GramSchmidt([v1], orthonormal=True)
                res = v_ortho[0]
                st.success("Vector normalizado:")
                imprimir_matriz_simbolica(res)

            else:
                v2 = st.session_state.mis_vectores[v2_nombre]

                if operacion == "Suma (+)":
                    if v1.shape == v2.shape:
                        res = sp.simplify(v1 + v2)
                        imprimir_matriz_simbolica(res)
                    else: st.error("Diferente dimensión.")

                elif operacion == "Resta (-)":
                    if v1.shape == v2.shape:
                        res = sp.simplify(v1 - v2)
                        imprimir_matriz_simbolica(res)
                    else: st.error("Diferente dimensión.")

                elif operacion == "Distancia":
                    if v1.shape == v2.shape:
                        dist = sp.simplify((v1 - v2).norm())
                        st.latex(f"d({v1_nombre}, {v2_nombre}) = {sp.latex(dist)}")
                    else: st.error("Diferente dimensión.")

                elif operacion == "Producto Punto":
                    if v1.shape == v2.shape:
                        dot = sp.simplify(v1.dot(v2.conjugate()))
                        st.latex(f"{v1_nombre} \cdot {v2_nombre} = {sp.latex(dot)}")
                    else: st.error("Diferente dimensión.")

                elif operacion == "Producto Cruz (R3)":
                    if v1.rows == 3 and v2.rows == 3:
                        res = sp.simplify(v1.cross(v2))
                        imprimir_matriz_simbolica(res)
                    else: st.error("Ambos vectores deben estar en R3.")

                elif operacion == "Ángulo":
                    if v1.shape == v2.shape:
                        cos_theta = sp.simplify(v1.dot(v2) / (v1.norm() * v2.norm()))
                        ang = sp.acos(cos_theta)
                        st.latex(f"\\theta = {sp.latex(ang)} \\approx {sp.N(sp.deg(ang), 5)}^\circ")
                    else: st.error("Diferente dimensión.")

                elif operacion == "Proyección":
                    if v1.shape == v2.shape:
                        res = sp.simplify((v1.dot(v2.conjugate()) / v2.dot(v2.conjugate())) * v2)
                        st.write(f"Proyección de {v1_nombre} sobre {v2_nombre}:")
                        imprimir_matriz_simbolica(res)
                    else: st.error("Diferente dimensión.")

            # Activador de guardado: Solo se enciende si 'res' es un vector válido
            if res is not None:
                st.session_state.ultimo_res_vec = res
                st.session_state.mostrar_guardado_vec = True
            else:
                st.session_state.mostrar_guardado_vec = False

        # Interfaz de guardado persistente (fuera del botón)
        if st.session_state.get('mostrar_guardado_vec') and 'ultimo_res_vec' in st.session_state:
            st.divider()
            col_g1, col_g2 = st.columns([2, 1])
            with col_g1:
                nombre_guardar = st.text_input("Asignar nombre para guardar este vector:", key="save_vec_input").upper().strip()
            with col_g2:
                st.write("")
                if st.button("💾 Guardar Vector"):
                    if nombre_guardar:
                        st.session_state.mis_vectores[nombre_guardar] = st.session_state.ultimo_res_vec
                        st.session_state.mostrar_guardado_vec = False
                        st.rerun()
                    else:
                        st.error("Ingrese un nombre válido.")
    else:
        st.info("Defina vectores en la barra lateral.")

# ------------------------------------------------------------------------------
# TAB 2: GRAFICACIÓN
# ------------------------------------------------------------------------------
with tab_graficas:
    st.subheader("Graficador Espacial")
    if st.session_state.mis_vectores:
        seleccionados = st.multiselect("Seleccione vectores a graficar:", list(st.session_state.mis_vectores.keys()))
        if st.button("Generar Gráfica") and seleccionados:
            vecs = [st.session_state.mis_vectores[n] for n in seleccionados]
            dim = vecs[0].rows

            if all(v.rows == dim for v in vecs) and dim in [2, 3] and not any(
                    v.free_symbols or v.has(sp.I) for v in vecs):
                fig = plt.figure()
                colores = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
                if dim == 2:
                    ax = fig.add_subplot(111)
                    max_val = 1
                    for i, v in enumerate(vecs):
                        x, y = float(v[0]), float(v[1])
                        ax.quiver(0, 0, x, y, angles='xy', scale_units='xy', scale=1, color=colores[i % len(colores)],
                                  label=seleccionados[i])
                        max_val = max(max_val, abs(x), abs(y))
                    ax.set_xlim(-max_val - 1, max_val + 1); ax.set_ylim(-max_val - 1, max_val + 1)
                    ax.grid(True); ax.legend(); ax.axhline(0, color='black'); ax.axvline(0, color='black')
                else:
                    ax = fig.add_subplot(111, projection='3d')
                    max_val = 1
                    for i, v in enumerate(vecs):
                        x, y, z = float(v[0]), float(v[1]), float(v[2])
                        ax.quiver(0, 0, 0, x, y, z, color=colores[i % len(colores)], label=seleccionados[i])
                        max_val = max(max_val, abs(x), abs(y), abs(z))
                    ax.set_xlim([-max_val, max_val]); ax.set_ylim([-max_val, max_val]); ax.set_zlim([-max_val, max_val])
                    ax.legend()
                st.pyplot(fig)
            else:
                st.error("Todos los vectores deben ser puramente numéricos y pertenecer al mismo espacio (R2 o R3).")

# ------------------------------------------------------------------------------
# TAB 3: SISTEMAS DE ECUACIONES
# ------------------------------------------------------------------------------
with tab_sistemas:
    st.subheader("Resolución de Sistemas de Ecuaciones Lineales")
    
    n_vars = int(st.number_input("Número de incógnitas:", min_value=2, max_value=10, value=3, step=1))
    st.write(f"Ingrese la matriz aumentada $[A|b]$ de tamaño ${n_vars} \\times {n_vars+1}$:")
    
    with st.form("form_sistema"):
        elementos = []
        for i in range(n_vars):
            cols = st.columns(n_vars + 1)
            fila = []
            for j in range(n_vars + 1):
                with cols[j]:
                    label = f"x_{j+1}" if j < n_vars else "b"
                    fila.append(st.text_input(label, value="0", key=f"sys_{n_vars}_{i}_{j}"))
            elementos.append(fila)
            
        if st.form_submit_button("Resolver Sistema"):
            M_aug = sp.zeros(
