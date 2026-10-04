"""Shape fallback from the game's TAP art, with independent prompt evidence."""
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np


@lru_cache(maxsize=1)
def tap_templates():
    path = Path(__file__).resolve().parent/'assets'/'vision'/'tap_letters.png'
    template = cv2.imdecode(np.fromfile(path,np.uint8),cv2.IMREAD_GRAYSCALE) if path.is_file() else None
    if template is None:
        return ()
    # analyze() normalizes to 900px; smaller inputs keep the same proportions.
    return template


def tap_art_prompt(hsv, w, h):
    """A shape match is insufficient alone: require outline and a ! below it.

    This fallback tolerates a dark/low-saturation pink badge while preserving
    the actual shared-language TAP letter geometry. It never clicks by colour.
    """
    template = tap_templates()
    if not isinstance(template,np.ndarray):
        return False,0.
    x0,x1,y0,y1 = int(.34*w),int(.66*w),int(.28*h),int(.68*h)
    roi = hsv[y0:y1,x0:x1]
    white = cv2.inRange(roi,np.array((0,0,175)),np.array((179,85,255)))
    yellow = cv2.inRange(roi,np.array((20,35,150)),np.array((40,255,255)))
    letters = cv2.bitwise_or(white,yellow)
    # Skip expensive matching on an empty waiting scene.
    if cv2.countNonZero(letters) < .001*w*h:
        return False,0.
    best = (0.,None)
    for fraction in (.13,.15,.17,.19,.21,.23,.25,.27,.29):
        tw = max(8,round(fraction*w))
        th = max(4,round(tw*template.shape[0]/template.shape[1]))
        if tw > letters.shape[1] or th > letters.shape[0]:
            continue
        resized = cv2.resize(template,(tw,th),interpolation=cv2.INTER_AREA)
        scores = cv2.matchTemplate(letters,resized,cv2.TM_CCOEFF_NORMED)
        _,score,_,location = cv2.minMaxLoc(scores)
        if np.isfinite(score) and score > best[0]:
            best = (score,(location[0]+x0,location[1]+y0,tw,th))
    score,position = best
    if score < .72 or position is None:
        return False,score
    tx,ty,tw,th = position
    # The blue outline must remain immediately around the matched letter art.
    border = hsv[max(0,ty-round(.25*th)):min(h,ty+round(1.25*th)),
                 max(0,tx-round(.06*tw)):min(w,tx+round(1.06*tw))]
    blue = cv2.inRange(border,np.array((105,80,80)),np.array((132,255,255)))
    if cv2.countNonZero(blue) < .10*tw*th:
        return False,score
    # Exclamation stem + dot below the centre of TAP; unrelated TAP text in
    # tutorial/menu artwork cannot start a round without this second feature.
    from bot_vision import components
    bx0,bx1 = max(0,round(tx+.32*tw)),min(w,round(tx+.65*tw))
    by0,by1 = min(h,ty+th),min(h,round(ty+4*th))
    badge = hsv[by0:by1,bx0:bx1]
    marks = components(cv2.inRange(badge,np.array((0,0,175)),np.array((179,85,255))))
    stems = [m for m in marks if .24*th < m['h'] < .9*th and .07*th < m['w'] < .40*th]
    dots = [m for m in marks if .08*th < m['h'] < .40*th and .08*th < m['w'] < .40*th]
    confirmed = any(.20*th < dot['cy']-stem['cy'] < 1.1*th
                    and abs(dot['cx']-stem['cx']) < .18*th
                    for stem in stems for dot in dots)
    return confirmed,score
