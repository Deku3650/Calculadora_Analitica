import streamlit as st
import math
import numpy as np
import pandas as pd
from datetime import date

st.set_page_config(page_title="Matemáticas Financieras", layout="wide")

if 'mis_inversiones' not in st.session_state:
    st.session_state.mis_inversiones = {}

st.title("📈 Módulo de Matemáticas Financieras")
st.markdown("Análisis didáctico del valor del dinero en el tiempo, tablas de amortización y comparación de curvas.")

# Diccionario interno para capitalizaciones (m)
frecuencias_m = {
    "Anual": 1, "Semestral": 2, "Cuatrimestral": 3, "Trimestral": 4, 
    "Bimestral": 6, "Mensual": 12, "Quincenal": 24, "Semanal": 52, "Diaria": 360
}

tab_lab, tab_tasas, tab_fechas, tab_anualidades = st.tabs([
    "Laboratorio de Crecimiento (Simple vs Compuesto)", 
    "Tasas Equivalentes", 
    "Calculadora de Fechas", 
    "Anualidades y Amortización"
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: LABORATORIO DIDÁCTICO (Simple vs Compuesto)
# ------------------------------------------------------------------------------
with tab_lab:
    st.subheader("Configuración del Escenario Financiero")
    
    col_c, col_tasa, col_frec, col_t = st.columns(4)
    with col_c:
        tipo_interes = st.selectbox("Régimen de Interés:", ["Simple", "Compuesto"])
        C = st.number_input("Capital Inicial (C):", min_value=0.01, value=1000.0, step=100.0)
    with col_tasa:
        tasa_input = st.number_input("Tasa de Interés (%)", value=12.0, step=0.5)
    with col_frec:
        frec_str = st.selectbox("Frecuencia de la tasa:", 
                                ["Anual", "Semestral", "Trimestral", "Bimestral", "Mensual", "Diaria", "Continua", "Personalizada (Días)"])
        if frec_str == "Personalizada (Días)":
            dias_pers = st.number_input("¿Cada cuántos días?", min_value=1, value=28)
            m = 360 / dias_pers
        else:
            m = frecuencias_m.get(frec_str, 1) # Si es continua, usaremos otra lógica matemática
    with col_t:
        t_anios = st.number_input("Tiempo de Inversión (Años):", min_value=0.1, value=5.0, step=1.0)

    # Lógica Matemática Didáctica
    i_decimal = tasa_input / 100
    
    st.divider()
    col_res, col_graf = st.columns([1, 2])
    
    with col_res:
        st.write("### Desglose Analítico")
        
        # 1. Mostrar la tasa adaptada didácticamente
        if frec_str == "Continua":
            st.info("💡 **Capitalización Continua:** El interés se reinvierte en cada instante infinito. Usamos la constante de Euler ($e$).")
            M_final = C * math.exp(i_decimal * t_anios)
            formula_usada = r"M = C e^{it}"
        else:
            tasa_por_periodo = i_decimal / m
            periodos_totales = t_anios * m
            if tipo_interes == "Simple":
                st.info(f"💡 **Interés Simple:** La tasa del {tasa_input}% {frec_str} no se reinvierte. Solo el capital base genera intereses.")
                M_final = C * (1 + (i_decimal * t_anios))
                formula_usada = r"M = C(1 + it)"
            else:
                st.info(f"💡 **Interés Compuesto:** Tasa equivalente de **{tasa_por_periodo*100:.4f}%** aplicada durante **{periodos_totales:,.2f}** periodos. Los intereses generan más intereses.")
                M_final = C * (1 + tasa_por_periodo)**periodos_totales
                formula_usada = r"M = C \left(1 + \frac{j}{m}\right)^{mt}"

        st.metric("Monto Final Proyectado (M)", f"${M_final:,.2f}", delta=f"+ ${M_final - C:,.2f} de ganancia")
        st.latex(formula_usada)
        
        # 2. Generación de Tabla de Evolución
        if st.checkbox("Ver tabla de evolución periodo a periodo"):
            if frec_str == "Continua":
                st.warning("La tabla por periodos discretos no está definida para tiempo continuo.")
            else:
                n_int = int(periodos_totales)
                tabla = []
                saldo = C
                for k in range(1, min(n_int + 1, 121)): # Limitamos a 120 meses visuales para no trabar el navegador
                    if tipo_interes == "Simple":
                        int_gen = C * tasa_por_periodo
                        saldo += int_gen
                    else:
                        int_gen = saldo * tasa_por_periodo
                        saldo += int_gen
                    tabla.append({"Periodo": k, "Interés Generado": round(int_gen, 2), "Monto Acumulado": round(saldo, 2)})
                
                df_tabla = pd.DataFrame(tabla)
                st.dataframe(df_tabla, use_container_width=True, hide_index=True)
                if n_int > 120: st.caption("Mostrando solo los primeros 120 periodos por rendimiento visual.")

    with col_graf:
        st.write("### Comparador de Escenarios")
        
        # Guardar en memoria
        with st.form("form_guardar_escenario"):
            c_nom, c_btn = st.columns([3, 1])
            with c_nom: nom_escenario = st.text_input("Nombre para guardar este escenario en la gráfica:", value=f"{tipo_interes} al {tasa_input}%")
            with c_btn: 
                st.write("")
                if st.form_submit_button("💾 Guardar"):
                    st.session_state.mis_inversiones[nom_escenario] = {
                        "C": C, "tipo": tipo_interes, "i": i_decimal, "frec": frec_str, "m": m, "t": t_anios
                    }
                    st.rerun()
                    
        # Generar Gráfica Múltiple
        if st.session_state.mis_inversiones:
            st.write("**Curvas de Crecimiento en el Tiempo**")
            
            # Buscamos el horizonte de tiempo máximo entre los guardados
            t_max_graf = max([datos['t'] for datos in st.session_state.mis_inversiones.values()])
            
            # Creamos un vector de tiempo suave (x-axis)
            t_vector = np.linspace(0, t_max_graf, 100)
            df_graf = pd.DataFrame({"Años": t_vector}).set_index("Años")
            
            for nombre, datos in st.session_state.mis_inversiones.items():
                v_C = datos['C']; v_i = datos['i']; v_m = datos['m']; v_tipo = datos['tipo']; v_frec = datos['frec']
                
                if v_frec == "Continua":
                    if v_tipo == "Simple": curva = v_C * (1 + v_i * t_vector)
                    else: curva = v_C * np.exp(v_i * t_vector)
                else:
                    if v_tipo == "Simple": curva = v_C * (1 + v_i * t_vector)
                    else: curva = v_C * (1 + v_i/v_m)**(v_m * t_vector)
                    
                df_graf[nombre] = curva
                
            st.line_chart(df_graf)
            
            if st.button("🗑️ Limpiar Gráfica"):
                st.session_state.mis_inversiones.clear()
                st.rerun()
        else:
            st.info("Guarde un escenario arriba para comenzar a graficar y comparar.")

# ------------------------------------------------------------------------------
# PESTAÑA 2: TASAS EQUIVALENTES
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
        dias_exactos = (fecha_fin - fecha_inicio).days
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
# PESTAÑA 4: ANUALIDADES Y AMORTIZACIÓN
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
            VP = R * n_per; M = R * n_per
        else:
            VP = R * ((1 - (1 + i_an)**(-n_per)) / i_an)
            M = R * (((1 + i_an)**n_per - 1) / i_an)
            if tipo_anualidad == "Anticipada":
                VP = VP * (1 + i_an); M = M * (1 + i_an)
                
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
