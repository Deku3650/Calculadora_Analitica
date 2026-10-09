import streamlit as st

def cargar_estilos_globales():
    st.markdown("""
        <style>
        /* Reescribir el color primario de Streamlit a azul */
        :root {
            --primary-color: #0284c7 !important;
            --stConfig-primaryColor: #0284c7 !important;
        }

        /* Cambiar el indicador de las pestañas activas */
        div[data-baseweb="tab-highlight"],
        div[data-baseweb="tab-border"],
        [aria-selected="true"] {
            background-color: #0284c7 !important;
            border-color: #0284c7 !important;
        }

        /* Texto de pestañas seleccionadas */
        button[data-baseweb="tab"][aria-selected="true"] p,
        button[data-baseweb="tab"][aria-selected="true"] span {
            color: #38bdf8 !important;
            font-weight: 800 !important;
        }
        </style>
    """, unsafe_allow_html=True)
