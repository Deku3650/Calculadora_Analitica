import streamlit as st
import sympy as sp
import re
from utils import imprimir_matriz_simbolica, leer_expresion_st, mostrar_detalle_tl

st.set_page_config(page_title="Transformaciones Lineales", layout="wide")

# Inicialización de inventarios globales
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
    "Definir T.L.", "Detalles y Núcleo/Imagen", "Evaluar Vector", "Composición e Inversa", "Bases y Espacio Dual"
])

# --------------------------------------------------------------------------
# PESTAÑA 1: Definir T.L. (Módulo unificado y optimizado)
# --------------------------------------------------------------------------
with tab_crear:
    st.header("⚙️ Configuración y Construcción de T.L.")
    
    col_v, col_w = st.columns(2)
    with col_v:
        st.subheader("1. Espacio de Entrada / Dominio (V)")
        tipo_dom = st.selectbox("Tipo de Espacio (V)", ["R^n", "Polinomios (Pn)", "Matrices (mxn)"], key="crear_tipo_dom")
        if tipo_dom == "R^n":
            dim_v = st.number_input("Dimensión n (V):", min_value=1, value=3, key="c_dim_v")
        elif tipo_dom == "Polinomios (Pn)":
            grado = st.number_input("Grado máximo n (V):", min_value=0, value=2, key="c_grado_v")
            dim_v = grado + 1
        else:
            m = st.number_input("Filas m (V):", min_value=1, value=2, key="c_m1")
            n = st.number_input("Columnas n (V):", min_value=1, value=2, key="c_n1")
            dim_v = m * n

    with col_w:
        st.subheader("2. Espacio de Salida / Codominio (W)")
        tipo_cod = st.selectbox("Tipo de Espacio (W)", ["R^n", "Polinomios (Pn)", "Matrices (mxn)"], key="crear_tipo_cod")
        if tipo_cod == "R^n":
            dim_w = st.number_input("Dimensión n (W):", min_value=1, value=2, key="c_dim_w")
        elif tipo_cod == "Polinomios (Pn)":
            grado_cod = st.number_input("Grado máximo n (W):", min_value=0, value=2, key="c_grado_w")
            dim_w = grado_cod + 1
        else:
            m2 = st.number_input("Filas m (W):", min_value=1, value=2, key="c_m2")
            n2 = st.number_input("Columnas n (W):", min_value=1, value=2, key="c_n2")
            dim_w = m2 * n2

    st.divider()
    st.subheader("3. Coordenadas y Variables de Entrada")
    
    if tipo_dom == "Polinomios (Pn)":
        if dim_v == 3: default_vars = "a, b, c"
        elif dim_v == 2: default_vars = "m, b"
        else: default_vars = ",".join([f"a{i}" for i in range(dim_v - 1, -1, -1)])
        st.info(rf"💡 **Interpretación de Variables:** Los coeficientes ingresados mapearán el polinomio abstracto: $p(x) = { 'x^2 + '.join(default_vars.split(', ')) if dim_v==3 else 'x + '.join(default_vars.split(', ')) if dim_v==2 else '...' }$")
    else:
        if dim_v <= 4: default_vars = ",".join(["x", "y", "z", "w"][:dim_v])
        else: default_vars = ",".join([f"x{i+1}" for i in range(dim_v)])

    vars_str = st.text_input("Defina los nombres de las variables libres (separadas por comas):", value=default_vars, key="tl_input_vars")
    lista_vars = [v.strip() for v in vars_str.split(',') if v.strip()]
    
    if len(lista_vars) != dim_v:
        st.warning(f"Se requieren exactamente {dim_v} variables para el Dominio configurado.")
    else:
        variables_simbolicas = tuple(sp.symbols(v) for v in lista_vars)

        st.divider()
        st.subheader("4. Especificación de Bases de Trabajo")
        
        with st.expander("Configurar Bases No Canónicas (Opcional)"):
            st.info("ℹ️ **Instrucciones:** Ingrese cada vector columna encerrado en corchetes `[...]` y separados por comas. El sistema validará automáticamente la base. Si se deja en blanco, se utilizarán las bases canónicas estándar.")
            col_in_b1, col_in_b2 = st.columns(2)
            with col_in_b1:
                b1_txt = st.text_area("Base del Dominio (V):", value="", placeholder="Ej: [1,0], [1,1]", key="txt_b1")
            with col_in_b2:
                b2_txt = st.text_area("Base del Codominio (W):", value="", placeholder="Ej: [1,0,0], [0,1,0], [0,0,1]", key="txt_b2")

            def parsear_base_entrada(texto, dim):
                if not texto.strip(): return sp.eye(dim)
                bloques = re.findall(r'\[(.*?)\]', texto)
                if not bloques: return sp.eye(dim)
                return sp.Matrix([[parse_expr(c) for c in b.split(',')] for b in bloques]).T

            try:
                Base1 = parsear_base_entrada(b1_txt, dim_v)
                Base2 = parsear_base_entrada(b2_txt, dim_w)
                if Base1.det() == 0 or Base2.det() == 0:
                    st.error("Una de las bases ingresadas tiene determinante 0 (No es L.I.). Se usarán canónicas.")
                    Base1, Base2 = sp.eye(dim_v), sp.eye(dim_w)
                else:
                    st.success("Bases analizadas y vinculadas con éxito.")
            except:
                st.error("Error de formato al procesar corchetes. Usando bases canónicas por defecto.")
                Base1, Base2 = sp.eye(dim_v), sp.eye(dim_w)

        st.divider()
        st.subheader("5. Regla de Asignación / Correspondencia")
        metodo = st.radio("Método de definición analítica:", ["1. Regla de Correspondencia / Operador Funcional", "2. Matriz Asociada Directa", "3. Importar desde Matrices"], key="radio_metodo")

        def registrar_def_temporal(mat_asoc, mat_reg):
            st.session_state.t_mat = mat_asoc
            st.session_state.t_reg = mat_reg
            st.session_state.t_b1 = Base1
            st.session_state.t_b2 = Base2
            st.session_state.t_vars = variables_simbolicas
            st.session_state.t_dv = dim_v
            st.session_state.t_dw = dim_w
            st.rerun()

        if "1. Regla de Correspondencia" in metodo:
            if tipo_dom == "Polinomios (Pn)" and tipo_cod == "Polinomios (Pn)":
                st.markdown(rf"""
                💡 **Guía de Sintaxis del Motor de Operaciones de Cálculo:**
                * **Derivada ($p'(x)$):** `diff(p, x)` | Segunda derivada: `diff(p, x, 2)`
                * **Integral Indefinida ($\int p(x)dx$):** `integrate(p, x)`
                * **Integral Definida ($\int_0^x p(t)dt$):** `integrate(p.subs(x, t), (t, 0, x))`
                * **Operadores Lineales Combinados:** `x*diff(p,x) + 2*p`
                ---
                El polinomio abstracto se define usando tus coeficientes configurados: $p(x) = { 'x^2 + '.join(lista_vars) if dim_v==3 else 'x + '.join(lista_vars) if dim_v==2 else '...' }$
                """)
                regla_str = st.text_input("Ingrese el operador funcional $T(p) =$", value="diff(p, x)", key="op_calc_input")
                
                if st.button("Procesar Operador de Cálculo"):
                    x_s, t_s = sp.symbols('x t')
                    p_poly = sum(variables_simbolicas[i] * x_s**(dim_v - 1 - i) for i in range(dim_v))
                    try:
                        expr_eval = sp.expand(parse_expr(regla_str, local_dict={'p': p_poly, 'x': x_s, 't': t_s, 'diff': sp.diff, 'integrate': sp.integrate}))
                        st.success("Operador evaluado:")
                        st.latex(rf"T(p(x)) = {sp.latex(expr_eval)}")
                        
                        v_col = [expr_eval.coeff(x_s, g) for g in range(dim_w - 1, 0, -1)] + [expr_eval.subs(x_s, 0)]
                        mat_reg = sp.Matrix(v_col)
                        registrar_def_temporal(mat_reg.jacobian(variables_simbolicas), mat_reg)
                    except Exception as e: st.error(f"Error analítico: {e}")
            else:
                if tipo_dom == "Polinomios (Pn)":
                    st.info(rf"📝 **Guía:** Cada entrada representa una componente del Codominio calculada a partir de los coeficientes del polinomio: {variables_simbolicas}")
                with st.form("form_regla_standard"):
                    eqs = [st.text_input(f"Componente del Vector de Salida {i+1}:", value="0") for i in range(dim_w)]
                    sub_r = st.form_submit_button("Procesar Regla Analítica")
                if sub_r:
                    try:
                        v_col = [parse_expr(e) for e in eqs]
                        mat_reg = sp.Matrix(v_col)
                        if not all(val == 0 for val in mat_reg.subs({v: 0 for v in variables_simbolicas})):
                            st.error("Error: La transformación viola la condición de linealidad básica $T(\mathbf{0}) = \mathbf{0}$.")
                        else:
                            registrar_def_temporal(mat_reg.jacobian(variables_simbolicas), mat_reg)
                    except Exception as e: st.error(f"Sintaxis inválida: {e}")

        elif "2. Definir una Matriz" in metodo:
            st.write(f"Ingrese las entradas para la Matriz Asociada ($B_W \leftarrow B_V$) de tamaño ({dim_w}x{dim_v}):")
            with st.form("form_mat_tl"):
                elementos_matriz = []
                for i in range(dim_w):
                    cols_i = st.columns(dim_v)
                    fila_i = [cols_i[j].text_input(f"M({i+1},{j+1})", value="0", key=f"m_c_{i}_{j}") for j in range(dim_v)]
                    elementos_matriz.append(fila_i)
                sub_m = st.form_submit_button("Construir desde Matriz")
            if sub_m:
                try:
                    m_asoc = sp.Matrix([[parse_expr(cell) for cell in row] for row in elementos_matriz])
                    registrar_def_temporal(m_asoc, m_asoc * sp.Matrix(variables_simbolicas))
                except Exception as e: st.error(f"Error en matriz: {e}")

        elif "3. Importar" in metodo:
            if st.session_state.mis_matrices:
                m_sel = st.selectbox("Seleccione Matriz del Inventario:", list(st.session_state.mis_matrices.keys()))
                M_obj = st.session_state.mis_matrices[m_sel]
                if M_obj.shape != (dim_w, dim_v):
                    st.error(f"Dimensiones incompatibles. La matriz seleccionada mide {M_obj.shape[0]}x{M_obj.shape[1]}.")
                elif st.button("Acoplar Matriz Seleccionada"):
                    registrar_def_temporal(M_obj, M_obj * sp.Matrix(variables_simbolicas))
            else: st.warning("No hay matrices en el inventario global.")

        # Panel de guardado persistente para la creación de la T.L.
        if 't_mat' in st.session_state:
            st.divider()
            st.subheader("Confirmación de Estructura")
            c1, c2 = st.columns(2)
            with c1: st.write("**Matriz Asociada:**"); st.latex(sp.latex(st.session_state.t_mat))
            with c2: st.write("**Regla de Correspondencia:**"); st.latex(sp.latex(st.session_state.t_reg))
            
            nombre_final = st.text_input("Asigne un identificador único (Ej: T1, S):", key="save_crear_name").upper().strip()
            cb1, cb2 = st.columns([1, 5])
            with cb1:
                if st.button("💾 Guardar T.L."):
                    if nombre_final:
                        st.session_state.mis_transformaciones[nombre_final] = {
                            "dim_V": st.session_state.t_dv, "dim_W": st.session_state.t_dw,
                            "variables": st.session_state.t_vars, "matriz_asociada": st.session_state.t_mat,
                            "regla": st.session_state.t_reg, "base_dominio": st.session_state.t_b1,
                            "base_codominio": st.session_state.t_b2
                        }
                        for k in ['t_mat', 't_reg', 't_b1', 't_b2', 't_vars', 't_dv', 't_dw']: del st.session_state[k]
                        st.success(f"Transformación '{nombre_final}' almacenada.")
                        st.rerun()
                    else: st.error("Escriba un nombre.")
            with cb2:
                if st.button("❌ Cancelar Operación"):
                    for k in ['t_mat', 't_reg', 't_b1', 't_b2', 't_vars', 't_dv', 't_dw']: del st.session_state[k]
                    st.rerun()

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
                if not base_ker: st.write("El núcleo es trivial: $\{ 0 \}$")
                else: imprimir_matriz_simbolica(sp.Matrix.hstack(*base_ker))
                st.info(f"Nulidad: {len(base_ker)}")
            with col2:
                st.subheader("Imagen (Im)")
                base_im = A.columnspace()
                if not base_im: st.write("La imagen es trivial: $\{ 0 \}$")
                else: imprimir_matriz_simbolica(sp.Matrix.hstack(*base_im))
                st.info(f"Rango: {len(base_im)}")
    else: st.info("Primero defina una transformación.")

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
            if st.form_submit_button("Evaluar"):
                V = sp.Matrix([leer_expresion_st(c) for c in comp])
                imprimir_matriz_simbolica(paquete["matriz_asociada"] * V)
    else: st.info("No hay transformaciones definidas.")

