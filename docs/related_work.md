# 선행 연구 정리

작성일: 2026-08-04
정리 대상: partial audio deepfake 탐지 관련 주요 논문 13편

---

## 1. PartialSpoof (Zhang et al., 2021/2023)

| 항목 | 내용 |
|---|---|
| **논문 제목** | The PartialSpoof Database and Countermeasures for the Detection of Short Fake Speech Segments Embedded in an Utterance |
| **연구 목적** | 발화 전체가 아닌 일부 구간만 합성음으로 대체된 "부분 위조" 음성을 탐지하고, 그 위치를 프레임 단위로 특정하는 문제를 정식 태스크로 정립 |
| **사용 데이터** | ASVspoof2019 LA 기반으로 구축. Train 진짜 2,580 / 가짜 22,800, Dev 진짜 2,548 / 가짜 22,296, Eval 진짜 7,355 / 가짜 63,882 |
| **분석 방법/모델** | 다중 해상도(multi-resolution) segment-level 판별. VAD 3종 다수결로 구간 탐지, 시간영역 상호상관(cross-correlation)으로 최적 접합점 계산(무음 영역 고려), ITU-T SV56 기준 -26 dBov 볼륨 정규화 |
| **평가 지표** | Utterance-level EER, Segment-level EER (20ms~640ms 다중 해상도) |
| **주요 결과** | 부분 위조 탐지가 발화 단위 탐지보다 훨씬 어렵다는 것을 정량적으로 입증. 이후 모든 partial spoof 연구의 표준 벤치마크가 됨 |
| **연구의 한계** | 영어(ASVspoof2019 LA) 단일 언어. TTS 시스템이 2019년 기준으로 현재 기술 대비 구식. 텍스트 의미 변화가 아닌 단순 구간 삽입 방식 |
| **본인 연구와의 차이** | 본 연구는 한국어(Zeroth) 기반이며, 최신 TTS(CosyVoice2 등) 사용. 볼륨 정규화·접합점 탐색 방법론은 이 논문을 그대로 준용 |

---

## 2. Half-Truth / HAD (Yi et al., Interspeech 2021)

| 항목 | 내용 |
|---|---|
| **논문 제목** | Half-Truth: A Partially Fake Audio Detection Dataset |
| **연구 목적** | 발화 내 일부 단어만 합성음으로 교체한 "반쪽 진실" 음성 데이터셋을 구축하여, 이진 진위 판별을 넘어선 탐지 연구를 촉진 |
| **사용 데이터** | AISHELL-3(중국어) 기반. 원본 발화의 특정 단어를 TTS 합성음으로 교체 |
| **분석 방법/모델** | 데이터셋 논문. baseline으로 기존 anti-spoofing 모델을 적용 |
| **평가 지표** | EER |
| **주요 결과** | 기존 발화 단위 탐지 모델이 부분 위조에서 성능이 크게 저하됨을 보임. PartialSpoof와 함께 partial spoof 분야의 양대 표준 데이터셋이 됨 |
| **연구의 한계** | 중국어 단일 언어. 교체 단위가 단어 중심이라 자연스러움에 한계 |
| **본인 연구와의 차이** | 본 연구는 한국어 대상이며, 단어 단위가 아닌 절(phrase) 단위 교체를 채택. 또한 조작 비율을 통제 변수로 설계 |
| **⚠️ 확인 필요** | DOI(10.21437/interspeech.2021-1955) 원문을 직접 확인하여 데이터 규모(발화 수, 시간)를 정확히 채울 것. 위 내용은 일반적으로 알려진 수준의 기술이며 세부 수치는 미확인 |

---

## 3. ADD 2023 (Yi et al., 2023)

