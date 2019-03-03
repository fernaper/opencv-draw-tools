# MIT License
# Copyright (c) 2019 Fernando Perez
import numpy as np
import sys
import cv2

"""
    You can change it.
    If IGNORE_ERRORS are True, opencv_draw_tools tried to solve the problems or
    conflictive cases by himself.
    Recommended: False
"""
IGNORE_ERRORS = False

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def get_lighter_color(color):
    """Generates a lighter color.

    Keyword arguments:
    color -- color you want to change, touple with 3 elements BGR
             BGR = Blue - Green - Red
    Return:
    Return a lighter version of the provided color

    """
    add = 255 - max(color)
    add = min(add,30)
    return (color[0] + add, color[1] + add, color[2] + add)

def add_tags(frame, position, tags, tag_position=None, alpha=0.75, color=(20, 20, 20),
             margin=5, font_info=(cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.75, (255,255,255), 1)):
    """Add tags to selected zone.

    It was originally intended as an auxiliary method to add details to the select_zone()
    method, however it can be used completely independently.

    Keyword arguments:
    frame -- opencv frame object where you want to draw
    position -- touple with 4 elements (x1, y1, x2, y2)
                This elements must be between 0 and 1 in case it is normalized
                or between 0 and frame height/width.
    tags -- list of strings/tags you want to associate to the selected zone
    tag_position -- position where you want to add the tags, relatively to the selected zone (default None)
                    If None provided it will auto select the zone where it fits better:
                        - First try to put the text on the Bottom Rigth corner
                        - If it doesn't fit, try to put the text on the Bottom Left corner
                        - If it doesn't fit, try to put the text Inside the rectangle
                        - Finally if it doesn't fit, try to put the text On top of the rectangle
    alpha -- transparency of the tags background on the image (default 0.75)
             1 means totally visible and 0 totally invisible
    color -- color of the tags background, touple with 3 elements BGR (default (20,20,20) -> almost black)
             BGR = Blue - Green - Red
    margin -- extra margin in pixels to be separeted with the selected zone (default 5)
    font_info -- touple with 4 elements (font, font_scale, font_color, thickness)
                 font -- opencv font (default cv2.FONT_HARSHEY_COMPLEX_SMALL)
                 font_scale -- scale of the fontm between 0 and 1 (default 0.75)
                 font_color -- color of the tags text, touple with 3 elements BGR (default (255,255,255) -> white)
                          BGR = Blue - Green - Red
                 thickness -- thickness of the text in pixels (default 1)

    Return:
    A new drawed Frame

    """
    f_height, f_width = frame.shape[:2]
    font, font_scale, font_color, thickness = font_info
    x1, y1, x2, y2 = position

    aux_tags = []
    for tag in tags:
        line = [x+'\n' for x in tag.split('\n')]
        line[0] = line[0][:-1]
        for element in line:
            aux_tags.append(element)
    tags = aux_tags

    text_width = -1
    text_height = -1
    line_height = -1
    for tag in tags:
        size = cv2.getTextSize(tag, font, font_scale, thickness)
        text_width = max(text_width,size[0][0])
        text_height = max(text_height, size[0][1])
        line_height = max(line_height, text_height + size[1] + margin)

    '''
        If not tags position are provided:
            - First try to put the text on the Bottom Rigth corner
            - If it doesn't fit, try to put the text on the Bottom Left corner
            - If it doesn't fit, try to put the text Inside the rectangle
            - If it doesn't fit, try to put the text On top of the rectangle
    '''
    if not tag_position:
        fits_right = x2 + text_width + margin*3 <= f_width
        fits_left = x1 - (text_width + margin*3) >= 0
        fits_below = (text_height + margin)*len(tags) - margin <= y2 - thickness
        fits_inside = x1 + text_width + margin*3 <= x2 - thickness and \
                      y1 + (margin*2 + text_height)*len(tags) + text_height - margin <= y2 - thickness

        if fits_right and fits_below:
            tag_position = 'bottom_right'
        elif fits_left and fits_below:
            tag_position = 'bottom_left'
        elif fits_inside:
            tag_position = 'inside'
        else:
            tag_position = 'top'
    else:
        valid = ['bottom_right', 'bottom_left', 'inside', 'top']
        if tag_position not in ['bottom_right', 'bottom_left', 'inside', 'top']:
            if not IGNORE_ERRORS:
                raise ValueError('Error, invalid tag_position ({}) must be in: {}'.format(tag_position, valid))
            else:
                tag_position = 'bottom_right'

    # Add triangle to know to whom each tag belongs
    if tag_position == 'bottom_right':
        pt1 = (x2 + margin - 1, y2 - (margin*2 + text_height)*len(tags) - text_height - margin)
        pt2 = (pt1[0], pt1[1] + text_height + margin*2)
        pt3 = (pt1[0] - margin + 1, pt1[1] + int(text_height/2)+margin)
    elif tag_position == 'bottom_left':
        pt1 = (x1 - margin + 1, y2 - (margin*2 + text_height)*len(tags) - text_height - margin)
        pt2 = (pt1[0], pt1[1] + text_height + margin*2)
        pt3 = (pt1[0] + margin - 1, pt1[1] + int(text_height/2)+margin)
    elif tag_position == 'top':
        pt1 = (x1 + margin + int(text_width/3), y1 - margin*2 + 1)
        pt2 = (pt1[0] + int(text_width/3) + margin*2, pt1[1])
        pt3 = (int((pt1[0] + pt2[0])/2), pt1[1] + margin*2 - 1)

    if tag_position != 'inside':
        overlay = frame.copy()
        cv2.drawContours(overlay, [np.array([pt1, pt2, pt3])], 0, color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)

    overlay = frame.copy()
    for i, tag in enumerate(tags):
        reverse_i = len(tags) - i
        extra_adjustment = 2 if tag[-1] == '\n' else 1
        if tag_position == 'top':
            cv2.rectangle(overlay, (x1 + margin, y1 - (margin + text_height)*reverse_i - margin * (reverse_i-1) - text_height - margin * (extra_adjustment - 1 )),
                          (x1 + text_width + margin*3, y1 - (margin + text_height)*reverse_i - margin * (reverse_i) + text_height), color,-1)
        elif tag_position == 'inside':
            cv2.rectangle(overlay, (x1 + margin, y1 + (margin*2 + text_height)*(i+1) - text_height - margin - extra_adjustment),
                          (x1 + text_width + margin*3, y1 + (margin*2 + text_height)*(i+1) + text_height - margin), color,-1)
        elif tag_position == 'bottom_left':
            cv2.rectangle(overlay, (x1 - (text_width + margin*3), y2 - (margin*2 + text_height)*reverse_i - text_height - margin * extra_adjustment),
                          (x1 - margin, y2 - (margin*2 + text_height)*reverse_i + text_height - margin), color,-1)
        elif tag_position == 'bottom_right':
            cv2.rectangle(overlay, (x2 + margin, y2 - (margin*2 + text_height)*reverse_i - text_height - margin * extra_adjustment),
                          (x2 + text_width + margin*3, y2 - (margin*2 + text_height)*reverse_i + text_height - margin), color,-1)
        if tag_position != 'top':
            y1 += margin
            y2 += margin
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    x1, y1, x2, y2 = position
    for i, tag in enumerate(tags):
        reverse_i = len(tags) - i
        extra_adjustment = int(margin*( 0.5 if tag[-1] == '\n' else 0))
        if tag_position == 'top':
            cv2.putText(frame, tag.replace('\n',''),
                        (x1 + margin*2, y1 - (margin + text_height)*reverse_i - margin * (reverse_i-1) + int(margin/2) - extra_adjustment),
                        font, font_scale, font_color, thickness)
        elif tag_position == 'inside':
            cv2.putText(frame, tag.replace('\n',''),
                        (x1 + margin*2, y1 + (margin*2 + text_height)*(i+1) - extra_adjustment),
                        font, font_scale, font_color, thickness)
        elif tag_position == 'bottom_left':
            cv2.putText(frame, tag.replace('\n',''),
                        (x1 - (text_width + margin*2), y2 - (margin*2 + text_height)*reverse_i - extra_adjustment),
                        font, font_scale, font_color, thickness)
        elif tag_position == 'bottom_right':
            cv2.putText(frame, tag.replace('\n',''),
                        (x2 + margin*2, y2 - (margin*2 + text_height)*reverse_i - extra_adjustment),
                        font, font_scale, font_color, thickness)
        if tag_position != 'top':
            y1 += margin
            y2 += margin

    return frame

