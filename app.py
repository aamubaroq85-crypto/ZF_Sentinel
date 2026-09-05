import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ZF-Sentinel Enterprise", page_icon="⚡", layout="wide")

# SIMULASI DATABASE ARCHIVAL VAULT (Rekam Jejak Sinyal Kritis)
if 'vault_history' not in st.session_state:
    st.session_state['vault_history'] = pd.DataFrame(columns=['Waktu', 'Pair', 'Perubahan (%)', 'ZF-Score', 'Status'])

st.title("⚡ ZF-Sentinel: Enterprise Console")
st.markdown("*Protokol Komersial, Paywall, & Archival Vault Berbasis Zuhri Formalism*")

# 1. SISTEM PAYWALL / LISENSI AKSES (Sederhana)
st.sidebar.header("🔐 Akses Pelanggan (Paywall)")
license_key = st.sidebar.text_input("Masukkan Lisensi VIP", type="password")

VALID_KEYS = ["ZF-PREDATOR-2026", "ZF-ARCHITECT-VIP"] # Contoh lisensi berbayar

if license_key not in VALID_KEYS:
    st.warning("🔒 Anda berada dalam Mode Tamu (Terbatas). Masukkan Kunci Lisensi VIP yang valid di menu samping untuk membuka fitur penuh dan siaran langsung Sinyal Kritis.")
    is_vip = False
else:
    st.success("✅ Akses VIP Terverifikasi. Selamat datang, Arsitek.")
    is_vip = True

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Konfigurasi Sistem")
filter_type = st.sidebar.selectbox("Segmentasi Pasar", ["Semua Aset", "Major Pairs (BTC, ETH, SOL, BNB, XRP)"])

if st.button("🔄 Segarkan Data Pasar"):
    st.rerun()

@st.cache_data(ttl=10)
def fetch_market_data():
    url = "https://data-api.binance.vision/api/v3/ticker/24hr"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df = df[df['symbol'].str.endswith('USDT')]
            df['priceChangePercent'] = df['priceChangePercent'].astype(float)
            df['volume'] = df['volume'].astype(float)
            df['quoteVolume'] = df['quoteVolume'].astype(float)
            return df
        return None
    except Exception as e:
        return None

with st.spinner("Memindai manifold..."):
    df = fetch_market_data()

if df is not None and not df.empty:
    if filter_type == "Major Pairs (BTC, ETH, SOL, BNB, XRP)":
        majors = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
        df = df[df['symbol'].isin(majors)]

    df['zf_score'] = (abs(df['priceChangePercent']) / 20.0).clip(0.0, 1.0)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Pair Dipindai", len(df))
    with col2:
        top_gain = df.sort_values(by="priceChangePercent", ascending=False).iloc[0]
        st.metric("Tertinggi", top_gain['symbol'], f"+{top_gain['priceChangePercent']:.1f}%")

    st.subheader("🚨 Deteksi Anomali & Rekam Jejak")
    
    threshold = st.slider("Ambang Batas Perubahan (%)", 0.1, 20.0, 3.0)
    anomalies = df[abs(df['priceChangePercent']) >= threshold].sort_values(by="priceChangePercent", ascending=False)

    if not anomalies.empty:
        # Masukkan temuan ke Archival Vault secara otomatis jika memenuhi kriteria kritis (> 0.75)
        critical_found = anomalies[anomalies['zf_score'] > 0.75]
        if not critical_found.empty and is_vip:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for _, r in critical_found.iterrows():
                # Hindari duplikat instan
                if r['symbol'] not in st.session_state['vault_history']['Pair'].values:
                    new_row = pd.DataFrame({
                        'Waktu': [current_time],
                        'Pair': [r['symbol']],
                        'Perubahan (%)': [f"{r['priceChangePercent']:+.2f}%"],
                        'ZF-Score': [f"{r['zf_score']:.2f}"],
                        'Status': ['Kritis / Tangkap Sinyal']
                    })
                    st.session_state['vault_history'] = pd.concat([new_row, st.session_state['vault_history']], ignore_index=True)

        # Tampilan Kartu Berdasarkan Hak Akses
        for index, row in anomalies.iterrows():
            symbol = row['symbol']
            price = row['lastPrice']
            change = row['priceChangePercent']
            vol = row['quoteVolume']
            score = row['zf_score']
            
            color_icon = "🟢" if change > 0 else "🔴"
            status_kritis = "🔥 KRITIS (Predator)" if score > 0.75 else "⚡ Aktif/Observasi"
            
            with st.container():
                if not is_vip and score > 0.75:
                    st.markdown(f"**🔒 {symbol}** | *Konten Terkunci. Masukkan Lisensi VIP di Sidebar untuk Membuka Detail Anomali Kritis Ini.*")
                else:
                    st.markdown(f"""
                    **{color_icon} {symbol}** | ZF-Score: `{score:.2f}` ({status_kritis})  
                    💰 Harga: `{price}` | Perubahan: **{change:+.2f}%**  
                    📊 Vol: `${vol:,.0f}`
                    """)
                st.markdown("---")
        
        # FITUR: Menampilkan Archival Vault (Proof of Performance)
        st.subheader("🏛️ Archival Vault (Rekam Jejak Sinyal Historis)")
        st.markdown("Daftar arsip anomali sistem yang terekam sebagai bukti performa keakuratan deteksi:")
        if not st.session_state['vault_history'].empty:
            st.dataframe(st.session_state['vault_history'], use_container_width=True)
        else:
            st.info("Belum ada rekam jejak anomali kritis yang masuk ke arsip pada sesi ini.")

    else:
        st.success("Pasar dalam fase laminar murni di bawah ambang batas ini.")
else:
    st.error("Gagal terhubung ke node data.")

st.caption("ZF-Core V16.7-PREDATOR | Enterprise Edition | Time-Lock 2326")
