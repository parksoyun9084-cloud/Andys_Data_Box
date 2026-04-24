import sys
from pathlib import Path
import re
import streamlit as st

# 프로젝트 루트를 import 경로에 추가
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.app_service import run_chat_analysis

st.set_page_config(page_title="연인 갈등 대응 AI", layout="wide")


@st.cache_data(ttl=600, show_spinner=False)
def cached_analysis(user_text: str, conflict_type: str):
    return run_chat_analysis(user_text, conflict_type=conflict_type)


def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', sans-serif;
            background-color: #F8F9FA;
        }

        .block-container{
            padding-top:2rem;
            padding-bottom:1rem;
        }

        .top-bar {
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding:15px 25px;
            background:#FFF0F3;
            border-bottom:1px solid #eee;
            margin-top:10px;
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
            margin-bottom:16px;
            color:#212529;
        }

        .emoji-title {
            font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif;
            font-size: 20px;
            vertical-align: -2px;
            margin-right: 4px;
        }

        .st-key-chat_panel {
            background:#F0F4F8;
            border:1px solid #C7E4F8;
            border-radius:18px;
            padding:18px 14px 10px 14px;
            box-shadow:0 4px 14px rgba(0,0,0,0.04);
        }

        .selected-mode-badge{
            display:inline-block;
            padding:7px 14px;
            border-radius:999px;
            background:#FFF3BF;
            color:#5F3B00;
            font-size:13px;
            font-weight:700;
            margin-bottom:12px;
        }

        .message-row {
            width:100%;
            clear:both;
            margin-bottom:14px;
            display:flex;
            align-items:flex-start;
        }

        .row-right {
            flex-direction:row-reverse;
        }

        .row-right .avatar {
            display:block;
            margin:2px 4px 0 10px;
        }

        .bubble {
            max-width:78%;
            padding:11px 15px;
            border-radius:18px;
            font-size:14px;
            line-height:1.65;
            box-shadow:0 1px 3px rgba(0,0,0,0.08);
            white-space:pre-wrap;
            position:relative;
            word-break:keep-all;
        }

        .bubble-left {
            border:2px solid #FFF3BF;
            color:#1F2933;
            background:#FFFFFF;
            border-top-left-radius:5px;
            margin-left:4px;
        }

        .bubble-left::before {
            content:"";
            position:absolute;
            left:-8px;
            top:10px;
            width:0;
            height:0;
            border-top:7px solid transparent;
            border-bottom:7px solid transparent;
            border-right:8px solid #FFF3BF;
        }

        .bubble-right {
            border:2px solid #916848;
            background:#FFFDF9;
            color:#111111;
            border-top-right-radius:5px;
            margin-right:4px;
        }

        .bubble-right::after {
            content:"";
            position:absolute;
            right:-8px;
            top:10px;
            width:0;
            height:0;
            border-top:7px solid transparent;
            border-bottom:7px solid transparent;
            border-left:8px solid #916848;
        }

        .avatar {
            font-size:24px;
            margin:2px 10px 0 4px;
            width:30px;
            text-align:center;
        }

        div[data-testid="stChatInput"] {
            background:#FFFFFF;
            border:1px solid #D6DEE6;
            border-radius:999px;
            box-shadow:0 2px 8px rgba(0,0,0,0.05);
            padding:4px 10px;
        }

        div[data-testid="stChatInput"] textarea {
            font-size:14px !important;
            color:#343A40 !important;
        }

        div[data-testid="stChatInput"] button {
            background:#E9EEF5 !important;
            border-radius:50% !important;
        }

        /* 카드 컴포넌트 디테일 강화 */
        .card {
            background:linear-gradient(180deg, #FFFFFF 0%, #FCFCFD 100%);
            border-radius:24px;
            padding:22px 20px;
            box-shadow:
                0 12px 28px rgba(15, 23, 42, 0.08),
                0 2px 8px rgba(15, 23, 42, 0.04);
            text-align:center;
            border:1px solid rgba(255,255,255,0.75);
            min-height:205px;
        }

        .analysis-icon-wrap {
            width:64px;
            height:64px;
            margin:10px auto 12px auto;
            border-radius:999px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:34px;
            background:var(--icon-bg);
            box-shadow:0 0 0 8px var(--icon-ring), 0 8px 20px var(--icon-glow);
        }

        .gauge-container {
            background:#EEF1F5;
            border-radius:999px;
            height:10px;
            width:100%;
            margin-top:12px;
            overflow:hidden;
            box-shadow:inset 0 1px 2px rgba(0,0,0,0.08);
        }

        .gauge-fill {
            height:100%;
            border-radius:999px;
            transition:width 0.5s ease-in-out;
            background:var(--gauge-gradient);
        }

        .analysis-report {
            background:#FFFFFF;
            border-radius:20px;
            padding:14px;
            margin-top:10px;
            box-shadow:0 10px 24px rgba(15, 23, 42, 0.06);
            border:1px solid rgba(230,235,240,0.9);
        }

        .report-item {
            display:flex;
            align-items:flex-start;
            gap:10px;
            padding:12px 10px;
            border-radius:14px;
            background:#FAFBFC;
            margin-bottom:10px;
            border:1px solid #F0F2F5;
        }

        .report-item:last-child {
            margin-bottom:0;
        }

        .report-dot {
            width:28px;
            height:28px;
            border-radius:999px;
            display:flex;
            align-items:center;
            justify-content:center;
            background:#FFF3BF;
            color:#5F3B00;
            font-size:14px;
            flex-shrink:0;
            box-shadow:0 3px 8px rgba(95,59,0,0.08);
        }

        .report-body {
            flex:1;
        }

        .report-badge {
            display:inline-block;
            padding:4px 9px;
            border-radius:999px;
            background:#FFF8D9;
            color:#5F3B00;
            font-size:11.5px;
            font-weight:700;
            margin-bottom:6px;
        }

        .report-text {
            font-size:13.5px;
            line-height:1.65;
            color:#333;
            word-break:keep-all;
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
            border:none;
            background:#FFF3BF;
            color:#5F3B00;
            font-weight:700;
            min-height:44px;
            box-shadow:none;
        }

        div[data-testid="stButton"] > button:hover{
            background:#FFE066;
            color:#5F3B00;
        }

        div[data-testid="stButton"] > button:focus,
        div[data-testid="stButton"] > button:active,
        div[data-testid="stButton"] > button:focus-visible{
            outline:none !important;
            box-shadow:none !important;
            background:#FFF3BF !important;
            color:#5F3B00 !important;
            border:none !important;
        }
        </style>
    """, unsafe_allow_html=True)


def clean_display_text(text: str) -> str:
    if text is None:
        return ""
    text = str(text).strip()
    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        text = text[1:-1].strip()
    if text.startswith("'") and text.endswith("'") and len(text) >= 2:
        text = text[1:-1].strip()
    return text


def normalize_section_label(label: str) -> str:
    label = clean_display_text(label).replace(" ", "")
    alias_map = {
        "상황요약": "상황 요약",
        "감정": "감정",
        "위험도": "위험도",
        "공감형": "공감형",
        "조언형": "조언형",
        "갈등완충형": "갈등 완충형",
        "피해야할표현": "피해야 할 표현",
        "대체표현": "대체 표현",
    }
    return alias_map.get(label, clean_display_text(label))


def normalize_emotion_label(label: str) -> str:
    mapping = {
        "neutral": "중립",
        "sadness": "슬픔",
        "anger": "분노",
        "fear": "불안",
        "joy": "행복",
        "surprise": "놀람",
        "disgust": "혐오",
    }
    label = clean_display_text(label)
    return mapping.get(label.lower(), label) if label else ""


def normalize_risk_label(label: str) -> str:
    mapping = {
        "normal": "보통",
        "low": "안전",
        "medium": "주의",
        "high": "위험",
        "critical": "심각",
    }
    label = clean_display_text(label)
    return mapping.get(label.lower(), label) if label else ""


def parse_tagged_sections(text: str) -> dict[str, str]:
    if not text:
        return {}

    safe_text = str(text).replace("\r\n", "\n").replace("\r", "\n").strip()

    raw_labels = [
        "상황 요약",
        "상황요약",
        "감정",
        "위험도",
        "공감형",
        "조언형",
        "갈등 완충형",
        "갈등완충형",
        "피해야 할 표현",
        "피해야할표현",
        "대체 표현",
        "대체표현",
    ]

    pattern = r"\[\s*(" + "|".join(map(re.escape, raw_labels)) + r")\s*\]"
    parts = re.split(pattern, safe_text)

    sections = {}
    for i in range(1, len(parts), 2):
        raw_label = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        label = normalize_section_label(raw_label)
        sections[label] = content

    return sections


def expand_phrase_items(items: list[str]) -> list[str]:
    expanded = []

    for item in items:
        text = clean_display_text(item)
        if not text:
            continue

        quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', text)
        if quoted:
            for a, b in quoted:
                phrase = clean_display_text(a or b)
                if phrase and phrase not in expanded:
                    expanded.append(phrase)
            continue

        parts = [clean_display_text(x) for x in re.split(r"\s*,\s*", text)]
        non_empty_parts = [p for p in parts if p]
        if len(non_empty_parts) > 1:
            for p in non_empty_parts:
                if p and p not in expanded:
                    expanded.append(p)
            continue

        if text not in expanded:
            expanded.append(text)

    return expanded[:3]


def get_card_visual(label: str, kind: str) -> dict:
    label = clean_display_text(label)

    if kind == "emotion":
        if label in ["분노", "상처", "불안", "혐오"]:
            return {
                "gradient": "linear-gradient(90deg, #FFB4A2 0%, #FF6B6B 100%)",
                "icon_bg": "#FFF0F0",
                "icon_ring": "rgba(255,107,107,0.18)",
                "icon_glow": "rgba(255,107,107,0.24)",
            }
        if label in ["슬픔", "서운함"]:
            return {
                "gradient": "linear-gradient(90deg, #A5D8FF 0%, #5C7CFA 100%)",
                "icon_bg": "#EFF6FF",
                "icon_ring": "rgba(92,124,250,0.16)",
                "icon_glow": "rgba(92,124,250,0.22)",
            }
        if label == "행복":
            return {
                "gradient": "linear-gradient(90deg, #FFF3BF 0%, #FFD43B 100%)",
                "icon_bg": "#FFF9DB",
                "icon_ring": "rgba(255,212,59,0.18)",
                "icon_glow": "rgba(255,212,59,0.25)",
            }

        return {
            "gradient": "linear-gradient(90deg, #DDE7F0 0%, #AAB7C4 100%)",
            "icon_bg": "#F3F6F9",
            "icon_ring": "rgba(170,183,196,0.16)",
            "icon_glow": "rgba(170,183,196,0.20)",
        }

    if label in ["위험", "심각", "높음"]:
        return {
            "gradient": "linear-gradient(90deg, #FFB4A2 0%, #E74C3C 100%)",
            "icon_bg": "#FFF0F0",
            "icon_ring": "rgba(231,76,60,0.18)",
            "icon_glow": "rgba(231,76,60,0.24)",
        }
    if label in ["주의", "경고", "보통"]:
        return {
            "gradient": "linear-gradient(90deg, #FFF3BF 0%, #F08C00 100%)",
            "icon_bg": "#FFF8E1",
            "icon_ring": "rgba(240,140,0,0.16)",
            "icon_glow": "rgba(240,140,0,0.22)",
        }

    return {
        "gradient": "linear-gradient(90deg, #B2F2BB 0%, #51CF66 100%)",
        "icon_bg": "#EBFBEE",
        "icon_ring": "rgba(81,207,102,0.16)",
        "icon_glow": "rgba(81,207,102,0.22)",
    }


def render_analysis_card(
    title: str,
    emoji: str,
    label: str,
    score: int,
    color: str,
    description: str = "",
    score_label: str = "분석 점수",
    kind: str = "emotion",
):
    safe_label = clean_display_text(label)
    safe_desc = clean_display_text(description)
    visual = get_card_visual(safe_label, kind)

    st.markdown(f"""
        <div class="card">
            <div style="color:#888; font-size:13px; font-weight:700;">{title}</div>
            <div class="analysis-icon-wrap"
                 style="--icon-bg:{visual['icon_bg']};
                        --icon-ring:{visual['icon_ring']};
                        --icon-glow:{visual['icon_glow']};">
                {emoji}
            </div>
            <div style="font-weight:800; font-size:21px; color:{color if title == '위험도 분석' else '#212529'};">
                {safe_label}
            </div>
            <div style="font-size:12px; color:{color}; margin-top:5px; font-weight:700;">
                {score_label} {score}%
            </div>
            <div class="gauge-container">
                <div class="gauge-fill"
                     style="width:{score}%; --gauge-gradient:{visual['gradient']};">
                </div>
            </div>
            <div style="font-size:12px; color:#868E96; margin-top:12px; line-height:1.55;">
                {safe_desc}
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_report_item(icon: str, label: str, body: str):
    st.markdown(f"""
        <div class="report-item">
            <div class="report-dot">{icon}</div>
            <div class="report-body">
                <div class="report-badge">{label}</div>
                <div class="report-text">{clean_display_text(body)}</div>
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
    cleaned = [clean_display_text(item) for item in items if clean_display_text(item)]
    cleaned = expand_phrase_items(cleaned)

    if not cleaned:
        render_text_box(title, empty_text)
        return

    for item in cleaned:
        render_text_box(title, item)


def get_risk_color(label: str) -> str:
    if label in ["심각", "위험", "높음"]:
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
        "높음": "자극적인 표현을 피하고 대화를 차분히 이어가는 게 좋습니다.",
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
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None
    if "pending_conflict_type" not in st.session_state:
        st.session_state.pending_conflict_type = None


def set_conflict_type(v):
    st.session_state.conflict_type = v


def reset_chat():
    st.session_state.messages = [{
        "role": "assistant",
        "avatar": "🎁",
        "content": "안녕하세요.\nAI 채팅상담입니다.\n\n연인관계 갈등 유형을 먼저 선택한 뒤, 상황을 입력해 주세요."
    }]
    st.session_state.latest_result = None
    st.session_state.history = []
    st.session_state.error_message = ""
    st.session_state.last_prompt = ""
    st.session_state.conflict_type = "연락 문제 > 답장 지연 > 서운함"
    st.session_state.pending_prompt = None
    st.session_state.pending_conflict_type = None

    cached_analysis.clear()
    st.rerun()


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
        "화해/재회": ["사과법", "다시 연락", "화해 대화", "재회 고민"],
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
        with st.container(height=700, key="chat_panel"):
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

                if idx == 0:
                    render_quick_conflict_buttons()

        placeholder = f"[{st.session_state.conflict_type}] 현재 상황을 입력해주세요."

        if prompt := st.chat_input(placeholder, key="main_chat_input"):
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

            st.session_state.pending_prompt = prompt
            st.session_state.pending_conflict_type = st.session_state.conflict_type

            st.rerun()

    with col_report:
        if st.session_state.pending_prompt:
            with st.spinner("AI 분석 중..."):
                try:
                    prompt = st.session_state.pending_prompt
                    conflict_type = st.session_state.pending_conflict_type

                    result = cached_analysis(prompt, conflict_type)

                    result["user_input"] = prompt
                    result["conflict_type"] = conflict_type

                    assistant_raw = clean_display_text(
                        result.get("assistant_message") or result.get("result_text") or ""
                    )
                    parsed_sections = result.get("parsed_sections") or parse_tagged_sections(assistant_raw)

                    result["assistant_message"] = assistant_raw
                    result["parsed_sections"] = parsed_sections

                    result["summary_text"] = clean_display_text(
                        result.get("summary_text")
                        or result.get("situation_summary")
                        or parsed_sections.get("상황 요약")
                        or ""
                    )

                    emotion_info = result.get("emotion", {}) if isinstance(result.get("emotion"), dict) else {}
                    risk_info = result.get("risk", {}) if isinstance(result.get("risk"), dict) else {}

                    emotion_label = normalize_emotion_label(emotion_info.get("label", ""))
                    risk_label = normalize_risk_label(risk_info.get("label", ""))

                    result["emotion_text"] = clean_display_text(
                        emotion_label or parsed_sections.get("감정") or ""
                    )

                    result["risk_text"] = clean_display_text(
                        risk_label or parsed_sections.get("위험도") or ""
                    )

                    result["empathy_reply"] = clean_display_text(
                        result.get("empathy_reply") or parsed_sections.get("공감형") or ""
                    )
                    result["advice_reply"] = clean_display_text(
                        result.get("advice_reply") or parsed_sections.get("조언형") or ""
                    )
                    result["buffer_reply"] = clean_display_text(
                        result.get("buffer_reply") or parsed_sections.get("갈등 완충형") or ""
                    )

                    if result.get("avoid_phrases"):
                        result["avoid_phrases"] = [
                            clean_display_text(x) for x in result.get("avoid_phrases", []) if clean_display_text(x)
                        ]

                    if result.get("alternative_phrases"):
                        result["alternative_phrases"] = [
                            clean_display_text(x) for x in result.get("alternative_phrases", []) if clean_display_text(x)
                        ]

                    chat_preview = "분석이 완료됐어요. 오른쪽 패널에서 감정, 위험도, 추천 답장을 확인해보세요."

                    st.session_state.latest_result = result
                    st.session_state.messages.append({
                        "role": "assistant",
                        "avatar": "🎁",
                        "content": chat_preview
                    })
                    st.session_state.history.insert(0, {
                        **result,
                        "chat_preview": chat_preview,
                    })

                    st.session_state.pending_prompt = None
                    st.session_state.pending_conflict_type = None

                    st.rerun()

                except Exception as e:
                    st.session_state.error_message = str(e)
                    st.session_state.pending_prompt = None
                    st.session_state.pending_conflict_type = None
                    st.rerun()

        with st.container(height=700):
            st.markdown(
                '<div class="section-title"><span class="emoji-title">🤖</span> AI 분석 결과</div>',
                unsafe_allow_html=True
            )

            latest = st.session_state.latest_result

            emotion_label, emotion_score, emotion_emoji, emotion_desc = "대기 중", 0, "🙂", "입력 시 분석을 시작합니다."
            risk_label, risk_score, risk_color, risk_desc = "대기 중", 0, "#ADB5BD", "갈등 위험도를 측정합니다."

            if latest:
                emotion_info = latest.get("emotion", {}) if isinstance(latest.get("emotion"), dict) else {}
                risk_info = latest.get("risk", {}) if isinstance(latest.get("risk"), dict) else {}

                emotion_label = normalize_emotion_label(
                    emotion_info.get("label") or latest.get("emotion_text") or "대기 중"
                )
                emotion_score = int(emotion_info.get("score", 0))
                emotion_emoji = get_emotion_emoji(emotion_label)
                emotion_desc = get_emotion_description(emotion_label)

                risk_label = normalize_risk_label(
                    risk_info.get("label") or latest.get("risk_text") or "대기 중"
                )
                risk_score = int(risk_info.get("score", 0))
                risk_color = get_risk_color(risk_label)
                risk_desc = get_risk_description(risk_label)

            c1, c2 = st.columns(2)
            with c1:
                render_analysis_card(
                    "감정 분석",
                    emotion_emoji,
                    emotion_label,
                    emotion_score,
                    "#5C7CFA",
                    emotion_desc,
                    kind="emotion",
                )
            with c2:
                render_analysis_card(
                    "위험도 분석",
                    "⏱️",
                    risk_label,
                    risk_score,
                    risk_color,
                    risk_desc,
                    kind="risk",
                )

            if st.session_state.error_message:
                st.error(st.session_state.error_message)

            st.markdown("<strong>입력 메시지 분석</strong>", unsafe_allow_html=True)

            if latest:
                render_report_item("🏷️", "갈등유형", latest.get("conflict_type", "미선택"))
                render_report_item("📝", "상황 요약", latest.get("summary_text", ""))
                render_report_item("💬", "감정 해석", latest.get("emotion_text", ""))
                render_report_item("⚠️", "위험도 해석", latest.get("risk_text", ""))

                risk_obj = latest.get("risk", {})
                if isinstance(risk_obj, dict) and risk_obj.get("recommendation"):
                    render_report_item("🧭", "대응 가이드", risk_obj["recommendation"])
            else:
                st.markdown(
                    '<div class="note-box">왼쪽 채팅창에서 갈등 유형을 선택하고 내용을 입력하면 결과가 표시됩니다.</div>',
                    unsafe_allow_html=True
                )

            st.markdown("<strong>💡 연인에게 보낼 추천 답장</strong>", unsafe_allow_html=True)

            if latest:
                styles = [
                    ("공감형", "💛", clean_display_text(latest.get("empathy_reply", ""))),
                    ("조언형", "🗣️", clean_display_text(latest.get("advice_reply", ""))),
                    ("갈등 완충형", "🤝🏻‍", clean_display_text(latest.get("buffer_reply", ""))),
                ]

                found_count = 0

                for label, icon, reply in styles:
                    if reply:
                        found_count += 1
                        safe_html = reply.replace("\n", "<br>")

                        st.markdown(f"""
                            <div class="list-item">
                                <div class="item-icon">{icon}</div>
                                <div class="item-content" style="padding-right:0;">
                                    <strong>{label}</strong><br>{safe_html}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                if found_count == 0:
                    raw = latest.get("assistant_message", "")
                    st.info("추천 답장을 불러오지 못했습니다.")
                    with st.expander("디버그: 구조화 응답 확인"):
                        st.write({
                            "query_type": latest.get("query_type", ""),
                            "empathy_reply": latest.get("empathy_reply", ""),
                            "advice_reply": latest.get("advice_reply", ""),
                            "buffer_reply": latest.get("buffer_reply", ""),
                            "result_text": latest.get("result_text", ""),
                        })
                    with st.expander("디버그: assistant_message 원문 보기"):
                        st.text(raw)

            else:
                st.info("분석 후 추천 답장이 표시됩니다.")

            st.markdown("<strong>⚠️ 피해야 할 표현 / 대체 표현</strong>", unsafe_allow_html=True)

            lc, rc = st.columns(2)

            if latest:
                with lc:
                    render_phrase_box("피해야 할 표현", latest.get("avoid_phrases", [])[:3], "없음")
                with rc:
                    render_phrase_box("대체 표현", latest.get("alternative_phrases", [])[:3], "없음")
            else:
                with lc:
                    render_text_box("피해야 할 표현", "예: 비난형 표현")
                with rc:
                    render_text_box("대체 표현", "예: 감정 설명형 표현")

            st.markdown("<strong>대화 히스토리 (최근 3개)</strong>", unsafe_allow_html=True)

            if st.session_state.history:
                for idx, item in enumerate(st.session_state.history[:3]):
                    title = f"[{item.get('conflict_type', '미선택')}] {item.get('user_input', '')[:24]}"
                    preview_text = item.get("chat_preview") or "오른쪽 패널에서 결과를 확인해보세요."

                    render_history_item(
                        "👩🏻‍❤️‍🧑🏻",
                        title,
                        "방금" if idx == 0 else f"{idx+1}분전",
                        preview_text,
                        idx == 0
                    )
            else:
                render_history_item("👩🏻‍❤️‍🧑🏻", "히스토리 없음", "-", "첫 분석을 시작해보세요.", True)

            st.markdown("<br>", unsafe_allow_html=True)

            _, reset_col = st.columns([2, 1])
            with reset_col:
                if st.button("🔄 새로운 고민 시작하기", key="reset_chat_button"):
                    reset_chat()


if __name__ == "__main__":
    main()