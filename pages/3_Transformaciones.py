import streamlit as st
import sympy as sp

try:
    from utils import imprimir_matriz_simbolica, leer_expresion_st, Crear_Transformacion_UI
except ImportError:
    st.error("Error al cargar utils.py. Asegúrate de ejecutar la aplicación correctamente.")

st.set_page_config(page_title="Transformaciones Lineales", layout="wide")

if 'mis_transformaciones' not in st.session_state:
    st.session_state.mis_transformaciones = {}
if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}

st.title("🔄 Transformaciones Lineales")

# ==============================================================================
# PANEL LATERAL (INVENTARIO Y PUENTES)
# ==============================================================================
with st.sidebar:
    st.header("Inventario de T.L.")

    if st.session_state.mis_transformaciones:
        for nombre in st.session_state.mis_transformaciones.keys():
            st.write(f"- **{nombre}**")
    else:
        st.info("No hay transformaciones guardadas.")

    st.divider()

    # Puente B: Exportar T.L. a Matriz
    st.subheader("Exportar a Matrices")
    if st.session_state.mis_transformaciones:
        tl_exportar = st.selectbox("Seleccione T.L.:", list(st.session_state.mis_transformaciones.keys()), key="exp_tl")
        nombre_nueva_mat = st.text_input("Guardar matriz como:").upper().strip()

        if st.button("Exportar Matriz Asociada"):
            if nombre_nueva_mat:
                st.session_state.mis_matrices[nombre_nueva_mat] = st.session_state.mis_transformaciones[tl_exportar][
                    "matriz_asociada"]
                st.success(f"Matriz '{nombre_nueva_mat}' exportada.")
            else:
                st.error("Ingrese un nombre válido.")

    st.divider()
    if st.button("🗑️ Borrar todas las T.L."):
        st.session_state.mis_transformaciones.clear()
        st.rerun()

# ==============================================================================
# ÁREA PRINCIPAL (CREACIÓN Y OPERACIONES)
# ==============================================================================
tab_crear, tab_analisis, tab_evaluacion, tab_composicion, tab_bases = st.tabs([
    "Definir T.L.", "Núcleo e Imagen", "Evaluar Vector", "Composición e Inversa", "Bases y Espacio Dual"
])

# --------------------------------------------------------------------------
# PESTAÑA 1: Creación
# --------------------------------------------------------------------------
with tab_crear:
    # Llamamos a la función UI que ya tenías en utils.py
    Crear_Transformacion_UI()

# --------------------------------------------------------------------------
# PESTAÑA 2: Análisis (Ker, Im, Teorema de Dimensiones, Clasificación)
# --------------------------------------------------------------------------
with tab_analisis:
    if st.session_state.mis_transformaciones:
        tl_sel = st.selectbox("Seleccione Transformación a Analizar:",
                              list(st.session_state.mis_transformaciones.keys()), key="ana_tl")
        paquete = st.session_state.mis_transformaciones[tl_sel]
        A = paquete["matriz_asociada"]
        dim_V = paquete["dim_V"]
        dim_W = paquete["dim_W"]

        if st.button("Ejecutar Análisis Completo", key="btn_ana"):
            col1, col2 = st.columns(2)

            # --- NÚCLEO (KER) ---
            with col1:
                st.subheader("Núcleo (Ker)")
                base_ker = A.nullspace()
                dim_ker = len(base_ker)

                if dim_ker == 0:
                    st.write("El núcleo es trivial: $\{ 0 \}$")
                else:
                    imprimir_matriz_simbolica(sp.Matrix.hstack(*base_ker))
                st.info(f"**Nulidad:** {dim_ker}")

            # --- IMAGEN (IM) ---
            with col2:
                st.subheader("Imagen (Im)")
                base_im = A.columnspace()
                dim_im = len(base_im)

                if dim_im == 0:
                    st.write("La imagen es trivial: $\{ 0 \}$")
                else:
                    imprimir_matriz_simbolica(sp.Matrix.hstack(*base_im))
                st.info(f"**Rango:** {dim_im}")

            st.divider()

            # --- TEOREMA Y CLASIFICACIÓN ---
            st.subheader("Teorema de las Dimensiones y Clasificación")
            st.latex(r"\dim(V) = \dim(\text{Ker}) + \dim(\text{Im})")
            st.latex(f"{dim_V} = {dim_ker} + {dim_im}")

            if dim_V == dim_ker + dim_im:
                st.success("El Teorema de las Dimensiones se cumple perfectamente.")
            else:
                st.error("Incongruencia matemática detectada.")

            # Clasificación
            if dim_ker == 0 and dim_im == dim_W:
                st.success("**Clasificación:** Biyectiva (Isomorfismo). Es invertible.")
            elif dim_ker == 0:
                st.info("**Clasificación:** Inyectiva (pero no suprayectiva).")
            elif dim_im == dim_W:
                st.info("**Clasificación:** Suprayectiva (pero no inyectiva).")
            else:
                st.warning("**Clasificación:** Ni inyectiva ni suprayectiva.")
    else:
        st.info("Defina una transformación primero.")

