import streamlit as st
import pandas as pd
import random
import re
import os

# 設定網頁標題
st.set_page_config(page_title="抗生素學習與測驗系統", page_icon="💊")

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
    # 清理空值，避免程式報錯
    df['首選藥'] = df['首選藥'].fillna('無')
    df['替代藥'] = df['替代藥'].fillna('無')
    
    if '分類' not in df.columns:
        df['分類'] = '無分類資訊'
    else:
        df['分類'] = df['分類'].fillna('無分類資訊')
        
    # 🌟 新增了第五個模式：模擬考
    mode = st.radio("🔄 請選擇功能：", [
        "📖 學習卡 (Flashcards)", 
        "🎯 選擇題測驗 (Multiple Choice)", 
        "✍️ 單題拼寫 (Typing)",
        "🔍 反向查詢 (給藥物 ➔ 猜細菌)",
        "🏆 全真模擬考 (Mock Exam)" 
    ])
    st.divider()

    bacteria_list = df['菌種'].tolist()
    
    unique_drugs = df['首選藥'].unique().tolist()
    if '無' in unique_drugs: unique_drugs.remove('無')
    
    unique_alts = df['替代藥'].unique().tolist()
    if '無' in unique_alts: unique_alts.remove('無')

    # 共用函數：產生字數與符號提示
    def generate_hint(text):
        if str(text) == "無" or pd.isna(text):
            return "無"
        return re.sub(r'[a-zA-Z]', '*', str(text))

    # ==========================================
    # 模式一：學習卡 (Flashcards)
    # ==========================================
    if mode == "📖 學習卡 (Flashcards)":
        st.header("📖 學習卡模式")
        
        selected_bac = st.selectbox("🔍 請選擇要學習的細菌：", bacteria_list)
        
        if 'flashcard_flip' not in st.session_state: st.session_state.flashcard_flip = False
        if 'last_flash_bac' not in st.session_state: st.session_state.last_flash_bac = selected_bac
            
        if selected_bac != st.session_state.last_flash_bac:
            st.session_state.flashcard_flip = False
            st.session_state.last_flash_bac = selected_bac

        row = df[df['菌種'] == selected_bac].iloc[0]
        st.info(f"### 🦠 {selected_bac}")
        st.caption(f"💡 分類提示：{row['分類']}")
        
        if st.button("🔄 翻轉卡片看藥物"): st.session_state.flashcard_flip = True
            
        if st.session_state.flashcard_flip:
            st.success(f"**🏆 首選藥:** {row['首選藥']}")
            st.warning(f"**🛡️ 替代藥:** {row['替代藥']}")

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
    # 模式三：單題拼寫測驗 (Typing)
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
        with col1: st.text_input("✍️ 首選藥", key="doc_input")
        with col2: st.text_input("✍️ 替代藥", key="alt_input")
            
        if st.button("👁️ 看解答 / 對答案"): st.session_state.type_show_ans = True

        if st.session_state.type_show_ans:
            st.markdown("### 💡 標準答案：")
            st.success(f"🏆 **首選藥:** {row['首選藥']}")
            st.warning(f"🛡️ **替代藥:** {row['替代藥']}")
            
    # ==========================================
    # 模式四：反向查詢 (給藥物 ➔ 猜細菌)
    # ==========================================
    elif mode == "🔍 反向查詢 (給藥物 ➔ 猜細菌)":
        st.header("🔍 反向查詢")
        
        all_drugs_raw = df['首選藥'].dropna().tolist()
        individual_drugs = []
        for drug_str in all_drugs_raw:
            individual_drugs.extend([d.strip() for d in re.split(r'[,+/]', str(drug_str)) if d.strip() != "無"])
        
        selected_drug = st.selectbox("💊 請選擇要測驗的單一藥物：", sorted(list(set(individual_drugs))))
        
        if 'rev_show_ans' not in st.session_state: st.session_state.rev_show_ans = False
        if 'last_rev_drug' not in st.session_state: st.session_state.last_rev_drug = selected_drug
            
        if selected_drug != st.session_state.last_rev_drug:
            st.session_state.rev_show_ans = False
            st.session_state.last_rev_drug = selected_drug

        st.subheader(f"請問哪些細菌的首選藥包含 **{selected_drug}**？")
        st.text_area("✍️ 請寫下你聯想到的細菌", key="rev_input")
            
        if st.button("👁️ 看解答 / 對答案"): st.session_state.rev_show_ans = True

        if st.session_state.rev_show_ans:
            st.markdown(f"### 💡 首選藥包含 **{selected_drug}** 的細菌有：")
            matching_rows = df[df['首選藥'].str.contains(re.escape(selected_drug), na=False)]
            if not matching_rows.empty:
                for _, row in matching_rows.iterrows():
                    st.success(f"🦠 **{row['菌種']}**\n\n(完整用藥：{row['首選藥']} | 提示：{row['分類']})")
            else: st.write("目前題庫中沒有對應的資料。")

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

                # 提交答案按鈕
                if not st.session_state.mock_show_ans:
                    if st.button("👁️ 提交答案 / 看解答"):
                        st.session_state.mock_show_ans = True
                        st.rerun()

                # 顯示解答與進入下一題的邏輯
                if st.session_state.mock_show_ans:
                    st.markdown("---")
                    st.markdown("### 💡 標準答案：")
                    st.success(f"🏆 **首選藥:** {correct_doc}")
                    st.warning(f"🛡️ **替代藥:** {correct_alt}")
                    
                    if st.button("➡️ 下一題", type="primary"):
                        st.session_state.mock_index += 1
                        st.session_state.mock_show_ans = False
                        st.session_state.mock_options_doc = [] # 清空選項，讓下一題重新生成
                        st.session_state.mock_options_alt = [] # 清空選項，讓下一題重新生成
                        st.rerun()
            else:
                # 所有題目做完的畫面
                st.progress(1.0)
                st.balloons() # 撒紙花慶祝
                st.success(f"🎉 太厲害了！你已經完成全部 {total_q} 題的模擬考！")
                
                if st.button("🔄 再挑戰一次"):
                    st.session_state.mock_active = False
                    st.rerun()rerun()
