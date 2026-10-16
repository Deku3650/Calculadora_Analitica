# pages/5_Vectores_Ecuaciones.py
import numpy as np
import streamlit as st
import sympy as sp
from matplotlib.figure import Figure

# 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO)
st.set_page_config(page_title="Vectores y Sistemas - MATHESIS", page_icon="↗️", layout="wide")

from estilos import cargar_estilos_globales  # noqa: E402
from utils import imprimir_matriz_simbolica, inicializar_estado, leer_expresion_st  # noqa: E402

cargar_estilos_globales()
inicializar_estado()

AZUL = "#0284c7"
NARANJA = "#ea580c"
VERDE = "#16a34a"
ROJO = "#dc2626"
MORADO = "#7c3aed"
GRIS = "#6b7280"
PALETA_VEC = [AZUL, NARANJA, VERDE, ROJO, MORADO, "#0891b2", "#be185d"]


def header_tarjeta(texto: str):
    st.markdown(f'<div class="card-header-title">{texto}</div>', unsafe_allow_html=True)


def subheader_tarjeta(texto: str):
    st.markdown(f'<div class="card-subheader-title">{texto}</div>', unsafe_allow_html=True)


# ==============================================================================
# ENCABEZADO PRINCIPAL
# ==============================================================================
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">↗️ Vectores y Sistemas de Ecuaciones</h1>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# PANEL LATERAL (INVENTARIO DE VECTORES)
# ==============================================================================
with st.sidebar:
    subheader_tarjeta("📦 Inventario de Vectores")
    if st.session_state.mis_vectores:
        for nombre, vec in st.session_state.mis_vectores.items():
            with st.expander(f"Vector {nombre} (ℝ^{vec.shape[0]})"):
                imprimir_matriz_simbolica(vec)
    else:
        st.info("No hay vectores en memoria.")

    st.divider()
    if st.button("🗑️ Borrar todos los vectores", use_container_width=True):
        st.session_state.mis_vectores.clear()
        st.session_state.pop("ultimo_res_vec", None)
        st.session_state.pop("mostrar_guardado_vec", None)
        st.rerun()

# ==============================================================================
# ÁREA PRINCIPAL (PESTAÑAS)
# ==============================================================================
tab_gestion, tab_ops, tab_graficas, tab_sistemas, tab_analisis_conjunto = st.tabs([
    "📥 Gestión y Creación",
    "⚙️ Operaciones",
    "📈 Graficación (ℝ² y ℝ³)",
    "📐 Sistemas de Ecuaciones",
    "🔍 Análisis de Conjuntos",
])

# ------------------------------------------------------------------------------
# TAB 0: GESTIÓN Y CREACIÓN
# ------------------------------------------------------------------------------
with tab_gestion:
    with st.container(border=True):
        header_tarjeta("Constructor de Vectores")

        col_v1, col_v2 = st.columns([1, 1.6], gap="large")

        with col_v1:
            subheader_tarjeta("➕ Nuevo Vector")
            nombre_nuevo = st.text_input("Asignar nombre (Ej: U, V, W):", key="input_nom_vector").upper().strip()
            dim = int(st.number_input("Dimensión del vector (ℝⁿ):", min_value=2, max_value=10, value=3, key="dim_vector_input"))

            with st.form("form_vector_main"):
                componentes = [
                    st.text_input(f"Componente {i + 1}:", value="1" if i == 0 else "0", key=f"comp_{i}_{dim}_main")
                    for i in range(dim)
                ]
                if st.form_submit_button("💾 Guardar Vector", use_container_width=True):
                    vec_nums = [leer_expresion_st(c) for c in componentes]
                    if None not in vec_nums and nombre_nuevo:
                        st.session_state.mis_vectores[nombre_nuevo] = sp.Matrix(vec_nums)
                        st.success(f"Vector '{nombre_nuevo}' guardado exitosamente.")
                        st.rerun()
                    elif not nombre_nuevo:
                        st.error("Por favor, asigna un nombre al vector.")
                    else:
                        st.error("Error al procesar las componentes.")

        with col_v2:
            subheader_tarjeta("📋 Vista Previa del Espacio de Trabajo")
            if st.session_state.mis_vectores:
                st.info("Tus vectores actuales están listos para usarse en operaciones, graficación y análisis de bases.")
                cols_prev = st.columns(min(len(st.session_state.mis_vectores), 3))
                for idx_v, (nom, v) in enumerate(st.session_state.mis_vectores.items()):
                    with cols_prev[idx_v % len(cols_prev)]:
                        st.markdown(f"**{nom}** $(\\mathbb{{R}}^{{{v.rows}}})$:")
                        imprimir_matriz_simbolica(v)
            else:
                st.warning("Aún no has creado ningún vector. Utiliza el formulario de la izquierda para comenzar.")

