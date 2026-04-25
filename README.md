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
11. [한계 및 개선 방향](#11-한계-및-개선-방향)
12. [동료 회고](#12-동료-회고)

---

## 1. How to Run

### 배포 서비스
🔗 https://andysdatabox-7tb38xujsfiq3uaiwdr9na.streamlit.app/

별도의 설치 없이 웹에서 바로 사용 가능합니다.

---

### 💻 로컬 실행 방법

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

## 🎁 Andy's Data Box

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

## 역할 분담

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
      <td>서비스 기획·아키텍처 설계 / RAG·감정·위험도 통합 AI 로직 설계 / Streamlit 구현 및 기능 연동 / 데이터 구조 및 문서화 설계 / 일정·마일스톤 관리</td>
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

### 3-1. TL;DR

<pre>
사용자의 갈등 상황 입력 
→ 감정 및 위험도 분석 
→ RAG 기반 유사 사례 검색 
→ 실제 사용할 수 있는 답장 3종 추천 (공감형 / 조언형 / 갈등 완충형)
</pre>

### 3-2. 목표

- 감정 기반 상황 이해
- 갈등 위험도 판단
- RAG 기반 유사 사례 활용
- 실사용 가능한 답장 생성

### 3-3. Tech Stack

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
> "요즘 연락이 너무 뜸해서 서운해..."

**출력**

- 감정: 서운함 (슬픔)
- 위험도: 주의

**추천 답장**
1. 공감형 → "요즘 연락이 줄어서 많이 서운했어..."
2. 조언형 → "우리 연락 패턴에 대해 한 번 얘기해보면 좋을 것 같아"
3. 완충형 → "바쁜 건 이해하지만 조금만 더 신경 써주면 좋겠어"

---

## 9. 프로젝트 구조

<pre>
project/
│
├─ data/
├─ src/
│   ├─ emotion/
│   ├─ rag/
│   └─ app_service.py
│
├─ app/
│   └─ streamlit_app.py
│
├─ docs/
├─ tests/
└─ README.md
</pre>

---

## 10. 주요 기능

- 감정 분석 (LLM 기반)
- 갈등 위험도 판단
- RAG 기반 유사 사례 검색
- 답장 3종 자동 생성
- 표현 가이드 (피해야 할 표현 / 대체 표현)

### 10-1. 주요 차별점

- 단순 챗봇이 아닌 “답장 생성 시스템”
- 감정 + 위험도 기반 대응 전략
- RAG 기반 상황 이해
- 실제 메시지 스타일 출력

---

## 11. 한계 및 개선 방향

### 11-1. 한계
- 감정 분석에서 일부 미묘한 감정 구분 한계 존재
- 데이터셋이 연인 관계 중심으로 제한됨
- LLM 응답 형식 불안정성 존재
- RAG 검색 결과 품질이 입력 표현에 영향 받음

### 11-2. 개선 방향
- 감정 분류 세분화 (multi-label emotion)
- 데이터셋 확장 (다양한 관계 포함)
- RAG reranking 고도화
- 실시간 대화 흐름 추적 기능 추가
- 사용자 맞춤형 답변 스타일 적용 (personalization)

---

## 12. 동료 회고

<table style="width:100%; border-collapse: collapse;">
  <thead>
    <tr style="background-color:#f6f8fa;">
      <th style="border:1px solid #d0d7de; padding:10px; width:120px;">작성자</th>
      <th style="border:1px solid #d0d7de; padding:10px; width:120px;">대상자</th>
      <th style="border:1px solid #d0d7de; padding:10px;">회고 내용</th>
    </tr>
  </thead>
  <tbody>
    <!-- 김용욱 -->
    <tr>
      <td rowspan="3" align="center" style="border:1px solid #d0d7de;"><b>김용욱</b></td>
      <td align="center" style="border:1px solid #d0d7de;">박소윤</td>
      <td style="border:1px solid #d0d7de;">프로젝트 내에서 주도적으로 회의를 이끌어나가며 방향을 정리해주었고, README 작성 및 Streamlit 초기 구성안 제안으로 팀 진행에 큰 도움을 주었습니다.</td>
    </tr>
    <tr>
      <td align="center" style="border:1px solid #d0d7de;">윤찬호</td>
      <td style="border:1px solid #d0d7de;">데이터 전처리와 후보 문장, 대화 구조 정리를 담당해주었고, RAG 파이프라인을 세분화하여 기존 구조와 병합하는 데 기여해주었습니다.</td>
    </tr>
    <tr>
      <td align="center" style="border:1px solid #d0d7de;">전승권</td>
      <td style="border:1px solid #d0d7de;">감정 및 위험도 분석 기준을 정리해주었고, 개발 중 발생한 오류를 함께 해결하며 프로젝트 진행 속도를 높이는 데 도움을 주었습니다.</td>
    </tr>
    <!-- 박소윤 -->
    <tr>
      <td rowspan="3" align="center" style="border:1px solid #d0d7de;"><b>박소윤</b></td>
      <td align="center" style="border:1px solid #d0d7de;">김용욱</td>
      <td style="border:1px solid #d0d7de;">RAG 파이프라인 구축과 Vector DB 구성, 프롬프트 설계를 담당하여 검색과 답변 생성의 기반 구조를 구현해주었습니다. 특히 RAG 흐름 설계 과정에서 핵심 기능 개발에 기여해주었습니다.</td>
    </tr>
    <tr>
      <td align="center" style="border:1px solid #d0d7de;">윤찬호</td>
      <td style="border:1px solid #d0d7de;">데이터 전처리와 RAG 검색 구조 비교, Retrieval 성능 평가를 담당하여 데이터 품질 확보와 검색 성능 개선에 기여해주었습니다.</td>
    </tr>
    <tr>
      <td align="center" style="border:1px solid #d0d7de;">전승권</td>
      <td style="border:1px solid #d0d7de;">환경설정과 API 연동, 앱 구조 정리를 담당하여 프로젝트가 정상적으로 실행될 수 있는 기반을 마련해주었습니다.</td>
    </tr>
    <!-- 윤찬호 -->
    <tr>
      <td rowspan="3" align="center" style="border:1px solid #d0d7de;"><b>윤찬호</b></td>
      <td align="center" style="border:1px solid #d0d7de;">김용욱</td>
      <td style="border:1px solid #d0d7de;">Vector DB 구축과 프롬프트 설계를 진행해주시고, RAG 문서 검색 파이프라인 구성에도 기여해주셔서 프로젝트 완성도 향상에 도움이 되었습니다.</td>
    </tr>
    <tr>
      <td align="center" style="border:1px solid #d0d7de;">박소윤</td>
      <td style="border:1px solid #d0d7de;">프로젝트 주제 선정과 역할 분배 과정에서 먼저 나서주셔서 팀이 방향을 빠르게 정하고 원활하게 출발할 수 있었습니다.</td>
    </tr>
    <tr>
      <td align="center" style="border:1px solid #d0d7de;">전승권</td>
      <td style="border:1px solid #d0d7de;">갈등 상황에서 감정과 위험도를 분석하는 역할을 맡아 프로젝트의 핵심 차별점을 잘 살려주었습니다.</td>
    </tr>
    <!-- 전승권 -->
    <tr>
      <td rowspan="3" align="center" style="border:1px solid #d0d7de;"><b>전승권</b></td>
      <td align="center" style="border:1px solid #d0d7de;">김용욱</td>
      <td style="border:1px solid #d0d7de;">RAG 파트에서 벡터 DB를 깔끔하게 구축해주었습니다.</td>
    </tr>
    <tr>
      <td align="center" style="border:1px solid #d0d7de;">박소윤</td>
      <td style="border:1px solid #d0d7de;">프로젝트 전반에서 의견 표현이 명확했고, 역할 분배를 주도하여 팀 진행에 도움이 되었습니다.</td>
    </tr>
    <tr>
      <td align="center" style="border:1px solid #d0d7de;">윤찬호</td>
      <td style="border:1px solid #d0d7de;">전처리 데이터셋을 담당하여 자료 준비가 수월해졌고, 프로젝트 수행에 도움이 되었습니다.</td>
    </tr>

  </tbody>
</table>