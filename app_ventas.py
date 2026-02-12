import streamlit as st
import pandas as pd
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestor Ruta 8087", page_icon="🚛", layout="wide")

# Estilos CSS
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; }
    .status-badge { padding: 5px 10px; border-radius: 5px; color: white; font-weight: bold; text-align: center; }
    .red-bg { background-color: #ff4b4b; }
    .green-bg { background-color: #28a745; }
    .blue-bg { background-color: #29b5e8; }
    .client-card { padding: 10px; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 10px; background-color: #f9f9f9; }
    .progress-text { font-weight: bold; color: #555; }
    </style>
""", unsafe_allow_html=True)

# --- 1. CARGA DE DATOS ---
FILE_PATH = 'Copia de LISTADO ACCIONES Q1.xlsx - BITS.csv'

@st.cache_data
def load_data():
    df = pd.read_csv(FILE_PATH)
    # Filtrar solo ruta 8087
    df = df[df['Route'] == 8087].copy()
    return df

# --- 2. GESTIÓN DEL ESTADO ---
if 'data' not in st.session_state:
    st.session_state.data = load_data()
    st.session_state.original = st.session_state.data.copy()

def save_data():
    """Guarda los cambios en el CSV original"""
    # Primero leemos el CSV completo original para no perder las otras rutas
    df_full = pd.read_csv(FILE_PATH)
    
    # Actualizamos solo las filas de nuestra ruta modificada
    df_8087_actual = st.session_state.data
    
    # Usamos el Customer Code como índice para actualizar seguro
    df_full.set_index('Customer Code', inplace=True)
    df_8087_actual.set_index('Customer Code', inplace=True)
    
    df_full.update(df_8087_actual)
    
    # Reseteamos índice y guardamos
    df_full.reset_index(inplace=True)
    df_8087_actual.reset_index(inplace=True) # Restaurar estado sesión
    
    df_full.to_csv(FILE_PATH, index=False)
    st.toast("✅ ¡Cambios guardados en el archivo original!")

def registrar_venta(customer_code, col_name):
    """Marca venta y guarda"""
    # Buscar índice en el dataframe de sesión
    idx = st.session_state.data[st.session_state.data['Customer Code'] == customer_code].index[0]
    
    # Actualizar valor a 1
    st.session_state.data.at[idx, col_name] = 1
    
    # Guardar en disco
    save_data()
    st.rerun()

# --- 3. INTERFAZ ---
st.title("🚛 Ruta 8087 - Gestor Pro")

# Identificar columnas de productos
prod_cols = [c for c in st.session_state.data.columns if 'Bits' in c]
total_refs = len(prod_cols)

# --- PANEL LATERAL: LISTADO DE CLIENTES ---
with st.sidebar:
    st.header("🔍 Clientes")
    search = st.text_input("Buscar (Nombre o Código)...", placeholder="Ej: 714492 o Lara")
    
    # Filtrado
    df_display = st.session_state.data
    if search:
        mask = df_display['Customer Full Name'].str.contains(search, case=False, na=False) | \
               df_display['Customer Code'].astype(str).str.contains(search, na=False)
        df_display = df_display[mask]
    
    # Selector de cliente
    # Creamos una lista formateada: "NOMBRE (CÓDIGO) [PROGRESO]"
    opciones = []
    mapa_clientes = {}
    
    for idx, row in df_display.iterrows():
        # Calcular progreso
        comprados = row[prod_cols].sum()
        progreso = f"{int(comprados)}/{total_refs}"
        
        label = f"{row['Customer Full Name']} ({row['Customer Code']}) [{progreso}]"
        opciones.append(label)
        mapa_clientes[label] = row['Customer Code']
    
    seleccion = st.radio("Selecciona un cliente:", opciones)

# --- ÁREA PRINCIPAL ---
if seleccion:
    codigo_cliente = mapa_clientes[seleccion]
    cliente = st.session_state.data[st.session_state.data['Customer Code'] == codigo_cliente].iloc[0]
    
    # Cabecera Cliente
    st.subheader(f"📍 {cliente['Customer Full Name']}")
    c1, c2, c3 = st.columns(3)
    c1.info(f"🆔 Código: **{cliente['Customer Code']}**")
    c2.warning(f"🏠 {cliente['Address']}")
    
    # Barra de Progreso Visual
    comprados = cliente[prod_cols].sum()
    porcentaje = comprados / total_refs
    c3.metric("Progreso Referencias", f"{int(comprados)} de {total_refs}", delta=f"{int(porcentaje*100)}%")
    st.progress(porcentaje)

    st.divider()

    # Productos
    col_falta, col_tiene = st.columns(2)
    
    with col_falta:
        st.markdown("### 🔴 OPORTUNIDADES (Falta)")
        for prod in prod_cols:
            if cliente[prod] == 0:
                if st.button(f"🛒 VENDER: {prod.replace('Bits ', '')}", key=f"v_{prod}"):
                    registrar_venta(codigo_cliente, prod)
    
    with col_tiene:
        st.markdown("### ✅ SURTIDO ACTUAL")
        for prod in prod_cols:
            if cliente[prod] == 1:
                # Chequear si es nuevo (azul) o viejo (verde) comparando con original
                orig_val = st.session_state.original[st.session_state.original['Customer Code'] == codigo_cliente].iloc[0][prod]
                if orig_val == 0:
                    st.markdown(f'<div class="status-badge blue-bg">🔵 NUEVO: {prod}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="status-badge green-bg">🟢 {prod}</div>', unsafe_allow_html=True)

