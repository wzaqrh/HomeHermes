#!/usr/bin/env python3
"""
AI视频增强工具 —— 基于BasicSR (ESRGAN) 的动画/视频超分
支持: 图片文件夹、单视频、批处理

用法:
  python video_upscale.py --input input.mp4 --output output.mp4 --scale 4
  python video_upscale.py --input frames_dir/ --output output_dir/ --scale 4

注意: 使用前确保 ~/venv-basicsr 已创建并激活
  source ~/venv-basicsr/bin/activate
"""

import argparse
import cv2
import glob
import numpy as np
import os
import subprocess
import sys
import torch
import tempfile
import shutil
from tqdm import tqdm

from basicsr.archs.rrdbnet_arch import RRDBNet


def load_model(model_path, device, scale=4):
    """加载 ESRGAN / PSNR 模型"""
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32)
    state_dict = torch.load(model_path, map_location=device, weights_only=True)
    if 'params' in state_dict:
        model.load_state_dict(state_dict['params'], strict=True)
    elif 'params_ema' in state_dict:
        model.load_state_dict(state_dict['params_ema'], strict=True)
    else:
        model.load_state_dict(state_dict, strict=True)
    model.eval()
    model = model.to(device)
    print(f"  Model loaded: {os.path.basename(model_path)} (scale={scale}x)")
    return model


def upscale_batch(model, img_paths, device, output_dir, batch_size=4):
    """
    批量超分图片 (比逐帧处理快2-4倍，因为有矩阵并行)
    """
    os.makedirs(output_dir, exist_ok=True)
    out_paths = []
    for i in range(0, len(img_paths), batch_size):
        batch = img_paths[i:i+batch_size]
        imgs = []
        bases = []
        for p in batch:
            img = cv2.imread(p, cv2.IMREAD_COLOR).astype(np.float32) / 255.
            img_t = torch.from_numpy(np.transpose(img[:, :, [2, 1, 0]], (2, 0, 1))).float()
            imgs.append(img_t)
            bases.append(os.path.splitext(os.path.basename(p))[0])
        batch_t = torch.stack(imgs).to(device)
        with torch.no_grad():
            outputs = model(batch_t)
        for j, output in enumerate(outputs):
            out = output.float().cpu().clamp_(0, 1).numpy()
            out = np.transpose(out[[2, 1, 0], :, :], (1, 2, 0))
            out = (out * 255.0).round().astype(np.uint8)
            out_path = os.path.join(output_dir, f"{bases[j]}_x4.png")
            cv2.imwrite(out_path, out)
            out_paths.append(out_path)
    return out_paths


def extract_frames(video_path, frames_dir):
    """用ffmpeg提取视频帧"""
    os.makedirs(frames_dir, exist_ok=True)
    cmd = [
        'ffmpeg', '-i', video_path,
        '-qscale:v', '1', '-qmin', '1', '-qmax', '1',
        '-vsync', '0',
        os.path.join(frames_dir, 'frame_%08d.png'),
        '-y', '-loglevel', 'error'
    ]
    subprocess.run(cmd, check=True)
    frames = sorted(glob.glob(os.path.join(frames_dir, 'frame_*.png')))
    print(f"  Extracted {len(frames)} frames from {video_path}")
    return frames


def combine_frames(frames_dir, output_video, fps):
    """用ffmpeg合并帧为视频"""
    cmd = [
        'ffmpeg',
        '-framerate', str(fps),
        '-i', os.path.join(frames_dir, 'frame_%08d.png'),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '18',
        '-preset', 'slow',
        output_video,
        '-y', '-loglevel', 'error'
    ]
    subprocess.run(cmd, check=True)
    print(f"  Video saved: {output_video}")


def process_video(model, input_video, output_video, device, tmp_dir):
    """处理完整视频工作流"""
    # 提取原始视频信息
    # 注意: ffprobe 的 -show_entries stream=width,height,r_frame_rate
    # 输出顺序永远是 width,height,r_frame_rate, 与参数顺序无关!
    probe_cmd = ['ffprobe', '-v', 'error',
                 '-select_streams', 'v:0',
                 '-show_entries', 'stream=width,height,r_frame_rate',
                 '-of', 'csv=p=0', input_video]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    parts = result.stdout.strip().split(',')
    w, h = int(parts[0]), int(parts[1])
    fps_str = parts[2]
    fps = eval(fps_str) if '/' in fps_str else float(fps_str)
    print(f"  Input: {w}x{h} @ {fps:.2f}fps -> Output: {w*4}x{h*4}")

    # 解帧
    frames_dir = os.path.join(tmp_dir, 'frames_original')
    frames = extract_frames(input_video, frames_dir)

    # 逐帧超分 (分批处理，提升CPU吞吐量)
    upscaled_dir = os.path.join(tmp_dir, 'frames_upscaled')
    for i in tqdm(range(0, len(frames), 4), desc="  Batch upscaling", unit="batch"):
        batch = frames[i:i+4]
        upscale_batch(model, batch, device, upscaled_dir, batch_size=4)

    # 合成视频
    combine_frames(upscaled_dir, output_video, fps)


def main():
    parser = argparse.ArgumentParser(description='BasicSR 动画/视频超分工具')
    parser.add_argument('--input', required=True, help='输入视频路径 或 图片文件夹')
    parser.add_argument('--output', default=None, help='输出视频/文件夹路径')
    parser.add_argument('--model', type=str,
                        default='/tmp/basicsr-src/experiments/pretrained_models/ESRGAN/ESRGAN_SRx4_DF2KOST_official-ff704c30.pth',
                        help='预训练模型路径')
    parser.add_argument('--scale', type=int, default=4, choices=[4], help='放大倍数')
    parser.add_argument('--device', type=str, default='cpu', help='设备: cpu / cuda')
    parser.add_argument('--batch-size', type=int, default=4, help='批处理大小 (CPU推荐4, GPU推荐8-16)')
    parser.add_argument('--keep-frames', action='store_true', help='保留中间帧文件')
    args = parser.parse_args()

    if args.output is None:
        base, ext = os.path.splitext(args.input)
        args.output = f"{base}_x4{ext}" if os.path.isfile(args.input) else f"{args.input}_x4"

    device = torch.device(args.device if torch.cuda.is_available() or args.device == 'cpu' else 'cpu')
    print(f"BasicSR Video Upscaler (x{args.scale})")
    print(f"  Device: {device}")
    print(f"  Input:  {args.input}")
    print(f"  Output: {args.output}")

    model = load_model(args.model, device, args.scale)

    tmp_dir = tempfile.mkdtemp(prefix='basicsr_')
    try:
        if os.path.isfile(args.input):
            # 输入是视频文件
            process_video(model, args.input, args.output, device, tmp_dir)
        elif os.path.isdir(args.input):
            # 输入是图片文件夹 -> 批量超分
            out_dir = args.output
            images = sorted(glob.glob(os.path.join(args.input, '*.[pj][np]g')))
            images += sorted(glob.glob(os.path.join(args.input, '*.png')))
            for i in tqdm(range(0, len(images), args.batch_size), desc="  Processing", unit="batch"):
                batch = images[i:i+args.batch_size]
                upscale_batch(model, batch, device, out_dir, batch_size=args.batch_size)
            print(f"  Saved {len(images)} upscaled images to {out_dir}")
    finally:
        if not args.keep_frames:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    print("Done!")


if __name__ == '__main__':
    main()
