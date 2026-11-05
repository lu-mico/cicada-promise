#!/usr/bin/env python3
"""合成章级样章：由六场切片组装 manuscripts/ch<N>-sample.md。

用法（项目根目录）：
    python3 tracks/compose.py            # 默认 ch3（输出与已交付的 a11955d 逐字节一致）
    python3 tracks/compose.py ch4        # 合成第四章
    python3 tracks/compose.py --chapter ch4

口径与 tracks/check.py 完全一致（非目测，可复现）：
  正文段 = 从切片/分线标题行起，到「## 写作说明」/「## 下一切片」之前。

组装时**只取切片正文**，丢弃每场切片自带的：
  ① 顶部元信息抬头（编制/轨道/大纲依据）
  ② 「## 写作说明」表 —— 其中含「手机 / 网络 / 现代品牌」等防漏复核词，
     留在正文段内会被 check.py 判为「B 线出现禁用现代物件」ERROR
  ③ 「## 下一切片」

章级写作说明正文来自 tracks/ch<N>-notes.md，合成为文件末的「## 写作说明（评审参考）」。

排布模式（per chapter）：
  by_line     —— A 线整块在前、B 线整块在后（ch3 原排法；**ch3 的评审 S1「双线未交错」不要带入 ch4**）
  interleaved —— A/B 逐场交错（ch4 用；依据 plan-v2 §5「20 章 × 双线，每章 A/B 交错」）。
                  2026-11-05 体例裁定：**每场一个 H2（场景标题带视角）**，不再输出
                  「## A 线 · …（续）」的分线 H2，也不再输出 H3 —— 交错排布下
                  「（续）」会出现四个（读者会读到四张「续」），H2+H3 双层则把成稿
                  切成两层目录。场景代号（A1／B2…）保留在 H2 里：ch3 已交付稿即
                  「### A1 · …」这一体例，且 tracks/check.py 的正文段口径
                  （SECTION 前缀 `## A1 ·` / `## A 线 ·`）依赖该前缀——不能在
                  ch4 v1.0 里顺手改测量脚本。彻底去代号另作书级口径变更。
"""

import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

SECTION = re.compile(r"^##\s+[AB]\s*(?:线|\d)")
END_MARK = re.compile(r"^##\s*(写作说明|下一切片)")
INNER_H = re.compile(r"^##\s+([一二三四五六七八九十]+)\s*$")
YEAR_TAG = re.compile(r"（([^）]*?)[，,]?\s*(?:19|20)\d{2}）")
TRAIL_POV = re.compile(r"（[^）]*）\s*$")

HEAD_CH3 = """# 《夏蝉的诺言》第三章·样章（A/B 双线）

> 编制：Yomi（主编）｜日期：2026-10-29
> 对应大纲：[outline/plan-v2.md §5 ch3](../outline/plan-v2.md)
> 合成来源：A 线 = [ch3-A1](ch3-A1.md) + [ch3-A2](ch3-A2.md) + [ch3-A3](ch3-A3.md)；
> B 线 = [ch3-B1](ch3-B1.md) + [ch3-B2](ch3-B2.md) + [ch3-B3](ch3-B3.md)
> 切片字数（check.py 实测）：A1 1,445 · A2 1,575 · A3 1,323 ｜ B1 1,444 · B2 1,598 · B3 1,431
> 章级完成判据：[tracks/ch3-done.md](../tracks/ch3-done.md)
> 版本：v0.1（章级首合，2026-10-29）
"""

HEAD_CH4 = """# 《夏蝉的诺言》第四章·样章（A/B 双线）

> 编制：Yomi（主编）｜日期：2026-11-03
> 对应大纲：[outline/plan-v2.md §5 ch4](../outline/plan-v2.md)
> 合成来源：A 线 = [ch4-A1](ch4-A1.md) + [ch4-A2](ch4-A2.md) + [ch4-A3](ch4-A3.md)；
> B 线 = [ch4-B1](ch4-B1.md) + [ch4-B2](ch4-B2.md) + [ch4-B3](ch4-B3.md)
> 合成顺序：A1 → B1 → A2 → B2 → A3 → B3（plan-v2 §5「20 章 × 双线，每章 A/B 交错」；
> ch3 评审 S1「双线未交错」的教训不带入本章）
> 本章双线：A 线 · 记录中断（周睿视角，2026）｜ B 线 · 灯台之约（晓晓视角，1996）
> 切片字数（check.py 实测）：A1 1,377 · A2 1,370 · A3 1,472 ｜ B1 1,382 · B2 1,311 · B3 1,400
> 章级完成判据：[tracks/ch3-done.md](../tracks/ch3-done.md)（字数口径唯一定义在 §四）
> 版本：v0.1（章级首合，2026-11-03）
"""

