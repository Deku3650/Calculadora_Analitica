import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from utils import imprimir_matriz_simbolica, leer_expresion_st, Crear_Transformacion_UI, mostrar_detalle_tl
except ImportError:
    st.error("Error: utils.py no fue encontrado en la raíz. Asegúrate de que el archivo existe.")
    st.stop() # Detenemos la ejecución si no carga
st.set_page_config(page_title="Transformaciones Lineales", layout="wide")

# Inicialización de estados globales
if 'mis_transformaciones' not in st.session_state:
    st.session_state.mis_transformaciones = {}
if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}

st.title("🔄 Módulo de Transformaciones Lineales")

# ==============================================================================
# PANEL LATERAL
# ==============================================================================
with st.sidebar:
    st.header("Gestión de T.L.")
    if st.session_state.mis_transformaciones:
        st.write("Transformaciones activas:")
        for nombre in st.session_state.mis_transformaciones.keys():
            st.write(f"• **{nombre}**")
    else:
        st.info("No hay transformaciones guardadas.")
        
    st.divider()
    if st.button("🗑️ Borrar todas las T.L."):
        st.session_state.mis_transformaciones.clear()
        st.rerun()

# ==============================================================================
# ÁREA PRINCIPAL
# ==============================================================================
tab_crear, tab_analisis, tab_evaluacion, tab_composicion, tab_bases = st.tabs([
    "Definir T.L.", "Detalles y Núcleo/Imagen", "Evaluar Vector", "Composición e Inversa", "Bases y Espacio Dual"
])

# Pestaña 1: Creación (Utiliza el flujo mejorado en utils.py)
with tab_crear:
    Crear_Transformacion_UI()

# Pestaña 2: Detalles, Núcleo e Imagen
with tab_analisis:
    if st.session_state.mis_transformaciones:
        tl_sel = st.selectbox("Seleccione Transformación:", list(st.session_state.mis_transformaciones.keys()), key="ana_tl")
        paquete = st.session_state.mis_transformaciones[tl_sel]
        
        # Invocamos la función de resumen detallado
        mostrar_detalle_tl(tl_sel, paquete)
        
        st.divider()
        if st.button("Ejecutar Análisis Completo (Ker/Im)"):
            A = paquete["matriz_asociada"]
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Núcleo (Ker)")
                base_ker = A.nullspace()
                if not base_ker: st.write("El núcleo es trivial: $\{ 0 \}$")
                else: imprimir_matriz_simbolica(sp.Matrix.hstack(*base_ker))
                st.info(f"Nulidad: {len(base_ker)}")
                
            with col2:
                st.subheader("Imagen (Im)")
                base_im = A.columnspace()
                if not base_im: st.write("La imagen es trivial: $\{ 0 \}$")
                else: imprimir_matriz_simbolica(sp.Matrix.hstack(*base_im))
                st.info(f"Rango: {len(base_im)}")
    else:
        st.info("Primero defina una transformación.")

# Pestaña 3: Evaluación de Vectores
with tab_evaluacion:
    if st.session_state.mis_transformaciones:
        tl_eval = st.selectbox("Seleccione:", list(st.session_state.mis_transformaciones.keys()), key="eval_tl")
        paquete = st.session_state.mis_transformaciones[tl_eval]
        
        st.write(f"Ingrese vector de dimensión ${paquete['dim_V']}$:")
        with st.form("form_eval"):
            comp = [st.text_input(f"v_{i+1}:", value="0") for i in range(paquete['dim_V'])]
            if st.form_submit_button("Evaluar"):
                V = sp.Matrix([leer_expresion_st(c) for c in comp])
                imprimir_matriz_simbolica(paquete["matriz_asociada"] * V)
    else:
        st.info("No hay transformaciones definidas.")

# Pestaña 4: Composición e Inversa
with tab_composicion:
    st.subheader("Inversa")
    tl_inv = st.selectbox("Invertir:", list(st.session_state.mis_transformaciones.keys()), key="inv_tl")
    if st.button("Calcular Inversa"):
        A = st.session_state.mis_transformaciones[tl_inv]["matriz_asociada"]
        try: imprimir_matriz_simbolica(sp.simplify(A.inv()))
        except: st.error("No es invertible (no es biyectiva).")
        
    st.divider()
    
    st.subheader("Composición")
    st.latex(r"(S \circ T)(\vec{v})") # Corrección de visualización
    col_t, col_s = st.columns(2)
    with col_t: T = st.selectbox("1º (T):", list(st.session_state.mis_transformaciones.keys()), key="comp_t")
    with col_s: S = st.selectbox("2º (S):", list(st.session_state.mis_transformaciones.keys()), key="comp_s")
    
    if st.button("Componer"):
        MT = st.session_state.mis_transformaciones[T]["matriz_asociada"]
        MS = st.session_state.mis_transformaciones[S]["matriz_asociada"]
        imprimir_matriz_simbolica(sp.simplify(MS * MT))

# Pestaña 5: Bases y Espacio Dual
with tab_bases:
    if st.session_state.mis_transformaciones:
        tl = st.selectbox("Seleccionar:", list(st.session_state.mis_transformaciones.keys()), key="base_tl")
        paq = st.session_state.mis_transformaciones[tl]
        st.write("Base Dominio:", paq['base_dominio'])
        st.write("Base Codominio:", paq['base_codominio'])
        if st.button("Calcular Base Dual"):
            inv = paq['base_dominio'].inv()
            imprimir_matriz_simbolica(inv)
    else:
        st.info("Defina una transformación primero.")
