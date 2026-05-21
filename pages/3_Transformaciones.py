import streamlit as st
import sympy as sp
import re
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
        if 'temp_inv_res' in st.session_state: del st.session_state.temp_inv_res
        if 'temp_comp_res' in st.session_state: del st.session_state.temp_comp_res
        st.rerun()

# ==============================================================================
# ÁREA PRINCIPAL
# ==============================================================================
tab_crear, tab_analisis, tab_evaluacion, tab_composicion, tab_bases = st.tabs([
    "Definir T.L.", "Detalles y Núcleo/Imagen", "Evaluar Vector", "Composición e Inversa", "Cambio de base"
])

# --------------------------------------------------------------------------
# PESTAÑA 1: Definir T.L.
# --------------------------------------------------------------------------
with tab_crear:
    Crear_Transformacion_UI()

# --------------------------------------------------------------------------
# PESTAÑA 2: Análisis (Ker/Im)
# --------------------------------------------------------------------------
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
                if not base_ker: st.write(r"El núcleo es trivial: $\{ \mathbf{0} \}$")
                else: imprimir_matriz_simbolica(sp.Matrix.hstack(*base_ker))
                st.info(f"Nulidad: {len(base_ker)}")
            with col2:
                st.subheader("Imagen (Im)")
                base_im = A.columnspace()
                if not base_im: st.write(r"La imagen es trivial: $\{ \mathbf{0} \}$")
                else: imprimir_matriz_simbolica(sp.Matrix.hstack(*base_im))
                st.info(f"Rango: {len(base_im)}")
    else:
        st.info("Primero defina una transformación.")

# --------------------------------------------------------------------------
# PESTAÑA 3: Evaluar Vector
# --------------------------------------------------------------------------
with tab_evaluacion:
    if st.session_state.mis_transformaciones:
        tl_eval = st.selectbox("Seleccione:", list(st.session_state.mis_transformaciones.keys()), key="eval_tl")
        paquete = st.session_state.mis_transformaciones[tl_eval]
        st.write(f"Ingrese vector de dimensión ${paquete['dim_V']}$:")
        
        with st.form("form_eval"):
            comp = [st.text_input(f"v_{i+1}:", value="0") for i in range(paquete['dim_V'])]
            if st.form_submit_button("Evaluar Vector"):
                try:
                    V = sp.Matrix([leer_expresion_st(c) for c in comp])
                    res = sp.simplify(paquete["matriz_asociada"] * V)
                    st.success("Resultado de la evaluación:")
                    imprimir_matriz_simbolica(res)
                except Exception as e:
                    st.error(f"Error al evaluar el vector: {e}")
    else:
        st.info("No hay transformaciones definidas.")

