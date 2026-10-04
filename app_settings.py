"""In-memory UI counters and validated global shortcuts."""
import re

NAMED_KEYS = {'ESC':0x1B,'ESCAPE':0x1B,'PAUSE':0x13,'SPACE':0x20,'TAB':0x09,
              'ENTER':0x0D,'BACKSPACE':0x08,'DELETE':0x2E,'INSERT':0x2D,
              'HOME':0x24,'END':0x23,'PAGEUP':0x21,'PAGEDOWN':0x22,
              'LEFT':0x25,'UP':0x26,'RIGHT':0x27,'DOWN':0x28,
              'CAPSLOCK':0x14,'NUMLOCK':0x90,'SCROLLLOCK':0x91,'PRINTSCREEN':0x2C,
              'SEMICOLON':0xBA,'EQUALS':0xBB,'COMMA':0xBC,'MINUS':0xBD,
              'PERIOD':0xBE,'SLASH':0xBF,'BACKTICK':0xC0,'LEFTBRACKET':0xDB,
              'BACKSLASH':0xDC,'RIGHTBRACKET':0xDD,'QUOTE':0xDE}


def parse_stop_hotkey(value):
    parts = value.upper().replace(' ', '').split('+')
    if not parts or any(not p for p in parts):
        raise ValueError('Invalid stop shortcut')
    modifiers = parts[:-1]
    if any(p not in ('CTRL','ALT','SHIFT') for p in modifiers) or len(set(modifiers)) != len(modifiers):
        raise ValueError('Use Ctrl, Alt, Shift plus one key')
    key = parts[-1]
    if re.fullmatch(r'F(?:[1-9]|1[0-9]|2[0-4])',key):
        vk = 0x70+int(key[1:])-1
    elif key in NAMED_KEYS:
        vk = NAMED_KEYS[key]
    elif re.fullmatch('NUM[0-9]',key):
        vk = 0x60+int(key[-1])
    elif len(key)==1 and key.isascii() and key.isalnum():
        vk = ord(key)
    else:
        raise ValueError('Use a supported keyboard key or a Ctrl/Alt/Shift combination')
    mods = tuple({'CTRL':0x11,'ALT':0x12,'SHIFT':0x10}[m] for m in modifiers)
    return mods,vk


def captured_hotkey(keysym,state=0,keycode=0):
    """Convert a Tk/Windows KeyPress to a physical key, not typed characters."""
    if keysym in ('Shift_L','Shift_R','Control_L','Control_R','Alt_L','Alt_R',
                  'Meta_L','Meta_R','Super_L','Super_R','Win_L','Win_R') or state&0x40:
        return None
    if 0x30<=keycode<=0x39 or 0x41<=keycode<=0x5A:
        key = chr(keycode)  # Shift+1 remains Shift+1, not the character '!'.
    elif 0x60<=keycode<=0x69:
        key = f'Num{keycode-0x60}'
    elif keycode in NAMED_KEYS.values():
        key = next(name.title() for name,vk in NAMED_KEYS.items() if vk==keycode)
    else:
        aliases = {'Escape':'Esc','space':'Space','Return':'Enter','KP_Enter':'Enter',
                   'Prior':'PageUp','Next':'PageDown','ISO_Left_Tab':'Tab',
                   'Caps_Lock':'CapsLock','Num_Lock':'NumLock','Scroll_Lock':'ScrollLock',
                   'Print':'PrintScreen'}
        key = aliases.get(keysym,keysym)
    modifiers = []
    if state&0x04: modifiers.append('Ctrl')
    if state&0x20008: modifiers.append('Alt')
    if state&0x01: modifiers.append('Shift')
    value = '+'.join([*modifiers,key])
    try: parse_stop_hotkey(value)
    except ValueError: return None
    return value


def stop_hotkey_pressed(value, get_state):
    modifiers,vk = parse_stop_hotkey(value)
    return bool(get_state(vk)&0x8000) and all(get_state(m)&0x8000 for m in modifiers)


def hotkeys_conflict(first, second):
    a, av = parse_stop_hotkey(first)
    b, bv = parse_stop_hotkey(second)
    return av == bv and (set(a) <= set(b) or set(b) <= set(a))


class StartHotkey:
    """Consume held keys even when disabled; only a fresh press can start."""
    def __init__(self):
        self.binding = None
        self.armed = False

    def disarm(self):
        self.armed = False

    def poll(self, value, get_state, enabled=True):
        mods, key = parse_stop_hotkey(value)
        binding = (frozenset(mods), key)
        if binding != self.binding:
            self.binding = binding
            self.armed = False
        if not get_state(key) & 0x8000:
            self.armed = True
            return False
        exact = all(bool(get_state(m) & 0x8000) == (m in mods)
                    for m in (0x11, 0x12, 0x10))
        exact = exact and not any(get_state(m) & 0x8000 for m in (0x5B, 0x5C))
        fire = self.armed and enabled and exact
        self.armed = False
        return fire


class FishingCounter:
    """In-memory count for one start; never reads/writes files."""
    def __init__(self):
        self.total = 0
        self.run_catches = 0

    def begin_run(self):
        self.total = 0
        self.run_catches = 0

    def update(self, catches):
        if catches < self.run_catches:
            raise ValueError('Catch count moved backwards within a run')
        self.total += catches-self.run_catches
        self.run_catches = catches
        return self.total

    def remaining(self, target):
        return max(0,target-self.total) if target else 0
