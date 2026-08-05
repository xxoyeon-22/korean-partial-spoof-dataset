"""
=========================================================
발화 표집: 길이 필터 + 화자 최소 보유 필터 + 화자당 균등 무작위 표집
  입력: analyze_distribution.py 가 만든 메타데이터 CSV
=========================================================
"""
import argparse

import numpy as np
import pandas as pd


def select(df, seed=42, min_utt=20, n_per_speaker=10):
    # 재현성 확보 -- 이 값 그대로 논문/노션에 기록해두면
    # 누구든 같은 표본을 재현할 수 있음
    rng = np.random.default_rng(seed)

    # ---- 1. 길이 필터 (p5 ~ p95) ----
    p5, p95 = np.percentile(df["duration"], [5, 95])
    df_len = df[(df["duration"] >= p5) & (df["duration"] <= p95)].copy()
    print(f"길이 필터 (p5={p5:.2f}s ~ p95={p95:.2f}s): {len(df)} -> {len(df_len)}건")

    # ---- 2. 화자 최소 보유 필터 ----
    counts = df_len.groupby("speaker").size()
    valid_speakers = counts[counts >= min_utt].index
    df_valid = df_len[df_len["speaker"].isin(valid_speakers)].copy()
    print(f"화자 최소 {min_utt}개 보유 필터: 화자 {len(valid_speakers)}명, 발화 {len(df_valid)}건")

    # ---- 3. 화자당 균등 무작위 표집 ----
    def sample_speaker(g):
        idx = rng.choice(g.index.values, size=n_per_speaker, replace=False)
        return g.loc[idx]

    sampled = (
        df_valid.groupby("speaker", group_keys=False)
        .apply(sample_speaker, include_groups=True)
        .reset_index(drop=True)
    )

    print(f"\n최종 표집: {len(sampled)}건 (화자 {sampled['speaker'].nunique()}명 x {n_per_speaker}개)")
    print(f"길이 범위: {sampled['duration'].min():.2f}s ~ {sampled['duration'].max():.2f}s")
    print(f"길이 중앙값: {sampled['duration'].median():.2f}s")

    # 화자당 실제 개수 검증 (전부 n_per_speaker 여야 정상)
    check = sampled.groupby("speaker").size()
    assert (check == n_per_speaker).all(), "화자당 개수가 안 맞습니다"
    print("화자당 개수 검증 통과 (전원 균등)")

    # ---- train/val/test 화자 분리 분할 ----
    # 같은 화자가 여러 split 에 걸치지 않도록 화자 단위로 분할
    speakers = sampled["speaker"].unique()
    rng.shuffle(speakers)

    n = len(speakers)
    n_train = int(n * 0.7)
    n_val = int(n * 0.15)
    # 나머지는 test

    train_spk = set(speakers[:n_train])
    val_spk = set(speakers[n_train:n_train + n_val])

    sampled["dataset_split"] = sampled["speaker"].apply(
        lambda s: "train" if s in train_spk else ("val" if s in val_spk else "test")
    )

    print("\nsplit별 화자 수 / 발화 수")
    print(sampled.groupby("dataset_split").agg(
        n_speakers=("speaker", "nunique"),
        n_utterances=("speaker", "size"),
    ))

    sampled = sampled.sort_values(["dataset_split", "speaker", "idx"]).reset_index(drop=True)
    sampled["sample_id"] = [f"zk_{i:05d}" for i in range(len(sampled))]
    return sampled


def main():
    parser = argparse.ArgumentParser(description="발화 표집 + 화자 분리 분할")
    parser.add_argument("--input", default="manifests/zeroth_meta.csv",
                         help="analyze_distribution.py 출력 CSV")
    parser.add_argument("--output", default="manifests/selected_utterances.csv")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-utterances", type=int, default=20,
                         help="화자당 최소 보유 발화 수")
    parser.add_argument("--per-speaker", type=int, default=10,
                         help="화자당 표집 개수")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    sampled = select(df, seed=args.seed, min_utt=args.min_utterances,
                      n_per_speaker=args.per_speaker)

    sampled.to_csv(args.output, index=False)
    print(f"\n저장 완료: {args.output}")
    print(sampled[["sample_id", "speaker", "dataset_split", "duration", "text"]].head(10))


if __name__ == "__main__":
    main()
