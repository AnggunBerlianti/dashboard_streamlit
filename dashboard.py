import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Dashboard E-Commerce", page_icon="🛒", layout="wide")
sns.set_theme(style="whitegrid")

BIRU = "#1f77b4"
PUDAR = "#b0c4de"
MERAH = "#d62728"
HIJAU = "#2ca02c"


# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_data():
    df = pd.read_csv(Path(__file__).parent / "all_data.csv")

    for kolom in ["order_purchase_timestamp",
                  "order_delivered_customer_date",
                  "order_estimated_delivery_date"]:
        df[kolom] = pd.to_datetime(df[kolom])

    df["delivery_time"] = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"]).dt.days
    df["delay_days"] = (df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]).dt.days
    df["is_late"] = df["delay_days"] > 0
    df["product_category_name_english"] = df["product_category_name_english"].fillna("Tidak diketahui")

    return df.sort_values("order_purchase_timestamp").reset_index(drop=True)


# =========================================================
# FUNGSI MENYIAPKAN DATAFRAME
# =========================================================
def create_monthly_df(df):
    monthly_df = df.assign(bulan=df["order_purchase_timestamp"].dt.to_period("M").astype(str))
    monthly_df = monthly_df.groupby("bulan").agg(
        jumlah_pesanan=("order_id", "nunique"),
        total_revenue=("price", "sum")
    ).reset_index()
    return monthly_df


def create_category_df(df):
    category_df = df.groupby("product_category_name_english").agg(
        jumlah_transaksi=("order_id", "nunique"),
        total_revenue=("price", "sum")
    ).sort_values("total_revenue", ascending=False).reset_index()
    category_df["persen_kontribusi"] = category_df["total_revenue"] / category_df["total_revenue"].sum() * 100
    return category_df


def create_delivery_df(df):
    # Satu baris per pesanan agar pesanan berisi banyak barang tidak dihitung berkali-kali
    order_df = df.drop_duplicates(subset="order_id")
    delivery_df = order_df.groupby("customer_state").agg(
        jumlah_pesanan=("order_id", "nunique"),
        rata_rata_hari=("delivery_time", "mean"),
        median_hari=("delivery_time", "median")
    ).reset_index()
    return delivery_df


def create_bystate_df(df):
    bystate_df = df.groupby("customer_state").agg(
        jumlah_pelanggan=("customer_unique_id", "nunique"),
        total_revenue=("price", "sum")
    ).sort_values("jumlah_pelanggan", ascending=False).reset_index()
    bystate_df["persen_pelanggan"] = bystate_df["jumlah_pelanggan"] / df["customer_unique_id"].nunique() * 100
    return bystate_df


def create_rfm_df(df):
    rfm_df = df.groupby("customer_unique_id", as_index=False).agg(
        max_order=("order_purchase_timestamp", "max"),
        frequency=("order_id", "nunique"),
        monetary=("price", "sum")
    )

    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order"].dt.date.apply(lambda x: (recent_date - x).days)
    rfm_df.drop(columns="max_order", inplace=True)

    # Ranking dan normalisasi (recency kecil = ranking tinggi)
    r_rank = rfm_df["recency"].rank(ascending=False)
    f_rank = rfm_df["frequency"].rank(ascending=True)
    m_rank = rfm_df["monetary"].rank(ascending=True)

    r_norm = r_rank / r_rank.max() * 100
    f_norm = f_rank / f_rank.max() * 100
    m_norm = m_rank / m_rank.max() * 100

    # Bobot: recency 15%, frequency 28%, monetary 57% -> skala 0-5
    rfm_df["RFM_score"] = ((0.15 * r_norm + 0.28 * f_norm + 0.57 * m_norm) * 0.05).round(2)

    kondisi = [rfm_df["RFM_score"] > 4.5,
               rfm_df["RFM_score"] > 4,
               rfm_df["RFM_score"] > 3,
               rfm_df["RFM_score"] > 1.6]
    label = ["Top customers", "High value customers", "Medium value customers", "Low value customers"]
    rfm_df["customer_segment"] = np.select(kondisi, label, default="Lost customers")

    return rfm_df