| 항목 | 내용 |
|---|---|
| **논문 제목** | ADD 2023: the Second Audio Deepfake Detection Challenge |
| **연구 목적** | 이진 진위 판별의 한계를 넘어, 부분 위조 음성 내 조작 구간을 실제로 위치 특정하고 생성에 사용된 알고리즘까지 식별하는 기술 개발을 촉진 |
| **사용 데이터** | 챌린지 주최 측 제공 데이터셋(중국어 중심) |
| **분석 방법/모델** | 3개 서브챌린지 구성: 오디오 페이크 게임(FG), 조작 구간 위치 특정(RL), 딥페이크 알고리즘 인식(AR) |
| **평가 지표** | 서브챌린지별 상이. RL 트랙에서 구간 위치 특정 정확도 평가 |
| **주요 결과** | 부분 위조의 "위치 특정(localization)"을 공식 태스크로 확립. ADD 2022 대비 페이크 오디오 게임 평가 라운드를 확대 |
| **연구의 한계** | 챌린지 특성상 특정 데이터셋에 최적화된 방법이 상위권을 차지하는 경향. 중국어 중심 |
| **본인 연구와의 차이** | 본 연구는 챌린지 참가가 아닌 독립 데이터셋 구축 및 기존 모델의 cross-domain 일반화 평가가 목적 |

---

## 4. CFPRF (Wu et al., ACM MM 2024) — 주요 평가 대상 모델

| 항목 | 내용 |
|---|---|
| **논문 제목** | Coarse-to-Fine Proposal Refinement Framework for Audio Temporal Forgery Detection and Localization |
| **연구 목적** | 부분 위조 음성의 조작 구간을 대략 탐지한 뒤 경계를 정밀하게 다듬는 2단계 방식으로 위치 특정 정확도를 향상 |
| **사용 데이터** | PartialSpoof, LAV-DF 등 |
| **분석 방법/모델** | FDN(Frame-level Detection Network)이 진짜/가짜 프레임 간 불일치 단서로 20ms 단위 대략 후보 구간 탐지 → PRN(Proposal Refinement Network)이 경계를 정밀 보정 |
| **평가 지표** | Segment-level EER(다중 해상도), Utterance-level EER, mAP |
| **주요 결과** | PartialSpoof 기준 20ms 해상도 EER 7.61%, 발화 단위 EER 1.72%로 당시 SOTA |
| **연구의 한계** | in-domain 성능은 뛰어나나 out-of-domain에서 급격히 저하(후속 연구에서 EER 27.59%로 확인). in-domain과 out-of-domain 간 최적 임계값 격차가 커서 실배포 시 성능 하락 위험 |
| **본인 연구와의 차이** | 본 연구는 CFPRF를 **평가 대상**으로 사용. 재학습 없이 한국어 데이터에 적용하여 cross-lingual 일반화 한계를 검증 |
| **저장소** | https://github.com/ItzJuny/CFPRF |

---

## 5. Split & Conquer (Rimon et al., 2026) — 주요 평가 대상 모델

| 항목 | 내용 |
|---|---|
| **논문 제목** | (Split-and-Conquer framework for partial deepfake speech detection) |
| **연구 목적** | 시간적 위치 특정과 진위 판별을 명시적으로 분리하여 각 단계가 명확히 정의된 과제에 집중하도록 학습 목표를 단순화 |
| **사용 데이터** | PartialSpoof, Half-Truth |
| **분석 방법/모델** | 2단계 구조. (1) 전용 경계 탐지기가 시간적 전환점을 먼저 식별하여 음향적으로 일관된 구간으로 분할 (2) 각 구간을 독립적으로 진짜/가짜 판별. 추가로 가변 길이 구간을 여러 고정 길이로 변환하는 reflection 기반 multi-length 학습 전략 적용, 서로 다른 특징 추출기·증강 전략으로 학습한 모델들의 예측을 융합 |
| **평가 지표** | Segment-level EER(다중 시간 해상도), Utterance-level EER |
| **주요 결과** | PartialSpoof에서 다중 시간 해상도 및 발화 단위 모두 SOTA 달성. Half-Truth에서도 SOTA를 기록하여 일반화 능력 확인 |
| **연구의 한계** | 평가가 PartialSpoof·Half-Truth(영어·중국어)에 한정. 다국어 검증 부재 |
| **본인 연구와의 차이** | 본 연구는 Split&Conquer를 **평가 대상**으로 사용. CFPRF와 구조적으로 유사(경계 탐지 → 구간 분류)하나 분리 정도가 더 명시적이라는 점에서 비교 가치가 있음 |

---

