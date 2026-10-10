import streamlit as st
import numpy as np
import pandas as pd

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Economía y Microeconomía - MATHESIS", page_icon="📊", layout="wide")

# ==============================================================================
# INYECCIÓN DIRECTA DE CSS (ESTILOS UNIFICADOS Y LIMPIOS DE MATHESIS)
# ==============================================================================
st.markdown("""
    <style>
    /* 1. VISIBILIDAD DE MENÚ SUPERIOR */
    #MainMenu { visibility: visible !important; }
    footer { visibility: hidden; }
    .block-container { padding-top: 1.5rem; }

    /* 2. VARIABLES GLOBALES DE TEMA EN AZUL */
    :root, html, body, [data-testid="stAppViewContainer"] {
        --primary-color: #0284c7 !important;
        --stConfig-primaryColor: #0284c7 !important;
    }

    /* 3. BANNER PRINCIPAL */
    .title-container {
        padding: 1.2rem 1.5rem;
        border-radius: 16px;
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.18) 0%, rgba(79, 70, 229, 0.18) 100%);
        border: 1px solid rgba(56, 189, 248, 0.35);
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(2, 132, 199, 0.12);
    }
    
    .title-text {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0284c7 0%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }

    /* 4. ESTILIZADO GLOBAL PARA SUBTÍTULOS (H2, H3, ST.HEADER, ST.SUBHEADER) */
    .stMarkdown h2, [data-testid="stHeader"] h2 {
        color: #38bdf8 !important;
        font-size: 1.35rem !important;
        font-weight: 800 !important;
        border-bottom: 2px solid rgba(56, 189, 248, 0.3) !important;
        padding-bottom: 6px !important;
        margin-top: 1.2rem !important;
        margin-bottom: 1.0rem !important;
        letter-spacing: -0.3px !important;
    }

    .stMarkdown h3, [data-testid="stSubheader"] h3 {
        color: #38bdf8 !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        border-left: 4px solid #0284c7 !important;
        padding-left: 10px !important;
        margin-top: 1rem !important;
        margin-bottom: 0.8rem !important;
    }

    /* 5. CONTENEDORES NATIVOS AZULES (ELIMINA RECUADROS FANTASMA) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.35) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 15px rgba(2, 132, 199, 0.08) !important;
        margin-bottom: 1rem !important;
    }

    /* 6. TÍTULOS Y SUBTÍTULOS RESALTADOS DENTRO DE LAS TARJETAS */
    .card-header-title {
        background: linear-gradient(135deg, #0284c7 0%, #6366f1 100%);
        color: #ffffff !important;
        font-size: 17px;
        font-weight: 800;
        padding: 8px 16px;
        border-radius: 10px;
        display: inline-block;
        margin-bottom: 14px;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
    }

    .card-subheader-title {
        color: #38bdf8 !important;
        font-size: 15px;
        font-weight: 700;
        border-bottom: 2px solid rgba(56, 189, 248, 0.3);
        padding-bottom: 6px;
        margin-top: 10px;
        margin-bottom: 12px;
    }

    /* 7. DISEÑO MODERNO DE PESTAÑAS (ST.TABS) */
    [data-baseweb="tab-list"] {
        gap: 10px !important;
        background-color: rgba(2, 132, 199, 0.05) !important;
        padding: 8px 10px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        margin-bottom: 20px !important;
    }

    button[data-baseweb="tab"] {
        border-radius: 12px !important;
        padding: 10px 22px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        color: #94a3b8 !important;
        background-color: transparent !important;
        border: 1px solid transparent !important;
        transition: all 0.25s ease-in-out !important;
    }

    button[data-baseweb="tab"]:hover {
        color: #38bdf8 !important;
        background: rgba(2, 132, 199, 0.12) !important;
        border: 1px solid rgba(56, 189, 248, 0.25) !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
        background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%) !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35) !important;
        border: 1px solid #38bdf8 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* 8. ESTILOS DE BARRA LATERAL (SIDEBAR UNIFICADO) */
    [data-testid="stSidebar"], section[data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 320px !important;
        border-right: 1px solid rgba(2, 132, 199, 0.2) !important;
    }

    [data-testid="stSidebarNav"] ul li div a, [data-testid="stSidebarNav"] a {
        border-radius: 12px !important;
        padding: 10px 14px !important;
        margin: 4px 8px !important;
        border: 1px solid rgba(2, 132, 199, 0.18) !important;
        background-color: rgba(2, 132, 199, 0.03) !important;
        transition: all 0.25s ease-in-out !important;
        white-space: nowrap !important;
    }

    [data-testid="stSidebarNav"] ul li div a:hover, [data-testid="stSidebarNav"] a:hover {
        border-color: #0284c7 !important;
        background: rgba(2, 132, 199, 0.12) !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2) !important;
        transform: translateX(4px);
    }

    [data-testid="stSidebarNav"] ul li div a[aria-current="page"], [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.25) 0%, rgba(79, 70, 229, 0.25) 100%) !important;
        border: 1px solid #38bdf8 !important;
        box-shadow: 0 4px 14px rgba(56, 189, 248, 0.25) !important;
    }

    [data-testid="stSidebarNav"] ul li div a[aria-current="page"] span, [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# ENCABEZADO CON BANNER ESTILIZADO
# ==============================================================================
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">📊 Economía y Microeconomía</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("Herramientas analíticas para equilibrio de mercado, elasticidades y restricción presupuestaria.")

tab_eq, tab_elas, tab_pres = st.tabs([
    "1. Equilibrio de Mercado (S = D)", 
    "2. Elasticidad Precio", 
    "3. Restricción Presupuestaria"
])

# ==============================================================================
# PESTAÑA 1: EQUILIBRIO DE MERCADO
# ==============================================================================
with tab_eq:
    with st.container(border=True):
        st.markdown('<div class="card-header-title">Análisis de Oferta y Demanda Lineal</div>', unsafe_allow_html=True)
        st.info(r"💡 *Ingrese los coeficientes de las ecuaciones de Oferta ($Q_s = c + dP$) y Demanda ($Q_d = a - bP$).*")
        
        with st.form("form_equilibrio"):
            st.markdown('<div class="card-subheader-title">📉 Ecuación de Demanda: $Q_d = a - bP$</div>', unsafe_allow_html=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1: a_dem = st.number_input("Intercepto Demanda ($a$):", value=20900.0, step=100.0)
            with col_d2: b_dem = st.number_input("Pendiente Demanda ($b$):", value=100.0, step=10.0)
            
            st.markdown('<div class="card-subheader-title">📈 Ecuación de Oferta: $Q_s = c + dP$</div>', unsafe_allow_html=True)
            col_o1, col_o2 = st.columns(2)
            with col_o1: c_of = st.number_input("Intercepto Oferta ($c$):", value=-100.0, step=10.0)
            with col_o2: d_of = st.number_input("Pendiente Oferta ($d$):", value=50.0, step=10.0)
            
            st.divider()
            p_eval = st.number_input("Precio específico a evaluar (Exceso de oferta/demanda):", value=100.0, step=10.0)
            
            submit_eq = st.form_submit_button("Calcular Equilibrio y Graficar", use_container_width=True)
            
        if submit_eq:
            try:
                if (b_dem + d_of) == 0:
                    raise ValueError("Las pendientes no pueden sumar cero (rectas paralelas).")
                    
                p_eq = (a_dem - c_of) / (b_dem + d_of)
                q_eq = a_dem - (b_dem * p_eq)
                
                if p_eq < 0 or q_eq < 0:
                    st.warning("Advertencia: El punto de equilibrio matemático arroja precios o cantidades negativas. Revise los coeficientes.")
                
                st.success("¡Equilibrio calculado exitosamente!")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.metric("Precio de Equilibrio ($P^*$)", f"${p_eq:,.2f}")
                with col_r2:
                    st.metric("Cantidad de Equilibrio ($Q^*$)", f"{q_eq:,.2f} unidades")
                    
                st.latex(r"Q_d = Q_s \implies a - bP = c + dP \implies P^* = \frac{a - c}{b + d}")
                
                qd_eval = a_dem - (b_dem * p_eval)
                qs_eval = c_of + (d_of * p_eval)
                diferencia = qs_eval - qd_eval
                
                st.markdown(f'<div class="card-subheader-title">Análisis al Precio de Prueba: ${p_eval:,.2f}</div>', unsafe_allow_html=True)
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1: st.metric("Cantidad Demandada", f"{qd_eval:,.2f}")
                with col_e2: st.metric("Cantidad Ofrecida", f"{qs_eval:,.2f}")
                with col_e3: 
                    if diferencia > 0:
                        st.metric("Situación", "Exceso de Oferta", f"{diferencia:,.2f}")
                    elif diferencia < 0:
                        st.metric("Situación", "Exceso de Demanda", f"{abs(diferencia):,.2f}")
                    else:
                        st.metric("Situación", "Mercado en Equilibrio", "0.00")

                st.markdown('<div class="card-subheader-title">📊 Gráfica de Equilibrio de Mercado</div>', unsafe_allow_html=True)
                p_min = max(0.0, p_eq * 0.2)
                p_max = p_eq * 1.8 if p_eq > 0 else 200.0
                p_vector = np.linspace(p_min, p_max, 100)
                
                q_dem_vector = a_dem - (b_dem * p_vector)
                q_of_vector = c_of + (d_of * p_vector)
                
                df_mercado = pd.DataFrame({
                    "Precio (P)": p_vector,
                    "Demanda (Qd)": np.where(q_dem_vector >= 0, q_dem_vector, np.nan),
                    "Oferta (Qs)": np.where(q_of_vector >= 0, q_of_vector, np.nan)
                }).set_index("Precio (P)")
                
                st.line_chart(df_mercado)
                
            except ValueError as ve:
                st.error(f"Error en el cálculo: {ve}")

# ==============================================================================
# PESTAÑA 2: ELASTICIDAD PRECIO
# ==============================================================================
with tab_elas:
    with st.container(border=True):
        st.markdown('<div class="card-header-title">Calculadora de Elasticidad Precio (Método del Punto Medio / Arco)</div>', unsafe_allow_html=True)
        
        with st.form("form_elasticidad"):
            c_el1, c_el2 = st.columns(2)
            with c_el1:
                st.write("**Punto Inicial**")
                p1 = st.number_input("Precio Inicial ($P_1$):", min_value=0.01, value=10.0, step=1.0)
                q1 = st.number_input("Cantidad Inicial ($Q_1$):", min_value=0.01, value=100.0, step=5.0)
            with c_el2:
                st.write("**Punto Final**")
                p2 = st.number_input("Precio Final ($P_2$):", min_value=0.01, value=12.0, step=1.0)
                q2 = st.number_input("Cantidad Final ($Q_2$):", min_value=0.01, value=80.0, step=5.0)
                
            submit_elas = st.form_submit_button("Calcular Elasticidad", use_container_width=True)
            
        if submit_elas:
            delta_q = q2 - q1
            delta_p = p2 - p1
            prom_q = (q1 + q2) / 2
            prom_p = (p1 + p2) / 2
            
            if prom_q == 0 or prom_p == 0 or delta_p == 0:
                st.error("Error matemático: división por cero o cambio de precio nulo.")
            else:
                ep = (delta_q / prom_q) / (delta_p / prom_p)
                ep_abs = abs(ep)
                
                if ep_abs > 1:
                    tipo_elas = "Elástica ($E > 1$)"
                    interp_elas = "Los consumidores son muy sensibles al cambio de precio. Una subida de precio reduce drásticamente los ingresos totales."
                elif ep_abs < 1:
                    tipo_elas = "Inelástica ($E < 1$)"
                    interp_elas = "Los consumidores son poco sensibles al cambio de precio (bienes de primera necesidad). Una subida de precio aumenta los ingresos totales."
                else:
                    tipo_elas = "Elasticidad Unitaria ($E = 1$)"
                    interp_elas = "El cambio porcentual en la cantidad es exactamente igual al cambio porcentual en el precio."
                    
                st.success("Cálculo de elasticidad completado.")
                col_er1, col_er2 = st.columns([1, 1.5])
                with col_er1:
                    st.metric("Elasticidad Precio ($|E|$)", f"{ep_abs:,.4f}")
                    st.write(f"**Clasificación:** {tipo_elas}")
                with col_er2:
                    st.write("**Interpretación:**")
                    st.info(interp_elas)
                    st.write("**Fórmula aplicada (Arco):**")
                    st.latex(r"E = \frac{\frac{Q_2 - Q_1}{(Q_1 + Q_2)/2}}{\frac{P_2 - P_1}{(P_1 + P_2)/2}}")

# ==============================================================================
# PESTAÑA 3: RESTRICCIÓN PRESUPUESTARIA
# ==============================================================================
with tab_pres:
    with st.container(border=True):
        st.markdown('<div class="card-header-title">Conjunto Asequible y Línea de Presupuesto</div>', unsafe_allow_html=True)
        st.info(r"💡 *Analiza las combinaciones máximas de consumo de dos bienes dados tu ingreso y sus precios.*")
        
        with st.form("form_presupuesto"):
            cp1, cp2, cp3 = st.columns(3)
            with cp1: ingreso_m = st.number_input("Ingreso Total ($m$):", min_value=1.0, value=1000.0, step=100.0)
            with cp2: p_bien1 = st.number_input("Precio del Bien 1 ($P_1$):", min_value=0.01, value=50.0, step=5.0)
            with cp3: p_bien2 = st.number_input("Precio del Bien 2 ($P_2$):", min_value=0.01, value=20.0, step=2.0)
            
            submit_pres = st.form_submit_button("Calcular y Graficar Recta Presupuestaria", use_container_width=True)
            
        if submit_pres:
            max_b1 = ingreso_m / p_bien1
            max_b2 = ingreso_m / p_bien2
            
            st.success("Valuación presupuestaria completada.")
            col_pr1, col_pr2 = st.columns(2)
            with col_pr1:
                st.metric("Consumo Máximo Bien 1 ($m / P_1$)", f"{max_b1:,.2f} unidades")
            with col_pr2:
                st.metric("Consumo Máximo Bien 2 ($m / P_2$)", f"{max_b2:,.2f} unidades")
                
            st.latex(r"P_1X_1 + P_2X_2 = m \implies X_2 = \frac{m}{P_2} - \frac{P_1}{P_2}X_1")
            
            st.markdown('<div class="card-subheader-title">📈 Línea de Restricción Presupuestaria</div>', unsafe_allow_html=True)
            x1_vector = np.linspace(0, max_b1, 100)
            x2_vector = (ingreso_m - (p_bien1 * x1_vector)) / p_bien2
            
            df_presupuesto = pd.DataFrame({
                "Bien 1 (X1)": x1_vector,
                "Bien 2 (X2)": np.where(x2_vector >= 0, x2_vector, 0)
            }).set_index("Bien 1 (X1)")
            
            st.line_chart(df_presupuesto)
