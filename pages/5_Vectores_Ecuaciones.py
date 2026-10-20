# pages/5_Vectores_Ecuaciones.py
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import sympy as sp
from matplotlib.ticker import AutoMinorLocator

st.set_page_config(page_title="Vectores y Sistemas - MATHESIS", page_icon="↗️", layout="wide")

from estilos import cargar_estilos_globales, encabezado_pagina, header_tarjeta, subheader_tarjeta  # noqa: E402
from utils import (  # noqa: E402
    calcular_con_limite,
    gestionar_inventario_sidebar,
    imprimir_matriz_simbolica,
    inicializar_estado,
    leer_expresion_st,
    mostrar_figura_segura,
)

cargar_estilos_globales()
inicializar_estado()

AZUL = "#0369a1"
NARANJA = "#ea580c"
VERDE = "#15803d"
ROJO = "#dc2626"
MORADO = "#7c3aed"
OSCURO = "#1e293b"
CLARO = "#cbd5e1"
FONDO = "#ffffff"
PALETA_VEC = [AZUL, NARANJA, VERDE, ROJO, MORADO, "#0891b2", "#be185d"]


def _leer_seguro(texto: str):
    if texto is None or not str(texto).strip():
        return None
    try:
        return leer_expresion_st(str(texto).strip())
    except Exception:
        st.error("La expresión ingresada no es válida.")
        return None


# ==============================================================================
# ENCABEZADO Y PANEL LATERAL
# ==============================================================================
encabezado_pagina(
    "↗️ Espacios Vectoriales y Sistemas de Ecuaciones Lineales",
    "Operaciones vectoriales, producto mixto, graficación ℝ²/ℝ³, sistemas m×n (Rouché-Frobenius), Gram-Schmidt, base dual y proyección sobre subespacios.",
)

gestionar_inventario_sidebar(
    clave_estado="mis_vectores",
    titulo="📦 Inventario de Vectores",
    etiqueta_item="Vector",
    claves_temporales=("ultimo_res_vec", "mostrar_guardado_vec"),
)

# ==============================================================================
# PESTAÑAS PRINCIPALES
# ==============================================================================
tab_gestion, tab_ops, tab_graficas, tab_sistemas, tab_analisis_conjunto = st.tabs([
    "📥 1. Gestión y Creación",
    "⚙️ 2. Operaciones y Producto Mixto",
    "📈 3. Graficación (ℝ² y ℝ³)",
    "📐 4. Sistemas Lineales (Rouché-Frobenius)",
    "🔍 5. Bases, Gram-Schmidt y Proyección en Subespacios",
])

# ------------------------------------------------------------------------------
# TAB 1: GESTIÓN Y CREACIÓN
# ------------------------------------------------------------------------------
with tab_gestion:
    with st.container(border=True):
        header_tarjeta("Constructor de Vectores y Puente con Matrices")
        col_v1, col_v2 = st.columns([1, 1.5], gap="large")

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
                    vec_nums = [_leer_seguro(c) for c in componentes]
                    if None not in vec_nums and nombre_nuevo:
                        st.session_state.mis_vectores[nombre_nuevo] = sp.Matrix(vec_nums)
                        st.success(f"Vector '{nombre_nuevo}' guardado exitosamente.")
                        st.rerun()
                    elif not nombre_nuevo:
                        st.error("Por favor, asigna un nombre al vector.")
                    else:
                        st.error("Error al procesar las componentes.")

        with col_v2:
            subheader_tarjeta("📋 Espacio de Trabajo Actual")
            if st.session_state.mis_vectores:
                cols_prev = st.columns(min(len(st.session_state.mis_vectores), 3))
                for idx_v, (nom, v) in enumerate(st.session_state.mis_vectores.items()):
                    with cols_prev[idx_v % len(cols_prev)]:
                        st.markdown(f"**{nom}** (ℝ^{v.rows}):")
                        imprimir_matriz_simbolica(v)
            else:
                st.info("Aún no has creado ningún vector. Utiliza el formulario de la izquierda para comenzar.")

            st.divider()
            subheader_tarjeta("⬇️ Extraer Filas o Columnas desde el Inventario de Matrices")
            if st.session_state.mis_matrices:
                c_ex1, c_ex2, c_ex3 = st.columns([1.2, 1.2, 1])
                with c_ex1:
                    mat_nombre = st.selectbox("Elegir matriz:", list(st.session_state.mis_matrices.keys()))
                with c_ex2:
                    tipo_ext = st.radio("Extraer:", ["Columnas", "Renglones"], horizontal=True)
                with c_ex3:
                    st.write("")
                    if st.button("⬇️ Extraer", use_container_width=True):
                        M = st.session_state.mis_matrices[mat_nombre]
                        for i in range(M.rows if tipo_ext == "Renglones" else M.cols):
                            vec = M.row(i).T if tipo_ext == "Renglones" else M.col(i)
                            nombre = f"{mat_nombre}_{tipo_ext[0]}{i + 1}"
                            st.session_state.mis_vectores[nombre] = vec
                        st.rerun()
            else:
                st.caption("No hay matrices guardadas en el inventario global.")

