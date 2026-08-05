"""
=========================================================
정렬 + 스플라이싱 (수동 구간 지정 버전)
  splice_forced_align.py 이전 단계에서 쓰던 방식.
  발화 구간을 자동 탐지해 보여주고, 사용자가 직접 초 단위로
  잘라낼 구간을 지정하면 볼륨 정규화 + 크로스페이드로 접합한다.
=========================================================
"""
import argparse

import numpy as np
import soundfile as sf


def load_mono(path, target_sr=None):
    import librosa

    x, sr = sf.read(path)
    if x.ndim > 1:
        x = x.mean(axis=1)
    if target_sr and sr != target_sr:
        x = librosa.resample(x.astype(float), orig_sr=sr, target_sr=target_sr)
        sr = target_sr
    return x.astype(float), sr


def show_segments(x, sr, name, rel_th=0.05, win_s=0.03):
    """발화 구간 자동 탐지 (최대값 대비 상대 임계값)"""
    win = int(win_s * sr)
    rms = np.array([np.sqrt(np.mean(x[i:i+win]**2))
                    for i in range(0, len(x)-win, win)])
    th = rms.max() * rel_th
    print(f"[{name}] 발화 구간")
    prev, st = False, 0.0
    for k, r in enumerate(rms):
        t, cur = k * win_s, r > th
        if cur and not prev:
            st = t
        if prev and not cur:
            print(f"   {st:5.2f} ~ {t:5.2f}s   ({t-st:.2f}초)")
        prev = cur
    if prev:
        print(f"   {st:5.2f} ~ {len(x)/sr:5.2f}s")
    print()


def active_rms(x, th_ratio=0.05):
    """무음 제외 RMS (조용한 꼬리 때문에 배율이 튀는 것 방지)"""
    th = np.abs(x).max() * th_ratio
    a = x[np.abs(x) > th]
    return np.sqrt(np.mean(a**2)) if len(a) > 10 else np.sqrt(np.mean(x**2) + 1e-12)


def main():
    parser = argparse.ArgumentParser(description="수동 구간 지정 스플라이싱 (CosyVoice 예시)")
    parser.add_argument("--orig-file", required=True)
    parser.add_argument("--tts-file", required=True)
    parser.add_argument("--tts-start", type=float, required=True, help="합성음에서 잘라낼 시작(초)")
    parser.add_argument("--tts-end", type=float, required=True, help="합성음에서 잘라낼 끝(초)")
    parser.add_argument("--orig-start", type=float, required=True, help="원본에서 교체될 시작(초)")
    parser.add_argument("--orig-end", type=float, required=True, help="원본에서 교체될 끝(초)")
    parser.add_argument("--speech-ref-start", type=float, default=0.80,
                         help="볼륨 기준으로 삼을 원본 발화 구간 시작(초)")
    parser.add_argument("--speech-ref-end", type=float, required=True,
                         help="볼륨 기준으로 삼을 원본 발화 구간 끝(초)")
    parser.add_argument("--fade-ms", type=float, default=15.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    orig, sr = load_mono(args.orig_file)
    tts, _ = load_mono(args.tts_file, sr)
    print(f"원본 : {len(orig)/sr:.2f}초  (max {np.abs(orig).max():.3f})")
    print(f"합성 : {len(tts)/sr:.2f}초  (max {np.abs(tts).max():.3f})\n")

    show_segments(orig, sr, "원본")
    show_segments(tts, sr, "합성")

    seg = tts[int(args.tts_start*sr):int(args.tts_end*sr)].copy()

    # 볼륨 기준: 교체 구간이 아니라 '문장 전체 발화'에 맞춤
    #            (문장 끝은 원래 목소리가 잦아들어서 기준으로 삼으면 너무 작아짐)
    speech_ref = orig[int(args.speech_ref_start*sr):int(args.speech_ref_end*sr)]
    ratio = np.clip(active_rms(speech_ref) / active_rms(seg), 0.05, 20)
    seg *= ratio
    print(f"볼륨 배율: {ratio:.2f}")

    fade = int(args.fade_ms / 1000 * sr)
    s, e = int(args.orig_start*sr), int(args.orig_end*sr)
    head, tail, mid = orig[:s].copy(), orig[e:].copy(), seg

    fo, fi = np.linspace(1, 0, fade), np.linspace(0, 1, fade)
    if len(head) >= fade and len(mid) >= fade:
        head = np.concatenate([head[:-fade], head[-fade:]*fo + mid[:fade]*fi])
        mid = mid[fade:]
    if len(tail) >= fade and len(mid) >= fade:
        tail = np.concatenate([mid[-fade:]*fo + tail[:fade]*fi, tail[fade:]])
        mid = mid[:-fade]

    merged = np.clip(np.concatenate([head, mid, tail]), -1.0, 1.0)

    sf.write(args.output, merged, sr)
    print(f"저장 완료: {args.output}  ({len(merged)/sr:.2f}초)")

    fake_start = args.orig_start
    fake_end = args.orig_start + (args.tts_end - args.tts_start)
    print(f"조작 구간 라벨: {fake_start:.2f}s ~ {fake_end:.2f}s")


if __name__ == "__main__":
    main()
