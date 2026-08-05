# 분석 계획서

작성일: 2026-08-03

---

## 1. 연구 가설 또는 연구 질문

### 배경
기존 partial audio forgery 탐지 모델(CFPRF 등)은 PartialSpoof 등 영어/중국어 중심 데이터셋에서 학습·평가되었으며, in-domain에서는 SOTA 성능(EER 7.61%)을 보이나 out-of-domain(LlamaPartialSpoof, Half-Truth)에서는 EER이 27~43%까지 급격히 악화된다고 보고됨. 이는 언어·TTS 모델·도메인이 바뀔 때 기존 탐지 모델의 일반화 성능에 근본적 한계가 있음을 시사함.

### 연구 질문
1. **(RQ1, 주 연구질문)** 한국어(Zeroth-Korean) 기반 partial fake 음성에 대해, 영어/중국어 중심으로 학습된 기존 탐지 모델(CFPRF, Split&Conquer)의 탐지 성능(EER)은 어떻게 나타나는가?
2. **(RQ2)** 조작에 사용된 TTS 모델(GPT-SoVITS / CosyVoice2 / VITS)의 종류에 따라 탐지 성능이 달라지는가? 즉 탐지 모델이 특정 TTS의 아티팩트에 편향되어 있는가?
3. **(RQ3)** 발화 내 조작 비율(저 ~15% / 중 15~30% / 고 30%~)이 커질수록 탐지 성능(EER, 위치 특정 정확도)이 어떻게 변화하는가?
4. **(RQ4)** CFPRF와 Split&Conquer 중 어느 모델이 한국어 도메인에서 더 강건한가, 그리고 두 모델의 실패 양상(어느 조건에서 EER이 높아지는가)에 차이가 있는가?

### 가설
- H1: 기존 탐지 모델은 한국어 partial fake에 대해 선행 연구의 out-of-domain 결과(EER 25~40%대)와 유사하거나 그 이상으로 성능이 저하될 것이다.
- H2: 조작 비율이 낮을수록(저 구간) 탐지가 어려워 EER이 높게 나타날 것이다.
- H3: TTS 모델별로 남기는 아티팩트가 달라 탐지 성능에 유의한 차이가 발생할 것이다.

---

## 2. 사용 모델

| 모델 | 유형 | 출력 | 근거 |
|---|---|---|---|
| **CFPRF** | 2단계 (FDN + PRN) | 프레임 단위(20ms) 진위 판별 + 조작 구간 위치(start/end) | ACM MM 2024, PartialSpoof 기준 SOTA 보고 |
| **Split&Conquer** | 경계 탐지 + 구간 분류 분리형 | 조작 구간 위치 | PartialSpoof 벤치마크 여러 시간 해상도 SOTA |

두 모델 모두 원저자 공개 pretrained weight(PartialSpoof로 학습된 버전)를 그대로 사용하여, **재학습 없이 cross-domain(한국어) 평가**를 수행함 (LlamaPartialSpoof 논문의 out-of-domain 평가 설계를 따름).

---

## 3. 비교 모델 (조작에 사용한 TTS 모델)

| 모델 | 특성 | 선정 사유 |
|---|---|---|
| **GPT-SoVITS** | VITS 계열 파인튜닝, 중국어 중심 학습 | 커뮤니티에서 가장 널리 쓰이는 한국어 지원 TTS, baseline 성격 |
| **CosyVoice2 (Fun-CosyVoice 3.0)** | LLM 기반 zero-shot, 9개 언어 명시 지원(한국어 포함) | 실험적으로 GPT-SoVITS 대비 한국어 자연스러움 우수 확인 |
| **VITS (기본)** | End-to-end 고전 구조, non-autoregressive | 구조적으로 가장 단순한 원조 모델, 아키텍처 비교 축의 baseline 역할 |

실험적으로 GPT-SoVITS는 짧은 어절(0.55초)이 2.06초로 늘어지는 등 한국어에서 속도·억양 왜곡이 확인되었고, CosyVoice2는 원본과 유사한 속도로 자연스럽게 합성됨. VITS는 아직 실험적으로 확인되지 않아 별도 검증 필요. 이 품질 차이 자체가 RQ2의 분석 대상.

---

## 4. 데이터 분할 방법

### 원칙
ASVspoof2019 / PartialSpoof / PartialEdit의 관례에 따라 **화자 분리(speaker-disjoint) 분할**을 적용. 동일 화자가 여러 split에 걸치지 않도록 화자 단위로 분할하여, 탐지 모델이 조작이 아닌 화자 특성을 학습하는 것을 방지.

### 적용
- 대상: 113명 화자, 1,120개 원본 발화(화자당 10개)
- 분할 비율: train 70% / val 15% / test 15% (화자 단위)
- 결과: train 78명(780개) / val 16명(160개) / test 18명(180개)
- **검증 필수**: 동일 원본 발화의 저/중/고 구간 버전이 서로 다른 split에 걸치지 않도록 `orig_idx` 기준 확인 (데이터 품질 점검 보고서 6번 항목과 연동)

---

## 5. 전처리 방법