# ------------------------------------------------------------------------------
# TAB 2: OPERACIONES VECTORIALES Y PRODUCTO MIXTO
# ------------------------------------------------------------------------------
with tab_ops:
    if not st.session_state.mis_vectores:
        st.info("👈 Defina vectores primero en la pestaña '1. Gestión y Creación'.")
    else:
        with st.container(border=True):
            header_tarjeta("Operaciones Vectoriales y Triple Producto Escalar")
            operacion = st.radio(
                "Seleccione la operación:",
                [
                    "Suma (v + u)",
                    "Resta (v − u)",
                    "Escalar (k · v)",
                    "Norma ‖v‖",
                    "Vector Unitario (Normalizar)",
                    "Distancia d(v, u)",
                    "Producto Punto ⟨v, u⟩",
                    "Ángulo entre dos vectores",
                    "Proyección Ortogonal de v sobre u",
                    "Producto Cruz v × u (ℝ³)",
                    "Triple Producto Escalar u · (v × w) (Volumen en ℝ³)",
                ],
                horizontal=True,
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                v1_nombre = st.selectbox("Vector 1 (v / u):", list(st.session_state.mis_vectores.keys()), key="v1")
            if operacion == "Escalar (k · v)":
                with col2:
                    escalar_str = st.text_input("Ingrese el escalar k:", value="2")
            elif operacion not in ("Norma ‖v‖", "Vector Unitario (Normalizar)"):
                with col2:
                    v2_nombre = st.selectbox("Vector 2 (u / v):", list(st.session_state.mis_vectores.keys()), key="v2")
            if operacion.startswith("Triple"):
                with col3:
                    v3_nombre = st.selectbox("Vector 3 (w):", list(st.session_state.mis_vectores.keys()), key="v3")

            if st.button("🧮 Calcular Operación", use_container_width=True):
                v1 = st.session_state.mis_vectores[v1_nombre]
                res = None

                if operacion == "Escalar (k · v)":
                    esc = _leer_seguro(escalar_str)
                    if esc is not None:
                        res = sp.simplify(esc * v1)
                        imprimir_matriz_simbolica(res)

                elif operacion == "Norma ‖v‖":
                    norma_v1 = sp.simplify(v1.norm())
                    st.latex(r"\|\mathbf{" + str(v1_nombre) + r"}\| = " + sp.latex(norma_v1) + r" \approx " + sp.latex(sp.N(norma_v1, 6)))

                elif operacion == "Vector Unitario (Normalizar)":
                    if sp.simplify(v1.norm()) == 0:
                        st.error("⛔ No se puede normalizar el vector nulo (su norma es 0).")
                    else:
                        res = sp.simplify(v1 / v1.norm())
                        st.success("Vector unitario en la dirección de " + str(v1_nombre) + ":")
                        imprimir_matriz_simbolica(res)

                elif operacion.startswith("Triple"):
                    v2 = st.session_state.mis_vectores[v2_nombre]
                    v3 = st.session_state.mis_vectores[v3_nombre]
                    if v1.rows != 3 or v2.rows != 3 or v3.rows != 3:
                        st.error("⛔ El triple producto escalar requiere 3 vectores en ℝ³.")
                    else:
                        mat_3v = sp.Matrix.hstack(v1, v2, v3)
                        prod_mixto = sp.simplify(mat_3v.det())
                        vol_par = sp.simplify(sp.Abs(prod_mixto))
                        vol_tet = sp.simplify(vol_par / 6)
                        st.latex(
                            r"[\mathbf{" + str(v1_nombre) + r"}, \mathbf{" + str(v2_nombre) + r"}, \mathbf{" + str(v3_nombre)
                            + r"}] = \det" + sp.latex(mat_3v) + " = " + sp.latex(prod_mixto)
                        )
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Volumen del Paralelepípedo", f"{float(sp.N(vol_par)):.4f}" if not vol_par.free_symbols else str(vol_par))
                        m2.metric("Volumen del Tetraedro (V/6)", f"{float(sp.N(vol_tet)):.4f}" if not vol_tet.free_symbols else str(vol_tet))
                        m3.metric("¿Son Coplanares?", "Sí (Volumen = 0)" if prod_mixto == 0 else "No (Forman base de ℝ³)")

                else:
                    v2 = st.session_state.mis_vectores[v2_nombre]
                    if v1.shape != v2.shape:
                        st.error(f"⛔ Incompatibilidad de dimensiones: {v1_nombre} está en ℝ^{v1.rows} y {v2_nombre} en ℝ^{v2.rows}.")
                    else:
                        if operacion.startswith("Suma"):
                            res = sp.simplify(v1 + v2)
                            imprimir_matriz_simbolica(res)
                        elif operacion.startswith("Resta"):
                            res = sp.simplify(v1 - v2)
                            imprimir_matriz_simbolica(res)
                        elif operacion.startswith("Distancia"):
                            dist = sp.simplify((v1 - v2).norm())
                            st.latex(
                                "d(" + str(v1_nombre) + ", " + str(v2_nombre) + r") = \|\mathbf{"
                                + str(v1_nombre) + r"} - \mathbf{" + str(v2_nombre) + r"}\| = "
                                + sp.latex(dist) + r" \approx " + sp.latex(sp.N(dist, 6))
                            )
                        elif operacion.startswith("Producto Punto"):
                            dot = sp.simplify(v1.dot(v2.conjugate()))
                            st.latex(r"\langle \mathbf{" + str(v1_nombre) + r"}, \mathbf{" + str(v2_nombre) + r"} \rangle = " + sp.latex(dot))
                            if dot == 0:
                                st.info("✅ El producto punto es 0: los vectores son **ortogonales**.")
                        elif operacion.startswith("Producto Cruz"):
                            if v1.rows != 3:
                                st.error("⛔ El producto cruz solo está definido para vectores de ℝ³.")
                            else:
                                res = sp.simplify(v1.cross(v2))
                                area_par = sp.simplify(res.norm())
                                st.success("Producto vectorial v × u (ortogonal a ambos):")
                                imprimir_matriz_simbolica(res)
                                st.latex(r"\text{Área del paralelogramo } \|\mathbf{v}\times\mathbf{u}\| = " + sp.latex(area_par))
                        elif operacion.startswith("Ángulo"):
                            if sp.simplify(v1.norm()) == 0 or sp.simplify(v2.norm()) == 0:
                                st.error("⛔ El ángulo no está definido si alguno de los vectores es el vector nulo.")
                            else:
                                cos_theta = sp.simplify(v1.dot(v2) / (v1.norm() * v2.norm()))
                                ang = sp.acos(cos_theta)
                                st.latex(
                                    r"\cos(\theta) = " + sp.latex(cos_theta)
                                    + r" \implies \theta = " + sp.latex(ang)
                                    + r" \text{ rad} \approx " + sp.latex(sp.N(ang * 180 / sp.pi, 5)) + r"^\circ"
                                )
                        elif operacion.startswith("Proyección"):
                            if sp.simplify(v2.norm()) == 0:
                                st.error("⛔ No se puede proyectar sobre el vector nulo.")
                            else:
                                res = sp.simplify((v1.dot(v2.conjugate()) / v2.dot(v2.conjugate())) * v2)
                                st.write(f"**Proyección ortogonal de {v1_nombre} sobre {v2_nombre}:**")
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
                            st.rerun()

# ------------------------------------------------------------------------------
# TAB 3: GRAFICACIÓN (ESTILO LIBRO DE TEXTO)
# ------------------------------------------------------------------------------
with tab_graficas:
    with st.container(border=True):
        header_tarjeta("Graficador Espacial de Vectores (ℝ² y ℝ³)")
        if st.session_state.mis_vectores:
            seleccionados = st.multiselect("Seleccione vectores a graficar:", list(st.session_state.mis_vectores.keys()))
            if st.button("📈 Generar Gráfica", use_container_width=True) and seleccionados:
                vecs = [st.session_state.mis_vectores[n] for n in seleccionados]
                dim = vecs[0].rows

                if all(v.rows == dim for v in vecs) and dim in (2, 3) and not any(v.free_symbols or v.has(sp.I) for v in vecs):
                    if dim == 2:
                        fig, ax = plt.subplots(figsize=(6.4, 5.0), dpi=110, facecolor=FONDO)
                        ax.set_facecolor("#fbfdff")
                        ax.set_aspect("equal", adjustable="box")
                        ax.minorticks_on()
                        ax.xaxis.set_minor_locator(AutoMinorLocator(2))
                        ax.yaxis.set_minor_locator(AutoMinorLocator(2))
                        ax.grid(True, which="major", color=CLARO, lw=0.9, alpha=0.9)
                        ax.grid(True, which="minor", color="#e2e8f0", lw=0.5, alpha=0.8)
                        for lado in ("top", "right"):
                            ax.spines[lado].set_visible(False)
                        ax.axhline(0, color=OSCURO, lw=1.1, alpha=0.7)
                        ax.axvline(0, color=OSCURO, lw=1.1, alpha=0.7)
                        max_val = 1.0
                        for i, v in enumerate(vecs):
                            x_v, y_v = float(v[0]), float(v[1])
                            col = PALETA_VEC[i % len(PALETA_VEC)]
                            ax.quiver(0, 0, x_v, y_v, angles="xy", scale_units="xy", scale=1, color=col, label=f"{seleccionados[i]} ({x_v:g}, {y_v:g})", zorder=5)
                            max_val = max(max_val, abs(x_v), abs(y_v))
                        lim = max_val * 1.35
                        ax.set_xlim(-lim, lim)
                        ax.set_ylim(-lim, lim)
                        ax.set_xlabel("x", color=OSCURO, fontweight="bold")
                        ax.set_ylabel("y", color=OSCURO, fontweight="bold")
                        ax.legend(fontsize=8.5, frameon=True, framealpha=0.92, edgecolor=CLARO)
                    else:
                        fig = plt.figure(figsize=(6.8, 5.4), dpi=110, facecolor=FONDO)
                        ax = fig.add_subplot(111, projection="3d")
                        ax.set_box_aspect([1, 1, 1])
                        max_val = 1.0
                        for i, v in enumerate(vecs):
                            x_v, y_v, z_v = float(v[0]), float(v[1]), float(v[2])
                            col = PALETA_VEC[i % len(PALETA_VEC)]
                            ax.quiver(0, 0, 0, x_v, y_v, z_v, color=col, lw=2.2, label=str(seleccionados[i]))
                            max_val = max(max_val, abs(x_v), abs(y_v), abs(z_v))
                        lim = max_val * 1.25
                        ax.set_xlim([-lim, lim])
                        ax.set_ylim([-lim, lim])
                        ax.set_zlim([-lim, lim])
                        ax.set_xlabel("X", fontweight="bold")
                        ax.set_ylabel("Y", fontweight="bold")
                        ax.set_zlabel("Z", fontweight="bold")
                        ax.legend(fontsize=8.5)
                    mostrar_figura_segura(fig)
                else:
                    st.error("Todos los vectores seleccionados deben ser numéricos reales y tener la misma dimensión (2 o 3).")
        else:
            st.info("No hay vectores disponibles para graficar.")

# ------------------------------------------------------------------------------
# TAB 4: SISTEMAS DE ECUACIONES LINEALES (m x n + Rouché-Frobenius)
# ------------------------------------------------------------------------------
with tab_sistemas:
    with st.container(border=True):
        header_tarjeta("Resolución de Sistemas de Ecuaciones Lineales (A·x = b)")
        c_m, c_n = st.columns(2, gap="large")
        with c_m:
            m_ecs = int(st.number_input("Número de ecuaciones (m):", min_value=1, max_value=8, value=3, step=1))
        with c_n:
            n_vars = int(st.number_input("Número de incógnitas (n):", min_value=1, max_value=8, value=3, step=1))

        st.markdown(f"Ingrese la matriz aumentada **[A | b]** de tamaño {m_ecs} × {n_vars + 1}:")

        with st.form("form_sistema"):
            elementos = []
            for i in range(m_ecs):
                cols = st.columns(n_vars + 1)
                fila = []
                for j in range(n_vars + 1):
                    with cols[j]:
                        label = f"Ec.{i + 1} · x_{j + 1}" if j < n_vars else f"Ec.{i + 1} · b_{i + 1}"
                        val_def = "1" if i == j and j < n_vars else "0"
                        fila.append(st.text_input(label, value=val_def, key=f"sys_{m_ecs}_{n_vars}_{i}_{j}"))
                elementos.append(fila)

            submit_sys = st.form_submit_button("🧮 Analizar y Resolver Sistema", use_container_width=True)

        if submit_sys:
            M_aug = sp.zeros(m_ecs, n_vars + 1)
            error_parser = False
            for i in range(m_ecs):
                for j in range(n_vars + 1):
                    val = _leer_seguro(elementos[i][j])
                    if val is None:
                        error_parser = True
                    else:
                        M_aug[i, j] = val

            if not error_parser:
                A_coef = M_aug[:, :n_vars]
                rref_aug, _ = calcular_con_limite(M_aug.rref, timeout=6)
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
                    f"rg(A) = {rg_A} | rg(A | b) = {rg_Aug} | Incógnitas n = {n_vars}"
                )

                variables = sp.symbols("x1:" + str(n_vars + 1))
                solucion = calcular_con_limite(sp.linsolve, args=(M_aug, variables), timeout=6)

                if not solucion:
                    st.error("⛔ **Sistema Incompatible (S.I.):** rg(A) < rg(A | b). No existe solución.")
                else:
                    sol_lista = list(solucion)[0]
                    hay_parametros = any(val.free_symbols for val in sol_lista if hasattr(val, "free_symbols"))
                    if not hay_parametros:
                        st.success("✅ **Sistema Compatible Determinado (S.C.D.):** rg(A) = rg(A | b) = n. Solución única:")
                    else:
                        grados_lib = n_vars - rg_A
                        st.warning(f"⚠️ **Sistema Compatible Indeterminado (S.C.I.):** Infinitas soluciones con **{grados_lib}** grado(s) de libertad:")

                    for i, var in enumerate(variables):
                        st.latex(sp.latex(var) + " = " + sp.latex(sol_lista[i]))

