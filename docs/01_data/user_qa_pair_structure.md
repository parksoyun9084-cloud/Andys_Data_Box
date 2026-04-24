# 사용자 관점 질문-답변 페어 구조

## 1. 문서 목적

본 문서는 기존 `response_pairs.csv`를 사용자 관점에서 바로 활용 가능한 질문-답변 페어 구조로 재구성하기 위한 기준을 정의한다.

기존 데이터는 데이터셋 관점의 역할명(`speaker`, `listener`)을 사용하고 있어, 실제 챗봇 서비스에서 그대로 사용하기에는 해석 비용이 존재한다.

따라서 본 문서에서는 데이터를 **사용자-챗봇 관점으로 재구성하여 RAG 검색 및 답변 생성에 최적화된 구조를 정의**한다.

---

## 2. 기존 구조의 한계

기존 `response_pairs.csv`는 다음과 같은 한계를 가진다.

- `speaker` / `listener` 구조 → 서비스 관점에서 직관성이 낮음
- 질문-답변 구조가 명확하게 분리되지 않음
- 마지막 사용자 발화(user question)가 명확히 정의되지 않음
- RAG 검색에 필요한 필드가 분산되어 있음

따라서, 이를 해결하기 위해 사용자 중심 QA 구조를 별도로 설계한다.

---

## 3. 역할 재정의

| 원본 역할 | 사용자 관점 역할 | 의미 |
|---|---|---|
| speaker | user | 사용자의 발화 (고민, 감정, 질문) |
| listener | assistant | 챗봇 또는 상담형 응답 |

---

## 4. 생성 파일

생성되는 파생 데이터:

- `data/processed/user_qa_pairs.csv`

### 처리 원칙

- 원본 파일(`response_pairs.csv`, `rag_documents.csv`)은 수정하지 않는다.
- 기존 데이터는 그대로 유지하고, 파생 데이터만 생성한다.
- 사용자 관점 구조는 별도 문서 및 파일로 관리한다.

---

## 5. 구조 정의

`user_qa_pairs.csv`는 **assistant 응답 1개를 기준으로 1행을 구성**한다.

즉, 한 행은 다음 의미를 가진다.

> 사용자가 특정 상황과 감정 상태에서 발화를 했고,  
> 이에 대해 assistant가 제공할 수 있는 적절한 답변을 정의한 구조

---

## 6. 컬럼 정의

| 컬럼명 | 의미 | 생성 기준 |
|---|---|---|
| qa_pair_id | QA 페어 고유 ID | `dialogue_id + response_index` |
| dialogue_id | 원본 대화 ID | `response_pairs.csv` |
| response_index | 응답 순번 | 대화별 누적 순번 |
| relation | 관계 유형 | 원본 |
| situation | 상황 요약 | 원본 |
| user_emotion | 사용자 감정 | `speaker_emotion` |
| risk_level | 갈등 위험도 | `rag_documents.csv`에서 join |
| user_context | 답변 직전 대화 맥락 | role 변환 적용 |
| user_question | 마지막 사용자 발화 | context에서 추출 |
| assistant_answer | 추천 답변 | `listener_response` |
| answer_empathy | 공감 유형 | `listener_empathy` |
| is_terminal | 대화 종료 여부 | `terminate` |
| grade | 품질 등급 | `rag_documents.csv` |
| avg_rating | 평균 평점 | `rag_documents.csv` |
| final_speaker_change_emotion | 감정 변화 | `rag_documents.csv` |

---

## 7. 예시

```text
user_context:
user: 자기야, 나 결국 돈 아끼기에 실패했어.
assistant: 어라, 왜 그래? 큰돈 나갈 일이 있었어?
user: 아니, 요즘 미세먼지가 너무 심해서 결국 공기청정기를 샀잖아.

user_question:
아니, 요즘 미세먼지가 너무 심해서 결국 공기청정기를 샀잖아.

assistant_answer:
한참 고민하더니 결국 샀구나? 공기는 안 좋고, 공기청정기 금액은 싸지도 않고, 고민 많았을 텐데.
```

---
## 8. 활용 방식

### 8.1 RAG 검색

다음 컬럼을 검색 및 필터링에 활용한다.

- `situation`
- `user_emotion`
- `risk_level`
- `user_context`
- `user_question`

→ 사용자 상황 + 감정 + 맥락 기반 검색 가능

---

### 8.2 답변 생성

다음 컬럼을 답변 생성 참고 데이터로 활용한다.

- `assistant_answer`
- `answer_empathy`
- `grade`
- `avg_rating`

→ 품질 기반 응답 생성 및 스타일 제어 가능

---

### 8.3 UI 및 서비스 적용

서비스에서는 내부 데이터 구조를 그대로 노출하지 않고 다음과 같이 매핑한다.

- 사용자 입력 → `user_question`
- 이전 대화 → `user_context`
- 추천 답변 → `assistant_answer`
- 공감 유형 → `answer_empathy`

---

## 9. 생성 방식

### 스크립트

- `src/build_user_qa_pairs.py`
- `src/build_user_qa_pairs.ps1`

### 결과

- `data/processed/user_qa_pairs.csv`

---

## 10. 설계 특징

본 구조는 다음과 같은 특징을 가진다.

- 사용자 중심 데이터 구조 재설계
- RAG 검색에 최적화된 필드 구성
- 질문-답변 구조 명확화
- 기존 데이터와의 호환성 유지 (원본 수정 없음)

---

## 11. 최종 정리

`user_qa_pairs.csv`는 기존 `response_pairs.csv`를 기반으로 생성된 **서비스 최적화형 QA 데이터셋**이다.

해당 구조를 통해  
- RAG 검색 정확도를 향상시키고  
- 실제 사용자에게 자연스러운 답변을 제공할 수 있도록 설계하였다.
