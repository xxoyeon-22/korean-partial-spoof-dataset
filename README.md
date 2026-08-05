<div align="center">

# Korean Partial Deepfake Speech Dataset

**한국어 부분 위조 음성 데이터셋 구축 및 탐지 모델 일반화 평가**

[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Status](https://img.shields.io/badge/status-in%20progress-yellow?style=flat-square)]()

</div>

---

## 개요

발화 전체가 아닌 **일부 구간만 TTS 합성음으로 교체된 음성**(partial deepfake)을 한국어로 구축하고,
영어·중국어 중심으로 학습된 기존 탐지 모델이 한국어 도메인에서도 작동하는지 평가하는 연구입니다.

기존 partial deepfake 데이터셋은 영어(PartialSpoof), 중국어(Half-Truth), 유럽 8개 언어(HQ-MPSD)에 집중되어 있으며
**한국어 데이터셋은 부재한 상황**입니다. 본 연구는 이 공백을 메우는 것을 목표로 합니다.

### 연구 질문

| # | 질문 |
|---|---|
| RQ1 | 영어·중국어 중심으로 학습된 탐지 모델이 한국어 partial fake에서 어떤 성능을 보이는가? |
| RQ2 | 조작에 사용된 TTS 모델에 따라 탐지 성능이 달라지는가? (탐지기의 TTS 편향) |
| RQ3 | 발화 내 조작 비율이 커질수록 탐지 성능은 어떻게 변화하는가? |
| RQ4 | CFPRF와 Split&Conquer 중 한국어 도메인에서 더 강건한 모델은? |

---

## 파이프라인

```
Zeroth-Korean (22,720 utterances)
        │
        ├─ [1] 발화 선정      길이 p5~p95 필터 + 화자당 균등 표집
        │                     → 1,120 utterances (112 speakers)
        │
        ├─ [2] 텍스트 치환    LLM 기반 의미 변화 텍스트 생성
        │                     → 3,360 texts (low / mid / high 3구간)
        │
        ├─ [3] TTS 합성       GPT-SoVITS · CosyVoice2 · VITS
        │                     → 10,080 synthesized audio
        │
        ├─ [4] 정렬 & 접합    Forced alignment → 무음 지점 스냅
        │                     → 볼륨 정규화 → 크로스페이드 스플라이싱
        │
        ├─ [5] 품질 검증      전사 일치율 · 화자 유사도 · 경계 불연속
        │
        └─ [6] 탐지 모델 평가  CFPRF · Split&Conquer
                              → EER (utterance / segment level)
```

---

## 데이터셋 구성

| 항목 | 값 |
|---|---|
| 원본 코퍼스 | [Zeroth-Korean](https://openslr.org/40/) (CC BY 4.0) |
| 선정 발화 | 1,120개 (112명 화자 × 10개) |
| 발화 길이 | 5.0 ~ 13.3초 (전체 분포 p5~p95) |
| TTS 모델 | GPT-SoVITS, CosyVoice2, VITS |
| 조작 비율 구간 | low (~15%) / mid (15~30%) / high (30%~) |
| 목표 규모 | 11,200 발화 (genuine 1,120 + fake 10,080), 약 24.7시간 |
| 분할 | 화자 분리(speaker-disjoint) train 78 / val 16 / test 18명 |

### 설계 원칙

- **화자 분리 분할** — 동일 화자가 여러 split에 걸치지 않도록 하여, 모델이 조작이 아닌 화자 특성을 학습하는 것을 방지 (ASVspoof2019 / PartialSpoof 관례)
- **볼륨 정규화** — 볼륨 차이가 조작 탐지의 단서로 작용하지 않도록 정규화
- **무음 지점 접합** — 발음 중간이 아닌 무음 구간에서 접합하여 경계 아티팩트 최소화
- **조작 비율 통제** — 동일 발화 내에서 교체 어절 수를 조절하여 발화 길이와 조작 비율 간 교란 제거

---

## 저장소 구조

```
.
├── src/
│   ├── data/
│   │   ├── analyze_distribution.py    # Zeroth 발화 길이/어절 분포 분석
│   │   └── select_utterances.py       # 발화 표집 + 화자 분리 분할
│   └── generation/
│       ├── text_substitution.py       # LLM(Claude) 기반 텍스트 치환
│       ├── redo_substitution.py       # 어절 수 불일치 건 재작업
│       ├── splice_forced_align.py     # forced alignment 기반 정렬+스플라이싱
│       ├── splice_cosyvoice_manual.py # 수동 구간 지정 스플라이싱 (초기 버전)
│       ├── splice_phrase_manual.py    # 무음 탐색 기반 수동 스플라이싱 (초기 버전)
│       └── gpt_sovits_pipeline.py     # GPT-SoVITS API 기반 대화형 부분 합성
├── manifests/                # 데이터셋 매니페스트 (라벨 원장)
│   ├── selected_utterances.csv
│   └── text_substituted.csv
├── data/                     # (gitignore) 오디오 및 중간 산출물
├── docs/
│   ├── selection_criteria.md # 발화 선정 기준 근거
│   ├── analysis_plan.md      # 분석 계획서
│   ├── related_work.md       # 선행 연구 정리
│   ├── pipeline.md           # 생성 파이프라인 실행 계획
│   └── progress_report.md    # 연구 진행 상황 보고서
├── requirements.txt
└── README.md
```

> `src/quality/` (자동 품질 검사), `src/evaluation/` (탐지 모델 평가), `configs/` 는
> 아직 구현 전 단계로, 아래 진행 상황을 참고하세요.

---

## 설치

```bash
conda create -n kpd python=3.10 -y
conda activate kpd
pip install -r requirements.txt
```

`src/generation/text_substitution.py`, `redo_substitution.py`는 Anthropic API를 사용합니다.

```bash
export ANTHROPIC_API_KEY="your-key"   # 절대 코드에 하드코딩하지 마세요
```

---

## 사용법

### 1. 발화 분포 분석 + 발화 선정

```bash
python src/data/analyze_distribution.py --output manifests/zeroth_meta.csv
python src/data/select_utterances.py \
    --input manifests/zeroth_meta.csv \
    --min-utterances 20 \
    --per-speaker 10 \
    --seed 42 \
    --output manifests/selected_utterances.csv
```

### 2. 텍스트 치환

```bash
python src/generation/text_substitution.py \
    --input manifests/selected_utterances.csv \
    --output manifests/text_substituted.csv

# 어절 수가 안 맞는 건만 재작업
python src/generation/redo_substitution.py --manifest manifests/text_substituted.csv
```

### 3. 정렬 + 스플라이싱

```bash
python src/generation/splice_forced_align.py \
    --orig-file data/sample.wav --tts-file data/sample-CosyVoice2.wav \
    --orig-text "..." --tts-text "..." \
    --orig-first-word 일을 --orig-last-word 실천하겠습니다 \
    --tts-first-word 일을 --tts-last-word 포기하겠습니다 \
    --output data/partial_fake/sample.wav
```

---

## 매니페스트 형식

`manifests/text_substituted.csv`의 각 행은 하나의 텍스트 치환 결과입니다.

| 필드 | 설명 |
|---|---|
| `sample_id` | 원본 발화 ID (예: `zk_00000`) |
| `speaker` | Zeroth-Korean 원본 화자 ID |
| `dataset_split` | train / val / test (화자 분리) |
| `ratio_bin` | low / mid / high (조작 비율 구간) |
| `n_words_replaced` | 치환된 어절 수 (2 / 3 / 5) |
| `original_text` / `new_text` | 원본 / 치환된 전체 문장 |
| `replaced_tail` | 치환된 마지막 n어절 |
| `word_count_ok` | 어절 수 검증 통과 여부 |

TTS 합성 및 스플라이싱 이후에는 `audio_path`, `fake_start`, `fake_end`, `label` 필드가
추가되어 segment-level 탐지 모델 평가의 ground truth로 사용될 예정입니다.

---

## 진행 상황

- [x] 선행 연구 조사
- [x] Zeroth 분포 분석 및 발화 선정 기준 확립
- [x] 원본 발화 1,120개 표집 및 화자 분리 분할
- [x] 텍스트 치환 3,360건 생성
- [x] 파이프라인 단건 검증 (청취상 조작 여부 구분 불가 수준 확인)
- [ ] TTS 3종 대량 합성
- [ ] 자동 품질 검증 (`src/quality/`)
- [ ] CFPRF / Split&Conquer 평가 (`src/evaluation/`)

자세한 내용은 [docs/progress_report.md](docs/progress_report.md)를 참고하세요.

---

## 라이선스 및 윤리 고지

- 원본 코퍼스 [Zeroth-Korean](https://openslr.org/40/)은 **CC BY 4.0**으로 배포됩니다.
- 본 데이터셋은 **딥페이크 탐지 연구 목적으로만** 사용되어야 합니다.
- 음성 클로닝 기술은 사칭·사기에 악용될 수 있습니다. 본 저장소의 코드와 데이터를
  타인을 기만하거나 피해를 입히는 목적으로 사용하는 것을 **엄격히 금지**합니다.
- 화자 정보는 원본 코퍼스의 익명 ID를 그대로 사용하며, 개인 식별 정보를 추가로 수집하지 않습니다.

---

## 참고 문헌

주요 참고 연구는 다음과 같습니다.

- Zhang et al., *The PartialSpoof Database and Countermeasures...*, IEEE/ACM TASLP 2023
- Yi et al., *Half-Truth: A Partially Fake Audio Detection Dataset*, Interspeech 2021
- Wu et al., *Coarse-to-Fine Proposal Refinement Framework (CFPRF)*, ACM MM 2024
- Luong et al., *LlamaPartialSpoof*, ICASSP 2025
- Li et al., *HQ-MPSD: A Multilingual Artifact-Controlled Benchmark*, 2025

전체 목록은 [docs/related_work.md](docs/related_work.md)를 참고하세요.