# --------------------------------------------------------------------------
# PESTAÑA 4: Composición e Inversa
# --------------------------------------------------------------------------
with tab_composicion:
    st.header("🔄 Operaciones Avanzadas")
    
    # --- SECCIÓN: INVERSA ---
    st.subheader(r"1. Inversa de una Transformación Lineal ($T^{-1}$)")
    tl_inv = st.selectbox("Transformación a invertir:", list(st.session_state.mis_transformaciones.keys()), key="inv_tl")
    
    if st.button("Calcular Inversa Analítica"):
        paq_inv = st.session_state.mis_transformaciones[tl_inv]
        A = paq_inv["matriz_asociada"]
        
        if paq_inv["dim_V"] != paq_inv["dim_W"]:
            st.error("La matriz asociada no es cuadrada. Solo los endomorfismos admiten inversa.")
        else:
            try:
                M_inversa = sp.simplify(A.inv())
                vars_inv = tuple(sp.symbols(f"w_{i+1}") for i in range(paq_inv["dim_W"]))
                regla_inv = sp.simplify(M_inversa * sp.Matrix(vars_inv))
                
                st.session_state.temp_inv_res = {
                    "matriz": M_inversa, "regla": regla_inv, "variables": vars_inv,
                    "dv": paq_inv["dim_W"], "dw": paq_inv["dim_V"],
                    "b1": paq_inv["base_codominio"], "b2": paq_inv["base_dominio"]
                }
                st.success("¡Estructura invertible calculada con éxito!")
            except Exception:
                st.error("La transformación no es un Isomorfismo (determinante 0). No admite operador inverso.")

    if 'temp_inv_res' in st.session_state:
        inv_d = st.session_state.temp_inv_res
        c1, c2 = st.columns(2)
        with c1:
            st.write(r"**Matriz Asociada ($[T^{-1}]$):**")
            imprimir_matriz_simbolica(inv_d["matriz"])
        with c2:
            st.write(r"**Regla de Correspondencia ($T^{-1}(\mathbf{w})$):**")
            st.latex(sp.latex(inv_d["regla"]))
        
        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            nombre_inv = st.text_input("Guardar operador inverso como:", value=f"{tl_inv}_INV").upper().strip()
        with col_btn2:
            st.write("")
            if st.button("💾 Guardar Inversa"):
                if nombre_inv:
                    st.session_state.mis_transformaciones[nombre_inv] = {
                        "dim_V": inv_d["dv"], "dim_W": inv_d["dw"], "variables": inv_d["variables"],
                        "matriz_asociada": inv_d["matriz"], "regla": inv_d["regla"],
                        "base_dominio": inv_d["b1"], "base_codominio": inv_d["b2"]
                    }
                    del st.session_state.temp_inv_res
                    st.success(f"Operador guardado como '{nombre_inv}'.")
                    st.rerun()

    st.divider()
    
    # --- SECCIÓN: COMPOSICIÓN ---
    st.subheader(r"2. Composición de Transformaciones ($S \circ T$)")
    st.latex(r"(S \circ T)(\vec{v})")
    col_t, col_s = st.columns(2)
    with col_t: T = st.selectbox("1º Se aplica (Interna T):", list(st.session_state.mis_transformaciones.keys()), key="comp_t")
    with col_s: S = st.selectbox("2º Se aplica (Externa S):", list(st.session_state.mis_transformaciones.keys()), key="comp_s")
    
    if st.button("Efectuar Composición"):
        paq_T = st.session_state.mis_transformaciones[T]
        paq_S = st.session_state.mis_transformaciones[S]
        
        if paq_T["dim_W"] != paq_S["dim_V"]:
            st.error(f"Incompatibilidad: El codominio de {T} (dim={paq_T['dim_W']}) no coincide con el dominio de {S} (dim={paq_S['dim_V']}).")
        else:
            MT = paq_T["matriz_asociada"]
            MS = paq_S["matriz_asociada"]
            M_comp = sp.simplify(MS * MT)
            regla_comp = sp.simplify(M_comp * sp.Matrix(paq_T["variables"]))
            
            st.session_state.temp_comp_res = {
                "matriz": M_comp, "regla": regla_comp, "variables": paq_T["variables"],
                "dv": paq_T["dim_V"], "dw": paq_S["dim_W"],
                "b1": paq_T["base_dominio"], "b2": paq_S["base_codominio"]
            }
            st.success("¡Composición calculada analíticamente!")

    if 'temp_comp_res' in st.session_state:
        comp_d = st.session_state.temp_comp_res
        c1, c2 = st.columns(2)
        with c1:
            st.write(r"**Matriz Asociada Resultante ($[S \circ T]$):**")
            imprimir_matriz_simbolica(comp_d["matriz"])
        with c2:
            st.write(r"**Regla de Correspondencia ($(S \circ T)(\mathbf{v})$):**")
            st.latex(sp.latex(comp_d["regla"]))
        
        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            nombre_comp = st.text_input("Guardar composición como:", value=f"{S}_COMP_{T}").upper().strip()
        with col_btn2:
            st.write("")
            if st.button("💾 Guardar Composición"):
                if nombre_comp:
                    st.session_state.mis_transformaciones[nombre_comp] = {
                        "dim_V": comp_d["dv"], "dim_W": comp_d["dw"], "variables": comp_d["variables"],
                        "matriz_asociada": comp_d["matriz"], "regla": comp_d["regla"],
                        "base_dominio": comp_d["b1"], "base_codominio": comp_d["b2"]
                    }
                    del st.session_state.temp_comp_res
                    st.success(f"Composición guardada como '{nombre_comp}'.")
                    st.rerun()

