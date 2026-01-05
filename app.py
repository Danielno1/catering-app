import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests

# 1. 頁面與介面設定
st.set_page_config(page_title="餐飲採買雲端版", layout="centered")
st.markdown("""<style>#MainMenu, footer, header {visibility: hidden;}
    .stButton>button { width: 100%; height: 4em; font-size: 22px !important; background-color: #28a745; color: white; border-radius: 15px; }</style>""", unsafe_allow_html=True)

st.title("🛡️ 採買成本雲端助手 (直連版)")

# ---------------------------------------------------------
# 正確的試算表 ID (從您的網址中提取)
# ---------------------------------------------------------
SHEET_ID = "1dPuQ80Yudrym53l3h6FJygu2Yj_Y7fyfLBXNnFAEa4"
# 這是讀取用的 CSV 連結
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# 2. 讀取資料
try:
    # 直接從網址讀取 CSV 格式
    response = requests.get(READ_URL)
    df = pd.read_csv(io.BytesIO(response.content))
    if df.empty:
        df = pd.DataFrame(columns=["時間", "採買店家", "項目", "總價", "重量(g)", "每克成本", "售價"])
except:
    df = pd.DataFrame(columns=["時間", "採買店家", "項目", "總價", "重量(g)", "每克成本", "售價"])

# 3. 輸入區域
st.subheader("📝 新增採買紀錄")
shop_name = st.text_input("🏪 採買店家", placeholder="例如：南門市場")
item_name = st.text_input("🍎 食材項目", placeholder="例如：豬梅花")

col_a, col_b = st.columns(2)
with col_a:
    price = st.number_input("💰 購買總價 (TWD)", min_value=0.0, step=10.0)
with col_b:
    weight = st.number_input("⚖️ 購買重量", min_value=0.01, step=0.1)

unit = st.selectbox("計算單位", ("台斤", "兩", "公斤 (kg)", "公克 (g)"))
selling_price = st.number_input("💹 預計總售價", min_value=0.0, step=10.0)

# 4. 存檔邏輯 (本地備份)
if st.button("🚀 存入今日紀錄"):
    if item_name and price > 0:
        u_map = {"台斤": 600, "兩": 37.5, "公斤 (kg)": 1000, "公克 (g)": 1}
        g_weight = weight * u_map[unit]
        cost_per_g = price / g_weight
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        new_row = pd.DataFrame([{
            "時間": now, "採買店家": shop_name, "項目": item_name, 
            "總價": price, "重量(g)": g_weight, "每克成本": round(cost_per_g, 3), 
            "售價": selling_price
        }])
        
        # 1. 存到電腦本地 (保證資料不丟失)
        updated_df = pd.concat([df, new_row], ignore_index=True)
        updated_df.to_csv("market_data.csv", index=False, encoding="utf-8-sig")
        
        st.success(f"✅ 已成功存入電腦！")
        st.info("💡 請將此檔案上傳或貼至 Google 試算表即可。")
        st.balloons()
        st.rerun()
    else:
        st.warning("⚠️ 請輸入名稱與金額")

# 5. 顯示紀錄
st.divider()
st.subheader("📊 今日清單")
st.dataframe(df.tail(10), use_container_width=True)