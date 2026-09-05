import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="ZF-Sentinel Live", page_icon="⚡", layout="wide")

st.title("⚡ ZF-Sentinel: Market Anomaly")
st.markdown("*Protokol Pemantauan Ketegangan Pasar & Deteksi Anomali*")

if st.button("🔄 Segarkan Data"):
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
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Pair", len(df))
    with col2:
        top_gain = df.sort_values(by="priceChangePercent", ascending=False).iloc[0]
        st.metric("Tertinggi", top_gain['symbol'], f"+{top_gain['priceChangePercent']:.1f}%")

    st.subheader("🚨 Daftar Anomali Pasar")
    
    threshold = st.slider("Ambang Batas (%)", 3.0, 20.0, 7.0)
    anomalies = df[abs(df['priceChangePercent']) >= threshold].sort_values(by="priceChangePercent", ascending=False)

    if not anomalies.empty:
        st.warning(f"Ditemukan {len(anomalies)} aset dengan distorsi tinggi!")
        
        # Menampilkan dalam bentuk kartu vertikal yang pas di layar HP
        for index, row in anomalies.iterrows():
            symbol = row['symbol']
            price = row['lastPrice']
            change = row['priceChangePercent']
            vol = row['quoteVolume']
            
            color_icon = "🟢" if change > 0 else "🔴"
            
            with st.container():
                st.markdown(f"""
                **{color_icon} {symbol}**  
                💰 Harga: `{price}` | Perubahan: **{change:+.2f}%**  
                📊 Vol: `${vol:,.0f}`
                """)
                st.markdown("---")
    else:
        st.success("Pasar dalam fase laminar (stabil).")
else:
    st.error("Gagal terhubung ke node data.")

st.caption("ZF-Core V16.7-PREDATOR | Time-Lock 2326")
