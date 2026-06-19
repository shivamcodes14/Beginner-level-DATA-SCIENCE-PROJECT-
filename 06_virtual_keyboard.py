"""
AI Virtual Keyboard
====================
Real-time virtual keyboard using webcam + MediaPipe Tasks API (0.10+).

Install:
    pip install -r requirements.txt

Run:
    python virtual_keyboard.py
"""

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import time
import math
import urllib.request
import os
from typing import Optional
from pynput.keyboard import Controller

# Try CVZone (optional – better tracking)
try:
    from cvzone.HandTrackingModule import HandDetector
    CVZONE_AVAILABLE = True
    print("[INFO] cvzone found – using CVZone hand tracking.")
except ImportError:
    CVZONE_AVAILABLE = False
    print("[WARNING] cvzone not found. Using MediaPipe Tasks API.")

# ─────────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────────

CAM_WIDTH,  CAM_HEIGHT = 1280, 720
KEY_W,      KEY_H      = 85,   75
KEY_RADIUS, KEY_MARGIN = 10,   8
KB_ORIGIN_X, KB_ORIGIN_Y = 40, 220

PINCH_THRESHOLD = 45.0   # pixels
DEBOUNCE_TIME   = 0.45   # seconds

TEXT_AREA_X, TEXT_AREA_Y = 40, 30
TEXT_AREA_W = CAM_WIDTH - 80
TEXT_AREA_H = 80

# Colours (BGR)
CLR_BG               = (20,  20,  30)
CLR_KEY_NORMAL       = (50,  50,  70)
CLR_KEY_HOVER        = (80,  130, 200)
CLR_KEY_PRESSED      = (0,   200, 120)
CLR_KEY_BORDER       = (100, 100, 140)
CLR_KEY_BORDER_HOVER = (140, 190, 255)
CLR_TEXT_KEY         = (230, 230, 255)
CLR_TEXT_TYPED       = (220, 255, 220)
CLR_TEXT_AREA_BG     = (30,  30,  45)
CLR_TEXT_AREA_BORDER = (80,  120, 180)
CLR_FPS              = (0,   220, 150)
CLR_CURSOR           = (0,   255, 200)
CLR_PINCH_LINE       = (0,   200, 100)

KEYBOARD_ROWS = [
    ["1","2","3","4","5","6","7","8","9","0"],
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["Z","X","C","V","B","N","M","BKSP|⌫","ENTER|↵"],
    ["SPACE| "],
]

WIDE_KEYS = {"BKSP|⌫": 1.6, "ENTER|↵": 1.6, "SPACE| ": 8.5}

# MediaPipe hand connections (21 landmark pairs) – defined manually
# so we never touch mp.solutions.*
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),          # thumb
    (0,5),(5,6),(6,7),(7,8),          # index
    (0,9),(9,10),(10,11),(11,12),     # middle
    (0,13),(13,14),(14,15),(15,16),   # ring
    (0,17),(17,18),(18,19),(19,20),   # pinky
    (5,9),(9,13),(13,17),             # palm
]

MP_MODEL_FILENAME = "hand_landmarker.task"
MP_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)


# ─────────────────────────────────────────────────────────────────────────────
#  Drawing helpers
# ─────────────────────────────────────────────────────────────────────────────

def _fill_rounded(img, x1, y1, x2, y2, r, c):
    cv2.rectangle(img, (x1+r, y1),   (x2-r, y2),   c, -1)
    cv2.rectangle(img, (x1,   y1+r), (x2,   y2-r), c, -1)
    for cx, cy in [(x1+r,y1+r),(x2-r,y1+r),(x1+r,y2-r),(x2-r,y2-r)]:
        cv2.circle(img, (cx, cy), r, c, -1)

def _border_rounded(img, x1, y1, x2, y2, r, c, t):
    cv2.line(img, (x1+r,y1),(x2-r,y1), c, t)
    cv2.line(img, (x1+r,y2),(x2-r,y2), c, t)
    cv2.line(img, (x1,y1+r),(x1,y2-r), c, t)
    cv2.line(img, (x2,y1+r),(x2,y2-r), c, t)
    for cx,cy,a1,a2 in [(x1+r,y1+r,180,270),(x2-r,y1+r,270,360),
                        (x1+r,y2-r,90,180), (x2-r,y2-r,0,90)]:
        cv2.ellipse(img,(cx,cy),(r,r),0,a1,a2,c,t)