# =========================================================
# FUNGSI GRAFIK
# =========================================================
def grafik_batang_horizontal(label, nilai, warna, judul, xlabel, teks=None,
                             garis=None, format_ribuan=False, ukuran=(10, 6)):
    fig, ax = plt.subplots(figsize=ukuran)
    nilai = np.asarray(nilai, dtype=float)
    ax.barh(list(label), nilai, color=warna)
    ax.invert_yaxis()

    if teks is not None:
        for i, (v, t) in enumerate(zip(nilai, teks)):
            ax.text(v, i, f"  {t}", va="center", fontsize=9)
        ax.set_xlim(0, nilai.max() * 1.18)

    if garis is not None:
        ax.axvline(garis[0], color="black", linestyle="--", label=garis[1])
        ax.legend(loc="lower right")

    if format_ribuan:
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    ax.set_title(judul, fontsize=13)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")
    fig.tight_layout()
    return fig


def grafik_garis(x, y, judul, ylabel, warna, bulan_puncak, format_ribuan=False):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(x, y, marker="o", color=warna)

    idx_puncak = list(x).index(bulan_puncak)
    ax.scatter(bulan_puncak, list(y)[idx_puncak], color=MERAH, s=110, zorder=5)
    ax.annotate(f"Puncak: {list(y)[idx_puncak]:,.0f}",
                (bulan_puncak, list(y)[idx_puncak]),
                textcoords="offset points", xytext=(8, -14), color=MERAH)

    if format_ribuan:
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:,.0f}"))

    ax.set_title(judul, fontsize=13)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    return fig


# =========================================================
# MEMUAT DATA DAN FILTER
# =========================================================
try:
    all_df = load_data()
except FileNotFoundError:
    st.error("File `all_data.csv` tidak ditemukan. Letakkan file tersebut di folder yang sama dengan `dashboard.py`.")
    st.stop()

min_date = all_df["order_purchase_timestamp"].min().date()
max_date = all_df["order_purchase_timestamp"].max().date()

with st.sidebar:
    st.title("🛒 Filter Data")

    rentang = st.date_input(
        label="Rentang waktu pesanan",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    semua_state = sorted(all_df["customer_state"].dropna().unique())
    state_dipilih = st.multiselect(
        "State pelanggan (kosongkan untuk semua)",
        options=semua_state
    )

if isinstance(rentang, (tuple, list)) and len(rentang) == 2:
    start_date, end_date = rentang
else:
    st.info("Pilih tanggal akhir pada filter di sebelah kiri untuk menampilkan data.")
    st.stop()

main_df = all_df[(all_df["order_purchase_timestamp"] >= pd.Timestamp(start_date)) &
                 (all_df["order_purchase_timestamp"] < pd.Timestamp(end_date) + pd.Timedelta(days=1))]

if state_dipilih:
    main_df = main_df[main_df["customer_state"].isin(state_dipilih)]

if main_df.empty:
    st.warning("Tidak ada data pada filter yang dipilih. Ubah rentang waktu atau state.")
    st.stop()

# =========================================================
# HEADER DAN RINGKASAN
# =========================================================
st.header("Dashboard Analisis E-Commerce :sparkles:")
st.caption(f"Periode ditampilkan: {start_date:%d %b %Y} sampai {end_date:%d %b %Y}")

order_level_df = main_df.drop_duplicates(subset="order_id")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Pesanan", f"{main_df['order_id'].nunique():,}")
col2.metric("Total Revenue", f"{main_df['price'].sum():,.0f}")
col3.metric("Pelanggan Unik", f"{main_df['customer_unique_id'].nunique():,}")
col4.metric("Rata-rata Durasi Kirim", f"{order_level_df['delivery_time'].mean():.1f} hari")
col5.metric("Pesanan Terlambat", f"{order_level_df['is_late'].mean() * 100:.1f}%")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Kategori Produk",
    "🚚 Durasi Pengiriman",
    "📈 Tren Bulanan",
    "👥 Pelanggan",
    "⭐ Analisis RFM"
])

