import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="ZF-Sentinel Live", page_icon="⚡", layout="wide")

st.title("⚡ ZF-Sentinel: Market Anomaly & Liquidity Scanner")
st.markdown("*Protokol Pemantauan Ketegangan Pasar & Deteksi Anomali Berbasis Zuhri Formalism*")

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

with st.spinner("Menghubungkan ulang ke node resonansi..."):
    df = fetch_market_data()

if df is not None and not df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pair Dipindai", len(df))
    with col2:
        top_gainers = df.sort_values(by="priceChangePercent", ascending=False).iloc[0]
        st.metric("Lonjakan Tertinggi", top_gainers['symbol'], f"+{top_gainers['priceChangePercent']:.1f}%")
    with col3:
        top_volume = df.sort_values(by="quoteVolume", ascending=False).iloc[0]
        st.metric("Likuiditas Terbesar", top_volume['symbol'], f"${top_volume['quoteVolume']:,.0f}")

    st.subheader("🚨 Deteksi Anomali & Lonjakan Volatilitas")
    
    threshold = st.slider("Ambang Batas Anomali (%)", 3.0, 20.0, 7.0)
    anomalies = df[abs(df['priceChangePercent']) >= threshold].sort_values(by="priceChangePercent", ascending=False)

    if not anomalies.empty:
        st.warning(f"Ditemukan {len(anomalies)} aset dengan distorsi topologis tinggi!")
        
        # Format dan ganti nama kolom agar pas di layar seluler
        display_df = anomalies[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume']].copy()
        display_df.columns = ['Pair', 'Harga', 'Perubahan (%)', 'Volume (USDT)']
        display_df['Perubahan (%)'] = display_df['Perubahan (%)'].round(2)
        display_df['Volume (USDT)'] = display_df['Volume (USDT)'].map('{:,.0f}'.format)
        
        st.dataframe(display_df, use_container_width=True)
    else:
        st.success("Kondisi pasar dalam fase laminar (stabil, belum ada anomali ekstrem).")
else:
    st.error("Gagal terhubung ke node penyedia data likuiditas.")

st.markdown("---")
st.caption("ZF-Core V16.7-PREDATOR | Terkunci pada Time-Lock 2326")
