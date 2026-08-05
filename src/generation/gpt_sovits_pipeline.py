"""
Zeroth-Korean에서 ~7초 샘플을 하나 받아서,
사용자가 지정한 단어/구간만 GPT-SoVITS TTS로 교체하는 스크립트.

사전 준비:
1. pip install datasets soundfile faster-whisper requests
2. GPT-SoVITS API 서버를 별도로 실행해둘 것
   (GPT-SoVITS 폴더에서: python api_v2.py -a 0.0.0.0 -p 9880)
   -> 서버가 켜져 있어야 4단계 TTS 합성이 동작함

흐름:
1) Zeroth 데이터셋에서 7초 근처 샘플 하나 다운로드
2) faster-whisper로 단어별 타임스탬프 추출
3) 원문 텍스트 보여주고, 사용자에게 "바꿀 단어" + "바꿀 텍스트" 입력받기
4) GPT-SoVITS API에 "원본 wav를 레퍼런스로, 새 단어를 그 화자 목소리로 합성해줘" 요청
5) 원본 오디오에서 해당 구간만 잘라내고 합성 오디오로 교체 후 저장
"""
import argparse

import numpy as np
import requests
import soundfile as sf


# ---------- 1) Zeroth 샘플 다운로드 ----------
def download_zeroth_sample(output_dir, target_sec=7.0, tolerance=0.5):
    from datasets import load_dataset

    print("[1/5] Zeroth-Korean(test split) 다운로드 중... (처음엔 시간 좀 걸림)")
    dataset = load_dataset("kresnik/zeroth_korean", split="test")

    for i, s in enumerate(dataset):
        duration = len(s["audio"]["array"]) / s["audio"]["sampling_rate"]
        if abs(duration - target_sec) <= tolerance:
            wav_path = f"{output_dir}/zeroth_sample.wav"
            sf.write(wav_path, s["audio"]["array"], s["audio"]["sampling_rate"])
            print(f"  -> 샘플 index {i}, 길이 {duration:.2f}초")
            print(f"  -> 원문 텍스트: {s['text']}")
            print(f"  -> 저장 위치: {wav_path}")
            return wav_path, s["text"]

    raise RuntimeError("조건에 맞는 샘플을 못 찾았습니다. tolerance를 늘려보세요.")


# ---------- 2) 단어별 타임스탬프 추출 ----------
def get_word_timestamps(wav_path):
    from faster_whisper import WhisperModel

    print("[2/5] 단어별 타임스탬프 추출 중 (faster-whisper)...")
    model = WhisperModel("large-v3", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(wav_path, word_timestamps=True, language="ko")

    words = []
    for seg in segments:
        for w in seg.words:
            words.append({"word": w.word.strip(), "start": w.start, "end": w.end})

    print("  -> 인식된 단어들:")
    for idx, w in enumerate(words):
        print(f"     [{idx}] {w['word']}  ({w['start']:.2f}s ~ {w['end']:.2f}s)")

    return words


# ---------- 3) 사용자에게 바꿀 부분 물어보기 ----------
def ask_user_edit(words):
    print("\n[3/5] 위 단어 목록에서 바꿀 단어의 번호를 입력하세요.")
    print("      (연속된 여러 단어를 바꾸려면 '1,2,3'처럼 콤마로 입력)")
    idx_input = input("바꿀 단어 번호: ").strip()
    indices = [int(x) for x in idx_input.split(",")]

    start_time = words[min(indices)]["start"]
    end_time = words[max(indices)]["end"]
    original_phrase = " ".join(words[i]["word"] for i in indices)

    print(f"선택된 구간: '{original_phrase}' ({start_time:.2f}s ~ {end_time:.2f}s)")
    new_text = input("이 부분을 뭐라고 바꿀까요? (새 텍스트 입력): ").strip()

    return start_time, end_time, new_text


# ---------- 4) GPT-SoVITS로 새 텍스트 합성 ----------
def synthesize_with_gpt_sovits(api_url, output_dir, ref_wav_path, ref_text, new_text):
    print("[4/5] GPT-SoVITS API로 새 구간 합성 중...")
    payload = {
        "text": new_text,
        "text_lang": "ko",
        "ref_audio_path": ref_wav_path,
        "prompt_text": ref_text,
        "prompt_lang": "ko",
    }
    resp = requests.post(f"{api_url}/tts", json=payload)
    resp.raise_for_status()

    tts_wav_path = f"{output_dir}/tts_segment.wav"
    with open(tts_wav_path, "wb") as f:
        f.write(resp.content)

    print(f"  -> 합성 결과 저장: {tts_wav_path}")
    return tts_wav_path


# ---------- 5) 원본 오디오에 합성 조각 끼워넣기 ----------
def splice_audio(output_dir, original_wav_path, tts_wav_path, start_time, end_time):
    print("[5/5] 원본 오디오에 합성 구간 병합 중...")
    orig, sr = sf.read(original_wav_path)
    tts, tts_sr = sf.read(tts_wav_path)

    if tts_sr != sr:
        raise RuntimeError(f"샘플링레이트 불일치: 원본 {sr} vs 합성 {tts_sr}. 리샘플링 필요.")

    start_sample = int(start_time * sr)
    end_sample = int(end_time * sr)

    merged = np.concatenate([orig[:start_sample], tts, orig[end_sample:]])

    out_path = f"{output_dir}/final_merged.wav"
    sf.write(out_path, merged, sr)
    print(f"  -> 최종 결과 저장: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="GPT-SoVITS 기반 대화형 부분 합성 파이프라인")
    parser.add_argument("--api-url", default="http://127.0.0.1:9880",
                         help="api_v2.py 실행 시 기본 주소")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--target-sec", type=float, default=7.0)
    args = parser.parse_args()

    wav_path, ref_text = download_zeroth_sample(args.output_dir, target_sec=args.target_sec)
    words = get_word_timestamps(wav_path)
    start_time, end_time, new_text = ask_user_edit(words)
    tts_wav_path = synthesize_with_gpt_sovits(args.api_url, args.output_dir, wav_path, ref_text, new_text)
    splice_audio(args.output_dir, wav_path, tts_wav_path, start_time, end_time)


if __name__ == "__main__":
    main()
