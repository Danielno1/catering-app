import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="料理成本智慧系統", layout="wide")

# 1. 定義試算表 CSV 讀取連結
SHEET_ID = "1dPuQ80Yudrym53l3h6FJygu2Yj_Y7fyfLBXNnFAEa4"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"

st.title("🛡️ 料理成本智慧系統")

@st.cache_data(ttl=5)
def load_data():
    try:
        # 讀取雲端資料
        data = pd.read_csv(CSV_URL)
        return data
    except:
        return pd.DataFrame()

df = load_data()

tab1, tab2 = st.tabs(["🛒 採買記帳", "📊 成本分析"])

with tab1:
    st.subheader("📝 成本快速計算器")
    with st.form("purchase_form", clear_on_submit=False):
        col_date, col_shop = st.columns(2)
        # 完全對應您的試算表標題：日期、採買店家、項目
        buy_date = col_date.date_input("日期", date.today())
        shop = col_shop.text_input("採買店家")
        name = st.text_input("項目 (食材名稱)")
        
        col3, col4, col5 = st.columns([1, 1, 1])
        price = col3.number_input("總價 (元)", min_value=0, step=1)
        weight = col4.number_input("購買重量", min_value=0.01, step=0.01)
        unit = col5.selectbox("單位", ["台斤", "公克(g)"])
        
        if st.form_submit_button("⚖️ 開始換算"):
            if not name:
                st.error("⚠️ 請輸入項目名稱！")
            else:
                # 台斤換算：1台斤 = 600g
                real_g = weight * 600 if unit == "台斤" else weight
                cost_per_g = round(price / real_g, 4)
                
                st.success(f"✅ 計算成功！請手動填入試算表第一列：")
                st.markdown(f"""
                | 日期 | 採買店家 | 項目 | 總價 | 重量(g) | 每克成本 |
                | :--- | :--- | :--- | :--- | :--- | :--- |
                | {buy_date} | {shop} | {name} | {price} | {real_g} | **{cost_per_g}** |
                """)
                st.info("💡 填好後，切換到『成本分析』分頁即可直接選用。")

with tab2:
    # 這裡檢查欄位，必須跟您的 A1 到 F1 完全一樣
    required_cols = ['日期', '採買店家', '項目', '每克成本']
    
    if df.empty or not all(c in df.columns for c in required_cols):
        st.warning("⚠️ 雲端資料庫同步中，或欄位名稱未對齊。")
        st.write("目前偵測到的標題：", list(df.columns) if not df.empty else "讀取不到資料")
    else:
        st.subheader("📊 雲端單價庫 (Sheet1)")
        # 只顯示您需要的資訊
        st.dataframe(df[['日期', '採買店家', '項目', '每克成本']].tail(10), use_container_width=True)
        
        st.divider()
        st.subheader("⚖️ 料理配方試算")
        
        # 抓取每個項目最後一次更新的單價
        price_dict = df.groupby('項目')['每克成本'].last().to_dict()
        items = sorted(list(price_dict.keys()))
        
        sel_item = st.selectbox("請選擇食材", ["--請選擇--"] + items)
        if sel_item != "--請選擇--":
            u_p = price_dict.get(sel_item, 0)
            st.write(f"🔹 **{sel_item}** 紀錄單價: `${u_p}` /g")
            use_w = st.number_input("用量 (g)", min_value=0.0, step=1.0)
            if use_w > 0:
                st.metric("成本小計", f"${round(u_p * use_w, 2)} 元")
