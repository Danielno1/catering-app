import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="餐飲成本智慧大師", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛡️ 料理成本智慧連動系統")

# --- 核心：根據您的試算表標題讀取資料 ---
try:
    inventory_df = conn.read(worksheet="採買紀錄")
    # 建立食材單價對照表，對應您的標題：【項目】與【每克成本】
    # 確保抓到的是最新單價
    price_dict = inventory_df.groupby('項目')['每克成本'].last().to_dict()
    item_list = sorted(list(price_dict.keys()))
except:
    st.warning("⚠️ 系統連動中...請確認『採買紀錄』分頁已有資料存入。")
    item_list = []
    price_dict = {}

tab1, tab2 = st.tabs(["🛒 採買記帳", "📊 菜單成本分析"])

# --- 分頁 1：採買記錄 (完全對應您的標題) ---
with tab1:
    st.subheader("📝 新增採買紀錄")
    with st.form("purchase_form", clear_on_submit=True):
        col_shop, col_item = st.columns(2)
        shop = col_shop.text_input("採買店家", placeholder="例如：南門市場")
        item = col_item.text_input("項目 (食材名稱)", placeholder="例如：豬梅花")
        
        col_p, col_w = st.columns(2)
        price = col_p.number_input("總價 (TWD)", min_value=0, step=1)
        weight = col_w.number_input("重量(g)", min_value=1, step=1)
        
        if st.form_submit_button("🚀 送出並儲存"):
            # 計算每克成本
            unit_p = round(price/weight, 4)
            new_row = pd.DataFrame([{
                "時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                "採買店家": shop,
                "項目": item,
                "總價": price,
                "重量(g)": weight,
                "每克成本": unit_p
            }])
            # 讀取並更新
            existing = conn.read(worksheet="採買紀錄")
            updated = pd.concat([existing, new_row], ignore_index=True)
            conn.update(worksheet="採買紀錄", data=updated)
            st.success(f"✅ 已存入！『{item}』每克成本為 ${unit_p}")
            st.rerun()

# --- 分頁 2：菜單成本分析 (無限新增食材版) ---
with tab2:
    st.subheader("⚖️ 料理成本率與毛利計算")
    
    col_d, col_s = st.columns(2)
    dish_name = col_d.text_input("料理名稱", placeholder="例如：招牌牛肉麵")
    sell_price = col_s.number_input("預計售價", min_value=0, step=1)

    st.write("---")
    st.markdown("**1. 食材組成 (自動連動資料庫單價)**")
    
    if 'rows' not in st.session_state: st.session_state['rows'] = 3
    def add_row(): st.session_state['rows'] += 1

    total_food_cost = 0.0
    for i in range(st.session_state['rows']):
        c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
        # 下拉選單
        sel = c1.selectbox(f"選擇食材 {i+1}", ["-- 請選擇 --"] + item_list, key=f"s_{i}")
        # 抓單價
        u_p = price_dict.get(sel, 0.0)
        c2.markdown(f"單價<br>**${u_p}**", unsafe_allow_html=True)
        # 填重量
        u_w = c3.number_input(f"重量(g)", min_value=0.0, key=f"w_{i}")
        # 小計
        sub = round(u_p * u_w, 2)
        c4.markdown(f"小計<br>**${sub}**", unsafe_allow_html=True)
        total_food_cost += sub

    st.button("➕ 增加一種食材", on_click=add_row)

    st.write("---")
    # 其他成本計算
    oc1, oc2 = st.columns(2)
    o_type = oc1.selectbox("其他支出", ["包材/瓦斯(固定金額)", "平台抽成(%)"])
    o_val = oc2.number_input("數值 ", min_value=0.0)
    o_cost = o_val if "固定" in o_type else (total_food_cost * o_val / 100)

    total_cost = total_food_cost + o_cost
    
    st.divider()
    if sell_price > 0:
        net = sell_price - total_cost
        margin = ((sell_price - total_food_cost) / sell_price) * 100
        r1, r2, r3 = st.columns(3)
        r1.metric("總成本", f"${round(total_cost, 1)}")
        r2.metric("淨利", f"${round(net, 1)}")
        r3.metric("毛利率", f"{round(margin, 1)}%")
