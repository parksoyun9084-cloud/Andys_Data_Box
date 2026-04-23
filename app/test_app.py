import sys
from pathlib import Path
import streamlit as st

# 프로젝트 루트를 import 경로에 추가
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.app_service import run_chat_analysis

st.set_page_config(page_title="연인 갈등 대응 AI", layout="wide")


@st.cache_data(ttl=600, show_spinner=False)
def cached_analysis(prompt: str):
    return run_chat_analysis(prompt)


def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', sans-serif;
            background-color: #F8F9FA;
        }

        .block-container{
            padding-top:1rem;
            padding-bottom:1rem;
        }

        .top-bar {
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding:15px 25px;
            background:#FFF0F3;
            border-bottom:1px solid #eee;
            margin-bottom:20px;
            border-radius:12px;
        }

        .top-bar strong {
            font-size:24px;
            color:#212529;
            font-weight:700;
        }

        .section-title {
            font-size:18px;
            font-weight:700;
            margin-bottom:12px;
        }

        .chat-shell{
            background:#ffffff;
            border-radius:22px;
            padding:16px;
            border:1px solid #ECEDEF;
            box-shadow:0 4px 14px rgba(0,0,0,0.04);
        }

        .assistant-card{
            background:#F3F4F6;
            border-radius:22px;
            padding:18px;
            border:1px solid #ECEDEF;
            margin-bottom:14px;
        }

        .assistant-head{
            display:flex;
            align-items:center;
            gap:10px;
        }

        .assistant-avatar{
            font-size:30px;
        }

        .assistant-name{
            font-size:18px;
            font-weight:800;
            color:#191919;
        }

        .assistant-desc{
            font-size:14px;
            color:#666;
            line-height:1.7;
            margin-top:3px;
        }

        .selected-mode-badge{
            display:inline-block;
            padding:7px 14px;
            border-radius:999px;
            background:#EFEAFE;
            color:#6F42C1;
            font-size:13px;
            font-weight:700;
            margin-bottom:10px;
        }

        .message-row {
            width:100%;
            clear:both;
            margin-bottom:18px;
            display:flex;
            align-items:flex-start;
        }

        .row-right {
            flex-direction:row-reverse;
        }

        .bubble {
            max-width:78%;
            padding:12px 18px;
            border-radius:18px;
            font-size:14px;
            line-height:1.65;
            background:white;
            box-shadow:0 2px 5px rgba(0,0,0,0.02);
            white-space:pre-wrap;
        }

        .bubble-left {
            border:1px solid #DEE2E6;
            color:#000;
            background:#F7F7F8;
        }

        .bubble-right {
            border:2px solid #916848;
            background:#FFFDF9;
            color:#000;
        }

        .avatar {
            font-size:25px;
            margin:0 12px;
        }

        .card {
            background:white;
            border-radius:15px;
            padding:20px;
            box-shadow:0 4px 12px rgba(0,0,0,0.05);
            text-align:center;
            border:1px solid #f0f0f0;
            min-height:180px;
        }

        .gauge-container {
            background:#E9ECEF;
            border-radius:10px;
            height:8px;
            width:100%;
            margin-top:10px;
        }

        .gauge-fill {
            height:100%;
            border-radius:10px;
            transition:width 0.5s ease-in-out;
        }

        .list-item {
            display:flex;
            align-items:flex-start;
            padding:12px;
            background:white;
            border-radius:12px;
            margin-bottom:10px;
            border:1px solid #eee;
            position:relative;
        }

        .item-icon {
            background:#EDF2FF;
            color:#4C6EF5;
            width:38px;
            height:38px;
            display:flex;
            justify-content:center;
            align-items:center;
            border-radius:10px;
            font-weight:700;
            flex-shrink:0;
        }

        .item-content {
            flex:1;
            margin-left:12px;
            font-size:13.5px;
            line-height:1.6;
            color:#333;
            padding-right:50px;
        }

        .copy-button {
            position:absolute;
            right:12px;
            top:50%;
            transform:translateY(-50%);
            background:#f1f3f5;
            border:1px solid #dee2e6;
            border-radius:6px;
            padding:4px 8px;
            font-size:11px;
            cursor:pointer;
            color:#495057;
        }

        .copy-button:hover{
            background:#e9ecef;
        }

        .active-history {
            background:#EDF2FF;
            border-color:#DBE4FF;
        }

        .sub-card {
            background:white;
            border:1px solid #eee;
            border-radius:12px;
            padding:14px;
            margin-bottom:10px;
        }

        .small-label {
            font-size:12px;
            color:#888;
            margin-bottom:6px;
        }

        .note-box {
            background:#FFFFFF;
            border:1px dashed #D0D7DE;
            border-radius:12px;
            padding:12px 14px;
            font-size:13px;
            color:#555;
            line-height:1.6;
        }

        div[data-testid="stButton"] > button{
            width:100%;
            border-radius:999px;
            border:1px solid #DDD6FE;
            background:white;
            color:#6F42C1;
            font-weight:700;
            min-height:44px;
        }

        div[data-testid="stButton"] > button:hover{
            border-color:#B197FC;
            background:#F8F5FF;
            color:#5F3DC4;
        }
        </style>

        <script>
        function copyToClipboard(text) {
            const tempTextArea = document.createElement('textarea');
            tempTextArea.value = text.replace(/<br>/g, '\\n');
            document.body.appendChild(tempTextArea);
            tempTextArea.select();
            document.execCommand('copy');
            document.body.removeChild(tempTextArea);
            alert('답변이 클립보드에 복사되었습니다.');
        }
        </script>
    """, unsafe_allow_html=True)


def clean_display_text(text: str) -> str:
    if not text:
        return ""
    text = str(text).strip().strip('"').strip("'")
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()
    return text


def render_analysis_card(title: str, emoji: str, label: str, score: int, color: str, description: str = ""):
    safe_label = clean_display_text(label)
    safe_desc = clean_display_text(description)

    st.markdown(f"""
        <div class="card">
            <div style="color:#888; font-size:13px;">{title}</div>
            <div style="font-size:45px; margin:10px 0;">{emoji}</div>
            <div style="font-weight:700; font-size:20px; color:{color if title == '위험도 분석' else '#212529'};">
                {safe_label}
            </div>
            <div style="font-size:12px; color:{color}; margin-top:5px;">신뢰도 {score}%</div>
            <div class="gauge-container">
                <div class="gauge-fill" style="width:{score}%; background:{color};"></div>
            </div>
            <div style="font-size:12px; color:#868E96; margin-top:10px; line-height:1.5;">
                {safe_desc}
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_history_item(icon: str, title: str, time_text: str, preview: str, is_active=False):
    active_cls = "active-history" if is_active else ""
    title_color = "#4C6EF5" if is_active else "#333"

    st.markdown(f"""
        <div class="list-item {active_cls}">
            <div style="font-size:24px;">{icon}</div>
            <div class="item-content">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:700; color:{title_color};">{title}</span>
                    <span style="font-size:11px; color:#aaa;">{time_text}</span>
                </div>
                <div style="font-size:12px; color:#888; margin-top:2px;">{preview}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_text_box(title: str, body: str):
    st.markdown(f"""
        <div class="sub-card">
            <div class="small-label">{title}</div>
            <div style="font-size:13.5px; line-height:1.65; color:#333;">{clean_display_text(body)}</div>
        </div>
    """, unsafe_allow_html=True)


def render_phrase_box(title: str, items: list[str], empty_text: str):
    if not items:
        render_text_box(title, empty_text)
        return
    for item in items:
        render_text_box(title, item)


def get_risk_color(label: str) -> str:
    if label in ["심각", "위험"]:
        return "#E74C3C"
    if label in ["경고", "주의", "보통"]:
        return "#F08C00"
    return "#5C7CFA"


def get_emotion_emoji(label: str) -> str:
    mapping = {
        "분노": "😡", "슬픔": "😢", "혐오": "😖", "공포": "😨", "행복": "😊",
        "놀람": "😮", "중립": "😐", "상처": "😢", "불안": "😟", "서운함": "😢"
    }
    return mapping.get(label, "🙂")


def get_risk_description(label: str) -> str:
    mapping = {
        "안전": "감정이 크게 격화된 상태는 아닙니다.",
        "주의": "표현 방식에 따라 갈등이 커질 수 있습니다.",
        "경고": "감정 충돌 가능성이 있어 부드러운 표현이 중요합니다.",
        "위험": "자극적인 표현을 피하고 감정 진정이 우선입니다.",
        "심각": "즉각적인 설득보다 상황 진정이 더 중요합니다.",
        "보통": "표현을 조심하면 충분히 대화를 이어갈 수 있습니다.",
    }
    return mapping.get(label, "현재 대화 흐름을 조심스럽게 이어가는 것이 좋습니다.")


def get_emotion_description(label: str) -> str:
    mapping = {
        "분노": "억울함이나 답답함이 함께 섞여 있을 수 있습니다.",
        "슬픔": "서운함, 상처, 외로움이 함께 나타날 수 있습니다.",
        "중립": "감정이 비교적 안정적인 상태입니다.",
        "상처": "정서적으로 마음이 상한 상태에 가깝습니다.",
        "불안": "관계 변화나 반응에 대한 걱정이 섞여 있을 수 있습니다.",
        "서운함": "기대와 다른 반응에서 오는 아쉬움이 큽니다.",
    }
    return mapping.get(label, "현재 감정 흐름을 참고해 대화를 조절하는 것이 좋습니다.")


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "avatar": "🎁",
            "content": "안녕하세요.\nAI 채팅상담입니다.\n\n연인관계 갈등 유형을 먼저 선택한 뒤, 상황을 입력해 주세요."
        }]
    if "latest_result" not in st.session_state:
        st.session_state.latest_result = None
    if "history" not in st.session_state:
        st.session_state.history = []
    if "error_message" not in st.session_state:
        st.session_state.error_message = ""
    if "last_prompt" not in st.session_state:
        st.session_state.last_prompt = ""
    if "conflict_type" not in st.session_state:
        st.session_state.conflict_type = "연락 문제 > 답장 지연 > 서운함"


def set_conflict_type(v):
    st.session_state.conflict_type = v


def build_analysis_prompt(user_prompt: str, conflict_type: str):
    return f"""
연인 관계 고민입니다.
반드시 연인/커플/애인 갈등으로 해석하세요.
현재 갈등유형: {conflict_type}
이 갈등유형을 우선 반영해서 분석하세요.
사용자 입력: {user_prompt}
"""


def render_quick_conflict_buttons():
    st.markdown(
        f'<div class="selected-mode-badge">현재 선택: {st.session_state.conflict_type}</div>',
        unsafe_allow_html=True
    )

    major = st.selectbox(
        "어떤 고민인가요?",
        [
            "연락 문제",
            "감정 표현",
            "신뢰 문제",
            "생활 습관",
            "이별 위기",
            "화해/재회"
        ],
        key="major_type"
    )

    middle_map = {
        "연락 문제": ["답장 지연", "읽씹", "연락 빈도", "잠수"],
        "감정 표현": ["서운함", "말투", "무시당함", "공감 부족"],
        "신뢰 문제": ["거짓말", "이성 문제", "의심", "비밀"],
        "생활 습관": ["시간 약속", "돈 문제", "청소", "게임/술"],
        "이별 위기": ["헤어지자 함", "지침", "권태기", "거리두기"],
        "화해/재회": ["사과법", "다시 연락", "화해 대화", "재회 고민"]
    }

    middle = st.selectbox(
        "조금 더 자세히 골라주세요",
        middle_map[major],
        key="middle_type"
    )

    final_type = f"{major} > {middle}"

    if st.button("갈등유형 선택 완료"):
        set_conflict_type(final_type)
        st.rerun()


def main():
    apply_custom_css()
    init_session_state()

    st.markdown(
        '<div class="top-bar"><strong>🎁 연인 갈등 상황 대응 답변 추천 AI</strong><span>👩🏻‍❤️‍🧑🏻</span></div>',
        unsafe_allow_html=True
    )

    col_chat, col_report = st.columns([1.05, 1])

    with col_chat:
        st.markdown('<div class="chat-shell">', unsafe_allow_html=True)

        with st.container(height=550):

            for idx, msg in enumerate(st.session_state.messages):
                is_user = msg["role"] == "user"
                avatar = "👩🏻‍❤️‍🧑🏻" if is_user else msg.get("avatar", "🎁")
                bubble_class = "bubble-right" if is_user else "bubble-left"
                row_class = "row-right" if is_user else ""
                content = clean_display_text(msg["content"]).replace("\n", "<br>")

                st.markdown(f"""
                    <div class="message-row {row_class}">
                        <div class="avatar">{avatar}</div>
                        <div class="bubble {bubble_class}">{content}</div>
                    </div>
                """, unsafe_allow_html=True)

                # 첫 안내 메시지 바로 아래에 버튼 배치
                if idx == 0:
                    render_quick_conflict_buttons()

        st.markdown('</div>', unsafe_allow_html=True)

        placeholder = f"[{st.session_state.conflict_type}] 현재 상황을 입력해주세요."

        if prompt := st.chat_input(placeholder):
            prompt = prompt.strip()

            if not prompt:
                st.stop()

            dedupe = f"{st.session_state.conflict_type}::{prompt}"
            if dedupe == st.session_state.last_prompt:
                st.info("같은 입력은 다시 분석하지 않았어요.")
                st.stop()

            st.session_state.last_prompt = dedupe
            st.session_state.error_message = ""
            st.session_state.messages.append({"role": "user", "content": prompt})

            try:
                analysis_prompt = build_analysis_prompt(prompt, st.session_state.conflict_type)

                with st.spinner("분석 중..."):
                    result = cached_analysis(analysis_prompt)

                result["user_input"] = prompt
                result["conflict_type"] = st.session_state.conflict_type

                st.session_state.latest_result = result
                st.session_state.messages.append({
                    "role": "assistant",
                    "avatar": "🎁",
                    "content": clean_display_text(result["assistant_message"])
                })
                st.session_state.history.insert(0, result)

            except Exception as e:
                st.session_state.error_message = str(e)
                st.session_state.messages.append({
                    "role": "assistant",
                    "avatar": "🎁",
                    "content": "분석 중 오류가 발생했어. 설정을 확인해줘."
                })

            st.rerun()

    with col_report:
        st.markdown('<div class="section-title">AI 분석 결과</div>', unsafe_allow_html=True)

        with st.container(height=760):
            latest = st.session_state.latest_result

            emotion_label, emotion_score, emotion_emoji, emotion_desc = "대기 중", 0, "🙂", "입력 시 분석을 시작합니다."
            risk_label, risk_score, risk_color, risk_desc = "대기 중", 0, "#ADB5BD", "갈등 위험도를 측정합니다."

            if latest:
                emotion_label = clean_display_text(latest["emotion"]["label"])
                emotion_score = latest["emotion"]["score"]
                emotion_emoji = get_emotion_emoji(emotion_label)
                emotion_desc = get_emotion_description(emotion_label)

                risk_label = clean_display_text(latest["risk"]["label"])
                risk_score = latest["risk"]["score"]
                risk_color = get_risk_color(risk_label)
                risk_desc = get_risk_description(risk_label)

            c1, c2 = st.columns(2)
            with c1:
                render_analysis_card("감정 분석", emotion_emoji, emotion_label, emotion_score, "#5C7CFA", emotion_desc)
            with c2:
                render_analysis_card("위험도 분석", "⏱️", risk_label, risk_score, risk_color, risk_desc)

            if st.session_state.error_message:
                st.error(st.session_state.error_message)

            st.markdown("<strong>입력 메시지 분석</strong>", unsafe_allow_html=True)

            if latest:
                render_text_box("갈등유형", latest.get("conflict_type", "미선택"))
                render_text_box("상황 요약", latest.get("summary_text", ""))
                render_text_box("감정 해석", latest.get("emotion_text", ""))
                if latest["risk"].get("recommendation"):
                    render_text_box("대응 가이드", latest["risk"]["recommendation"])
            else:
                st.markdown(
                    '<div class="note-box">왼쪽 채팅창에서 갈등 유형을 선택하고 내용을 입력하면 결과가 표시됩니다.</div>',
                    unsafe_allow_html=True
                )

            st.markdown("<strong>💡 AI 추천 답변</strong>", unsafe_allow_html=True)

            if latest and latest.get("reply_candidates"):
                for i, text in enumerate(latest["reply_candidates"][:3], 1):
                    safe = clean_display_text(text).replace("\n", "<br>")
                    st.markdown(f"""
                        <div class="list-item">
                            <div class="item-icon">{i}</div>
                            <div class="item-content">{safe}</div>
                            <button class="copy-button"
                            onclick='copyToClipboard(`{safe}`)'>복사</button>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("분석 후 추천 답변이 표시됩니다.")

            st.markdown("<strong>⚠️ 피해야 할 표현 / 대체 표현</strong>", unsafe_allow_html=True)

            lc, rc = st.columns(2)

            if latest:
                with lc:
                    render_phrase_box("피해야 할 표현", latest.get("avoid_phrases", [])[:2], "없음")
                with rc:
                    render_phrase_box("대체 표현", latest.get("alternative_phrases", [])[:2], "없음")
            else:
                with lc:
                    render_text_box("피해야 할 표현", "예: 비난형 표현")
                with rc:
                    render_text_box("대체 표현", "예: 감정 설명형 표현")

            st.markdown("<strong>대화 히스토리 (최근 3개)</strong>", unsafe_allow_html=True)

            if st.session_state.history:
                for idx, item in enumerate(st.session_state.history[:3]):
                    title = f"[{item.get('conflict_type','미선택')}] {item.get('user_input','')[:24]}"
                    render_history_item(
                        "👩🏻‍❤️‍🧑🏻",
                        title,
                        "방금" if idx == 0 else f"{idx+1}전",
                        item.get("assistant_message", "")[:70],
                        idx == 0
                    )
            else:
                render_history_item("👩🏻‍❤️‍🧑🏻", "히스토리 없음", "-", "첫 분석을 시작해보세요.", True)


if __name__ == "__main__":
    main()