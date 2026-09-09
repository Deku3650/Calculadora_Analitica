import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor

try:
    from utils import leer_expresion_st, imprimir_matriz_simbolica
except ImportError:
    st.error("Error crítico: No se pudo cargar el analizador matemático desde utils.py. Asegúrese de ejecutar la app desde la raíz.")
    st.stop()

st.set_page_config(page_title="Ecuaciones Diferenciales", layout="wide")

# ==============================================================================
# INICIALIZACIÓN DE MEMORIA PERSISTENTE (CRÍTICO PARA QUE LOS BOTONES FUNCIONEN)
# ==============================================================================
if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}
if 'sys_P' not in st.session_state:
    st.session_state.sys_P = None
if 'sys_Q' not in st.session_state:
    st.session_state.sys_Q = None

st.title("🌪️ Análisis de Campos Vectoriales y Sistemas Dinámicos")
st.markdown("Estudio de sistemas lineales y no lineales, retratos de fase y linealización Jacobiana en $\mathbb{R}^2$.")

tab_sistemas, tab_edo1 = st.tabs([
    "Sistemas y Plano Fase (x', y')",
    "Resolutor de EDOs (1er Orden)"
])

# Símbolos base globales
t_sym, x_sym, y_sym = sp.symbols('t x y')
transf = standard_transformations + (implicit_multiplication_application, convert_xor)
dicc_loc = {'x': x_sym, 'y': y_sym, 't': t_sym, 'sin': sp.sin, 'cos': sp.cos, 'exp': sp.exp}