def add_peephole(frame, position, alpha=0.5, color=(110,70,45), thickness=2, line_length=7, corners=True):
    """Add peephole effect to the select_zone.

    It was originally intended as an auxiliary method to add details to the select_zone()
    method, however it can be used completely independently.

    Keyword arguments:
    frame -- opencv frame object where you want to draw
    position -- touple with 4 elements (x1, y1, x2, y2)
                This elements must be between 0 and 1 in case it is normalized
                or between 0 and frame height/width.
                Outer rectangle on which the peephole is drawn.
    alpha -- transparency of the selected zone on the image (default 0.5)
             1 means totally visible and 0 totally invisible
    color -- color of the selected zone, touple with 3 elements BGR (default (110,70,45) -> dark blue)
             BGR = Blue - Green - Red
    normalized -- boolean parameter, if True, position provided normalized (between 0 and 1)
                  else you shold provide concrete values (default False)
    thickness -- thickness of the drawing in pixels (default 2)
    corners -- boolean parameter, if True, also draw the corners of the rectangle

    Return:
    A new drawed Frame

    """
    x1, y1, x2, y2 = position
    # Min value of thickness = 2
    thickness = min(thickness,2)
    # If the selected zone is too small don't draw
    if x2 - x1 > thickness*2 + line_length  and y2 - y1 > thickness*2 + line_length:
        overlay = frame.copy()
        if corners:
            # Draw horizontal lines of the corners
            cv2.line(overlay,(x1, y1),(x1 + line_length, y1), color, thickness+1)
            cv2.line(overlay,(x2, y1),(x2 - line_length, y1), color, thickness+1)
            cv2.line(overlay,(x1, y2),(x1 + line_length, y2), color, thickness+1)
            cv2.line(overlay,(x2, y2),(x2 - line_length, y2), color, thickness+1)
            # Draw vertical lines of the corners
            cv2.line(overlay,(x1, y1),(x1, y1 + line_length), color, thickness+1)
            cv2.line(overlay,(x1, y2),(x1, y2 - line_length), color, thickness+1)
            cv2.line(overlay,(x2, y1),(x2, y1 + line_length), color, thickness+1)
            cv2.line(overlay,(x2, y2),(x2, y2 - line_length), color, thickness+1)
        # Added extra lines that gives the peephole effect
        cv2.line(overlay,(x1, int((y1 + y2) / 2)),(x1 + line_length, int((y1 + y2) / 2)), color, thickness-1)
        cv2.line(overlay,(x2, int((y1 + y2) / 2)),(x2 - line_length, int((y1 + y2) / 2)), color, thickness-1)
        cv2.line(overlay,(int((x1 + x2) / 2), y1),(int((x1 + x2) / 2), y1 + line_length), color, thickness-1)
        cv2.line(overlay,(int((x1 + x2) / 2), y2),(int((x1 + x2) / 2), y2 - line_length), color, thickness-1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    return frame

def adjust_position(shape, position, normalized=False, thickness=0):
    """Auxiliar Method: Adjust provided position to select_zone.

    Keyword arguments:
    shape -- touple with 2 elements (height, width)
             this information should be the height and width of the frame.
    position -- touple with 4 elements (x1, y1, x2, y2)
                This elements must be between 0 and 1 in case it is normalized
                or between 0 and frame height/width.
    normalized -- boolean parameter, if True, position provided normalized (between 0 and 1)
                  else you shold provide concrete values (default False)
    thickness -- thickness of the drawing in pixels (default 0)

    Return:
    A new position with all the adjustments

    """
    f_height, f_width = shape
    x1, y1, x2, y2 = position
    if normalized:
        x1 *= f_width
        x2 *= f_width
        y1 *= f_height
        y2 *= f_height

    if x1 < 0 or x1 > f_width:
        if not IGNORE_ERRORS:
            raise ValueError('Error: x1 = {}; Value must be between {} and {}. If normalized between 0 and 1.'.format(x1, 0, f_width))
        else:
            x1 = min(max(x1,0),f_width)
    if x2 < 0 or x2 > f_width:
        if not IGNORE_ERRORS:
            raise ValueError('Error: x2 = {}; Value must be between {} and {}. If normalized between 0 and 1.'.format(x2, 0, f_width))
        else:
            x2 = min(max(x2,0),f_width)
    if y1 < 0 or y1 > f_height:
        if not IGNORE_ERRORS:
            raise ValueError('Error: y1 = {}; Value must be between {} and {}. If normalized between 0 and 1.'.format(y1, 0, f_height))
        else:
            y1 = min(max(y1,0),f_height)
    if y2 < 0 or y2 > f_height:
        if not IGNORE_ERRORS:
            raise ValueError('Error: y2 = {}; Value must be between {} and {}. If normalized between 0 and 1.'.format(y2, 0, f_height))
        else:
            y2 = min(max(y2,0),f_height)
    # Auto adjust the limits of the selected zone
    x2 = int(min(max(x2, thickness*2), f_width - thickness))
    y2 = int(min(max(y2, thickness*2), f_height - thickness))
    x1 = int(min(max(x1, thickness), x2 - thickness))
    y1 = int(min(max(y1, thickness), y2 - thickness))
    return (x1, y1, x2, y2)

def select_zone(frame, position, tags=[], tag_position=None, alpha=0.9, color=(110,70,45),
                normalized=False, thickness=2, filled=False, peephole=True):
    """Draw better rectangles to select zones.

    Keyword arguments:
    frame -- opencv frame object where you want to draw
    position -- touple with 4 elements (x1, y1, x2, y2)
                This elements must be between 0 and 1 in case it is normalized
                or between 0 and frame height/width.
    tags -- list of strings/tags you want to associate to the selected zone (default [])
    tag_position -- position where you want to add the tags, relatively to the selected zone (default None)
                    If None provided it will auto select the zone where it fits better:
                        - First try to put the text on the Bottom Rigth corner
                        - If it doesn't fit, try to put the text on the Bottom Left corner
                        - If it doesn't fit, try to put the text Inside the rectangle
                        - Finally if it doesn't fit, try to put the text On top of the rectangle
    alpha -- transparency of the selected zone on the image (default 0.9)
             1 means totally visible and 0 totally invisible
    color -- color of the selected zone, touple with 3 elements BGR (default (110,70,45) -> dark blue)
             BGR = Blue - Green - Red
    normalized -- boolean parameter, if True, position provided normalized (between 0 and 1)
                  else you should provide concrete values (default False)
    thickness -- thickness of the drawing in pixels (default 2)
    filled -- boolean parameter, if True, will draw a filled rectangle with one-third opacity compared to the rectangle (default False)
    peephole -- boolean parameter, if True, also draw additional effect, so it looks like a peephole

    Return:
    A new drawed Frame

    """
    x1, y1, x2, y2 = position = adjust_position(frame.shape[:2], position, normalized=normalized, thickness=thickness)
    if peephole:
        frame = add_peephole(frame, position, alpha=alpha, color=color)

    if filled:
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color,thickness=cv2.FILLED)
        cv2.addWeighted(overlay, alpha/3.0, frame, 1 - alpha/3.0, 0, frame)

    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color,thickness=thickness)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    frame = add_tags(frame, position, tags, tag_position=tag_position)
    return frame