# ------------------------------------------------------------------------------
# TAB 1: OPERACIONES VECTORIALES
# ------------------------------------------------------------------------------
with tab_ops:
    if st.session_state.mis_vectores:
        with st.container(border=True):
            header_tarjeta("Operaciones Vectoriales")
            col1, col2 = st.columns(2, gap="large")
            with col1:
                v1_nombre = st.selectbox("Vector 1 (v):", list(st.session_state.mis_vectores.keys()), key="v1")

            operacion = st.radio(
                "Operación:",
                [
                    "Suma (+)",
                    "Resta (-)",
                    "Escalar * v",
                    "Distancia",
                    "Norma",
                    "Producto Punto",
                    "Producto Cruz (ℝ³)",
                    "Ángulo",
                    "Proyección",
                    "Vector Unitario (Normalizar)",
                ],
                horizontal=True,
            )

            if operacion == "Escalar * v":
                with col2:
                    escalar_str = st.text_input("Ingrese el escalar:", value="2")
            elif operacion not in ["Norma", "Vector Unitario (Normalizar)"]:
                with col2:
                    v2_nombre = st.selectbox("Vector 2 (u):", list(st.session_state.mis_vectores.keys()), key="v2")

            if st.button("🧮 Calcular Operación", use_container_width=True):
                v1 = st.session_state.mis_vectores[v1_nombre]
                res = None

                if operacion == "Escalar * v":
                    esc = leer_expresion_st(escalar_str)
                    if esc is not None:
                        res = sp.simplify(esc * v1)
                        st.success("Resultado de la multiplicación por escalar:")
                        imprimir_matriz_simbolica(res)

                elif operacion == "Norma":
                    norma_v1 = sp.simplify(v1.norm())
                    st.latex(rf"\|\mathbf{{{v1_nombre}}}\| = {sp.latex(norma_v1)} \approx {sp.latex(sp.N(norma_v1, 6))}")

                elif operacion == "Vector Unitario (Normalizar)":
                    if v1.norm() == 0:
                        st.error("Error: No se puede normalizar el vector nulo.")
                    else:
                        res = sp.simplify(v1 / v1.norm())
                        st.success("Vector unitario en la dirección de v:")
                        imprimir_matriz_simbolica(res)

                else:
                    v2 = st.session_state.mis_vectores[v2_nombre]

                    if operacion == "Suma (+)":
                        if v1.shape == v2.shape:
                            res = sp.simplify(v1 + v2)
                            imprimir_matriz_simbolica(res)
                        else:
                            st.error("Error: Los vectores tienen diferente dimensión.")

                    elif operacion == "Resta (-)":
                        if v1.shape == v2.shape:
                            res = sp.simplify(v1 - v2)
                            imprimir_matriz_simbolica(res)
                        else:
                            st.error("Error: Los vectores tienen diferente dimensión.")

                    elif operacion == "Distancia":
                        if v1.shape == v2.shape:
                            dist = sp.simplify((v1 - v2).norm())
                            st.latex(rf"d({v1_nombre}, {v2_nombre}) = \|\mathbf{{{v1_nombre}}} - \mathbf{{{v2_nombre}}}\| = {sp.latex(dist)} \approx {sp.latex(sp.N(dist, 6))}")
                        else:
                            st.error("Error: Los vectores tienen diferente dimensión.")

                    elif operacion == "Producto Punto":
                        if v1.shape == v2.shape:
                            dot = sp.simplify(v1.dot(v2.conjugate()))
                            st.latex(rf"\langle \mathbf{{{v1_nombre}}}, \mathbf{{{v2_nombre}}} \rangle = {sp.latex(dot)}")
                            if dot == 0:
                                st.info("✅ El producto punto es 0: los vectores son **ortogonales**.")
                        else:
                            st.error("Error: Los vectores tienen diferente dimensión.")

                    elif operacion == "Producto Cruz (ℝ³)":
                        if v1.rows == 3 and v2.rows == 3:
                            res = sp.simplify(v1.cross(v2))
                            area_par = sp.simplify(res.norm())
                            st.success("Producto vectorial $v \\times u$ (ortogonal a ambos):")
                            imprimir_matriz_simbolica(res)
                            st.caption(f"Área del paralelogramo generado $\\Vert{}v \\times u\\Vert{} = {sp.latex(area_par)}$")
                        else:
                            st.error("Ambos vectores deben pertenecer a ℝ³.")

                    elif operacion == "Ángulo":
                        if v1.shape != v2.shape:
                            st.error("Error: Los vectores tienen diferente dimensión.")
                        elif v1.norm() == 0 or v2.norm() == 0:
                            st.error("Error: El ángulo no está definido para el vector nulo.")
                        else:
                            cos_theta = sp.simplify(v1.dot(v2) / (v1.norm() * v2.norm()))
                            ang = sp.acos(cos_theta)
                            st.latex(rf"\cos(\theta) = {sp.latex(cos_theta)} \implies \theta = {sp.latex(ang)} \text{{ rad}} \approx {sp.N(ang * 180 / sp.pi, 5)}^\circ")

                    elif operacion == "Proyección":
                        if v1.shape != v2.shape:
                            st.error("Error: Los vectores tienen diferente dimensión.")
                        elif v2.norm() == 0:
                            st.error("Error: No se puede proyectar sobre el vector nulo.")
                        else:
                            res = sp.simplify((v1.dot(v2.conjugate()) / v2.dot(v2.conjugate())) * v2)
                            st.write(f"**Proyección ortogonal de ${v1_nombre}$ sobre ${v2_nombre}$:**")
                            imprimir_matriz_simbolica(res)

                if res is not None:
                    st.session_state.ultimo_res_vec = res
                    st.session_state.mostrar_guardado_vec = True
                else:
                    st.session_state.mostrar_guardado_vec = False

            if st.session_state.get("mostrar_guardado_vec") and "ultimo_res_vec" in st.session_state:
                st.divider()
                col_g1, col_g2 = st.columns([2, 1])
                with col_g1:
                    nombre_guardar = st.text_input("Asignar nombre para guardar este vector:", key="save_vec_input").upper().strip()
                with col_g2:
                    st.write("")
                    if st.button("💾 Guardar Vector", use_container_width=True):
                        if nombre_guardar:
                            st.session_state.mis_vectores[nombre_guardar] = st.session_state.ultimo_res_vec
                            st.session_state.mostrar_guardado_vec = False
                            st.success(f"Vector '{nombre_guardar}' guardado en el inventario.")
                            st.rerun()
                        else:
                            st.error("Ingrese un nombre válido.")
    else:
        st.info("👈 Defina vectores primero en la pestaña 'Gestión y Creación'.")

