from src.audiomanager.AssistantUtils import *
from src.audiomanager.AudioUtils import *
from src.audiomanager.AudioText import *
from src.datamanager.QuestionModel import *


screenCount = 0
MP3 = '.mp3'


def attach_bell(screen_time_map):
    screen_time_map[list(screen_time_map.keys())[-1]+'_bell'] = [get_audio_duration(AUDIO_LOCATION_MISC+BELL), AUDIO_LOCATION_MISC+BELL]
    return screen_time_map


def attach_blank(screen_time_map, key, time):
    screenkey = key + '_blank_'+str(time) + '.mp3'
    screen_time_map[screenkey] = [get_audio_duration(AUDIO_LOCATION_BLANK + 'blank_' + str(time) + '.mp3'), AUDIO_LOCATION_BLANK + 'blank_' + str(time) + '.mp3']
    return screen_time_map


def get_intro_static_audio(screen_time_map):
    global screenCount
    screenCount += 1
    screenkey = SCREEN + str(screenCount) + MP3
    screen_time_map[screenkey] = [get_audio_duration(AUDIO_LOCATION_STATIC_GENDER + screenkey), AUDIO_LOCATION_STATIC_GENDER + screenkey]

    screenCount += 1
    screenkey = SCREEN + str(screenCount) + MP3
    screen_time_map[screenkey] = [get_audio_duration(AUDIO_LOCATION_STATIC_GENDER + screenkey), AUDIO_LOCATION_STATIC_GENDER + screenkey]

    return screen_time_map


def get_list_audio_concat(screen_time_map):
    audio_location_list = []
    for key in screen_time_map.keys():
        audio_location_list.append(screen_time_map[key][1])
    return audio_location_list


def remove_location_screen_time_map(screen_time_map):
    for key in list(screen_time_map.keys()):
        screen_time_map[key] = screen_time_map[key][0]
    return screen_time_map


def create_audio_map(QuestionsList):
    screen_time_map = dict()

    screen_time_map = get_intro_static_audio(screen_time_map)
    questionNumber = 0
    for question in QuestionsList:
        questionNumber += 1
        timer = int(question.Timer)
        screenkey = 'question_'+str(questionNumber) + '_' + question.QuestionId
        screen_time_map = attach_blank(screen_time_map, screenkey, timer)
        screen_time_map = attach_bell(screen_time_map)
    return screen_time_map


def audio_controller():
    QuestionsList = []
    for question in questionJson:
        obj = Question.get_question_to_object(question)
        QuestionsList.append(obj)

    screen_time_map = create_audio_map(QuestionsList)
    audio_location_list = get_list_audio_concat(screen_time_map)
    [print(i) for i in audio_location_list]
    concat_audios(audio_location_list, AUDIO_LOCATION_DYNAMIC_NORMAL + MAIN_AUDIO_WITHOUT_MUSIC)
    screen_time_map = remove_location_screen_time_map(screen_time_map)
    return screen_time_map, QuestionsList


def set_static_commands():
    assistant_speaks(screen_1, AUDIO_LOCATION_STATIC_FEMALE+'screen_1.mp3')
    assistant_speaks(screen_2, AUDIO_LOCATION_STATIC_FEMALE + 'screen_2.mp3')
    assistant_speaks("ding dong!", AUDIO_LOCATION_STATIC_FEMALE + 'bell.mp3')
    for i in range(1, 51):
        create_blank_audio(AUDIO_LOCATION_BLANK, i)


# if __name__ == '__main__':
#     screen_time_map, QuestionList = audio_controller()
#     print(screen_time_map)