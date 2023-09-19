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
    probe = ffmpeg.probe(filepath)
    
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    
    return eval(video_stream['avg_frame_rate'])

# This can not be used to extract audio and video together, unkown reason, the output of some video will be static. :(
def trim_and_crop(input_dir, output_dir, clip_params):
    video_name, H, W, S, E, L, T, R, B = clip_params.strip().split(',')
    video_name = video_name[:-4] + 'full_' + video_name[-4:]
    H, W, S, E, L, T, R, B = int(H), int(W), int(S), int(E), int(L), int(T), int(R), int(B)
    output_filename = '{}_S{}_E{}_L{}_T{}_R{}_B{}_audio.mp4'.format(video_name, S, E, L, T, R, B)
    output_filepath = os.path.join(output_dir, output_filename)
    if os.path.exists(output_filepath):
        print('Output file %s exists, skipping' % (output_filepath))
        return

    input_filepath = os.path.join(input_dir, video_name + '.mp4')
    if not os.path.exists(input_filepath):
        print('Input file %s does not exist, skipping' % (input_filepath))
        return

    h, w = get_h_w(input_filepath)
    fps = get_fps(input_filepath)

    t = int(T / H * h)
    b = int(B / H * h)
    l = int(L / W * w)
    r = int(R / W * w)

    audio_stream = ffmpeg.input(input_filepath).audio
    
    # Trim the audio stream to match the video stream
    start_time = S / fps
    end_time = (E+1) / fps
    audio_stream = audio_stream.filter('atrim', start=start_time, end=end_time).filter('asetpts', 'PTS-STARTPTS')

    # Combine video and audio streams
    output_stream = ffmpeg.output(audio_stream, output_filepath)
    ffmpeg.run(output_stream)
    video_path=output_filepath.replace('_full_', '_')[:-10]+'.mp4'
    final_output=output_filepath[:-10]+'.mp4'
    os.system(f'/usr/bin/ffmpeg -i {video_path} -i {output_filepath} -c:v copy -c:a aac -crf 20 {final_output}')


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
    # pool_size = args.num_workers
    pool_size = 1
    print('Using pool size of %d' % (pool_size))
    with mp.Pool(processes=pool_size) as p:
        _ = list(tqdm(p.imap_unordered(downloader, clip_info), total=len(clip_info)))
    print('Elapsed time: %.2f' % (timer() - start))
