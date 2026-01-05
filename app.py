import streamlit as st
import pandas as pd
import gspread

st.set_page_config(page_title="餐飲系統", layout="wide")

# 1. 直接定義您的公開網址
SHEET_URL = "https://docs.google.com/spreadsheets/d/1dPuQ80Yudrym53l3h6FJygu2Yj_Y7fyfLBXNnFAEa4"

# 2. 建立連線 (使用公開編輯模式)
try:
    gc = gspread.public()
    sh = gc.open_by_url(SHEET_URL)
    ws = sh.get_worksheet(0) # 讀取第一個分頁
    data = ws.get_all_records()
    df = pd.DataFrame(data)
except:
    st.error("❌ 無法連線！請確保 Google 試算表已開啟『知道連結的任何人都能編輯』權限。")
    df = pd.DataFrame()

st.title("🛡️ 料理成本智慧系統")

t1, t2 = st.tabs(["🛒 採買記帳", "📊 成本分析"])

with t1:
    with st.form("my_form", clear_on_submit=True):
        item = st.text_input("食材名稱")
        price = st.number_input("總價", min_value=0)
        weight = st.number_input("購買重量", min_value=0.01)
        unit = st.selectbox("單位", ["台斤", "公克(g)"])
        
        if st.form_submit_button("儲存資料"):
            # 台斤換算：1台斤 = 600g
            real_g = weight * 600 if unit == "台斤" else weight
            cost_per_g = round(price / real_g, 4)
            
            # 準備存入資料 (這裡建議手動打開試算表，權限改為編輯者)
            st.info("💡 提醒：若要自動存入，請確認試算表共用權限為『編輯者』")
            st.success(f"計算完成：{item} 每克成本為 {cost_per_g} 元")

with t2:
    if df.empty:
        st.write("目前資料庫是空的，請先記帳。")
    else:
        st.write("### 目前食材單價庫")
        st.dataframe(df)
