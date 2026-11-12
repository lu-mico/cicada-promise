#!/usr/bin/env python3
"""ch3 切片自检：字数口径 + 防漏规则。非目测，可复现。

用法（在项目根目录）：
    python3 tracks/check.py manuscripts/ch3-A1.md manuscripts/ch3-B1.md manuscripts/ch2-sample.md

口径定义（全项目统一，不再各算各的）：
  正文段 = 从「## A1 ·」「## A 线 ·」这类**切片/分线标题行**开始，
           到「## 写作说明」/「## 下一切片」/ 下一个切片或分线标题之前；
           **不含**文件顶部元信息抬头，**不含**文末「## 写作说明」，
           但**包含**标题行本身与段内小标题（## 一 / ## 二 …）。
  字数 = 该正文段内 Unicode 汉字（U+4E00–U+9FFF）个数，不含标点、空格、Markdown 记号。
  年份扫描**跳过标题行**（形如「（晓晓视角，1996）」属结构标签，不算叙事文本泄漏）。

已校准（与已交付数字对齐）：
  manuscripts/ch2-sample.md  → A 2933 / B 2836（与 v1.0 交付口径一致）
  manuscripts/ch3-A1.md      → 正文 1445
  manuscripts/ch3-B1.md      → 正文 1444

退出码：0 = 全部通过；1 = 有 ERROR。WARN 不影响退出码。
"""

import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import theme_rules as tr  # noqa: E402  —— 主题句门禁（归一化匹配 + 章号分级）
import span_rules as sr  # noqa: E402  —— 年数跨度门禁（rule 4：只拦「三十年」式推算）

HANZI = re.compile(r"[\u4e00-\u9fff]")
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")

# 切片/分线标题：## A1 · / ## B1 · / ## A 线 · / ## B 线 ·
SECTION = re.compile(r"^##\s+[AB]\s*(?:线|\d)")
# 正文段结束标记
END_MARK = re.compile(r"^##\s*(写作说明|下一切片|写作说明（评审参考）)")

# B 线禁用现代物件（plan-v2 §4 防漏规则 1、2）
B_FORBIDDEN = [
    "手机", "网络", "上网", "短信", "微信", "网吧", "电脑", "监控",
    "可乐", "苹果", "华为", "小米", "尼康", "索尼",
]
# 只提醒不拦（1996 年可以有，但要看具体物件）
B_WARN = ["照片", "相机", "电视", "冰箱", "空调"]


def slice_bodies(text):
    """切出 (标题, 正文段文本)。正文段含标题行；年份扫描时另跳过标题行。"""
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
        body = "\n".join([lines[i]] + buf)
        out.append((title, body, "\n".join(buf)))
        i = j
    return out


def check_file(path):
    p = pathlib.Path(path)
    text = p.read_text(encoding="utf-8")
    errors, warns = [], []
    print(f"\n=== {path} ===")
    picked = slice_bodies(text)
    if not picked:
        errors.append("找不到正文段（既没有「## A1 ·」也没有「## A 线 ·」）")
    # 主题句门禁（2026-11-12 补洞）：
    #   旧判据 `"时间是一种很危险的东西" in body_no_head` **从 ch1 起从未成立**——
    #   ch1 原句被对话打断（"时间，"他说，"是一种很危险的东西。"），字面串在正文里不存在。
    #   现改为归一化后匹配（对话插入 ≤8 字照样命中），按章号分级：
    #   ch1（立句）／ch2（降级）已交付允许；**ch3 起为 ERROR**（ch3–ch7 禁第三句）。
    #   新第三句无字可 grep → 结构规则（抽象名词作主语的判断句）只报候选，由评审兜底。
    chapter = tr.chapter_of(p.name)
    theme_banned = tr.banned_for(chapter)
    for title, body, body_no_head in picked:
        hanzi = len(HANZI.findall(body))
        is_b = bool(re.match(r"^B", title))
        print(f"  · {title}  正文汉字 {hanzi}")
        # 年数跨度（rule 4）：**只拦「三十年」式推算**，不拦年龄说法。
        # 旧判据是 body.count("三十") → 把「三十多岁」这类年龄也判成 ERROR
        # （ch1 A 线「三十多岁的男人」是 Mico 已认可的交付稿，却因此挂着 ERROR 1）。
        # 同时补上旧门禁**根本没查**的两种写法：「二十九年」「多少年」。
        spans = sr.span_mentions(body)
        if spans:
            errors.append(f"{title}: 年数跨度出现 {len(spans)} 次（rule 4 破线）→ {spans[:3]}")
        years = YEAR.findall(body_no_head)
        if years:
            (errors if is_b else warns).append(
                f"{title}: 正文出现年份数字 {sorted(set(years))}"
                + ("（B 线绝对禁止）" if is_b else "（A 线为 2026 视角，仅提示）")
            )
        if is_b:
            hits = [w for w in B_FORBIDDEN if w in body]
            if hits:
                errors.append(f"{title}: B 线出现禁用现代物件 {hits}")
            whits = [w for w in B_WARN if w in body]
            if whits:
                warns.append(f"{title}: B 线出现需确认年代感的物件 {whits}")
        hits = tr.theme_hits(body_no_head)
        if hits:
            msg = f"{title}: 出现林默主题句（ch1 已立）→ {hits}"
            (errors if theme_banned else warns).append(msg)
        if theme_banned:
            cands = tr.abstract_candidates(body_no_head)
            if cands:
                warns.append(f"{title}: 抽象名词作主语的判断句（候选，需评审判定是否第三句）→ {cands[:3]}")
    for e in errors:
        print(f"  [ERROR] {e}")
    for w in warns:
        print(f"  [WARN]  {w}")
    if not errors:
        print("  [OK] 规则自检通过")
    return errors


def main():
    paths = sys.argv[1:]
    if not paths:
        print(__doc__)
        return 2
    all_errors = []
    for path in paths:
        all_errors += check_file(path)
    print(f"\n合计 ERROR {len(all_errors)} 项")
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