1. **발화 선정**: Zeroth-Korean 전체(22,720개) 중 길이 p5~p95(5.0~13.3초), 화자당 20개 이상 보유 화자(113명)에서 화자당 10개 무작위 표집 (seed=42)
2. **텍스트 수정**: 원본 발화의 마지막 절(2/3/5어절)의 의미를 바꾸는 내용어로 치환
3. **TTS 합성**: 7초 내외 레퍼런스 음성으로 zero-shot 음성 클로닝 (GPT-SoVITS, CosyVoice2, VITS 각각)
4. **위치 정렬**: torchaudio MMS_FA(forced alignment)로 원본·합성음 양쪽에서 단어 단위 타임스탬프 추출, 한글은 uroman으로 로마자 변환 후 정렬
5. **접합점 보정**: 정렬 경계를 무음 구간 중앙(`snap_to_silence`)으로 스냅하여 파형 불연속 최소화
6. **볼륨 정규화**: ITU-T SV56 표준에 따라 -26 dBov로 정규화 (볼륨 차이가 탐지 단서로 작용하는 것을 방지, PartialSpoof 방법론 준용)
7. **접합**: 15ms 크로스페이드로 원본-합성-원본 스플라이싱
8. **라벨링**: 각 샘플에 조작 구간의 정확한 시작/끝 시간(초) 기록 → CFPRF/Split&Conquer 평가용 ground truth

---

## 6. 평가 지표

### 기본 지표
- **Utterance-level EER**: 발화 전체가 진짜/가짜인지 이진 판별 성능
- **Segment-level EER** (20ms 해상도): 프레임 단위 조작 위치 판별 성능

### 보완 지표 (EER의 한계 보완)
최근 연구에서 EER이 threshold-dependent하지 않아 실배포 환경의 유용성을 가리는 한계가 지적되었으므로, threshold 고정 후 다음 지표를 함께 보고:
- Accuracy, Precision, Recall, F1-score (EER 지점의 threshold 기준)

### 위치 특정 정확도
- 예측 조작 구간과 ground truth 구간의 IoU (Intersection over Union)
- mAP (temporal forgery localization 관례)

### TTS 품질 지표 (RQ2 보조)
- MOS 추정 (DistillMOS 등 사전학습 모델, PartialEdit 방법론 준용)
- 화자 유사도(speaker similarity), WER(합성 텍스트 재인식 정확도)

---

## 7. 통계적 검정 방법

| 비교 대상 | 검정 방법 | 목적 |
|---|---|---|
| CFPRF vs Split&Conquer의 EER 차이 | Bootstrap 신뢰구간 (1,000회 resampling) | EER 차이가 표본 변동 범위를 벗어나는지 확인 |
| TTS 모델(GPT-SoVITS/CosyVoice2/VITS) 3종 간 탐지 정확도 차이 | Cochran's Q test (동일 발화 반복측정, 3개 이상 조건) | 세 TTS 조건에서 탐지 성공/실패 패턴이 유의하게 다른지 |
| 위 Cochran's Q 유의 시 | McNemar's test (쌍별 사후검정, Bonferroni 보정) | 어느 TTS 모델 쌍 간에 유의한 차이가 있는지 특정 |
| 조작 비율(저/중/고) 구간 간 EER 차이 | Kruskal-Wallis test (비모수, 3개 이상 그룹) | 구간별 EER 차이가 우연이 아닌지 |
| 위 Kruskal-Wallis 유의 시 | Dunn's test (사후검정) | 어느 구간 쌍이 유의하게 다른지 특정 |

모든 검정은 유의수준 α=0.05 기준, 다중비교 시 Bonferroni 보정 적용.

---

## 8. 주요 실험 목록

| # | 실험명 | 내용 | 대응 RQ |
|---|---|---|---|
| E1 | In-domain 재현 | CFPRF/Split&Conquer를 PartialSpoof 원 평가셋에서 재현하여 보고된 EER과 비교 (재현성 확인) | 사전 검증 |
| E2 | 한국어 cross-domain 평가 | 본 데이터셋 전체(test split)로 CFPRF/Split&Conquer 평가, EER 산출 | RQ1 |
| E3 | TTS 모델별 성능 분해 | GPT-SoVITS/CosyVoice2/VITS 생성분을 나누어 EER 비교 | RQ2 |
| E4 | 조작 비율별 성능 분해 | 저/중/고 구간별로 나누어 EER 및 IoU 비교 | RQ3 |
| E5 | 모델 간 비교 | CFPRF vs Split&Conquer의 전체 성능 및 실패 사례 비교 분석 | RQ4 |
| E6 | 실패 사례 정성 분석 | EER이 높게 나온 샘플들의 공통 특성(조작 위치, 화자, TTS 아티팩트) 분석 | RQ1~4 종합 |
| E7 (선택) | Threshold 민감도 분석 | EER 임계값 대신 고정 threshold에서의 Precision/Recall/F1 산출, 실배포 관점 평가 | 보완 지표 검증 |

---

## 9. 아직 확정되지 않은 부분

| 항목 | 상태 |
|---|---|
| CFPRF/Split&Conquer의 정확한 입력 포맷(샘플레이트, 세그먼트 길이) | 레포 확인 필요 (학교 GPU 서버에서 설치 후 확정) |
| E1(in-domain 재현) 수행 여부 | 시간 여유에 따라 결정, 재현 안 되면 논문 신뢰도에 영향 있어 우선순위 높음 |
| MOS 추정 모델(DistillMOS 등)의 한국어 적용 가능 여부 | 별도 검증 필요 |
