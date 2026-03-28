import streamlit as st
import pandas as pd
import random
import re  # 用來處理文字遮罩的套件

# 設定網頁標題
st.set_page_config(page_title="抗生素學習與測驗系統", page_icon="💊")

st.title("🦠 藥理/微免 學習與測驗系統")
st.markdown("請上傳題庫，並選擇你要進行的學習模式！")

# 建立檔案上傳區塊
uploaded_file = st.file_uploader("📂 上傳 CSV 題庫 (需包含：菌種, 首選藥, 替代藥, 分類)", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # 清理空值，避免程式報錯
    df['首選藥'] = df['首選藥'].fillna('無')
    df['替代藥'] = df['替代藥'].fillna('無')
    
    # 防呆機制：如果忘記打分類，會自動補上提示文字
    if '分類' not in df.columns:
        df['分類'] = '無分類資訊'
    else:
        df['分類'] = df['分類'].fillna('無分類資訊')
        
    # 建立四大模式選單
    mode = st.radio("🔄 請選擇功能：", [
        "📖 學習卡 (Flashcards)", 
        "🎯 選擇題測驗 (Multiple Choice)", 
        "✍️ 拼寫測驗 (Typing)",
        "🔍 反向查詢 (給藥物 ➔ 猜細菌)"
    ])
    st.divider()

    bacteria_list = df['菌種'].tolist()
    # 抓出所有「不重複」的首選藥，用來做選擇題的選項
    unique_drugs = df['首選藥'].unique().tolist()
    if '無' in unique_drugs: 
        unique_drugs.remove('無') # 把"無"從選項裡剔除

    # ==========================================
    # 模式一：學習卡 (Flashcards)
    # ==========================================
    if mode == "📖 學習卡 (Flashcards)":
        st.header("📖 學習卡模式")
        st.caption("先別急著測驗，看看卡片建立記憶連結。")
        
        selected_bac = st.selectbox("🔍 請選擇要學習的細菌：", bacteria_list)
        
        # 狀態重置
        if 'flashcard_flip' not in st.session_state:
            st.session_state.flashcard_flip = False
        if 'last_flash_bac' not in st.session_state:
            st.session_state.last_flash_bac = selected_bac
            
        if selected_bac != st.session_state.last_flash_bac:
            st.session_state.flashcard_flip = False
            st.session_state.last_flash_bac = selected_bac

        row = df[df['菌種'] == selected_bac].iloc[0]

        # 顯示卡片正面 (細菌名)與分類提示
        st.info(f"### 🦠 {selected_bac}")
        st.caption(f"💡 分類提示：{row['分類']}")
        
        if st.button("🔄 翻轉卡片看藥物"):
            st.session_state.flashcard_flip = True
            
        # 顯示卡片背面 (藥物名)
        if st.session_state.flashcard_flip:
            st.success(f"**🏆 首選藥:** {row['首選藥']}")
            st.warning(f"**🛡️ 替代藥:** {row['替代藥']}")

    # ==========================================
    # 模式二：選擇題 (Multiple Choice)
    # ==========================================
    elif mode == "🎯 選擇題測驗 (Multiple Choice)":
        st.header("🎯 選擇題測驗")
        selected_bac = st.selectbox("🔍 請選擇題目 (細菌)：", bacteria_list)

        # 狀態管理：確保選項不會在點擊時一直亂跳
        if 'mc_options' not in st.session_state:
            st.session_state.mc_options = []
        if 'last_mc_bac' not in st.session_state:
            st.session_state.last_mc_bac = ""
        if 'mc_show_ans' not in st.session_state:
            st.session_state.mc_show_ans = False

        row = df[df['菌種'] == selected_bac].iloc[0]
        correct_drug = row['首選藥']

        # 如果換了題目，就重新生成四個不重複的選項
        if selected_bac != st.session_state.last_mc_bac:
            st.session_state.last_mc_bac = selected_bac
            st.session_state.mc_show_ans = False
            
            # 1. 把正確答案從清單拿掉，剩下的當作干擾選項
            other_drugs = [d for d in unique_drugs if d != correct_drug]
            # 2. 隨機抽 3 個錯的藥 (如果題庫太小不到3個，就全拿)
            sample_size = min(3, len(other_drugs))
            distractors = random.sample(other_drugs, sample_size)
            # 3. 把正確答案加進去，然後打亂順序
            options = distractors + [correct_drug]
            random.shuffle(options)
            st.session_state.mc_options = options

        st.subheader(f"請問 **{selected_bac}** 的首選藥是哪一個？")
        st.caption(f"💡 分類提示：{row['分類']}")
        
        user_choice = st.radio("👉 請選擇：", st.session_state.mc_options, index=None)

        if st.button("送出答案"):
            st.session_state.mc_show_ans = True

        if st.session_state.mc_show_ans:
            if user_choice == correct_drug:
                st.success("🎉 答對了！精準命中！")
            else:
                st.error(f"❌ 答錯囉。正確答案應該是：**{correct_drug}**")
            st.info(f"💡 順帶一提，這隻菌的替代藥是：{row['替代藥']}")

    # ==========================================
    # 模式三：拼寫測驗 (Typing)
    # ==========================================
    elif mode == "✍️ 拼寫測驗 (Typing)":
        st.header("✍️ 拼寫測驗")
        st.caption("期中考實戰演練，請精準拼出藥名。")
        
        selected_bac = st.selectbox("🔍 請選擇題目 (細菌)：", bacteria_list)

        # 狀態重置
        if 'type_show_ans' not in st.session_state:
            st.session_state.type_show_ans = False
        if 'last_type_bac' not in st.session_state:
            st.session_state.last_type_bac = selected_bac
            
        if selected_bac != st.session_state.last_type_bac:
            st.session_state.type_show_ans = False
            st.session_state.last_type_bac = selected_bac

        row = df[df['菌種'] == selected_bac].iloc[0]

        st.subheader(f"請拼出 **{selected_bac}** 的用藥")
        st.caption(f"💡 分類提示：{row['分類']}")
        
        # 🌟 產生字數與符號提示的功能 (例如 Ampicillin + GM 變成 ********** + **)
        def generate_hint(text):
            if str(text) == "無" or pd.isna(text):
                return "無"
            return re.sub(r'[a-zA-Z]', '*', str(text))
            
        hint_doc = generate_hint(row['首選藥'])
        hint_alt = generate_hint(row['替代藥'])
        
        # 顯示格式密碼提示框
        st.info(f"**🧩 格式密碼提示：**\n\n首選藥： `{hint_doc}`\n\n替代藥： `{hint_alt}`")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("✍️ 首選藥 (Drugs of choice)", key="doc_input")
        with col2:
            st.text_input("✍️ 替代藥 (Alternatives)", key="alt_input")
            
        if st.button("👁️ 看解答 / 對答案"):
            st.session_state.type_show_ans = True

        if st.session_state.type_show_ans:
            st.markdown("### 💡 標準答案：")
            st.success(f"🏆 **首選藥:** {row['首選藥']}")
            st.warning(f"🛡️ **替代藥:** {row['替代藥']}")
            
    # ==========================================
    # 模式四：反向查詢 (給藥物 ➔ 猜細菌) - 升級版
    # ==========================================
    elif mode == "🔍 反向查詢 (給藥物 ➔ 猜細菌)":
        st.header("🔍 反向查詢")
        st.caption("臨床實戰：只要用藥清單裡包含這顆藥，就會自動列出。")
        
        # 🌟 升級 1：自動拆解 Excel 裡的複合藥物，讓選單更乾淨
        all_drugs_raw = df['首選藥'].dropna().tolist()
        individual_drugs = []
        for drug_str in all_drugs_raw:
            # 依照你習慣的符號 (逗號、加號、斜線) 拆開成單顆藥名
            split_drugs = re.split(r'[,+/]', str(drug_str))
            individual_drugs.extend([d.strip() for d in split_drugs if d.strip() != "無"])
        
        # 取得不重複的單顆藥物清單供選擇
        unique_single_drugs = sorted(list(set(individual_drugs)))
        selected_drug = st.selectbox("💊 請選擇要測驗的單一藥物：", unique_single_drugs)
        
        # 狀態重置邏輯
        if 'rev_show_ans' not in st.session_state:
            st.session_state.rev_show_ans = False
        if 'last_rev_drug' not in st.session_state:
            st.session_state.last_rev_drug = selected_drug
            
        if selected_drug != st.session_state.last_rev_drug:
            st.session_state.rev_show_ans = False
            st.session_state.last_rev_drug = selected_drug

        st.subheader(f"請問哪些細菌的首選藥包含 **{selected_drug}**？")
        st.text_area("✍️ 請寫下你聯想到的細菌 (可寫多個)", key="rev_input")
            
        if st.button("👁️ 看解答 / 對答案"):
            st.session_state.rev_show_ans = True

        if st.session_state.rev_show_ans:
            st.markdown(f"### 💡 首選藥包含 **{selected_drug}** 的細菌有：")
            
            # 🌟 升級 2：改用 "contains" (包含)，只要格子裡有這顆藥就會被搜出來
            matching_rows = df[df['首選藥'].str.contains(re.escape(selected_drug), na=False)]
            
            if not matching_rows.empty:
                for index, row in matching_rows.iterrows():
                    st.success(f"🦠 **{row['菌種']}**\n\n(完整用藥：{row['首選藥']} | 提示：{row['分類']})")
            else:
                st.write("目前題庫中沒有對應的資料。")