## 6. TDAM (Li, Zhang & Zhao, IEEE SPL 2025)

| 항목 | 내용 |
|---|---|
| **논문 제목** | Frame-level Temporal Difference Learning for Partial Deepfake Speech Detection |
| **연구 목적** | 프레임 단위 주석(annotation)에 의존하는 기존 방식의 확장성 한계를 극복하고, 경계 아티팩트가 아닌 시간적 변화의 부자연스러움 자체로 탐지 |
| **사용 데이터** | PartialSpoof, HAD |
| **분석 방법/모델** | TDAM(Temporal Difference Attention Module). 딥페이크 음성이 진짜 음성 대비 불규칙한 방향 변화와 부자연스러운 국소 전환을 보인다는 발견에 기반. 이중 계층 차이 표현으로 미세·거시 스케일 시간 불규칙성 포착, adaptive average pooling으로 가변 길이 입력의 핵심 패턴 보존 |
| **평가 지표** | EER |
| **주요 결과** | 프레임 단위 지도 학습 없이 PartialSpoof EER 0.59%, HAD EER 0.03% 달성 |
| **연구의 한계** | 극도로 낮은 EER은 in-domain 결과이며 cross-domain 검증 부재. HQ-MPSD 등 고품질 데이터셋에서의 성능은 미확인 |
| **본인 연구와의 차이** | 본 연구는 새 탐지 모델 제안이 아닌 데이터셋 구축 및 기존 모델 평가가 목적. 다만 TDAM의 "경계 아티팩트가 점점 매끄러워진다"는 문제의식은 본 연구가 고품질 스플라이싱을 지향하는 근거와 일치 |

---

## 7. BAM (Zhong, Li & Yi, Interspeech 2024)

| 항목 | 내용 |
|---|---|
| **논문 제목** | Enhancing Partially Spoofed Audio Localization with Boundary-aware Attention Mechanism |
| **연구 목적** | 단일 모델 내에서 경계(boundary) 정보를 활용하는 미개척 주제를 탐구하여 프레임 단위 위치 특정 정확도 향상 |
| **사용 데이터** | PartialSpoof |
| **분석 방법/모델** | 2개 핵심 모듈. (1) Boundary Enhancement: 프레임 내·프레임 간 정보를 결합해 판별력 있는 경계 특징을 추출, 경계 위치 탐지와 진위 판단에 사용 (2) Boundary Frame-wise Attention: 경계 예측 결과로 프레임 간 특징 상호작용을 명시적으로 제어 |
| **평가 지표** | Segment-level EER |
| **주요 결과** | PartialSpoof에서 당시 최고 성능 달성 |
| **연구의 한계** | PartialSpoof 단일 데이터셋 평가. cross-domain 검증 부재. 경계 아티팩트에 의존하므로 고품질 스플라이싱에서는 성능 저하 예상 |
| **본인 연구와의 차이** | 본 연구는 무음 지점 스냅·크로스페이드로 경계 아티팩트를 최소화하므로, BAM 계열 방법이 취약할 조건을 의도적으로 만들어냄 |
| **저장소** | https://github.com/media-sec-lab/BAM |

---

## 8. Robust Localization / Out-of-Domain 평가 (Thi et al., 2025) — 핵심 참고 논문

