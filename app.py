import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="餐飲成本智慧大師", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛡️ 料理成本智慧連動系統")

# --- 核心：讀取資料庫 ---
try:
    inventory_df = conn.read(worksheet="採買紀錄")
    # 建立食材單價字典 {項目名稱: 最新每克成本}
    price_dict = inventory_df.groupby('項目')['每克成本'].last().to_dict()
    item_list = sorted(list(price_dict.keys()))
except:
    st.warning("⚠️ 系統連動中...請確認『採買紀錄』分頁已有資料存入。")
    item_list = []
    price_dict = {}

tab1, tab2 = st.tabs(["🛒 採買記帳", "📊 菜單成本分析"])

# --- 分頁 1：採買記錄 (新增單位選擇) ---
with tab1:
    st.subheader("📝 新增採買紀錄")
    with st.form("purchase_form", clear_on_submit=True):
        col_shop, col_item = st.columns(2)
        shop = col_shop.text_input("採買店家")
        item = col_item.text_input("項目 (食材名稱)")
        
        col_p, col_w, col_u = st.columns([1.5, 1.5, 1])
        price = col_p.number_input("總價 (TWD)", min_value=0, step=1)
        input_weight = col_w.number_input("重量", min_value=0.01)
        unit = col_u.selectbox("單位", ["台斤", "公克 (g)"])
        
        if st.form_submit_button("🚀 送出並儲存"):
            # 換算逻辑：如果是台斤則乘上 600g
            actual_weight_g = input_weight * 600 if unit == "台斤" else input_weight
            unit_p_g = round(price / actual_weight_g, 4)
            
            new_row = pd.DataFrame([{
                "時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                "採買店家": shop,
                "項目": item,
                "總價": price,
                "輸入重量": input_weight,
                "單位": unit,
                "每克成本": unit_p_g
            }])
            
            existing = conn.read(worksheet="採買紀錄")
            updated = pd.concat([existing, new_row], ignore_index=True)
            conn.update(worksheet="採買紀錄", data=updated)
            st.success(f"✅ 已存入！換算每克成本為 ${unit_p_g}")
            st.rerun()

# --- 分頁 2：菜單成本分析 ---
with tab2:
    st.subheader("⚖️ 料理成本率與毛利計算")
    
    col_d, col_s = st.columns(2)
    dish_name = col_d.text_input("料理名稱", placeholder="例如：紅燒牛肉麵")
    sell_price = col_s.number_input("預計售價", min_value=0, step=1)

    st.write("---")
    st.markdown("**1. 食材組成 (從資料庫選取項目)**")
    
    if 'rows' not in st.session_state: st.session_state['rows'] = 3
    def add_row(): st.session_state['rows'] += 1

    total_food_cost = 0.0
    for i in range(st.session_state['rows']):
        c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
        sel = c1.selectbox(f"選擇食材 {i+1}", ["-- 請選擇 --"] + item_list, key=f"s_{i}")
        u_p = price_dict.get(sel, 0.0)
        c2.markdown(f"單價<br>**${u_p}**/g", unsafe_allow_html=True)
        # 料理時通常用公克計算，若需台斤可再告訴我
        u_w = c3.number_input(f"用量(g)", min_value=0.0, key=f"w_{i}")
        sub = round(u_p * u_w, 2)
        c4.markdown(f"小計<br>**${sub}**", unsafe_allow_html=True)
        total_food_cost += sub

    st.button("➕ 增加一種食材", on_click=add_row)

    st.write("---")
    # 經營數據分析
    total_cost = total_food_cost # 此處簡化，可再加雜支
    st.divider()
    if sell_price > 0:
        net = sell_price - total_cost
        margin = ((sell_price - total_cost) / sell_price) * 100
        cost_rate = (total_cost / sell_price) * 100
        
        r1, r2, r3 = st.columns(3)
        r1.metric("總食材成本", f"${round(total_cost, 1)}")
        r2.metric("預計淨利", f"${round(net, 1)}")
        r3.metric("毛利率", f"{round(margin, 1)}%")
        st.info(f"💡 目前成本率為：{round(cost_rate, 1)}%")
