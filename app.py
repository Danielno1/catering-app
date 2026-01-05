import streamlit as st
import pandas as pd

st.set_page_config(page_title="料理成本智慧系統", layout="wide")

# 試算表 ID
SHEET_ID = "1dPuQ80Yudrym53l3h6FJygu2Yj_Y7fyfLBXNnFAEa4"
# 使用 CSV 格式讀取 Sheet1
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"

st.title("🛡️ 料理成本智慧系統")

# --- 讀取資料 ---
@st.cache_data(ttl=5)
def load_data():
    try:
        return pd.read_csv(CSV_URL)
    except:
        return pd.DataFrame()

df = load_data()

tab1, tab2 = st.tabs(["🛒 採買記帳", "📊 成本分析"])

with tab1:
    st.subheader("📝 成本快速計算器")
    with st.form("purchase_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        shop = col1.text_input("採買店家 (例如：貴吉、全聯)")
        name = col2.text_input("食材項目 (例如：豬肉絲)")
        
        col3, col4, col5 = st.columns([1, 1, 1])
        price = col3.number_input("總價 (元)", min_value=0, step=1)
        weight = col4.number_input("購買重量", min_value=0.01, step=0.01)
        unit = col5.selectbox("單位", ["台斤", "公克(g)"])
        
        if st.form_submit_button("⚖️ 開始換算"):
            if not name:
                st.error("⚠️ 請輸入食材項目名稱！")
            else:
                # 台斤換算：1台斤 = 600g
                real_g = weight * 600 if unit == "台斤" else weight
                cost_per_g = round(price / real_g, 4)
                
                st.success(f"✅ 計算成功！")
                # 重新顯示採買店家
                st.markdown(f"""
                ### 📋 換算結果
                * **採買來源：** {shop if shop else '未填寫'}
                * **食材項目：** {name}
                * **實際重量：** {real_g} g
                * **💰 每克成本：** :red[**${cost_per_g}**] 元
                """)
                st.warning("💡 請將此數據填入您的試算表，『成本分析』頁面將自動同步。")

with tab2:
    if df.empty or '項目' not in df.columns:
        st.warning("⚠️ 試算表目前是空的。請確保您的試算表第一行標題包含：時間, 採買店家, 項目, 總價, 重量(g), 每克成本")
    else:
        st.subheader("📊 雲端單價庫")
        st.dataframe(df[['採買店家', '項目', '每克成本']].tail(10), use_container_width=True)
        
        st.divider()
        st.subheader("⚖️ 料理配方試算")
        
        price_dict = df.groupby('項目')['每克成本'].last().to_dict()
        items = sorted(list(price_dict.keys()))
        
        sel_item = st.selectbox("請選擇食材", ["--請選擇--"] + items)
        if sel_item != "--請選擇--":
            u_p = price_dict.get(sel_item, 0)
            st.write(f"🔹 **{sel_item}** 紀錄單價: `${u_p}` /g")
            use_w = st.number_input("用量 (g)", min_value=0.0, step=1.0)
            if use_w > 0:
                st.metric("成本小計", f"${round(u_p * use_w, 2)} 元")
