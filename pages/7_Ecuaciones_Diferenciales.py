import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Ecuaciones Diferenciales", layout="wide")

if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}

st.title("🌪️ Análisis de Campos Vectoriales y Sistemas Dinámicos")
st.markdown("Estudio de sistemas no lineales, retratos de fase, isoclinas curvas y linealización Jacobiana en $\mathbb{R}^2$.")

tab_sistemas, tab_edo1 = st.tabs([
    "Sistemas y Plano Fase (x', y')",
    "Resolutor de EDOs (1er Orden)"
])

# ==============================================================================
# PESTAÑA 1: CAMPOS VECTORIALES (LINEALES Y NO LINEALES)
# ==============================================================================
with tab_sistemas:
    col_input, col_info = st.columns([1, 1.5])
    
    # Símbolos base
    t_sym, x_sym, y_sym = sp.symbols('t x y')
    
    with col_input:
        st.subheader("Definición del Campo Vectorial")
        st.info("💡 Exprese su campo $V(x, y)$. Use `x` e `y` (equivalentes a $x_1, x_2$). El sistema soporta sintaxis natural como `-x(y^2 - x^6)`.")
        
        fuente_matriz = st.radio("Entrada:", ["Ecuaciones Explícitas", "Matriz $2\\times2$ (Lineal)"])
        P_expr, Q_expr = None, None
        
        if fuente_matriz == "Ecuaciones Explícitas":
            with st.form("form_ecuaciones"):
                # Placeholder muestra el ejemplo exacto de tu imagen adaptado a x, y
                str_P = st.text_input("dx/dt = P(x, y, t)", value="-x*(y^2 - x^6)")
                str_Q = st.text_input("dy/dt = Q(x, y, t)", value="0")
                submit_eq = st.form_submit_button("Analizar Campo Vectorial")
                
                if submit_eq:
                    from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
                    # Parser de alto nivel: convierte ^ en **, e inserta * entre variables pegadas (ej. 2x -> 2*x)
                    transf = standard_transformations + (implicit_multiplication_application, convert_xor)
                    dicc_loc = {'x': x_sym, 'y': y_sym, 't': t_sym, 'sin': sp.sin, 'cos': sp.cos, 'exp': sp.exp}
                    
                    try:
                        P_expr = parse_expr(str_P, transformations=transf, local_dict=dicc_loc)
                        Q_expr = parse_expr(str_Q, transformations=transf, local_dict=dicc_loc)
                    except Exception as e:
                        st.error(f"Error de sintaxis: {e}. Revise los paréntesis.")
                        
        else:
            with st.form("form_matriz_sist"):
                c1, c2 = st.columns(2)
                with c1: 
                    a11 = st.text_input("a:", value="-1")
                    a21 = st.text_input("c:", value="-1")
                with c2: 
                    a12 = st.text_input("b:", value="1")
                    a22 = st.text_input("d:", value="-1")
                if st.form_submit_button("Cargar Sistema Lineal"):
                    from utils import leer_expresion_st
                    try:
                        P_expr = leer_expresion_st(a11)*x_sym + leer_expresion_st(a12)*y_sym
                        Q_expr = leer_expresion_st(a21)*x_sym + leer_expresion_st(a22)*y_sym
                    except: st.error("Error en las entradas.")

    # ================= PROCESAMIENTO MATEMÁTICO CENTRAL =================
    if P_expr is not None and Q_expr is not None:
        es_autonomo = not (P_expr.has(t_sym) or Q_expr.has(t_sym))
        es_lineal = not (P_expr.has(x_sym**2, y_sym**2, x_sym*y_sym, sp.sin, sp.exp) or Q_expr.has(x_sym**2, y_sym**2, x_sym*y_sym, sp.sin, sp.exp))
        
        with col_info:
            st.subheader("1. Campo Vectorial Interpretado")
            st.latex(rf"V(x, y) = \begin{{bmatrix}} x' \\ y' \end{{bmatrix}} = \begin{{bmatrix}} {sp.latex(P_expr)} \\ {sp.latex(Q_expr)} \end{{bmatrix}}")
            
            t_eval = 0.0
            if not es_autonomo:
                st.warning("El campo es **No Autónomo** (depende del tiempo 't').")
                t_eval = st.slider("Evaluar espacio en t =", min_value=-10.0, max_value=10.0, value=0.0, step=0.5)
                
            P_f = P_expr.subs(t_sym, t_eval)
            Q_f = Q_expr.subs(t_sym, t_eval)
            
            # Linealización local usando la Matriz Jacobiana
            st.subheader("2. Matriz Jacobiana (Linealización)")
            J_sym = sp.Matrix([
                [sp.diff(P_f, x_sym), sp.diff(P_f, y_sym)],
                [sp.diff(Q_f, x_sym), sp.diff(Q_f, y_sym)]
            ])
            
            if not es_lineal:
                st.info("💡 El sistema es **No Lineal**. La Matriz Jacobiana preserva variables espaciales y debe evaluarse en un punto crítico $(x_0, y_0)$ específico para aplicar el Teorema de Hartman-Grobman.")
                st.latex(rf"J(x, y) = {sp.latex(J_sym)}")
                
                c_pt1, c_pt2 = st.columns(2)
                with c_pt1: x0_val = st.number_input("x_0 para linearizar:", value=0.0)
                with c_pt2: y0_val = st.number_input("y_0 para linearizar:", value=0.0)
            else:
                x0_val, y0_val = 0.0, 0.0
                st.write("El sistema es **Lineal**. El Jacobiano es la matriz de coeficientes constante:")

            A_eval = J_sym.subs({x_sym: x0_val, y_sym: y0_val})
            
            try:
                # Análisis Espectral del Punto Evaluado
                traza = sp.simplify(A_eval.trace())
                det = sp.simplify(A_eval.det())
                disc = sp.simplify(traza**2 - 4*det)
                
                c_eig1, c_eig2, c_eig3 = st.columns(3)
                with c_eig1: st.latex(rf"\tau = {sp.latex(traza)}")
                with c_eig2: st.latex(rf"\Delta = {sp.latex(det)}")
                with c_eig3: st.latex(rf"\tau^2 - 4\Delta = {sp.latex(disc)}")

                vectores_propios = A_eval.eigenvects()
                
                if det < 0: clasificacion = "Punto Silla (Inestable)"
                elif det > 0:
                    if disc > 0: clasificacion = "Nodo Inestable" if traza > 0 else "Nodo Estable"
                    elif disc < 0: clasificacion = "Foco Inestable (Espiral)" if traza > 0 else "Foco Estable"
                    else: clasificacion = "Nodo Propio/Impropio " + ("Inestable" if traza > 0 else "Estable")
                else: clasificacion = "Punto Crítico Degenerado (Det = 0). Hartman-Grobman falla."
                
                st.success(f"**Topología Local en $({x0_val}, {y0_val})$:** {clasificacion}")
                
            except Exception as e:
                st.error("El Jacobiano contiene singularidades numéricas en este punto.")
                vectores_propios = []

        st.divider()
        col_graf, col_sol = st.columns([1.5, 1])
        
        with col_graf:
            st.subheader(f"3. Retrato de Fase (Global)")
            
            # ------------------------------------------------------------------
            # MOTOR GRÁFICO PROFESIONAL CON LAMBDIFY Y CONTOUR
            # ------------------------------------------------------------------
            @st.cache_data
            def graficar_campo_vectorial(str_p, str_q, t_val):
                # Re-parseamos de forma segura dentro de la función cacheada
                p_eq = parse_expr(str_p, transformations=transf, local_dict=dicc_loc).subs(t_sym, t_val)
                q_eq = parse_expr(str_q, transformations=transf, local_dict=dicc_loc).subs(t_sym, t_val)
                
                # Lambdify convierte ecuaciones simbólicas a código numpy optimizado de C
                # Esto es lo que permite que x*(y^2 - x^6) se renderice sin explotar
                func_U = sp.lambdify((x_sym, y_sym), p_eq, modules=['numpy'])
                func_V = sp.lambdify((x_sym, y_sym), q_eq, modules=['numpy'])
                
                Y, X = np.mgrid[-5:5:30j, -5:5:30j]
                
                # Forzamos compatibilidad de dimensiones por si U o V son constantes (ej. Q=0 de tu imagen)
                U = np.broadcast_to(func_U(X, Y), X.shape)
                V = np.broadcast_to(func_V(X, Y), X.shape)
                
                velocidad = np.sqrt(U**2 + V**2)
                
                fig, ax = plt.subplots(figsize=(8, 7))
                
                # Trazado del campo vectorial principal
                ax.streamplot(X, Y, U, V, color=velocidad, cmap='inferno', linewidth=1, arrowsize=1.5, density=1.5)
                
                # Trazado de isoclinas NO LINEALES usando contornos
                # Ya no usamos rectas. ax.contour detecta donde P(X,Y) == 0 y dibuja las curvas exactas
                ax.contour(X, Y, U, levels=[0], colors=['red'], alpha=0.5, linestyles='dashed', linewidths=2)
                ax.contour(X, Y, V, levels=[0], colors=['blue'], alpha=0.5, linestyles='dashed', linewidths=2)

                ax.set_xlim([-5, 5])
                ax.set_ylim([-5, 5])
                ax.axhline(0, color='white', linewidth=1)
                ax.axvline(0, color='white', linewidth=1)
                
                # Formato oscuro profesional
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                ax.tick_params(colors='white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
                for spine in ax.spines.values(): spine.set_edgecolor('white')
                
                # Leyenda falsa para las isoclinas
                ax.plot([], [], color='red', linestyle='dashed', label="Isoclina x'=0 (Flujo vertical)")
                ax.plot([], [], color='blue', linestyle='dashed', label="Isoclina y'=0 (Flujo horizontal)")
                ax.legend(facecolor='#0e1117', edgecolor='white', labelcolor='white')
                
                return fig

            try:
                # Pasamos strings al motor gráfico para evitar fallos de caché con SymPy
                fig_fase = graficar_campo_vectorial(str(P_expr), str(Q_expr), t_eval)
                st.pyplot(fig_fase)
            except Exception as e:
                st.error(f"Fallo crítico en renderizado de malla numpy. Posible singularidad en el rango [-5, 5]. Detalle: {e}")

        with col_sol:
            st.subheader("4. Ecuación de Órbitas")
            st.latex(rf"\frac{{dy}}{{dx}} = \frac{{{sp.latex(Q_expr)}}}{{{sp.latex(P_expr)}}}")
            
            if st.button("Intentar solución analítica integral (dy/dx)"):
                y_orb = sp.Function('y')(x_sym)
                try:
                    eq_orbita = sp.Eq(y_orb.diff(x_sym), Q_expr.subs(y_sym, y_orb) / P_expr.subs(y_sym, y_orb))
                    sol_orbita = sp.dsolve(eq_orbita, y_orb)
                    st.info("Solución implicita general:")
                    st.latex(sp.latex(sol_orbita))
                except Exception:
                    st.warning("SymPy no pudo encontrar una solución cerrada (EDO no integrable por métodos elementales). Es el comportamiento esperado para sistemas altamente no lineales.")

# ==============================================================================
# PESTAÑA 2: EDOs DE PRIMER ORDEN (RESOLUTOR)
# ==============================================================================
with tab_edo1:
    st.subheader("Resolutor de Ecuaciones Diferenciales Ordinarias")
    
    eq_str = st.text_input("Ingrese la expresión igualada a cero (use diff(y, x)):", value="diff(y, x) + (2/x)*y - x**3")
    
    c_pvi1, c_pvi2 = st.columns(2)
    with c_pvi1: usar_pvi = st.checkbox("Resolver con Condición Inicial (PVI)")
    
    x0_str, y0_str = "1", "0"
    if usar_pvi:
        with c_pvi2:
            st.write("Condición Inicial: $y(x_0) = y_0$")
            c_p1, c_p2 = st.columns(2)
            with c_p1: x0_str = st.text_input("x_0:", value="1")
            with c_p2: y0_str = st.text_input("y_0:", value="0")
            
    if st.button("Resolver EDO"):
        x = sp.Symbol('x')
        y = sp.Function('y')(x)
        dicc_edo = {'x': x, 'y': y, 'diff': sp.diff, 'exp': sp.exp, 'sin': sp.sin, 'cos': sp.cos}
        
        try:
            from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
            transf = standard_transformations + (implicit_multiplication_application, convert_xor)
            eq_parseada = parse_expr(eq_str, transformations=transf, local_dict=dicc_edo)
            ecuacion_formal = sp.Eq(eq_parseada, 0)
            
            st.latex(sp.latex(ecuacion_formal))
            
            if usar_pvi:
                from utils import leer_expresion_st
                x0_val = leer_expresion_st(x0_str)
                y0_val = leer_expresion_st(y0_str)
                sol = sp.dsolve(ecuacion_formal, y, ics={y.subs(x, x0_val): y0_val})
                st.success("**Solución PVI:**")
            else:
                sol = sp.dsolve(ecuacion_formal, y)
                st.success("**Solución General:**")
            st.latex(sp.latex(sol))
            
        except Exception as e:
            st.error(f"Error al procesar la ecuación: {e}")
