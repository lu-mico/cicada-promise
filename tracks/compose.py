#!/usr/bin/env python3
"""合成 ch3 章级样章：由六场切片组装 manuscripts/ch3-sample.md。

口径与 tracks/check.py 完全一致（非目测，可复现）：
  正文段 = 从切片/分线标题行起，到「## 写作说明」/「## 下一切片」之前。

组装时**只取切片正文**，丢弃每场切片自带的：
  ① 顶部元信息抬头（编制/轨道/大纲依据）
  ② 「## 写作说明」表 —— 其中含「手机 / 网络 / 现代品牌」等防漏复核词，
     留在正文段内会被 check.py 判为「B 线出现禁用现代物件」ERROR
  ③ 「## 下一切片」

章级写作说明正文来自 tracks/ch3-notes.md，合成为文件末的「## 写作说明（评审参考）」。

用法（项目根目录）：
    python3 tracks/compose.py
"""

import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "manuscripts" / "ch3-sample.md"
NOTES = ROOT / "tracks" / "ch3-notes.md"

SLICES = ["A1", "A2", "A3", "B1", "B2", "B3"]

SECTION = re.compile(r"^##\s+[AB]\s*(?:线|\d)")
END_MARK = re.compile(r"^##\s*(写作说明|下一切片)")
INNER_H = re.compile(r"^##\s+([一二三四五六七八九十]+)\s*$")
YEAR_TAG = re.compile(r"（([^）]*?)[，,]?\s*(?:19|20)\d{2}）")

A_HEADER = "## A 线 · 不在场证明（周睿视角，2026）"
B_HEADER = "## B 线 · 重伤（晓晓视角，1996）"

HEAD = """# 《夏蝉的诺言》第三章·样章（A/B 双线）

> 编制：Yomi（主编）｜日期：2026-10-29
> 对应大纲：[outline/plan-v2.md §5 ch3](../outline/plan-v2.md)
> 合成来源：A 线 = [ch3-A1](ch3-A1.md) + [ch3-A2](ch3-A2.md) + [ch3-A3](ch3-A3.md)；
> B 线 = [ch3-B1](ch3-B1.md) + [ch3-B2](ch3-B2.md) + [ch3-B3](ch3-B3.md)
> 切片字数（check.py 实测）：A1 1,445 · A2 1,575 · A3 1,323 ｜ B1 1,444 · B2 1,598 · B3 1,431
> 章级完成判据：[tracks/ch3-done.md](../tracks/ch3-done.md)
> 版本：v0.1（章级首合，2026-10-29）
"""


def extract(slice_id):
    path = ROOT / "manuscripts" / f"ch3-{slice_id}.md"
    lines = path.read_text(encoding="utf-8").split("\n")
    for i, line in enumerate(lines):
        if not SECTION.match(line):
            continue
        title = line
        j = i + 1
        buf = []
        while j < len(lines):
            if END_MARK.match(lines[j]) or SECTION.match(lines[j]):
                break
            buf.append(lines[j])
            j += 1
        # 标题：h2 → h3，并剥掉视角里的年份数字（B 线绝对禁止年份出现在正文段）
        title = YEAR_TAG.sub(r"（\1）", title)
        title = "###" + title[2:]
        # 段内小标题：h2「## 一」→ h4「#### 一」
        buf = [INNER_H.sub(r"#### \1", ln) for ln in buf]
        # 去掉尾部空行
        while buf and not buf[-1].strip():
            buf.pop()
        return title, buf
    raise SystemExit(f"找不到正文段：{path}")


def main():
    parts = [HEAD, "\n---\n"]
    for label, header in (("A", A_HEADER), ("B", B_HEADER)):
        parts.append("\n" + header + "\n\n")
        for sid in SLICES:
            if not sid.startswith(label):
                continue
            title, buf = extract(sid)
            parts.append(title + "\n\n")
            parts.append("\n".join(buf).strip() + "\n\n")
        parts.append("\n---\n")
    parts.append("\n" + NOTES.read_text(encoding="utf-8").strip() + "\n")
    text = "".join(parts)
    OUT.write_text(text, encoding="utf-8")
    print(f"已写出 {OUT}（{len(text)} 字符）")


if __name__ == "__main__":
    main()
