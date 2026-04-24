# 컬럼 역할 표 (Column Dictionary)

본 문서는 프로젝트에서 사용된 주요 데이터셋의 컬럼 정의 및 활용 목적을 정리한 문서이다.  
데이터 이해 및 RAG 시스템 구성 시 참조 기준으로 활용된다.

---

## 📁 대상 파일

- `continuous_dialogue_dialogue.csv`
- `continuous_dialogue_utterance.csv`
- `rag_documents.csv`
- `response_pairs.csv`

---

## 📁 continuous_dialogue_dialogue

| 컬럼명 | 의미 | 활용 |
|--------|------|------|
| dialogue_group_id | 대화 그룹 고유 ID | 대화 단위 추적 |
| full_dialogue | 전체 대화 텍스트 | 대화 흐름 분석 |
| emotion_sequence | 감정 흐름 시퀀스 | 감정 변화 분석 |
| turn_count | 총 발화 수 | 대화 길이 분석 |

---

## 📁 continuous_dialogue_utterance

| 컬럼명 | 의미 | 활용 |
|--------|------|------|
| dialogue_group_id | 대화 그룹 고유 ID | 대화 연결 |
| turn_index | 발화 순서 | 흐름 파악 |
| utterance | 발화 텍스트 | 감정 분석 입력 |
| emotion | 감정 라벨 | 분류 기준 |

---

## 📁 rag_documents

| 컬럼명 | 의미 | 활용 |
|--------|------|------|
| dialogue_id | 대화 ID | 검색 추적 |
| file_name | 파일명 | 출처 추적 |
| relation | 관계 유형 | 필터링 |
| situation | 상황 요약 | 검색 |
| speaker_emotion | 화자 감정 | 조건 검색 |
| listener_behavior | 청자 반응 | 참고 |
| avg_rating | 평균 평점 | 품질 기준 |
| grade | 등급 | 품질 분류 |
| speaker_texts | 화자 발화 | 패턴 분석 |
| listener_texts | 청자 발화 | 패턴 분석 |
| full_dialogue | 전체 대화 | 근거 문서 |
| listener_empathy_tags | 공감 태그 | 유형 분석 |
| final_speaker_change_emotion | 감정 변화 | 효과 분석 |
| risk_level | 위험도 | 필터링 |
| turn_count | 발화 수 | 길이 참고 |
| terminated | 종료 여부 | 흐름 판단 |

---

## 📁 response_pairs

| 컬럼명 | 의미 | 활용 |
|--------|------|------|
| dialogue_id | 대화 ID | 추적 |
| relation | 관계 유형 | 필터링 |
| situation | 상황 | 문맥 |
| speaker_emotion | 감정 | 추천 |
| context_before_response | 직전 문맥 | 입력 |
| listener_response | 응답 | 예시 |
| listener_empathy | 공감 유형 | 스타일 |
| terminate | 종료 여부 | 결과 |

---

## 📌 비고

- 일부 컬럼은 전처리 과정에서 결측값 보정 수행
- 감정 및 공감 관련 컬럼은 모델 학습 및 RAG 필터링에 핵심적으로 사용됨
- `rag_documents`는 벡터DB 저장을 위한 최종 문서 단위 데이터셋임