"""Track-local colour/geometry vision, independent of Windows input."""
from dataclasses import dataclass
import cv2
import numpy as np


@dataclass
class Detection:
    tap: bool = False
    tap_pixels: int = 0
    player_center: tuple[float, float] | None = None
    player_box: tuple[int, int, int, int] | None = None
    fish_center: tuple[float, float] | None = None
    fish_box: tuple[int, int, int, int] | None = None
    track_present: bool = False
    track_box: tuple[int, int, int, int] | None = None
    action_button: tuple[float, float] | None = None
    scene: str = 'unknown'
    confidence: float = 0.0

    @property
    def minigame(self):
        return self.track_present and self.player_center is not None and self.fish_center is not None


def components(mask, offset=(0, 0)):
    _, _, stats, centers = cv2.connectedComponentsWithStats(mask)
    return [dict(x=int(s[0]+offset[0]), y=int(s[1]+offset[1]), w=int(s[2]),
                 h=int(s[3]), area=int(s[4]), cx=float(c[0]+offset[0]), cy=float(c[1]+offset[1]))
            for s, c in zip(stats[1:], centers[1:])]


def box(c):
    return c['x'], c['y'], c['w'], c['h']


def close_buttons(cyan, w, h):
    """Require a round ring AND a cyan X, not merely a cyan scenery blob."""
    # Cyan scenery can join the outer ring. Its white circular interior is
    # still a nested contour, so external contours alone miss a real X.
    contours, _ = cv2.findContours(cyan, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    found = []
    for contour in contours:
        x, y, cw, ch = cv2.boundingRect(contour)
        if not (.55*w < x < .99*w and .015*h < y < .55*h
                and .022*w < cw < .065*w and .035*h < ch < .12*h
                and .8 < cw/ch < 1.25):
            continue
        perimeter = cv2.arcLength(contour, True)
        if 4*np.pi*cv2.contourArea(contour)/max(perimeter**2, 1) < .68:
            continue
        patch = cyan[y:y+ch, x:x+cw]
        # Include enough white corners for both outer and inner ring bounds;
        # too small a crop makes a thick X look like a filled cyan square.
        inner = cv2.resize(patch[int(ch*.22):int(ch*.78), int(cw*.22):int(cw*.78)], (21,21)) > 128
        yy, xx = np.indices((21,21))
        diagonal = (abs(xx-yy)<3) | (abs(xx+yy-20)<3)
        if inner[diagonal].mean() > .60 and inner[~diagonal].mean() < .58:
            found.append((x+cw/2, y+ch/2))
    return found


def bottom_action_button(cyan, w, h):
    """Locate the filled bottom-right Continue/Next button, not scenery."""
    bx0, by0 = int(.55*w), int(.82*h)
    mask = cyan[by0:int(.985*h), bx0:int(.98*w)]
    buttons = [c for c in components(mask, (bx0, by0))
               if .10*w<c['w']<.32*w and .038*h<c['h']<.135*h
               and 2.4<c['w']/c['h']<6.5
               and c['area']/(c['w']*c['h'])>.45 and c['cx']>.68*w]
    if not buttons:
        return None
    button = max(buttons, key=lambda c:c['cx'])
    return button['x']+button['w']/2, button['y']+button['h']/2


def _analyze(frame):
    h, w = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    d = Detection()
    # Gold outline is the prerequisite for ALL marker detection. Scenery is
    # never allowed to compete with a marker in a different x-column.
    x0, x1, y0, y1 = int(.60*w), int(.79*w), int(.02*h), int(.94*h)
    roi = hsv[y0:y1, x0:x1]
    gold = cv2.inRange(roi, np.array((10,70,60)), np.array((24,255,255)))
    gold = cv2.morphologyEx(gold, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8))
    tracks = [c for c in components(gold,(x0,y0)) if c['h']>.55*h
              and .035*w<c['w']<.14*w and c['area']>.005*w*h]
    if tracks:
        track = max(tracks, key=lambda c:c['h'])
        d.track_present, d.track_box, d.scene = True, box(track), 'reel'
        tx, ty, tw, th = d.track_box
        # Only the left lane, excluding the adjacent orange progress gauge.
        lx, rx = round(tx+.14*tw), round(tx+.55*tw)
        lane = hsv[ty:ty+th, lx:rx]
        yellow = cv2.inRange(lane, np.array((20,35,175)), np.array((37,255,255)))
        rows = np.flatnonzero((yellow>0).mean(axis=1)>.18)
        if rows.size:
            # Boundaries, not colour centroid: an overlapping fish does not
            # drag the bar's centre toward its visible upper/lower half.
            groups = np.split(rows,np.flatnonzero(np.diff(rows)>.075*h)+1)
            valid = [g for g in groups if .022*h<g[-1]-g[0]+1<.31*h and len(g)>.008*h]
            if valid:
                group = max(valid,key=len)
                top, bottom = int(group[0]),int(group[-1])+1
                d.player_box = (lx,ty+top,rx-lx,bottom-top)
                d.player_center = ((lx+rx)/2,ty+(top+bottom)/2)
        fx0, fx1 = max(0,tx), min(w, round(tx+.68*tw))
        fishmask = cv2.inRange(hsv[ty:ty+th,fx0:fx1],np.array((84,150,165)),np.array((103,255,255)))
        fishmask = cv2.morphologyEx(fishmask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
        fishes = [c for c in components(fishmask,(fx0,ty))
                  if .018*w<c['w']<.075*w and .018*h<c['h']<.09*h
                  and .75<c['w']/c['h']<2.4 and c['area']>.00013*w*h]
        if fishes:
            fish = max(fishes,key=lambda c:c['area'])
            d.fish_box = box(fish)
            d.fish_center = (fish['x']+fish['w']/2,fish['y']+fish['h']/2)
        d.confidence = 1.0 if d.minigame else .4
        return d

    cyan = cv2.inRange(hsv,np.array((84,70,170)),np.array((105,255,255)))
    # Reward strips span the complete screen. Dismiss on blank space below
    # the strip, NEVER on the item icon (that opens item details).
    reward_mask = cv2.inRange(hsv,np.array((75,65,175)),np.array((105,255,255)))
    reward_rows = (reward_mask[int(.23*h):int(.75*h)]>0).mean(axis=1)>.84
    # The strip alone can match a smooth blue ocean during a fade. Require
    # the three aligned light GET letters as independent positive evidence.
    get_visible = False
    if reward_rows.sum()>.15*h:
        for brightness in (238,220,205):
            get_mask = cv2.inRange(hsv[int(.04*h):int(.22*h),int(.40*w):int(.61*w)],
                                  np.array((0,0,brightness)),np.array((180,55,255)))
            letters = [c for c in components(get_mask) if .015*w<c['w']<.05*w
                       and .04*h<c['h']<.10*h and c['area']>.0003*w*h]
            if len(letters)>=3 and max(c['cy'] for c in letters)-min(c['cy'] for c in letters)<.025*h:
                get_visible = True
                break
    closes = close_buttons(cyan,w,h)
    cream = cv2.inRange(hsv,np.array((0,0,215)),np.array((180,65,255)))
    if closes:
        point = max(closes,key=lambda p:p[0])
        # Encyclopedia has paper across both sides; item details have a
        # central white card and an inset X. Ready/waiting also have an X but
        # must NOT be closed (their paper area is small).
        paper_left = (cream[int(.16*h):int(.84*h),int(.06*w):int(.46*w)]>0).mean()
        if point[0]>.91*w and paper_left>.55:
            d.scene, d.action_button, d.confidence = 'encyclopedia',point,.95
            return d
        if .62*w<point[0]<.87*w and .08*h<point[1]<.5*h:
            paper_mid = (cream[int(.30*h):int(.76*h),int(.28*w):int(.69*w)]>0).mean()
            paper_header = (cream[int(.16*h):int(.26*h),int(.28*w):int(.69*w)]>0).mean()
            if paper_mid>.65 or paper_header>.75:
                d.scene,d.action_button,d.confidence = 'item_detail',point,.95
                return d

    button = bottom_action_button(cyan,w,h)
    if reward_rows.sum()>.15*h and get_visible:
        # Fishing materials keep Continue visible. Clicking the old blank
        # point instead can open the fish list underneath the reward strip.
        # Modal close buttons above must still take precedence over Continue.
        if button:
            d.scene, d.action_button = 'reward_continue', button
        else:
            d.scene, d.action_button = 'reward', (.50*w,.87*h)
        d.confidence = .95
        return d

    if reward_rows.sum()>.15*h:
        d.scene = 'overlay_animation'
        return d

    if button:
        d.action_button = button
        d.scene = 'action'
        d.confidence = .9
        return d

    tx0,tx1,ty0,ty1 = int(.40*w),int(.82*w),int(.55*h),int(.93*h)
    tapmask = cv2.inRange(hsv[ty0:ty1,tx0:tx1],np.array((140,100,150)),np.array((170,255,255)))
    badges = [c for c in components(tapmask,(tx0,ty0))
              if .018*w<c['w']<.07*w and .03*h<c['h']<.14*h
              and .6<c['w']/c['h']<1.4 and c['area']>.0003*w*h]
    d.tap_pixels = int(cv2.countNonZero(tapmask))
    if badges:
        d.tap, d.scene, d.confidence = True,'tap',.95
    return d


def analyze(frame):
    """Bound processing cost; report original client coordinates."""
    h,w = frame.shape[:2]
    scale = min(1., 900/w)
    small = cv2.resize(frame,(round(w*scale),round(h*scale)),interpolation=cv2.INTER_AREA) if scale<1 else frame
    d = _analyze(small)
    if scale<1:
        for name in ('player_center','fish_center','action_button'):
            value = getattr(d,name)
            if value:
                setattr(d,name,tuple(v/scale for v in value))
        for name in ('player_box','fish_box','track_box'):
            value = getattr(d,name)
            if value:
                setattr(d,name,tuple(round(v/scale) for v in value))
        d.tap_pixels = round(d.tap_pixels/scale**2)
    return d
