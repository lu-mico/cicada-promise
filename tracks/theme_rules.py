"""林默主题句规则（ch3–ch7 禁第三句）——2026-11-12 补门禁洞。

**为什么单独立模块**：旧判据写在 `tracks/check.py` 里，字面串
    "时间是一种很危险的东西" in body
但 ch1 的原句被对话打断 ——「"时间，"他说，"是一种很危险的东西。"」——
这个字面串在**任何正文里都不存在** → 那条限制**自 ch1 起从未生效过**。
补法（主编定，Mico 09:44 指出）：① 归一化（去标点/空白/引号）后再匹配，
对话插入 ≤8 字照样命中；② 另给「抽象名词作主语的判断句」候选——
新第三句无字可 grep，**只能评审兜底**，门禁只作回归。

`tracks/check.py` 与 `tracks/check_theme.py` 共用本模块，避免两处判据漂移。
"""

import re

CJK = re.compile(r"[\u4e00-\u9fff]")

# 切片/分线标题：## A1 · / ## B1 · / ## A 线 · / ## B 线 ·
SECTION = re.compile(r"^##\s+[AB]\s*(?:线|\d)")
# 正文段结束标记（写作说明 / 下一切片 之后一律不算正文）
END_MARK = re.compile(r"^##\s*(写作说明|下一切片|写作说明（评审参考）)")

# ── 字面命中（ch1 立句、ch2 降级句）────────────────────────────────────────
# 归一化后按 CJK 连续串匹配。
# **R46（Mico 2026-11-12 10:41 指出两处漏网）**：
#   ① 窗口 .{0,8} 太窄 → 带情绪节拍的长中断（"时间，"他停了一下，把书合上，"是一种很危险的东西。"）
#      会从两个门禁的缝里滑过去 → 窗口放 .{0,30}。
#   ② 字面式锚死在「时间」一个主语上 → 换主语（"记忆，"，他说，"是一种很危险的东西。"）
#      掉到 WARN 层 → 字面式加**主语组**（时间/记忆/遗忘/孤独/命运），且「很」设为可选。
#   两条都靠**句尾固定串**（「是一种很危险的东西」）定位，加宽窗口不会带来噪声。
THEME_PATTERNS = [
    re.compile(r"(?:时间|记忆|遗忘|孤独|命运).{0,30}是一种(?:很)?危险的东西"),
    re.compile(r"(?:时间|记忆|遗忘|孤独|命运).{0,30}不是被记住的是被用掉的"),
]

# ── 结构候选（无字可 grep → 评审兜底，门禁只报候选不作判定）──────────────
# 抽象名词作主语的判断句：时间／记忆／遗忘／孤独／命运 + 是/不是/会/能/该
# 窗口与字面式同步放 .{0,30}（R46 同批）。
ABSTRACT_SUBJECT = re.compile(r"(?:时间|记忆|遗忘|孤独|命运).{0,30}(?:是|不是|会|能|该)")

# ch3–ch7 禁第三句；ch1（立句）与 ch2（降级）已交付，允许
BANNED_FROM_CHAPTER = 3


def norm(text):
    """归一化：只留 CJK 汉字，丢掉标点、引号、空白与 Markdown 记号。"""
    return "".join(CJK.findall(text))


def slice_bodies(text):
    """切出 (标题, 正文段文本, 正文段去标题行文本)。

    与 `tracks/check.py` 同口径：正文段 = 分线/切片标题行起，到「## 写作说明」
    或「## 下一切片」之前；**不含顶部元信息抬头**（元信息区引用旧句不再误报）。
    """
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if not SECTION.match(lines[i]):
            i += 1
            continue
        title = lines[i][3:].strip()
        j = i + 1
        buf = []
        while j < len(lines):
            if END_MARK.match(lines[j]) or SECTION.match(lines[j]):
                break
            buf.append(lines[j])
            j += 1
        out.append((title, "\n".join([lines[i]] + buf), "\n".join(buf)))
        i = j
    return out


def theme_hits(body_no_head):
    """正文段里的主题句字面命中（归一化后）。返回命中片段列表。"""
    n = norm(body_no_head)
    hits = []
    for pat in THEME_PATTERNS:
        for m in pat.finditer(n):
            hits.append(n[max(0, m.start() - 4):m.end() + 4])
    return hits


def abstract_candidates(body_no_head):
    """抽象名词作主语的判断句候选（评审兜底用，门禁不作判定）。"""
    out = []
    for raw_line in body_no_head.split("\n"):
        n = norm(raw_line)
        if not n:
            continue
        for m in ABSTRACT_SUBJECT.finditer(n):
            out.append(n[max(0, m.start() - 4):m.end() + 6])
    return out


def chapter_of(filename):
    """从文件名取章号：ch5-sample.md → 5；认不出返回 None。"""
    m = re.search(r"ch(\d+)", filename)
    return int(m.group(1)) if m else None


def banned_for(chapter):
    """该章是否禁主题句（ch3 起禁；ch1／ch2 已交付允许；章号未知按禁处理）。"""
    if chapter is None:
        return True
    return chapter >= BANNED_FROM_CHAPTER
