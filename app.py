import streamlit as st
import pandas as pd

st.set_page_config(page_title="料理成本智慧系統", layout="wide")

# 直接使用 CSV 匯出連結，這是最穩定的讀取方式
SHEET_ID = "1dPuQ80Yudrym53l3h6FJygu2Yj_Y7fyfLBXNnFAEa4"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"

st.title("🛡️ 料理成本智慧系統")

# --- 讀取資料 ---
@st.cache_data(ttl=5) # 每 5 秒更新一次
def load_data():
    try:
        return pd.read_csv(CSV_URL)
    except:
        return pd.DataFrame()

df = load_data()

tab1, tab2 = st.tabs(["🛒 採買記帳", "📊 成本分析"])

with tab1:
    st.subheader("新增採買資料")
    with st.form("my_form"):
        name = st.text_input("食材名稱")
        price = st.number_input("總價 (元)", min_value=0)
        weight = st.number_input("重量", min_value=0.01)
        unit = st.selectbox("單位", ["台斤", "公克(g)"])
        
        if st.form_submit_button("計算成本"):
            # 換算
            real_g = weight * 600 if unit == "台斤" else weight
            cost_per_g = round(price / real_g, 4)
            st.success(f"✅ 計算成功！{name} 每克成本為：{cost_per_g} 元")
            st.info("💡 請手動將此資料填入您的試算表，系統即可在下一頁同步。")

with tab2:
    if df.empty or '項目' not in df.columns:
        st.warning("⚠️ 試算表內尚無資料，請確認 Sheet1 是否已有標題列（時間、採買店家、項目、總價、重量(g)、每克成本）。")
    else:
        st.subheader("分析食材成本")
        price_dict = df.groupby('項目')['每克成本'].last().to_dict()
        items = sorted(list(price_dict.keys()))
        
        sel_item = st.selectbox("選取食材", ["--請選擇--"] + items)
        if sel_item != "--請選擇--":
            u_p = price_dict.get(sel_item, 0)
            st.write(f"當前單價：${u_p} /g")
            u_w = st.number_input("預計用量 (g)", min_value=0.0)
            st.metric("本項成本小計", f"${round(u_p * u_w, 2)}")
