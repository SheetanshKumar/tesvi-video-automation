import random
from src.audiomanager.AudioConstants import *
from gtts import gTTS
import os
from mutagen.mp3 import MP3
import subprocess


def get_audio_duration(filename):
    audio = MP3(filename)
    return audio.info.length

def create_blank_audio(blank_audio_location, time):
    filename = BLANKAUDIO + '_' + str(time) + '.mp3'
    st = "ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t {} -q:a 9 -acodec libmp3lame " + blank_audio_location + filename
    try:
        os.remove(blank_audio_location + filename)
    except Exception as e:
        print(e)
    st = st.format(str(time))
    print(st)
    os.system(st)
    print('-------------blank audio created---------------')
    # for i in range(1, 21):
    #     print(st.format(i, i))
    #     os.system(st.format(i, i))

def get_random_from_list(lis):
    r1 = random.randint(0, len(lis) - 1)
    return lis[r1]

def concat_audios(lis, file_location):
    st = ["ffmpeg"]
    for i in range(len(lis)):
        st.append("-i")
        st.append(lis[i])
    st.append("-filter_complex")
    st = ' '.join(st) + " "
    for i in range(len(lis)):
        st = st + "[" + str(i) + ":0]"

    st = st + "concat=n=" + str(len(lis)) + ":v=0:a=1[out] -map [out] " + file_location
    print(st)
    try:
        os.remove(file_location)
    except:
        pass
    subprocess.run([st], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True)
    # out = subprocess.Popen(st, shell=True).wait()
    # out = os.system(st)
    # for i in lis:
    #     os.remove(i)
    print("------------------------------Audio Concatinated at ----------------------------{}".format(file_location))
    return st

def create_audio_text_concat_command(n, file_location, outputfile):
    st = ["ffmpeg"]
    for i in range(n):
        st.append("-i")
        st.append(file_location+"audio"+str(i+1)+".mp3")
    st.append("-filter_complex")
    st = ' '.join(st)+" "
    for i in range(n):
        st = st + "["+str(i)+":0]"

    st = st + "concat=n=" + str(n) + ":v=0:a=1[out] -map [out] " + file_location+outputfile
    print(st)
    return st

def merge_audio_with_music(audiopath, musicpath, outputfile):
    cmd = '''ffmpeg -y -i {} -i {} -filter_complex "[0:0]volume={}[a];[1:0]volume={}[b];[a][b]amix=inputs=2:duration=shortest" -c:a libmp3lame {}'''
    cmd = cmd.format(musicpath, audiopath, MUSIC_LEVEL, AUDIO_LEVEL, outputfile)
    try:
        os.remove(AUDIO_LOCATION + outputfile)
    except:
        pass
    print(cmd)
    os.system(cmd)
    print("----------------------Audio Merged with Music-------------------------")
    return cmd


# def alter_audio_tempo_dict(dictionary):
#     print(dictionary)
#     new_dictionary = dict()
#     for filepath in list(dictionary.keys()):
#         filename = filepath.split('/')[-1]
#         filepath = filepath.replace('/changed_tempo', '')
#         new_filepath = tempo_file_location+filename
#         try:
#             audio_tempo = alter_audio_tempo_map[filepath]
#         except:
#             audio_tempo = data_audio_tempo
#         print(audio_tempo)
#         st = '''ffmpeg -i {} -filter:a "atempo={}" -vn {}'''.format(filepath, audio_tempo, new_filepath)
#         try:
#             os.remove(new_filepath)
#         except Exception as e:
#             print(e)
#         print(st)
#         os.system(st)
#         # os.rename(filepath.replace('.mp3', '_new.mp3'), filepath)
#         # dictionary[filepath] = get_audio_duration(filepath)
#         new_dictionary[new_filepath] = get_audio_duration(new_filepath)
#     print("-------------------------Tempo set to {}-----------------------------------".format(audio_tempo))
#     return new_dictionary