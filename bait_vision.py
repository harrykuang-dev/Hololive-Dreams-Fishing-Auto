"""Bait dialog evidence from artwork and geometry, without localized text."""
from dataclasses import dataclass
import cv2
import numpy as np


@dataclass
class BaitObservation:
    result: bool = False
    exhausted: bool = False
    dim_continue: bool = False
    change_point: tuple | None = None
    continue_point: tuple | None = None
    continue_visible: bool = False
    dialog: bool = False
    infinite_point: tuple | None = None
    selected_infinite: bool = False
    confirm_point: tuple | None = None


def observe_bait(frame, detection):
    h0, w0 = frame.shape[:2]
    scale = min(1., 900/w0)
    f = cv2.resize(frame, (round(w0*scale), round(h0*scale)), interpolation=cv2.INTER_AREA) if scale < 1 else frame
    h, w = f.shape[:2]
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    white = cv2.inRange(hsv, (0, 0, 205), (179, 55, 255))
    # The dialog can use a different theme from the result card. Preserve
    # saturated and neutral ink; never match a particular character hue.
    ink = cv2.inRange(hsv, (0, 25, 55), (179, 255, 255)) | cv2.inRange(hsv, (0, 0, 30), (179, 24, 140))
    orange = cv2.inRange(hsv, (10, 80, 145), (40, 255, 255))

    def patch(mask, rect):
        x1,y1,x2,y2 = rect
        return mask[round(y1*h):round(y2*h), round(x1*w):round(x2*w)]

    def fraction(mask, rect):
        p = patch(mask, rect)
        return np.count_nonzero(p)/max(p.size, 1)

    def pill(rect):
        x1,y1,_,_ = rect
        p = cv2.morphologyEx(patch(white, rect), cv2.MORPH_CLOSE, np.ones((3,3), np.uint8))
        contours, _ = cv2.findContours(p, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x,y,cw,ch = cv2.boundingRect(c)
            if .11*w < cw < .20*w and .045*h < ch < .095*h and 2.8 < cw/ch < 5.2 and cv2.contourArea(c) > .65*cw*ch:
                return ((round(x1*w)+x+cw/2)/scale, (round(y1*h)+y+ch/2)/scale)
        return None

    o = BaitObservation(result=detection.catch_result,
                        dim_continue=False)
    if o.result:
        bright = cv2.inRange(hsv, (0,0,235), (179,55,255))
        point = detection.action_button
        o.continue_point = point
        o.continue_visible = bool(point and detection.confidence >= .9)
        if point:
            cx,cy = point[0]/w0, point[1]/h0
            o.dim_continue = bool(fraction(bright, (cx-.035,cy-.018,cx+.035,cy+.018)) < .06)
        else:
            o.dim_continue = True
        red = cv2.inRange(hsv, (0, 140, 145), (12, 255, 255)) | cv2.inRange(hsv, (170, 140, 145), (179, 255, 255))
        rect = (.43,.85,.54,.96)
        contours, _ = cv2.findContours(patch(red,rect), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x,y,cw,ch = cv2.boundingRect(c)
            if .018*w < cw < .04*w and .025*h < ch < .065*h and .7 < cw/ch < 1.5:
                x += round(rect[0]*w); y += round(rect[1]*h)
                inner = white[y+round(ch*.2):y+round(ch*.85), x+round(cw*.35):x+round(cw*.65)]
                area = cv2.contourArea(c)/max(cw*ch,1)
                triangle = len(cv2.approxPolyDP(c, .05*cv2.arcLength(c, True), True)) == 3
                if triangle and .25 < area < .8 and np.count_nonzero(inner) > inner.size*.18:
                    o.exhausted = True
        o.change_point = pill((.015,.85,.21,.97))

    # The recorded bait dialog uses a blue header with a purple park theme.
    # Its first dough icon and infinity quantity distinguish it from item detail.
    header = fraction(ink, (.20,.115,.75,.16)) > .80
    panel = fraction(white, (.58,.19,.78,.40)) > .60
    dough = fraction(orange, (.21,.23,.285,.36)) > .25
    infinity = False
    p = patch(ink, (.22,.375,.29,.42))
    contours, hierarchy = cv2.findContours(p, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is not None:
        for i,c in enumerate(contours):
            _,_,cw,ch = cv2.boundingRect(c)
            if .007*w < cw < .022*w and .004*h < ch < .017*h and 1.4 < cw/ch < 3.3 and .25 < cv2.contourArea(c)/max(cw*ch,1) < .85:
                infinity = True
    o.dialog = bool(header and panel and dough and infinity)
    if o.dialog:
        o.infinite_point = (.247*w0, .30*h0)
        corners = ((.201,.227,.219,.252),(.272,.227,.293,.252),
                   (.201,.34,.219,.38),(.272,.34,.293,.38))
        selected = all(fraction(ink, r) > .18 for r in corners)
        preview = fraction(orange, (.64,.245,.74,.40)) > .42
        o.selected_infinite = bool(selected and preview)
        # An enabled themed confirm pill and its white border must both be visible.
        if fraction(ink, (.84,.90,.93,.94)) > .40:
            o.confirm_point = pill((.79,.865,.985,.98))
            if o.confirm_point is None and fraction(white, (.84,.90,.93,.94)) > .04:
                # Small-window antialiasing can break the white pill outline.
                # The full dialog, first-cell infinity and confirm glyphs still
                # establish the prefab's bottom-right confirmation anchor.
                o.confirm_point = (.886*w0, .915*h0)
    return o
