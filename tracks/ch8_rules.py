#!/usr/bin/env python3
"""ch8 章级判据（2026-11-24 立轨 · tracks/ch8-daily.md「八之二」D1／D2／D5／D6／D7）。

**为什么单独一个文件**：ch8 是**反转①的章**（plan-v2 §5 ch8「她三十年前就死了」），
它有几条**只属于 ch8** 的红线；写进共享脚本的通用分支会误伤别的章
（11/20 纪律：判据的作用域不得大于它要判的事实）→ 独立成文件，**按章调用**。

四条红线（每条都能被负向用例打红）：
  ① **D1／D4：林默 0 次**（A 线与 B 线都禁）—— ch8 A 线不得把林默与「三十年前」挂钩
     （plan-v2 §0 修订要点 2）；「林默葬仪外见白布」移到 ch9（D4）→ B 线同样 0 次。
  ② **D2：「三十年前」** —— A 线**最多 1 次**（首现就在 ch8，plan-v2 §0 防漏规则 4）；
     **B 线 0 次**。**放行的那一次由 `tracks/span_rules.py` 的章级白名单负责**
     （不���则「三十年」式硬跨度会把合规稿判红）。
  ③ **D6：她的死因定性不归本章** —— B 线不得出现「自杀」「病故」；
     「意外」只报 WARN（可能是普通词，交评审看，不直接罚）。
  ④ **D7：胸针 0 次**（四重身份里「署名」在 ch15；ch8 的题眼是合照与旧报纸）。

**ENABLED 开关**：`gate_selftest.py --prove` 会把它置 False（换成「不查」的坏判据）
→ 整套用例必须变红 → 证明这些用例真在检验判据，而不是摆设。
"""

ENABLED = True

# D6：B 线不得出现的死因定性词（定性词，不是普通用法）
B_DEATH_VERDICTS = ("自杀", "病故")
# D6：「意外」只报 WARN（普通用法可能无辜，交评审看）
B_DEATH_SOFT = ("意外",)
# D1／D4：全章不得出现的人名
FORBIDDEN_NAMES = ("林默",)
# D2：A 线允许且只允许的年数词（首现）
ALLOWED_PHRASE = "三十年前"


def ch8_hits(body, is_b=True):
    """查 ch8 章级红线，返回 (errors, warns) 两个列表（空＝通过）。"""
    if not ENABLED:
        return [], []
    errs, warns = [], []

    for w in FORBIDDEN_NAMES:
        n = body.count(w)
        if n:
            errs.append(f"D1/D4：出现「{w}」×{n}（ch8 两线林默 0 次出场）")

    n = body.count(ALLOWED_PHRASE)
    if is_b:
        if n:
            errs.append(f"D2：B 线出现「{ALLOWED_PHRASE}」×{n}（B 线 0 次）")
    elif n > 1:
        errs.append(f"D2：A 线出现「{ALLOWED_PHRASE}」×{n}（首现只允许 1 次）")

    if is_b:
        for w in B_DEATH_VERDICTS:
            if w in body:
                errs.append(f"D6：B 线出现「{w}」（她的死因定性归 ch9）")
        for w in B_DEATH_SOFT:
            if w in body:
                warns.append(f"D6：B 线出现「{w}」→ 复核是不是在给她的死定性")

    n = body.count("胸针")
    if n:
        errs.append(f"D7：出现「胸针」×{n}（ch8 胸针 0 次）")

    return errs, warns


# ── 旧（坏的）判据，供 gate_selftest.py --prove 用 ─────────────────────────
# 什么都不查 —— 用来证明 ch8 用例真在检验判据。
BROKEN_ENABLED = False