# ------------------------------------------------------------------------------
# TAB 2: GRAFICACIÓN (ESTILO INSTITUCIONAL LIMPIO)
# ------------------------------------------------------------------------------
with tab_graficas:
    with st.container(border=True):
        header_tarjeta("Graficador Espacial (ℝ² y ℝ³)")
        if st.session_state.mis_vectores:
            seleccionados = st.multiselect("Seleccione vectores a graficar:", list(st.session_state.mis_vectores.keys()))
            if st.button("📈 Generar Gráfica", use_container_width=True) and seleccionados:
                vecs = [st.session_state.mis_vectores[n] for n in seleccionados]
                dim = vecs[0].rows

                if all(v.rows == dim for v in vecs) and dim in [2, 3] and not any(v.free_symbols or v.has(sp.I) for v in vecs):
                    fig = Figure(figsize=(6.4, 4.8), dpi=110, layout="constrained")
                    fig.patch.set_alpha(0.0)
                    if dim == 2:
                        ax = fig.add_subplot(111)
                        ax.patch.set_alpha(0.0)
                        ax.set_aspect("equal", adjustable="box")
                        ax.grid(True, alpha=0.25, linestyle="--")
                        for lado in ("top", "right"):
                            ax.spines[lado].set_visible(False)
                        ax.axhline(0, color=GRIS, lw=0.8, alpha=0.6)
                        ax.axvline(0, color=GRIS, lw=0.8, alpha=0.6)
                        max_val = 1.0
                        for i, v in enumerate(vecs):
                            x_v, y_v = float(v[0]), float(v[1])
                            col = PALETA_VEC[i % len(PALETA_VEC)]
                            ax.quiver(0, 0, x_v, y_v, angles="xy", scale_units="xy", scale=1, color=col, label=f"{seleccionados[i]} ({x_v:g}, {y_v:g})")
                            max_val = max(max_val, abs(x_v), abs(y_v))
                        lim = max_val * 1.3
                        ax.set_xlim(-lim, lim)
                        ax.set_ylim(-lim, lim)
                        ax.set_xlabel("x", color=GRIS)
                        ax.set_ylabel("y", color=GRIS)
                        ax.legend(fontsize=8.5, frameon=False)
                    else:
                        ax = fig.add_subplot(111, projection="3d")
                        ax.patch.set_alpha(0.0)
                        ax.set_box_aspect([1, 1, 1])
                        max_val = 1.0
                        for i, v in enumerate(vecs):
                            x_v, y_v, z_v = float(v[0]), float(v[1]), float(v[2])
                            col = PALETA_VEC[i % len(PALETA_VEC)]
                            ax.quiver(0, 0, 0, x_v, y_v, z_v, color=col, lw=2.0, label=seleccionados[i])
                            max_val = max(max_val, abs(x_v), abs(y_v), abs(z_v))
                        lim = max_val * 1.25
                        ax.set_xlim([-lim, lim])
                        ax.set_ylim([-lim, lim])
                        ax.set_zlim([-lim, lim])
                        ax.set_xlabel("x", color=GRIS)
                        ax.set_ylabel("y", color=GRIS)
                        ax.set_zlabel("z", color=GRIS)
                        ax.legend(fontsize=8.5, frameon=False)
                    st.pyplot(fig)
                else:
                    st.error("Todos los vectores seleccionados deben ser numéricos reales y tener la misma dimensión (2 o 3).")
        else:
            st.info("No hay vectores disponibles para graficar.")

