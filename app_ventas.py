import streamlit as st
import pandas as pd
import openpyxl

# --- CONFIGURACIÓN ESTÉTICA (LOOK & FEEL IPHONE) ---
st.set_page_config(page_title="Ruta 8087", page_icon="🚛", layout="centered")

# CSS para imitar la Simulación (Botones grandes, tarjetas limpias)
st.markdown("""
    <style>
    /* Ocultar elementos molestos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilo general */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
    }
    
    /* Tarjetas de Clientes */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        padding: 15px;
        text-align: left;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.2s;
    }
    
    /* Botón de VOLVER (más pequeño y simple) */
    div.row-widget.stButton > button[kind="secondary"] {
        border: none;
        background: none;
        color: #007aff;
        box-shadow: none;
        text-align: left;
        padding: 0;
    }
    
    /* Métricas estilo Dashboard */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #007aff;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN ARCHIVO ---
FILE_PATH = 'Copia de LISTADO ACCIONES Q1.xlsx'
HOJA_DATOS = 'BITS'

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    try:
        # Cargar Excel manteniendo todas las pestañas
        all_sheets = pd.read_excel(FILE_PATH, sheet_name=None, engine='openpyxl')
        
        # Buscar la hoja BITS
        sheet_found = next((k for k in all_sheets.keys() if 'BIT' in k.upper()), list(all_sheets.keys())[0])
        df = all_sheets[sheet_found]
        
        # Filtrar Ruta 8087
        if 'Route' in df.columns:
            df = df[df['Route'] == 8087].copy()
            
        return df, sheet_found
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), ""

# --- 2. GESTIÓN DE SESIÓN ---
if 'data' not in st.session_state:
    df_loaded, sheet_name = load_data()
    st.session_state.data = df_loaded
    st.session_state.sheet_name = sheet_name
    # Navegación: None = Lista, 'CODIGO' = Detalle Cliente
    st.session_state.current_view = None 

def save_data():
    """Guarda cambios en el Excel Real"""
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
    except Exception as e:
        st.error(f"Error guardando: {e}")

def toggle_producto(customer_code, col_name):
    """Cambia de 0 a 1 y guarda"""
    mask = st.session_state.data['Customer Code'] == customer_code
    if mask.any():
        idx = st.session_state.data[mask].index[0]
        # Si es 0 lo pone a 1 (Venta). Si ya es 1, no hace nada (o podríamos deshacer)
        current_val = st.session_state.data.at[idx, col_name]
        if current_val == 0:
            st.session_state.data.at[idx, col_name] = 1
            save_data()
            st.toast(f"✅ Venta registrada: {col_name}")

def ir_a_lista():
    st.session_state.current_view = None
    st.rerun()

def ir_a_detalle(code):
    st.session_state.current_view = code
    st.rerun()

# --- 3. INTERFAZ PRINCIPAL ---

# VISTA 1: LISTADO Y BUSCADOR (La "Home")
if st.session_state.current_view is None:
    st.subheader("🚛 Ruta 8087")
    
    # Dashboard Mini
    prod_cols = [c for c in st.session_state.data.columns if 'Bits' in c]
    total_ventas = st.session_state.data[prod_cols].sum().sum()
    st.metric("Productos Colocados", int(total_ventas))
    
    st.markdown("---")
    
    # Buscador Grande
    query = st.text_input("🔍 Buscar Cliente", placeholder="Nombre, calle o código...")
    
    # Filtrado
    df = st.session_state.data
    if query:
        mask = df['Customer Full Name'].str.contains(query, case=False, na=False) | \
               df['Address'].str.contains(query, case=False, na=False) | \
               df['Customer Code'].astype(str).str.contains(query, na=False)
        df_filtered = df[mask]
    else:
        df_filtered = df # Mostrar todos (o podríamos mostrar vacío para limpiar)

    # Lista de resultados como BOTONES (Clickable Rows)
    st.write(f"Encontrados: {len(df_filtered)}")
    
    # Limitamos a 20 para no saturar el móvil si no hay búsqueda
    for idx, row in df_filtered.head(20).iterrows():
        # Calculamos progreso para mostrarlo en la tarjeta
        hechos = row[prod_cols].sum()
        total = len(prod_cols)
        
        # El texto del botón simula la tarjeta
        texto_boton = f"""
        🏢 {row['Customer Full Name']}
        📍 {row['Address']}
        📊 {int(hechos)}/{total} productos
        """
        # Al pulsar, vamos al detalle
        if st.button(texto_boton, key=row['Customer Code']):
            ir_a_detalle(row['Customer Code'])

# VISTA 2: DETALLE DEL CLIENTE (Ficha Técnica)
else:
    # Botón Volver estilo iOS
    if st.button("← Volver a la lista", key="back", type="secondary"):
        ir_a_lista()

    # Datos del Cliente
    code = st.session_state.current_view
    cliente = st.session_state.data[st.session_state.data['Customer Code'] == code].iloc[0]
    prod_cols = [c for c in st.session_state.data.columns if 'Bits' in c]

    st.title(cliente['Customer Full Name'])
    st.caption(f"ID: {code} | {cliente['Address']}")
    
    st.markdown("### 🛒 Oportunidades (Faltan)")
    
    # Grid de productos faltantes
    faltan = [p for p in prod_cols if cliente[p] == 0]
    
    if not faltan:
        st.success("¡Este cliente tiene TODO! 🏆")
    else:
        for prod in faltan:
            # Botón ROJO grande para vender
            name = prod.replace('Bits ', '')
            if st.button(f"🔴 VENDER {name}", key=f"btn_{prod}", type="primary"):
                toggle_producto(code, prod)
                st.rerun() # Recargar para que desaparezca de la lista
                
    st.markdown("---")
    st.markdown("### ✅ En Tienda (Stock)")
    
    tiene = [p for p in prod_cols if cliente[p] == 1]
    # Mostramos estos como texto o botones desactivados/verdes
    if tiene:
        st.info("Ya tiene: " + ", ".join([p.replace('Bits ', '') for p in tiene]))

