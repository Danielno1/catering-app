import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 設定頁面寬度與標題
st.set_page_config(page_title="餐飲成本助手", layout="wide")

# 連結 Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛡️ 餐飲成本與雲端助手")

# --- 使用標籤分頁 (這會在網頁最上方顯示按鈕，不用找側邊欄) ---
tab1, tab2 = st.tabs(["🛒 採買記帳", "⚖️ 菜單成本分析"])

# --- 分頁 1：採買記錄 ---
with tab1:
    st.subheader("📝 新增採買紀錄")
    with st.form("purchase_form"):
        item_name = st.text_input("食材項目", placeholder="例如：豬梅花")
        category = st.selectbox("分類", ["蔬菜", "肉類", "海鮮", "乾貨", "其他"])
        price = st.number_input("購買總價 (TWD)", min_value=0, step=1)
        weight = st.number_input("購買重量 (g)", min_value=1, step=1)
        
        if st.form_submit_button("🚀 送出並儲存"):
            new_row = pd.DataFrame([{
                "日期": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                "食材名稱": item_name,
                "金額": price,
                "重量(g)": weight,
                "單價(g)": round(price/weight, 4)
            }])
            existing = conn.read(worksheet="採買紀錄")
            updated = pd.concat([existing, new_row], ignore_index=True)
            conn.update(worksheet="採買紀錄", data=updated)
            st.success(f"已同步至試算表！單價為 ${round(price/weight, 2)}/g")

# --- 分頁 2：菜單成本分析 ---
with tab2:
    st.subheader("⚖️ 料理成本率與毛利計算")
    
    col_a, col_b = st.columns(2)
    dish_name = col_a.text_input("料理名稱", value="新產品")
    sell_price = col_b.number_input("預計售價", min_value=0, step=1)

    st.write("---")
    st.markdown("**1. 食材組成**")
    # 這裡設計兩個快速輸入區
    c1, c2, c3 = st.columns([2, 1, 1])
    ing1 = c1.text_input("食材1名稱", key="n1")
    w1 = c2.number_input("公克", min_value=0, key="w1")
    p1 = c3.number_input("單價($/g)", format="%.4f", key="p1")

    ing2 = c1.text_input("食材2名稱", key="n2")
    w2 = c2.number_input("公克 ", min_value=0, key="w2")
    p2 = c3.number_input("單價 ($/g)", format="%.4f", key="p2")

    st.write("---")
    st.markdown("**2. 其他成本**")
    other_name = st.text_input("其他項目名稱 (如包材)", value="水電包材")
    cost_mode = st.radio("計算方式", ["固定金額 (元)", "佔食材比 (%)"], horizontal=True)
    other_val = st.number_input("數值", min_value=0.0)

    # 計算邏輯
    food_cost = (w1 * p1) + (w2 * p2)
    other_cost = other_val if cost_mode == "固定金額 (元)" else (food_cost * other_val / 100)
    total_cost = food_cost + other_cost
    
    # 經營數據
    net_profit = sell_price - total_cost
    margin = ((sell_price - food_cost) / sell_price * 100) if sell_price > 0 else 0
    cost_rate = (total_cost / sell_price * 100) if sell_price > 0 else 0

    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("總成本", f"${round(total_cost, 1)}")
    res2.metric("淨利", f"${round(net_profit, 1)}")
    res3.metric("毛利率", f"{round(margin, 1)}%")
    
    st.info(f"💡 這道菜的成本率為：{round(cost_rate, 1)}%")

    if st.button("💾 儲存此料理分析"):
        menu_row = pd.DataFrame([{
            "料理名稱": dish_name,
            "總成本": total_cost,
            "售價": sell_price,
            "毛利率": f"{round(margin, 1)}%"
        }])
        try:
            m_existing = conn.read(worksheet="菜單分析")
            m_updated = pd.concat([m_existing, menu_row], ignore_index=True)
        except:
            m_updated = menu_row
        conn.update(worksheet="菜單分析", data=m_updated)
        st.success("分析結果已記錄！")
