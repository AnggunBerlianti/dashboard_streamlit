# dashboard_streamlit ✨
Dashboard interaktif berbasis Streamlit untuk menyampaikan hasil analisis data e-commerce. 

## Pertanyaan Bisnis
```
- Pertanyaan 1: Kategori produk apa yang menghasilkan revenue tertinggi sepanjang tahun 2018, dan berapa persentase kontribusinya terhadap total revenue pada periode tersebut?
- Pertanyaan 2: Berapa rata-rata durasi pengiriman pesanan dari tanggal pembelian hingga diterima pelanggan pada setiap state sepanjang tahun 2018?
- Pertanyaan 3: Bagaimana perkembangan jumlah pesanan dan total revenue setiap bulan selama periode 2017-2018, serta pada bulan apa kedua indikator tersebut mencapai nilai tertinggi?
```

## Fitur Dashboard
```
- Filter di sidebar: rentang waktu pesanan dan pilihan state pelanggan.
- Ringkasan: total pesanan, total revenue, pelanggan unik, rata-rata durasi pengiriman, dan persentase pesanan terlambat.
- Kategori Produk: kategori dengan revenue tertinggi beserta persentase kontribusinya.
- Durasi Pengiriman: rata-rata durasi pengiriman per state dibandingkan dengan rata-rata nasional.
- Tren Bulanan: perkembangan jumlah pesanan dan total revenue per bulan beserta bulan puncaknya.
- Pelanggan: sebaran pelanggan per state.
- Analisis RFM: pelanggan terbaik pada tiap parameter dan segmentasi pelanggan berdasarkan `RFM_score`.
```

## Setup Environment
```
Proyek ini dikembangkan dengan **Python 3.10.11**. Python 3.10 atau lebih baru disarankan.
```

### Setup Environment - VS Code / Terminal (venv)

```
cd streamlit_ecommerce
python -m venv .venv
```

Aktifkan environment:

```
# Windows (CMD)
.venv\Scripts\activate

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Mac / Linux
source .venv/bin/activate
```

Pasang library:

```
pip install -r requirements.txt
```

## Run steamlit app
```
streamlit run dashboard.py
```