CHAPTERS = {
    "ch3": {
        "out": "ch3-sample.md",
        "notes": "ch3-notes.md",
        "order": ["A1", "A2", "A3", "B1", "B2", "B3"],
        "mode": "by_line",
        "slice_title": "full",   # H3 保留切片原题（含视角）
        "lines": {
            "A": {"title": "## A 线 · 不在场证明", "pov": "周睿视角，2026"},
            "B": {"title": "## B 线 · 重伤", "pov": "晓晓视角，1996"},
        },
        "head": HEAD_CH3,
    },
    "ch4": {
        "out": "ch4-sample.md",
        "notes": "ch4-notes.md",
        # 交错：每场 A/B 交替（plan-v2 §5「每章 A/B 交错」）
        "order": ["A1", "B1", "A2", "B2", "A3", "B3"],
        "mode": "interleaved",
        "slice_title": "short",  # H3 = "### A1 · 档案室"（视角由分线标题承担）
        "lines": {
            "A": {"title": "## A 线 · 记录中断", "pov": "周睿视角，2026"},
            "B": {"title": "## B 线 · 灯台之约", "pov": "晓晓视角，1996"},
        },
        "head": HEAD_CH4,
    },
}


def extract(chapter, slice_id, strip_year=True):
    """取一场切片的正文段。返回 (H3 标题, 正文行列表)。

    strip_year=True 时剥掉标题里的年份（B 线绝对禁止年份进入正文段）；
    A 线在交错排布下保留年份（视角标签要写清 2026）。
    """
    path = ROOT / "manuscripts" / f"{chapter}-{slice_id}.md"
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
        if strip_year:
            title = YEAR_TAG.sub(r"（\1）", title)
        title = "###" + title[2:]
        # 段内小标题：h2「## 一」→ h4「#### 一」
        buf = [INNER_H.sub(r"#### \1", ln) for ln in buf]
        # 去掉尾部空行
        while buf and not buf[-1].strip():
            buf.pop()
        return title, buf
    raise SystemExit(f"找不到正文段：{path}")


def slice_head(chapter, slice_id, full_title):
    """H3 标题：full = 原题（ch3）；short = "### A1 · 档案室"（ch4）。"""
    if CHAPTERS[chapter]["slice_title"] == "full":
        return full_title
    body = full_title[3:].strip()            # 去掉 "###"
    m = re.match(r"^([AB]\d)\s*·\s*(.*)$", body)
    if not m:
        return full_title
    sid, rest = m.group(1), TRAIL_POV.sub("", m.group(2)).strip()
    return f"### {sid} · {rest}" if rest else f"### {sid}"


def line_header(chapter, label, cont):
    spec = CHAPTERS[chapter]["lines"][label]
    if cont:
        return f"{spec['title']}（续）"
    return f"{spec['title']}（{spec['pov']}）"


def compose(chapter):
    cfg = CHAPTERS[chapter]
    parts = [cfg["head"], "\n---\n"]
    if cfg["mode"] == "by_line":
        for label in ("A", "B"):
            parts.append("\n" + line_header(chapter, label, False) + "\n\n")
            for sid in cfg["order"]:
                if not sid.startswith(label):
                    continue
                full, buf = extract(chapter, sid)
                parts.append(slice_head(chapter, sid, full) + "\n\n")
                parts.append("\n".join(buf).strip() + "\n\n")
            parts.append("\n---\n")
    else:  # interleaved —— 每场一个 H2，无「（续）」、无 H3 双层
        for sid in cfg["order"]:
            label = sid[0]
            # A 线标题保留年份（B 线标题剥掉年份）
            full, buf = extract(chapter, sid, strip_year=(label == "B"))
            parts.append("\n## " + full[3:].strip() + "\n\n")
            parts.append("\n".join(buf).strip() + "\n\n")
        parts.append("\n---\n")
    notes = ROOT / "tracks" / cfg["notes"]
    if not notes.exists():
        raise SystemExit(f"章级写作说明不存在：{notes}")
    parts.append("\n" + notes.read_text(encoding="utf-8").strip() + "\n")
    text = "".join(parts)
    out = ROOT / "manuscripts" / cfg["out"]
    out.write_text(text, encoding="utf-8")
    print(f"已写出 {out}（{len(text)} 字符，章节 {chapter}，排布 {cfg['mode']}）")


def main():
    args = sys.argv[1:]
    if args and args[0] in ("-c", "--chapter"):
        args = args[1:]
    chapter = args[0] if args else "ch3"
    if chapter not in CHAPTERS:
        print(f"未知章节：{chapter}（可选：{', '.join(CHAPTERS)}）", file=sys.stderr)
        return 2
    compose(chapter)
    return 0


if __name__ == "__main__":
    sys.exit(main())