def webcam_test():
    """Reproduce Webcam in real time with a selected zone."""
    print('Launching webcam test')
    cap = cv2.VideoCapture(0)
    f_width = cap.get(3)
    f_height = cap.get(4)
    window_name = 'opencv_draw_tools'
    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)
        if ret:
            keystroke = cv2.waitKey(1)
            position = (0.33,0.2,0.66,0.8)
            tags = ['MIT License', '(C) Copyright\n    Fernando\n    Perez\n    Gutierrez']
            frame = select_zone(frame, position, tags=tags, color=(14,28,200),
                                thickness=2, filled=True, normalized=True)
            cv2.imshow(window_name, frame)
            # True if escape 'esc' is pressed
            if keystroke == 27:
                break
    cv2.destroyAllWindows()
    cv2.VideoCapture(0).release()

def get_complete_help():
    return '''
    Public methods information:

    * select_zone:
    {}

    * add_peephole:
    {}

    * add_tags:
    {}

    * get_lighter_color:
    {}

    Auxiliar methods information:

    * adjust_position:
    {}

    Testing methods information:

    * webcam_test:
    {}

    '''.format(select_zone.__doc__, add_peephole.__doc__,
               add_tags.__doc__, get_lighter_color.__doc__, adjust_position.__doc__,
               webcam_test.__doc__)

if __name__ == '__main__':
    webcam_test()