# ------------------------------------------------------------------------------
# TAB 5: ANÁLISIS DE CONJUNTOS, GRAM-SCHMIDT, BASE DUAL Y PROYECCIÓN EN SUBESPACIOS
# ------------------------------------------------------------------------------
with tab_analisis_conjunto:
    with st.container(border=True):
        header_tarjeta("Análisis de Conjuntos, Ortogonalización, Base Dual y Proyección sobre Subespacios")
        seleccion = st.multiselect("Seleccione el conjunto de vectores S = {v₁, v₂, …}:", list(st.session_state.mis_vectores.keys()))

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

                t_ind, t_gs, t_proy = st.tabs([
                    "📋 1. Independencia Lineal y Base Dual",
                    "📐 2. Proceso de Gram-Schmidt",
                    "🎯 3. Coordenadas y Proyección sobre Subespacio W = gen(S)",
                ])

                with t_ind:
                    col_c1, col_c2 = st.columns(2, gap="large")
                    with col_c1:
                        subheader_tarjeta("Matriz dispuesta por columnas")
                        imprimir_matriz_simbolica(mat_conjunto)
                        if st.button("📤 Enviar como Matriz al Inventario", use_container_width=True):
                            nombre_mat = "MAT_" + "_".join(seleccion)[:10]
                            st.session_state.mis_matrices[nombre_mat] = mat_conjunto
                            st.success(f"Guardado como '{nombre_mat}' en el módulo de Matrices.")
                    with col_c2:
                        subheader_tarjeta(f"Diagnóstico en ℝ^{dim}")
                        st.markdown(
                            f"| Propiedad | Resultado |\n|---|---|\n"
                            f"| **Dimensión del subespacio generado ($\\dim W$)** | `{rank}` |\n"
                            f"| **¿Linealmente Independiente (L.I.)?** | {'✅ Sí' if es_li else '❌ No (Linealmente Dependiente)'} |\n"
                            f"| **¿Genera a todo ℝ^{dim}?** | {'✅ Sí' if genera_rn else '❌ No'} |\n"
                            f"| **¿Forma una Base de ℝ^{dim}?** | {'✅ Sí' if es_base else '❌ No'} |"
                        )
                        if es_base and st.button("🔄 Calcular Base Dual (B* = (M⁻¹)ᵀ)", use_container_width=True):
                            try:
                                # CORRECCIÓN CRÍTICA: Las columnas de (M^{-1})^T son los vectores de la base dual
                                base_dual = calcular_con_limite(lambda: sp.simplify(mat_conjunto.inv().T), timeout=6)
                                st.write("**Matriz de la Base Dual (columnas = funcionales duales):**")
                                imprimir_matriz_simbolica(base_dual)
                                st.session_state.mis_matrices["DUAL_MAT"] = base_dual
                                st.success("Guardado como 'DUAL_MAT' en Matrices.")
                            except Exception as e:
                                st.error("Error al calcular la base dual: " + str(e))

                with t_gs:
                    ortonormal = st.checkbox("Normalizar vectores (Base Ortonormal)", value=True)
                    if st.button("📐 Ejecutar Proceso de Gram-Schmidt", use_container_width=True):
                        if not es_li:
                            st.error("El conjunto debe ser linealmente independiente para aplicar Gram-Schmidt.")
                        else:
                            try:
                                base_ortho = calcular_con_limite(sp.GramSchmidt, args=(vectores,), kwargs={"orthonormal": ortonormal}, timeout=8)
                                mat_ortho = sp.Matrix.hstack(*base_ortho)
                                st.write("**Base Ortonormal resultante:**" if ortonormal else "**Base Ortogonal resultante:**")
                                imprimir_matriz_simbolica(mat_ortho)
                                st.session_state.mis_matrices["GS_MAT"] = mat_ortho
                                st.success("Guardado como 'GS_MAT' en Matrices.")
                            except Exception as e:
                                st.error("Error al aplicar Gram-Schmidt: " + str(e))

                with t_proy:
                    vec_objetivo_nom = st.selectbox(
                        "Seleccione un vector b para proyectar sobre W = gen(S) o hallar sus coordenadas:",
                        list(st.session_state.mis_vectores.keys()),
                        key="proy_sub_vec",
                    )
                    b_vec = st.session_state.mis_vectores[vec_objetivo_nom]
                    if b_vec.rows != dim:
                        st.error(f"El vector {vec_objetivo_nom} debe tener dimensión {dim}.")
                    elif st.button("🎯 Calcular Proyección Ortogonal sobre W y Distancia Mínima", use_container_width=True):
                        try:
                            base_w_ort = calcular_con_limite(sp.GramSchmidt, args=(vectores,), kwargs={"orthonormal": False}, timeout=8)
                            proy_w = sp.zeros(dim, 1)
                            for u_k in base_w_ort:
                                if u_k.norm() != 0:
                                    proy_w += (b_vec.dot(u_k) / u_k.dot(u_k)) * u_k
                            proy_w = sp.simplify(proy_w)
                            comp_perp = sp.simplify(b_vec - proy_w)
                            dist_w = sp.simplify(comp_perp.norm())

                            p1, p2, p3 = st.columns(3)
                            with p1:
                                st.markdown("**Proyección $\\hat{\\mathbf{b}} = \\operatorname{Proy}_W(\\mathbf{b}) \\in W$:**")
                                imprimir_matriz_simbolica(proy_w)
                            with p2:
                                st.markdown("**Componente Ortogonal $\\mathbf{b}^\\perp = \\mathbf{b} - \\hat{\\mathbf{b}} \\in W^\\perp$:**")
                                imprimir_matriz_simbolica(comp_perp)
                            with p3:
                                st.metric("Distancia de b a W", f"{float(sp.N(dist_w)):.4f}" if not dist_w.free_symbols else str(dist_w))
                                st.latex(r"d(\mathbf{b}, W) = \|\mathbf{b}^\perp\| = " + sp.latex(dist_w))

                            if es_base:
                                coords_b = sp.simplify(mat_conjunto.inv() * b_vec)
                                st.markdown(f"**Vector de coordenadas $[\\mathbf{{{vec_objetivo_nom}}}]_S$ en la base $S$:**")
                                imprimir_matriz_simbolica(coords_b)
                        except Exception as e:
                            st.error("Error al calcular la proyección: " + str(e))
