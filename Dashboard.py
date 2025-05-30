import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.stats import kstest
import plotly.express as px

st.set_page_config(page_title="Dashboard Inventaris", page_icon="📦", layout="wide")

# Sidebar
st.sidebar.title("Dashboard Inventaris")
page = st.sidebar.radio("Pilih halaman:", ["🏢 Company Profile", "📤 Upload Data", 
                                           "📊 Inventory Data Monitoring", "🔢 ABC Analysis"])

# Fungsi halaman profil perusahaan
def page_profil_perusahaan():

    col1, col2 = st.columns([1.2, 5])
    with col1:
        st.image("LogoIC.png")
    with col2:
        st.markdown("<h1 style='margin-top: 5px;'>Profil Perusahaan - PLN ICON+</h1>", unsafe_allow_html=True)

    st.markdown("""
    **PLN ICON+** (PT Indonesia Comnets Plus) adalah anak perusahaan dari PT PLN (Persero) yang bergerak di bidang layanan jaringan dan teknologi informasi.

    Visi: *Menjadi penyedia solusi teknologi informasi dan komunikasi terdepan di Indonesia.*

    Misi:
    - Memberikan layanan infrastruktur jaringan terbaik
    - Mendukung transformasi digital PLN dan masyarakat luas
    - Mendorong inovasi berkelanjutan di bidang TIK

    📍 Kantor Pusat: Jakarta, Indonesia  
    🌐 Website: [https://iconpln.co.id](https://iconpln.co.id)
    """)

# Upload data dan simpan di session state
if 'data' not in st.session_state:
    st.session_state['data'] = None

if page == "🏢 Company Profile":
    page_profil_perusahaan()

