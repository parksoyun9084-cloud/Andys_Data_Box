# SKN26-3rd-4Team

---

# 💬 감정 기반 연인 갈등 완화 대화 추천 시스템

---

## 📌 목차

1. [How to Run](#1-how-to-run)
2. [Team](#2-team)
3. [프로젝트 개요](#3-프로젝트-개요)
4. [시스템 아키텍처](#4-시스템-아키텍처)
5. [데이터 전처리](#5-데이터-전처리)
6. [RAG 기반 시스템](#6-rag-기반-시스템)
7. [테스트 및 평가](#7-테스트-및-평가)
8. [Streamlit UI](#8-streamlit-ui)
9. [프로젝트 구조](#9-프로젝트-구조)
10. [주요 기능](#10-주요-기능)
11. [AI 처리 흐름](#11-ai-처리-흐름)
12. [출력 안정화 설계](#12-출력-안정화-설계)
13. [한계 및 개선 방향](#13-한계-및-개선-방향)
14. [동료 회고](#14-동료-회고)

---

## 1. How to Run

### 1-1. 배포 서비스
🔗 https://andysdatabox-7tb38xujsfiq3uaiwdr9na.streamlit.app/

별도의 설치 없이 웹에서 바로 사용 가능합니다.

### 1-2. 로컬 실행 방법

```bash
1. 환경 설정
conda env create -f environment.yml
conda activate <env_name>

2. API Key 설정
.streamlit/secrets.toml 파일 생성 후 아래 값 입력

OPENAI_API_KEY="your_openai_api_key"
GEMINI_API_KEY="your_gemini_api_key"
PINECONE_API_KEY="your_pinecone_api_key"

** PINECONE_API_KEY는 요청 시 제공 **

3. 실행
streamlit run app/streamlit_app.py
```

---

## 2. Team

### 🎁 Andy's Data Box

<table align="center">
  <tr>
    <td align="center" width="170" valign="top">
      <table>
        <tr>
          <td align="center" height="130">
            <img src="app/figures/렉스.jpg" width="100" height="110" style="object-fit:contain; border-radius:10px;">
          </td>
        </tr>
        <tr>
          <td align="center"><b>김용욱</b></td>
        </tr>
        <tr>
          <td align="center"><a href="https://github.com/yonguk12077-beep">@yonguk12077-beep</a></td>
        </tr>
      </table>
    </td>
    <td align="center" width="170" valign="top">
      <table>
        <tr>
          <td align="center" height="130">
            <img src="app/figures/우디.jpg" width="100" height="110" style="object-fit:contain; border-radius:10px;">
          </td>
        </tr>
        <tr>
          <td align="center"><b>박소윤</b></td>
        </tr>
        <tr>
          <td align="center"><a href="https://github.com/parksoyun9084-cloud">@parksoyun9084-cloud</a></td>
        </tr>
      </table>
    </td>
    <td align="center" width="170" valign="top">
      <table>
        <tr>
          <td align="center" height="130">
            <img src="app/figures/미스터샤크.jpg" width="100" height="110" style="object-fit:contain; border-radius:10px;">
          </td>
        </tr>
        <tr>
          <td align="center"><b>윤찬호</b></td>
        </tr>
        <tr>
          <td align="center"><a href="https://github.com/ch3477-sudo">@ch3477-sudo</a></td>
        </tr>
      </table>
    </td>
    <td align="center" width="170" valign="top">
      <table>
        <tr>
          <td align="center" height="130">
            <img src="app/figures/저그 황제.jpg" width="100" height="110" style="object-fit:contain; border-radius:10px;">
          </td>
        </tr>
        <tr>
          <td align="center"><b>전승권</b></td>
        </tr>
        <tr>
          <td align="center"><a href="https://github.com/eaent">@eaent</a></td>
        </tr>
      </table>
    </td>
  </tr>
</table>

### 역할 분담

<table>
  <thead>
    <tr>
      <th width="120">이름</th>
      <th>역할</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center"><b>김용욱</b></td>
      <td>Vector DB 구축 / 프롬프트 설계 / RAG 파이프라인 구성 / 답변 추천 구조 기본 구성</td>
    </tr>
    <tr>
      <td align="center"><b>박소윤</b></td>
      <td>서비스 기획·아키텍처 설계 / RAG·감정·위험도 통합 AI 로직 설계 및 서비스 레이어 구현 / LLM 출력 파싱 및 UI 표시 구조 설계 / Streamlit 구현 및 기능 연동 / 데이터 구조 및 문서화 설계 / 일정·마일스톤 관리</td>
    </tr>
    <tr>
      <td align="center"><b>윤찬호</b></td>
      <td>데이터 전처리 / RAG 검색 구조 비교 / Retrieval 성능 평가 / 답변 추천 흐름 개선</td>
    </tr>
    <tr>
      <td align="center"><b>전승권</b></td>
      <td>환경설정 / API 연동 / 앱 구조 정리</td>
    </tr>
  </tbody>
</table>

---

## 3. 프로젝트 개요

연인 간 대화에서 발생하는 갈등 상황을 분석하고  
감정 및 갈등 위험도를 기반으로 실제 사용할 수 있는 답장 메시지를 추천하는 AI 시스템이다.

### 3-1. 문제 정의

연인 간 갈등 상황에서는 감정이 앞서기 때문에  
적절한 표현을 선택하기 어렵고,  
잘못된 말 한마디로 갈등이 심화되는 경우가 많다.

기존 챗봇은 일반적인 상담이나 조언을 제공하지만,  
👉 실제로 상대에게 보낼 수 있는 "메시지 형태의 답장"을 생성하는 데에는 한계가 있다.

따라서 본 프로젝트는  
👉 "실제 대화에 바로 사용할 수 있는 답장 생성"을 목표로 설계되었다.

### 3-2. TL;DR (핵심 요약)

<pre>
사용자가 연인 갈등 유형 선택 및 상황 입력
→ 감정 분석 및 갈등 위험도 분석
→ RAG 기반 유사 사례 검색
→ 공감형 / 조언형 / 갈등 완충형 답장 추천
→ 피해야 할 표현과 대체 표현 제공
</pre>

### 3-3. 목표

- 감정 기반 상황 이해
- 갈등 위험도 판단
- RAG 기반 유사 사례 활용
- 실사용 가능한 답장 생성

### 3-4. Tech Stack

- LLM: Gemini, GPT
- Retrieval: BM25, Dense Embedding (OpenAI)
- Vector DB: Pinecone
- Backend: Python
- Frontend: Streamlit
- 기타: RRF (Reciprocal Rank Fusion)

---

## 4. 시스템 아키텍처

<pre>
사용자 입력
→ Streamlit UI
→ 감정 분석 (Gemini)
→ 위험도 분석 (Gemini)
→ RAG 검색 (BM25 + Dense + RRF)
→ 답변 생성 (GPT)
→ 출력 파싱 및 보정
→ UI 출력
</pre>

👉 상세 구조: [시스템 아키텍처](docs/02_architecture/system_architecture.md)

### 4-1. 핵심 특징

- LLM + RAG 혼합 구조
- 감정 + 위험도 기반 분석
- 실제 메시지 생성 중심 설계
- 출력 안정화 (repair prompt)

---

## 5. 데이터 전처리

### 5-1. 사용 데이터

- 감정 라벨링 대화 데이터셋  
  → 감정 분석 모델 입력 데이터로 사용

- 연인 관계 필터링 대화 데이터  
  → 실제 연인 갈등 상황 중심 데이터 구성

- RAG 문서용 대화 사례 데이터  
  → 유사 사례 검색 및 답변 생성 참고 데이터

### 5-2. 전처리 결과

| 파일 | 역할 |
|------|------|
| continuous_dialogue_dialogue.csv | 대화 단위 감정 흐름 |
| continuous_dialogue_utterance.csv | 발화 단위 감정 |
| rag_documents.csv | RAG 검색 문서 |
| response_pairs.csv | 답변 추천 데이터 |

---

## 6. RAG 기반 시스템

### 6-1. 구조

- BM25 (키워드 검색)
- Dense Embedding (OpenAI)
- RRF 결합

### 6-2. Vector DB
- Pinecone 기반 Vector DB 구축

### 6-3. 효과
- LLM 환각 감소
- 실제 사례 기반 답변 생성
- 상황 적합도 향상

---

## 7. 테스트 및 평가

- 감정 분석 정상 동작
- 위험도 분류 단계별 구분 성공
- 답변 생성 실사용 가능 수준 확보

👉 [테스트 및 평가 보기](docs/04_test/)

---

## 8. Streamlit UI

- 채팅 인터페이스
- 감정 / 위험도 카드
- 추천 답변 출력

### 8-1. 사용 예시

**입력**
> 남자친구가 요즘 연락을 너무 안 해서 서운해. 뭐라고 보내면 좋을까?

**출력**

- 감정: 슬픔
- 위험도: 주의
- 상황 요약: 연인 관계에서 연락 빈도 문제로 서운함을 느끼는 갈등 상황

**추천 답장**
1. 공감형 → "요즘 연락이 줄어든 것 같아서 내가 좀 서운하고 마음이 멀어진 느낌이 들어."
2. 조언형 → "나는 하루에 한 번 정도는 연락이 있었으면 좋겠어. 그렇게 해주면 내가 훨씬 편안할 것 같아."
3. 갈등 완충형 → "연락이 줄어서 내가 조금 불안한 마음이 들었어. 서로 부담되지 않는 선에서 연락 방식 한번 맞춰보면 좋을 것 같아."

**표현 가이드**
- 피해야 할 표현: "왜 연락 안 해?", "맨날 내가 먼저 하잖아"
- 대체 표현: "요즘 연락이 줄어서 조금 서운해", "나는 연락이 조금 더 있었으면 좋겠어"

---

## 9. 프로젝트 구조

```text
project/
│
├─ app/                         # Streamlit UI
│   └─ streamlit_app.py         # 메인 실행 파일 (UI + 사용자 입력 처리)
│
├─ src/                         # 핵심 서비스 로직
│   │
│   ├─ app_service.py           # 전체 AI 파이프라인 orchestration
│   │                           # (감정 분석 + 위험도 분석 + RAG + LLM 결과 통합)
│   │
│   ├─ app_payload_formatter.py # UI 출력용 데이터 구조 생성 및 정리
│   │
│   ├─ app_rag_result_parser.py # LLM 출력 파싱 및 후처리
│   │                           # (태그 분리, 문장 정제, 리스트 변환)
│   │
│   ├─ emotion/                 # 감정 및 위험도 분석 모듈
│   │   ├─ llm_connector.py     # Gemini LLM 호출 wrapper
│   │   └─ risk_analyzer.py     # 감정 + 위험도 분석 로직
│   │
│   ├─ rag/                     # RAG 기반 답변 생성 시스템
│   │   └─ build_rag_chain.py   # 검색 + 답변 생성 전체 pipeline
│   │                           # (BM25 + Dense + RRF + GPT 생성)
│   │
│   └─ utils/                   # 공통 유틸 (텍스트 정제, 파싱 등)
│
├─ data/                        # 데이터 저장
│   ├─ processed/               # 전처리된 데이터
│   │   ├─ rag_documents.csv
│   │   └─ response_pairs.csv
│
├─ docs/                        # 문서
│   ├─ 02_architecture/
│   └─ 04_test/
│
├─ tests/                       # 테스트 코드
│
└─ README.md
```

### 9-1. 구조 설계 특징

- UI / 서비스 로직 / AI 처리 파이프라인을 분리한 구조
- app_service를 중심으로 모든 AI 흐름을 통합 관리
- RAG / 감정 분석 / 출력 파싱을 모듈 단위로 분리하여 유지보수성 확보

---

## 10. 주요 기능

- 연인 갈등 유형 선택
- 감정 분석 (LLM 기반)
- 갈등 위험도 판단
- RAG 기반 유사 사례 검색 (Dense + RRF)
- 공감형 / 조언형 / 갈등 완충형 답장 자동 생성
- 표현 가이드 (피해야 할 표현 / 대체 표현)
- 답장 품질 검증 (상담형 문체 필터링)
- 최근 대화 히스토리 제공
- 새로운 고민 시작 기능

### 10-1. 주요 차별점

- 단순 챗봇이 아닌 "실제 보낼 답장 생성 시스템"
- 감정 + 위험도를 동시에 고려한 대응 전략 생성
- RAG 기반 실제 연애 갈등 사례 활용 (환각 감소)
- 상담형이 아닌 카카오톡 메시지 스타일 출력
- 부적절한 답장 자동 필터링 (상담형 문체 제거)
- LLM 출력 구조 파싱 및 후처리 기반 안정화
- 사용자 입력 기반 상황 유지 (임의 상황 생성 방지 설계)

---

## 11. AI 처리 흐름

본 시스템은 사용자 입력을 단순히 LLM에 전달하는 구조가 아니라, 감정 분석·위험도 분석·RAG 검색·답변 생성·출력 후처리를 순차적으로 수행하는 파이프라인 구조로 설계하였다.

```text
사용자 입력
→ 갈등 유형 및 세부 상황 선택
→ Gemini 기반 감정 분석
→ Gemini 기반 갈등 위험도 분석
→ RAG 검색 쿼리 생성
→ BM25 검색 + Dense 검색
→ RRF 기반 검색 결과 결합
→ 유사 사례 및 응답 예시 추출
→ GPT 기반 답장 생성
→ LLM 출력 파싱 및 보정
→ Streamlit UI 출력
```

### 11-1. 처리 단계별 역할

| 단계 | 설명 |
|------|------|
| 감정 분석 | 사용자 입력에서 주요 감정 라벨을 추출 |
| 위험도 분석 | 갈등이 심화될 가능성을 단계별로 판단 |
| RAG 검색 | 유사한 연인 갈등 사례를 검색 |
| 답변 생성 | 공감형 / 조언형 / 갈등 완충형 답장 생성 |
| 출력 보정 | LLM 출력 형식을 UI에 맞게 파싱 및 정리 |

---

## 12. 출력 안정화 설계

LLM 응답은 항상 동일한 형식으로 반환되지 않을 수 있기 때문에, 본 프로젝트에서는 출력 안정화를 위한 후처리 구조를 적용하였다.

### 12-1. 출력 파싱

LLM 결과에서 아래 태그를 기준으로 응답을 분리한다.

```text
[상황 요약]
[감정]
[위험도]
[공감형]
[조언형]
[갈등 완충형]
[피해야 할 표현]
[대체 표현]
```

### 12-2. 답변 품질 검증

추천 답변이 상담형 문체로 흐르지 않도록 아래 조건을 검증한다.

- 사용자를 위로하는 상담형 문장 필터링
- 상대에게 직접 보낼 수 있는 메시지인지 검증
- “나 / 내 / 우리” 중심 화법 포함 여부 확인
- 공감형 / 조언형 / 갈등 완충형 답변 누락 여부 확인

### 12-3. UI 표시 안정화

파싱된 결과는 Streamlit 화면에 맞게 다시 정리된다.

- 감정 / 위험도 카드 표시
- 입력 메시지 분석 카드 표시
- 추천 답장 3종 분리 출력
- 피해야 할 표현 / 대체 표현 분리 출력

---

## 13. 한계 및 개선 방향

### 13-1. 한계
- 감정 분석에서 일부 미묘한 감정 구분 한계 존재
- 데이터셋이 연인 관계 중심으로 제한됨
- LLM 응답 형식 불안정성 존재
- RAG 검색 결과 품질이 입력 표현에 영향 받음

### 13-2. 개선 방향
- 감정 분류 세분화 (multi-label emotion)
- 데이터셋 확장 (다양한 관계 포함)
- RAG reranking 고도화
- 실시간 대화 흐름 추적 기능 추가
- 사용자 맞춤형 답변 스타일 적용 (personalization)

---

## 14. 동료 회고

<table>
  <thead>
    <tr>
      <th width="120">작성자</th>
      <th width="120">대상자</th>
      <th>회고 내용</th>
    </tr>
  </thead>
  <tbody>
    <!-- 김용욱 -->
    <tr>
      <td rowspan="3" align="center"><b>김용욱</b></td>
      <td align="center"><b>박소윤</b></td>
      <td>프로젝트 내에서 주도적으로 회의를 이끌어나가며 방향을 정리해주었고, README 작성 및 Streamlit 초기 구성안 제안으로 팀 진행에 큰 도움을 주었습니다.</td>
    </tr>
    <tr>
      <td align="center"><b>윤찬호</b></td>
      <td>데이터 전처리와 후보 문장, 대화 구조 정리를 담당해주었고, RAG 파이프라인을 세분화하여 기존 구조와 병합하는 데 기여해주었습니다.</td>
    </tr>
    <tr>
      <td align="center"><b>전승권</b></td>
      <td>감정 및 위험도 분석 기준을 정리해주었고, 개발 중 발생한 오류를 함께 해결하며 프로젝트 진행 속도를 높이는 데 도움을 주었습니다.</td>
    </tr>
  <!-- 박소윤 -->
    <tr>
      <td rowspan="3" align="center"><b>박소윤</b></td>
      <td align="center"><b>김용욱</b></td>
      <td>RAG 파이프라인 구축과 Vector DB 구성, 프롬프트 설계를 담당하여 검색과 답변 생성의 기반 구조를 구현해주었습니다. 전체 시스템 흐름에서 RAG가 핵심적으로 동작할 수 있도록 구조 설계에 기여해주었습니다.</td>
    </tr>
    <tr>
      <td align="center"><b>윤찬호</b></td>
      <td>데이터 전처리와 RAG 검색 구조 비교, Retrieval 성능 평가를 수행하여 데이터 품질 확보와 검색 성능 개선에 기여해주었습니다. 시스템 성능 개선 방향을 정리하는데 도움이 되었습니다.</td>
    </tr>
    <tr>
      <td align="center"><b>전승권</b></td>
      <td>API 연동과 앱 구조 정리를 담당하여 프로젝트가 정상적으로 실행될 수 있는 기반을 마련해주었습니다. 개발 과정에서 환경 차이로 인한 실행 이슈가 발생하였으나, 이를 정리하고 통합하는 과정을 통해 전체 시스템이 안정적으로 동작할 수 있도록 개선하였습니다.</td>
    </tr>
    <!-- 윤찬호 -->
    <tr>
      <td rowspan="3" align="center"><b>윤찬호</b></td>
      <td align="center"><b>김용욱</b></td>
      <td>Vector DB 구축과 프롬프트 설계를 진행해주시고, RAG 문서 검색 파이프라인 구성에도 기여해주셔서 프로젝트 완성도 향상에 도움이 되었습니다.</td>
    </tr>
    <tr>
      <td align="center"><b>박소윤</b></td>
      <td>프로젝트 주제 선정과 역할 분배 과정에서 먼저 나서주셔서 팀이 방향을 빠르게 정하고 원활하게 출발할 수 있었습니다.</td>
    </tr>
    <tr>
      <td align="center"><b>전승권</b></td>
      <td>갈등 상황에서 감정과 위험도를 분석하는 역할을 맡아 프로젝트의 핵심 차별점을 잘 살려주었습니다.</td>
    </tr>
    <!-- 전승권 -->
    <tr>
      <td rowspan="3" align="center"><b>전승권</b></td>
      <td align="center"><b>김용욱</b></td>
      <td>RAG 파트에서 벡터 DB를 로컬 환경에 깔끔하게 생성해주었습니다.</td>
    </tr>
    <tr>
      <td align="center"><b>박소윤</b></td>
      <td>프로젝트 전반에서 의견 표현이 명확했고, 역할 분배를 주도하여 팀 진행에 도움이 되었습니다.</td>
    </tr>
    <tr>
      <td align="center"><b>윤찬호</b></td>
      <td>전처리 데이터셋을 담당하여 자료 준비가 수월해졌고, 프로젝트 수행에 도움이 되었습니다.</td>
    </tr>

  </tbody>
</table>