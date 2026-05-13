import subprocess
import os
import time
import threading
from pynput import keyboard

# === CONFIGURATION ===
ADB_PATH = os.path.join(os.getcwd(), "adb-tools", "platform-tools", "adb.exe")

# Joystick (left side of screen)
JOY_X, JOY_Y = 220, 720
JOY_R = 120

# Button coordinates (from screenshot analysis)
# Right side buttons
ADS_BTN     = (2220, 450)   # Crosshair / Aim Down Sight
KNIFE_BTN   = (2150, 700)   # Melee knife
CROUCH_BTN  = (2300, 850)   # Crouch / Slide
JUMP_BTN    = (2220, 300)   # Jump (above ADS)
RELOAD_BTN  = (1500, 750)   # Reload (center-right area)

# NOTE: Fire is best done by clicking directly in Scrcpy window!
# Mouse look is also best done by dragging in Scrcpy window!


class GameController:
    def __init__(self):
        # Shell for joystick (motionevent hold)
        self.move_shell = self._open_shell()
        # Shell for button taps (separate so they dont conflict AS much)
        self.tap_shell = self._open_shell()

        self.active_keys = set()
        self.is_joy_touching = False
        self.move_lock = threading.Lock()
        self.tap_lock = threading.Lock()

    def _open_shell(self):
        return subprocess.Popen(
            [ADB_PATH, "shell"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    def _send_move(self, cmd):
        with self.move_lock:
            try:
                self.move_shell.stdin.write((cmd + "\n").encode())
                self.move_shell.stdin.flush()
            except:
                self.move_shell = self._open_shell()

    def _send_tap(self, cmd):
        with self.tap_lock:
            try:
                self.tap_shell.stdin.write((cmd + "\n").encode())
                self.tap_shell.stdin.flush()
            except:
                self.tap_shell = self._open_shell()

    def cleanup(self):
        print("\n[CLEANUP] Stopping controller and closing ADB shells...")
        if self.is_joy_touching:
            try: self._send_move(f"input motionevent UP {JOY_X} {JOY_Y}")
            except: pass
        
        for shell in [self.move_shell, self.tap_shell]:
            try:
                shell.stdin.close()
                shell.terminate()
                shell.wait(timeout=1)
            except:
                try: shell.kill()
                except: pass
        print("[CLEANUP] Done.")

    # === JOYSTICK (TRUE HOLD via motionevent) ===
    def joy_update(self):
        dx, dy = 0, 0
        if 'w' in self.active_keys: dy = -JOY_R
        if 's' in self.active_keys: dy = JOY_R
        if 'a' in self.active_keys: dx = -JOY_R
        if 'd' in self.active_keys: dx = JOY_R

        if dx == 0 and dy == 0:
            if self.is_joy_touching:
                self._send_move(f"input motionevent UP {JOY_X} {JOY_Y}")
                self.is_joy_touching = False
            return

        tx = JOY_X + dx
        ty = JOY_Y + dy

        if not self.is_joy_touching:
            self._send_move(f"input motionevent DOWN {JOY_X} {JOY_Y}")
            time.sleep(0.01)
            self._send_move(f"input motionevent MOVE {tx} {ty}")
            self.is_joy_touching = True
        else:
            self._send_move(f"input motionevent MOVE {tx} {ty}")

    # === BUTTON TAP ===
    def tap_button(self, x, y, name):
        # If joystick is active, briefly release, tap, then re-engage
        was_moving = self.is_joy_touching
        if was_moving:
            self._send_move(f"input motionevent UP {JOY_X} {JOY_Y}")
            self.is_joy_touching = False
            time.sleep(0.02)

        self._send_tap(f"input tap {x} {y}")
        print(f"  [{name}]")

        if was_moving:
            time.sleep(0.05)
            self.joy_update()

    # === KEY HANDLERS ===
    def on_key_press(self, key):
        if key == keyboard.Key.esc:
            print("\n[ESC] Exit requested.")
            return False # Stop listener

        try:
            k = key.char.lower() if key.char else key.name
        except AttributeError:
            k = key.name

        if k in self.active_keys:
            return
        self.active_keys.add(k)

        if k in ['w', 'a', 's', 'd']:
            self.joy_update()
            dirs = '+'.join(mk.upper() for mk in ['w','a','s','d'] if mk in self.active_keys)
            print(f"  [MOVE] {dirs}")
        elif k == 'space':
            threading.Thread(target=self.tap_button, args=(*JUMP_BTN, "JUMP"), daemon=True).start()
        elif k == 'c':
            threading.Thread(target=self.tap_button, args=(*CROUCH_BTN, "CROUCH"), daemon=True).start()
        elif k == 'r':
            threading.Thread(target=self.tap_button, args=(*RELOAD_BTN, "RELOAD"), daemon=True).start()
        elif k == 'e':
            threading.Thread(target=self.tap_button, args=(*ADS_BTN, "AIM/SCOPE"), daemon=True).start()
        elif k == 'v':
            threading.Thread(target=self.tap_button, args=(*KNIFE_BTN, "KNIFE"), daemon=True).start()

    def on_key_release(self, key):
        try:
            k = key.char.lower() if key.char else key.name
        except AttributeError:
            k = key.name

        if k in self.active_keys:
            self.active_keys.remove(k)

        if k in ['w', 'a', 's', 'd']:
            self.joy_update()
            if not any(mk in self.active_keys for mk in ['w', 'a', 's', 'd']):
                print("  [STOP]")


def main():
    ctrl = GameController()

    print()
    print("==========================================")
    print("   CPCONNECT - CODM CONTROLLER v3")
    print("==========================================")
    print("  W,A,S,D  = Move (TRUE HOLD)")
    print("  Space    = Jump")
    print("  C        = Crouch / Slide")
    print("  R        = Reload")
    print("  E        = Aim / Scope")
    print("  V        = Knife")
    print("------------------------------------------")
    print("  MOUSE: Use directly in Scrcpy window!")
    print("   - Click+Drag right side = Look around")
    print("   - Click fire button     = Shoot")
    print("------------------------------------------")
    print("  ESC or Ctrl+C   = Quit")
    print("==========================================")
    print()
    print("Ready! Use keyboard here + mouse in Scrcpy!")
    print()

    k_listener = keyboard.Listener(
        on_press=ctrl.on_key_press,
        on_release=ctrl.on_key_release
    )
    k_listener.start()

    try:
        k_listener.join()
    except KeyboardInterrupt:
        pass
    finally:
        ctrl.cleanup()


if __name__ == "__main__":
    main()
