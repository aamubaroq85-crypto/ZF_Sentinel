import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="ZF-Sentinel Pro", page_icon="⚡", layout="wide")

st.title("⚡ ZF-Sentinel: Pro Console")
st.markdown("*Protokol Pemantauan, ZF-Score, & Telegram Gateway*")

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
    # 1. FITUR SEGMENTASI PASAR (Sidebar)
    st.sidebar.header("⚙️ Konfigurasi ZF-Core")
    filter_type = st.sidebar.selectbox("Segmentasi Pasar", ["Semua Aset", "Major Pairs (BTC, ETH, SOL, BNB, XRP)"])
    
    if filter_type == "Major Pairs (BTC, ETH, SOL, BNB, XRP)":
        majors = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
        df = df[df['symbol'].isin(majors)]

    # Konfigurasi Telegram Gateway (Sidebar)
    st.sidebar.markdown("---")
    st.sidebar.subheader("📢 Telegram Gateway")
    tg_token = st.sidebar.text_input("Bot Token", type="password")
    tg_chat_id = st.sidebar.text_input("Chat ID / Channel")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Pair", len(df))
    with col2:
        if not df.empty:
            top_gain = df.sort_values(by="priceChangePercent", ascending=False).iloc[0]
            st.metric("Tertinggi", top_gain['symbol'], f"+{top_gain['priceChangePercent']:.1f}%")

    st.subheader("🚨 Deteksi Anomali & ZF-Score")
    
    threshold = st.slider("Ambang Batas Perubahan (%)", 1.0, 20.0, 5.0)
    
    # 2. FITUR ZF-SCORE SINTETIS (Skala 0 - 1)
    df['zf_score'] = (abs(df['priceChangePercent']) / 20.0).clip(0.0, 1.0)
    
    anomalies = df[abs(df['priceChangePercent']) >= threshold].sort_values(by="priceChangePercent", ascending=False)

    if not anomalies.empty:
        st.warning(f"Ditemukan {len(anomalies)} aset dengan distorsi tinggi!")
        
        # 3. FITUR TELEGRAM BROADCAST BUTTON
        if st.button("🚀 Broadcast 3 Anomali Teratas ke Telegram"):
            if not tg_token or not tg_chat_id:
                st.error("Harap isi Bot Token dan Chat ID di menu samping (Sidebar) terlebih dahulu!")
            else:
                success_count = 0
                for _, row in anomalies.head(3).iterrows():
                    msg = (
                        f"🚨 ZF-SENTINEL ALERT 🚨\n"
                        f"Pair: {row['symbol']}\n"
                        f"Harga: {row['lastPrice']}\n"
                        f"Perubahan: {row['priceChangePercent']:+.2f}%\n"
                        f"ZF-Score: {row['zf_score']:.2f}"
                    )
                    tg_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
                    try:
                        res = requests.post(tg_url, json={"chat_id": tg_chat_id, "text": msg}, timeout=5)
                        if res.status_code == 200:
                            success_count += 1
                    except Exception:
                        pass
                if success_count > 0:
                    st.success(f"Berhasil mengirim {success_count} sinyal ke Telegram!")
                else:
                    st.error("Gagal mengirim. Periksa kembali Token Bot & Chat ID Anda.")

        # Menampilkan Kartu Data dengan Indikator ZF-Score
        for index, row in anomalies.iterrows():
            symbol = row['symbol']
            price = row['lastPrice']
            change = row['priceChangePercent']
            vol = row['quoteVolume']
            score = row['zf_score']
            
            color_icon = "🟢" if change > 0 else "🔴"
            status_kritis = "🔥 KRITIS (Predator)" if score > 0.75 else "⚡ Stabil/Laminar"
            
            with st.container():
                st.markdown(f"""
                **{color_icon} {symbol}** | ZF-Score: `{score:.2f}` ({status_kritis})  
                💰 Harga: `{price}` | Perubahan: **{change:+.2f}%**  
                📊 Vol: `${vol:,.0f}`
                """)
                st.markdown("---")
    else:
        st.success("Pasar dalam fase laminar (stabil).")
else:
    st.error("Gagal terhubung ke node data.")

st.caption("ZF-Core V16.7-PREDATOR | Time-Lock 2326")