# ------------------------------------------------------------------------------
# TAB 3: SISTEMAS DE ECUACIONES LINEALES (m x n + Rouché-Frobenius)
# ------------------------------------------------------------------------------
with tab_sistemas:
    with st.container(border=True):
        header_tarjeta("Resolución de Sistemas de Ecuaciones Lineales (A·x = b)")

        c_m, c_n = st.columns(2, gap="large")
        with c_m:
            m_ecs = int(st.number_input("Número de ecuaciones (m):", min_value=1, max_value=8, value=3, step=1))
        with c_n:
            n_vars = int(st.number_input("Número de incógnitas (n):", min_value=1, max_value=8, value=3, step=1))

        st.markdown(f"Ingrese la matriz aumentada $[A \\mid b]$ de tamaño ${m_ecs} \\times {n_vars + 1}$:")

        with st.form("form_sistema"):
            elementos = []
            for i in range(m_ecs):
                cols = st.columns(n_vars + 1)
                fila = []
                for j in range(n_vars + 1):
                    with cols[j]:
                        label = f"Ec.{i+1} · x_{j+1}" if j < n_vars else f"Ec.{i+1} · b_{i+1}"
                        val_def = "1" if i == j and j < n_vars else "0"
                        fila.append(st.text_input(label, value=val_def, key=f"sys_{m_ecs}_{n_vars}_{i}_{j}"))
                elementos.append(fila)

            submit_sys = st.form_submit_button("🧮 Analizar y Resolver Sistema", use_container_width=True)

        if submit_sys:
            M_aug = sp.zeros(m_ecs, n_vars + 1)
            error_parser = False

            for i in range(m_ecs):
                for j in range(n_vars + 1):
                    val = leer_expresion_st(elementos[i][j])
                    if val is None:
                        error_parser = True
                    else:
                        M_aug[i, j] = val

            if not error_parser:
                A_coef = M_aug[:, :n_vars]
                rref_aug, _ = M_aug.rref()
                rg_A = A_coef.rank()
                rg_Aug = M_aug.rank()

                c_mat1, c_mat2 = st.columns(2, gap="large")
                with c_mat1:
                    subheader_tarjeta("Matriz Aumentada [A | b]")
                    imprimir_matriz_simbolica(M_aug)
                with c_mat2:
                    subheader_tarjeta("Forma Escalonada Reducida (RREF)")
                    imprimir_matriz_simbolica(rref_aug)

                st.info(
                    f"**Teorema de Rouché-Frobenius:** "
                    f"$\\operatorname{{rg}}(A) = {rg_A}$ | "
                    f"$\\operatorname{{rg}}(A\\mid b) = {rg_Aug}$ | "
                    f"Incógnitas $n = {n_vars}$"
                )

                variables = sp.symbols(f"x1:{n_vars+1}")
                solucion = sp.linsolve(M_aug, variables)

                if not solucion:
                    st.error("⛔ **Sistema Incompatible (S.I.):** $\\operatorname{rg}(A) < \\operatorname{rg}(A\\mid b)$. No existe solución.")
                else:
                    sol_lista = list(solucion)[0]
                    hay_parametros = any(val.free_symbols for val in sol_lista if hasattr(val, "free_symbols"))

                    if not hay_parametros:
                        st.success("✅ **Sistema Compatible Determinado (S.C.D.):** $\\operatorname{rg}(A) = \\operatorname{rg}(A\\mid b) = n$. Solución única:")
                    else:
                        grados_lib = n_vars - rg_A
                        st.warning(f"⚠️ **Sistema Compatible Indeterminado (S.C.I.):** Infinitas soluciones con **{grados_lib}** grado(s) de libertad:")

                    for i, var in enumerate(variables):
                        st.latex(rf"{sp.latex(var)} = {sp.latex(sol_lista[i])}")

