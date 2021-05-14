import cv2
from VideoConstants import *


def get_photo_frame(img, frame, flag):

    x1, y1 = DIMENSION_DICT[flag]

    # rows, cols, chl = frame.shape
    # alpha = 0.1
    # added_image = cv2.addWeighted(frame[x1:rows + x1, y1:cols + y1, :], alpha, img[0:rows, 0:cols:], 1 - alpha, 0)

    # if flag == 2:
    #     x1 = vc.phone2_pos_x
    # elif flag == 3:
    #     x1,y1 = vc.slate_position1
    # elif flag ==4:
    #     x1,y1 = vc.slate_position2
    # elif flag == 5: # position for initial phone1 pos
    #     x1, y1 = vc.phone1_pos_initial_x, vc.phone1_pos_initial_y
    # elif flag == 6: # position for initial phone2 pos
    #     x1, y1 = vc.phone2_pos_initial_x, vc.phone2_pos_initial_y
    # elif flag == 7: # position for initial phone1 back pos
    #     x1, y1 = vc.phone1_pos_initial_back_x, vc.phone1_pos_initial_back_y
    # elif flag == 8: # position for initial phone2 back pos
    #     x1, y1 = vc.phone2_pos_initial_back_x, vc.phone2_pos_initial_back_y
    # elif flag == 9:
    #     x1, y1 = vc.logo_pos_x_temp, vc.logo_pos_y_temp
    # elif flag == 10:
    #     x1, y1 = vc.trans_pos_x, vc.trans_pos_y
    # elif flag == 11:
    #     x1, y1 = vc.card_pos_x, vc.card_pos_y

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    th, threshed = cv2.threshold(gray, THRES, MAXVAL, cv2.THRESH_BINARY_INV)

    ## (2) Morph-op to remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    morphed = cv2.morphologyEx(threshed, cv2.MORPH_CLOSE, kernel)

    ## (3) Find the max-area contour
    cnts = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    cnt = sorted(cnts, key=cv2.contourArea)[-1]

    ## (4) Crop and save it
    x, y, w, h = cv2.boundingRect(cnt)
    dst = img[y:y + h, x:x + w]
    # print(x, y, w, h)
    frame[y + y1:y + h + y1, x + x1:x + x1 + w] = dst
    # frame[x1:rows + x1, y1:cols + y1] = added_image
    return frame


def resize_image(img, height, width):
    # width = int(img.shape[1] * scale_percent / 100)
    # height = int(img.shape[0] * scale_percent / 100)
    try:
        dim = (width, height)
        # resize image
        resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
        return resized
    except:
        return None