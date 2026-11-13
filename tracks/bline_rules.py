#!/usr/bin/env python3
"""B 线红线门禁（ch4 起）——署名线索与誓言语汇。

背景（2026-11-13）：Mico 在**切片级验收脚本**（他那侧）补了 B 线红线
「L」「永远」与 B3 誓言语汇「永不」「一辈子」「到死」，并做了负向测试。
但**仓库侧** `tracks/check.py` 从来没有查这几条——切片级守住的东西，
到了章级合成、阶段 3 四视角评审、v1.0 交付就没人守了。
本文件把同一批红线搬到仓库侧，与 check.py 的正文段口径完全一致（可复现、退出码判过）。

口径（与既有门禁同族，R44–R47 的纪律）：
  ① 只查 **B 线**：A 线不受约束——ch1 立句处的「L」「永远」是证物描写，不是红线。
  ② 只查 **ch4 起**：ch1–ch3 已交付，不追溯；ch2 正文里那处「一辈子」是人物原话。
  ③ 只查 **正文段**：写作说明表、顶部抬头、「下一切片」一律不入正文段
     （见 tracks/check.py 的 slice_bodies 口径）——ch4–ch6 各切片的
     「无「L」「永远」」等复核语句都在写作说明区，若不按正文段切，会全量误报。
  ④ 每个字都要能被「负向测试」打红：门禁自测 tracks/gate_selftest.py 里
     有本文件专属用例，并用 `--prove` 证明换回旧（坏的）判据时整套会变红。
"""

import re

# 署名语汇（胸针背面的刻字语汇：署名留 ch15，本章 B 线不得提前露出）
REDLINE_WORDS = ("永远", "永不", "一辈子", "到死")
# 署名首字母「L」：独立大写 L（不是单词的一部分）
LETTER_L = re.compile(r"(?<![A-Za-z])L(?![A-Za-z])")
# 称谓口径：一律「我爸」／「父亲」
FORBIDDEN_KINSHIP = ("夏父",)

# 红线自哪一章起生效（ch4 蝉蜕胸针＝信物，署名线索留到 ch8/ch15）
FROM_CHAPTER = 4


def redline_hits(body, chapter=None, is_b=True):
    """查 B 线红线，返回命中说明列表（空列表＝通过）。

    body     —— 正文段文本（含标题行）
    chapter  —— 章号（int 或 None；None 视为不启用）
    is_b     —— 该段是否属于 B 线
    """
    if not is_b:
        return []
    if chapter is not None and chapter < FROM_CHAPTER:
        return []
    hits = []
    for w in REDLINE_WORDS:
        if w in body:
            hits.append(f"红线语汇「{w}」×{body.count(w)}")
    if LETTER_L is not None and LETTER_L.search(body):
        hits.append(f"署名首字母「L」×{len(LETTER_L.findall(body))}")
    for w in FORBIDDEN_KINSHIP:
        if w in body:
            hits.append(f"禁用称谓「{w}」×{body.count(w)}")
    return hits


# ── 旧（坏的）判据，供 gate_selftest.py --prove 用 ─────────────────────────
# 只查「永远」，漏掉 L／永不／一辈子／到死／夏父——用来证明用例真在检验判据。
BROKEN_WORDS = ("永远",)
BROKEN_LETTER = None
BROKEN_KINSHIP = ()
