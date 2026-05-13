import tkinter as tk
import json
import os
import subprocess
import time
import threading
from pynput import keyboard as kb, mouse
import ctypes

# === CONFIG ===
ADB_PATH = os.path.join(os.getcwd(), "adb-tools", "platform-tools", "adb.exe")
CONFIG_FILE = "button_config.json"
GAME_W, GAME_H = 2400, 1080

# Default button positions (game coordinates)
DEFAULT_BUTTONS = {
    "JOYSTICK":  {"x": 220, "y": 720, "key": "WASD", "color": "#ff00ea", "size": 60},
    "JUMP":      {"x": 2220, "y": 300, "key": "Space", "color": "#00f2ff", "size": 30},
    "CROUCH":    {"x": 2300, "y": 850, "key": "C",     "color": "#ffaa00", "size": 30},
    "AIM":       {"x": 2220, "y": 450, "key": "E",     "color": "#ff4444", "size": 30},
    "KNIFE":     {"x": 2150, "y": 700, "key": "V",     "color": "#44ff44", "size": 30},
    "RELOAD":    {"x": 1500, "y": 750, "key": "R",     "color": "#ffff00", "size": 30},
    "FIRE":      {"x": 2100, "y": 600, "key": "L-CLK", "color": "#ff0000", "size": 40},
}

JOY_R = 120


class OverlayApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CPConnect Overlay - Drag buttons to position!")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.6)
        self.root.configure(bg='black')
        self.root.geometry("960x432+100+100")
        
        # Make window transparent to clicks when not dragging? 
        # No, we need clicks to drag. But we can make it prettier.

        # Load or create config
        self.buttons = self.load_config()

        # Canvas
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Draw buttons
        self.items = {}
        self.labels = {}
        self.drag_data = {"item": None, "x": 0, "y": 0, "name": None}

        self.root.after(100, self.draw_all)
        self.root.bind("<Configure>", lambda e: self.root.after(50, self.draw_all))

        # Toolbar
        toolbar = tk.Frame(self.root, bg="#111", height=35)
        toolbar.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Button(toolbar, text="SAVE & PLAY", bg="#00f2ff", fg="black", font=("Arial", 10, "bold"),
                  command=self.save_and_play).pack(side=tk.LEFT, padx=5, pady=3)
        tk.Button(toolbar, text="RESET", bg="#ff4444", fg="white", font=("Arial", 10, "bold"),
                  command=self.reset_config).pack(side=tk.LEFT, padx=5, pady=3)
        
        self.status = tk.Label(toolbar, text="Drag buttons to match your game layout!", 
                               bg="#111", fg="#888", font=("Arial", 9))
        self.status.pack(side=tk.RIGHT, padx=10)

        self.root.mainloop()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return DEFAULT_BUTTONS.copy()

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.buttons, f, indent=2)

    def reset_config(self):
        self.buttons = DEFAULT_BUTTONS.copy()
        self.draw_all()

    def game_to_screen(self, gx, gy):
        """Convert game coords (2400x1080) to overlay window coords."""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        sx = int(gx * w / GAME_W)
        sy = int(gy * h / GAME_H)
        return sx, sy

    def screen_to_game(self, sx, sy):
        """Convert overlay window coords to game coords (2400x1080)."""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        gx = int(sx * GAME_W / w)
        gy = int(sy * GAME_H / h)
        return gx, gy

    def draw_all(self):
        self.canvas.delete("all")
        self.items.clear()
        self.labels.clear()

        for name, btn in self.buttons.items():
            sx, sy = self.game_to_screen(btn["x"], btn["y"])
            r = btn["size"]
            color = btn["color"]

            # Draw circle
            item = self.canvas.create_oval(sx-r, sy-r, sx+r, sy+r,
                                            outline=color, width=2, fill="")
            # Draw label
            label = self.canvas.create_text(sx, sy,
                                             text=f"{name}\n[{btn['key']}]\n({btn['x']},{btn['y']})",
                                             fill=color, font=("Arial", 7, "bold"))

            self.items[item] = name
            self.items[label] = name
            self.labels[name] = label

            # Bind drag events
            self.canvas.tag_bind(item, "<ButtonPress-1>", self.on_drag_start)
            self.canvas.tag_bind(item, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self.on_drag_end)
            self.canvas.tag_bind(label, "<ButtonPress-1>", self.on_drag_start)
            self.canvas.tag_bind(label, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(label, "<ButtonRelease-1>", self.on_drag_end)

    def on_drag_start(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        name = self.items.get(item)
        if name:
            self.drag_data["item"] = item
            self.drag_data["name"] = name
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def on_drag(self, event):
        name = self.drag_data["name"]
        if not name:
            return
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]

        # Move all items for this button
        for item_id, item_name in self.items.items():
            if item_name == name:
                self.canvas.move(item_id, dx, dy)

        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

        # Update game coordinates
        gx, gy = self.screen_to_game(event.x, event.y)
        self.buttons[name]["x"] = gx
        self.buttons[name]["y"] = gy

        # Update label text
        label = self.labels.get(name)
        if label:
            btn = self.buttons[name]
            self.canvas.itemconfig(label, text=f"{name}\n[{btn['key']}]\n({gx},{gy})")

        self.status.config(text=f"{name} -> ({gx}, {gy})")

    def on_drag_end(self, event):
        self.drag_data = {"item": None, "x": 0, "y": 0, "name": None}

    def save_and_play(self):
        self.save_config()
        self.status.config(text="Saved! Starting controller...")
        self.root.after(500, self.start_controller)

    def start_controller(self):
        # Instead of destroying, we transform the overlay into "Play Mode"
        self.status.config(text="CONTROLLER ACTIVE - F1: FPS Look | ESC: Exit", fg="#00f2ff")
        self.canvas.delete("all")
        
        # Draw a simple crosshair
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        cx, cy = w // 2, h // 2
        size = 10
        self.canvas.create_line(cx - size, cy, cx + size, cy, fill="#00f2ff", width=2)
        self.canvas.create_line(cx, cy - size, cx, cy + size, fill="#00f2ff", width=2)
        
        # Make the window click-through (Windows only trick)
        # This allows clicking Scrcpy through the transparent parts of the overlay
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x20) # WS_EX_LAYERED | WS_EX_TRANSPARENT

        # Start controller in a background thread so Tkinter can stay alive
        threading.Thread(target=run_controller, args=(self.buttons,), daemon=True).start()