| 항목 | 내용 |
|---|---|
| **논문 제목** | (Robust Localization / out-of-domain evaluation of partial deepfake detection) |
| **연구 목적** | 기존 모델들이 in-domain 성능은 강하게 보고되지만 실제 배포 환경에서의 유용성이 불분명하다는 문제를 제기하고, EER 중심 평가 관행 자체를 비판 |
| **사용 데이터** | PartialSpoof(in-domain), LlamaPartialSpoof, Half-Truth(out-of-domain) |
| **분석 방법/모델** | 기존 모델(CFPRF 등) 재현 및 재학습, 데이터 증강(MaskedSpec) 효과 검증, 파인튜닝 데이터 구성 변경 실험 |
| **평가 지표** | EER + threshold 기반 지표(Accuracy, Precision, Recall, F1) |
| **주요 결과** | CFPRF가 Half-Truth에서 EER 27.59%, 재구현 버전(reCFPRF) 14.98%, 증강 적용(reCFPRF+ms) 12.00%. 그러나 LlamaPartialSpoof에서는 +ms가 42.23%로 오히려 reCFPRF(41.72%)보다 나빠 증강 효과가 데이터셋마다 일관되지 않음. CFPRF는 in-domain/out-of-domain 간 최적 임계값 격차가 커서 in-domain에 과적합됐음을 확인. 가장 일관되게 효과적이었던 것은 증강이 아니라 **파인튜닝 데이터에 partial fake 샘플을 추가**하는 것 |
| **연구의 한계** | 여전히 영어·중국어 중심. 한국어 등 비주류 언어 미검증 |
| **본인 연구와의 차이** | 본 연구는 이 논문이 제기한 out-of-domain 일반화 문제를 **한국어라는 새로운 축**으로 확장. EER 외 threshold 기반 지표 병행 보고 방침도 이 논문을 따름 |

---

## 9. PartialEdit (Zhang et al., Interspeech 2025)

| 항목 | 내용 |
|---|---|
| **논문 제목** | (PartialEdit: partial deepfake speech dataset with neural codec editing) |
| **연구 목적** | 최신 신경 코덱 기반 음성 편집 모델로 생성한 부분 위조 음성에 대해 기존 탐지 모델의 성능을 검증 |
| **사용 데이터** | 108명 화자, 43,358개 발화. ASVspoof2019·PartialSpoof의 화자 설정을 따라 훈련 20명(8,258 발화) / 검증 20명(7,915 발화) / 평가 68명(27,185 발화)으로 화자·발화가 겹치지 않게 분할 |
| **분석 방법/모델** | 여러 신경 코덱 편집 모델로 데이터 생성. 사전학습 DistillMOS로 생성 음성의 자연스러움을 MOS로 추정 |
| **평가 지표** | EER, MOS |
| **주요 결과** | 기존 데이터셋으로 학습한 탐지 모델이 신경 코덱 편집 기반 부분 위조에 일반화되지 못함을 확인 |
| **연구의 한계** | 영어 중심. 편집 모델 종류에 따른 성능 차이 분석이 제한적 |
| **본인 연구와의 차이** | 본 연구는 화자 분리 분할 방식과 MOS 기반 품질 검증 방법론을 이 논문에서 준용. 다만 신경 코덱 편집이 아닌 zero-shot TTS 클로닝 방식을 사용하며 언어가 다름 |

---

## 10. LlamaPartialSpoof (Luong et al., ICASSP 2025) — 방법론 참고 핵심

| 항목 | 내용 |
|---|---|
| **논문 제목** | LlamaPartialSpoof: An LLM-Driven Fake Speech Dataset Simulating Disinformation Generation |
| **연구 목적** | 공격자 관점을 반영하여, LLM으로 의미를 조작한 텍스트를 음성 클로닝으로 합성한 현실적인 허위정보 시나리오 데이터셋 구축 |
| **사용 데이터** | LibriTTS 등 영어 낭독체 기반. 총 130시간, 완전 합성(fully fake)과 부분 합성(partially fake) 모두 포함 |
| **분석 방법/모델** | LLM으로 원문의 의미가 바뀌도록 문장 수정(예: 대명사·주체 변경으로 행위 주체 전환) → 타겟 화자의 3~7초 음성(또는 5개 발화)으로 클로닝 → 원본과 합성음을 조합해 부분 위조 생성. 특정 TTS에 편향되지 않도록 여러 SOTA TTS 시스템 사용 |
| **평가 지표** | EER |
| **주요 결과** | 기존 탐지 시스템이 미지의 시나리오에 일반화하지 못해 최고 성능조차 EER 24.49%에 그침. 공격자가 특정 TTS나 이어붙이기 방식에 편향된 탐지 시스템의 취약점을 악용할 수 있음을 입증 |
| **연구의 한계** | 영어 단일 언어. 조작 비율을 명시적 변수로 통제하지 않음 |
| **본인 연구와의 차이** | 본 연구는 이 논문의 설계(LLM 텍스트 조작 + 다중 TTS + 부분 합성)를 **한국어로 확장**. 추가로 조작 비율을 저/중/고 3구간으로 통제하여 독립 분석 변수로 사용하는 점이 차별됨 |

