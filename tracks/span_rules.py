"""年数跨度判据（rule 4）——2026-11-12 与主题句门禁同批补洞。

**为什么补**：旧判据是 `body.count("三十")` → **任何**「三十」二字一律 ERROR。
但「三十」有两种完全不同的用法：
- **年数跨度**（「三十年」「三十年前」「三十多年前的」「三十七年前」「二十九年」「多少年」）
  → 破 rule 4，**必须拦**；
- **年龄/计数/时刻说法**（「三十多岁」「三十岁」「三十来岁」「三十出头」「三十七分」「三十几个人」）
  → 与三十年跨度无关，**不该拦**。

**证据（不是推测）**：ch1 A 线原句「镜子里映出一个三十多岁的男人」是 **Mico 已认可的交付稿**，
旧粗规则却把它判成 ERROR（ch1-sample 至今挂着 ERROR 1，即此误报）→ 语义上的正解是**跨度**，
不是「三十」二字本身。另外「二十九年」「多少年」两种跨度写法**旧门禁根本没查**（真漏网）。

判定：**「三十」后接年/载（含「多/几/余/来」与阿拉伯数字的修饰）＝跨度＝拦**；
其余一律放行（年龄、计数、时刻、裸数字）。

用法：见 `tracks/check.py` 与 `tracks/gate_selftest.py`。
"""

import re

# ── 跨度式（拦）────────────────────────────────────────────────────────────
# 「三十」+ 可选修饰（多/几/余/来）+ 可选一到两位数 + 年/载
_SPAN_PATTERNS = [
    re.compile(r"三十[多几余来]?[一二三四五六七八九十]{0,2}[年载]"),
    re.compile(r"二十九[一二三四五六七八九十]{0,2}年"),
    re.compile(r"多少年"),
    re.compile(r"30\s*年"),
]

# ── 软跨度（只报 WARN，交评审；不拦）────────────────────────────────────
# Mico 2026-11-12 10:41：「十几年／二十多年／十多年／好多年」这类**不构成推算**
# （已交付稿里本来就有这类写法）→ **只报 WARN，不报 ERROR**。
# 注意末尾必须是「年/载」才算跨度：「二十多个人」「十几个牌」是计数，**不匹配**。
_SOFT_SPAN_PATTERNS = [
    re.compile(r"十几[年载]"),
    re.compile(r"二十多[年载]"),
    re.compile(r"十多年"),
    re.compile(r"十来年"),
    re.compile(r"二十来年"),
    re.compile(r"好多年"),
]


# ── 章级放行（2026-11-24 · tracks/ch8-daily.md「八之二」D2/D12）────────────
# plan-v2 §0 防漏规则 4：「三十年前」一词**首次出现必须 ≥ ch8**。
#   ch3–ch7 的门禁一律拦「三十年」式硬跨度（含「三十年前」「三十年前的」）
#   → 到了 ch8 就必须**放行这一处**，否则合规稿会被判红（11/20 纪律：判据不得罚合格稿）。
#   放行条件三条，缺一不可：
#     ① 章号是 ch8；② 该段是 **A 线**（B 线仍拦）；③ 该词形**只放行一次**（第二次仍拦）。
#   其它推算写法（「三十年整」「多少年」「二十九年」「快三十年」）**一律不放行**。
ALLOWED_SPAN_PHRASES = {
    "ch8": ("三十年前",),
}


def _norm_chapter(chapter):
    """章号归一：8 / '8' / 'ch8' 一律 → 'ch8'。"""
    if chapter is None:
        return None
    s = str(chapter).strip().lower()
    if s.isdigit():
        s = "ch" + s
    return s


def span_mentions(body, chapter=None, is_b=False):
    """正文段里的年数跨度提及（返回上下文片段列表）——**硬跨度，报 ERROR**。

    年龄/计数/时刻写法不计入；「三十」后接年/载一律计入（默认严格）。

    chapter／is_b：章级放行用（见 ALLOWED_SPAN_PHRASES）。
    不传 chapter 时行为与放行前**完全相同**（旧调用方不受影响）。
    """
    out = []
    allowed = () if is_b else ALLOWED_SPAN_PHRASES.get(_norm_chapter(chapter), ())
    used = {p: 0 for p in allowed}
    for pat in _SPAN_PATTERNS:
        for m in pat.finditer(body):
            frag = body[max(0, m.start() - 6):m.end() + 8].replace("\n", " ")
            skip = False
            for phrase in allowed:
                if phrase in frag and used[phrase] == 0:
                    used[phrase] += 1
                    skip = True
                    break
            if not skip:
                out.append(frag)
    return out


def soft_span_mentions(body):
    """软跨度提及（十几年／二十多年／十多年／好多年…）——**只报 WARN，交评审**。

    这类写法不构成年数推算（已交付稿里本来就有），故不作硬拦截。
    """
    out = []
    for pat in _SOFT_SPAN_PATTERNS:
        for m in pat.finditer(body):
            out.append(body[max(0, m.start() - 6):m.end() + 8].replace("\n", " "))
    return out