def draw_rounded_rect(img, x1, y1, x2, y2, radius, color,
                      border_color=None, border_thickness=2, alpha=1.0):
    if alpha < 1.0:
        overlay = img.copy()
        _fill_rounded(overlay, x1, y1, x2, y2, radius, color)
        cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)
    else:
        _fill_rounded(img, x1, y1, x2, y2, radius, color)
    if border_color:
        _border_rounded(img, x1, y1, x2, y2, radius, border_color, border_thickness)


# ─────────────────────────────────────────────────────────────────────────────
#  Key
# ─────────────────────────────────────────────────────────────────────────────

class Key:
    def __init__(self, display, action, x, y, w, h):
        self.display = display
        self.action  = action
        self.x, self.y, self.w, self.h = x, y, w, h
        self.is_hovered = False
        self.is_pressed = False
        self._press_time = 0.0

    def contains(self, px, py):
        return self.x <= px <= self.x+self.w and self.y <= py <= self.y+self.h

    def trigger_press(self):
        self.is_pressed = True
        self._press_time = time.time()

    def update(self):
        if self.is_pressed and (time.time()-self._press_time) > 0.15:
            self.is_pressed = False

    def draw(self, img):
        self.update()
        if self.is_pressed:
            fill, border, alpha = CLR_KEY_PRESSED, (0,255,150), 1.0
        elif self.is_hovered:
            fill, border, alpha = CLR_KEY_HOVER, CLR_KEY_BORDER_HOVER, 1.0
        else:
            fill, border, alpha = CLR_KEY_NORMAL, CLR_KEY_BORDER, 0.85

        draw_rounded_rect(img, self.x, self.y, self.x+self.w, self.y+self.h,
                          KEY_RADIUS, fill, border_color=border,
                          border_thickness=2, alpha=alpha)

        font = cv2.FONT_HERSHEY_SIMPLEX
        fs   = 0.55 if len(self.display) > 1 else 0.75
        tk   = 1    if len(self.display) > 1 else 2
        (tw, th), _ = cv2.getTextSize(self.display, font, fs, tk)
        cv2.putText(img, self.display,
                    (self.x+(self.w-tw)//2, self.y+(self.h+th)//2),
                    font, fs, CLR_TEXT_KEY, tk, cv2.LINE_AA)


# ─────────────────────────────────────────────────────────────────────────────
#  Build keyboard layout
# ─────────────────────────────────────────────────────────────────────────────

def build_keyboard():
    keys = []
    for row_idx, row in enumerate(KEYBOARD_ROWS):
        total_w = sum(int(KEY_W*WIDE_KEYS.get(r,1.0))+KEY_MARGIN for r in row) - KEY_MARGIN
        cur_x   = KB_ORIGIN_X + (CAM_WIDTH - 2*KB_ORIGIN_X - total_w) // 2
        cur_y   = KB_ORIGIN_Y + row_idx * (KEY_H + KEY_MARGIN)
        for raw in row:
            parts   = raw.split("|")
            display = parts[0]
            action  = parts[1] if len(parts) > 1 else parts[0]
            kw      = int(KEY_W * WIDE_KEYS.get(raw, 1.0))
            keys.append(Key(display, action, cur_x, cur_y, kw, KEY_H))
            cur_x += kw + KEY_MARGIN
    return keys


# ─────────────────────────────────────────────────────────────────────────────
#  Fallback detector — 100% MediaPipe Tasks API, zero mp.solutions references
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_model():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), MP_MODEL_FILENAME)
    if not os.path.exists(path):
        print("[INFO] Downloading MediaPipe hand landmarker model (~24 MB)…")
        urllib.request.urlretrieve(MP_MODEL_URL, path)
        print("[INFO] Model downloaded.")
    return path


