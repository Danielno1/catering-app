import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="餐飲助手", layout="wide")

# 1. 這裡直接寫您的網址
URL = "https://docs.google.com/spreadsheets/d/1dPuQ80Yudrym53l3h6FJygu2Yj_Y7fyfLBXNnFAEa4"

conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛡️ 料理成本智慧系統")

# 2. 讀取資料 (使用 Sheet1 避免編碼報錯)
try:
    df = conn.read(spreadsheet=URL, worksheet="Sheet1")
    # 建立食材清單
    if not df.empty and '項目' in df.columns:
        price_dict = df.groupby('項目')['每克成本'].last().to_dict()
        items = sorted(list(price_dict.keys()))
    else:
        items = []
        price_dict = {}
except:
    df = pd.DataFrame()
    items = []
    price_dict = {}

t1, t2 = st.tabs(["🛒 採買記帳", "📊 成本分析"])

with t1:
    with st.form("f1", clear_on_submit=True):
        c1, c2 = st.columns(2)
        shop = c1.text_input("店家")
        name = c2.text_input("品項")
        p = st.number_input("總價", min_value=0)
        w = st.number_input("重量", min_value=0.01)
        u = st.selectbox("單位", ["台斤", "公克(g)"])
        
        if st.form_submit_button("儲存"):
            # 台斤換算：1台斤=600g
            real_g = w * 600 if u == "台斤" else w
            g_p = round(p / real_g, 4)
            
            new_row = pd.DataFrame([{"時間": pd.Timestamp.now().strftime("%Y-%m-%d"), "店家": shop, "項目": name, "總價": p, "重量": w, "單位": u, "每克成本": g_p}])
            
            # 合併並上傳
            res = pd.concat([df, new_row], ignore_index=True)
            conn.update(spreadsheet=URL, worksheet="Sheet1", data=res)
            st.success(f"存好了！{name} 每克 {g_p} 元")
            st.rerun()

with t2:
    if not items:
        st.info("請先去記帳，這裡才會有食材選單喔！")
    else:
        rows = st.number_input("食材種類數量", min_value=1, max_value=20, value=3)
        total = 0.0
        for i in range(int(rows)):
            col1, col2, col3 = st.columns([2, 1, 1])
            sel = col1.selectbox(f"食材 {i+1}", ["-選取-"] + items, key=f"s{i}")
            weight = col2.number_input(f"克數", min_value=0.0, key=f"w{i}")
            single_p = price_dict.get(sel, 0)
            sub = round(single_p * weight, 2)
            col3.write(f"小計: {sub}")
            total += sub
        st.divider()
        st.metric("總成本", f"${round(total, 1)}")