# --------------------------------------------------------------------------
# PESTAÑA 4: Composición e Inversa (Cálculo, Reglas de correspondencia y Guardado)
# --------------------------------------------------------------------------
with tab_composicion:
    st.header("🔄 Operaciones Avanzadas entre Espacios Vectoriales")
    
    # --- SECCIÓN: INVERSA ---
    st.subheader("1. Operador Inverso ($T^{-1}$)")
    tl_inv = st.selectbox("Seleccione la transformación para invertir:", list(st.session_state.mis_transformaciones.keys()), key="inv_tl")
    
    if st.button("Calcular Inversa Analítica"):
        paq_inv = st.session_state.mis_transformaciones[tl_inv]
        A = paq_inv["matriz_asociada"]
        
        if paq_inv["dim_V"] != paq_inv["dim_W"]:
            st.error("Error Matemático: La matriz asociada no es cuadrada. Solo los endomorfismos de espacios equipotentes admiten inversa.")
        else:
            try:
                A_inv = sp.simplify(A.inv())
                # Construcción de variables correspondientes al codominio para la regla inversa
                vars_inv_s = tuple(sp.symbols(f"w_{i+1}") for i in range(paq_inv["dim_W"]))
                reg_inv = sp.simplify(A_inv * sp.Matrix(vars_inv_s))
                
                st.session_state.temp_inv_res = {
                    "matriz": A_inv, "regla": reg_inv, "variables": vars_inv_s,
                    "dv": paq_inv["dim_W"], "dw": paq_inv["dim_V"],
                    "b1": paq_inv["base_codominio"], "b2": paq_inv["base_dominio"]
                }
                st.success("¡Estructura invertible confirmada!")
            except: st.error("La transformación no es un Isomorfismo (Determinante nulo). No admite inversa.")

    if 'temp_inv_res' in st.session_state:
        inv_d = st.session_state.temp_inv_res
        st.write("**Matriz Asociada a la Inversa ($[T^{-1}]$):**")
        imprimir_matriz_simbolica(inv_d["matriz"])
        st.write("**Regla de Correspondencia de la Inversa ($T^{-1}(\mathbf{w})$):**")
        st.latex(sp.latex(inv_d["regla"]))
        
        nombre_inv = st.text_input("Guardar operador inverso como:", value=f"{tl_inv}_INV").upper().strip()
        if st.button("💾 Almacenar Inversa en Inventario"):
            if nombre_inv:
                st.session_state.mis_transformaciones[nombre_inv] = {
                    "dim_V": inv_d["dv"], "dim_W": inv_d["dw"], "variables": inv_d["variables"],
                    "matriz_asociada": inv_d["matriz"], "regla": inv_d["regla"],
                    "base_dominio": inv_d["b1"], "base_codominio": inv_d["b2"]
                }
                del st.session_state.temp_inv_res
                st.success(f"Inversa guardada con éxito como '{nombre_inv}'.")
                st.rerun()

    st.divider()
    
    # --- SECCIÓN: COMPOSICIÓN ---
    st.subheader("2. Composición de Transformaciones ($S \circ T$)")
    st.latex(rf"(S \circ T)(\vec{{v}})")
    
    col_t, col_s = st.columns(2)
    with col_t: T = st.selectbox("1º Se aplica (Transformación interna $T$):", list(st.session_state.mis_transformaciones.keys()), key="comp_t")
    with col_s: S = st.selectbox("2º Se aplica (Transformación externa $S$):", list(st.session_state.mis_transformaciones.keys()), key="comp_s")
    
    if st.button("Efectuar Composición"):
        paq_T = st.session_state.mis_transformaciones[T]
        paq_S = st.session_state.mis_transformaciones[S]
        
        if paq_T["dim_W"] != paq_S["dim_V"]:
            st.error(f"Incompatibilidad de dimensiones: El codominio de {T} (dim={paq_T['dim_W']}) no concuerda con el dominio de {S} (dim={paq_S['dim_V']}).")
        else:
            MT = paq_T["matriz_asociada"]
            MS = paq_S["matriz_asociada"]
            M_comp = sp.simplify(MS * MT)
            
            # Regla de correspondencia analítica
            v_inputs = sp.Matrix(paq_T["variables"])
            reg_comp = sp.simplify(M_comp * v_inputs)
            
            st.session_state.temp_comp_res = {
                "matriz": M_comp, "regla": reg_comp, "variables": paq_T["variables"],
                "dv": paq_T["dim_V"], "dw": paq_S["dim_W"],
                "b1": paq_T["base_dominio"], "b2": paq_S["base_codominio"]
            }
            st.success("Composición efectuada analíticamente.")

    if 'temp_comp_res' in st.session_state:
        comp_d = st.session_state.temp_comp_res
        st.write("**Matriz Asociada Resultante ($[S \circ T]$):**")
        imprimir_matriz_simbolica(comp_d["matriz"])
        st.write("**Regla de Correspondencia de la Composición ($(S \circ T)(\mathbf{v})$):**")
        st.latex(sp.latex(comp_d["regla"]))
        
        nombre_comp = st.text_input("Guardar composición como:", value=f"{S}_COMP_{T}").upper().strip()
        if st.button("💾 Almacenar Composición en Inventario"):
            if nombre_comp:
                st.session_state.mis_transformaciones[nombre_comp] = {
                    "dim_V": comp_d["dv"], "dim_W": comp_d["dw"], "variables": comp_d["variables"],
                    "matriz_asociada": comp_d["matriz"], "regla": comp_d["regla"],
                    "base_dominio": comp_d["b1"], "base_codominio": comp_d["b2"]
                }
                del st.session_state.temp_comp_res
                st.success(f"Composición guardada con éxito como '{nombre_comp}'.")
                st.rerun()

