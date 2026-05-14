# 安装与使用参考

## 环境
- OS: Linux 6.17.0, x86_64
- Python: 3.11.15 (venv: ~/venv-basicsr)
- 无GPU，纯CPU模式
- ffmpeg: 6.1.1-3ubuntu5

## 已安装包
- torch (CPU) + torchvision (PyPI cpu index)
- basicsr (editable install, GitHub: XPixelGroup/BasicSR)
- tqdm, opencv-python-headless

## 模型文件路径
```
/tmp/basicsr-src/experiments/pretrained_models/ESRGAN/
├── ESRGAN_SRx4_DF2KOST_official-ff704c30.pth  (64MB, GAN版 — 画质更锐利)
└── ESRGAN_PSNR_SRx4_DF2K_official-150ff491.pth (64MB, PSNR版 — 更稳定)
```

## ESRGAN模型结构 (RRDBNet)
- 输入/输出通道: 3 (RGB)
- 特征通道: 64
- RRDB模块数: 23
- 增长通道: 32
- 放大倍数: 4x

## 性能实测 (CPU: AMD, 无GPU)

| 视频 | 分辨率 | 帧数 | 单帧耗时 | 总耗时 |
|------|--------|------|----------|--------|
| fish 1.mp4 | 744x496 | 151帧 | ~56s/帧 | ~2.5h |
| trees.mp4 | 784x470 | 151帧 | ~60s/帧 | ~2.5h |

> 批处理(batch_size=4)可提升约20-30%总体吞吐量，但受CPU算力限制仍很慢。推荐换用anime 6B模型（6个RRDB块 vs 23块，速度快约4倍）。

## 已知问题 (2025-05-14会话发现)
1. **ffprobe输出顺序**: `-show_entries stream=r_frame_rate,width,height` 输出顺序是 `width,height,r_frame_rate`，与参数顺序无关。已修复在脚本中
2. **wget下载GitHub Release Assets失败**: 返回0字节文件，改用 `gh release download` 成功
3. **RealESRGAN anime模型正确URL**: v0.2.2.4 (不是v0.1.0)
4. **rm -rf venv 重建时需要 approval**: 首次创建的venv因为conda污染了python路径，必须重建

## 动画模型下载
```bash
# 6B版动画模型 (6个RRDB, 推荐)
gh release download v0.2.2.4 --repo xinntao/Real-ESRGAN \
  --pattern "RealESRGAN_x4plus_anime_6B.pth" \
  --dir /tmp/basicsr-src/experiments/pretrained_models/RealESRGAN/ --clobber

# 动画视频v3模型 (更新的动画视频模型)
gh release download v0.2.5.0 --repo xinntao/Real-ESRGAN \
  --pattern "realesr-animevideov3.pth" \
  --dir /tmp/basicsr-src/experiments/pretrained_models/RealESRGAN/ --clobber
```

## 验证命令
```bash
source ~/venv-basicsr/bin/activate
python -c "from basicsr.archs.rrdbnet_arch import RRDBNet; m = RRDBNet(num_in_ch=3,num_out_ch=3,num_feat=64,num_block=23,num_grow_ch=32); print('Model class OK')"
python ~/.hermes/skills/media/ai-video-upscaling/scripts/video_upscale.py --help
```
