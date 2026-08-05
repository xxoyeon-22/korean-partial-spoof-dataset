"""
=========================================================
low 구간 1어절 결과 재작업
  대상: ratio_bin == "low" 인데 결과가 1어절로 나온 건
  목표: 정확히 2어절로 다시 생성

  사전 준비: 환경변수 ANTHROPIC_API_KEY 설정 (text_substitution.py 참고)
=========================================================
"""
import argparse

import pandas as pd

from text_substitution import get_client


def redo_two_words(client, original_text, prev_result):
    """
    2어절 치환을 더 강한 프롬프트로 재시도.
    이전에 1어절로 나왔던 사례를 프롬프트에 명시해 같은 실수를 막음.
    """
    words = original_text.split()
    if len(words) <= 2:
        return None, None

    kept_part = " ".join(words[:-2])
    original_tail = " ".join(words[-2:])

    prompt = f"""한국어 문장의 마지막 두 어절입니다: "{original_tail}"

이것을 **정확히 2개의 어절**로, 의미가 실제로 달라지도록 자연스럽게 바꿔주세요.

중요한 규칙:
- 어절이란 띄어쓰기로 구분되는 단위입니다. 반드시 공백이 1개 들어간 형태여야 합니다.
- 예: "비판도 받았다" -> "찬사를 받았다" (O, 2어절)
- 예: "비판도 받았다" -> "칭찬받았다" (X, 1어절이라 안 됨)
- 이전 시도에서 "{prev_result}"라고 답했는데 이것은 1어절이라 틀렸습니다.
- 의미는 원래와 반대되거나 확실히 다른 내용이어야 합니다.

바뀐 2어절 텍스트만 출력하세요. 설명이나 따옴표 없이."""

    new_tail = None
    for attempt in range(4):
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}],
        )
        new_tail = resp.content[0].text.strip()

        if len(new_tail.split()) == 2:
            return f"{kept_part} {new_tail}", new_tail

        prompt += f'\n\n(재차 주의: "{new_tail}"은 {len(new_tail.split())}어절입니다. 공백으로 구분된 2개 단어로 답하세요.)'

    # 4번 시도해도 실패하면 마지막 결과 반환 (표시는 남김)
    return f"{kept_part} {new_tail}", new_tail


def main():
    parser = argparse.ArgumentParser(description="1어절로 잘못 나온 low 구간 재작업")
    parser.add_argument("--manifest", default="manifests/text_substituted.csv")
    args = parser.parse_args()

    client = get_client()

    final_df = pd.read_csv(args.manifest)

    mask = (
        (final_df["ratio_bin"] == "low")
        & (final_df["replaced_tail"].astype(str).str.split().str.len() == 1)
    )
    redo_idx = final_df[mask].index
    print(f"재작업 대상: {len(redo_idx)}건")

    success, fail = 0, 0

    for i in redo_idx:
        original_text = final_df.at[i, "original_text"]
        prev = final_df.at[i, "replaced_tail"]

        try:
            new_text, new_tail = redo_two_words(client, original_text, prev)

            if new_text is None:
                print(f"  [건너뜀] {final_df.at[i,'sample_id']}: 문장이 2어절 이하")
                fail += 1
                continue

            ok = (len(new_tail.split()) == 2)
            final_df.at[i, "replaced_tail"] = new_tail
            final_df.at[i, "new_text"] = new_text
            final_df.at[i, "word_count_ok"] = ok

            if ok:
                success += 1
                print(f"  OK  {final_df.at[i,'sample_id']}: '{prev}' -> '{new_tail}'")
            else:
                fail += 1
                print(f"  실패 {final_df.at[i,'sample_id']}: '{new_tail}' ({len(new_tail.split())}어절)")

        except Exception as e:
            print(f"  [에러] {final_df.at[i,'sample_id']}: {e}")
            fail += 1

        if (success + fail) % 20 == 0:
            final_df.to_csv(args.manifest, index=False)

    final_df.to_csv(args.manifest, index=False)
    print(f"\n재작업 완료: 성공 {success}건 / 실패 {fail}건")

    check = pd.read_csv(args.manifest)
    print(f"\n전체 {len(check)}건")
    print("\n어절 수 검증:")
    print(check["word_count_ok"].value_counts())

    check["actual_words"] = check["replaced_tail"].astype(str).str.split().str.len()
    print("\n구간별 실제 어절 수 분포:")
    print(check.groupby(["ratio_bin", "actual_words"]).size())

    print("\n구간별 총 개수:")
    print(check["ratio_bin"].value_counts())


if __name__ == "__main__":
    main()
