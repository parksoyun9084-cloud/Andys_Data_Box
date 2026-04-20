import sys
from pathlib import Path
import streamlit as st
import time

# --- 0. 프로젝트 루트 경로 설정 (찬호님 로직 반영) ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# 찬호님의 실제 분석 함수 임포트
try:
    from src.app_service import run_chat_analysis, run_chat_analysis_from_image_bytes
except ImportError:
    st.error("분석 엔진(src.app_service)을 불러올 수 없습니다. 경로를 확인해주세요.")

# --- 1. 설정 및 스타일 (본인 UI 유지 + 찬호님 타이틀 반영) ---
st.set_page_config(page_title="Andys Dialogue Box - 연인 갈등 대응 AI", layout="wide")


def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
        html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #F8F9FA; }

        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px 25px; background: white; border-bottom: 1px solid #eee; margin-bottom: 20px; border-radius: 12px; }
        .top-bar strong { font-size: 24px; color: #212529; font-weight: 700; }

        .section-title { font-size: 18px; font-weight: 700; color: #212529; margin-bottom: 12px; }
        .message-row { width: 100%; clear: both; margin-bottom: 20px; display: flex; align-items: flex-start; }
        .row-right { flex-direction: row-reverse; }
        .bubble { max-width: 78%; padding: 12px 18px; border-radius: 15px; font-size: 14px; line-height: 1.65; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.02); white-space: pre-wrap; }
        .bubble-left { border: 1px solid #DEE2E6; }
        .bubble-right { border: 2.5px solid #916848; background: #FFFDF9; }
        .avatar { font-size: 25px; margin: 0 12px; }

        /* 분석 카드 및 게이지 */
        .card { background: white; border-radius: 15px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center; border: 1px solid #f0f0f0; min-height: 180px; }
        .gauge-container { background: #E9ECEF; border-radius: 10px; height: 8px; width: 100%; margin-top: 10px; }
        .gauge-fill { height: 100%; border-radius: 10px; transition: width 0.8s ease-in-out; }

        /* 추천 답변 리스트 및 복사 버튼 */
        .list-item { display: flex; align-items: flex-start; padding: 12px; background: white; border-radius: 12px; margin-bottom: 10px; border: 1px solid #eee; }
        .item-icon { background: #EDF2FF; color: #4C6EF5; width: 38px; height: 38px; display: flex; justify-content: center; align-items: center; border-radius: 10px; font-weight: 700; flex-shrink: 0; }
        .item-content { flex: 1; margin-left: 12px; font-size: 13.5px; line-height: 1.6; color: #333; }
        .copy-btn { background: #4C6EF5; color: white; border: none; border-radius: 6px; padding: 6px 12px; font-size: 11px; cursor: pointer; margin-left: 10px; transition: 0.3s; min-width: 60px; }
        .copy-btn:hover { background: #364FC7; }
        .copy-btn.success { background: #2B8A3E !important; }

        .sub-card { background: white; border: 1px solid #eee; border-radius: 12px; padding: 14px; margin-bottom: 10px; }
        .small-label { font-size: 12px; color: #888; margin-bottom: 6px; }
        .pill { display: inline-block; padding: 4px 10px; border-radius: 999px; background: #F1F3F5; color: #666; font-size: 11px; margin-bottom: 10px; }
        </style>

        <script>
        function copyToClipboard(btn, text) {
            const el = document.createElement('textarea');
            el.value = text;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);

            const originalText = btn.innerText;
            btn.innerText = '✅';
            btn.classList.add('success');
            setTimeout(() => { 
                btn.innerText = originalText; 
                btn.classList.remove('success');
            }, 1500);
        }
        </script>
    """, unsafe_allow_html=True)


# --- 2. 헬퍼 함수 (찬호님의 데이터 정리 로직 반영) ---
def clean_display_text(text: str) -> str:
    if not text: return ""
    return str(text).strip().strip('"').strip("'")


def get_risk_color(label: str) -> str:
    label = clean_display_text(label)
    if label in ["심각", "위험"]: return "#E74C3C"
    if label in ["경고", "주의", "보통"]: return "#F08C00"
    return "#5C7CFA"


def get_emotion_emoji(label: str) -> str:
    mapping = {"분노": "😡", "슬픔": "😢", "혐오": "😖", "공포": "😨", "행복": "😊", "중립": "😐", "서운함": "🥺", "불안": "😟", "놀람": "😮",
               "상처": "😢"}
    return mapping.get(clean_display_text(label), "🙂")


# --- 3. UI 컴포넌트 ---
def render_analysis_card(title, emoji, label, score, color, description=""):
    st.markdown(f"""
        <div class="card">
            <div style="color:#888; font-size:13px;">{title}</div>
            <div style="font-size:45px; margin:10px 0;">{emoji}</div>
            <div style="font-weight:700; font-size:20px; color:{color if title == '위험도 분석' else '#212529'};">{label}</div>
            <div style="font-size:12px; color:{color}; margin-top:5px;">신뢰도: {score}%</div>
            <div class="gauge-container"><div class="gauge-fill" style="width:{score}%; background:{color};"></div></div>
            <div style="font-size:12px; color:#868E96; margin-top:10px; line-height:1.5;">{description}</div>
        </div>
    """, unsafe_allow_html=True)


def render_rec_item(idx, text):
    safe_text = text.replace("'", "\\'").replace('"', '\\"')
    st.markdown(f"""
        <div class="list-item">
            <div class="item-icon">{idx}</div>
            <div class="item-content">{text}</div>
            <button class="copy-btn" onclick="copyToClipboard(this, '{safe_text}')">복사</button>
        </div>
    """, unsafe_allow_html=True)


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "avatar": "🍴", "content": "안녕! 대화 텍스트를 입력하거나 캡처 이미지를 올려주면 분석해줄게."}]
    if "latest_result" not in st.session_state: st.session_state.latest_result = None
    if "history" not in st.session_state: st.session_state.history = []
    if "input_mode" not in st.session_state: st.session_state.input_mode = "텍스트 입력"


# --- 4. 메인 어플리케이션 (통합 버전) ---
def main():
    apply_custom_css()
    init_session_state()

    st.markdown('<div class="top-bar"><strong>🎁 Andys Dialogue Box</strong><span>⛶</span></div>',
                unsafe_allow_html=True)

    col_chat, col_report = st.columns([5.5, 4.5])

    with col_chat:
        # 입력 방식 선택 (본인 UI)
        st.session_state.input_mode = st.radio("입력 방식", ["텍스트 입력", "이미지 업로드"], horizontal=True,
                                               label_visibility="collapsed")

        # 채팅창 (본인 스타일)
        with st.container(height=520):
            st.markdown(
                '<div style="text-align:center; margin-bottom:20px;"><span class="pill">📅 실시간 분석 중</span></div>',
                unsafe_allow_html=True)
            for msg in st.session_state.messages:
                is_user = msg["role"] == "user"
                content = clean_display_text(msg["content"]).replace("\n", "<br>")
                st.markdown(f"""
                    <div class="message-row {'row-right' if is_user else ''}">
                        <div class="avatar">{'🐶' if is_user else '🍴'}</div>
                        <div class="bubble {'bubble-right' if is_user else 'bubble-left'}">{content}</div>
                    </div>
                """, unsafe_allow_html=True)

        # 텍스트 입력 처리 (찬호님 로직 반영)
        if st.session_state.input_mode == "텍스트 입력":
            if prompt := st.chat_input("상대방의 메시지를 입력하세요..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("찬호님의 AI 엔진이 분석 중..."):
                    try:
                        result = run_chat_analysis(prompt)
                        st.session_state.latest_result = result
                        st.session_state.messages.append(
                            {"role": "assistant", "avatar": "🍴", "content": result["assistant_message"]})
                        st.session_state.history.insert(0, result)
                    except Exception as e:
                        st.error(f"분석 중 오류 발생: {e}")
                st.rerun()

        # 이미지 업로드 처리 (찬호님 로직 반영)
        else:
            uploaded_file = st.file_uploader("대화 캡처 업로드", type=["png", "jpg", "jpeg", "webp"])
            if st.button("이미지 분석 실행", use_container_width=True) and uploaded_file:
                st.session_state.messages.append({"role": "user", "content": f"[이미지 업로드] {uploaded_file.name}"})
                with st.spinner("이미지에서 텍스트 추출 및 분석 중..."):
                    try:
                        result = run_chat_analysis_from_image_bytes(uploaded_file.getvalue(), uploaded_file.type)
                        st.session_state.latest_result = result
                        st.session_state.messages.append(
                            {"role": "assistant", "avatar": "🍴", "content": result["assistant_message"]})
                        st.session_state.history.insert(0, result)
                    except Exception as e:
                        st.error(f"이미지 분석 오류: {e}")
                st.rerun()

    with col_report:
        st.markdown('<div class="section-title">AI 실시간 분석 리포트</div>', unsafe_allow_html=True)
        latest = st.session_state.latest_result

        if latest:
            c1, c2 = st.columns(2)
            with c1:
                # 찬호님의 감정 데이터 매핑
                emo_label = latest["emotion"].get("label", "중립")
                emo_score = latest["emotion"].get("score", 0)
                render_analysis_card("감정 분석", get_emotion_emoji(emo_label), emo_label, emo_score, "#5C7CFA",
                                     latest.get("emotion_text", ""))
            with c2:
                # 찬호님의 위험도 데이터 매핑
                risk_label = latest["risk"].get("label", "보통")
                risk_score = latest["risk"].get("score", 0)
                render_analysis_card("위험도 분석", "⏱️", risk_label, risk_score, get_risk_color(risk_label),
                                     latest.get("risk_text", ""))

            st.write("---")
            st.markdown("<strong>💡 상황 맞춤 추천 답변 (복사 가능)</strong>", unsafe_allow_html=True)
            # 찬호님의 RAG 추천 답변 리스트 출력
            for i, txt in enumerate(latest.get("reply_candidates", []), 1):
                render_rec_item(i, txt)

            # 유사 사례 정보 (찬호님 파일 하단 로직 반영)
            if latest.get("retrieved_cases"):
                with st.expander("📄 참고된 유사 사례 보기"):
                    for case in latest["retrieved_cases"][:2]:
                        st.markdown(f"**상황:** {case.get('situation', '')}")
                        st.caption(f"관계: {case.get('relation', '연인')} | 추천도: {case.get('risk_level', '')}")
        else:
            st.info("대화를 시작하면 찬호님의 AI 엔진이 분석 결과를 여기에 표시합니다.")

        if st.button("🔴 대화 종료 및 초기화", use_container_width=True):
            st.session_state.messages = []
            st.session_state.latest_result = None
            st.rerun()


if __name__ == "__main__":
    main()