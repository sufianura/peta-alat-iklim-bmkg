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
def create_map(data=None):
    m = folium.Map(location=[-2.5, 118], zoom_start=5, tiles="OpenStreetMap")

    if data is not None and not data.empty:
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
alat_list = list(all_data.keys())
alat_options = ["🗂️ Semua Alat"] + alat_list

# Multiselect pilih alat
selected_alat_list = st.multiselect(
    "🔧 Pilih Alat yang Ditampilkan (boleh lebih dari satu)",
    options=alat_options,
    default=["🗂️ Semua Alat"]
)

# Simpan label asli untuk PDF/tampilan, tapi proses semua data kalau "Semua Alat" dipilih
show_all = not selected_alat_list or "🗂️ Semua Alat" in selected_alat_list
alat_terpilih = alat_list if show_all else selected_alat_list

# Gabungkan data dari alat yang dipilih
selected_data = pd.concat([all_data[alat] for alat in alat_terpilih], ignore_index=True)

# Tampilkan peta
mymap = create_map(selected_data)
st_folium(mymap, width=1000, height=600)

# -------------------------
# Download PDF Terkait Alat
# -------------------------
st.sidebar.header("📎 Unduh Peta (PDF)")

if len(selected_alat_list) == 1 and selected_alat_list[0] != "🗂️ Semua Alat":
    alat = selected_alat_list[0]
    pdf_path = os.path.join("peta", f"{alat}.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.sidebar.download_button(
                label=f"⬇️ Unduh Peta: {alat}.pdf",
                data=f,
                file_name=f"{alat}.pdf",
                mime="application/pdf"
            )
    else:
        st.sidebar.info(f"📄 PDF untuk alat {alat} tidak ditemukan.")
else:
    st.sidebar.info("Pilih hanya satu alat untuk melihat tombol unduh PDF-nya.")

# -------------------------
# TABEL REKAP: Alat, Provinsi, Jumlah
# -------------------------
st.subheader("📊 TABEL REKAPITULASI")

if not selected_data.empty:
    summary_df = (
        selected_data.groupby(["alat", "nama_propinsi"])
        .size()
        .reset_index(name="JUMLAH STASIUN")
        .rename(columns={"alat": "ALAT", "nama_propinsi": "PROVINSI"})
    )
    summary_df.insert(0, "NO", range(1, len(summary_df) + 1))
    st.dataframe(summary_df, use_container_width=True)
else:
    st.info("Tidak ada data untuk ditampilkan dalam tabel.")
