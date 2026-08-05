"""
=========================================================
정렬 + 스플라이싱 (무음 구간 탐색 + 수동 절 지정 버전)
  splice_cosyvoice_manual.py 와 유사하지만, 무음 구간을 먼저 찾아
  보여준 뒤 그 지점 기준으로 절 경계를 수동 지정하는 방식.
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


def find_silences(x, sr, rel_th=0.05, win_s=0.02, min_sil=0.03):
    """무음 구간 리스트 반환 [(시작, 끝, 중앙), ...]"""
    win = int(win_s*sr)
    rms = np.array([np.sqrt(np.mean(x[i:i+win]**2))
                    for i in range(0, len(x)-win, win)])
    th = rms.max()*rel_th
    sil, run_start = [], None
    for k, r in enumerate(rms):
        t = k*win_s
        if r <= th and run_start is None:
            run_start = t
        elif r > th and run_start is not None:
            if t - run_start >= min_sil:
                sil.append((run_start, t, (run_start+t)/2))
            run_start = None
    return sil


def active_rms(x, th_ratio=0.05):
    th = np.abs(x).max()*th_ratio
    a = x[np.abs(x) > th]
    return np.sqrt(np.mean(a**2)) if len(a) > 10 else np.sqrt(np.mean(x**2)+1e-12)


def main():
    parser = argparse.ArgumentParser(description="무음 구간 탐색 기반 수동 스플라이싱")
    parser.add_argument("--orig-file", required=True)
    parser.add_argument("--tts-file", required=True)
    parser.add_argument("--orig-start", type=float, required=True, help="원본에서 교체될 시작(초)")
    parser.add_argument("--orig-end", type=float, required=True, help="원본에서 교체될 끝(초)")
    parser.add_argument("--tts-start", type=float, required=True, help="합성음에서 가져올 시작(초)")
    parser.add_argument("--tts-end", type=float, required=True, help="합성음에서 가져올 끝(초)")
    parser.add_argument("--speech-ref-start", type=float, default=0.80)
    parser.add_argument("--speech-ref-end", type=float, required=True)
    parser.add_argument("--fade-ms", type=float, default=10.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    orig, sr = load_mono(args.orig_file)
    tts, _ = load_mono(args.tts_file, sr)
    print(f"원본 {len(orig)/sr:.2f}s (max {np.abs(orig).max():.3f})")
    print(f"합성 {len(tts)/sr:.2f}s (max {np.abs(tts).max():.3f})\n")

    print("[원본] 무음 구간 (여기서 자르면 자연스러움)")
    for a, b, c in find_silences(orig, sr):
        print(f"   {a:5.2f} ~ {b:5.2f}s   중앙 {c:.3f}s")

    print("\n[합성] 무음 구간")
    for a, b, c in find_silences(tts, sr):
        print(f"   {a:5.2f} ~ {b:5.2f}s   중앙 {c:.3f}s")

    seg = tts[int(args.tts_start*sr):int(args.tts_end*sr)].copy()

    # 볼륨 기준 = 문장 전체 발화 (문장 끝만 쓰면 너무 작아짐)
    speech_ref = orig[int(args.speech_ref_start*sr):int(args.speech_ref_end*sr)]
    ratio = np.clip(active_rms(speech_ref) / active_rms(seg), 0.05, 20)
    seg *= ratio
    print(f"볼륨 배율 {ratio:.2f}")

    # 무음 지점에서 자르므로 페이드는 짧게만
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
    print(f"저장: {args.output}  ({len(merged)/sr:.2f}s)")
    print(f"조작 구간 라벨: {args.orig_start:.2f}s ~ {args.orig_start+(args.tts_end-args.tts_start):.2f}s")


if __name__ == "__main__":
    main()
