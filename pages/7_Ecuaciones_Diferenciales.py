import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import scipy.integrate as spi 
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application, convert_xor

try:
    from utils import leer_expresion_st, imprimir_matriz_simbolica, parse_seguro, calcular_con_limite
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
if 'sys_R' not in st.session_state:
    st.session_state.sys_R = None

st.title("🌪️ Análisis de Campos Vectoriales y Sistemas Dinámicos")
st.markdown(r"Estudio de sistemas lineales y no lineales, retratos de fase, diagonalización, límites asintóticos e isoclinas en $\mathbb{R}^2$ y $\mathbb{R}^3$.")

tab_sistemas, tab_edo1 = st.tabs([
    "Sistemas y Plano Fase",
    "Resolutor de EDOs (1er Orden)"
])

# Símbolos base globales
t_sym, x_sym, y_sym, z_sym = sp.symbols('t x y z')
c1_sym, c2_sym, c3_sym = sp.symbols('c_1 c_2 c_3')
transf = standard_transformations + (implicit_multiplication_application, convert_xor)
dicc_loc = {'x': x_sym, 'y': y_sym, 'z': z_sym, 't': t_sym, 'sin': sp.sin, 'cos': sp.cos, 'exp': sp.exp}

# ==============================================================================
# PESTAÑA 1: CAMPOS VECTORIALES (LINEALES Y NO LINEALES)
# ==============================================================================
with tab_sistemas:
    col_input, col_info = st.columns([1, 1.5])
    
    with col_input:
        st.subheader("Definición del Campo Vectorial")
        st.info(r"💡 Exprese su campo $V(x, y)$ o $V(x, y, z)$.")
        
        fuente_matriz = st.radio("Entrada:", ["Ecuaciones Explícitas", "Matriz $2\\times2$ (Lineal)", "Matriz $3\\times3$ (Lineal)", "Importar del Módulo de Matrices"])
        
        if fuente_matriz == "Ecuaciones Explícitas":
            with st.form("form_ecuaciones"):
                str_P = st.text_input("dx/dt = P(x, y, z, t)", value="-x*(y^2 - x^6)")
                str_Q = st.text_input("dy/dt = Q(x, y, z, t)", value="0")
                str_R = st.text_input("dz/dt = R(x, y, z, t) [Opcional para 3D]", value="")
                
                if st.form_submit_button("Analizar Campo Vectorial"):
                    try:
                        st.session_state.sys_P = parse_seguro(str_P, transformaciones=transf, local_dict=dicc_loc)
                        st.session_state.sys_Q = parse_seguro(str_Q, transformaciones=transf, local_dict=dicc_loc)
                        if str_R.strip():
                            st.session_state.sys_R = parse_seguro(str_R, transformaciones=transf, local_dict=dicc_loc)
                        else:
                            st.session_state.sys_R = None
                    except Exception as e:
                        st.error(f"Error de sintaxis o seguridad: {e}. Revise los caracteres ingresados.")
                        
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
                        st.session_state.sys_R = None
                    except: st.error("Error en las entradas.")
                    
        elif fuente_matriz == "Matriz $3\\times3$ (Lineal)":
            with st.form("form_matriz_sist_3x3"):
                c1, c2, c3 = st.columns(3)
                with c1: 
                    a11 = st.text_input("a11:", value="1")
                    a21 = st.text_input("a21:", value="0")
                    a31 = st.text_input("a31:", value="0")
                with c2: 
                    a12 = st.text_input("a12:", value="0")
                    a22 = st.text_input("a22:", value="-1")
                    a32 = st.text_input("a32:", value="0")
                with c3: 
                    a13 = st.text_input("a13:", value="0")
                    a23 = st.text_input("a23:", value="0")
                    a33 = st.text_input("a33:", value="-2")
                if st.form_submit_button("Cargar Sistema Lineal 3x3"):
                    try:
                        st.session_state.sys_P = leer_expresion_st(a11)*x_sym + leer_expresion_st(a12)*y_sym + leer_expresion_st(a13)*z_sym
                        st.session_state.sys_Q = leer_expresion_st(a21)*x_sym + leer_expresion_st(a22)*y_sym + leer_expresion_st(a23)*z_sym
                        st.session_state.sys_R = leer_expresion_st(a31)*x_sym + leer_expresion_st(a32)*y_sym + leer_expresion_st(a33)*z_sym
                    except: st.error("Error en las entradas.")

        elif fuente_matriz == "Importar del Módulo de Matrices":
            matrices_compatibles = {k: v for k, v in st.session_state.mis_matrices.items() if v.shape in [(2, 2), (3, 3)]}
            if not matrices_compatibles:
                st.warning(r"No hay matrices $2 \times 2$ o $3 \times 3$ guardadas.")
            else:
                nombre_mat = st.selectbox("Seleccione Matriz:", list(matrices_compatibles.keys()))
                mat = matrices_compatibles[nombre_mat]
                imprimir_matriz_simbolica(mat)
                if st.button("Analizar Matriz Importada"):
                    st.session_state.sys_P = mat[0,0]*x_sym + mat[0,1]*y_sym + (mat[0,2]*z_sym if mat.shape == (3,3) else 0)
                    st.session_state.sys_Q = mat[1,0]*x_sym + mat[1,1]*y_sym + (mat[1,2]*z_sym if mat.shape == (3,3) else 0)
                    if mat.shape == (3,3):
                        st.session_state.sys_R = mat[2,0]*x_sym + mat[2,1]*y_sym + mat[2,2]*z_sym
                    else:
                        st.session_state.sys_R = None

        if st.button("🗑️ Limpiar Sistema"):
            st.session_state.sys_P = None
            st.session_state.sys_Q = None
            st.session_state.sys_R = None
            st.rerun()

    # ================= PROCESAMIENTO MATEMÁTICO CENTRAL =================
    if st.session_state.sys_P is not None and st.session_state.sys_Q is not None:
        P_expr = st.session_state.sys_P
        Q_expr = st.session_state.sys_Q
        es_3d = st.session_state.sys_R is not None
        Lambda_sym = None 
        
        if es_3d:
            R_expr = st.session_state.sys_R
            es_autonomo = not (P_expr.has(t_sym) or Q_expr.has(t_sym) or R_expr.has(t_sym))
        else:
            es_autonomo = not (P_expr.has(t_sym) or Q_expr.has(t_sym))
        
        with col_info:
            st.subheader("1. Campo Vectorial Interpretado")
            if es_3d:
                st.latex(rf"V(x, y, z) = \begin{{bmatrix}} x' \\ y' \\ z' \end{{bmatrix}} = \begin{{bmatrix}} {sp.latex(P_expr)} \\ {sp.latex(Q_expr)} \\ {sp.latex(R_expr)} \end{{bmatrix}}")
            else:
                st.latex(rf"V(x, y) = \begin{{bmatrix}} x' \\ y' \end{{bmatrix}} = \begin{{bmatrix}} {sp.latex(P_expr)} \\ {sp.latex(Q_expr)} \end{{bmatrix}}")
            
            t_eval = 0.0
            if not es_autonomo:
                st.warning("El campo es **No Autónomo**. Seleccione un instante de evaluación $t$:")
                t_eval = st.slider("Evaluar espacio en t =", min_value=-10.0, max_value=10.0, value=0.0, step=0.5)
                
            P_f = P_expr.subs(t_sym, t_eval)
            Q_f = Q_expr.subs(t_sym, t_eval)
            if es_3d: R_f = R_expr.subs(t_sym, t_eval)
            
            st.subheader("2. Matriz Jacobiana (Linealización)")
            if es_3d:
                J_sym = sp.Matrix([
                    [sp.diff(P_f, x_sym), sp.diff(P_f, y_sym), sp.diff(P_f, z_sym)],
                    [sp.diff(Q_f, x_sym), sp.diff(Q_f, y_sym), sp.diff(Q_f, z_sym)],
                    [sp.diff(R_f, x_sym), sp.diff(R_f, y_sym), sp.diff(R_f, z_sym)]
                ])
            else:
                J_sym = sp.Matrix([
                    [sp.diff(P_f, x_sym), sp.diff(P_f, y_sym)],
                    [sp.diff(Q_f, x_sym), sp.diff(Q_f, y_sym)]
                ])
                
            if es_3d:
                es_lineal = not bool(J_sym.free_symbols.intersection({x_sym, y_sym, z_sym}))
            else:
                es_lineal = not bool(J_sym.free_symbols.intersection({x_sym, y_sym}))
            
            x0_val, y0_val, z0_val = 0.0, 0.0, 0.0
            es_equilibrio = True 
            
            if not es_lineal:
                st.info("💡 El sistema es **No Lineal**. Evalúe la matriz Jacobiana en un punto crítico para aplicar Hartman-Grobman.")
                st.latex(rf"J = {sp.latex(J_sym)}")
                if es_3d:
                    c_pt1, c_pt2, c_pt3 = st.columns(3)
                    with c_pt1: x0_val = st.number_input("x_0:", value=0.0)
                    with c_pt2: y0_val = st.number_input("y_0:", value=0.0)
                    with c_pt3: z0_val = st.number_input("z_0:", value=0.0)
                else:
                    c_pt1, c_pt2 = st.columns(2)
                    with c_pt1: x0_val = st.number_input("x_0:", value=0.0)
                    with c_pt2: y0_val = st.number_input("y_0:", value=0.0)
                    
                sust_pto = {x_sym: x0_val, y_sym: y0_val, z_sym: z0_val} if es_3d else {x_sym: x0_val, y_sym: y0_val}
                val_P = float(P_f.subs(sust_pto))
                val_Q = float(Q_f.subs(sust_pto))
                val_R = float(R_f.subs(sust_pto)) if es_3d else 0.0
                
                es_equilibrio = np.isclose(val_P, 0, atol=1e-5) and np.isclose(val_Q, 0, atol=1e-5) and (not es_3d or np.isclose(val_R, 0, atol=1e-5))
                if not es_equilibrio:
                    st.warning(rf"⚠️ El punto evaluado **NO es un punto de equilibrio** (el campo vectorial no es nulo ahí). El análisis topológico de Hartman-Grobman carece de sentido fuera de los puntos críticos.")
            else:
                st.write("El sistema es **Lineal**. El Jacobiano es la matriz de coeficientes constante $A$:")

            if es_3d:
                A_eval = J_sym.subs({x_sym: x0_val, y_sym: y0_val, z_sym: z0_val})
            else:
                A_eval = J_sym.subs({x_sym: x0_val, y_sym: y0_val})
            
            try:
                traza = sp.simplify(A_eval.trace())
                det = sp.simplify(A_eval.det())
                
                if es_3d:
                    c_eig1, c_eig2 = st.columns(2)
                    with c_eig1: st.latex(rf"\tau = {sp.latex(traza)}")
                    with c_eig2: st.latex(rf"\Delta = {sp.latex(det)}")
                else:
                    disc = sp.simplify(traza**2 - 4*det)
                    c_eig1, c_eig2, c_eig3 = st.columns(3)
                    with c_eig1: st.latex(rf"\tau = {sp.latex(traza)}")
                    with c_eig2: st.latex(rf"\Delta = {sp.latex(det)}")
                    with c_eig3: st.latex(rf"\tau^2 - 4\Delta = {sp.latex(disc)}")

                vectores_propios = A_eval.eigenvects()
                
                real_parts = [float(sp.re(v[0])) for v in vectores_propios for _ in range(v[1])]
                es_hiperbolico = all(not np.isclose(r, 0, atol=1e-5) for r in real_parts)
                
                if not es_lineal and es_equilibrio and not es_hiperbolico:
                    st.warning("⚠️ **Punto No Hiperbólico:** Al menos un valor propio tiene parte real cero. El Teorema de Hartman-Grobman falla.")

                if not es_3d:
                    if np.isclose(float(det), 0, atol=1e-5):
                        clasificacion = "Punto Crítico Degenerado (Det = 0)."
                    elif float(det) < 0: 
                        clasificacion = "Punto Silla (Inestable)"
                    else: 
                        if np.isclose(float(traza), 0, atol=1e-5): 
                            clasificacion = "Centro (Estable u Oscilatorio)"
                        elif float(disc) > 0: 
                            clasificacion = "Nodo Inestable" if float(traza) > 0 else "Nodo Estable"
                        elif float(disc) < 0: 
                            clasificacion = "Foco Inestable (Espiral)" if float(traza) > 0 else "Foco Estable"
                        else: 
                            clasificacion = "Nodo Propio/Impropio " + ("Inestable" if float(traza) > 0 else "Estable")
                    
                    st.success(f"**Topología Local en $({x0_val}, {y0_val})$:** {clasificacion}")
                else:
                    if any(np.isclose(r, 0, atol=1e-5) for r in real_parts):
                        clasificacion = "Centro, Degenerado o No Hiperbólico (Partes reales nulas)"
                    elif all(r < -1e-5 for r in real_parts):
                        clasificacion = "Sumidero / Nodo Estable (Atractor)"
                    elif all(r > 1e-5 for r in real_parts):
                        clasificacion = "Fuente / Nodo Inestable (Repulsor)"
                    elif any(r < -1e-5 for r in real_parts) and any(r > 1e-5 for r in real_parts):
                        clasificacion = "Punto Silla (Inestable)"
                    else:
                        clasificacion = "No clasificado"
                    st.success(f"**Topología Local en $({x0_val}, {y0_val}, {z0_val})$:** {clasificacion}")

                # ==========================================================
                # ANÁLISIS PASO A PASO (DIAGONALIZACIÓN Y LÍMITES)
                # ==========================================================
                val_prop_reales = all(v[0].is_real for v in vectores_propios)
                es_diagonalizable = sum(v[1] for v in vectores_propios) == (3 if es_3d else 2)
                
                if es_diagonalizable:
                    with st.expander("Ver Análisis Analítico Paso a Paso", expanded=True):
                        st.markdown("### Polinomio Característico")
                        lam_sym = sp.Symbol('lambda')
                        pol_carac = sp.det(A_eval - lam_sym * sp.eye(3 if es_3d else 2))
                        st.latex(rf"P_A(\lambda) = \det(A - \lambda I) = {sp.latex(pol_carac)} = 0")
                        
                        P_mat = []
                        lambdas = []
                        for val, mult, vecs in vectores_propios:
                            for vec in vecs:
                                P_mat.append(vec)
                                lambdas.append(val)
                                
                        if len(P_mat) == (3 if es_3d else 2):
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
                                
                                try:
                                    x_fun = sp.Function('x')(t_sym)
                                    y_fun = sp.Function('y')(t_sym)
                                    funcs = [x_fun, y_fun]
                                    if es_3d: funcs.append(sp.Function('z')(t_sym))
                                    
                                    eqs_lin = []
                                    for i in range(len(funcs)):
                                        eq_fila = 0
                                        for j in range(len(funcs)):
                                            eq_fila += A_eval[i,j] * funcs[j]
                                        eqs_lin.append(sp.Eq(funcs[i].diff(t_sym), eq_fila))
                                        
                                    sol_real = calcular_con_limite(sp.dsolve, args=(eqs_lin,), timeout=10)
                                    
                                    st.write("**Solución analítica del sistema original:**")
                                    for eq_sol in sol_real:
                                        # Eliminar el rewrite forzado que causaba sinh/cosh
                                        st.latex(sp.latex(sp.simplify(eq_sol)))
                                        
                                except Exception:
                                    st.warning("No se pudo simplificar la solución explícita.")

                                if val_prop_reales:
                                    if not es_3d and lambdas[0] != lambdas[1]:
                                        st.markdown("### Comportamiento Asintótico (Límites)")
                                        try:
                                            x_t_expr = sol_real[0].rhs
                                            y_t_expr = sol_real[1].rhs
                                            razon_expr = y_t_expr / x_t_expr
                                            
                                            st.write(r"Pendiente de las trayectorias $m(t) = \frac{y(t)}{x(t)}$:")
                                            st.latex(rf"m(t) = \frac{{{sp.latex(y_t_expr)}}}{{{sp.latex(x_t_expr)}}}")
                                            
                                            lim_inf_pos = sp.limit(razon_expr, t_sym, sp.oo)
                                            lim_inf_neg = sp.limit(razon_expr, t_sym, -sp.oo)
                                            
                                            c_lim1, c_lim2 = st.columns(2)
                                            with c_lim1:
                                                st.write(r"Dirección cuando $t \to \infty$:")
                                                st.latex(rf"\lim_{{t \to \infty}} m(t) = {sp.latex(lim_inf_pos)}")
                                            with c_lim2:
                                                st.write(r"Dirección cuando $t \to -\infty$:")
                                                st.latex(rf"\lim_{{t \to -\infty}} m(t) = {sp.latex(lim_inf_neg)}")
                                                
                                            st.caption("Los límites asintóticos confirman que las trayectorias nacen o mueren siendo tangentes/paralelas a los vectores propios.")
                                        except:
                                            pass
                                else:
                                    st.info("💡 **Nota Matemática:** Los valores propios son complejos. El comportamiento oscilatorio (rotaciones) implica funciones periódicas (senos y cosenos), por lo que el análisis de asíntotas lineales no aplica.")

                            except Exception as e:
                                st.error(f"Error en la diagonalización: {e}")
                
            except Exception as e:
                st.error(f"El Jacobiano contiene singularidades numéricas en este punto. Detalle: {e}")
                vectores_propios = []

        st.divider()
        st.subheader("3. Análisis Gráfico del Sistema")
        
        func_U = sp.lambdify((x_sym, y_sym, z_sym) if es_3d else (x_sym, y_sym), P_f, modules=['numpy'])
        func_V = sp.lambdify((x_sym, y_sym, z_sym) if es_3d else (x_sym, y_sym), Q_f, modules=['numpy'])
        if es_3d: func_W = sp.lambdify((x_sym, y_sym, z_sym), R_f, modules=['numpy'])
        
        if es_3d:
            # Reestructuración de Pestañas: Prioridad total a los Planos Canónicos
            if es_diagonalizable and es_lineal and val_prop_reales:
                tab_canonico3d, tab_fase3d = st.tabs(["📐 Planos Canónicos (Subespacios Invariantes)", "🌌 Retrato de Fase 3D (Limpio)"])
                
                with tab_canonico3d:
                    st.write(r"Descomposición matemática del sistema en sus **Planos Canónicos**. Las trayectorias están completamente desacopladas sobre los ejes generados por los vectores propios.")
                    try:
                        fig_can, axs_can = plt.subplots(1, 3, figsize=(15, 5))
                        l1, l2, l3 = lambdas
                        Y_c, X_c = np.mgrid[-5:5:50j, -5:5:50j]
                        
                        # y1 - y2
                        U12 = float(l1) * X_c; V12 = float(l2) * Y_c
                        axs_can[0].streamplot(X_c, Y_c, U12, V12, color=np.hypot(U12, V12), cmap='viridis', density=1.2, arrowsize=1.5)
                        axs_can[0].set_title(f"Plano $y_1$-$y_2$ ($\lambda_1={l1}$, $\lambda_2={l2}$)")
                        axs_can[0].set_xlabel("y_1"); axs_can[0].set_ylabel("y_2")
                        
                        # y1 - y3
                        U13 = float(l1) * X_c; V13 = float(l3) * Y_c
                        axs_can[1].streamplot(X_c, Y_c, U13, V13, color=np.hypot(U13, V13), cmap='viridis', density=1.2, arrowsize=1.5)
                        axs_can[1].set_title(f"Plano $y_1$-$y_3$ ($\lambda_1={l1}$, $\lambda_3={l3}$)")
                        axs_can[1].set_xlabel("y_1"); axs_can[1].set_ylabel("y_3")
                        
                        # y2 - y3
                        U23 = float(l2) * X_c; V23 = float(l3) * Y_c
                        axs_can[2].streamplot(X_c, Y_c, U23, V23, color=np.hypot(U23, V23), cmap='viridis', density=1.2, arrowsize=1.5)
                        axs_can[2].set_title(f"Plano $y_2$-$y_3$ ($\lambda_2={l2}$, $\lambda_3={l3}$)")
                        axs_can[2].set_xlabel("y_2"); axs_can[2].set_ylabel("y_3")
                        
                        for ax in axs_can:
                            ax.axhline(0, color='black'); ax.axvline(0, color='black')
                            ax.grid(True, linestyle='--', alpha=0.5)
                        
                        plt.tight_layout()
                        st.pyplot(fig_can)
                    except Exception as e:
                        st.error(f"Error al generar planos canónicos: {e}")

            else:
                tab_fase3d, = st.tabs(["🌌 Retrato de Fase 3D (Limpio)"])
                    
            with tab_fase3d:
                st.write(r"Generando trayectorias dinámicas limpias en $\mathbb{R}^3$...")
                try:
                    fig3d_fase = plt.figure(figsize=(8, 8))
                    ax3d_fase = fig3d_fase.add_subplot(111, projection='3d')
                    ax3d_fase.set_box_aspect([1, 1, 1]) 
                    
                    # Ejes
                    ax3d_fase.plot([-5, 5], [0, 0], [0, 0], 'k--', alpha=0.3, linewidth=1)
                    ax3d_fase.plot([0, 0], [-5, 5], [0, 0], 'k--', alpha=0.3, linewidth=1)
                    ax3d_fase.plot([0, 0], [0, 0], [-5, 5], 'k--', alpha=0.3, linewidth=1)
                    
                    def vector_field_3d(Y, t):
                        x_v, y_v, z_v = Y
                        return [func_U(x_v, y_v, z_v), func_V(x_v, y_v, z_v), func_W(x_v, y_v, z_v)]
                    
                    ics = []
                    for r in [0.5, 2.0, 4.0]:
                        for th in np.linspace(0, np.pi, 5):
                            for ph in np.linspace(0, 2*np.pi, 8):
                                ics.append([r*np.sin(th)*np.cos(ph), r*np.sin(th)*np.sin(ph), r*np.cos(th)])
                    
                    t_span = np.linspace(0, 15, 2000) 
                    
                    for ic in ics:
                        try:
                            traj_f = spi.odeint(vector_field_3d, ic, t_span, mxstep=1000)
                            
                            # Filtro estricto: cortar si sale de la caja
                            fueras = np.where(np.max(np.abs(traj_f), axis=1) > 5.0)[0]
                            if len(fueras) > 0:
                                traj_f = traj_f[:fueras[0]]
                            
                            if len(traj_f) > 5:
                                ax3d_fase.plot(traj_f[:,0], traj_f[:,1], traj_f[:,2], color='royalblue', alpha=0.7, linewidth=1.2)
                        except Exception:
                            pass 
                    
                    ax3d_fase.set_xlabel("x")
                    ax3d_fase.set_ylabel("y")
                    ax3d_fase.set_zlabel("z")
                    ax3d_fase.set_xlim([-5, 5]); ax3d_fase.set_ylim([-5, 5]); ax3d_fase.set_zlim([-5, 5])
                    ax3d_fase.set_title("Trayectorias Dinámicas en el Espacio")
                    st.pyplot(fig3d_fase)
                except Exception as e:
                    st.error(f"Error al generar trayectorias 3D: {e}")

        else:
            if es_lineal and Lambda_sym is not None and val_prop_reales:
                tab_fase, tab_vect, tab_canonico = st.tabs(["🌊 Retrato de Fase (Original)", "🔀 Campo Vectorial (Quiver)", "📐 Plano Canónico (y1, y2)"])
                mostrar_canonico = True
            else:
                tab_fase, tab_vect = st.tabs(["🌊 Retrato de Fase (Original)", "🔀 Campo Vectorial (Quiver)"])
                mostrar_canonico = False

            def generar_graficas_sistema(str_p, str_q, t_val, str_A=None):
                p_eq = parse_seguro(str_p, transformaciones=transf, local_dict=dicc_loc).subs(t_sym, t_val)
                q_eq = parse_seguro(str_q, transformaciones=transf, local_dict=dicc_loc).subs(t_sym, t_val)
                
                puntos_criticos = []
                try:
                    equilibrios = calcular_con_limite(sp.solve, args=([p_eq, q_eq], (x_sym, y_sym)), kwargs={'dict':True}, timeout=5)
                    if isinstance(equilibrios, list):
                        for sol in equilibrios:
                            if x_sym in sol and y_sym in sol:
                                if sol[x_sym].is_real and sol[y_sym].is_real:
                                    puntos_criticos.append((float(sol[x_sym]), float(sol[y_sym])))
                except Exception:
                    pass
                
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
                
                ax2.streamplot(X_s, Y_s, U_s, V_s, color=velocidad, cmap='viridis', linewidth=1.2, arrowsize=1.5, density=1.5)
                
                try:
                    if np.ptp(U_s) > 0: ax2.contour(X_s, Y_s, U_s, levels=[0], colors=['red'], alpha=0.6, linewidths=2.0)
                    if np.ptp(V_s) > 0: ax2.contour(X_s, Y_s, V_s, levels=[0], colors=['blue'], alpha=0.6, linewidths=2.0)
                except Exception: pass

                for pt in puntos_criticos:
                    if -5 <= pt[0] <= 5 and -5 <= pt[1] <= 5:
                        ax1.plot(pt[0], pt[1], 'ro', markersize=8, markeredgecolor='black', zorder=5)
                        ax2.plot(pt[0], pt[1], 'ro', markersize=8, markeredgecolor='black', zorder=5)

                if str_A is not None:
                    try:
                        A_mat = parse_seguro(str_A, transformaciones=transf)
                        vecs = A_mat.eigenvects()
                        colores_vp = ['orange', 'cyan']
                        idx_c = 0
                        for val, mult, vectores in vecs:
                            if val.is_real: 
                                for v in vectores:
                                    try:
                                        vx, vy = float(v[0]), float(v[1])
                                        if vx != 0:
                                            m = vy / vx
                                            x_vals = np.linspace(-5, 5, 100)
                                            y_vals = m * x_vals
                                            ax2.plot(x_vals, y_vals, color=colores_vp[idx_c % 2], linestyle='--', linewidth=2.5, label=f"Eje Propio $\lambda={val}$")
                                        else:
                                            ax2.axvline(0, color=colores_vp[idx_c % 2], linestyle='--', linewidth=2.5, label=f"Eje Propio $\lambda={val}$")
                                        idx_c += 1
                                    except: pass 
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
                # FIGURA 3: PLANO CANÓNICO Y1-Y2
                # ==========================================
                fig3 = None
                if str_A is not None:
                    try:
                        A_mat = parse_seguro(str_A, transformaciones=transf)
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
                            
                            ax3.streamplot(X_c, Y_c, U_c, V_c, color=velocidad_c, cmap='plasma', linewidth=1.2, arrowsize=1.5, density=1.5)
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
                        st.write("Visualización del flujo continuo del sistema original. Si el sistema es lineal y posee vectores propios reales, estos se trazan como líneas punteadas, actuando como las asíntotas y directrices fundamentales del comportamiento geométrico.")
                
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
                            st.write(r"Este es el plano desacoplado $\dot{y} = \Lambda y$. Aquí los ejes representan directamente las direcciones de los vectores propios. La matriz $P$ aplica una transformación lineal que rota y estira este espacio para formar el retrato de fase original.")

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
            eq_parseada = parse_seguro(eq_str, transformaciones=transf, local_dict={'x': x, 'y': y, 'diff': sp.diff, 'exp': sp.exp, 'sin': sp.sin, 'cos': sp.cos})
            ecuacion_formal = sp.Eq(eq_parseada, 0)
            
            st.latex(sp.latex(ecuacion_formal))
            
            if usar_pvi:
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
