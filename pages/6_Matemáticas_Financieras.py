import streamlit as st
import math
from datetime import date

st.set_page_config(page_title="Matemáticas Financieras", layout="wide")

st.title("📈 Módulo de Matemáticas Financieras")
st.markdown("Herramientas de valuación, tasas equivalentes y valor del dinero en el tiempo.")

# ==============================================================================
# PESTAÑAS DEL MÓDULO
# ==============================================================================
tab_interes, tab_tasas, tab_fechas, tab_anualidades = st.tabs([
    "Interés Simple y Compuesto", 
    "Tasas Equivalentes", 
    "Calculadora de Fechas", 
    "Anualidades"
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: INTERÉS SIMPLE Y COMPUESTO
# ------------------------------------------------------------------------------
with tab_interes:
    st.subheader("Valor del Dinero en el Tiempo")
    
    col_tipo, col_var = st.columns(2)
    with col_tipo:
        tipo_interes = st.radio("Régimen de Interés:", ["Simple", "Compuesto"], horizontal=True)
    with col_var:
        variable_calc = st.selectbox("¿Qué desea calcular?", ["Monto Final (M)", "Capital Inicial (C)", "Tasa de Interés (i)", "Tiempo (t)"])
        
    st.divider()
    
    with st.form("form_interes"):
        c1, c2, c3 = st.columns(3)
        
        # Entradas dinámicas dependiendo de lo que se va a calcular
        if variable_calc != "Monto Final (M)":
            with c1: M_val = st.number_input("Monto Final (M):", min_value=0.01, value=1500.0, step=100.0)
        if variable_calc != "Capital Inicial (C)":
            with c1 if variable_calc == "Monto Final (M)" else c2: 
                C_val = st.number_input("Capital Inicial (C):", min_value=0.01, value=1000.0, step=100.0)
        if variable_calc != "Tasa de Interés (i)":
            col_tasa = c2 if variable_calc in ["Monto Final (M)", "Capital Inicial (C)"] else c3
            with col_tasa: 
                i_val_porc = st.number_input("Tasa de Interés (i) en %:", value=10.0, step=0.5)
                i_val = i_val_porc / 100
        if variable_calc != "Tiempo (t)":
            with c3: t_val = st.number_input("Tiempo / Periodos (t):", min_value=0.01, value=1.0, step=1.0)
            
        calcular_btn = st.form_submit_button(f"Calcular {variable_calc.split(' ')[0]}")
        
    if calcular_btn:
        res = 0.0
        formula = ""
        
        try:
            if tipo_interes == "Simple":
                if variable_calc == "Monto Final (M)":
                    res = C_val * (1 + i_val * t_val)
                    formula = r"M = C(1 + it)"
                elif variable_calc == "Capital Inicial (C)":
                    res = M_val / (1 + i_val * t_val)
                    formula = r"C = \frac{M}{1 + it}"
                elif variable_calc == "Tasa de Interés (i)":
                    res = ((M_val / C_val) - 1) / t_val
                    formula = r"i = \frac{\frac{M}{C} - 1}{t}"
                elif variable_calc == "Tiempo (t)":
                    res = ((M_val / C_val) - 1) / i_val
                    formula = r"t = \frac{\frac{M}{C} - 1}{i}"
                    
            elif tipo_interes == "Compuesto":
                if variable_calc == "Monto Final (M)":
                    res = C_val * (1 + i_val)**t_val
                    formula = r"M = C(1 + i)^t"
                elif variable_calc == "Capital Inicial (C)":
                    res = M_val / (1 + i_val)**t_val
                    formula = r"C = \frac{M}{(1 + i)^t}"
                elif variable_calc == "Tasa de Interés (i)":
                    res = (M_val / C_val)**(1 / t_val) - 1
                    formula = r"i = \left(\frac{M}{C}\right)^{\frac{1}{t}} - 1"
                elif variable_calc == "Tiempo (t)":
                    res = math.log(M_val / C_val) / math.log(1 + i_val)
                    formula = r"t = \frac{\ln(M/C)}{\ln(1+i)}"

            # Formateo visual del resultado
            st.success("Cálculo realizado con éxito.")
            col_res1, col_res2 = st.columns([1, 2])
            with col_res1:
                if variable_calc == "Tasa de Interés (i)":
                    st.metric(label=variable_calc, value=f"{res*100:,.4f} %")
                elif variable_calc == "Tiempo (t)":
                    st.metric(label=variable_calc, value=f"{res:,.4f} periodos")
                else:
                    st.metric(label=variable_calc, value=f"${res:,.2f}")
            with col_res2:
                st.write("**Fórmula aplicada:**")
                st.latex(formula)
                
        except Exception as e:
            st.error("Error matemático. Verifique que el Capital Inicial sea menor al Monto Final.")

# ------------------------------------------------------------------------------
# PESTAÑA 2: TASAS EQUIVALENTES Y DESCUENTO
# ------------------------------------------------------------------------------
with tab_tasas:
    st.subheader("Conversión y Equivalencia de Tasas")
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("**1. Tasa Efectiva $\\leftrightarrow$ Nominal**")
        st.info("💡 Convierte entre tasa efectiva anual ($i$) y tasa nominal ($j$) capitalizable $m$ veces al año.")
        
        modo_nom_efec = st.radio("Conversión:", ["De Nominal a Efectiva", "De Efectiva a Nominal"], horizontal=True)
        m_capitalizaciones = st.number_input("Frecuencia de capitalización ($m$):", min_value=1, value=12, help="Ej. 12 para mensual, 4 para trimestral.")
        
        if modo_nom_efec == "De Nominal a Efectiva":
            j_tasa = st.number_input("Tasa Nominal ($j$) en %:", value=12.0) / 100
            if st.button("Calcular Tasa Efectiva"):
                i_efec = (1 + j_tasa / m_capitalizaciones)**m_capitalizaciones - 1
                st.latex(r"i = \left(1 + \frac{j}{m}\right)^m - 1")
                st.metric("Tasa Efectiva ($i$)", f"{i_efec*100:,.4f} %")
        else:
            i_tasa = st.number_input("Tasa Efectiva ($i$) en %:", value=12.68) / 100
            if st.button("Calcular Tasa Nominal"):
                j_nom = m_capitalizaciones * ((1 + i_tasa)**(1 / m_capitalizaciones) - 1)
                st.latex(r"j = m \left[ (1 + i)^{\frac{1}{m}} - 1 \right]")
                st.metric("Tasa Nominal ($j$)", f"{j_nom*100:,.4f} %")

    with col_t2:
        st.markdown("**2. Tasa de Interés ($i$) $\\leftrightarrow$ Tasa de Descuento ($d$)**")
        st.info("💡 Herramienta clave para valuación de CETES y matemáticas actuariales.")
        
        modo_int_desc = st.radio("Conversión:", ["De Interés a Descuento", "De Descuento a Interés"], horizontal=True)
        
        if modo_int_desc == "De Interés a Descuento":
            tasa_i = st.number_input("Tasa de Interés vencida ($i$) en %:", value=10.0, key="tasa_i") / 100
            if st.button("Calcular Tasa de Descuento"):
                tasa_d = tasa_i / (1 + tasa_i)
                st.latex(r"d = \frac{i}{1+i}")
                st.metric("Tasa de Descuento anticipada ($d$)", f"{tasa_d*100:,.4f} %")
        else:
            tasa_d2 = st.number_input("Tasa de Descuento anticipada ($d$) en %:", value=9.09, key="tasa_d") / 100
            if st.button("Calcular Tasa de Interés"):
                if tasa_d2 >= 1:
                    st.error("La tasa de descuento no puede ser del 100% o superior.")
                else:
                    tasa_i2 = tasa_d2 / (1 - tasa_d2)
                    st.latex(r"i = \frac{d}{1-d}")
                    st.metric("Tasa de Interés vencida ($i$)", f"{tasa_i2*100:,.4f} %")

# ------------------------------------------------------------------------------
# PESTAÑA 3: CALCULADORA DE FECHAS
# ------------------------------------------------------------------------------
with tab_fechas:
    st.subheader("Cálculo de Plazos (Bases Actuariales)")
    
    c_f1, c_f2 = st.columns(2)
    with c_f1: fecha_inicio = st.date_input("Fecha Inicial:", value=date(2026, 1, 1))
    with c_f2: fecha_fin = st.date_input("Fecha Final:", value=date(2026, 12, 31))
    
    if fecha_inicio > fecha_fin:
        st.error("La Fecha Inicial debe ser menor o igual a la Fecha Final.")
    else:
        # Cálculo Actual/Actual (Días exactos)
        dias_exactos = (fecha_fin - fecha_inicio).days
        
        # Cálculo 30/360 (Convención comercial/bancaria)
        dias_360 = (fecha_fin.year - fecha_inicio.year) * 360 + \
                   (fecha_fin.month - fecha_inicio.month) * 30 + \
                   (fecha_fin.day - fecha_inicio.day)
                   
        st.write("")
        col_res_f1, col_res_f2 = st.columns(2)
        with col_res_f1:
            st.metric("Días Exactos (Actual/Actual)", dias_exactos)
            st.caption(f"Equivale a **{dias_exactos/365:,.4f}** años (Base 365)")
        with col_res_f2:
            st.metric("Días Comerciales (Método 30/360)", dias_360)
            st.caption(f"Equivale a **{dias_360/360:,.4f}** años (Base 360)")

# ------------------------------------------------------------------------------
# PESTAÑA 4: ANUALIDADES
# ------------------------------------------------------------------------------
with tab_anualidades:
    st.subheader("Valuación de Anualidades Ciertas")
    st.markdown("Cálculo del Valor Presente ($VP$) y Monto Futuro ($M$) de flujos de efectivo constantes.")
    
    tipo_anualidad = st.radio("Tipo de Anualidad:", ["Vencida (Ordinaria)", "Anticipada"], horizontal=True)
    
    with st.form("form_anualidad"):
        ca1, ca2, ca3 = st.columns(3)
        with ca1: R = st.number_input("Pago periódico (Renta):", min_value=0.01, value=1000.0, step=100.0)
        with ca2: i_an = st.number_input("Tasa de interés por periodo (%)", value=5.0) / 100
        with ca3: n_per = st.number_input("Número de periodos (n):", min_value=1, value=12, step=1)
        
        submit_anualidad = st.form_submit_button("Valuar Anualidad")
        
    if submit_anualidad:
        if i_an == 0:
            VP = R * n_per
            M = R * n_per
        else:
            # Fórmulas Anualidad Vencida
            VP = R * ((1 - (1 + i_an)**(-n_per)) / i_an)
            M = R * (((1 + i_an)**n_per - 1) / i_an)
            
            # Ajuste si es Anticipada
            if tipo_anualidad == "Anticipada":
                VP = VP * (1 + i_an)
                M = M * (1 + i_an)
                
        st.success(f"Valuación completada ({tipo_anualidad}).")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Valor Presente (VP)", f"${VP:,.2f}")
            formula_vp = r"VP = R \left[ \frac{1 - (1+i)^{-n}}{i} \right]"
            if tipo_anualidad == "Anticipada": formula_vp += r"(1+i)"
            st.latex(formula_vp)
        with col_m2:
            st.metric("Monto Futuro (M)", f"${M:,.2f}")
            formula_m = r"M = R \left[ \frac{(1+i)^n - 1}{i} \right]"
            if tipo_anualidad == "Anticipada": formula_m += r"(1+i)"
            st.latex(formula_m)
