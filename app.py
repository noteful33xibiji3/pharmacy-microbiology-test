import streamlit as st
import pandas as pd
import random
import re
import os

# 設定網頁標題
st.set_page_config(page_title="期中細菌與抗生素", page_icon="💊")

st.title("🦠 藥理/微免 學習與測驗系統")
st.markdown("請上傳題庫，並選擇你要進行的學習模式！")

# 1. 建立檔案上傳區塊
uploaded_file = st.file_uploader("📂 上傳 CSV 題庫 (需包含：菌種, 首選藥, 替代藥, 分類)", type=['csv'])

# 2. 自動讀取邏輯
df = None
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
elif os.path.exists("bacteria_test.csv"):
    df = pd.read_csv("bacteria_test.csv")
    st.info("ℹ️ 已自動載入預設題庫：bacteria_test.csv")

if df is not None:
    # 清理空值與換行符號，避免排版跑掉或程式報錯
    df['菌種'] = df['菌種'].astype(str).replace(r'[\n\r]', ' ', regex=True).str.strip()
    df['首選藥'] = df['首選藥'].fillna('無')
    df['替代藥'] = df['替代藥'].fillna('無')

    if '分類' not in df.columns:
        df['分類'] = '無分類資訊'
    else:
        df['分類'] = df['分類'].fillna('無分類資訊')

   # 🌟 移至側邊欄的選單設定
    st.sidebar.title("⚙️ 設定區")
    mode = st.sidebar.radio("🔄 請選擇測驗模式：", [
        "📖 學習卡 (Flashcards)", 
        "🎯 選擇題測驗 (Multiple Choice)", 
        "✍️ 單題拼寫 (Typing)",
        "🔍 反向查詢 (給藥物 ➔ 猜細菌)",
        "🏆 全真模擬考 (Mock Exam)",
        "📊 查看完整題庫 (Data Table)"
    ])
    st.divider()
    bacteria_list = df['菌種'].tolist()
    
    unique_drugs = df['首選藥'].unique().tolist()
    if '無' in unique_drugs: unique_drugs.remove('無')
    
    unique_alts = df['替代藥'].unique().tolist()
    if '無' in unique_alts: unique_alts.remove('無')

   # 原本的密碼提示函數
    def generate_hint(text):
        if str(text) == "無" or pd.isna(text):
            return "無"
        return re.sub(r'[a-zA-Z]', '*', str(text))

    # 🌟 新增：寬鬆對答案過濾器 (只保留英文字母和數字，且不分大小寫)
    def normalize_text(text):
        if pd.isna(text) or str(text) == "無": 
            return "無"
        return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()
  # ==========================================
    # 模式一：學習卡 (Flashcards) - 🌟 Quizlet 專業版
    # ==========================================
    if mode == "📖 學習卡 (Flashcards)":
        st.header("📖 學習卡模式")
        st.caption("就像 Quizlet 一樣！你可以連續翻頁、洗牌，還能設定正反面。")
        
        # Quizlet 核心功能：卡片設定
        col_set1, col_set2 = st.columns(2)
        with col_set1:
            fc_front = st.radio("🔄 卡片正面顯示：", ["🦠 菌種 (背藥物)", "💊 藥物 (背菌種)"])
        with col_set2:
            fc_order_type = st.radio("🔀 出牌順序：", ["循序播放", "隨機打亂"])

        # 初始化學習卡狀態
        if 'fc_order' not in st.session_state: st.session_state.fc_order = bacteria_list.copy()
        if 'fc_index' not in st.session_state: st.session_state.fc_index = 0
        if 'fc_flipped' not in st.session_state: st.session_state.fc_flipped = False
        if 'last_fc_order_type' not in st.session_state: st.session_state.last_fc_order_type = "循序播放"

        # 如果切換了洗牌/循序，就重新整理牌堆
        if fc_order_type != st.session_state.last_fc_order_type:
            st.session_state.last_fc_order_type = fc_order_type
            st.session_state.fc_index = 0
            st.session_state.fc_flipped = False
            if fc_order_type == "隨機打亂":
                shuffled = bacteria_list.copy()
                random.shuffle(shuffled)
                st.session_state.fc_order = shuffled
            else:
                st.session_state.fc_order = bacteria_list.copy()

        total_cards = len(st.session_state.fc_order)
        curr_fc_bac = st.session_state.fc_order[st.session_state.fc_index]
        row = df[df['菌種'] == curr_fc_bac].iloc[0]

        st.write(f"**📚 目前進度： 第 {st.session_state.fc_index + 1} 張 / 共 {total_cards} 張**")

        # 決定卡片正反面要顯示的文字
        if fc_front == "🦠 菌種 (背藥物)":
            front_text = f"### 🦠 {curr_fc_bac}\n\n*(提示：{row['分類']})*"
            back_text = f"### 🏆 **首選藥:** {row['首選藥']}\n\n#### 🛡️ **替代藥:** {row['替代藥']}"
        else:
            front_text = f"### 💊 {row['首選藥']}\n\n*(這是誰的首選藥？)*"
            back_text = f"### 🦠 **{curr_fc_bac}**\n\n*(提示：{row['分類']})*\n\n🛡️ 替代藥: {row['替代藥']}"

        # 顯示卡片 UI
        st.markdown("---")
        if not st.session_state.fc_flipped:
            st.info(front_text)  # 正面用藍色框
        else:
            st.success(back_text) # 背面用綠色框
        st.markdown("---")

        # 底部按鈕區：上一張、翻轉、下一張
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn1:
            if st.button("⬅️ 上一張", use_container_width=True):
                if st.session_state.fc_index > 0:
                    st.session_state.fc_index -= 1
                    st.session_state.fc_flipped = False
                    st.rerun()
                else:
                    st.toast("這已經是第一張囉！", icon="⚠️")
        with col_btn2:
            if st.button("🔄 翻轉卡片", use_container_width=True, type="primary"):
                st.session_state.fc_flipped = not st.session_state.fc_flipped
                st.rerun()
        with col_btn3:
            if st.button("下一張 ➡️", use_container_width=True):
                if st.session_state.fc_index < total_cards - 1:
                    st.session_state.fc_index += 1
                    st.session_state.fc_flipped = False
                    st.rerun()
                else:
                    st.toast("🎉 恭喜！卡片已經全部複習完畢！", icon="🎉")
    # ==========================================
    # 模式二：選擇題 (Multiple Choice)
    # ==========================================
    elif mode == "🎯 選擇題測驗 (Multiple Choice)":
        st.header("🎯 選擇題測驗")
        mc_target = st.radio("🎯 請選擇本次測驗目標：", ["首選藥", "替代藥", "兩者皆考 (綜合測驗)"], horizontal=True)
        selected_bac = st.selectbox("🔍 請選擇題目 (細菌)：", bacteria_list)

        if 'mc_options_doc' not in st.session_state: st.session_state.mc_options_doc = []
        if 'mc_options_alt' not in st.session_state: st.session_state.mc_options_alt = []
        if 'last_mc_bac' not in st.session_state: st.session_state.last_mc_bac = ""
        if 'last_mc_target' not in st.session_state: st.session_state.last_mc_target = ""
        if 'mc_show_ans' not in st.session_state: st.session_state.mc_show_ans = False

        row = df[df['菌種'] == selected_bac].iloc[0]
        correct_doc = row['首選藥']
        correct_alt = row['替代藥']

        if selected_bac != st.session_state.last_mc_bac or mc_target != st.session_state.last_mc_target:
            st.session_state.last_mc_bac = selected_bac
            st.session_state.last_mc_target = mc_target
            st.session_state.mc_show_ans = False
            
            other_docs = [d for d in unique_drugs if d != correct_doc]
            opts_doc = random.sample(other_docs, min(3, len(other_docs))) + [correct_doc]
            random.shuffle(opts_doc)
            st.session_state.mc_options_doc = opts_doc
            
            other_alts = [a for a in unique_alts if a != correct_alt]
            opts_alt = random.sample(other_alts, min(3, len(other_alts))) + [correct_alt]
            random.shuffle(opts_alt)
            st.session_state.mc_options_alt = opts_alt

        st.subheader(f"請問 **{selected_bac}** 的用藥是？")
        st.caption(f"💡 分類提示：{row['分類']}")
        
        user_choice_doc, user_choice_alt = None, None
        if mc_target in ["首選藥", "兩者皆考 (綜合測驗)"]:
            user_choice_doc = st.radio("👉 請選擇【首選藥】：", st.session_state.mc_options_doc, index=None, key="rad_doc")
        if mc_target in ["替代藥", "兩者皆考 (綜合測驗)"]:
            user_choice_alt = st.radio("👉 請選擇【替代藥】：", st.session_state.mc_options_alt, index=None, key="rad_alt")

        if st.button("送出答案"): st.session_state.mc_show_ans = True

        if st.session_state.mc_show_ans:
            st.markdown("---")
            if mc_target == "首選藥":
                if user_choice_doc == correct_doc: st.success("🎉 答對了！首選藥精準命中！")
                else: st.error(f"❌ 答錯囉。首選藥應該是：**{correct_doc}**")
                st.info(f"💡 順帶一提，這隻菌的替代藥是：{correct_alt}")
            elif mc_target == "替代藥":
                if user_choice_alt == correct_alt: st.success("🎉 答對了！替代藥精準命中！")
                else: st.error(f"❌ 答錯囉。替代藥應該是：**{correct_alt}**")
                st.info(f"💡 順帶一提，這隻菌的首選藥是：{correct_doc}")
            elif mc_target == "兩者皆考 (綜合測驗)":
                if user_choice_doc == correct_doc: st.success("🎉 首選藥：正確！")
                else: st.error(f"❌ 首選藥：錯誤 (正確為 **{correct_doc}**)")
                if user_choice_alt == correct_alt: st.success("🎉 替代藥：正確！")
                else: st.error(f"❌ 替代藥：錯誤 (正確為 **{correct_alt}**)")

    # ==========================================
    # 模式三：單題拼寫 (Typing) - 🌟 升級寬鬆批改系統
    # ==========================================
    elif mode == "✍️ 單題拼寫 (Typing)":
        st.header("✍️ 單題拼寫測驗")
        selected_bac = st.selectbox("🔍 請選擇題目 (細菌)：", bacteria_list)

        if 'type_show_ans' not in st.session_state: st.session_state.type_show_ans = False
        if 'last_type_bac' not in st.session_state: st.session_state.last_type_bac = selected_bac
            
        if selected_bac != st.session_state.last_type_bac:
            st.session_state.type_show_ans = False
            st.session_state.last_type_bac = selected_bac

        row = df[df['菌種'] == selected_bac].iloc[0]

        st.subheader(f"請拼出 **{selected_bac}** 的用藥")
        st.caption(f"💡 分類提示：{row['分類']}")
        
        st.info(f"**🧩 格式密碼提示：**\n\n首選藥： `{generate_hint(row['首選藥'])}`\n\n替代藥： `{generate_hint(row['替代藥'])}`")
        
        col1, col2 = st.columns(2)
        with col1: user_doc = st.text_input("✍️ 首選藥", key="doc_input")
        with col2: user_alt = st.text_input("✍️ 替代藥", key="alt_input")
            
        if st.button("👁️ 提交答案 / 看解答"): st.session_state.type_show_ans = True

        if st.session_state.type_show_ans:
            st.markdown("---")
            st.markdown("### 💡 批改結果：")
            
            # 🌟 使用 normalize_text 進行寬鬆比對
            if normalize_text(user_doc) == normalize_text(row['首選藥']):
                st.success(f"✅ **首選藥：正確！** (標準寫法: {row['首選藥']})")
            else:
                st.error(f"❌ **首選藥：錯誤。** (標準寫法: {row['首選藥']})")
                
            if normalize_text(user_alt) == normalize_text(row['替代藥']):
                st.success(f"✅ **替代藥：正確！** (標準寫法: {row['替代藥']})")
            else:
                st.error(f"❌ **替代藥：錯誤。** (標準寫法: {row['替代藥']})")
            
    # ==========================================
    # 模式四：反向查詢 (給藥物 ➔ 猜細菌) - 🌟 升級搜替代藥版
    # ==========================================
    elif mode == "🔍 反向查詢 (給藥物 ➔ 猜細菌)":
        st.header("🔍 反向查詢")
        
        # 🌟 升級 1：把首選藥和替代藥全部抓出來合併，製作更完整的下拉選單
        all_drugs_raw = df['首選藥'].dropna().tolist() + df['替代藥'].dropna().tolist()
        individual_drugs = []
        for drug_str in all_drugs_raw:
            individual_drugs.extend([d.strip() for d in re.split(r'[,+/]', str(drug_str)) if d.strip() != "無"])
        
        selected_drug = st.selectbox("💊 請選擇要測驗的單一藥物：", sorted(list(set(individual_drugs))))
        
        if 'rev_show_ans' not in st.session_state: st.session_state.rev_show_ans = False
        if 'last_rev_drug' not in st.session_state: st.session_state.last_rev_drug = selected_drug
            
        if selected_drug != st.session_state.last_rev_drug:
            st.session_state.rev_show_ans = False
            st.session_state.last_rev_drug = selected_drug

        st.subheader(f"請問哪些細菌的用藥 (包含首選與替代) 包含 **{selected_drug}**？")
        st.text_area("✍️ 請寫下你聯想到的細菌", key="rev_input")
            
        if st.button("👁️ 看解答 / 對答案"): st.session_state.rev_show_ans = True

        if st.session_state.rev_show_ans:
            st.markdown(f"### 💡 用藥包含 **{selected_drug}** 的細菌有：")
            
            # 🌟 升級 2：同時搜尋首選藥和替代藥的欄位
            mask_doc = df['首選藥'].str.contains(re.escape(selected_drug), na=False)
            mask_alt = df['替代藥'].str.contains(re.escape(selected_drug), na=False)
            matching_rows = df[mask_doc | mask_alt]
            
            if not matching_rows.empty:
                for _, row in matching_rows.iterrows():
                    # 判斷這顆藥是這隻菌的首選還是替代，讓顯示更清楚
                    is_doc = selected_drug in str(row['首選藥'])
                    is_alt = selected_drug in str(row['替代藥'])
                    
                    role_text = []
                    if is_doc: role_text.append("🏆 首選")
                    if is_alt: role_text.append("🛡️ 替代")
                    role_display = " & ".join(role_text)
                    
                    st.success(f"🦠 **{row['菌種']}** 【{role_display}】\n\n(首選：{row['首選藥']} | 替代：{row['替代藥']} | 提示：{row['分類']})")
            else: 
                st.write("目前題庫中沒有對應的資料。")

    # ==========================================
    # 模式五：全真模擬考 (Mock Exam) - 🌟 升級選擇/拼寫雙模式！
    # ==========================================
    elif mode == "🏆 全真模擬考 (Mock Exam)":
        st.header("🏆 全真模擬考")
        st.caption("系統將隨機打亂所有細菌，每隻細菌只考一次，快來挑戰全對吧！")

        # 🌟 新增：讓使用者選擇模擬考的題型
        mock_type = st.radio("📝 請選擇模擬考題型：", ["✍️ 拼寫測驗", "🎯 選擇題測驗"], horizontal=True)

        # 初始化模擬考的進度狀態
        if 'mock_active' not in st.session_state: st.session_state.mock_active = False
        if 'mock_order' not in st.session_state: st.session_state.mock_order = []
        if 'mock_index' not in st.session_state: st.session_state.mock_index = 0
        if 'mock_show_ans' not in st.session_state: st.session_state.mock_show_ans = False
        # 新增：紀錄模擬考選擇題的選項狀態
        if 'mock_options_doc' not in st.session_state: st.session_state.mock_options_doc = []
        if 'mock_options_alt' not in st.session_state: st.session_state.mock_options_alt = []

        # 如果還沒開始考試，顯示開始按鈕
        if not st.session_state.mock_active:
            if st.button("🚀 點我開始模擬考！", use_container_width=True):
                shuffled_bac = df['菌種'].tolist()
                random.shuffle(shuffled_bac)
                st.session_state.mock_order = shuffled_bac
                st.session_state.mock_index = 0
                st.session_state.mock_active = True
                st.session_state.mock_show_ans = False
                st.session_state.mock_options_doc = [] # 重置選項
                st.session_state.mock_options_alt = [] # 重置選項
                st.rerun() # 重新整理畫面進入第一題
        else:
            total_q = len(st.session_state.mock_order)
            curr_q = st.session_state.mock_index

            # 如果還沒考完
            if curr_q < total_q:
                st.progress((curr_q) / total_q)
                st.write(f"**📝 目前進度： 第 {curr_q + 1} 題 / 共 {total_q} 題**")
                
                current_bac = st.session_state.mock_order[curr_q]
                row = df[df['菌種'] == current_bac].iloc[0]
                correct_doc = row['首選藥']
                correct_alt = row['替代藥']

                st.subheader(f"請問 **{current_bac}** 的用藥是？")
                st.caption(f"💡 分類提示：{row['分類']}")
                
                # 🌟 根據選擇的題型顯示不同介面
                if mock_type == "✍️ 拼寫測驗":
                    st.info(f"**🧩 格式密碼提示：**\n\n首選藥： `{generate_hint(correct_doc)}`\n\n替代藥： `{generate_hint(correct_alt)}`")
                    col1, col2 = st.columns(2)
                    with col1: st.text_input("✍️ 首選藥", key=f"mock_doc_text_{curr_q}")
                    with col2: st.text_input("✍️ 替代藥", key=f"mock_alt_text_{curr_q}")
                
                else: # 🎯 選擇題測驗
                    # 如果這題還沒生成四選一選項，就生成一次
                    if not st.session_state.mock_options_doc:
                        other_docs = [d for d in unique_drugs if d != correct_doc]
                        opts_doc = random.sample(other_docs, min(3, len(other_docs))) + [correct_doc]
                        random.shuffle(opts_doc)
                        st.session_state.mock_options_doc = opts_doc
                        
                        other_alts = [a for a in unique_alts if a != correct_alt]
                        opts_alt = random.sample(other_alts, min(3, len(other_alts))) + [correct_alt]
                        random.shuffle(opts_alt)
                        st.session_state.mock_options_alt = opts_alt
                    
                    st.caption("提示：請在下方選出首選藥與替代藥")
                    col1, col2 = st.columns(2)
                    with col1: st.radio("👉 【首選藥】", st.session_state.mock_options_doc, index=None, key=f"mock_doc_rad_{curr_q}")
                    with col2: st.radio("👉 【替代藥】", st.session_state.mock_options_alt, index=None, key=f"mock_alt_rad_{curr_q}")

               # 顯示解答與進入下一題的邏輯
                if st.session_state.mock_show_ans:
                    st.markdown("---")
                    st.markdown("### 💡 批改結果：")
                    
                    # 🌟 針對拼寫測驗進行寬鬆比對
                    if mock_type == "✍️ 拼寫測驗":
                        user_doc = st.session_state.get(f"mock_doc_text_{curr_q}", "")
                        user_alt = st.session_state.get(f"mock_alt_text_{curr_q}", "")
                        
                        if normalize_text(user_doc) == normalize_text(correct_doc):
                            st.success(f"✅ **首選藥正確！** ({correct_doc})")
                        else:
                            st.error(f"❌ **首選藥錯誤。** 標準：{correct_doc}")
                            
                        if normalize_text(user_alt) == normalize_text(correct_alt):
                            st.success(f"✅ **替代藥正確！** ({correct_alt})")
                        else:
                            st.error(f"❌ **替代藥錯誤。** 標準：{correct_alt}")
                            
                    # 針對選擇題進行比對
                    else: 
                        user_doc = st.session_state.get(f"mock_doc_rad_{curr_q}")
                        user_alt = st.session_state.get(f"mock_alt_rad_{curr_q}")
                        
                        if user_doc == correct_doc:
                            st.success(f"✅ **首選藥正確！** ({correct_doc})")
                        else:
                            st.error(f"❌ **首選藥錯誤。** 標準：{correct_doc}")
                            
                        if user_alt == correct_alt:
                            st.success(f"✅ **替代藥正確！** ({correct_alt})")
                        else:
                            st.error(f"❌ **替代藥錯誤。** 標準：{correct_alt}")
                    
                    if st.button("➡️ 下一題", type="primary"):
                        st.session_state.mock_index += 1
                        st.session_state.mock_show_ans = False
                        st.session_state.mock_options_doc = [] 
                        st.session_state.mock_options_alt = [] 
                        st.rerun()
            else:
                # 所有題目做完的畫面
                st.progress(1.0)
                st.balloons() # 撒紙花慶祝
                st.success(f"🎉 太厲害了！你已經完成全部 {total_q} 題的模擬考！")
                
                if st.button("🔄 再挑戰一次"):
                    st.session_state.mock_active = False
                    st.rerun()
    # ==========================================
    # 模式六：查看完整題庫 (Data Table)
    # ==========================================
    elif mode == "📊 查看完整題庫 (Data Table)":
        st.header("📊 完整題庫一覽")
        st.caption("你可以在這裡總覽所有的細菌與用藥，點擊欄位標題可以進行排序。")

        # 顯示互動式資料表，隱藏最左邊的數字索引，並讓表格自動撐滿寬度
        st.dataframe(df, use_container_width=True, hide_index=True)
