import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="餐飲智慧成本大師", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛡️ 料理成本智慧連動系統")

# --- 核心：讀取資料庫食材與單價 ---
try:
    # 讀取採買紀錄分頁
    inventory_df = conn.read(worksheet="採買紀錄")
    # 依照日期排序，確保抓到的是最新價格
    inventory_df['日期'] = pd.to_datetime(inventory_df['日期'])
    # 建立食材單價字典 {食材名稱: 最新單價(g)}
    price_dict = inventory_df.sort_values('日期').groupby('食材名稱')['單價(每g)'].last().to_dict()
    item_list = sorted(list(price_dict.keys()))
except Exception as e:
    st.error("⚠️ 無法讀取資料庫，請確認試算表中有『採買紀錄』分頁且包含『食材名稱』與『單價(每g)』欄位。")
    item_list = []
    price_dict = {}

tab1, tab2 = st.tabs(["🛒 採買記帳", "📊 菜單成本分析"])

# --- 分頁 1：採買記錄 ---
with tab1:
    st.subheader("📝 新增採買紀錄")
    with st.form("purchase_form", clear_on_submit=True):
        item_name = st.text_input("食材名稱 (例如：豬梅花)")
        price = st.number_input("購買總價 (TWD)", min_value=0, step=1)
        weight = st.number_input("購買重量 (g)", min_value=1, step=1)
        if st.form_submit_button("🚀 送出並儲存"):
            unit_p = round(price/weight, 4)
            new_row = pd.DataFrame([{
                "日期": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                "食材名稱": item_name,
                "金額": price,
                "重量(g)": weight,
                "單價(每g)": unit_p
            }])
            existing = conn.read(worksheet="採買紀錄")
            updated = pd.concat([existing, new_row], ignore_index=True)
            conn.update(worksheet="採買紀錄", data=updated)
            st.success(f"✅ {item_name} 已存入！單價為 ${unit_p}/g")
            st.rerun()

# --- 分頁 2：菜單成本分析 (連動資料庫) ---
with tab2:
    st.subheader("⚖️ 料理成本率與毛利計算")
    
    col_dish, col_price = st.columns(2)
    dish_name = col_dish.text_input("料理名稱", placeholder="例如：紅燒牛肉麵")
    sell_price = col_price.number_input("預計售價 (元)", min_value=0, step=1)

    st.write("---")
    st.markdown("**1. 食材組成 (從資料庫自動帶入單價)**")
    
    # 使用 Session State 記錄目前的食材列數
    if 'ingredient_rows' not in st.session_state:
        st.session_state['ingredient_rows'] = 3

    def add_ingredient():
        st.session_state['ingredient_rows'] += 1

    total_food_cost = 0.0
    
    # 動態產生食材列
    for i in range(st.session_state['ingredient_rows']):
        c1, c2, c3, c4 = st.columns([2.5, 1.2, 1.2, 1])
        
        # 食材選擇 (下拉選單)
        sel_item = c1.selectbox(f"食材 {i+1}", ["-- 請選擇 --"] + item_list, key=f"item_{i}")
        
        # 自動顯示單價 (唯讀)
        unit_p = price_dict.get(sel_item, 0.0)
        c2.markdown(f"<small>單價</small><br>**${unit_p}**/g", unsafe_allow_html=True)
        
        # 輸入使用重量
        use_w = c3.number_input(f"重量(g)", min_value=0.0, step=1.0, key=f"w_{i}")
        
        # 計算小計
        sub_total = unit_p * use_w
        c4.markdown(f"<small>小計</small><br>**${round(sub_total, 1)}**", unsafe_allow_html=True)
        total_food_cost += sub_total

    st.button("➕ 增加一種食材", on_click=add_ingredient)

    st.write("---")
    
    # 2. 其他成本
    st.markdown("**2. 其他支出 (如包材、抽成)**")
    oc1, oc2, oc3 = st.columns([2, 2, 2])
    other_name = oc1.text_input("項目名稱", value="包材/水電", key="other_n")
    other_type = oc2.selectbox("計算方式", ["固定金額 (元)", "食材成本比例 (%)"])
    other_val = oc3.number_input("數值", min_value=0.0, key="other_v")

    calc_other_cost = other_val if other_type == "固定金額 (元)" else (total_food_cost * other_val / 100)
    total_cost = total_food_cost + calc_other_cost

    # 3. 數據分析
    st.divider()
    st.subheader("📊 經營分析數據")
    
    if sell_price > 0:
        net_profit = sell_price - total_cost
        # 毛利公式：(售價 - 食材成本) / 售價
        gross_margin = ((sell_price - total_food_cost) / sell_price) * 100
        # 成本率公式：總成本 / 售價
        cost_rate = (total_cost / sell_price) * 100
        
        res1, res2, res3 = st.columns(3)
        res1.metric("總成本 (含雜支)", f"${round(total_cost, 1)}")
        res2.metric("預計淨利", f"${round(net_profit, 1)}")
        res3.metric("毛利率", f"{round(gross_margin, 1)}%")
        
        if cost_rate > 40:
            st.error(f"⚠️ 警告：成本率高達 {round(cost_rate, 1)}% (建議低於 40%)")
        else:
            st.success(f"✅ 理想：成本率為 {round(cost_rate, 1)}%")
    else:
        st.info("請輸入售價以計算利潤分析")

    if st.button("💾 儲存此料理分析至雲端"):
        menu_row = pd.DataFrame([{
            "日期": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            "料理名稱": dish_name,
            "食材成本": round(total_food_cost, 2),
            "雜支成本": round(calc_other_cost, 2),
            "總成本": round(total_cost, 2),
            "預計售價": sell_price,
            "預計淨利": round(sell_price - total_cost, 2),
            "毛利率": f"{round(gross_margin, 1)}%" if sell_price > 0 else "0%"
        }])
        try:
            m_existing = conn.read(worksheet="菜單分析")
            m_updated = pd.concat([m_existing, menu_row], ignore_index=True)
        except:
            m_updated = menu_row
        conn.update(worksheet="菜單分析", data=m_updated)
        st.success(f"✅ 『{dish_name}』的成本結構已永久存入 Google 試算表！")