---

## 11. HQ-MPSD (Li et al., 2025) — ⚠️ 본 연구와 방법론이 가장 유사 (원문 확인 완료)

| 항목 | 내용 |
|---|---|
| **논문 제목** | HQ-MPSD: A Multilingual Artifact-Controlled Benchmark for Partial Deepfake Speech Detection |
| **저자/소속** | Menglu Li, Majd Alber, Ramtin Asgarianamiri, Lian Zhao, Xiao-Ping Zhang (Tsinghua SIGS / Toronto Metropolitan University) |
| **연구 목적** | 기존 데이터셋이 구식 합성 시스템과 단순한 생성 절차에 의존해 현실적 조작 단서가 아닌 데이터셋 고유 아티팩트를 만들어낸다는 한계를 지적하고, 아티팩트가 통제된 고품질 다국어 벤치마크를 제시 |
| **사용 데이터** | **Multilingual LibriSpeech 기반, 8개 언어: 네덜란드어, 영어, 프랑스어, 독일어, 이탈리아어, 폴란드어, 포르투갈어, 스페인어 (전부 유럽 언어, 아시아 언어 없음)**<br>550명 화자, 약 155,145개 발화, 350.8시간. 진짜 51,715 / 딥페이크 103,430. 16kHz. 발화 길이 5~15초로 제한 |
| **분석 방법/모델** | **TTS는 XTTSv2 단일 모델** 사용(원본 오디오를 레퍼런스로 조건화). 3단계 partial fake 생성:<br>(1) **사전 정규화** — RMS 기반 라우드니스 정렬 + adaptive pre-emphasis 필터링으로 신경 보코더가 유발하는 스펙트럼 불균형 완화<br>(2) **정렬 기반 구간 치환** — Whisper로 전사해 전사가 충분히 일치하는 쌍만 유지(합성 품질 검증 겸용), Montreal Forced Aligner로 정렬 후 **정렬된 단어 쌍의 중간점**에 교체 경계 배치(음소·운율 전환을 가로지르지 않도록), 모든 경계는 코사인 페이딩 **30ms overlap-add** 처리<br>(3) **음향 증강** — OpenSLR 26의 room impulse response 컨볼루션 + MUSAN 배경 잡음 15dB SNR<br>**라벨링**: 30ms 프레임 단위로 bonafide / deepfake / **transition** 3종 (경계 아티팩트와 실제 합성 단서를 분리 해석하기 위함) |
| **평가 지표** | EER, AUC, DNSMOS (평균 MOS 3.58~3.68로 기존 데이터셋 중 최고 자연스러움) |
| **주요 결과** | **cross-lingual**: 영어 학습 후 7개 미지 언어 평가 시 EER 급등. 영어 in-domain은 TDAM 0.29%, W2v2-XLSR-GAT 0.59%였으나, 교차 언어에서는 SincNet 36~47%, Spectrogram 37~55%, W2v2-XLSR 41~44%, TDAM 27~36%, MFCC 21~31%. XLS-R은 128개 언어 사전학습에도 불구하고 영어로만 파인튜닝하면 교차언어 강건성이 낮아 파인튜닝 도메인에 과특화됨을 확인<br>**cross-dataset**: PartialSpoof로 학습한 TDAM·Nes2Net을 HQ-MPSD 영어셋에 적용하자 EER 51.38% / 57.47%로 **무작위 추측보다 나쁨** |
| **연구의 한계** | ① 8개 언어가 전부 유럽 언어 — 아시아 언어(한국어·중국어·일본어) 전무<br>② TTS가 XTTSv2 단일 모델이라 TTS별 편향 분석 불가<br>③ 조작 비율을 통제 변수로 다루지 않음("발화당 제한된 수의 구간 치환"이라고만 기술)<br>④ 원본이 오디오북(Multilingual LibriSpeech) 단일 도메인 |
| **본인 연구와의 차이** | **방법론(forced alignment 기반 접합점 도출)은 가장 유사하나, 세 가지 축에서 명확히 구분됨:**<br>① **언어** — HQ-MPSD에 한국어 미포함. 유럽 언어 간에도 EER 27~55%인데, 음운 구조가 근본적으로 다른 한국어에서는 더 큰 격차 예상<br>② **TTS 다양성** — HQ-MPSD는 XTTSv2 1개, 본 연구는 GPT-SoVITS·CosyVoice2·VITS 3개 비교로 "탐지기의 특정 TTS 편향" 분석 가능<br>③ **조작 비율 통제** — 본 연구는 저/중/고 3구간을 동일 발화 내에서 생성하여 독립 분석 변수로 사용<br>④ **평가 대상 모델 상이** — HQ-MPSD는 GAT-ST·TDAM·Nes2Net, 본 연구는 CFPRF·Split&Conquer |
| **본 연구가 채택을 검토할 점** | ① **Whisper 전사 일치 검증**을 품질 필터로 사용 (본 연구의 자동 품질검사 WER 항목의 선행 근거)<br>② 크로스페이드를 현재 15ms → **30ms**로 늘리는 것 검토<br>③ **배경 효과 증강**(RIR + MUSAN 15dB SNR) 추가 검토 — 미적용 시 "clean-lab bias" 지적 가능성<br>④ **transition 프레임 라벨** 도입 검토 — 경계 아티팩트와 합성 단서 분리 해석에 유용<br>⑤ 발화 길이 5~15초 제한은 본 연구(5.0~13.3초, p5~p95)와 거의 일치 → 길이 기준의 추가 근거로 인용 가능 |
| **데이터** | https://zenodo.org/records/17929533 |
| **arXiv** | https://arxiv.org/abs/2512.13012 |