class FallbackHandDetector:
    """
    Hand detector using ONLY mediapipe.tasks (works with mediapipe >= 0.10).
    No mp.solutions references anywhere.
    """

    def __init__(self, max_hands=1, detection_confidence=0.7):
        model_path   = _ensure_model()
        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options      = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.IMAGE,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self._landmarker = mp_vision.HandLandmarker.create_from_options(options)

    def findHands(self, img: np.ndarray, draw: bool = True):
        """Detect hands; return (img, list_of_hand_dicts)."""
        h, w   = img.shape[:2]
        rgb    = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_img)

        hands_data = []
        if result.hand_landmarks:
            for hand_lms in result.hand_landmarks:
                # Build lm_list: [ [idx, px, py], … ]
                lm_list = []
                pts = []
                for idx, lm in enumerate(hand_lms):
                    px, py = int(lm.x * w), int(lm.y * h)
                    lm_list.append([idx, px, py])
                    pts.append((px, py))
                hands_data.append({"lmList": lm_list})

                if draw:
                    # Draw connections (no mp.solutions needed)
                    for s, e in HAND_CONNECTIONS:
                        if s < len(pts) and e < len(pts):
                            cv2.line(img, pts[s], pts[e], (0, 150, 200), 2)
                    # Draw landmark dots
                    for px, py in pts:
                        cv2.circle(img, (px, py), 5, (0, 200, 255), -1)

        return img, hands_data

    def findDistance(self, p1, p2, img, hand_data, draw=True):
        """Euclidean distance between landmarks p1 and p2."""
        lm     = hand_data["lmList"]
        x1, y1 = lm[p1][1], lm[p1][2]
        x2, y2 = lm[p2][1], lm[p2][2]
        cx, cy = (x1+x2)//2, (y1+y2)//2
        dist   = math.hypot(x2-x1, y2-y1)
        if draw:
            cv2.line(img,   (x1,y1), (x2,y2), CLR_PINCH_LINE, 2)
            cv2.circle(img, (cx,cy),  8,       CLR_PINCH_LINE, cv2.FILLED)
        return dist, img, [x1, y1, x2, y2, cx, cy]


# ─────────────────────────────────────────────────────────────────────────────
#  Main application
# ─────────────────────────────────────────────────────────────────────────────

