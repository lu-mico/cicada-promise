#!/bin/zsh
# 兼容入口 —— ch7 版复审链已并入 `tracks/review_chain.sh`（**按章参数化**，2026-11-24 · G11a）。
#
# 为什么并：原来这条链**整份写死 ch7** → 拿它验 ch8 ＝ **验的不是本章**（ch7 G5 的教训）。
# 现在一条链按 CHAPTER 走：ch7／ch8 各跑各的章。
#
# 本文件只把 CHAPTER 固定为 ch7 → **ch7 模式的读数与并入前逐字相同**。
# 建议直接用统一入口：`CHAPTER=ch8 zsh tracks/review_chain.sh <sha>`
set -u
export CHAPTER=ch7
exec zsh "$(dirname "$0")/review_chain.sh" "$@"