---

## 12. XMAD-Bench (Ciobanu et al., EACL 2026)

| 항목 | 내용 |
|---|---|
| **논문 제목** | XMAD-Bench: Cross-Domain Multilingual Audio Deepfake Benchmark |
| **연구 목적** | 대부분의 탐지 연구가 in-domain 환경에서만 평가되어 99%대 정확도를 보고하는 관행을 비판하고, 실환경("in the wild") 평가를 위한 cross-domain 벤치마크 구축 |
| **사용 데이터** | 진짜·딥페이크 음성 총 668.8시간. **화자, 생성 방법, 원본 오디오 출처가 훈련/평가 split 간 모두 상이**하도록 설계 |
| **분석 방법/모델** | 벤치마크 논문. 기존 탐지 모델들을 in-domain과 cross-domain 양쪽에서 평가 |
| **평가 지표** | Accuracy 등 |
| **주요 결과** | in-domain 성능은 100%에 가까운 반면 동일 모델의 cross-domain 성능은 때때로 **무작위 추측 수준**까지 하락. 언어·화자·생성 방법·데이터 출처가 달라져도 일반화를 유지하는 강건한 탐지기 개발 필요성을 강조 |
| **연구의 한계** | 부분 위조(partial spoof)가 아닌 전체 딥페이크 중심 |
| **본인 연구와의 차이** | XMAD-Bench는 fully fake 대상, 본 연구는 partial fake 대상. 다만 "훈련/평가 간 화자·생성방법·출처를 모두 분리"하는 설계 원칙은 본 연구의 화자 분리 분할과 같은 문제의식 |
| **저장소** | https://github.com/ristea/xmad-bench/ |

---

## 13. XLS-R (Babu et al., 2021) — SSL 프론트엔드