# --------------------------------------------------------------------------
# PESTAÑA 3: Evaluación de Vectores
# --------------------------------------------------------------------------
with tab_evaluacion:
    if st.session_state.mis_transformaciones:
        tl_eval = st.selectbox("Seleccione Transformación:", list(st.session_state.mis_transformaciones.keys()),
                               key="eval_tl")
        paquete = st.session_state.mis_transformaciones[tl_eval]

        st.write(f"Ingrese un vector de dimensión ${paquete['dim_V']}$:")

        with st.form("form_eval"):
            componentes = []
            cols = st.columns(paquete["dim_V"])
            for i in range(paquete["dim_V"]):
                with cols[i]:
                    val = st.text_input(f"v_{i + 1}:", value="0", key=f"v_{i}")
                    componentes.append(val)

            if st.form_submit_button("Evaluar $T(v)$"):
                try:
                    vec_numerico = [leer_expresion_st(c) for c in componentes]
                    if None not in vec_numerico:
                        V = sp.Matrix(vec_numerico)
                        Resultado = paquete["matriz_asociada"] * V
                        st.success("Resultado de la evaluación:")
                        imprimir_matriz_simbolica(Resultado)
                except Exception:
                    st.error("Error al procesar el vector de entrada.")
    else:
        st.info("Defina una transformación primero.")

# --------------------------------------------------------------------------
# PESTAÑA 4: Composición e Inversa
# --------------------------------------------------------------------------
with tab_composicion:
    if st.session_state.mis_transformaciones:
        st.subheader("Inversa de una T.L.")
        tl_inv = st.selectbox("Seleccione Transformación:", list(st.session_state.mis_transformaciones.keys()),
                              key="inv_tl")

        if st.button("Calcular Inversa"):
            paq_inv = st.session_state.mis_transformaciones[tl_inv]
            A_inv = paq_inv["matriz_asociada"]

            if len(A_inv.nullspace()) == 0 and len(A_inv.columnspace()) == paq_inv["dim_W"]:
                try:
                    M_inversa = sp.simplify(A_inv.inv())
                    st.success("Transformación Invertible. Matriz asociada a $T^{-1}$:")
                    imprimir_matriz_simbolica(M_inversa)
                except Exception:
                    st.error("Error paramétrico al invertir.")
            else:
                st.error("La transformación no es biyectiva, por lo tanto no admite inversa.")

        st.divider()

        st.subheader("Composición $(S \circ T)(\vec{v})$")
        col_t, col_s = st.columns(2)
        with col_t:
            T_nombre = st.selectbox("1º Se aplica (T):", list(st.session_state.mis_transformaciones.keys()),
                                    key="comp_t")
        with col_s:
            S_nombre = st.selectbox("2º Se aplica (S):", list(st.session_state.mis_transformaciones.keys()),
                                    key="comp_s")

        if st.button("Calcular Composición"):
            paq_T = st.session_state.mis_transformaciones[T_nombre]
            paq_S = st.session_state.mis_transformaciones[S_nombre]

            if paq_T["dim_W"] == paq_S["dim_V"]:
                M_comp = sp.simplify(paq_S["matriz_asociada"] * paq_T["matriz_asociada"])
                st.success("Composición válida. Matriz asociada resultante:")
                imprimir_matriz_simbolica(M_comp)

                # Regla de correspondencia
                vars_T = sp.Matrix(paq_T["variables"])
                Regla_comp = sp.simplify(M_comp * vars_T)
                st.write("Regla de correspondencia resultante:")
                imprimir_matriz_simbolica(Regla_comp)
            else:
                st.error(
                    f"Incompatible: El codominio de {T_nombre} (dim={paq_T['dim_W']}) no coincide con el dominio de {S_nombre} (dim={paq_S['dim_V']}).")
    else:
        st.info("Defina al menos una transformación primero.")

# --------------------------------------------------------------------------
# PESTAÑA 5: Bases y Espacio Dual
# --------------------------------------------------------------------------
with tab_bases:
    if st.session_state.mis_transformaciones:
        tl_base = st.selectbox("Seleccione Transformación:", list(st.session_state.mis_transformaciones.keys()),
                               key="base_tl")
        paquete = st.session_state.mis_transformaciones[tl_base]

        st.subheader("Cambio de Base")
        st.write(
            "Visualiza o actualiza las bases de tu transformación (Las bases no canónicas se ingresan directamente desde el módulo de vectores y se vinculan aquí en futuras versiones).")

        col_bd, col_bc = st.columns(2)
        with col_bd:
            st.write("**Base del Dominio actual:**")
            imprimir_matriz_simbolica(paquete["base_dominio"])
        with col_bc:
            st.write("**Base del Codominio actual:**")
            imprimir_matriz_simbolica(paquete["base_codominio"])

        st.divider()

        st.subheader("Espacio Dual ($V^*$)")
        st.markdown("Calcula la Base Dual asociada a la Base del Dominio actual.")

        if st.button("Calcular Base Dual"):
            B_dom = paquete["base_dominio"]
            if B_dom.det() == 0:
                st.error("La base del dominio no es linealmente independiente (Error de estado).")
            else:
                Inversa_B = sp.simplify(B_dom.inv())
                vars_dom = paquete["variables"]

                st.success("¡Base Dual Calculada con Éxito!")
                st.write(
                    "Los funcionales $f_i$ de la Base Dual $\mathcal{B}^*$ son las filas de la matriz inversa de la base:")

                for i in range(paquete["dim_V"]):
                    fila = Inversa_B.row(i)
                    funcional = sp.simplify((fila * sp.Matrix(vars_dom))[0])
                    st.latex(f"f_{{{i + 1}}}({', '.join(map(str, vars_dom))}) = {sp.latex(funcional)}")

                st.write("Matriz de Transición de la Base Dual:")
                imprimir_matriz_simbolica(Inversa_B)
    else:
        st.info("Defina una transformación primero.")
