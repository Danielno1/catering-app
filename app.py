import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="餐飲成本智慧助手", layout="wide")

# --- 暴力直接連線法 ---
# 直接定義網址，避開 Secrets 編碼問題
SHEET_URL = "https://docs.google.com/spreadsheets/d/1dPuQ80Yudrym53l3h6FJygu2Yj_Y7fyfLBXNnFAEa4/edit#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛡️ 料理成本智慧連動系統")

# --- 讀取資料庫 ---
try:
    # 這裡直接傳入網址
    inventory_df = conn.read(spreadsheet=SHEET_URL, worksheet="採買紀錄")
    price_dict = inventory_df.groupby('項目')['每克成本'].last().to_dict()
    item_list = sorted(list(price_dict.keys()))
except Exception as e:
    st.error(f"連線失敗，請確認試算表分頁名稱是否為『採買紀錄』。錯誤訊息: {e}")
    item_list = []
    price_dict = {}

tab1, tab2 = st.tabs(["🛒 採買記帳", "📊 菜單成本分析"])

# --- 分頁 1：採買記錄 ---
with tab1:
    st.subheader("📝 新增採買紀錄")
    with st.form("purchase_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        shop = col1.text_input("採買店家")
        item = col2.text_input("項目 (食材名稱)")
        
        col3, col4, col5 = st.columns([1.5, 1.5, 1])
        price = col3.number_input("總價 (TWD)", min_value=0, step=1)
        w_val = col4.number_input("購買重量", min_value=0.01)
        unit = col5.selectbox("單位", ["台斤", "公克(g)"])
        
        if st.form_submit_button("🚀 送出並儲存"):
            actual_g = w_val * 600 if unit == "台斤" else w_val
            unit_p = round(price / actual_g, 4)
            
            new_row = pd.DataFrame([{
                "時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                "採買店家": shop,
                "項目": item,
                "總價": price,
                "重量": w_val,
                "單位": unit,
                "每克成本": unit_p
            }])
            
            # 儲存時也直接使用網址
            existing = conn.read(spreadsheet=SHEET_URL, worksheet="採買紀錄")
            updated = pd.concat([existing, new_row], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, worksheet="採買紀錄", data=updated)
            st.success(f"✅ 已存入！『{item}』換算每克成本為 ${unit_p}")
            st.rerun()

# --- 分頁 2：菜單成本分析 ---
with tab2:
    st.subheader("⚖️ 料理成本分析")
    sell_price = st.number_input("預計售價", min_value=0)

    if 'rows' not in st.session_state: st.session_state['rows'] = 3
    
    total_food_cost = 0.0
    for i in range(st.session_state['rows']):
        c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
        sel = c1.selectbox(f"選擇食材 {i+1}", ["-- 請選擇 --"] + item_list, key=f"s_{i}")
        u_p = price_dict.get(sel, 0.0)
        c2.write(f"單價: ${u_p}/g")
        u_w = c3.number_input(f"用量(g)", min_value=0.0, key=f"w_{i}")
        sub = round(u_p * u_w, 2)
        c4.write(f"小計: ${sub}")
        total_food_cost += sub

    if st.button("➕ 增加一種食材"):
        st.session_state['rows'] += 1
        st.rerun()

    st.divider()
    if sell_price > 0:
        margin = ((sell_price - total_food_cost) / sell_price) * 100
        st.metric("總食材成本", f"${round(total_food_cost, 1)}")
        st.metric("毛利率", f"{round(margin, 1)}%")
