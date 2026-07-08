# Author: Steven Blair (aka Randm978)
# Date: 08-JUL-2026
# Script Name: Star Citizen Mining Buddy (SCMB)
# Description: Creates an overlay over the star citizen client and deciphers mining signals as well as give info on server status
import cv2
import pytesseract
import numpy as np
import tkinter as tk
import threading
import time
import ctypes
import re
import os
import webbrowser
from mss import MSS
import config 

pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

# Windows API Constants for Mouse Transparency Pass-Through
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000

FR_PRIVATE = 0x10

def load_custom_font(font_path):
    if os.path.exists(font_path):
        try:
            result = ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
            if result != 0:
                print(f"[SYSTEM] Successfully loaded custom font: {font_path}")
                return config.FONT_PRIMARY
        except Exception as e:
            print(f"[ERROR] Failed to load font via Windows API: {e}")
    print(f"[WARN] Font file missing or failed. Falling back to: {config.FONT_FALLBACK}")
    return config.FONT_FALLBACK

def make_window_click_through(hwnd):
    try:
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_TRANSPARENT | WS_EX_LAYERED
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    except Exception as e:
        print(f"Error setting click-through: {e}")

def make_window_interactive(hwnd):
    try:
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style &= ~WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    except Exception as e:
        print(f"Error restoring interactivity: {e}")


class RegionSelector:
    def __init__(self, parent, initial_box, border_color, label_text, active_font):
        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.45)
        
        self.frame = tk.Frame(self.window, highlightbackground=border_color, highlightthickness=2, bg=border_color)
        self.frame.pack(fill="both", expand=True)
        
        self.lbl = tk.Label(self.frame, text=f" {label_text} ", fg="#ffffff", bg="#000000", font=(active_font, 8, "bold"))
        self.lbl.place(x=4, y=4)
        
        self.window.geometry(f"{initial_box['width']}x{initial_box['height']}+{initial_box['left']}+{initial_box['top']}")
        
        self.frame.bind("<Button-1>", self.start_drag)
        self.frame.bind("<B1-Motion>", self.do_drag)
        self.lbl.bind("<Button-1>", self.start_drag)
        self.lbl.bind("<B1-Motion>", self.do_drag)
        
        self.grip_size = 6
        self.grips = {}
        
        grip_configs = [
            ("nw", 0.0, 0.0, "size_nw_se"), ("n", 0.5, 0.0, "size_ns"),   ("ne", 1.0, 0.0, "size_ne_sw"),
            ("w", 0.0, 0.5, "size_we"),                                  ("e", 1.0, 0.5, "size_we"),
            ("sw", 0.0, 1.0, "size_ne_sw"), ("s", 0.5, 1.0, "size_ns"),   ("se", 1.0, 1.0, "size_nw_se")
        ]
        
        for name, relx, rely, cursor in grip_configs:
            g = tk.Frame(self.frame, width=self.grip_size, height=self.grip_size, bg="#ffffff", highlightbackground="#000000", highlightthickness=1, cursor=cursor)
            g.place(relx=relx, rely=rely, anchor=name)
            g.bind("<Button-1>", lambda e, n=name: self.start_resize(e, n))
            g.bind("<B1-Motion>", lambda e, n=name: self.do_resize(e, n))
            self.grips[name] = g

    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def do_drag(self, event):
        x = self.window.winfo_x() - self.drag_x + event.x
        y = self.window.winfo_y() - self.drag_y + event.y
        self.window.geometry(f"+{x}+{y}")

    def start_resize(self, event, side):
        self.resize_start_y = event.y_root
        self.resize_start_x = event.x_root
        self.orig_x = self.window.winfo_x()
        self.orig_y = self.window.winfo_y()
        self.orig_w = self.window.winfo_width()
        self.orig_h = self.window.winfo_height()

    def do_resize(self, event, side):
        dx = event.x_root - self.resize_start_x
        dy = event.y_root - self.resize_start_y
        
        new_x, new_y, new_w, new_h = self.orig_x, self.orig_y, self.orig_w, self.orig_h
        min_w, min_h = 40, 20
        
        if "e" in side: new_w = max(min_w, self.orig_w + dx)
        if "s" in side: new_h = max(min_h, self.orig_h + dy)
        
        if "w" in side:
            max_w = self.orig_w + self.orig_x - min_w
            new_x = min(max_w, self.orig_x + dx)
            new_w = self.orig_w + (self.orig_x - new_x)
            
        if "n" in side:
            max_h = self.orig_h + self.orig_y - min_h
            new_y = min(max_h, self.orig_y + dy)
            new_h = self.orig_h + (self.orig_y - new_y)
            
        self.window.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")

    def get_coordinates(self):
        return {
            "top": self.window.winfo_y(),
            "left": self.window.winfo_x(),
            "width": self.window.winfo_width(),
            "height": self.window.winfo_height()
        }