def run_controller(buttons):
    """Run the game controller with the configured button positions."""
    joy = buttons["JOYSTICK"]
    JOY_X, JOY_Y = joy["x"], joy["y"]

    move_shell = subprocess.Popen([ADB_PATH, "shell"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    tap_shell = subprocess.Popen([ADB_PATH, "shell"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    look_shell = subprocess.Popen([ADB_PATH, "shell"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    active_keys = set()
    is_joy_touching = False
    is_look_touching = False
    fps_look_mode = False
    
    move_lock = threading.Lock()
    tap_lock = threading.Lock()
    look_lock = threading.Lock()

    # Center of look area (right side of screen)
    LOOK_X, LOOK_Y = 1800, 540 
    
    mouse_ctrl = mouse.Controller()

    def cleanup():
        nonlocal is_joy_touching, is_look_touching
        print("\n[CLEANUP] Stopping controller and closing ADB shells...")
        if is_joy_touching:
            try: send_move(f"input motionevent UP {JOY_X} {JOY_Y}")
            except: pass
        if is_look_touching:
            try: send_look(f"input motionevent UP {LOOK_X} {LOOK_Y}")
            except: pass
        
        for shell in [move_shell, tap_shell, look_shell]:
            try:
                shell.stdin.close()
                shell.terminate()
            except: pass
        print("[CLEANUP] Done.")

    def send_move(cmd):
        nonlocal move_shell
        with move_lock:
            try:
                move_shell.stdin.write((cmd + "\n").encode())
                move_shell.stdin.flush()
            except:
                move_shell = subprocess.Popen([ADB_PATH, "shell"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def send_tap(cmd):
        nonlocal tap_shell
        with tap_lock:
            try:
                tap_shell.stdin.write((cmd + "\n").encode())
                tap_shell.stdin.flush()
            except:
                tap_shell = subprocess.Popen([ADB_PATH, "shell"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def send_look(cmd):
        nonlocal look_shell
        with look_lock:
            try:
                look_shell.stdin.write((cmd + "\n").encode())
                look_shell.stdin.flush()
            except:
                look_shell = subprocess.Popen([ADB_PATH, "shell"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def joy_update():
        nonlocal is_joy_touching
        dx, dy = 0, 0
        if 'w' in active_keys: dy = -JOY_R
        if 's' in active_keys: dy = JOY_R
        if 'a' in active_keys: dx = -JOY_R
        if 'd' in active_keys: dx = JOY_R

        if dx == 0 and dy == 0:
            if is_joy_touching:
                send_move(f"input motionevent UP {JOY_X} {JOY_Y}")
                is_joy_touching = False
            return

        tx, ty = JOY_X + dx, JOY_Y + dy
        if not is_joy_touching:
            send_move(f"input motionevent DOWN {JOY_X} {JOY_Y}")
            time.sleep(0.01)
            send_move(f"input motionevent MOVE {tx} {ty}")
            is_joy_touching = True
        else:
            send_move(f"input motionevent MOVE {tx} {ty}")

    def tap_button(name):
        nonlocal is_joy_touching
        btn = buttons[name]
        was_moving = is_joy_touching
        if was_moving:
            send_move(f"input motionevent UP {JOY_X} {JOY_Y}")
            is_joy_touching = False
            time.sleep(0.02)
        send_tap(f"input tap {btn['x']} {btn['y']}")
        print(f"  [{name}]")
        if was_moving:
            time.sleep(0.05)
            joy_update()

    KEY_MAP = {
        'space': 'JUMP',
        'c':     'CROUCH',
        'r':     'RELOAD',
        'e':     'AIM',
        'v':     'KNIFE',
    }

    def on_press(key):
        nonlocal fps_look_mode, is_look_touching
        if key == kb.Key.esc:
            print("\n[ESC] Exit requested.")
            return False 

        if key == kb.Key.f1:
            fps_look_mode = not fps_look_mode
            print(f"\n[F1] FPS LOOK: {'ON' if fps_look_mode else 'OFF'}")
            if not fps_look_mode and is_look_touching:
                send_look(f"input motionevent UP {LOOK_X} {LOOK_Y}")
                is_look_touching = False
            return

        try:
            k = key.char.lower() if key.char else key.name
        except AttributeError:
            k = key.name
        if k in active_keys: return
        active_keys.add(k)

        if k in ['w', 'a', 's', 'd']:
            joy_update()
            dirs = '+'.join(mk.upper() for mk in ['w','a','s','d'] if mk in active_keys)
            print(f"  [MOVE] {dirs}")
        elif k in KEY_MAP:
            threading.Thread(target=tap_button, args=(KEY_MAP[k],), daemon=True).start()

    def on_release(key):
        try:
            k = key.char.lower() if key.char else key.name
        except AttributeError:
            k = key.name
        if k in active_keys: active_keys.remove(k)
        if k in ['w', 'a', 's', 'd']:
            joy_update()
            if not any(mk in active_keys for mk in ['w','a','s','d']):
                print("  [STOP]")

    print()
    print("==========================================")
    print("   CPCONNECT CONTROLLER - RUNNING!")
    print("==========================================")
    print("  WASD=Move  Space=Jump  C=Crouch")
    print("  R=Reload  E=Aim  V=Knife")
    print("  F1 = Toggle FPS Mouse Look (EXPERIMENTAL)")
    print("  ESC or Ctrl+C = Quit")
    print("==========================================")
    print()

    def on_move(x, y):
        nonlocal fps_look_mode, is_look_touching
        if not fps_look_mode: return

        # Calculate delta from center of screen (approx)
        # We'll use a fixed screen center for now or user can calibrate
        # For simplicity, let's just use the current position relative to start
        pass # We'll implement delta logic below

    # Actually, a better on_move logic:
    last_mouse_pos = [None, None]
    
    def on_mouse_move(x, y):
        nonlocal fps_look_mode, is_look_touching
        if not fps_look_mode: return
        
        if last_mouse_pos[0] is None:
            last_mouse_pos[0], last_mouse_pos[1] = x, y
            return

        dx = x - last_mouse_pos[0]
        dy = y - last_mouse_pos[1]
        
        if abs(dx) < 2 and abs(dy) < 2: return # Deadzone

        # Sensitivity
        sens = 1.5
        tx = LOOK_X + int(dx * sens)
        ty = LOOK_Y + int(dy * sens)

        if not is_look_touching:
            send_look(f"input motionevent DOWN {LOOK_X} {LOOK_Y}")
            is_look_touching = True
        
        send_look(f"input motionevent MOVE {tx} {ty}")
        
        # Reset mouse to avoid hitting screen edges
        # This is tricky without a true 'lock', but we can try
        # mouse_ctrl.position = (center_x, center_y) 
        # But that triggers another on_move. We'll skip for now and just use deltas.
        last_mouse_pos[0], last_mouse_pos[1] = x, y

    k_listener = kb.Listener(on_press=on_press, on_release=on_release)
    m_listener = mouse.Listener(on_move=on_mouse_move)
    
    k_listener.start()
    m_listener.start()
    
    # We don't join() here because we want the thread to finish when the app closes
    # or when kb_listener returns False.
    while k_listener.running:
        time.sleep(0.1)
    
    cleanup()
    # Close the whole app when controller exits
    os._exit(0)


if __name__ == "__main__":
    OverlayApp()
