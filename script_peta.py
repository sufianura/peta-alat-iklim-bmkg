import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import os
import glob

# -------------------------
# Fungsi untuk baca semua file CSV
# -------------------------
@st.cache_data
def load_all_data():
    data_frames = {}
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightblue']
    alat_files = glob.glob("data/*.csv")

    for i, file in enumerate(alat_files):
        df = pd.read_csv(file, sep=';')
        df['latt_station'] = pd.to_numeric(df['latt_station'], errors='coerce')
        df['long_station'] = pd.to_numeric(df['long_station'], errors='coerce')
        df = df.dropna(subset=['latt_station', 'long_station'])
        alat_name = os.path.basename(file).replace('.csv', '')
        df['alat'] = alat_name
        df['color'] = colors[i % len(colors)]
        data_frames[alat_name] = df

    return data_frames

# -------------------------
# Fungsi untuk membuat peta interaktif
# -------------------------
def create_map(data):
    m = folium.Map(location=[-2.5, 118], zoom_start=5)

    for provinsi in data['nama_propinsi'].dropna().unique():
        cluster = MarkerCluster(name=provinsi).add_to(m)
        subset = data[data['nama_propinsi'] == provinsi]
        for _, row in subset.iterrows():
            folium.Marker(
                location=[row['latt_station'], row['long_station']],
                popup=folium.Popup(f"""
                    <b>Stasiun:</b> {row['name_station']}<br>
                    <b>Provinsi:</b> {row['nama_propinsi']}<br>
                    <b>Kota:</b> {row['nama_kota']}<br>
                    <b>Alat:</b> {row['alat']}<br>
                    <b>Status:</b> {row['status_operasional']}<br>
                """, max_width=250),
                icon=folium.Icon(color=row['color'], icon='info-sign')
            ).add_to(cluster)

    folium.LayerControl().add_to(m)
    return m

# -------------------------
# UI Streamlit
# -------------------------
st.set_page_config(layout="wide")
st.title("📍 PETA JARINGAN ALAT PENGAMATAN IKLIM")

# Load semua data alat
all_data = load_all_data()
alat_options = list(all_data.keys())

# Dropdown pilih alat
selected_alat = st.selectbox("🔧 Pilih Alat yang Ditampilkan", options=alat_options)

# Ambil data alat yang dipilih
selected_data = all_data[selected_alat]

# Buat dan tampilkan peta
if not selected_data.empty:
    mymap = create_map(selected_data)
    st_folium(mymap, width=1000, height=600)
else:
    st.warning("Data tidak valid untuk alat yang dipilih.")

# -------------------------
# Download PDF Terkait Alat
# -------------------------
st.sidebar.header("📎 Unduh Peta (PDF) untuk Alat Terpilih")

pdf_path = os.path.join("peta", f"{selected_alat}.pdf")

if os.path.exists(pdf_path):
    with open(pdf_path, "rb") as f:
        st.sidebar.download_button(
            label=f"⬇️ Unduh Peta: {selected_alat}.pdf",
            data=f,
            file_name=f"{selected_alat}.pdf",
            mime="application/pdf",
            key="pdf-per-alat"
        )
else:
    st.sidebar.info(f"Tidak ditemukan PDF untuk alat: {selected_alat}")