# --------------------------------------------------------------------------
# PESTAÑA 5: Bases y Espacio Dual
# --------------------------------------------------------------------------
with tab_bases:
    if st.session_state.mis_transformaciones:
        tl_base = st.selectbox("Seleccione la T.L. activa para operar:", list(st.session_state.mis_transformaciones.keys()), key="base_tl")
        paquete = st.session_state.mis_transformaciones[tl_base]
        
        st.subheader("Bases Actuales de la T.L.")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.write("**Base del Dominio ($\\beta$):**")
            imprimir_matriz_simbolica(paquete['base_dominio'])
        with col_b2:
            st.write("**Base del Codominio ($\gamma$):**")
            imprimir_matriz_simbolica(paquete['base_codominio'])
            
        st.divider()
        st.subheader("Cambio de Base General")
        st.write("Ingrese las nuevas bases deseadas. Use corchetes para delimitar vectores columna separados por comas:")
        
        with st.form("form_cambio_base"):
            col_nb1, col_nb2 = st.columns(2)
            with col_nb1:
                nb1_input = st.text_area("Nueva Base del Dominio ($\\beta'$):", value="", placeholder="Ej: [2,0,0], [0,-1,0], [0,0,-2]", key="new_b1")
            with col_nb2:
                nb2_input = st.text_area("Nueva Base del Codominio ($\gamma'$):", value="", placeholder="Ej: [1,1], [1,-1]", key="new_b2")
                
            submit_bases = st.form_submit_button("Efectuar Cambio de Base Estructural")
            
        if submit_bases:
            def procesar_base(texto, dim):
                if not texto.strip(): return sp.eye(dim)
                bloques = re.findall(r'\[(.*?)\]', texto)
                if not bloques: return sp.eye(dim)
                return sp.Matrix([[leer_expresion_st(c) for c in b.split(',')] for b in bloques]).T
                
            try:
                Q = procesar_base(nb1_input, paquete["dim_V"]) 
                P = procesar_base(nb2_input, paquete["dim_W"]) 
                
                if Q.det() == 0 or P.det() == 0:
                    st.error("Error algebraico: Las bases ingresadas no son linealmente independientes.")
                else:
                    A_can = paquete["matriz_asociada"]
                    P_inv = sp.simplify(P.inv())
                    M_nueva = sp.simplify(P_inv * A_can * Q)
                    
                    st.success("¡Cambio de base estructural completado!")
                    st.write("### Desglose del Teorema de Cambio de Base")
                    st.latex(r"[T]_{\beta'}^{\gamma'} = P^{-1} \cdot [T]_{\beta}^{\gamma} \cdot Q")
                    
                    col_mat1, col_mat2, col_mat3 = st.columns(3)
                    with col_mat1:
                        st.write("**Paso del Dominio ($Q$):**")
                        imprimir_matriz_simbolica(Q)
                    with col_mat2:
                        st.write("**Paso del Codominio ($P$):**")
                        imprimir_matriz_simbolica(P)
                    with col_mat3:
                        st.write("**Inversa del Codominio ($P^{-1}$):**")
                        imprimir_matriz_simbolica(P_inv)
                        
                    st.write("**Comprobación matricial explícita:**")
                    st.latex(f"{sp.latex(P_inv)} \cdot {sp.latex(A_can)} \cdot {sp.latex(Q)} = {sp.latex(M_nueva)}")
                    
                    st.write("### Nueva Matriz Asociada $[T]_{\\beta'}^{\\gamma'}$:")
                    imprimir_matriz_simbolica(M_nueva)
                    
                    st.divider()
                    st.subheader("Estructura del Espacio Dual ($V^*$)")
                    st.write("Matriz de Transición de la Base Dual ($\mathcal{{B}}^*$) asociada al nuevo dominio:")
                    imprimir_matriz_simbolica(sp.simplify(Q.inv()))
                    
            except Exception as e:
                st.error(f"Error analítico al calcular bases estructurales: {e}")
                
    else: st.info("Defina una transformación primero.")