elif page == "📤 Upload Data":
    st.title("📁 Upload Inventory Data")
    uploaded_file = st.file_uploader("Unggah file Excel", type=["xlsx"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.session_state['data'] = df
        st.success("Data berhasil diunggah!")
        st.dataframe(df)

elif page == "📊 Inventory Data Monitoring":
    st.title("📊 Inventory Data Monitoring")
    df = st.session_state['data']

    if df is not None:
        col1, col2 = st.columns(2)
        with col1:
            stock_out = df["Quantity"].sum()
            st.metric(label="TOTAL OUTFLOW", value=f"{stock_out:,} Items")
        with col2:
            total_value = df["Amount in LC"].sum()
            formatted_value = f"Rp {total_value/1e9:.1f} B" if abs(total_value) > 1e9 else f"{total_value/1e6:.1f}M"
            st.metric(label="TOTAL VALUE", value=formatted_value)

        st.markdown("---")
        st.subheader("📦 Quantity by Valuation Type")
        if "Valuation Type" in df.columns:
            move_chart = df.groupby("Valuation Type")["Quantity"].sum().sort_values()
            move_chart_df = move_chart.reset_index().rename(columns={"Quantity": "Total Quantity"})
            fig1 = px.bar(move_chart_df, x="Total Quantity", y="Valuation Type", orientation='h', color="Valuation Type",
                        color_discrete_sequence=["#42a5f5"])
            st.plotly_chart(fig1)

        st.subheader("📌 Distribution by Material")
        top_materials = df["Material Description"].value_counts().head(10)
        top_materials_df = top_materials.reset_index()
        top_materials_df.columns = ['Material Description', 'Frequency']
        fig2 = px.bar(top_materials_df, x="Material Description", y="Frequency", color="Material Description",
                          color_discrete_sequence=["#ffa726"])
        st.plotly_chart(fig2)

        st.subheader("📈 Stock Changes by Date")
        if "Posting Date" in df.columns:
            df["Posting Date"] = pd.to_datetime(df["Posting Date"])
            daily_stock = df.groupby("Posting Date")["Quantity"].sum()
            daily_stock_df = daily_stock.reset_index()
            fig3 = px.line(daily_stock_df, x="Posting Date", y="Quantity", markers=True, line_shape="linear")
            st.plotly_chart(fig3)

        st.subheader("📋 Most Moved Items")
        moved_items = df.groupby("Material Description")["Quantity"].sum().abs().sort_values(ascending=False).head(10)
        moved_df = moved_items.reset_index().rename(columns={"Material Description": "Material", "Quantity": "Quantity"})
        st.table(moved_df)
    else:
        st.warning("Silakan unggah data terlebih dahulu di halaman 'Upload Data'.")
        
elif page == "🔢 ABC Analysis":
    st.title("🔍 ABC Analysis")
    df = st.session_state['data']

    if df is not None:
        df_abc = (
            df.copy()
            .groupby("Material")
            .agg(
                Material_Description=("Material Description", "first"),
                Quantity=("Quantity", "sum"),
                Value=("Amount in LC", "sum")
            )
            .reset_index()
        )

        # Hitung kumulatif dan klasifikasi ABC
        df_abc = df_abc.sort_values(by="Value", ascending=False)
        df_abc["Cumulative Sum"] = df_abc["Value"].cumsum()
        df_abc["Cumulative Percentage"] = 100 * df_abc["Cumulative Sum"] / df_abc["Value"].sum()

        def klasifikasi(row):
            if row["Cumulative Percentage"] <= 80:
                return "A"
            elif row["Cumulative Percentage"] <= 95:
                return "B"
            else:
                return "C"

        df_abc["Kategori"] = df_abc.apply(klasifikasi, axis=1)
        st.dataframe(df_abc)

        # Visualisasi Distribusi Kategori ABC
        st.markdown("---")
        st.markdown("### ABC Category Distribution")
        df_abc_plot = df_abc.groupby("Kategori")["Value"].sum().reset_index()
        fig3 = px.bar(df_abc_plot, x="Kategori", y="Value", color="Kategori",
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig3)

        st.markdown("### ABC Category Percentage")
        fig4 = px.pie(df_abc_plot, names="Kategori", values="Value",
                      color_discrete_sequence=px.colors.qualitative.Pastel,
                      hole=0.4)
        # Atur ukuran font label persentase
        fig4.update_traces(
            textinfo='percent',  # hanya tampilkan persentase
            textfont_size=18,    # ukuran font label di luar pie
            insidetextfont=dict(size=18),  # jika text di dalam pie
        )
        st.plotly_chart(fig4)

        # Ringkasan Analisis ABC
        st.markdown("---")
        st.subheader("📋 ABC Analysis Summary")
        abc_summary = df_abc.groupby("Kategori").agg(
            Jumlah_Item=("Material", lambda x: x.astype(str).nunique()),
            Total_Quantity=("Quantity", "sum"),
            Total_Amount=("Value", "sum"),
            Total_Nilai_Rupiah=("Value", "sum")
        ).reset_index()

        abc_summary["Persentase_Jumlah_Item"] = 100 * abc_summary["Jumlah_Item"] / df_abc.shape[0]
        abc_summary["Persentase_Penyerapan"] = 100 * abc_summary["Total_Nilai_Rupiah"] / df_abc["Value"].sum()

        abc_summary_display = abc_summary.rename(columns={
            "Kategori": "Kelompok",
            "Jumlah_Item": "Jumlah Item",
            "Total_Quantity": "Total Quantity",
            "Total_Amount": "Total Amount in LC",
            "Total_Nilai_Rupiah": "Jumlah Nilai Rupiah",
             "Persentase_Jumlah_Item": "Persentase Jumlah Item",
            "Persentase_Penyerapan": "Persentase Penyerapan Nilai Rupiah"
        })

        abc_summary_display["Jumlah Nilai Rupiah"] = abc_summary_display["Jumlah Nilai Rupiah"].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
        abc_summary_display["Total Amount in LC"] = abc_summary_display["Total Amount in LC"].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
        abc_summary_display["Persentase Jumlah Item"] = abc_summary_display["Persentase Jumlah Item"].map("{:.2f}%".format)
        abc_summary_display["Persentase Penyerapan Nilai Rupiah"] = abc_summary_display["Persentase Penyerapan Nilai Rupiah"].map("{:.2f}%".format)

        st.table(abc_summary_display)
    else:
        st.warning("Silakan unggah data terlebih dahulu di halaman 'Upload Data'.")
