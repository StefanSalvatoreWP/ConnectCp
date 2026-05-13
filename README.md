# 📱 CPConnect - Call of Duty Mobile PC Controller

Elevate your CODM experience by playing with a keyboard and mouse on your PC using ADB! No emulators needed, just your real phone and a USB cable. ⚡

---

## 🛠️ Prerequisites & Phone Setup

To make this work, your phone needs to be configured correctly to allow simulated inputs from your PC.

### 1. Enable Developer Options 🔓
- Go to **Settings** > **About Phone**.
- Tap **Build Number** 7 times until you see "You are now a developer!".

### 2. Critical Developer Settings ⚙️
Go to **Settings** > **Additional Settings** > **Developer Options** and enable:
- [x] **USB Debugging**: Allows the PC to communicate with your phone.
- [x] **USB Debugging (Security Settings)**: ⚠️ **CRITICAL** - This allows the script to simulate taps and swipes. If this is OFF, movement won't work!
- [x] **Disable Permission Monitoring**: (Optional) Prevents some popups during input simulation.

### 3. Connect to PC 💻
- Plug your phone into the PC via a high-quality USB cable.
- Accept the "Allow USB Debugging?" prompt on your phone screen.
- Ensure **Scrcpy** is running so you can see your game on the PC.

---

## 🎮 How to Use

### 🎨 The Overlay (`overlay.py`)
This is the easiest way to get started! It provides a visual interface to map your keys.

1. **Run the script**: `python overlay.py`
2. **Map Buttons**: A semi-transparent window will appear. Drag the colored circles 🔵 to match the positions of the buttons in your CODM layout.
3. **Save & Play**: Click the **SAVE & PLAY** button.
4. **FPS Mode**: 
   - Press **F1** to toggle **FPS Look Mode**. This captures your mouse and allows you to look around like a PC game! 🖱️
   - Use **F2** / **F3** to adjust your look sensitivity.
   - **Left Click** to Shoot 🔫
   - **Right Click** to Aim/Scope 🔭
5. **Move**: Use **W, A, S, D** to move your character.

### ⌨️ Controls
| Key | Action |
|-----|--------|
| **W, A, S, D** | Move Character |
| **Space** | Jump 🏃‍♂️ |
| **C** | Crouch / Slide 🧱 |
| **R** | Reload 🔄 |
| **E** | Aim / Scope 🎯 |
| **V** | Melee / Knife 🔪 |
| **F1** | Toggle Mouse Look 🔄 |
| **ESC** | Quit |

---

## 🚀 Script Details

- **`controller.py`**: The core logic for handling keyboard inputs and sending ADB commands.
- **`overlay.py`**: A GUI wrapper using Tkinter that makes positioning buttons easy and adds FPS-style mouse control.
- **`adb-tools/`**: Contains the necessary ADB binaries to talk to your Android device.

---

## ⚠️ Troubleshooting
- **Movements not working?** Double-check if **USB Debugging (Security Settings)** is ON.
- **Laggy input?** Ensure you are using a USB 3.0 port and a good cable.
- **Buttons misaligned?** Run `overlay.py` and drag the circles to match your specific HUD layout.

Enjoy your tactical advantage! 🏆