class VirtualKeyboardApp:
    def __init__(self):
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open webcam. Check connection / permissions.")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # Hand detector
        if CVZONE_AVAILABLE:
            self.detector = HandDetector(
                staticMode=False, maxHands=1,
                modelComplexity=0, detectionCon=0.7, minTrackCon=0.6,
            )
        else:
            self.detector = FallbackHandDetector(max_hands=1, detection_confidence=0.7)

        self.keys          = build_keyboard()
        self.typed_text    = ""
        self.kb_controller = Controller()

        self.last_press_time = 0.0
        self.prev_frame_time = time.time()
        self.fps             = 0.0

        self.index_pos  = (0, 0)
        self.pinch_dist = 999.0

        print("[INFO] Virtual Keyboard ready. Press ESC to quit.")

    # ── UI drawing ────────────────────────────────────────────────────────────

    def _draw_text_area(self, img):
        draw_rounded_rect(img,
            TEXT_AREA_X, TEXT_AREA_Y,
            TEXT_AREA_X+TEXT_AREA_W, TEXT_AREA_Y+TEXT_AREA_H,
            12, CLR_TEXT_AREA_BG,
            border_color=CLR_TEXT_AREA_BORDER, border_thickness=2)
        display = self.typed_text[-70:]
        blink   = "|" if int(time.time()*2) % 2 == 0 else " "
        cv2.putText(img, display+blink,
                    (TEXT_AREA_X+15, TEXT_AREA_Y+52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, CLR_TEXT_TYPED, 2, cv2.LINE_AA)
        cv2.putText(img, "Typed Text:",
                    (TEXT_AREA_X+15, TEXT_AREA_Y+18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (140,160,200), 1, cv2.LINE_AA)

    def _draw_hud(self, img):
        cv2.putText(img, f"FPS: {int(self.fps)}",
                    (CAM_WIDTH-130, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, CLR_FPS, 2, cv2.LINE_AA)
        sc = CLR_KEY_PRESSED if self.pinch_dist < PINCH_THRESHOLD else (160,160,180)
        sl = "PINCH!" if self.pinch_dist < PINCH_THRESHOLD else f"Dist:{int(self.pinch_dist)}"
        cv2.putText(img, sl, (CAM_WIDTH-180, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, sc, 2, cv2.LINE_AA)
        cv2.putText(img, "ESC to exit",
                    (CAM_WIDTH-155, CAM_HEIGHT-15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100,100,130), 1, cv2.LINE_AA)
        if self.index_pos != (0, 0):
            cv2.circle(img, self.index_pos, 12, CLR_CURSOR, 2)
            cv2.circle(img, self.index_pos,  4, CLR_CURSOR, cv2.FILLED)

    # ── Hand processing ───────────────────────────────────────────────────────

    def _process_hand_cvzone(self, img):
        result = self.detector.findHands(img, draw=True, flipType=True)
        hands  = result[0] if isinstance(result, tuple) else result
        if not hands:
            self.pinch_dist = 999.0
            return
        hand = hands[0]
        lm   = hand["lmList"]
        self.index_pos  = (int(lm[8][0]), int(lm[8][1]))
        dr = self.detector.findDistance(4, 8, img, hand, draw=True)
        self.pinch_dist = float(dr[0]) if isinstance(dr, tuple) else 999.0

    def _process_hand_fallback(self, img):
        img, hands = self.detector.findHands(img, draw=True)
        if not hands:
            self.pinch_dist = 999.0
            return
        hand = hands[0]
        lm   = hand["lmList"]
        self.index_pos  = (lm[8][1], lm[8][2])
        dist, img, _    = self.detector.findDistance(4, 8, img, hand, draw=True)
        self.pinch_dist = dist

    def _process_hand(self, img):
        if CVZONE_AVAILABLE:
            self._process_hand_cvzone(img)
        else:
            self._process_hand_fallback(img)

    # ── Key interaction ───────────────────────────────────────────────────────

    def _update_keys(self):
        ix, iy = self.index_pos
        now    = time.time()
        ok     = (now - self.last_press_time) > DEBOUNCE_TIME
        for key in self.keys:
            key.is_hovered = key.contains(ix, iy)
            if key.is_hovered and self.pinch_dist < PINCH_THRESHOLD and ok:
                self._press_key(key)
                self.last_press_time = now
                break

    def _press_key(self, key: Key):
        key.trigger_press()
        a = key.action
        if a == "⌫":
            if self.typed_text:
                self.typed_text = self.typed_text[:-1]
            self.kb_controller.press("\b")
            self.kb_controller.release("\b")
        elif a == "↵":
            self.typed_text += "\n"
            self.kb_controller.press("\n")
            self.kb_controller.release("\n")
        elif a == " ":
            self.typed_text += " "
            self.kb_controller.press(" ")
            self.kb_controller.release(" ")
        else:
            ch = a.lower()
            self.typed_text += ch
            self.kb_controller.press(ch)
            self.kb_controller.release(ch)

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[ERROR] Failed to read frame from camera.")
                break

            frame = cv2.flip(cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT)), 1)

            # Blend webcam + dark background so keys are readable
            dark  = np.full_like(frame, CLR_BG)
            frame = cv2.addWeighted(frame, 0.35, dark, 0.65, 0)

            self._process_hand(frame)
            self._update_keys()
            self._draw_text_area(frame)
            for key in self.keys:
                key.draw(frame)
            self._draw_hud(frame)

            now = time.time()
            self.fps = 1.0 / max(now - self.prev_frame_time, 1e-6)
            self.prev_frame_time = now

            cv2.imshow("AI Virtual Keyboard", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                print("[INFO] ESC – exiting.")
                break

        self.cap.release()
        cv2.destroyAllWindows()


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        VirtualKeyboardApp().run()
    except RuntimeError as e:
        print(f"[FATAL] {e}")
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted.")
    finally:
        cv2.destroyAllWindows()