# Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
#
# This script is licensed under the MIT License.

import argparse
import multiprocessing as mp
import os
from functools import partial
from time import time as timer

import ffmpeg
from tqdm import tqdm


parser = argparse.ArgumentParser()
parser.add_argument('--input_dir', type=str, required=True,
                    help='Dir containing youtube clips.')
parser.add_argument('--clip_info_file', type=str, required=True,
                    help='File containing clip information.')
parser.add_argument('--output_dir', type=str, required=True,
                    help='Location to dump outputs.')
parser.add_argument('--num_workers', type=int, default=8,
                    help='How many multiprocessing workers?')
args = parser.parse_args()


def get_h_w(filepath):
    probe = ffmpeg.probe(filepath)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    height = int(video_stream['height'])
    width = int(video_stream['width'])
    return height, width

def get_fps(filepath):
    # 使用ffmpeg的probe功能来获取视频文件的元数据。
    probe = ffmpeg.probe(filepath)
    
    # 从元数据中找到视频流（因为一个媒体文件可能包含多个流，如视频流、音频流等）。
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    
    # 从视频流中提取平均帧速率（avg_frame_rate）。
    # 这通常是一个形如"30/1"的字符串，表示每秒30帧。我们使用eval函数来计算这个比率，得到实际的帧速率。
    return eval(video_stream['avg_frame_rate'])

def trim_and_crop(input_dir, output_dir, clip_params):
    video_name, H, W, S, E, L, T, R, B = clip_params.strip().split(',')
    H, W, S, E, L, T, R, B = int(H), int(W), int(S), int(E), int(L), int(T), int(R), int(B)
    output_filename = '{}_S{}_E{}_L{}_T{}_R{}_B{}.mp4'.format(video_name, S, E, L, T, R, B)
    output_filepath = os.path.join(output_dir, output_filename)
    if os.path.exists(output_filepath):
        print('Output file %s exists, skipping' % (output_filepath))
        return

    input_filepath = os.path.join(input_dir, video_name + '.mp4')
    print(input_filepath)
    if not os.path.exists(input_filepath):
        print('Input file %s does not exist, skipping' % (input_filepath))
        return

    h, w = get_h_w(input_filepath)
    fps = get_fps(input_filepath)

    t = int(T / H * h)
    b = int(B / H * h)
    l = int(L / W * w)
    r = int(R / W * w)

    video_stream = ffmpeg.input(input_filepath).video
    audio_stream = ffmpeg.input(input_filepath).audio

    video_stream = ffmpeg.trim(video_stream, start_frame=S, end_frame=E+1)
    video_stream = ffmpeg.crop(video_stream, l, t, r-l, b-t)

    # Trim the audio stream to match the video stream
    start_time = S / fps
    end_time = E / fps
    audio_stream = audio_stream.filter('atrim', start=start_time, end=end_time).filter('asetpts', 'PTS-STARTPTS')

    # Combine video and audio streams
    output_stream = ffmpeg.output(video_stream, audio_stream, output_filepath)
    ffmpeg.run(output_stream)

if __name__ == '__main__':
    # Read list of videos.
    clip_info = []
    with open(args.clip_info_file) as fin:
        for line in fin:
            clip_info.append(line.strip())

    # Create output folder.
    os.makedirs(args.output_dir, exist_ok=True)

    # Download videos.
    downloader = partial(trim_and_crop, args.input_dir, args.output_dir)

    start = timer()
    pool_size = args.num_workers
    print('Using pool size of %d' % (pool_size))
    with mp.Pool(processes=pool_size) as p:
        _ = list(tqdm(p.imap_unordered(downloader, clip_info), total=len(clip_info)))
    print('Elapsed time: %.2f' % (timer() - start))
