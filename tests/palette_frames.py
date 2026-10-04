"""Offline fixtures with actual master-data tints, not live screenshots."""
import cv2
import numpy as np
from test_bot_vision import action_button, close_x, color, bite_frame, track_frame


def retint(frame, rgb):
    frame = frame.copy()
    frame[np.all(frame == np.array(color(99,210,245)), axis=2)] = tuple(bytes.fromhex(rgb)[::-1])
    return frame


def palette_frames(rgb):
    frame = np.zeros((600,1000,3),np.uint8)
    action_button(frame,(750,535),(920,575))
    yield 'button', retint(frame,rgb), 'action', (835,555)
    frame = np.zeros((600,1000,3),np.uint8)
    cv2.rectangle(frame,(35,90),(975,590),(235,245,250),-1)
    close_x(frame,(955,55))
    yield 'book_x', retint(frame,rgb), 'encyclopedia', (955,55)
    frame = np.full((600,1000,3),245,np.uint8)
    cv2.rectangle(frame,(580,0),(999,599),color(110,70,210),-1)
    cv2.rectangle(frame,(615,155),(969,245),(245,245,245),-1)
    cv2.rectangle(frame,(615,280),(969,485),(245,245,245),-1)
    close_x(frame,(955,45))
    action_button(frame,(700,520),(890,572))
    yield 'ready_start', retint(frame,rgb), 'action', (795,546)
    frame[500:] = color(110,70,210)
    yield 'ready_x_only', retint(frame,rgb), 'unknown', None
    frame = np.zeros((600,1000,3),np.uint8)
    cv2.rectangle(frame,(240,150),(770,500),(250,250,250),-1)
    close_x(frame,(760,155))
    yield 'item_x', retint(frame,rgb), 'item_detail', (760,155)
    frame = np.zeros((600,1000,3),np.uint8)
    cv2.rectangle(frame,(0,190),(999,410),tuple(bytes.fromhex(rgb)[::-1]),-1)
    for letter,x in zip('GET',(430,473,516)):
        cv2.putText(frame,letter,(x,92),cv2.FONT_HERSHEY_SIMPLEX,1.5,(255,255,255),4)
    yield 'reward', frame.copy(), 'reward', (500,522)
    action_button(frame,(785,525),(945,575))
    yield 'reward_continue', retint(frame,rgb), 'reward_continue', (865,550)
    yield 'tap', bite_frame(), 'tap', None
    yield 'reel', track_frame(), 'reel', None