# ==============================================================================
# PESTAÑA 1: CAMPOS VECTORIALES (LINEALES Y NO LINEALES)
# ==============================================================================
with tab_sistemas:
    col_input, col_info = st.columns([1, 1.5])
    
    with col_input:
        st.subheader("Definición del Campo Vectorial")
        st.info("💡 Exprese su campo $V(x, y)$. Use `x` e `y` (equivalentes a $x_1, x_2$).")
        
        fuente_matriz = st.radio("Entrada:", ["Ecuaciones Explícitas", "Matriz $2\\times2$ (Lineal)", "Importar del Módulo de Matrices"])
        
        if fuente_matriz == "Ecuaciones Explícitas":
            with st.form("form_ecuaciones"):
                str_P = st.text_input("dx/dt = P(x, y, t)", value="-x*(y^2 - x^6)")
                str_Q = st.text_input("dy/dt = Q(x, y, t)", value="0")
                if st.form_submit_button("Analizar Campo Vectorial"):
                    try:
                        st.session_state.sys_P = parse_expr(str_P, transformations=transf, local_dict=dicc_loc)
                        st.session_state.sys_Q = parse_expr(str_Q, transformations=transf, local_dict=dicc_loc)
                    except Exception as e:
                        st.error(f"Error de sintaxis: {e}. Revise los paréntesis.")
                        
        elif fuente_matriz == "Matriz $2\\times2$ (Lineal)":
            with st.form("form_matriz_sist"):
                c1, c2 = st.columns(2)
                with c1: 
                    a11 = st.text_input("a:", value="-1")
                    a21 = st.text_input("c:", value="0")
                with c2: 
                    a12 = st.text_input("b:", value="0")
                    a22 = st.text_input("d:", value="-3")
                if st.form_submit_button("Cargar Sistema Lineal"):
                    try:
                        st.session_state.sys_P = leer_expresion_st(a11)*x_sym + leer_expresion_st(a12)*y_sym
                        st.session_state.sys_Q = leer_expresion_st(a21)*x_sym + leer_expresion_st(a22)*y_sym
                    except: st.error("Error en las entradas.")
                    
        elif fuente_matriz == "Importar del Módulo de Matrices":
            matrices_2x2 = {k: v for k, v in st.session_state.mis_matrices.items() if v.shape == (2, 2)}
            if not matrices_2x2:
                st.warning("No hay matrices $2 \times 2$ guardadas.")
            else:
                nombre_mat = st.selectbox("Seleccione Matriz:", list(matrices_2x2.keys()))
                mat = matrices_2x2[nombre_mat]
                imprimir_matriz_simbolica(mat)
                if st.button("Analizar Matriz Importada"):
                    st.session_state.sys_P = mat[0,0]*x_sym + mat[0,1]*y_sym
                    st.session_state.sys_Q = mat[1,0]*x_sym + mat[1,1]*y_sym

        if st.button("🗑️ Limpiar Sistema"):
            st.session_state.sys_P = None
            st.session_state.sys_Q = None
            st.rerun()

    # ================= PROCESAMIENTO MATEMÁTICO CENTRAL =================
    if st.session_state.sys_P is not None and st.session_state.sys_Q is not None:
        P_expr = st.session_state.sys_P
        Q_expr = st.session_state.sys_Q
        
        es_autonomo = not (P_expr.has(t_sym) or Q_expr.has(t_sym))
        es_lineal = not (P_expr.has(x_sym**2, y_sym**2, x_sym*y_sym, sp.sin, sp.exp) or Q_expr.has(x_sym**2, y_sym**2, x_sym*y_sym, sp.sin, sp.exp))
        
        with col_info:
            st.subheader("1. Campo Vectorial Interpretado")
            st.latex(rf"V(x, y) = \begin{{bmatrix}} x' \\ y' \end{{bmatrix}} = \begin{{bmatrix}} {sp.latex(P_expr)} \\ {sp.latex(Q_expr)} \end{{bmatrix}}")
            
            t_eval = 0.0
            if not es_autonomo:
                st.warning("El campo es **No Autónomo** (depende del tiempo 't'). Seleccione un instante de evaluación:")
                t_eval = st.slider("Evaluar espacio en t =", min_value=-10.0, max_value=10.0, value=0.0, step=0.5)
                
            P_f = P_expr.subs(t_sym, t_eval)
            Q_f = Q_expr.subs(t_sym, t_eval)
            
            st.subheader("2. Matriz Jacobiana (Linealización)")
            J_sym = sp.Matrix([
                [sp.diff(P_f, x_sym), sp.diff(P_f, y_sym)],
                [sp.diff(Q_f, x_sym), sp.diff(Q_f, y_sym)]
            ])
            
            x0_val, y0_val = 0.0, 0.0
            if not es_lineal:
                st.info("💡 El sistema es **No Lineal**. Evalúe la matriz Jacobiana en un punto crítico $(x_0, y_0)$ para aplicar Hartman-Grobman.")
                st.latex(rf"J(x, y) = {sp.latex(J_sym)}")
                c_pt1, c_pt2 = st.columns(2)
                with c_pt1: x0_val = st.number_input("x_0:", value=0.0)
                with c_pt2: y0_val = st.number_input("y_0:", value=0.0)
            else:
                st.write("El sistema es **Lineal**. El Jacobiano es la matriz de coeficientes constante:")

            A_eval = J_sym.subs({x_sym: x0_val, y_sym: y0_val})
            
            try:
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
                else: clasificacion = "Punto Crítico Degenerado (Det = 0). Línea de puntos o no aislado."
                
                st.success(f"**Topología Local en $({x0_val}, {y0_val})$:** {clasificacion}")
                
            except Exception:
                st.error("El Jacobiano contiene singularidades numéricas en este punto.")
                vectores_propios = []

        st.divider()
        col_graf, col_sol = st.columns([1.5, 1])
        
        with col_graf:
            st.subheader("3. Retrato de Fase (Global)")
            
            @st.cache_data
            def graficar_campo_vectorial(str_p, str_q, t_val):
                p_eq = parse_expr(str_p, transformations=transf, local_dict=dicc_loc).subs(t_sym, t_val)
                q_eq = parse_expr(str_q, transformations=transf, local_dict=dicc_loc).subs(t_sym, t_val)
                
                func_U = sp.lambdify((x_sym, y_sym), p_eq, modules=['numpy'])
                func_V = sp.lambdify((x_sym, y_sym), q_eq, modules=['numpy'])
                
                Y, X = np.mgrid[-5:5:30j, -5:5:30j]
                
                U = np.broadcast_to(func_U(X, Y), X.shape)
                V = np.broadcast_to(func_V(X, Y), X.shape)
                
                velocidad = np.sqrt(U**2 + V**2)
                
                fig, ax = plt.subplots(figsize=(8, 7))
                ax.streamplot(X, Y, U, V, color=velocidad, cmap='inferno', linewidth=1, arrowsize=1.5, density=1.5)
                
                # Trazado de isoclinas con protección matemática (si el campo es constante, contour falla)
                try:
                    if np.ptp(U) > 0: ax.contour(X, Y, U, levels=[0], colors=['red'], alpha=0.5, linestyles='dashed', linewidths=2)
                except Exception: pass
                
                try:
                    if np.ptp(V) > 0: ax.contour(X, Y, V, levels=[0], colors=['blue'], alpha=0.5, linestyles='dashed', linewidths=2)
                except Exception: pass

                ax.set_xlim([-5, 5])
                ax.set_ylim([-5, 5])
                ax.axhline(0, color='white', linewidth=1)
                ax.axvline(0, color='white', linewidth=1)
                
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                ax.tick_params(colors='white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
                for spine in ax.spines.values(): spine.set_edgecolor('white')
                
                ax.plot([], [], color='red', linestyle='dashed', label="Isoclina x'=0")
                ax.plot([], [], color='blue', linestyle='dashed', label="Isoclina y'=0")
                ax.legend(facecolor='#0e1117', edgecolor='white', labelcolor='white', loc='upper right')
                
                return fig

            try:
                fig_fase = graficar_campo_vectorial(str(P_expr), str(Q_expr), t_eval)
                st.pyplot(fig_fase)
            except Exception as e:
                st.error(f"Fallo en renderizado. Es posible que el campo contenga singularidades insolubles (división por cero) en la malla. Detalle: {e}")

        with col_sol:
            st.subheader("4. Ecuación de Órbitas")
            st.latex(rf"\frac{{dy}}{{dx}} = \frac{{{sp.latex(Q_expr)}}}{{{sp.latex(P_expr)}}}")
            
            # Como P_expr y Q_expr están en session_state, este botón ahora sí funcionará sin borrarse
            if st.button("Intentar solución analítica integral (dy/dx)"):
                y_orb = sp.Function('y')(x_sym)
                try:
                    eq_orbita = sp.Eq(y_orb.diff(x_sym), Q_expr.subs(y_sym, y_orb) / P_expr.subs(y_sym, y_orb))
                    sol_orbita = sp.dsolve(eq_orbita, y_orb)
                    st.info("Solución implicita general:")
                    st.latex(sp.latex(sol_orbita))
                except Exception:
                    st.warning("La ecuación de la órbita no admite una solución cerrada explícita. Típico en sistemas no lineales complejos.")

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
        
        try:
            eq_parseada = parse_expr(eq_str, transformations=transf, local_dict={'x': x, 'y': y, 'diff': sp.diff, 'exp': sp.exp, 'sin': sp.sin, 'cos': sp.cos})
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