# ------------------------------------------------------------------------------
# TAB 4: ANÁLISIS DE CONJUNTOS
# ------------------------------------------------------------------------------
with tab_analisis_conjunto:
    with st.container(border=True):
        header_tarjeta("Análisis de Conjuntos (Independencia Lineal, Gram-Schmidt y Base Dual)")
        seleccion = st.multiselect("Seleccione vectores para analizar:", list(st.session_state.mis_vectores.keys()))

        if seleccion:
            vectores = [st.session_state.mis_vectores[n] for n in seleccion]
            dims_seleccionadas = {v.rows for v in vectores}

            if len(dims_seleccionadas) > 1:
                st.error("⛔ Todos los vectores seleccionados deben pertenecer al mismo espacio ℝⁿ (tener la misma dimensión).")
            else:
                mat_conjunto = sp.Matrix.hstack(*vectores)
                n_vecs = len(vectores)
                dim = vectores[0].rows
                rank = mat_conjunto.rank()
                es_li = rank == n_vecs
                genera_rn = rank == dim
                es_base = es_li and genera_rn

                col_c1, col_c2 = st.columns(2, gap="large")
                with col_c1:
                    subheader_tarjeta("Matriz dispuesta por columnas")
                    imprimir_matriz_simbolica(mat_conjunto)

                with col_c2:
                    subheader_tarjeta(f"Propiedades en ℝ^{dim}")
                    st.markdown(
                        f"- **Rango del conjunto:** `{rank}`\n"
                        f"- **¿Es Linealmente Independiente?:** {'✅ Sí' if es_li else '❌ No (Linealmente Dependiente)'}\n"
                        f"- **¿Genera a todo $\\mathbb{{R}}^{{{dim}}}$?:** {'✅ Sí' if genera_rn else '❌ No'}\n"
                        f"- **¿Es Base de $\\mathbb{{R}}^{{{dim}}}$?:** {'✅ Sí' if es_base else '❌ No'}"
                    )

                st.divider()
                subheader_tarjeta("Acciones sobre el conjunto")

                col_btn1, col_btn2, col_btn3 = st.columns(3, gap="medium")
                with col_btn1:
                    if st.button("📤 Enviar como Matriz", use_container_width=True):
                        nombre_mat = "MAT_" + "_".join(seleccion)[:10]
                        st.session_state.mis_matrices[nombre_mat] = mat_conjunto
                        st.success(f"Guardado como '{nombre_mat}' en el módulo de Matrices.")

                with col_btn2:
                    ortonormal = st.checkbox("Normalizar vectores (Ortonormal)", value=True)
                    if st.button("📐 Ortogonalizar (Gram-Schmidt)", use_container_width=True):
                        if not es_li:
                            st.error("El conjunto debe ser linealmente independiente para aplicar Gram-Schmidt.")
                        else:
                            try:
                                base_ortho = sp.GramSchmidt(vectores, orthonormal=ortonormal)
                                mat_ortho = sp.Matrix.hstack(*base_ortho)
                                st.write("**Base Ortonormal resultante:**" if ortonormal else "**Base Ortogonal resultante:**")
                                imprimir_matriz_simbolica(mat_ortho)
                                st.session_state.mis_matrices["GS_MAT"] = mat_ortho
                                st.success("Guardado como 'GS_MAT' en Matrices.")
                            except Exception as e:
                                st.error(f"Error al aplicar Gram-Schmidt: {e}")

                with col_btn3:
                    if st.button("🔄 Calcular Base Dual (V*)", use_container_width=True):
                        if not es_base:
                            st.error(f"El conjunto debe ser una base de ℝ^{dim} ({dim} vectores L.I.).")
                        else:
                            try:
                                base_dual = sp.simplify(mat_conjunto.inv())
                                st.write(r"**Matriz de la Base Dual ($\mathcal{B}^*$ por renglones):**")
                                imprimir_matriz_simbolica(base_dual)
                                st.session_state.mis_matrices["DUAL_MAT"] = base_dual
                                st.success("Guardado como 'DUAL_MAT' en Matrices.")
                            except Exception as e:
                                st.error(f"Error al calcular la base dual: {e}")

        st.divider()
        subheader_tarjeta("Extraer filas o columnas de una Matriz hacia Vectores")
        if st.session_state.mis_matrices:
            c_ex1, c_ex2, c_ex3 = st.columns([1.2, 1.2, 1])
            with c_ex1:
                mat_nombre = st.selectbox("Elegir matriz:", list(st.session_state.mis_matrices.keys()))
            with c_ex2:
                tipo_ext = st.radio("Extraer:", ["Columnas", "Renglones"], horizontal=True)
            with c_ex3:
                st.write("")
                if st.button("⬇️ Extraer a Vectores", use_container_width=True):
                    M = st.session_state.mis_matrices[mat_nombre]
                    for i in range(M.rows if tipo_ext == "Renglones" else M.cols):
                        vec = M.row(i).T if tipo_ext == "Renglones" else M.col(i)
                        nombre = f"{mat_nombre}_{tipo_ext[0]}{i+1}"
                        st.session_state.mis_vectores[nombre] = vec
                    st.success(f"{tipo_ext} extraídos al inventario lateral.")
                    st.rerun()
        else:
            st.info("No hay matrices guardadas en el inventario global.")