# =========================================================
# TAB 1: KATEGORI PRODUK (PERTANYAAN 1)
# =========================================================
with tab1:
    st.subheader("Kategori Produk dengan Revenue Tertinggi")
    st.caption("Revenue dihitung dari harga barang (price) tanpa ongkir.")

    category_df = create_category_df(main_df)
    maks_kategori = min(15, len(category_df))

    if maks_kategori >= 3:
        top_n = st.slider("Jumlah kategori yang ditampilkan", 3, maks_kategori, min(10, maks_kategori))
    else:
        top_n = maks_kategori

    top_df = category_df.head(top_n)
    warna = [BIRU] + [PUDAR] * (len(top_df) - 1)

    fig = grafik_batang_horizontal(
        top_df["product_category_name_english"], top_df["total_revenue"], warna,
        f"{top_n} Kategori dengan Revenue Tertinggi", "Total Revenue",
        teks=[f"{p:.2f}%" for p in top_df["persen_kontribusi"]], format_ribuan=True
    )
    st.pyplot(fig)
    plt.close(fig)

    kategori_teratas = category_df.iloc[0]
    kontribusi_5 = category_df.head(5)["persen_kontribusi"].sum()
    st.markdown(
        f"**Insight:** Kategori **{kategori_teratas['product_category_name_english']}** menghasilkan revenue tertinggi "
        f"({kategori_teratas['total_revenue']:,.0f}) dengan kontribusi **{kategori_teratas['persen_kontribusi']:.2f}%** "
        f"dari total revenue. Lima kategori teratas menyumbang **{kontribusi_5:.2f}%**."
    )

    with st.expander("Lihat tabel lengkap"):
        st.dataframe(category_df.round(2))

# =========================================================
# TAB 2: DURASI PENGIRIMAN (PERTANYAAN 2)
# =========================================================
with tab2:
    st.subheader("Rata-rata Durasi Pengiriman per State")
    st.caption("Durasi dihitung dari tanggal pembelian sampai pesanan diterima pelanggan.")

    delivery_df = create_delivery_df(main_df)
    min_pesanan = st.slider("Minimal jumlah pesanan per state", 1, 500, 100)

    delivery_plot = delivery_df[delivery_df["jumlah_pesanan"] >= min_pesanan] \
        .sort_values("rata_rata_hari", ascending=False)

    if delivery_plot.empty:
        st.info("Tidak ada state yang memenuhi batas minimal pesanan. Turunkan nilai slider.")
    else:
        rata_nasional = order_level_df["delivery_time"].mean()
        warna = [MERAH] + [PUDAR] * (len(delivery_plot) - 1)

        fig = grafik_batang_horizontal(
            delivery_plot["customer_state"], delivery_plot["rata_rata_hari"], warna,
            "Rata-rata Durasi Pengiriman per State", "Rata-rata durasi (hari)",
            teks=[f"{v:.1f}" for v in delivery_plot["rata_rata_hari"]],
            garis=(rata_nasional, f"Rata-rata nasional ({rata_nasional:.1f} hari)"),
            ukuran=(10, max(5, len(delivery_plot) * 0.4))
        )
        st.pyplot(fig)
        plt.close(fig)

        terlama = delivery_plot.iloc[0]
        tercepat = delivery_plot.iloc[-1]
        st.markdown(
            f"**Insight:** Rata-rata durasi pengiriman adalah **{rata_nasional:.1f} hari**. "
            f"State **{terlama['customer_state']}** paling lama (**{terlama['rata_rata_hari']:.1f} hari**, "
            f"{int(terlama['jumlah_pesanan']):,} pesanan), sedangkan **{tercepat['customer_state']}** "
            f"paling cepat ({tercepat['rata_rata_hari']:.1f} hari)."
        )

    with st.expander("Lihat tabel lengkap"):
        st.dataframe(delivery_df.sort_values("rata_rata_hari", ascending=False).round(2))

