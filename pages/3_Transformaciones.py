import streamlit as st
import sympy as sp
from utils import imprimir_matriz_simbolica, leer_expresion_st, Crear_Transformacion_UI, mostrar_detalle_tl

st.set_page_config(page_title="Transformaciones Lineales", layout="wide")

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

with tab_crear:
    Crear_Transformacion_UI()

with tab_analisis:
    if st.session_state.mis_transformaciones:
        tl_sel = st.selectbox("Seleccione Transformación:", list(st.session_state.mis_transformaciones.keys()), key="ana_tl")
        paquete = st.session_state.mis_transformaciones[tl_sel]
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

with tab_composicion:
    st.subheader("Inversa")
    tl_inv = st.selectbox("Invertir:", list(st.session_state.mis_transformaciones.keys()), key="inv_tl")
    if st.button("Calcular Inversa"):
        A = st.session_state.mis_transformaciones[tl_inv]["matriz_asociada"]
        try: imprimir_matriz_simbolica(sp.simplify(A.inv()))
        except: st.error("No es invertible.")
        
    st.divider()
    st.subheader("Composición")
    st.latex(r"(S \circ T)(\vec{v})")
    col_t, col_s = st.columns(2)
    with col_t: T = st.selectbox("1º (T):", list(st.session_state.mis_transformaciones.keys()), key="comp_t")
    with col_s: S = st.selectbox("2º (S):", list(st.session_state.mis_transformaciones.keys()), key="comp_s")
    if st.button("Componer"):
        MT = st.session_state.mis_transformaciones[T]["matriz_asociada"]
        MS = st.session_state.mis_transformaciones[S]["matriz_asociada"]
        imprimir_matriz_simbolica(sp.simplify(MS * MT))

with tab_bases:
    if st.session_state.mis_transformaciones:
        tl_base = st.selectbox("Seleccione Transformación:", list(st.session_state.mis_transformaciones.keys()), key="base_tl")
        paquete = st.session_state.mis_transformaciones[tl_base]
        
        st.subheader("Bases Actuales")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.write("**Base del Dominio (V):**")
            imprimir_matriz_simbolica(paquete['base_dominio'])
        with col_b2:
            st.write("**Base del Codominio (W):**")
            imprimir_matriz_simbolica(paquete['base_codominio'])
            
        st.divider()
        
        st.subheader("Cambio de Base")
        st.write("Ingrese los vectores de las nuevas bases (ej: `[1,0], [1,1]`). Si deja un campo vacío, se asumirá la base canónica.")
        
        with st.form("form_cambio_base"):
            col_nb1, col_nb2 = st.columns(2)
            with col_nb1:
                nb1_input = st.text_area("Nueva Base Dominio (V):", value="", key="new_b1")
            with col_nb2:
                nb2_input = st.text_area("Nueva Base Codominio (W):", value="", key="new_b2")
                
            submit_bases = st.form_submit_button("Calcular Matriz en Nuevas Bases")
            
        if submit_bases:
            import re  # Importación local de seguridad
            def procesar_base(texto, dim):
                if not texto.strip(): return sp.eye(dim)
                bloques = re.findall(r'\[(.*?)\]', texto)
                if not bloques: return sp.eye(dim)
                matriz = []
                for b in bloques:
                    matriz.append([leer_expresion_st(c) for c in b.split(',')])
                return sp.Matrix(matriz).T
                
            try:
                B1_new = procesar_base(nb1_input, paquete["dim_V"])
                B2_new = procesar_base(nb2_input, paquete["dim_W"])
                
                # Validación de Independencia Lineal (Determinante distinto de 0)
                if B1_new.det() == 0 or B2_new.det() == 0:
                    st.error("Error: Las bases ingresadas no son linealmente independientes (el determinante es 0).")
                else:
                    # La matriz_asociada en memoria es la Jacobiana (Base Canónica)
                    A_can = paquete["matriz_asociada"]
                    
                    # Fórmula de cambio de base
                    M_nueva = sp.simplify(B2_new.inv() * A_can * B1_new)
                    
                    st.success("¡Cambio de base matemático exitoso!")
                    st.write("**Nueva Matriz Asociada:**")
                    imprimir_matriz_simbolica(M_nueva)
                    
                    st.divider()
                    st.subheader("Espacio Dual ($V^*$)")
                    st.write("Matriz de Transición de la Base Dual (Asociada a la nueva base del dominio ingresada):")
                    imprimir_matriz_simbolica(sp.simplify(B1_new.inv()))
                    
            except Exception as e:
                st.error(f"Error al procesar el cambio de base. Verifique la sintaxis. Detalle: {e}")
                
    else:
        st.info("Defina una transformación primero.")