| 항목 | 내용 |
|---|---|
| **논문 제목** | XLS-R: Self-supervised Cross-lingual Speech Representation Learning at Scale |
| **연구 목적** | 대규모 다국어 음성 데이터로 자기지도 학습(SSL)을 수행하여, 언어 간 전이가 가능한 범용 음성 표현을 학습 |
| **사용 데이터** | 128개 언어, 약 50만 시간 규모의 공개 음성 데이터 |
| **분석 방법/모델** | wav2vec 2.0 아키텍처를 다국어로 확장. 최대 2B 파라미터까지 스케일업 |
| **평가 지표** | 다운스트림 태스크별(음성 인식 WER, 음성 번역 BLEU, 언어 식별 정확도 등) |
| **주요 결과** | 저자원 언어에서 특히 큰 성능 향상. 이후 anti-spoofing 분야에서 프론트엔드 특징 추출기로 광범위하게 채택됨 |
| **연구의 한계** | 딥페이크 탐지 목적으로 설계되지 않았으며, 사전학습 데이터에 합성음이 거의 없어 위조 아티팩트 표현 학습에는 한계 가능성 |
| **본인 연구와의 차이** | 본 연구에서 직접 학습하지는 않으나, CFPRF·Split&Conquer 등 평가 대상 모델의 프론트엔드로 사용되므로 배경 지식으로 필요. 한국어가 XLS-R 사전학습에 포함되어 있는지 확인하면 cross-lingual 성능 해석에 도움 |

---

## 전체 흐름 요약

### 연구 계보
```
PartialSpoof(2021) / HAD(2021)  →  태스크 정립 + 표준 벤치마크
        ↓
ADD 2023  →  "위치 특정(localization)"을 공식 태스크화
        ↓
BAM(2024) / CFPRF(2024) / TDAM(2025) / Split&Conquer(2026)  →  모델 성능 경쟁 (in-domain SOTA)
        ↓
LlamaPartialSpoof(2025) / PartialEdit(2025) / Robust Localization(2025)
        →  "in-domain SOTA가 실제로는 일반화 안 된다"는 반성
        ↓
HQ-MPSD(2025) / XMAD-Bench(2026)  →  고품질·다국어·cross-domain 벤치마크로 전환
        ↓
【본 연구】한국어 partial fake 데이터셋 + 조작 비율 통제 + TTS 3종 비교
```

### 본 연구의 위치
분야가 "더 좋은 모델 만들기"에서 "**기존 모델이 정말 일반화되는가 검증하기**"로 이동하는 흐름 위에 있음. 본 연구는 그 흐름에서 **한국어**와 **조작 비율 통제**라는 두 축을 추가하는 위치.

### 차별화 검증 결과 (HQ-MPSD, 원문 확인 완료)
forced alignment 기반 고품질 스플라이싱이라는 핵심 방법론이 겹쳤으나, 원문 확인 결과 **세 항목 모두 본 연구의 차별점으로 성립**함:

| 확인 항목 | 결과 | 차별점 성립 |
|---|---|---|
| 8개 언어에 한국어 포함? | **미포함** (네덜란드·영·프·독·이탈리아·폴란드·포르투갈·스페인 — 전부 유럽어) | ✅ 언어 차별성 확보 |
| 조작 비율을 통제 변수로? | **아님** ("발화당 제한된 수의 구간 치환"으로만 기술) | ✅ 조작 비율 통제 차별성 |
| TTS 모델별 편향 분석? | **불가** (XTTSv2 단일 모델) | ✅ TTS 3종 비교 차별성 |

**본 연구의 포지셔닝**: HQ-MPSD가 "다국어(유럽어) × 단일 TTS × 아티팩트 통제"라면, 본 연구는 **"한국어 심층 × 다중 TTS × 조작 비율 통제"**로 직교하는 축을 다룸.

---

## ⚠️ 추가 확인이 필요한 항목

| 논문 | 확인할 것 |
|---|---|
| 2번 HAD | 원문 DOI에서 데이터 규모(발화 수, 시간, 화자 수) 정확히 확인 |
| 5번 Split&Conquer | 저자명 표기(Rimon et al.) 및 게재 학회 확인. pretrained weight 공개 여부 확인 |
| 8번 Robust Localization | 정확한 논문 제목과 저자 표기 확인 |
| 9번 PartialEdit | 정확한 논문 제목 확인 |
| ~~11번 HQ-MPSD~~ | ~~8개 언어 목록에 한국어 포함 여부~~ → **확인 완료: 미포함 (유럽 8개 언어)** |
| 13번 XLS-R | 128개 언어에 한국어 포함 여부 및 데이터 비중. HQ-MPSD 실험에서 XLS-R이 128개 언어 사전학습에도 영어 파인튜닝 후 교차언어 성능이 나빴다는 점(과특화)은 확인됨 |
