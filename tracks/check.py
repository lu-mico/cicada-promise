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
    is_ch3 = "ch3" in p.name
    for title, body, body_no_head in picked:
        hanzi = len(HANZI.findall(body))
        is_b = bool(re.match(r"^B", title))
        print(f"  · {title}  正文汉字 {hanzi}")
        n30 = body.count("三十")
        if n30:
            errors.append(f"{title}: 「三十」出现 {n30} 次（rule 4 破线）")
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
        if "时间是一种很危险的东西" in body_no_head:
            msg = f"{title}: 出现林默主题句（ch1 已立）"
            (errors if is_ch3 else warns).append(msg)
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