class ConfigPanel:
    def __init__(self, parent, overlay_app, active_font):
        self.parent = parent
        self.overlay_app = overlay_app
        self.active_font = active_font
        
        self.window = tk.Toplevel(parent)
        self.window.title("Mining Config")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.configure(bg="#000000")
        self.window.attributes('-alpha', 0.85)
        
        self.is_minimized = False
        self.ui_unlocked = False
        
        self.scanner_selector = None
        self.overlay_selector = None
        self.fps_selector = None
        
        self.large_width = 400
        self.large_height = 150  
        self.small_width = 180   
        self.small_height = 32
        
        try:
            init_x = config.PANEL_LARGE_POS['left']
            init_y = config.PANEL_LARGE_POS['top']
        except AttributeError:
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            init_x = (screen_width // 2) - (self.large_width // 2)
            init_y = (screen_height // 2) - (self.large_height // 2)
            config.PANEL_LARGE_POS = {'left': init_x, 'top': init_y}
            config.PANEL_SMALL_POS = {'left': screen_width - self.small_width - 20, 'top': 20}
            
        self.window.geometry(f"{self.large_width}x{self.large_height}+{init_x}+{init_y}")
        
        self.header_frame = tk.Frame(self.window, bg="#000000", padx=5, pady=5)
        self.header_frame.pack(fill="x", side="top", anchor="n")
        
        self.status_light = tk.Canvas(self.header_frame, width=12, height=12, bg="#555555", highlightthickness=0)
        self.status_light.pack(side="left", padx=(5, 2), pady=4)
        
        self.fps_display_label = tk.Label(
            self.header_frame, text="Server FPS: --", fg="#555555", bg="#000000", 
            font=(self.active_font, 10, "bold")
        )
        self.fps_display_label.pack(side="left", padx=5)
        
        self.toggle_button = tk.Button(
            self.header_frame, text="🗕", fg="#ff5500", bg="#111111", 
            font=(self.active_font, 10, "bold"), bd=0, width=3, cursor="hand2", command=self.toggle_panel_state
        )
        self.toggle_button.pack(side="right", padx=2)
        
        self.control_frame = tk.Frame(self.window, bg="#111111", padx=15, pady=5)
        self.control_frame.pack(fill="both", expand=True, padx=10, pady=(5, 5))
        
        self.btn_row = tk.Frame(self.control_frame, bg="#111111")
        self.btn_row.pack(fill="x", pady=2)
        
        self.status_lbl = tk.Label(self.btn_row, text="UI Calibration Layout:", fg="#ffffff", bg="#111111", font=(self.active_font, 10, "bold"))
        self.status_lbl.pack(side="left")
        
        self.unlock_btn = tk.Button(
            self.btn_row, text="🔓 UNLOCK UI", fg="#ffffff", bg="#222222",
            font=(self.active_font, 9, "bold"), bd=1, padx=15, pady=4, cursor="hand2", command=self.toggle_ui_lock
        )
        self.unlock_btn.pack(side="right")
        
        self.slider_row = tk.Frame(self.control_frame, bg="#111111", pady=2)
        self.slider_row.pack(fill="x")
        
        self.slider_lbl = tk.Label(self.slider_row, text="HUD Font Size:", fg="#ffffff", bg="#111111", font=(self.active_font, 10, "bold"))
        self.slider_lbl.pack(side="left")
        
        start_size = getattr(config, "HUD_FONT_SIZE", 14)
        
        self.font_slider = tk.Scale(
            self.slider_row, from_=10, to=32, orient="horizontal", bg="#111111", fg="#ff5500",
            troughcolor="#222222", highlightthickness=0, font=(self.active_font, 8),
            cursor="hand2", command=self.on_font_slider_adjust
        )
        self.font_slider.set(start_size)
        self.font_slider.pack(side="right", fill="x", expand=True, padx=(10, 0))

        self.clipboard_row = tk.Frame(self.control_frame, bg="#111111", pady=0)
        self.clipboard_row.pack(fill="x", side="bottom", pady=0)

        self.support_btn = tk.Button(
            self.clipboard_row, 
            text="🤝 GITHUB", 
            fg="#94a3b8", 
            bg="#1c1c1c",
            activeforeground="#ffffff",
            activebackground="#475569",
            font=(self.active_font, 8, "bold"), 
            bd=0, 
            padx=10, 
            pady=3,
            cursor="hand2", 
            command=lambda: webbrowser.open("https://github.com/stevenjblair/SCMB")
        )
        self.support_btn.pack(side="left", pady=0)

        self.copy_btn = tk.Button(
            self.clipboard_row, 
            text="📋 R_DISPLAYINFO", 
            fg="#00ffcc", 
            bg="#1c1c1c",
            activeforeground="#ffffff",
            activebackground="#00ffcc",
            font=(self.active_font, 8, "bold"), 
            bd=0, 
            padx=10, 
            pady=3,
            cursor="hand2", 
            command=self.copy_command_to_clipboard
        )
        self.copy_btn.pack(side="right", pady=0)

        self.kofi_btn = tk.Button(
            self.clipboard_row, 
            text="☕ KO-FI", 
            fg="#ff5e5b", 
            bg="#1c1c1c",
            activeforeground="#ffffff",
            activebackground="#ff5e5b",
            font=(self.active_font, 8, "bold"), 
            bd=0, 
            padx=10, 
            pady=3,
            cursor="hand2", 
            command=lambda: webbrowser.open("https://ko-fi.com/randm978")
        )
        self.kofi_btn.pack(side="top", pady=0)

        self.hwnd = ctypes.windll.user32.GetParent(self.window.winfo_id())
        make_window_click_through(self.hwnd)
        
        self.window.bind("<Motion>", self.check_alt_state)
        self.window.bind("<Button-1>", self.start_drag)
        self.window.bind("<B1-Motion>", self.do_drag)
        self.window.bind("<ButtonRelease-1>", self.end_drag)

    def copy_command_to_clipboard(self):
        self.window.clipboard_clear()
        self.window.clipboard_append("r_displayinfo = 1")
        self.copy_btn.config(text="COPIED!", fg="#ffffff", bg="#00ffcc")
        self.window.after(1500, lambda: self.copy_btn.config(text="📋 COPY R_DISPLAYINFO", fg="#00ffcc", bg="#1c1c1c"))

    def check_alt_state(self, event):
        if event.state & 0x20000: 
            make_window_interactive(self.hwnd)
        else:
            make_window_click_through(self.hwnd)

    def start_drag(self, event):
        if event.state & 0x20000:
            self.drag_x = event.x
            self.drag_y = event.y

    def do_drag(self, event):
        if event.state & 0x20000:
            x = self.window.winfo_x() - self.drag_x + event.x
            y = self.window.winfo_y() - self.drag_y + event.y
            self.window.geometry(f"+{x}+{y}")

    def end_drag(self, event):
        if event.state & 0x20000:
            current_coords = {'left': self.window.winfo_x(), 'top': self.window.winfo_y()}
            if not self.is_minimized:
                config.PANEL_LARGE_POS = current_coords
                self.save_bulk_config({"PANEL_LARGE_POS": current_coords})
            else:
                config.PANEL_SMALL_POS = current_coords
                self.save_bulk_config({"PANEL_SMALL_POS": current_coords})

    def on_font_slider_adjust(self, val):
        new_size = int(val)
        config.HUD_FONT_SIZE = new_size
        self.overlay_app.ore_label.config(font=(self.active_font, new_size, "bold"))
        self.save_bulk_config({"HUD_FONT_SIZE": new_size})

    def update_fps_status(self, fps_val_str=None, force_grey=False):
        if force_grey:
            self.fps_display_label.config(text="Server FPS: --", fg="#555555")
            self.status_light.config(bg="#555555")
            return

        color = "#555555"
        display_text = "Server FPS: --"
        if fps_val_str:
            display_text = f"Server FPS: {fps_val_str}"
            try:
                val = int(float(fps_val_str))
                if val >= 20: color = "#00ff44"
                elif val < 10: color = "#ff3333"
                else: color = "#ffcc00"
            except ValueError:
                pass
        self.fps_display_label.config(text=display_text, fg=color)
        self.status_light.config(bg=color)

    def toggle_ui_lock(self):
        if not self.ui_unlocked:
            self.ui_unlocked = True
            self.unlock_btn.config(text="🔒 LOCK & SAVE", bg="#ff5500")
            self.scanner_selector = RegionSelector(self.window, config.MONITOR_BOX, "#ff3333", "SCANNER", self.active_font)
            self.overlay_selector = RegionSelector(self.window, config.OVERLAY_BOX, "#0055ff", "OUTPUT TEXT", self.active_font)
            self.fps_selector = RegionSelector(self.window, config.FPS_BOX, "#00ff44", "SERVER FPS", self.active_font)
        else:
            self.ui_unlocked = False
            self.unlock_btn.config(text="🔓 UNLOCK UI", bg="#222222")
            new_scanner = self.scanner_selector.get_coordinates()
            new_overlay = self.overlay_selector.get_coordinates()
            new_fps = self.fps_selector.get_coordinates()
            
            self.scanner_selector.window.destroy()
            self.overlay_selector.window.destroy()
            self.fps_selector.window.destroy()
            
            self.scanner_selector = None
            self.overlay_selector = None
            self.fps_selector = None
            
            config.MONITOR_BOX = new_scanner
            config.OVERLAY_BOX = new_overlay
            config.FPS_BOX = new_fps
            
            self.overlay_app.root.geometry(f"{new_overlay['width']}x{new_overlay['height']}+{new_overlay['left']}+{new_overlay['top']}")
            self.save_bulk_config({"MONITOR_BOX": new_scanner, "OVERLAY_BOX": new_overlay, "FPS_BOX": new_fps})

    def save_bulk_config(self, updates_dict):
        try:
            with open("config.py", "r", encoding="utf-8") as file:
                content = file.read()
            with open("config.py", "a", encoding="utf-8") as file:
                for var_name in updates_dict.keys():
                    if f"{var_name} =" not in content:
                        file.write(f"\n{var_name} = {{'left': 0, 'top': 0}}\n")
            with open("config.py", "r", encoding="utf-8") as file:
                lines = file.readlines()
            with open("config.py", "w", encoding="utf-8") as file:
                for line in lines:
                    matched = False
                    for var_name, coords in updates_dict.items():
                        if line.strip().startswith(f"{var_name} ="):
                            file.write(f"{var_name} = {coords}\n")
                            matched = True
                            break
                    if not matched:
                        file.write(line)
        except Exception as e:
            print(f"[ERROR] Serialization fault writing panel states: {e}")

    def toggle_panel_state(self):
        if not self.is_minimized:
            self.control_frame.pack_forget()
            self.toggle_button.config(text="🗖")
            try:
                sm_x = config.PANEL_SMALL_POS['left']
                sm_y = config.PANEL_SMALL_POS['top']
            except (AttributeError, KeyError):
                sm_x = self.window.winfo_screenwidth() - self.small_width - 20
                sm_y = 20
            self.window.geometry(f"{self.small_width}x{self.small_height}+{sm_x}+{sm_y}")
            self.is_minimized = True
        else:
            self.control_frame.pack(fill="both", expand=True, padx=10, pady=(5, 5))
            self.toggle_button.config(text="🗕")
            try:
                lg_x = config.PANEL_LARGE_POS['left']
                lg_y = config.PANEL_LARGE_POS['top']
            except (AttributeError, KeyError):
                lg_x = (self.window.winfo_screenwidth() // 2) - (self.large_width // 2)
                lg_y = (self.window.winfo_screenheight() // 2) - (self.large_height // 2)
            self.window.geometry(f"{self.large_width}x{self.large_height}+{lg_x}+{lg_y}")
            self.is_minimized = False


class MiningOverlay:
    def __init__(self, root, active_font):
        self.root = root
        self.root.title("SC Mining Buddy")
        invisible_color = '#121212' 
        self.root.wm_attributes('-transparentcolor', invisible_color)
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        self.root.geometry(f"{config.OVERLAY_BOX['width']}x{config.OVERLAY_BOX['height']}+{config.OVERLAY_BOX['left']}+{config.OVERLAY_BOX['top']}")
        self.root.configure(bg=invisible_color)
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        
        start_size = getattr(config, "HUD_FONT_SIZE", 14)
        
        self.ore_label = tk.Label(root, text="", fg="#ffffff", bg=invisible_color, font=(active_font, start_size, "bold"))
        self.ore_label.pack(anchor="w", padx=10, pady=10)
        
        hwnd_overlay = ctypes.windll.user32.GetParent(self.root.winfo_id())
        make_window_click_through(hwnd_overlay)
        self.panel_ref = None 

    def start_loop(self):
        threading.Thread(target=self.automation_loop, daemon=True).start()

    def calculate_ore_match(self, scanned_sig):
        if scanned_sig in config.MINING_DB:
            match_data = config.MINING_DB[scanned_sig]
            return True, match_data["name"]
        return False, ""

    def update_ui(self, text_to_display):
        self.ore_label.config(text=text_to_display)

    def automation_loop(self):
        import numpy as np
        import cv2
        import pytesseract
        from mss import mss
        
        current_active_text = ""
        blank_frame_count = 0
        
        last_known_fps = None
        blind_frame_counter = 0
        
        with MSS() as sct:
            while True:
                fps_detected_this_frame = False
                try:
                    sct_img = sct.grab(config.MONITOR_BOX)
                    img = np.array(sct_img)
                    gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                    resized = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
                    _, thresh = cv2.threshold(resized, 125, 255, cv2.THRESH_BINARY)
                    
                    custom_config = r'--psm 6 -c tessedit_char_whitelist=0123456789,'
                    raw_text = pytesseract.image_to_string(thresh, config=custom_config).strip()
                    clean_sig = "".join([char for char in raw_text if char.isdigit()])
                    
                    if len(clean_sig) >= 3:
                        match_found, display_text = self.calculate_ore_match(clean_sig)
                        if match_found:
                            blank_frame_count = 0
                            if display_text != current_active_text:
                                current_active_text = display_text
                                self.update_ui(display_text)
                        else:
                            blank_frame_count += 1
                    else:
                        blank_frame_count += 1

                    if blank_frame_count >= 4:
                        if current_active_text != "":
                            current_active_text = ""
                            self.update_ui("")

                    sct_fps = sct.grab(config.FPS_BOX)
                    img_fps = np.array(sct_fps)
                    gray_fps = cv2.cvtColor(img_fps, cv2.COLOR_BGRA2GRAY)
                    resized_fps = cv2.resize(gray_fps, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
                    _, thresh_fps = cv2.threshold(resized_fps, 120, 255, cv2.THRESH_BINARY)
                    
                    raw_fps_text = pytesseract.image_to_string(thresh_fps, config=r'--psm 6').strip()
                    match = re.search(r'(?:Server\s+FPS:?\s*|FPS:?\s*)(([0-9.]+))', raw_fps_text, re.IGNORECASE)
                    
                    if match and self.panel_ref:
                        fps_val = match.group(1).rstrip('.')
                        if fps_val:
                            clean_whole_fps = fps_val.split('.')[0]
                            if clean_whole_fps:
                                fps_detected_this_frame = True
                                blind_frame_counter = 0
                                last_known_fps = clean_whole_fps
                                self.panel_ref.update_fps_status(clean_whole_fps, force_grey=False)
                                
                except Exception as e:
                    print(f"Loop Error: {e}")
                
                if not fps_detected_this_frame and self.panel_ref:
                    blind_frame_counter += 1
                    if blind_frame_counter < 125 and last_known_fps is not None:
                        self.panel_ref.update_fps_status(last_known_fps, force_grey=False)
                    else:
                        last_known_fps = None
                        self.panel_ref.update_fps_status(None, force_grey=True)
                    
                time.sleep(0.04)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw() 
    active_ui_font = load_custom_font(config.FONT_FILE)
    root.deiconify() 
    
    app = MiningOverlay(root, active_ui_font)
    panel = ConfigPanel(root, app, active_ui_font)
    
    app.panel_ref = panel
    app.start_loop()
    root.mainloop()