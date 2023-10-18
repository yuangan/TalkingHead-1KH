import argparse
import multiprocessing as mp
import os
from functools import partial
from time import time as timer

from pytube import YouTube
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('--input_list', type=str, required=True,
                    help='List of youtube video ids')
parser.add_argument('--output_dir', type=str, default='data/youtube_videos',
                    help='Location to download videos')
parser.add_argument('--start', type=int, default='50',
                    help='start offset')
parser.add_argument('--end', type=int, default='51',
                    help='end offset')
parser.add_argument('--num_workers', type=int, default=8,
                    help='How many multiprocessing workers?')
args = parser.parse_args()


def download_video(output_dir, video_id):
    r"""Download video."""
    merged_path = os.path.join(output_dir, video_id + '_full.mp4')
    if not os.path.isfile(merged_path):
        try:
            yt = YouTube('https://www.youtube.com/watch?v=%s' % (video_id))
            
            # Get the highest quality video and audio streams
            video_stream = yt.streams.filter(subtype='mp4', only_video=True, adaptive=True).first()
            audio_stream = yt.streams.filter(only_audio=True, adaptive=True).first()
            
            # Download the streams
            video_path = video_stream.download(output_path=output_dir, filename=video_id + '.mp4')
            audio_path = audio_stream.download(output_path=output_dir, filename=video_id + '_audio.mp4')
            
            # Merge the video and audio
            os.system(f'ffmpeg -i {video_path} -i {audio_path} -c:v copy -c:a aac {merged_path}')
            
            # Optionally, remove the separate video and audio files to save space
            # os.remove(video_path)
            os.remove(audio_path)
            
        except Exception as e:
            print(e)
            print('Failed to download %s' % (video_id))
    else:
        print('File exists: %s' % (video_id))


if __name__ == '__main__':
    # Read list of videos.
    video_ids = []
    with open(args.input_list) as fin:
        for line in fin:
            video_ids.append(line.strip())
    video_ids = video_ids[args.start:args.end]
    # Create output folder.
    os.makedirs(args.output_dir, exist_ok=True)

    # Download videos.
    downloader = partial(download_video, args.output_dir)

    start = timer()
    pool_size = args.num_workers
    print('Using pool size of %d' % (pool_size))
    with mp.Pool(processes=pool_size) as p:
        _ = list(tqdm(p.imap_unordered(downloader, video_ids), total=len(video_ids)))
    print('Elapsed time: %.2f' % (timer() - start))

