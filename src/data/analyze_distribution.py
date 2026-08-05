"""
=========================================================
Zeroth-Korean 발화 분포 분석
  목적: 발화 선정 기준(길이 컷오프)을 임의 숫자가 아니라
        데이터 실제 분포에서 근거를 갖고 정하기 위함
=========================================================
CELL 1 : 메타데이터 수집 (오디오 디코딩 없이 헤더만 읽음)
"""
import argparse
import io

import numpy as np
import pandas as pd
import soundfile as sf
from datasets import Audio, load_dataset


def collect(split):
    ds = load_dataset("kresnik/zeroth_korean", split=split)
    # 디코딩 끄기 -> 파형을 메모리에 올리지 않음 (훨씬 빠름)
    ds = ds.cast_column("audio", Audio(decode=False))

    rows = []
    for i, s in enumerate(ds):
        a = s["audio"]
        try:
            if a.get("bytes"):
                info = sf.info(io.BytesIO(a["bytes"]))
            else:
                info = sf.info(a["path"])
            dur = info.frames / info.samplerate
            sr = info.samplerate
        except Exception:
            continue

        text = s.get("text", "")
        spk = s.get("speaker_id", s.get("id", "unknown"))
        rows.append({
            "split": split,
            "idx": i,
            "speaker": spk,
            "duration": dur,
            "sr": sr,
            "text": text,
            "n_eojeol": len(text.split()),      # 어절 수
            "n_char": len(text.replace(" ", "")),
        })
        if i % 2000 == 0:
            print(f"  {split} {i}...")
    return rows


"""
=========================================================
CELL 2 : 분포 통계 (논문에 그대로 쓸 숫자)
=========================================================
"""
def report(d, name):
    x = d["duration"]
    print(f"\n===== {name} (n={len(d)}, 화자 {d['speaker'].nunique()}명) =====")
    print(f"총 길이      : {x.sum()/3600:.2f} 시간")
    print(f"평균 / 중앙값: {x.mean():.2f}s / {x.median():.2f}s")
    print(f"표준편차     : {x.std():.2f}s")
    print(f"최소 / 최대  : {x.min():.2f}s / {x.max():.2f}s")
    print("\n백분위수")
    for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
        print(f"  p{p:<3d} : {np.percentile(x, p):6.2f}s")
    q1, q3 = np.percentile(x, [25, 75])
    print(f"\nIQR (p25~p75) : {q1:.2f} ~ {q3:.2f}s")
    print(f"극단값 제외 (p5~p95) : {np.percentile(x,5):.2f} ~ {np.percentile(x,95):.2f}s")

    e = d["n_eojeol"]
    print(f"\n어절 수  중앙값 {e.median():.0f} / p10 {np.percentile(e,10):.0f} / p90 {np.percentile(e,90):.0f}")
    print(f"발화 속도 중앙값 {(d['n_eojeol']/d['duration']).median():.2f} 어절/초")


"""
=========================================================
CELL 3 : 히스토그램
=========================================================
"""
def plot(df, out_path):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 2, figsize=(13, 4))

    ax[0].hist(df["duration"], bins=60, color="#5DCAA5", edgecolor="white")
    for p, c in [(5, "#D85A30"), (50, "#378ADD"), (95, "#D85A30")]:
        v = np.percentile(df["duration"], p)
        ax[0].axvline(v, color=c, ls="--", lw=1.2, label=f"p{p}={v:.1f}s")
    ax[0].set_xlabel("duration (s)"); ax[0].set_ylabel("count")
    ax[0].set_title("Zeroth utterance duration"); ax[0].legend()

    ax[1].hist(df["n_eojeol"], bins=40, color="#AFA9EC", edgecolor="white")
    ax[1].axvline(df["n_eojeol"].median(), color="#378ADD", ls="--",
                  label=f"median={df['n_eojeol'].median():.0f}")
    ax[1].set_xlabel("eojeol count"); ax[1].set_title("Words per utterance"); ax[1].legend()

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    print(f"히스토그램 저장: {out_path}")


"""
=========================================================
CELL 4 : 조작 비율 층화 시뮬레이션
  교체할 절 길이를 가정했을 때, 각 발화의 조작 비율이
  어느 구간에 떨어지는지 미리 확인
=========================================================
"""
def estimate_ratio_bins(df, phrase_eojeol=3):
    # 발화 속도 기준으로 '절 N어절' 길이를 추정
    rate = (df["n_eojeol"] / df["duration"]).median()      # 어절/초
    est_phrase = phrase_eojeol / rate

    df["est_ratio"] = est_phrase / df["duration"]

    bins = [0, 0.15, 0.30, 1.0]
    labels = ["low(~15%)", "mid(15~30%)", "high(30%~)"]
    df["ratio_bin"] = pd.cut(df["est_ratio"], bins=bins, labels=labels)

    print(f"발화 속도 중앙값 {rate:.2f} 어절/초")
    print(f"{phrase_eojeol}어절 절의 추정 길이 {est_phrase:.2f}초\n")
    print("조작 비율 구간별 발화 수")
    print(df["ratio_bin"].value_counts().sort_index())
    print("\n구간별 발화 길이 중앙값")
    print(df.groupby("ratio_bin", observed=True)["duration"].median().round(2))

    print(f"\n화자 수: train {df[df.split=='train'].speaker.nunique()}명, "
          f"test {df[df.split=='test'].speaker.nunique()}명")
    print("\n화자당 발화 수 (상위 5)")
    print(df.groupby("speaker").size().sort_values(ascending=False).head())

    return df


def main():
    parser = argparse.ArgumentParser(description="Zeroth-Korean 발화 분포 분석")
    parser.add_argument("--output", default="manifests/zeroth_meta.csv",
                         help="메타데이터 CSV 저장 경로")
    parser.add_argument("--plot-output", default="docs/assets/zeroth_dist.png",
                         help="히스토그램 이미지 저장 경로")
    args = parser.parse_args()

    rows = []
    for sp in ["test", "train"]:          # test 먼저 (작아서 빠름)
        print(f"[{sp}] 수집 시작")
        rows += collect(sp)

    df = pd.DataFrame(rows)
    df.to_csv(args.output, index=False)
    print(f"\n총 {len(df)}건 수집 완료 -> {args.output}")

    report(df, "전체")
    for sp in ["train", "test"]:
        report(df[df.split == sp], sp)

    plot(df, args.plot_output)
    estimate_ratio_bins(df)


if __name__ == "__main__":
    main()
