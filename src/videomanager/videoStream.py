from src.audiomanager.AudioStream import *
from src.audiomanager.AudioText import *
from src.datamanager.QuestionModel import *
from VideoConstants import *
from photoFrameUtils import *
from videoUtils import *
import cv2


def get_avatar_stock_images():
    avatar_images_dict = dict()

    for i in range(1, 13):
        key = 'avatar_' + str(i)
        avatar_images_dict[key] = resize_image(cv2.imread(AVATAR_LOCATION+key+'.png'),
                                               AVATAR_HEIGHT, AVATAR_WIDTH)
    return avatar_images_dict


def render_video(cap, cap_avatar, out, QuestionList, screen_time_map, avatar_dict):
    print("Rendering video:")
    if cap == None or out == None or QuestionList == None or screen_time_map == None or avatar_dict == dict():
        print("Something is None in render Video")
        return
    screen_time_map_keys = list(screen_time_map.keys())
    time_per_screen = list(screen_time_map.values())
    detail_per_second = time_per_screen[0] * FRAME_RATE

    keyCount = 0
    count = 0.0
    video_time = int(get_audio_duration(MAIN_AUDIO))
    current_screen_type = screen_time_map_keys[keyCount].split('_')[0]
    current_screen_type_count = screen_time_map_keys[keyCount].split('_')[1].replace('.mp3','')

    #avatar
    avatar_video_length = get_video_length(AVATAR_VIDEO)

    # timer
    timer = int(QuestionList[int(current_screen_type_count)-1].Timer)
    timer_count = 0
    timer_img = resize_image(cv2.imread(TIMER1_PHOTO), TIMER_SIZE_X, TIMER_SIZE_Y)

    # font initialise
    screeft = cv2.freetype.createFreeType2()
    timerft = cv2.freetype.createFreeType2()
    questionft = cv2.freetype.createFreeType2()
    screeft.loadFontData(fontFileName=FONT_RALEWAY_MED, id=0)
    timerft.loadFontData(fontFileName=FONT_UBUNTU_R, id=0)
    questionft.loadFontData(fontFileName=FONT_UBUNTU_R, id=0)

    while True:
        ret, frame = cap.read()
        # add video content here
        if current_screen_type == "screen":
            ret_ava, frame_ava = cap_avatar.read()
            frame = get_photo_frame(frame_ava, frame, "avatar")
            if cap_avatar.get(cv2.CAP_PROP_POS_FRAMES) + 1 >= FRAME_RATE * avatar_video_length:
                cap_avatar = cv2.VideoCapture(AVATAR_VIDEO)

            if current_screen_type_count == '1':
                screen_text = screen_1.split('.')
                screeft.putText(frame, screen_text[0], (100, 100), 25, (0, 0, 0), -1, cv2.LINE_AA, True)
                screeft.putText(frame, screen_text[1], (100, 200), 25, (0, 0, 0), -1, cv2.LINE_AA, True)
                screeft.putText(frame, screen_text[2], (100, 250), 25, (0, 0, 70), -1, cv2.LINE_AA, True)

            elif current_screen_type_count == '2':
                screen_text = screen_2.split('.')
                screeft.putText(frame, screen_text[0], (100, 100), 25, (0, 0, 0), -1, cv2.LINE_AA, True)
                screeft.putText(frame, screen_text[1], (100, 200), 25, (0, 0, 0), -1, cv2.LINE_AA, True)
                screeft.putText(frame, screen_text[2], (100, 250), 25, (78, 56, 100), -1, cv2.LINE_AA, True)
        if current_screen_type == "question":
            if (timer < 0):
                timer = 0
            frame = get_photo_frame(timer_img, frame, "timer")
            timerft.putText(frame, str(timer), TIMER_TEXT_POSITION, TIMER_TEXT_SIZE, TIMER_TEXT_COLOR, -1, cv2.LINE_AA, True)

            question = QuestionList[int(current_screen_type_count)-1]
            questionft.putText(frame, question.QuestionText, (200, 300), 25, (0, 0, 0), -1, cv2.LINE_AA, True)
            questionft.putText(frame, "QUESTION NO: " + question.QuestionNumber, (100, 100), 25, (0, 0, 255), -1, cv2.LINE_AA, True)
            questionft.putText(frame, "A: " + question.Options['A'], (200, 500), 25, (0, 0, 255), -1,
                               cv2.LINE_AA, True)
            questionft.putText(frame, "B: " + question.Options['B'], (600, 500), 25, (0, 0, 255), -1,
                               cv2.LINE_AA, True)
            questionft.putText(frame, "C: " + question.Options['C'], (200, 600), 25, (0, 0, 255), -1,
                               cv2.LINE_AA, True)
            questionft.putText(frame, "D: " + question.Options['D'], (600, 600), 25, (0, 0, 255), -1,
                               cv2.LINE_AA, True)
            timer_count += 1
            if timer_count == FRAME_RATE:
                timer -= 1
                timer_count = 0


        if keyCount < len(screen_time_map_keys) - 1 and count > detail_per_second:
            keyCount += 1
            current_screen_type = screen_time_map_keys[keyCount].split('_')[0]
            current_screen_type_count = screen_time_map_keys[keyCount].split('_')[1].replace('.mp3','')
            count = 0.0
            detail_per_second = time_per_screen[keyCount]*FRAME_RATE
            if "bell" not in screen_time_map_keys[keyCount]:
                timer = int(QuestionList[int(current_screen_type_count)-1].Timer)
                timer_count = 0
            print(current_screen_type, current_screen_type_count)
        count += 1.0

        # write to video
        out.write(frame)
        cv2.imshow('frame', frame)

        # stop and conclude the video
        # print(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if cap.get(cv2.CAP_PROP_POS_FRAMES) + 1 >= FRAME_RATE * video_time or cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    out.release()
    cv2.destroyAllWindows()

def create_video(screen_time_map, QuestionList):
    avatar_dict = get_avatar_stock_images()
    cap_backgroud = cv2.VideoCapture(BLANK_WHITE_VIDEO)
    cap_avatar = cv2.VideoCapture(AVATAR_VIDEO)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_filename = VIDEO_LOCATION_RENDERED + 'test1' + OUTPUT_VIDEO_FORMAT

    out = cv2.VideoWriter(output_filename, fourcc, FRAME_RATE, OUTPUT_VIDEO_DIMENSIONS)

    render_video(cap_backgroud, cap_avatar, out, QuestionList, screen_time_map, avatar_dict)
    print(output_filename)
    output_filename_music = add_audio_to_video(output_filename)
    # import Document as dc
    # try:
    #     dc.save_document(VIDEO_LOCATION_RENDERED, output_file_name_music.split('/')[-1])
    # except Exception as e:
    #     print("exception=", e)
    #     pass


def main_video_operator():
    screen_time_map, QuestionList = audio_controller()

    print(screen_time_map)
    create_video(screen_time_map, QuestionList)



if __name__ == '__main__':
    main_video_operator()

# {'screen_1.mp3': 23.568, 'screen_2.mp3': 19.464, 'question_1_A101_blank_5.mp3': 5.0416326530612245,
#  'question_1_A101_blank_5.mp3_bell': 1.2, 'question_2_A102_blank_5.mp3': 5.0416326530612245,
#  'question_2_A102_blank_5.mp3_bell': 1.2, 'question_3_A103_blank_8.mp3': 8.045714285714286,
#  'question_3_A103_blank_8.mp3_bell': 1.2}