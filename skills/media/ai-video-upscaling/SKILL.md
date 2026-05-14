---
name: ai-video-upscaling
description: >-
  AI视频超分增强 —— 使用BasicSR (ESRGAN/Real-ESRGAN) 修复低分辨率视频，
  特别是AI生成的动画/二次元内容。支持4x超分，工作流为 解帧→逐帧超分→合成。
trigger:
  - 视频超分
  - 视频增强
  - 低分辨率修复
  - 动画画质提升
  - video upscaling
  - video enhancement
  - ESRGAN
  - BasicSR
  - 低分动画修复
  - 4x超分
---

# AI 视频超分增强 (BasicSR + ESRGAN)

## 适用场景

- AI生成的低分辨率动画/视频修复（如SD生成的短视频）
- 老动画/老片源 4x 超分放大
- 任何需要帧级超分辨率处理的视频

## 环境安装

```bash
# Python 3.11 测试通过（3.13可能不兼容）
python3.11 -m venv ~/venv-basicsr
source ~/venv-basicsr/bin/activate

# 安装 PyTorch (CPU版，GPU请替换cuda版本)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 安装 BasicSR + 依赖
git clone --depth 1 https://github.com/XPixelGroup/BasicSR.git /tmp/basicsr-src
pip install -e /tmp/basicsr-src --no-build-isolation
pip install tqdm opencv-python-headless ffmpeg-python
```

## 下载预训练模型

```bash
source ~/venv-basicsr/bin/activate
cd /tmp/basicsr-src

# 下载 ESRGAN 模型（4x 超分，GAN版画质更好）
python scripts/download_pretrained_models.py ESRGAN
# 会下载到: experiments/pretrained_models/ESRGAN/

# 如需BasicVSR（视频级时序修复）
python scripts/download_pretrained_models.py BasicVSR
```

## 工作流程

```
输入视频 → ffmpeg解帧 → ESRGAN逐帧4x超分(分批) → ffmpeg合成 → 输出视频
```

核心优化：使用 batch_size=4 分批处理帧（torch.stack），比逐帧快2-4倍。

## 使用

使用配套脚本（位于 skill 目录下）：

```bash
source ~/venv-basicsr/bin/activate

# 单视频增强 (自动4x超分)
python ~/.hermes/skills/media/ai-video-upscaling/scripts/video_upscale.py --input your_video.mp4

# 自定输出路径
python ~/.hermes/skills/media/ai-video-upscaling/scripts/video_upscale.py --input input.mp4 --output hd_result.mp4

# 批量图片 (可指定批大小，CPU推荐4, GPU推荐16)
python ~/.hermes/skills/media/ai-video-upscaling/scripts/video_upscale.py --input ./frames/ --output ./hd_frames/ --batch-size 8

# GPU加速 (如有NVIDIA显卡)
python ~/.hermes/skills/media/ai-video-upscaling/scripts/video_upscale.py --input video.mp4 --device cuda
```

## 可用模型

| 模型 | 说明 | 适用 |
|------|------|------|
| ESRGAN_SRx4_DF2KOST_official | GAN训练，画质更锐利 | 通用视频/动画 |
| ESRGAN_PSNR_SRx4_DF2K_official | PSNR训练，更稳定 | 需要保真度的场景 |
| RealESRGAN_x4plus_anime_6B | 动画专用模型 (6个RRDB块，速度快4倍) | **推荐**：二次元动画 |
| realesr-animevideov3 | 动画视频专用 (v3，效果更好) | 动画视频优化 |

> 下载动画专用模型：
> ```bash
> # 方法1: gh CLI (推荐，国内网络友好)
> gh release download v0.2.2.4 --repo xinntao/Real-ESRGAN --pattern "RealESRGAN_x4plus_anime_6B.pth" --dir /tmp/basicsr-src/experiments/pretrained_models/RealESRGAN/ --clobber
>
> # 方法2: 手动下载链接
> # RealESRGAN_x4plus_anime_6B (推荐): https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth
> # realesr-animevideov3: https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth
> ```
> 注意：`wget`/`curl` 直接下载 GitHub release assets 在某些网络环境下可能返回空文件（0字节），此时请使用 `gh release download` 命令。

## 配套脚本

该技能附带一个可直接运行的脚本（位于 `scripts/video_upscale.py`），支持视频和图片文件夹的4x超分，调用方式：

```bash
source ~/venv-basicsr/bin/activate
python ~/.hermes/skills/media/ai-video-upscaling/scripts/video_upscale.py --input video.mp4
```

脚本已内置批量处理优化（默认batch_size=4），支持 --batch-size 参数调节。

## 参考文档

- `references/session-install-details.md` — 本会话安装详情和环境配置

## Pitfalls

1. **Python版本问题**: BasicSR 的 setup.py 在 Python 3.13 上会报 `KeyError: '__version__'`，必须用 Python 3.11/3.12
2. **pip install basicsr 失败**: 不要直接从 PyPI 装，GitHub clone 后用 `pip install -e . --no-build-isolation`
3. **GPU显存**: 4x超分每帧至少需 2GB VRAM（1080p→4K 很大）。没有GPU用CPU极慢，需了解实际速度预期
4. **CPU推理速度**: 全量RRDBNet (23块) 在CPU上每帧约 **50-60秒** (744x496分辨率)。5秒30fps视频(151帧)约需2.5小时。**必须使用 --batch-size 4 批量处理** 以提高CPU吞吐量（分批堆叠帧让PyTorch并行矩阵运算）。如换用 anime 6B模型（仅6个RRDB块），速度可提升约4倍
5. **GPU加速**: 如有NVIDIA显卡，使用 `--device cuda` 可将每帧时间从56秒降至约0.5-2秒（取决于显卡）
6. **ffprobe字段顺序陷阱**: `-show_entries stream=width,height,r_frame_rate` 的输出顺序永远是 **width,height,r_frame_rate**，与参数书写顺序无关。脚本中解析时必须按这个顺序，不要想当然按参数顺序解析
7. **GitHub下载模型失败**: `wget`/`curl` 下载 GitHub release assets 可能返回 0 字节（某些网络环境受限），需改用 `gh release download` 命令
8. **帧率保持**: 脚本自动读取原视频帧率并保持，但超分后文件体积会增大数倍（分辨率4倍、文件大小约4-8倍）
9. **ESRGAN vs Real-ESRGAN**: BasicSR自带的ESRGAN模型较旧，Real-ESRGAN的模型更新效果更好。如果追求画质，建议替换为Real-ESRGAN的模型文件（架构兼容 RRDBNet）
10. **ffmpeg依赖**: 必须预先安装 ffmpeg，用于解帧和合成