# --------------------------------------------------------------------------
# PESTAÑA 5: Bases y Espacio Dual
# --------------------------------------------------------------------------
with tab_bases:
    if st.session_state.mis_transformaciones:
        tl_base = st.selectbox("Seleccione la T.L. activa para operar:", list(st.session_state.mis_transformaciones.keys()), key="base_tl")
        paquete = st.session_state.mis_transformaciones[tl_base]
        
        st.subheader("Bases Actuales")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.write(r"**Base del Dominio ($\beta$):**")
            imprimir_matriz_simbolica(paquete['base_dominio'])
        with col_b2:
            st.write(r"**Base del Codominio ($\gamma$):**")
            imprimir_matriz_simbolica(paquete['base_codominio'])
            
        st.divider()
        st.subheader("Cambio de Base General")
        st.write("Ingrese los vectores de las nuevas bases. Ej: `[2,0,0], [0,-1,0], [0,0,-2]`. Si deja un campo vacío, se asumirá la base canónica.")
        
        with st.form("form_cambio_base"):
            col_nb1, col_nb2 = st.columns(2)
            with col_nb1:
                nb1_input = st.text_area(r"Nueva Base Dominio ($\beta'$):", value="", key="new_b1")
            with col_nb2:
                nb2_input = st.text_area(r"Nueva Base Codominio ($\gamma'$):", value="", key="new_b2")
                
            submit_bases = st.form_submit_button("Calcular Matriz en Nuevas Bases")
            
        if submit_bases:
            import re
            def procesar_base(texto, dim):
                if not texto.strip(): return sp.eye(dim)
                bloques = re.findall(r'\[(.*?)\]', texto)
                if not bloques: return sp.eye(dim)
                matriz = []
                for b in bloques:
                    matriz.append([leer_expresion_st(c) for c in b.split(',')])
                return sp.Matrix(matriz).T
                
            try:
                Q = procesar_base(nb1_input, paquete["dim_V"]) 
                P = procesar_base(nb2_input, paquete["dim_W"]) 
                
                if Q.det() == 0 or P.det() == 0:
                    st.error("Error: Las bases ingresadas no son linealmente independientes.")
                else:
                    A_can = paquete["matriz_asociada"]
                    P_inv = sp.simplify(P.inv())
                    M_nueva = sp.simplify(P_inv * A_can * Q)
                    
                    st.success("¡Cambio de base matemático exitoso!")
                    
                    st.write("### Desglose del Teorema de Cambio de Base")
                    st.latex(r"[T]_{\beta'}^{\gamma'} = P^{-1} \cdot [T]_{\beta}^{\gamma} \cdot Q")
                    
                    col_mat1, col_mat2, col_mat3 = st.columns(3)
                    with col_mat1:
                        st.write(r"**Paso del Dominio ($Q$):**")
                        imprimir_matriz_simbolica(Q)
                    with col_mat2:
                        st.write(r"**Paso del Codominio ($P$):**")
                        imprimir_matriz_simbolica(P)
                    with col_mat3:
                        st.write(r"**Inversa de P ($P^{-1}$):**")
                        imprimir_matriz_simbolica(P_inv)
                        
                    st.write("**Comprobación de la fórmula matricial:**")
                    st.latex(rf"{sp.latex(P_inv)} \cdot {sp.latex(A_can)} \cdot {sp.latex(Q)} = {sp.latex(M_nueva)}")
                    
                    st.write(r"### Nueva Matriz Asociada $[T]_{\beta'}^{\gamma'}$:")
                    imprimir_matriz_simbolica(M_nueva)
                    
                    st.divider()
                    st.subheader(r"Espacio Dual ($V^*$)")
                    st.write(r"Matriz de Transición de la Base Dual ($\mathcal{B}^*$) asociada a la nueva base del dominio $\beta'$:")
                    imprimir_matriz_simbolica(sp.simplify(Q.inv()))
                    
            except Exception as e:
                st.error(f"Error al procesar el cambio de base. Verifique la sintaxis. Detalle: {e}")
                
    else:
        st.info("Defina una transformación primero.")
