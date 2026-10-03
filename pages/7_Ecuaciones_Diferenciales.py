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
# INICIALIZACIÓN DE MEMORIA PERSISTENTE
# ==============================================================================
if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}
if 'sys_P' not in st.session_state:
    st.session_state.sys_P = None
if 'sys_Q' not in st.session_state:
    st.session_state.sys_Q = None

st.title("🌪️ Análisis de Campos Vectoriales y Sistemas Dinámicos")
st.markdown("Estudio de sistemas lineales y no lineales, retratos de fase, diagonalización, límites asintóticos e isoclinas en $\mathbb{R}^2$.")

tab_sistemas, tab_edo1 = st.tabs([
    "Sistemas y Plano Fase (x', y')",
    "Resolutor de EDOs (1er Orden)"
])

# Símbolos base globales
t_sym, x_sym, y_sym = sp.symbols('t x y')
c1_sym, c2_sym = sp.symbols('c_1 c_2')
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
                    a11 = st.text_input("a:", value="1")
                    a21 = st.text_input("c:", value="3")
                with c2: 
                    a12 = st.text_input("b:", value="-1")
                    a22 = st.text_input("d:", value="5")
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
                st.warning("El campo es **No Autónomo**. Seleccione un instante de evaluación $t$:")
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
                st.write("El sistema es **Lineal**. El Jacobiano es la matriz de coeficientes constante $A$:")

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

                # ==========================================================
                # NUEVO: ANÁLISIS PASO A PASO (DIAGONALIZACIÓN Y LÍMITES)
                # ==========================================================
                val_prop_reales = all(v[0].is_real for v in vectores_propios)
                es_diagonalizable = sum(v[1] for v in vectores_propios) == 2
                
                if es_diagonalizable:
                    with st.expander("Ver Análisis Analítico Paso a Paso", expanded=True):
                        st.markdown("### Polinomio Característico")
                        lam_sym = sp.Symbol('lambda')
                        pol_carac = sp.det(A_eval - lam_sym * sp.eye(2))
                        st.latex(rf"P_A(\lambda) = \det(A - \lambda I) = {sp.latex(pol_carac)} = 0")
                        
                        P_mat = []
                        lambdas = []
                        for val, mult, vecs in vectores_propios:
                            for vec in vecs:
                                P_mat.append(vec)
                                lambdas.append(val)
                                
                        if len(P_mat) == 2:
                            P_sym = sp.Matrix.hstack(*P_mat)
                            try:
                                P_inv = P_sym.inv()
                                Lambda_sym = sp.diag(*lambdas)
                                
                                st.markdown("### Cambio de Coordenadas (Diagonalización)")
                                col_p1, col_p2, col_p3 = st.columns(3)
                                with col_p1:
                                    st.write("Matriz $P$ (Vectores Propios):")
                                    st.latex(rf"P = {sp.latex(P_sym)}")
                                with col_p2:
                                    st.write("Matriz Inversa $P^{-1}$:")
                                    st.latex(rf"P^{{-1}} = {sp.latex(P_inv)}")
                                with col_p3:
                                    st.write("Matriz Diagonal $\Lambda = P^{-1}AP$:")
                                    st.latex(rf"\Lambda = {sp.latex(Lambda_sym)}")
                                
                                st.markdown("### Soluciones del Sistema")
                                y1_sol = c1_sym * sp.exp(lambdas[0] * t_sym)
                                y2_sol = c2_sym * sp.exp(lambdas[1] * t_sym)
                                Y_sol = sp.Matrix([y1_sol, y2_sol])
                                
                                st.write("**1. Solución en el eje canónico desacoplado $\dot{y} = \Lambda y$:**")
                                st.latex(rf"y(t) = \begin{{bmatrix}} y_1(t) \\ y_2(t) \end{{bmatrix}} = {sp.latex(Y_sol)}")
                                
                                X_sol = P_sym * Y_sol
                                st.write("**2. Solución en el sistema original $x(t) = P y(t)$:**")
                                st.latex(rf"x(t) = \begin{{bmatrix}} x(t) \\ y(t) \end{{bmatrix}} = {sp.latex(sp.simplify(X_sol))}")

                                if val_prop_reales and lambdas[0] != lambdas[1]:
                                    st.markdown("### Comportamiento Asintótico (Límites)")
                                    x_t_expr = X_sol[0]
                                    y_t_expr = X_sol[1]
                                    razon_expr = y_t_expr / x_t_expr
                                    
                                    st.write("Pendiente de las trayectorias $m(t) = \\frac{y(t)}{x(t)}$:")
                                    st.latex(rf"m(t) = \frac{{{sp.latex(y_t_expr)}}}{{{sp.latex(x_t_expr)}}}")
                                    
                                    try:
                                        lim_inf_pos = sp.limit(razon_expr, t_sym, sp.oo)
                                        lim_inf_neg = sp.limit(razon_expr, t_sym, -sp.oo)
                                        
                                        c_lim1, c_lim2 = st.columns(2)
                                        with c_lim1:
                                            st.write("Dirección cuando $t \\to \infty$:")
                                            st.latex(rf"\lim_{{t \to \infty}} m(t) = {sp.latex(lim_inf_pos)}")
                                        with c_lim2:
                                            st.write("Dirección cuando $t \\to -\infty$:")
                                            st.latex(rf"\lim_{{t \to -\infty}} m(t) = {sp.latex(lim_inf_neg)}")
                                            
                                        st.caption("Los límites asintóticos confirman que las trayectorias nacen o mueren siendo tangentes/paralelas a los vectores propios.")
                                    except:
                                        st.warning("Los límites asintóticos dependen fuertemente de las condiciones iniciales $c_1, c_2$.")

                            except Exception as e:
                                st.error(f"Error en la diagonalización: {e}")
                
            except Exception:
                st.error("El Jacobiano contiene singularidades numéricas en este punto.")
                vectores_propios = []

        st.divider()
        st.subheader("3. Análisis Gráfico del Sistema")
        
        # Determine tabs based on system properties
        if es_lineal and 'Lambda_sym' in locals() and val_prop_reales:
            tab_fase, tab_vect, tab_canonico = st.tabs(["🌊 Retrato de Fase (Original)", "🔀 Campo Vectorial (Quiver)", "📐 Plano Canónico (y1, y2)"])
            mostrar_canonico = True
        else:
            tab_fase, tab_vect = st.tabs(["🌊 Retrato de Fase (Original)", "🔀 Campo Vectorial (Quiver)"])
            mostrar_canonico = False

        @st.cache_data
        def generar_graficas_sistema(str_p, str_q, t_val, str_A=None):
            p_eq = parse_expr(str_p, transformations=transf, local_dict=dicc_loc).subs(t_sym, t_val)
            q_eq = parse_expr(str_q, transformations=transf, local_dict=dicc_loc).subs(t_sym, t_val)
            
            puntos_criticos = []
            try:
                equilibrios = sp.solve([p_eq, q_eq], (x_sym, y_sym), dict=True)
                if isinstance(equilibrios, list):
                    for sol in equilibrios:
                        if x_sym in sol and y_sym in sol:
                            if sol[x_sym].is_real and sol[y_sym].is_real:
                                puntos_criticos.append((float(sol[x_sym]), float(sol[y_sym])))
            except Exception:
                pass
            
            func_U = sp.lambdify((x_sym, y_sym), p_eq, modules=['numpy'])
            func_V = sp.lambdify((x_sym, y_sym), q_eq, modules=['numpy'])
            
            # ==========================================
            # FIGURA 1: CAMPO VECTORIAL (QUIVER)
            # ==========================================
            fig1, ax1 = plt.subplots(figsize=(7, 6))
            Y_q, X_q = np.mgrid[-5:5:20j, -5:5:20j]
            
            U_q = np.broadcast_to(func_U(X_q, Y_q), X_q.shape).astype(np.float64)
            V_q = np.broadcast_to(func_V(X_q, Y_q), X_q.shape).astype(np.float64)
            
            N_q = np.sqrt(U_q**2 + V_q**2)
            U_norm = np.divide(U_q, N_q, out=np.zeros_like(U_q), where=N_q!=0)
            V_norm = np.divide(V_q, N_q, out=np.zeros_like(V_q), where=N_q!=0)
            
            ax1.quiver(X_q, Y_q, U_norm, V_norm, color='mediumpurple', alpha=0.8, pivot='mid')
            
            ax1.set_xlim([-5, 5]); ax1.set_ylim([-5, 5])
            ax1.axhline(0, color='black', linewidth=1); ax1.axvline(0, color='black', linewidth=1)
            ax1.grid(True, linestyle='--', alpha=0.5)
            ax1.set_xlabel("x"); ax1.set_ylabel("y")
            ax1.set_title("Campo Vectorial Direccional")
            
            # ==========================================
            # FIGURA 2: RETRATO DE FASE (CON VECTORES PROPIOS)
            # ==========================================
            fig2, ax2 = plt.subplots(figsize=(7, 6))
            Y_s, X_s = np.mgrid[-5:5:100j, -5:5:100j]
            
            U_s = np.broadcast_to(func_U(X_s, Y_s), X_s.shape).astype(np.float64)
            V_s = np.broadcast_to(func_V(X_s, Y_s), X_s.shape).astype(np.float64)
            velocidad = np.sqrt(U_s**2 + V_s**2)
            
            ax2.streamplot(X_s, Y_s, U_s, V_s, color=velocidad, cmap='viridis', linewidth=1.2, arrowsize=1.2, density=1.5)
            
            try:
                if np.ptp(U_s) > 0: ax2.contour(X_s, Y_s, U_s, levels=[0], colors=['red'], alpha=0.6, linewidths=2.0)
                if np.ptp(V_s) > 0: ax2.contour(X_s, Y_s, V_s, levels=[0], colors=['blue'], alpha=0.6, linewidths=2.0)
            except Exception: pass

            for pt in puntos_criticos:
                if -5 <= pt[0] <= 5 and -5 <= pt[1] <= 5:
                    ax1.plot(pt[0], pt[1], 'ro', markersize=8, markeredgecolor='black', zorder=5)
                    ax2.plot(pt[0], pt[1], 'ro', markersize=8, markeredgecolor='black', zorder=5)

            # --- DIBUJAR EJES PROPIOS (VARIEDADES INVARIANTES) ---
            if str_A is not None:
                try:
                    A_mat = parse_expr(str_A, transformations=transf)
                    vecs = A_mat.eigenvects()
                    colores_vp = ['orange', 'cyan']
                    idx_c = 0
                    for val, mult, vectores in vecs:
                        if val.is_real:
                            for v in vectores:
                                vx, vy = float(v[0]), float(v[1])
                                if vx != 0:
                                    m = vy / vx
                                    x_vals = np.linspace(-5, 5, 100)
                                    y_vals = m * x_vals
                                    ax2.plot(x_vals, y_vals, color=colores_vp[idx_c % 2], linestyle='--', linewidth=2.5, label=f"Eje Propio $\lambda={val}$")
                                else:
                                    ax2.axvline(0, color=colores_vp[idx_c % 2], linestyle='--', linewidth=2.5, label=f"Eje Propio $\lambda={val}$")
                                idx_c += 1
                except:
                    pass

            ax2.set_xlim([-5, 5]); ax2.set_ylim([-5, 5])
            ax2.axhline(0, color='black', linewidth=1); ax2.axvline(0, color='black', linewidth=1)
            ax2.grid(True, linestyle='--', alpha=0.5)
            ax2.set_xlabel("x_1"); ax2.set_ylabel("x_2")
            ax2.set_title("Retrato de Fase")
            
            ax2.plot([], [], color='red', linewidth=2.0, label="Isoclina x'=0")
            ax2.plot([], [], color='blue', linewidth=2.0, label="Isoclina y'=0")
            ax2.legend(loc='upper right', fontsize='small')

            # ==========================================
            # FIGURA 3: PLANO CANÓNICO Y1-Y2 (SOLO SI ES DIAGONALIZABLE)
            # ==========================================
            fig3 = None
            if str_A is not None:
                try:
                    A_mat = parse_expr(str_A, transformations=transf)
                    vecs = A_mat.eigenvects()
                    if all(v[0].is_real for v in vecs) and sum(v[1] for v in vecs) == 2:
                        lambdas_diag = []
                        for val, mult, vectores in vecs:
                            for _ in vectores:
                                lambdas_diag.append(float(val))
                                
                        fig3, ax3 = plt.subplots(figsize=(7, 6))
                        Y_c, X_c = np.mgrid[-5:5:100j, -5:5:100j]
                        U_c = lambdas_diag[0] * X_c
                        V_c = lambdas_diag[1] * Y_c
                        velocidad_c = np.sqrt(U_c**2 + V_c**2)
                        
                        ax3.streamplot(X_c, Y_c, U_c, V_c, color=velocidad_c, cmap='plasma', linewidth=1.2, density=1.5)
                        ax3.set_xlim([-5, 5]); ax3.set_ylim([-5, 5])
                        ax3.axhline(0, color='black', linewidth=1.5); ax3.axvline(0, color='black', linewidth=1.5)
                        ax3.plot(0, 0, 'ro', markersize=8, markeredgecolor='black', zorder=5)
                        ax3.grid(True, linestyle='--', alpha=0.5)
                        ax3.set_xlabel("y_1"); ax3.set_ylabel("y_2")
                        ax3.set_title(f"Plano Diagonalizado: y_1'={lambdas_diag[0]}y_1, y_2'={lambdas_diag[1]}y_2")
                except:
                    pass

            return fig1, fig2, fig3

        try:
            str_A_eval = str(A_eval) if es_lineal else None
            fig_quiver, fig_stream, fig_canonico = generar_graficas_sistema(str(P_expr), str(Q_expr), t_eval, str_A_eval)
            
            with tab_fase:
                c_graf, c_txt = st.columns([2, 1])
                with c_graf:
                    st.pyplot(fig_stream)
                with c_txt:
                    st.write("**Interpretación:**")
                    st.write("Visualización del flujo continuo del sistema original. Si el sistema es lineal y posee vectores propios reales, estos se trazan como líneas punteadas, actuando como las asíntotas y directrices fundamentales del comportamiento geométrico[span_6](start_span)[span_6](end_span)[span_7](start_span)[span_7](end_span).")
            
            with tab_vect:
                st.pyplot(fig_quiver)
                st.caption("Vectores normalizados en color morado claro mostrando la dirección pura del flujo en el espacio.")
                
            if mostrar_canonico and fig_canonico is not None:
                with tab_canonico:
                    c_graf2, c_txt2 = st.columns([2, 1])
                    with c_graf2:
                        st.pyplot(fig_canonico)
                    with c_txt2:
                        st.write("**Interpretación:**")
                        st.write("Este es el plano desacoplado $\dot{y} = \Lambda y$[span_8](start_span)[span_8](end_span). Aquí los ejes representan directamente las direcciones de los vectores propios. La matriz $P$ aplica una transformación lineal que rota y estira este espacio para formar el retrato de fase original[span_9](start_span)[span_9](end_span)[span_10](start_span)[span_10](end_span).")

        except Exception as e:
            st.error(f"Fallo en renderizado. Es posible que el campo contenga singularidades insolubles en la malla. Detalle: {e}")

        st.divider()
        st.subheader("4. Ecuación de Órbitas Diferenciales")
        st.latex(rf"\frac{{dy}}{{dx}} = \frac{{{sp.latex(Q_expr)}}}{{{sp.latex(P_expr)}}}")
        
        if st.button("Intentar solución analítica integral (dy/dx)"):
            y_orb = sp.Function('y')(x_sym)
            try:
                eq_orbita = sp.Eq(y_orb.diff(x_sym), Q_expr.subs(y_sym, y_orb) / P_expr.subs(y_sym, y_orb))
                sol_orbita = sp.dsolve(eq_orbita, y_orb)
                st.info("Solución implicita general:")
                st.latex(sp.latex(sol_orbita))
            except Exception:
                st.warning("La ecuación de la órbita no admite una solución cerrada explícita por métodos estándar en SymPy.")

# ==============================================================================
# PESTAÑA 2: EDOs DE PRIMER ORDEN (RESOLUTOR)
# ==============================================================================
with tab_edo1:
    st.subheader("Resolutor de Ecuaciones Diferenciales Ordinarias (1er Orden)")
    
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
                st.success("**Solución Particular (PVI):**")
            else:
                sol = sp.dsolve(ecuacion_formal, y)
                st.success("**Solución General:**")
            st.latex(sp.latex(sol))
            
        except Exception as e:
            st.error(f"Error al procesar la ecuación: {e}")
