# pixel-diet

**先看数字，再看像素。** 一个与框架无关的技能和命令行工具，用来评估计算机视觉输出：图像差异、分割掩码、
深度图，以及帮助人眼快速定位问题的对比图。

由 **Mind Space Studio** 开发和维护。MIT 许可证。

[English](README.md) · [简体中文](README.zh-CN.md) · [Русский](README.ru.md)

## 为什么需要它

人或智能体看到一张漂亮的样例，就容易忽略其他失败。视觉评估需要指标、样本量和生成这些数字的命令。
这个工具一次调用就能给出第一轮证据：

- **图像 / 渲染差异** — PSNR、SSIM、MAE、RMSE、变化百分比、连通错误区域（线 / 块 / 点）；
- **分割** — 每个类别的 IoU、Dice、precision、recall；
- **深度** — AbsRel、RMSE、δ1/δ2/δ3；
- **对比图** — A | B | 放大的差异图，让眼睛检查数字发现的问题；
- **退出码** — 指标低于阈值时让 CI 失败。

它不训练模型、不托管数据集，也不替代真正的测试集。它只让第一轮评估更便宜、更诚实。

## 为什么能节省 token

智能体每"看"一张图，在 Claude 上大约消耗 `宽 × 高 / 750` 个 token（单张上限约 1.6k）。比较两张渲染图就要为两张都付费。
pixel-diet 改为用数字给出结论，只有阈值失败时才需要打开对比图。

| 图像对 | 把 A + B 发给模型 | 紧凑 JSON（默认） | `--brief` 单行 |
|--------|------------------:|------------------:|---------------:|
| 1920×1080 | ~3,200 token | ~150 token（**~21×**） | ~55 token（**~58×**） |
| 1024×1024 | ~2,800 token | ~130 token（**~22×**） | ~45 token（**~64×**） |
| 256×256   | ~170 token   | ~125 token             | ~45 token（~4×） |

对比图默认宽 768 px（约 260 token）；`--sheet-width` 可以更小。在自己的文件上复现：
`python examples/token_budget.py A.png B.png`。数字为估算值（图像公式来自 Anthropic 文档，文本用代理分词器计数）；
智能体需要检查的图像对越多，节省越多。

## 快速开始

需要 Python ≥ 3.10；依赖只有 `numpy` 和 `Pillow`。

```bash
git clone https://github.com/slowpoke-flex/pixel-diet.git
cd pixel-diet
python -m pip install -e .
python examples/make_examples.py

pixel-diet diff examples/a.png examples/b.png --json report.json --sheet sheet.png
pixel-diet mask examples/mask_pred.png examples/mask_gt.png --classes 1
pixel-diet depth examples/depth_pred.npy examples/depth_gt.npy
```

输出示例：

```json
{
  "mae": 0.015852,
  "rmse": 0.080293,
  "psnr_db": 21.906,
  "ssim": 0.96038,
  "changed_pct": 6.866,
  "regions": [{"kind": "blob", "area": 3500, "box": [80, 70, 149, 119], "peak": 0.6588}]
}
```

## 命令

| 命令 | 作用 | CI 阈值 |
|---|---|---|
| `pixel-diet diff A B` | 图像/渲染指标、区域、可选对比图 | `--min-psnr 38` |
| `pixel-diet mask PRED GT` | 每个类别的 IoU/Dice/precision/recall | `--min-iou 0.8` |
| `pixel-diet depth PRED GT` | AbsRel/RMSE/δ，可选缩放 | `--max-absrel 0.1` |

所有命令输出紧凑 JSON（`--pretty` 缩进，`--brief` 输出单行结论）。`--json PATH` 始终写入完整报告，`--sheet PATH` 写入对比图。退出码：`0` 通过，`1` 阈值失败，
`2` 输入错误。

## 智能体技能

`SKILL.md` 是可复用的智能体指令，适用于 Claude Code、Codex、OpenCode、Cursor 以及任何能读文件、
运行命令的智能体。

- **Claude Code：** 把本目录复制到 `~/.claude/skills/pixel-diet/`。
- **Codex / OpenCode：** 把 `SKILL.md` 的内容加入 `AGENTS.md`，或在卡片中引用。
- **Cursor：** 把 `docs/integrations/cursor.md` 复制到 `.cursor/rules/pixel-diet.mdc`。
- **MCP：** 见 `docs/integrations/mcp.md`，把 CLI 包成工具。
- **GitHub Actions：** 见 `docs/integrations/github-actions.md`。

## 指标简表

命令行工具目前计算图像、分割和深度指标。其余行仅供选择指标参考，**尚未实现**。

| 任务 | 主要指标 | 次要指标 |
|---|---|---|
| 图像 / 渲染 | PSNR、SSIM、MAE | FLIP、变化百分比 |
| 分割 | IoU、Dice | 边界 F、每类 IoU |
| 检测 | mAP@IoU、precision/recall | 按类别/尺寸的 AP |
| 深度 | AbsRel、RMSE | δ1/δ2/δ3 |
| 光流 | EPE | 异常值比例、光流图 |
| 关键点 | PCK、NME | 每个关节误差 |

不要比较使用不同缩放、裁剪、色彩空间或归一化方式算出的指标。报告里要写明这些设置。

## 它不做什么

- 不是排行榜。
- 不判断图像是否“好看”。
- 不替代主观质量的人眼评审。
- 不用平均值掩盖一个坏样本。

## 文档

- [SKILL.md](SKILL.md) — 智能体规则和工作流。
- [examples/README.md](examples/README.md) — 合成样例和命令。
- [docs/github-topics.md](docs/github-topics.md) — GitHub 话题标签。
- [LAUNCH.md](LAUNCH.md) — 诚实的发布与传播计划。
- [English](README.md) · [Русский](README.ru.md)

## 许可证

MIT © 2026 Mind Space Studio。见 [LICENSE](LICENSE)。
