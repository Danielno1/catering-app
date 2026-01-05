import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 設定頁面資訊
st.set_page_config(page_title="餐飲成本雲端助理", layout="wide")

# 建立分頁選單
page = st.sidebar.selectbox("切換功能", ["🛒 採買記錄", "📊 菜單成本分析"])

# 連結 Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 功能 1：採買記錄 ---
if page == "🛒 採買記錄":
    st.title("🛒 採買記錄系統")
    
    with st.form("purchase_form"):
        item_name = st.text_input("食材名稱")
        category = st.selectbox("類別", ["蔬菜", "肉類", "海鮮", "乾貨", "雜項"])
        price = st.number_input("購買總金額 (元)", min_value=0)
        weight = st.number_input("重量 (公克)", min_value=1)
        
        submit = st.form_submit_button("送出採買紀錄")
        
        if submit:
            new_data = pd.DataFrame([{
                "日期": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                "食材名稱": item_name,
                "類別": category,
                "金額": price,
                "重量(g)": weight,
                "單價(每g)": round(price/weight, 4)
            }])
            # 讀取舊資料並合併
            existing_data = conn.read(worksheet="採買紀錄")
            updated_df = pd.concat([existing_data, new_data], ignore_index=True)
            conn.update(worksheet="採買紀錄", data=updated_df)
            st.success(f"✅ 已存入試算表：{item_name}")

# --- 功能 2：菜單成本分析 ---
elif page == "📊 菜單成本分析":
    st.title("⚖️ 料理成本與利潤計算")
    
    with st.expander("第一步：設定料理與食材", expanded=True):
        dish_name = st.text_input("料理名稱", placeholder="例如：紅燒牛肉麵")
        
        # 動態增加食材 (此處簡化為三項，可視需求擴充)
        st.write("--- 食材組成 ---")
        col1, col2, col3 = st.columns([2, 1, 1])
        ing1 = col1.text_input("食材 1 名稱")
        w1 = col2.number_input("食材 1 公克", min_value=0, key="w1")
        p1 = col3.number_input("食材 1 單價(元/g)", min_value=0.0, format="%.4f", key="p1")
        
        ing2 = col1.text_input("食材 2 名稱")
        w2 = col2.number_input("食材 2 公克", min_value=0, key="w2")
        p2 = col3.number_input("食材 2 單價(元/g)", min_value=0.0, format="%.4f", key="p2")
        
        food_cost = (w1 * p1) + (w2 * p2)
        st.info(f"目前食材總成本：{round(food_cost, 2)} 元")

    with st.expander("第二步：其他成本與定價"):
        other_name = st.text_input("其他成本名稱", value="包材/水電")
        other_type = st.radio("其他成本計算方式", ["固定金額 (元)", "比例 (%)"])
        other_value = st.number_input("輸入金額或百分比", min_value=0.0)
        
        sell_price = st.number_input("預計售價 (元)", min_value=1)

    # 計算邏輯
    final_other_cost = other_value if other_type == "固定金額 (元)" else (food_cost * other_value / 100)
    total_cost = food_cost + final_other_cost
    net_profit = sell_price - total_cost
    gross_margin = (sell_price - food_cost) / sell_price * 100 if sell_price > 0 else 0
    cost_rate = (total_cost / sell_price) * 100 if sell_price > 0 else 0

    # 顯示分析結果
    st.subheader("📈 分析結果")
    c1, c2, c3 = st.columns(3)
    c1.metric("總成本", f"${round(total_cost, 1)}")
    c2.metric("淨利", f"${round(net_profit, 1)}")
    c3.metric("毛利率", f"{round(gross_margin, 1)}%")
    
    st.write(f"📊 **成本率：{round(cost_rate, 1)}%**")

    if st.button("💾 儲存此菜單分析"):
        menu_data = pd.DataFrame([{
            "日期": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            "料理名稱": dish_name,
            "食材成本": food_cost,
            "其他成本": final_other_cost,
            "總成本": total_cost,
            "售價": sell_price,
            "淨利": net_profit,
            "毛利率": f"{round(gross_margin, 1)}%"
        }])
        # 讀取或建立「菜單分析」分頁
        try:
            menu_existing = conn.read(worksheet="菜單分析")
            updated_menu = pd.concat([menu_existing, menu_data], ignore_index=True)
        except:
            updated_menu = menu_data
            
        conn.update(worksheet="菜單分析", data=updated_menu)
        st.success(f"✅ {dish_name} 的成本分析已存入試算表！")