# =========================================================
# TAB 3: TREN BULANAN (PERTANYAAN 3)
# =========================================================
with tab3:
    st.subheader("Perkembangan Pesanan dan Revenue per Bulan")

    monthly_df = create_monthly_df(main_df)

    bulan_puncak_pesanan = monthly_df.loc[monthly_df["jumlah_pesanan"].idxmax(), "bulan"]
    bulan_puncak_revenue = monthly_df.loc[monthly_df["total_revenue"].idxmax(), "bulan"]

    kol1, kol2 = st.columns(2)
    with kol1:
        fig = grafik_garis(monthly_df["bulan"], monthly_df["jumlah_pesanan"],
                           "Jumlah Pesanan per Bulan", "Jumlah pesanan", BIRU,
                           bulan_puncak_pesanan, format_ribuan=True)
        st.pyplot(fig)
        plt.close(fig)
    with kol2:
        fig = grafik_garis(monthly_df["bulan"], monthly_df["total_revenue"],
                           "Total Revenue per Bulan", "Total revenue", HIJAU,
                           bulan_puncak_revenue, format_ribuan=True)
        st.pyplot(fig)
        plt.close(fig)

    if bulan_puncak_pesanan == bulan_puncak_revenue:
        st.markdown(f"**Insight:** Jumlah pesanan dan revenue sama-sama mencapai nilai tertinggi pada **{bulan_puncak_pesanan}**.")
    else:
        st.markdown(f"**Insight:** Jumlah pesanan tertinggi terjadi pada **{bulan_puncak_pesanan}**, "
                    f"sedangkan revenue tertinggi pada **{bulan_puncak_revenue}**.")

    with st.expander("Lihat tabel per bulan"):
        st.dataframe(monthly_df.round(2))

# =========================================================
# TAB 4: PELANGGAN (DEMOGRAFI GEOGRAFIS)
# =========================================================
with tab4:
    st.subheader("Sebaran Pelanggan per State")
    st.caption("Dataset hanya memuat lokasi pelanggan (tanpa usia atau jenis kelamin), "
               "sehingga demografi dianalisis dari sisi geografis.")

    bystate_df = create_bystate_df(main_df)
    top_state_n = st.slider("Jumlah state yang ditampilkan", 3, min(15, len(bystate_df)), min(10, len(bystate_df))) \
        if len(bystate_df) > 3 else len(bystate_df)

    top_state = bystate_df.head(top_state_n)
    warna = [BIRU] + [PUDAR] * (len(top_state) - 1)

    fig = grafik_batang_horizontal(
        top_state["customer_state"], top_state["jumlah_pelanggan"], warna,
        f"{top_state_n} State dengan Pelanggan Terbanyak", "Jumlah pelanggan unik",
        teks=[f"{p:.1f}%" for p in top_state["persen_pelanggan"]], format_ribuan=True
    )
    st.pyplot(fig)
    plt.close(fig)

    st.markdown(
        f"**Insight:** State **{bystate_df.iloc[0]['customer_state']}** memiliki pelanggan terbanyak "
        f"({int(bystate_df.iloc[0]['jumlah_pelanggan']):,} pelanggan atau "
        f"{bystate_df.iloc[0]['persen_pelanggan']:.1f}% dari total)."
    )

