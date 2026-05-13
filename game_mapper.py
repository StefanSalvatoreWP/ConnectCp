import subprocess
import os
import time
from pynput import keyboard, mouse
import threading

# --- CONFIGURATION ---
# ADB Path
ADB_PATH = os.path.join(os.getcwd(), "adb-tools", "platform-tools", "adb.exe")

# Screen Resolution (Landscape)
WIDTH = 2400
HEIGHT = 1080

# Button Coordinates (Estimated from your screenshot)
# Format: (X, Y)
JOYSTICK_CENTER = (300, 800)
JOYSTICK_RADIUS = 150

FIRE_BTN = (2000, 750)
AIM_BTN = (1800, 650)
JUMP_BTN = (2200, 500)
CROUCH_BTN = (2200, 950)
RELOAD_BTN = (1950, 950)
INTERACT_BTN = (1400, 800)

# --- ADB FUNCTIONS ---
def tap(x, y):
    subprocess.run([ADB_PATH, "shell", "input", "tap", str(x), str(y)], capture_output=True)

def swipe(x1, y1, x2, y2, duration=100):
    subprocess.run([ADB_PATH, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)], capture_output=True)

# --- KEYBOARD LISTENER ---
active_keys = set()

def on_press(key):
    if key == keyboard.Key.esc:
        print("\n[ESC] Exit requested.")
        return False # Stop listener

    try:
        k = key.char.lower()
    except AttributeError:
        k = key.name

    if k not in active_keys:
        active_keys.add(k)
        handle_action(k, True)

def on_release(key):
    try:
        k = key.char.lower()
    except AttributeError:
        k = key.name
    
    if k in active_keys:
        active_keys.remove(k)
        handle_action(k, False)

def handle_action(k, is_pressed):
    if not is_pressed: return

    if k == 'space':
        print("Jump!")
        tap(*JUMP_BTN)
    elif k == 'r':
        print("Reload!")
        tap(*RELOAD_BTN)
    elif k == 'f':
        print("Interact!")
        tap(*INTERACT_BTN)
    elif k == 'shift':
        print("Crouch!")
        tap(*CROUCH_BTN)

# --- JOYSTICK THREAD ---
def joystick_loop():
    while True:
        if any(k in active_keys for k in ['w', 'a', 's', 'd']):
            dx, dy = 0, 0
            if 'w' in active_keys: dy -= JOYSTICK_RADIUS
            if 's' in active_keys: dy += JOYSTICK_RADIUS
            if 'a' in active_keys: dx -= JOYSTICK_RADIUS
            if 'd' in active_keys: dx += JOYSTICK_RADIUS
            
            x2 = JOYSTICK_CENTER[0] + dx
            y2 = JOYSTICK_CENTER[1] + dy
            
            # Send a fast swipe that lasts 150ms, but we repeat every 50ms
            # This 'overlaps' the touches to keep the joystick active
            swipe(JOYSTICK_CENTER[0], JOYSTICK_CENTER[1], x2, y2, 150)
        time.sleep(0.05)

# --- MOUSE LISTENER ---
def on_click(x, y, button, pressed):
    if pressed:
        if button == mouse.Button.left:
            print("Fire!")
            tap(*FIRE_BTN)
        elif button == mouse.Button.right:
            print("Aim!")
            tap(*AIM_BTN)

# --- MAIN ---
if __name__ == "__main__":
    print("--- CODM KEY MAPPER STARTED ---")
    print("Controls:")
    print("  W,A,S,D: Move")
    print("  Space: Jump")
    print("  R: Reload")
    print("  F: Interact")
    print("  Shift: Crouch")
    print("  Left Click: Fire")
    print("  Right Click: Aim")
    print("\nKeep this window focused while playing!")
    print("Press Ctrl+C to quit.")

    # Start joystick thread
    threading.Thread(target=joystick_loop, daemon=True).start()

    # Start listeners
    with keyboard.Listener(on_press=on_press, on_release=on_release) as k_listener:
        with mouse.Listener(on_click=on_click) as m_listener:
            k_listener.join()
            m_listener.join()
