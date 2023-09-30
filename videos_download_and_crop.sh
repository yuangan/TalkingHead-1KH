dataset=$1
s = 50 # start
e = 100 # end
# Download the videos.
python videos_download.py --input_list data_list/${dataset}_video_ids.txt --output_dir ${dataset}/raw_videos --start  ${s} --end ${e}

# Split the videos into 1-min chunks.
#./videos_split.sh ${dataset}/raw_videos ${dataset}/1min_clips

# Extract the talking head clips.
#python videos_crop.py --input_dir ${dataset}/1min_clips/ --output_dir ${dataset}/cropped_clips --clip_info_file data_list/${dataset}_video_tubes.txt

#python audios_crop.py --input_dir ${dataset}/1min_clips/ --output_dir ${dataset}/cropped_clips --clip_info_file data_list/${dataset}_video_tubes.txt
