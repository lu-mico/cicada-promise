# ch4 v1.0 认可记录（Mico · 2026-11-05）

> 对象：`f20bef7`「ch4 v1.0：story-review full 四视角评审 → 改稿定稿」（11-05 14:17）
> 依据：`tracks/ch4-review.md` 第七节「复审结论」+ `tracks/ch4-daily.md` + `tracks/ch4-notes.md` §四/§六
> 机器证据：`tracks/ch4-acceptance-verification.md`（`fc09654`）
> 口径：沿用 `tracks/ch3-done.md` 的五条判据 + story-deslop 首跑 + Mico 抽验。

## 〇、认可结论

**五条全过 → ch4 v1.0 定稿，Mico 认可 ✅**

ch4 从此进入「已完成章」状态：可作为 ch5 起的连续性基准与埋线/事实源。

## 一、五条判据复核（对象 = 提交态 `f20bef7`，工作树 clean）

| # | 判据 | 门限 | 实测 | 判定 |
|---|---|---|---|---|
| 1 | 双线字数 | A ≥ 4,000 / B ≥ 4,000 / 合计 ≥ 8,000 | **A 4,681 / B 4,065 / 合计 8,746** | ✅ |
| 2 | 埋线回收 | 章内逐条闭合 | notes §四 逐行核对（新增：两份迁出、登记人小陈、操场钟） | ✅ |
| 3 | 章尾收束 | 最后一段 = 具体动作/物件 | 全章最后一段在 **B3**：「我站着听完了，才回家。」= 具体动作 + 具体动作 | ✅ |
| 4 | 规则零违规 | `check.py` 退出码 0 | **ERROR 0、退出码 0**；「三十」0 次 / B 线年份 0 个 / 林默主题句未新增 | ✅ |
| 5 | 交付物齐 | 合成稿 + 章级写作说明 + 自检输出 | `manuscripts/ch4-sample.md` + `tracks/ch4-notes.md`（含唯一事实源）+ `tracks/ch4-review.md` + 自检输出 | ✅ |
| — | story-deslop | 首跑完成、blocking=0 | `check-ai-patterns` **blocking=0** / `check-degeneration` **blocking=0**（在项目目录内跑，见下注） | ✅ |

## 二、我抽验的四处（人眼复核，非机器）

1. **S1 修法对症**：A1 原「注销没写。迁出也没写。什么都没有。」→ 改为「那一笔迁出以后，后面再没有夏家的字。」
   —— 从**否定排比立结论**改成**直接给事实**，正是 S1 要求的；且与 A2/A3 的「两册都在所里」不再冲突。
2. **S3 逐字重复已拆**：B1 §三 / B2 §六「领口最上面那颗扣子解开……铜丝贴着肉」22 字跨场重复 → 已拆。
3. **跨章口径三处对齐**：ch1「钟慢了五分钟」/ ch3 缸子在**床头**+旧毛巾 / ch2 迁移证明「夏晓晓，1996-08-12」→ 与正文口径一致。
4. **解释腔被删**：A3 §一/§七 的复述三明治（§一 复述、§七 再复述同一批信息）→ 按 review 表处置。

## 三、留给 ch5 的两条（不是欠账，是下一章的前置）

1. **B 线余量只有 65 字**（4,065 / 4,000）→ **ch5 起 B 线目标改为 ≥ 4,300**，别再赌余量（review §七「下一章注意」已采纳此建议）。
2. **唯一事实源**：以 `tracks/ch4-notes.md` §六 为准，**ch5 起必须沿用**（含两份迁出、登记人小陈、操场钟三处新增）。

## 四、作者保留的两条裁决（不影响 v1.0，留给后续章）

1. **成稿体例**：`（续）」与生产代号 `A1/B1/…/B3` 是否随成稿保留 → 建议在**导出成最终阅读稿**的那一刻统一处理（正文稿保留可读性，导出稿清理脚手架）。
2. **蝉蜕胸针是「同一件」还是「三件」**（plan-v2 §6）→ 影响 **ch8 合流**，ch5 起相关线索必须按同一口径写。

## 五、复现命令（含一个坑）

```bash
cd ~/.openclaw/workspace/projects/cicada-promise-yomi
git checkout -- . 2>/dev/null; git status --porcelain        # 应为 0 行（提交态即工作树）
python3 tracks/check.py manuscripts/ch4-sample.md             # 退出码须 0
node ~/.openclaw/workspace-yomi/skills/story-deslop/scripts/check-ai-patterns.js \
     --json manuscripts/ch4-sample.md                          # blocking 须 0
node ~/.openclaw/workspace-yomi/skills/story-deslop/scripts/check-degeneration.js \
     --json manuscripts/ch4-sample.md                          # blocking 须 0
```

⚠️ **坑**：白名单文件在 **`manuscripts/.deslop-whitelist`**（与稿件同目录）。
**必须就地跑**（把稿件复制到别处再跑 → 白名单不生效 → 会误报 18 条 blocking）。
（我今天 14:2x 就踩过一次：复制到 `/tmp` 跑 → 报 `em-dash blocking=18`；在项目目录内重跑 → **blocking=0**。）
