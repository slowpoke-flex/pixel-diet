# pixel-diet

[![tests](https://github.com/slowpoke-flex/pixel-diet/actions/workflows/tests.yml/badge.svg)](https://github.com/slowpoke-flex/pixel-diet/actions/workflows/tests.yml)

**截图里的大部分内容不是信息。** 一张 1920×1080 的图片对视觉模型来说约 2,765 个图像 token —— 空白边距、壁纸和压缩噪点，
和你真正要问的那个按钮一样贵。

`pixel-diet` 是一个小型 Python 库和命令行工具：在图片进入 GPT-4o、Claude、Gemini 或本地 Qwen-VL **之前**，
按命名预设裁剪、缩放并重新编码。同一个包还能把图片比较变成数字，让智能体在指标足够回答问题时完全不必看图。

由 **Mind Space Studio** 开发和维护。MIT 许可证。

[English](README.md) · [简体中文](README.zh-CN.md) · [Русский](README.ru.md)

## 实测节省（数字，不是承诺）

五张合成输入，由 `examples/shrink_demo.py` 生成，在本机测量（Windows 11、Python 3.14、Pillow 13.0.0，2026-10-26）：

| 输入 | 预设 | 像素 | 字节 | 估算图像 token |
|---|---|---|---:|---:|
| 纯色边框 UI | `ui-agent` | 1920×1080 → 1280×678 | 9,811 → 8,152（−16.9%） | 2,765 → 1,158（**2.39×**） |
| 桌面截图 | `ui-agent` | 1920×1080 → 1280×720 | 2,180,496 → 9,854（−99.5%） | 2,765 → 1,229（**2.25×**） |
| A4 文档 | `ocr-document` | 1654×2339 → 800×1024 | 16,987 → 3,714（−78.1%） | 5,159 → 1,093（**4.72×**） |
| 游戏精灵 | `game-sprite` | 512×512 → 225×289 | 1,865 → 120（−93.6%） | 350 → 87（**4.02×**） |
| 摄像头画面 | `edge-fast` | 1600×900 → 768×432 | 14,852 → 3,208（−78.4%） | 1,920 → 443（**4.33×**） |

复现：`python examples/shrink_demo.py`

请诚实地读这张表：

- **字节是真实的**文件大小；**图像 token 是估算值**，公式为 `ceil(宽 × 高 / 750)`（Anthropic 公布的图像公式）。
  实际计费还取决于模型、服务商和提示词的其余部分。
- 输入是合成的替代样本，不是客户截图。纯色 UI 那一行是最弱的情况：纯色 PNG 本来就小，裁剪和重编码对**字节**帮助不大，
  但 **token** 仍然降到 2.4 分之一。带宽收益出现在照片类截图（桌面那一行）。
- 这里没有"模型输出完全一致"的承诺。缩小可能抹掉 6 px 的标签。请在**自己的任务**上验证。

## 安装

PyPI 名称留给首次发布；在此之前从仓库安装：

```bash
git clone https://github.com/slowpoke-flex/pixel-diet.git
cd pixel-diet
python -m pip install -e .
```

需要 Python ≥ 3.10，依赖只有 `numpy` 和 `Pillow`。不需要编译器、OpenCV 或模型权重。

## 用法

```python
from pixel_diet import optimize_for_llm, optimize_bytes

uri = optimize_for_llm("raw_screenshot.png", preset="ui-agent")   # data:image/webp;base64,...
clean = optimize_bytes(raw_bytes, preset="ocr-document", max_dimension=1024)
```

`optimize()` 接受路径、`BytesIO`、PIL 图像或 numpy 数组，返回 `Result`（`data`、`width`、`height`、
`saved_pct`、`tokens_before`、`tokens_after`、`token_ratio`、`.data_uri`）。

```bash
pixel-diet shrink screenshot.png -o slim.webp --preset ui-agent
pixel-diet shrink ./invoices -o ./clean --preset ocr-document --json report.json
cat shot.png | pixel-diet shrink - -o - --preset ui-agent > slim.webp
```

`--max-dimension`、`--format webp|png|jpeg`、`--quality`、`--no-trim` 可覆盖预设。

### 预设

| 预设 | 处理流程 | 适用 |
|---|---|---|
| `ui-agent` | 裁掉与角落同色的边框，长边限制 1280 px，WebP q80 | 浏览器自动化、RPA、UI 智能体 |
| `ocr-document` | 裁掉均匀边距，灰度，自动对比度，限制 1024 px，WebP q85 | 收据、发票、扫描件 |
| `game-sprite` | 按 alpha 包围盒裁剪，无损 WebP，最近邻安全 | 2D 精灵、图块、图标 |
| `edge-fast` | 双线性缩放到 768 px，WebP q65 | 摄像头、无人机、弱网 |

### 两个容易踩的坑

1. **坐标。** 从缩小图读到的 (x, y) 必须映射回去：`x * source_width / width`，y 同理。需要原始取景时用 `--no-trim`。
2. **小字。** 缩放可能抹掉 6–8 px 的标签。`ocr-document` 保留对比度但仍限制 1024 px；可读性优先时调大 `--max-dimension`。

## 验证后再信任

缩小本质上是有损的。诚实的流程是：缩小、跑任务、和全尺寸结果对比。这个包的另一半用数字完成对比：

```bash
pixel-diet diff full.png shrunk.png --brief
pixel-diet mask pred.png gt.png --classes 1
pixel-diet depth pred.npy gt.npy
```

## 它不是什么

- 不是模型、数据集或排行榜。
- 不是 CDN、图床或归档格式转换器。
- 不判断两张图对你的任务是否"相同"；它给出数字，由你判断。

## 文档

- [SKILL.md](SKILL.md) — 智能体规则：何时缩小、何时不要、如何报告。
- [README.md](README.md) — 完整英文说明与实测表。
- [LAUNCH.md](LAUNCH.md) · [PUBLISH.md](PUBLISH.md)
- [Русская инструкция](README.ru.md)

## 许可证

MIT © 2026 Mind Space Studio。见 [LICENSE](LICENSE)。
