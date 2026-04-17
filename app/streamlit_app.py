import streamlit as st

# --- 1. SETTINGS & STYLES ---
st.set_page_config(page_title="연인 갈등 대응 AI", layout="wide")


def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

        /* Base Style */
        html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #F8F9FA; }

        /* Top Navigation Bar */
        .top-bar {
            display: flex; justify-content: space-between; align-items: center;
            padding: 15px 25px; background: white; border-bottom: 1px solid #eee; margin-bottom: 20px;
        }
        .top-bar strong { font-size: 24px; color: #212529; font-weight: 700; }

        /* Chat Layout */
        .message-row { width: 100%; clear: both; margin-bottom: 20px; display: flex; align-items: flex-start; }
        .row-right { flex-direction: row-reverse; }
        .bubble {
            max-width: 75%; padding: 12px 18px; border-radius: 15px;
            font-size: 14px; line-height: 1.5; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }
        .bubble-left { border: 1px solid #DEE2E6; }
        .bubble-right { border: 2.5px solid #916848; } /* Slinky Dog Theme */
        .avatar { font-size: 25px; margin: 0 12px; }

        /* Analysis Cards & Gauge */
        .card {
            background: white; border-radius: 15px; padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center; border: 1px solid #f0f0f0;
        }
        .gauge-container { background: #E9ECEF; border-radius: 10px; height: 8px; width: 100%; margin-top: 10px; }
        .gauge-fill { height: 100%; border-radius: 10px; transition: width 0.5s ease-in-out; }

        /* List Items (Recommendations & History) */
        .list-item {
            display: flex; align-items: center; padding: 12px;
            background: white; border-radius: 12px; margin-bottom: 10px; border: 1px solid #eee;
        }
        .item-icon {
            background: #EDF2FF; color: #4C6EF5; width: 38px; height: 38px;
            display: flex; justify-content: center; align-items: center; border-radius: 10px; font-weight: 700;
        }
        .item-content { flex: 1; margin-left: 12px; font-size: 13.5px; }
        .active-history { background: #EDF2FF; border-color: #DBE4FF; }
        </style>
    """, unsafe_allow_html=True)


# --- 2. COMPONENTS (UI Reusable Parts) ---
def render_analysis_card(title, emoji, label, score, color):
    st.markdown(f"""
        <div class="card">
            <div style="color:#888; font-size:13px;">{title}</div>
            <div style="font-size:45px; margin:10px 0;">{emoji}</div>
            <div style="font-weight:700; font-size:20px; color:{color if title == '위험도 분석' else '#212529'};">{label}</div>
            <div style="font-size:12px; color:{color}; margin-top:5px;">신뢰도 {score}%</div>
            <div class="gauge-container"><div class="gauge-fill" style="width:{score}%; background:{color};"></div></div>
        </div>
    """, unsafe_allow_html=True)


def render_history_item(icon, title, time, preview, is_active=False):
    active_cls = "active-history" if is_active else ""
    title_color = "#4C6EF5" if is_active else "#333"
    st.markdown(f"""
        <div class="list-item {active_cls}">
            <div style="font-size:24px;">{icon}</div>
            <div class="item-content">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:700; color:{title_color};">{title}</span>
                    <span style="font-size:11px; color:#aaa;">{time}</span>
                </div>
                <div style="font-size:12px; color:#888; margin-top:2px;">{preview}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


# --- 3. MAIN APPLICATION LOGIC ---
def main():
    apply_custom_css()

    # Session State Initialization
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "avatar": "🍴",
             "content": "자주 보러 올게 꼭은 아니지만\n지켜보려 할게 시키지 않았지만\n또 놀러 올게 괜시리 눈물 나네\n이젠 정말 잘 있어!"}
        ]

    # Header
    st.markdown('<div class="top-bar"><strong>🎁 연인 갈등 상황 대응 답변 추천 AI</strong><span>⛶</span></div>',
                unsafe_allow_html=True)

    col_chat, col_report = st.columns([5.5, 4.5])

    # LEFT: Chat Interface
    with col_chat:
        st.markdown(
            '<div style="display:flex; justify-content:space-between; padding:0 10px 10px;"><span>〈 22</span><strong>Soap</strong><span>🔍 ☰</span></div>',
            unsafe_allow_html=True)

        with st.container(height=580):
            st.markdown(
                '<div style="text-align:center; margin-bottom:20px;"><span style="background:#E9ECEF; padding:5px 15px; border-radius:20px; font-size:12px; color:#868E96;">📅 Thursday, August 4, 2022</span></div>',
                unsafe_allow_html=True)
            for msg in st.session_state.messages:
                is_user = msg["role"] == "user"
                st.markdown(f"""
                    <div class="message-row {'row-right' if is_user else ''}">
                        <div class="avatar">{'🐶' if is_user else msg['avatar']}</div>
                        <div class="bubble {'bubble-right' if is_user else 'bubble-left'}">{msg['content'].replace('\\n', '<br>')}</div>
                    </div>
                """, unsafe_allow_html=True)

        if prompt := st.chat_input("메시지를 입력하세요..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

    # RIGHT: Intelligence Report
    with col_report:
        st.markdown("#### AI 분석 결과")
        card_l, card_r = st.columns(2)
        with card_l: render_analysis_card("감정 분석", "😡", "분노", 92, "#5C7CFA")
        with card_r: render_analysis_card("위험도 분석", "⏱️", "높음", 88, "#E74C3C")

        # Recommendations
        st.write("")
        st.markdown(
            "<div style='display:flex; justify-content:space-between;'><strong>💡 AI 추천 답변</strong><span style='font-size:12px; color:#aaa; cursor:pointer;'>↻ 새로고침</span></div>",
            unsafe_allow_html=True)
        recs = ["지금 화가 많이 난 것 같아. 무슨 일이 있었는지 이야기해줄래?",
                "내 마음이 이해돼. 잠시 숨을 고르고 천천히 이야기해보자.",
                "그런 일이 있어서 속상했겠네. 내가 들어줄게."]
        for i, text in enumerate(recs, 1):
            st.markdown(
                f'<div class="list-item"><div class="item-icon">{i}</div><div class="item-content">{text}</div><div style="color:#ccc;">❐</div></div>',
                unsafe_allow_html=True)

        # History
        st.write("")
        st.markdown(
            "<div style='display:flex; justify-content:space-between;'><strong>대화 히스토리 (최근 3개)</strong><span style='font-size:12px; color:#aaa; cursor:pointer;'>전체보기</span></div>",
            unsafe_allow_html=True)
        render_history_item("🐶", "Lose you to love me / Blind", "04:31 AM", "Soap 답변: 자주 보러 올게...", True)
        render_history_item("🍴", "I hate everything today", "어제 11:20 PM", "Soap 답변 확인하기...", False)
        render_history_item("💬", "우리 어제 싸운 거 말이야", "2일 전", "지난 대화 분석 완료", False)


if __name__ == "__main__":
    main()