# =========================================================
# TAB 5: ANALISIS RFM
# =========================================================
with tab5:
    st.subheader("Pelanggan Terbaik Berdasarkan Parameter RFM")

    rfm_df = create_rfm_df(main_df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rata-rata Recency", f"{rfm_df['recency'].mean():.1f} hari")
    col2.metric("Rata-rata Frequency", f"{rfm_df['frequency'].mean():.2f}")
    col3.metric("Rata-rata Monetary", f"{rfm_df['monetary'].mean():,.2f}")
    col4.metric("Pelanggan Sekali Beli", f"{(rfm_df['frequency'] == 1).mean() * 100:.1f}%")

    rfm_df["id_pendek"] = rfm_df["customer_unique_id"].str[:8]

    top_r = rfm_df.sort_values("recency", ascending=True).head(5)
    top_f = rfm_df.sort_values("frequency", ascending=False).head(5)
    top_m = rfm_df.sort_values("monetary", ascending=False).head(5)

    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(20, 5))
    for a, data, kolom, judul in zip(ax, [top_r, top_f, top_m],
                                     ["recency", "frequency", "monetary"],
                                     ["By Recency (days)", "By Frequency", "By Monetary"]):
        a.bar(data["id_pendek"], data[kolom], color=BIRU)
        a.set_title(judul, fontsize=14)
        a.set_xlabel("customer_unique_id")
        a.tick_params(axis="x", rotation=30)
    plt.suptitle("5 Pelanggan Terbaik pada Tiap Parameter RFM", fontsize=16)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    st.caption("Pada grafik recency, banyak pelanggan yang bernilai sama (0 hari) karena berbelanja tepat pada "
               "tanggal pesanan terakhir, sehingga batangnya bisa tidak terlihat.")

    st.subheader("Segmentasi Pelanggan Berdasarkan RFM Score")

    urutan_segmen = ["Top customers", "High value customers", "Medium value customers",
                     "Low value customers", "Lost customers"]

    segmen_df = rfm_df.groupby("customer_segment").agg(
        jumlah_pelanggan=("customer_unique_id", "nunique"),
        rata_recency=("recency", "mean"),
        rata_frequency=("frequency", "mean"),
        rata_monetary=("monetary", "mean"),
        total_monetary=("monetary", "sum")
    ).reindex(urutan_segmen).dropna(subset=["jumlah_pelanggan"]).reset_index()

    segmen_df["persen_pelanggan"] = segmen_df["jumlah_pelanggan"] / segmen_df["jumlah_pelanggan"].sum() * 100
    segmen_df["persen_revenue"] = segmen_df["total_monetary"] / segmen_df["total_monetary"].sum() * 100

    kol1, kol2 = st.columns(2)

    with kol1:
        warna_segmen = [BIRU] + [PUDAR] * (len(segmen_df) - 1)
        fig = grafik_batang_horizontal(
            segmen_df["customer_segment"], segmen_df["jumlah_pelanggan"], warna_segmen,
            "Jumlah Pelanggan per Segmen", "Jumlah pelanggan",
            teks=[f"{p:.1f}%" for p in segmen_df["persen_pelanggan"]],
            format_ribuan=True, ukuran=(8, 5)
        )
        st.pyplot(fig)
        plt.close(fig)

    with kol2:
        fig, ax = plt.subplots(figsize=(8, 5))
        posisi = np.arange(len(segmen_df))
        lebar = 0.38
        ax.bar(posisi - lebar / 2, segmen_df["persen_pelanggan"], lebar, label="% Pelanggan", color=PUDAR)
        ax.bar(posisi + lebar / 2, segmen_df["persen_revenue"], lebar, label="% Revenue", color=BIRU)
        ax.set_xticks(posisi)
        ax.set_xticklabels(segmen_df["customer_segment"], rotation=20, ha="right")
        ax.set_ylabel("Persen (%)")
        ax.set_title("Kontribusi Segmen terhadap Pelanggan dan Revenue", fontsize=13)
        ax.legend()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    terbesar = segmen_df.sort_values("jumlah_pelanggan", ascending=False).iloc[0]
    revenue_terbesar = segmen_df.sort_values("persen_revenue", ascending=False).iloc[0]
    st.markdown(
        f"**Insight:** Segmen terbesar adalah **{terbesar['customer_segment']}** "
        f"({terbesar['persen_pelanggan']:.1f}% pelanggan). Kontribusi revenue terbesar berasal dari "
        f"**{revenue_terbesar['customer_segment']}** ({revenue_terbesar['persen_revenue']:.1f}% revenue "
        f"dari {revenue_terbesar['persen_pelanggan']:.1f}% pelanggan)."
    )

    with st.expander("Lihat tabel ringkasan segmen"):
        st.dataframe(segmen_df.round(2))
