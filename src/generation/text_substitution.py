"""
=========================================================
LLM 기반 텍스트 치환
  원본 문장의 마지막 n어절을 의미가 달라지도록 자연스럽게 바꿔서
  TTS 합성 -> 스플라이싱 단계의 입력을 만든다.

  사전 준비: 환경변수 ANTHROPIC_API_KEY 설정
    export ANTHROPIC_API_KEY="sk-ant-..."
=========================================================
"""
import argparse
import os
import time

import anthropic
import pandas as pd

RATIO_MAP = {2: "low", 3: "mid", 5: "high"}


def get_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다. "
            "export ANTHROPIC_API_KEY=\"sk-ant-...\" 로 설정한 뒤 다시 실행하세요."
        )
    return anthropic.Anthropic()  # 환경변수의 키를 자동으로 읽어옴


def replace_last_words(client, original_text, n_words):
    """
    original_text: 원본 문장 (예: "아울러 미약하게나마 제가 할 수 있는 일을 찾아 실천하겠습니다")
    n_words: 마지막 몇 어절을 바꿀지 (2, 3, 5 중 하나)

    반환값: (새 문장, 원래 마지막 n어절, 바뀐 n어절)
    """
    words = original_text.split()

    # 발화가 너무 짧아서 n_words만큼 뗄 수 없으면 건너뜀
    if len(words) <= n_words:
        return None, None, None

    kept_part = " ".join(words[:-n_words])       # 안 바뀌는 앞부분
    original_tail = " ".join(words[-n_words:])   # 바뀔 대상 (원본)

    prompt = f"""다음은 한국어 문장의 마지막 부분입니다: "{original_tail}"

이 부분을 정확히 {n_words}개의 어절로, 문장의 의미가 실제로 달라지도록 자연스럽게 바꿔주세요.
예를 들어 "실천하겠습니다"를 "포기하겠습니다"처럼, 반대되거나 다른 의미의 내용으로 바꿔야 합니다.
문법적으로 자연스러운 한국어여야 하고, 어절 수는 반드시 {n_words}개를 지켜야 합니다.

바뀐 텍스트만 출력하세요. 설명이나 따옴표 없이 텍스트만 답하세요."""

    # 어절 수가 안 맞으면 최대 2번까지 재시도
    new_tail = None
    for attempt in range(3):
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}],
        )
        new_tail = response.content[0].text.strip()

        if len(new_tail.split()) == n_words:
            break
        prompt += f'\n\n(주의: 방금 답변 "{new_tail}"은 어절 수가 {len(new_tail.split())}개였습니다. 정확히 {n_words}개 어절로 다시 답해주세요.)'
    else:
        print(f"  [경고] 어절 수 불일치 지속: 원본='{original_tail}' 결과='{new_tail}'")

    new_full_text = f"{kept_part} {new_tail}"
    return new_full_text, original_tail, new_tail


def run(client, df, output_path):
    # 이미 처리된 파일이 있으면 이어서 진행 (중단 재개 기능)
    if os.path.exists(output_path):
        results_df = pd.read_csv(output_path)
        done_keys = set(zip(results_df["sample_id"], results_df["ratio_bin"]))
        print(f"기존 결과 {len(results_df)}건 발견, 이어서 진행합니다.")
    else:
        results_df = pd.DataFrame()
        done_keys = set()

    results = results_df.to_dict("records")

    for i, row in df.iterrows():
        sample_id = row["sample_id"]
        original_text = row["text"]

        for n_words, ratio_bin in RATIO_MAP.items():
            if (sample_id, ratio_bin) in done_keys:
                continue

            try:
                new_text, orig_tail, new_tail = replace_last_words(client, original_text, n_words)

                if new_text is None:
                    print(f"  [건너뜀] {sample_id}: 문장이 너무 짧아 {n_words}어절 치환 불가")
                    continue

                word_count_ok = (len(new_tail.split()) == n_words)

                results.append({
                    "sample_id": sample_id,
                    "speaker": row["speaker"],
                    "dataset_split": row["dataset_split"],
                    "ratio_bin": ratio_bin,
                    "n_words_replaced": n_words,
                    "original_text": original_text,
                    "replaced_tail": new_tail,
                    "new_text": new_text,
                    "duration": row["duration"],
                    "word_count_ok": word_count_ok,   # False면 나중에 검수 필요
                })

            except Exception as e:
                print(f"  [에러] {sample_id} ({ratio_bin}): {e}")
                time.sleep(3)

            if len(results) % 50 == 0:
                pd.DataFrame(results).to_csv(output_path, index=False)

        if i % 20 == 0:
            print(f"진행률: {i}/{len(df)} 원본 발화 처리 완료 (누적 {len(results)}건)")

    pd.DataFrame(results).to_csv(output_path, index=False)
    print(f"\n전체 완료! 총 {len(results)}건 저장: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="LLM 기반 텍스트 치환")
    parser.add_argument("--input", default="manifests/selected_utterances.csv")
    parser.add_argument("--output", default="manifests/text_substituted.csv")
    args = parser.parse_args()

    client = get_client()

    df = pd.read_csv(args.input)
    print(f"불러온 발화 수: {len(df)}개")
    print(df[["sample_id", "speaker", "text"]].head())

    run(client, df, args.output)

    final_df = pd.read_csv(args.output)
    print(f"\n구간별 개수:")
    print(final_df["ratio_bin"].value_counts())
    print(f"\n어절 수 검증 결과:")
    print(final_df["word_count_ok"].value_counts())
    if (~final_df["word_count_ok"]).sum() > 0:
        print(f"\n불일치 샘플 (재작업 필요, redo_substitution.py 참고):")
        print(final_df[~final_df["word_count_ok"]][["sample_id", "ratio_bin", "replaced_tail"]])


if __name__ == "__main__":
    main()
