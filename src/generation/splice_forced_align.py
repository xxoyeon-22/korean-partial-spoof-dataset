"""
=========================================================
정렬 + 스플라이싱 (forced alignment 기반)
  MMS_FA = 1000개 이상 언어 지원, 한국어 포함
  정답 텍스트를 주고 '위치만' 찾으므로 Whisper보다 훨씬 정확

  절 단위로 원본 발화의 일부를 합성 음성으로 교체하고,
  무음 지점 스냅 + 볼륨 정규화 + 크로스페이드로 접합한다.
=========================================================
"""
import argparse

import numpy as np
import soundfile as sf
import torch
import torchaudio


def load_mono(path, target_sr=None):
    import librosa

    x, sr = sf.read(path)
    if x.ndim > 1:
        x = x.mean(axis=1)
    if target_sr and sr != target_sr:
        x = librosa.resample(x.astype(float), orig_sr=sr, target_sr=target_sr)
        sr = target_sr
    return x.astype(float), sr


def align_words(model, tokenizer, aligner, device, wave, sr, text, target_sr):
    """단어별 (단어, 시작초, 끝초) 리스트 반환"""
    w = torch.tensor(wave, dtype=torch.float32).unsqueeze(0)
    if sr != target_sr:
        w = torchaudio.functional.resample(w, sr, target_sr)
    words = text.split()
    with torch.inference_mode():
        emission, _ = model(w.to(device))
        spans = aligner(emission[0], tokenizer(words))
    ratio = w.shape[1] / emission.shape[1] / target_sr
    out = []
    for word, span in zip(words, spans):
        out.append((word, span[0].start * ratio, span[-1].end * ratio))
    return out


def span_of(align, first, last):
    d = {w: (a, b) for w, a, b in align}
    return d[first][0], d[last][1]


def snap_to_silence(x, sr, t, search=0.12, win_s=0.01):
    """t 근처에서 에너지가 가장 낮은 지점으로 이동 (파형 튐 방지)"""
    win = int(win_s * sr)
    lo = max(0, int((t - search) * sr))
    hi = min(len(x) - win, int((t + search) * sr))
    if hi <= lo:
        return t
    best, best_r = t, 1e9
    for i in range(lo, hi, win // 2 or 1):
        r = np.sqrt(np.mean(x[i:i + win] ** 2))
        if r < best_r:
            best_r, best = r, i / sr
    return best


def active_rms(x, th_ratio=0.05):
    th = np.abs(x).max() * th_ratio
    a = x[np.abs(x) > th]
    return np.sqrt(np.mean(a ** 2)) if len(a) > 10 else np.sqrt(np.mean(x ** 2) + 1e-12)


def splice(orig, tts, sr, o_s, o_e, t_s, t_e, orig_align, fade_s=0.010):
    seg = tts[int(t_s * sr):int(t_e * sr)].copy()

    # 볼륨 기준 = 원본 발화 전체 (문장 끝만 쓰면 과하게 작아짐)
    sp_s, sp_e = orig_align[0][1], orig_align[-1][2]
    ratio = np.clip(active_rms(orig[int(sp_s * sr):int(sp_e * sr)]) / active_rms(seg), 0.05, 20)
    seg *= ratio
    print(f"볼륨 배율 {ratio:.2f}")

    fade = int(fade_s * sr)
    s, e = int(o_s * sr), int(o_e * sr)
    head, tail, mid = orig[:s].copy(), orig[e:].copy(), seg
    fo, fi = np.linspace(1, 0, fade), np.linspace(0, 1, fade)

    if len(head) >= fade and len(mid) >= fade:
        head = np.concatenate([head[:-fade], head[-fade:] * fo + mid[:fade] * fi])
        mid = mid[fade:]
    if len(tail) >= fade and len(mid) >= fade:
        tail = np.concatenate([mid[-fade:] * fo + tail[:fade] * fi, tail[fade:]])
        mid = mid[:-fade]

    return np.clip(np.concatenate([head, mid, tail]), -1.0, 1.0)


def main():
    parser = argparse.ArgumentParser(description="Forced alignment 기반 정렬 + 스플라이싱")
    parser.add_argument("--orig-file", required=True, help="원본 wav 경로")
    parser.add_argument("--tts-file", required=True, help="합성 wav 경로")
    parser.add_argument("--orig-text", required=True, help="원본 전체 문장")
    parser.add_argument("--tts-text", required=True, help="합성 전체 문장")
    parser.add_argument("--orig-first-word", required=True, help="원본에서 교체할 절의 첫 단어")
    parser.add_argument("--orig-last-word", required=True, help="원본에서 교체할 절의 마지막 단어")
    parser.add_argument("--tts-first-word", required=True, help="합성에서 가져올 절의 첫 단어")
    parser.add_argument("--tts-last-word", required=True, help="합성에서 가져올 절의 마지막 단어")
    parser.add_argument("--output", required=True, help="결과 wav 저장 경로")
    args = parser.parse_args()

    orig, sr = load_mono(args.orig_file)
    tts, _ = load_mono(args.tts_file, sr)
    print(f"원본 {len(orig)/sr:.2f}s / 합성 {len(tts)/sr:.2f}s")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("device:", device)

    bundle = torchaudio.pipelines.MMS_FA
    model = bundle.get_model().to(device)
    tokenizer = bundle.get_tokenizer()
    aligner = bundle.get_aligner()
    target_sr = bundle.sample_rate  # 16000

    print(f"\n[원본] {args.orig_text}")
    orig_align = align_words(model, tokenizer, aligner, device, orig, sr, args.orig_text, target_sr)
    for w, a, b in orig_align:
        print(f"   {w:12s} {a:5.2f} ~ {b:5.2f}s")

    print(f"\n[합성] {args.tts_text}")
    tts_align = align_words(model, tokenizer, aligner, device, tts, sr, args.tts_text, target_sr)
    for w, a, b in tts_align:
        print(f"   {w:12s} {a:5.2f} ~ {b:5.2f}s")

    o_s, o_e = span_of(orig_align, args.orig_first_word, args.orig_last_word)
    t_s, t_e = span_of(tts_align, args.tts_first_word, args.tts_last_word)
    print(f"원본 절 : {o_s:.2f} ~ {o_e:.2f}s")
    print(f"합성 절 : {t_s:.2f} ~ {t_e:.2f}s")

    o_s = snap_to_silence(orig, sr, o_s)
    o_e = snap_to_silence(orig, sr, o_e)
    t_s = snap_to_silence(tts, sr, t_s)
    t_e = snap_to_silence(tts, sr, t_e)
    print(f"\n무음 보정 후")
    print(f"원본 절 : {o_s:.3f} ~ {o_e:.3f}s")
    print(f"합성 절 : {t_s:.3f} ~ {t_e:.3f}s")

    merged = splice(orig, tts, sr, o_s, o_e, t_s, t_e, orig_align)

    sf.write(args.output, merged, sr)

    label_s = o_s
    label_e = o_s + (t_e - t_s)
    print(f"\n저장: {args.output} ({len(merged)/sr:.2f}s)")
    print(f"조작 구간 라벨: {label_s:.3f}s ~ {label_e:.3f}s")


if __name__ == "__main__":
    main()
