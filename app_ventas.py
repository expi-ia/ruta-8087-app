import streamlit as st
import pandas as pd
import openpyxl

# --- CONFIGURACIÓN VISUAL (ESTILO APP MÓVIL) ---
st.set_page_config(page_title="Ruta 8087", page_icon="🚛", layout="centered")

# CSS para forzar los colores de los cuadrados
st.markdown("""
    <style>
    /* Ocultar menú superior para ganar espacio */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilo de los Botones de Productos (Simulación de Cuadrados) */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
        height: 60px; /* Altura fija para parecer cuadrado */
        white-space: pre-wrap; /* Permitir dos líneas de texto */
        line-height: 1.2;
    }
    
    /* Colores Específicos */
    /* Nota: Streamlit limita los colores de botones, usamos hacks visuales */
    
    /* Cajas de estado (Verde y Azul) */
    .stAlert {
        padding: 10px;
        border-radius: 10px;
    }
    
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN ARCHIVO ---
FILE_PATH = 'Copia de LISTADO ACCIONES Q1.xlsx'

# --- 1. CARGA DE DATOS OPTIMIZADA ---
@st.cache_data
def load_data():
    try:
        all_sheets = pd.read_excel(FILE_PATH, sheet_name=None, engine='openpyxl')
        # Buscar hoja BITS
        sheet_found = next((k for k in all_sheets.keys() if 'BIT' in k.upper()), list(all_sheets.keys())[0])
        df = all_sheets[sheet_found]
        # Filtrar Ruta
        if 'Route' in df.columns:
            df = df[df['Route'] == 8087].copy()
        return df, sheet_found
    except Exception as e:
        return pd.DataFrame(), ""

# --- 2. GESTIÓN DE SESIÓN ---
if 'data' not in st.session_state:
    df_loaded, sheet_name = load_data()
    st.session_state.data = df_loaded
    st.session_state.sheet_name = sheet_name
    st.session_state.original = df_loaded.copy()
    st.session_state.current_client = None # Para saber si estamos en detalle

def save_data():
    """Guardado silencioso en segundo plano"""
    try:
        all_sheets = pd.read_excel(FILE_PATH, sheet_name=None, engine='openpyxl')
        df_full = all_sheets[st.session_state.sheet_name]
        df_act = st.session_state.data
        
        df_full.set_index('Customer Code', inplace=True)
        df_act.set_index('Customer Code', inplace=True)
        df_full.update(df_act)
        df_full.reset_index(inplace=True)
        df_act.reset_index(inplace=True)
        
        all_sheets[st.session_state.sheet_name] = df_full
        with pd.ExcelWriter(FILE_PATH, engine='openpyxl') as writer:
            for sheet, data in all_sheets.items():
                data.to_excel(writer, sheet_name=sheet, index=False)
    except:
        pass # Ignorar errores menores al guardar para no interrumpir

def vender_producto(code, col):
    # Buscar índice
    mask = st.session_state.data['Customer Code'] == code
    if mask.any():
        idx = st.session_state.data[mask].index[0]
        st.session_state.data.at[idx, col] = 1 # Marcar como 1
        save_data()
        st.rerun() # Recargar pantalla

def volver_inicio():
    st.session_state.current_client = None
    st.rerun()

# --- 3. INTERFAZ PRINCIPAL ---

# VISTA A: LISTADO (Optimizada para velocidad)
if st.session_state.current_client is None:
    st.title("🚛 Ruta 8087")
    
    # Buscador
    query = st.text_input("🔍 Buscar Cliente", placeholder="Escribe nombre...")
    
    df = st.session_state.data
    if query:
        # Filtrar
        mask = df['Customer Full Name'].str.contains(query, case=False, na=False) | \
               df['Customer Code'].astype(str).str.contains(query, na=False)
        df_filtered = df[mask]
    else:
        # TRUCO DE VELOCIDAD: Si no busca nada, solo mostramos los 5 primeros
        df_filtered = df.head(10)

    # Mostrar lista
    for idx, row in df_filtered.iterrows():
        # Tarjeta simple
        label = f"🏢 {row['Customer Full Name']}\n📍 {row['Address']}"
        if st.button(label, key=row['Customer Code']):
            st.session_state.current_client = row['Customer Code']
            st.rerun()
            
    if not query:
        st.caption("Escribe en el buscador para ver más clientes...")

# VISTA B: DETALLE DEL CLIENTE (Los Cuadrados)
else:
    # Botón Volver
    if st.button("⬅️ VOLVER A LA LISTA"):
        volver_inicio()
        
    code = st.session_state.current_client
    # Obtener datos frescos
    row = st.session_state.data[st.session_state.data['Customer Code'] == code].iloc[0]
    row_orig = st.session_state.original[st.session_state.original['Customer Code'] == code].iloc[0]
    
    st.header(row['Customer Full Name'])
    
    # Identificar productos
    prod_cols = [c for c in st.session_state.data.columns if 'Bits' in c]
    
    # Separar en listas
    faltan = []
    tienen_azul = [] # Vendido hoy
    tienen_verde = [] # Ya tenía
    
    for prod in prod_cols:
        val_actual = row[prod]
        val_orig = row_orig[prod]
        
        nombre_corto = prod.replace('Bits ', '').replace('0,50€', '0.5€')
        
        if val_actual == 0:
            faltan.append((prod, nombre_corto))
        elif val_actual == 1 and val_orig == 0:
            tienen_azul.append(nombre_corto)
        else:
            tienen_verde.append(nombre_corto)
            
    # --- SECCIÓN 1: FALTAN (BOTONES ROJOS) ---
    st.subheader("🔴 FALTAN (Pulsar para Vender)")
    if not faltan:
        st.success("¡Todo vendido! 🎉")
    else:
        # Rejilla de 2 columnas
        cols = st.columns(2)
        for i, (prod_full, prod_name) in enumerate(faltan):
            col_idx = i % 2
            with cols[col_idx]:
                # El botón es "primary" (rojo/destacado en Streamlit)
                if st.button(f"🛒 {prod_name}", key=f"btn_{prod_full}", type="primary", use_container_width=True):
                    vender_producto(code, prod_full)

    st.markdown("---")

    # --- SECCIÓN 2: LO QUE YA TIENE ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🔵 VENDIDO HOY")
        if tienen_azul:
            for item in tienen_azul:
                st.info(f"👍 {item}") # Azul
        else:
            st.caption("Nada vendido hoy")
            
    with c2:
        st.subheader("🟢 YA TENÍA")
        if tienen_verde:
            for item in tienen_verde:
                st.success(f"✅ {item}") # Verde
        else:
            st.caption("Inventario vacío")

