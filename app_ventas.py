import streamlit as st
import pandas as pd
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestor Ruta 8087", page_icon="🚛", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; }
    .status-badge { padding: 5px 10px; border-radius: 5px; color: white; font-weight: bold; text-align: center; }
    .red-bg { background-color: #ff4b4b; }
    .green-bg { background-color: #28a745; }
    .blue-bg { background-color: #29b5e8; }
    .client-card { padding: 10px; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 10px; background-color: #f9f9f9; }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DEL ARCHIVO ---
# Nombre EXACTO de tu archivo Excel subido a GitHub
FILE_PATH = 'Copia de LISTADO ACCIONES Q1.xlsx'
# Nombre de la hoja/pestaña dentro del Excel (asumimos 'BITS' o la primera hoja)
HOJA_DATOS = 'BITS' # Si da error, prueba cambiando esto a 'Sheet1' o 'Hoja1'

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    try:
        # Leemos el Excel. sheet_name=None lee TODAS las pestañas para no perder datos al guardar
        all_sheets = pd.read_excel(FILE_PATH, sheet_name=None, engine='openpyxl')
        
        # Buscamos la hoja correcta (ignorando mayúsculas/minúsculas)
        sheet_found = None
        for key in all_sheets.keys():
            if 'BIT' in key.upper(): # Busca una hoja que contenga "BIT"
                sheet_found = key
                break
        
        if not sheet_found:
            # Si no encuentra "BITS", usa la primera hoja por defecto
            sheet_found = list(all_sheets.keys())[0]
            
        df = all_sheets[sheet_found]
        
        # Filtramos solo la ruta 8087
        if 'Route' in df.columns:
            df = df[df['Route'] == 8087].copy()
        
        return df, sheet_found
        
    except FileNotFoundError:
        st.error(f"❌ No encuentro el archivo: {FILE_PATH}. Asegúrate de que está subido a GitHub.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error al leer el Excel: {e}")
        st.stop()

# --- 2. GESTIÓN DEL ESTADO ---
if 'data' not in st.session_state:
    df_loaded, sheet_name = load_data()
    st.session_state.data = df_loaded
    st.session_state.sheet_name = sheet_name
    st.session_state.original = df_loaded.copy()

def save_data():
    """Guarda los cambios en el Excel original manteniendo todas las pestañas"""
    try:
        # Leemos el Excel completo original de nuevo
        all_sheets = pd.read_excel(FILE_PATH, sheet_name=None, engine='openpyxl')
        
        # Actualizamos NUESTRA hoja con los datos de la sesión
        # Primero recuperamos el dataframe completo de esa hoja (incluyendo otras rutas)
        df_full_sheet = all_sheets[st.session_state.sheet_name]
        
        # Actualizamos las filas de la ruta 8087
        df_8087_actual = st.session_state.data
        
        # Usamos Customer Code como índice para actualizar
        df_full_sheet.set_index('Customer Code', inplace=True)
        df_8087_actual.set_index('Customer Code', inplace=True)
        
        df_full_sheet.update(df_8087_actual)
        
        # Reseteamos índices
        df_full_sheet.reset_index(inplace=True)
        df_8087_actual.reset_index(inplace=True)
        
        # Guardamos en el diccionario general
        all_sheets[st.session_state.sheet_name] = df_full_sheet
        
        # Escribimos todo el archivo Excel de nuevo
        with pd.ExcelWriter(FILE_PATH, engine='openpyxl') as writer:
            for sheet, data in all_sheets.items():
                data.to_excel(writer, sheet_name=sheet, index=False)
                
        st.toast("✅ ¡Cambios guardados en el Excel!")
        
    except Exception as e:
        st.error(f"Error al guardar: {e}")

def registrar_venta(customer_code, col_name):
    # Buscar índice en la sesión
    mask = st.session_state.data['Customer Code'] == customer_code
    if mask.any():
        idx = st.session_state.data[mask].index[0]
        st.session_state.data.at[idx, col_name] = 1
        save_data()
        st.rerun()

# --- 3. INTERFAZ ---
st.title("🚛 Ruta 8087 - Gestor Pro")

if 'data' in st.session_state:
    prod_cols = [c for c in st.session_state.data.columns if 'Bits' in c]
    total_refs = len(prod_cols)

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("🔍 Clientes")
        search = st.text_input("Buscar...", placeholder="Nombre o código")
        
        df_display = st.session_state.data
        if search:
            mask = df_display['Customer Full Name'].str.contains(search, case=False, na=False) | \
                   df_display['Customer Code'].astype(str).str.contains(search, na=False)
            df_display = df_display[mask]
        
        opciones = []
        mapa_clientes = {}
        for idx, row in df_display.iterrows():
            comprados = row[prod_cols].sum()
            progreso = f"{int(comprados)}/{total_refs}"
            label = f"{row['Customer Full Name']} ({row['Customer Code']})"
            opciones.append(label)
            mapa_clientes[label] = row['Customer Code']
        
        if opciones:
            seleccion = st.radio("Lista:", opciones)
        else:
            st.warning("No hay coincidencias")
            seleccion = None

    # --- PRINCIPAL ---
    if seleccion:
        codigo_cliente = mapa_clientes[seleccion]
        cliente = st.session_state.data[st.session_state.data['Customer Code'] == codigo_cliente].iloc[0]
        
        st.subheader(f"📍 {cliente['Customer Full Name']}")
        c1, c2 = st.columns(2)
        c1.info(f"🆔 **{cliente['Customer Code']}**")
        c2.caption(f"🏠 {cliente['Address']}")
        
        # Progreso
        comprados = cliente[prod_cols].sum()
        porcentaje = comprados / total_refs if total_refs > 0 else 0
        st.progress(porcentaje)
        st.caption(f"Progreso: {int(comprados)} de {total_refs} productos")

        st.divider()

        col_falta, col_tiene = st.columns(2)
        with col_falta:
            st.markdown("### 🔴 FALTAN")
            for prod in prod_cols:
                if cliente[prod] == 0:
                    if st.button(f"🛒 VENDER: {prod.replace('Bits ', '')}", key=f"v_{prod}_{codigo_cliente}"):
                        registrar_venta(codigo_cliente, prod)
        
        with col_tiene:
            st.markdown("### ✅ TIENE")
            for prod in prod_cols:
                if cliente[prod] == 1:
                    # Comparamos con original para ver si es nuevo
                    orig_val = st.session_state.original[st.session_state.original['Customer Code'] == codigo_cliente].iloc[0][prod]
                    if orig_val == 0:
                        st.markdown(f'<div class="status-badge blue-bg">🔵 VENDIDO HOY: {prod}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="status-badge green-bg">🟢 {prod}</div>', unsafe_allow_html=True)
