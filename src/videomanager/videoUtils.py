from VideoConstants import *
from src.audiomanager.AudioConstants import *
import os
import subprocess

def add_audio_to_video(outputvideofile):
    print("----------inside add music to video----------")
    outputvideofile = outputvideofile.replace(OUTPUT_VIDEO_FORMAT, "")
    # outputvideofile_music = outputvideofile + '_' + au.music_file.replace('.mp3', '')+output_video_format
    outputvideofile_music = outputvideofile + '_' + 'music' + OUTPUT_VIDEO_FORMAT
    try:
        os.remove(outputvideofile_music)
    except:
        pass
    cmd = 'ffmpeg -i '+outputvideofile+OUTPUT_VIDEO_FORMAT+' -i ' + MAIN_AUDIO + ' -c copy -map 0:v -map 1:a -shortest ' + outputvideofile_music
    os.system(cmd)
    print(cmd)
    return outputvideofile_music
    # try:
    #     os.remove(outputvideofile+output_video_format)
    # except:
    #     pass

def get_video_length(input_video):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_video], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return float(result.stdout)