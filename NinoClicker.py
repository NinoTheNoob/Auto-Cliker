import sys, time, threading, pyautogui, webbrowser, json, os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QLabel, QListWidget, QTabWidget, QSlider, QFrame, QComboBox, QCheckBox, QInputDialog)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject
import Quartz 

# --- MAC-SAFE PERSISTENCE ---
def get_save_path():
    app_dir = Path.home() / "Library" / "Application Support" / "NinoClicker"
    app_dir.mkdir(parents=True, exist_ok=True) 
    return app_dir / "nino_data.json"

SAVE_FILE = get_save_path()

def save_to_disk(data):
    try:
        with open(SAVE_FILE, "w") as f: json.dump(data, f)
    except: pass

def load_from_disk():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f: return json.load(f)
        except: return None
    return None

class Communicate(QObject):
    request_stop = pyqtSignal()

class NinoClicker(QWidget):
    def __init__(self):
        super().__init__()
        
        # 1. DEFAULTS
        self.is_running = False
        self.super_mode = False
        self.click_count = 0 
        self.session_clicks = 0
        self.rgb_on = False
        self.hue = 0
        self.current_profile = "Nino"
        self.active_skin = "#006400" 

        # 2. LOAD DATA
        saved = load_from_disk()
        if saved:
            self.total_lifetime_clicks = saved.get("lifetime", 0)
            self.profiles = saved.get("profiles", {"Nino": {"pts":[], "saves":[], "history":[]}})
            self.achievements = saved.get("achievements", {"noob": False, "pro": False, "god": False})
            self.active_skin = saved.get("skin", "#006400")
        else:
            self.total_lifetime_clicks = 0
            self.profiles = {"Nino": {"pts":[], "saves":[], "history":[]}}
            self.achievements = {"noob": False, "pro": False, "god": False}
        
        # Fix missing keys
        for p in self.profiles:
            for key in ["pts", "saves", "history"]:
                if key not in self.profiles[p]: self.profiles[p][key] = []

        self.comm = Communicate()
        self.comm.request_stop.connect(self.stop_all)
        
        # 3. UI SETUP
        self.setup_ui()
        
        self.panic_timer = QTimer(); self.panic_timer.timeout.connect(self.check_panic_key); self.panic_timer.start(100)
        self.ui_timer = QTimer(); self.ui_timer.timeout.connect(self.update_stats); self.ui_timer.start(1000)
        self.rgb_timer = QTimer(); self.rgb_timer.timeout.connect(self.cycle_rainbow)

    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        
        # Profile Select
        prof_layout = QHBoxLayout()
        self.prof_box = QComboBox()
        for p in self.profiles.keys(): self.prof_box.addItem(p)
        self.prof_box.currentTextChanged.connect(self.switch_profile)
        btn_new_prof = QPushButton("➕ NEW ACC"); btn_new_prof.clicked.connect(self.add_profile)
        prof_layout.addWidget(self.prof_box); prof_layout.addWidget(btn_new_prof)
        self.main_layout.addLayout(prof_layout)

        self.tabs = QTabWidget()

        # TAB: SINGLE
        self.tab1 = QWidget(); t1 = QVBoxLayout()
        self.x_in = QLineEdit(); self.y_in = QLineEdit(); self.cps_in = QLineEdit("10")
        self.super_check = QCheckBox("👹 GOD MODE (DIRECT INJECTION)"); self.super_check.stateChanged.connect(self.set_super)
        self.snipe_single_btn = QPushButton("🎯 SNIPE POSITION (3s)"); self.snipe_single_btn.clicked.connect(self.run_sniper_single)
        self.start_btn = QPushButton("🚀 START SINGLE"); self.start_btn.clicked.connect(self.toggle_single)
        for w in [QLabel("X:"), self.x_in, QLabel("Y:"), self.y_in, QLabel("CPS:"), self.cps_in, self.super_check, self.snipe_single_btn, self.start_btn]: t1.addWidget(w)
        self.tab1.setLayout(t1); self.tabs.addTab(self.tab1, "Single")

        # TAB: MACRO
        self.tab2 = QWidget(); t2 = QVBoxLayout()
        self.macro_list = QListWidget()
        self.snipe_macro_btn = QPushButton("🎯 ADD MACRO POINT (3s)"); self.snipe_macro_btn.clicked.connect(self.run_sniper_macro)
        self.macro_btn = QPushButton("🔥 START MACRO"); self.macro_btn.clicked.connect(self.toggle_macro)
        for w in [QLabel("Points:"), self.macro_list, self.snipe_macro_btn, self.macro_btn]: t2.addWidget(w)
        self.tab2.setLayout(t2); self.tabs.addTab(self.tab2, "Macro")

        # TAB: SPAMMER
        self.tab_spam = QWidget(); t_spam = QVBoxLayout()
        self.msg_in = QLineEdit(); self.spam_delay = QLineEdit("1.0")
        self.spam_btn = QPushButton("📢 START SPAM"); self.spam_btn.clicked.connect(self.toggle_spam)
        for w in [QLabel("Message:"), self.msg_in, QLabel("Delay:"), self.spam_delay, self.spam_btn]: t_spam.addWidget(w)
        self.tab_spam.setLayout(t_spam); self.tabs.addTab(self.tab_spam, "Spammer")

        # TAB: JAR
        self.tab3 = QWidget(); t3 = QVBoxLayout(); self.save_in = QLineEdit(); self.vault = QListWidget()
        btn_save = QPushButton("💾 SAVE"); btn_save.clicked.connect(self.add_save)
        btn_edit = QPushButton("✏️ EDIT"); btn_edit.clicked.connect(self.edit_save)
        t3.addWidget(QLabel("Save Code:")); t3.addWidget(self.save_in); t3.addWidget(btn_save); t3.addWidget(btn_edit); t3.addWidget(self.vault)
        self.tab3.setLayout(t3); self.tabs.addTab(self.tab3, "Jar")

        # TAB: ADVANCED
        self.tab4 = QWidget(); t4 = QVBoxLayout(); self.history_list = QListWidget()
        self.skin_box = QComboBox(); self.skin_box.addItems(["Hacker Green", "Void Purple", "Ruby Red", "Aqua Blue", "Gold Edition"])
        self.skin_box.currentTextChanged.connect(self.change_skin)
        self.rgb_btn = QPushButton("🌈 RAINBOW: OFF"); self.rgb_btn.clicked.connect(self.toggle_rgb)
        self.op_slider = QSlider(Qt.Orientation.Horizontal); self.op_slider.setMinimum(20); self.op_slider.setValue(100); self.op_slider.valueChanged.connect(lambda v: self.setWindowOpacity(v/100))
        for w in [QLabel("Skin:"), self.skin_box, QLabel("History:"), self.history_list, self.rgb_btn, QLabel("Ghost Mode:"), self.op_slider]: t4.addWidget(w)
        self.tab4.setLayout(t4); self.tabs.addTab(self.tab4, "Adv")

        # TAB: STATS
        self.tab5 = QWidget(); ts = QVBoxLayout()
        self.life_label = QLabel(f"📈 Lifetime: {self.total_lifetime_clicks}"); self.sess_label = QLabel("✨ Session: 0")
        self.ach_list = QListWidget()
        ts.addWidget(self.life_label); ts.addWidget(self.sess_label); ts.addWidget(QLabel("Achievements:")); ts.addWidget(self.ach_list)
        self.tab5.setLayout(ts); self.tabs.addTab(self.tab5, "Stats")

        self.main_layout.addWidget(self.tabs)
        self.panic_btn = QPushButton("🛑 PANIC (S)"); self.panic_btn.setFixedHeight(60); self.panic_btn.clicked.connect(self.stop_all)
        self.main_layout.addWidget(self.panic_btn)
        self.setLayout(self.main_layout)
        self.refresh_ui_lists()
        self.apply_styles()

    # --- CORE LOGIC ---
    def quartz_click(self, x, y):
        event = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        event = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

    def work_click(self):
        try:
            x, y = int(self.x_in.text()), int(self.y_in.text())
            if self.super_mode:
                while self.is_running:
                    for _ in range(10): self.quartz_click(x, y)
                    self.click_count += 10; self.session_clicks += 10
                    time.sleep(0.001)
            else:
                d = 1.0/float(self.cps_in.text())
                while self.is_running: pyautogui.click(x, y); self.click_count += 1; self.session_clicks += 1; time.sleep(d)
        except: self.is_running = False

    def work_macro(self):
        pts = self.profiles[self.current_profile]["pts"]
        while self.is_running and pts:
            for px, py in pts:
                if not self.is_running: break
                pyautogui.click(px, py); self.click_count += 1; self.session_clicks += 1; time.sleep(0.5)

    def work_spam(self):
        try:
            msg, d = self.msg_in.text(), float(self.spam_delay.text())
            while self.is_running: pyautogui.write(msg); pyautogui.press('enter'); time.sleep(d)
        except: self.is_running = False

    # --- UI HELPERS ---
    def set_super(self, state): self.super_mode = (state == 2); self.apply_styles()
    def toggle_single(self): self.start_worker(self.work_click, self.start_btn)
    def toggle_macro(self): self.start_worker(self.work_macro, self.macro_btn)
    def toggle_spam(self): self.start_worker(self.work_spam, self.spam_btn)

    def start_worker(self, func, btn):
        self.is_running = not self.is_running
        if self.is_running:
            btn.setText("🛑 STOP"); btn.setStyleSheet("background-color: #8b0000; color: white;")
            threading.Thread(target=func, daemon=True).start()
        else: self.stop_all()

    def stop_all(self):
        if self.is_running:
            self.is_running = False
            self.total_lifetime_clicks += self.click_count
            hist = f"{time.strftime('%H:%M')} - {self.click_count} clicks"
            self.profiles[self.current_profile]["history"].insert(0, hist)
            self.save_state(); self.refresh_ui_lists()
            self.start_btn.setText("🚀 START SINGLE"); self.macro_btn.setText("🔥 START MACRO"); self.spam_btn.setText("📢 START SPAM")
            self.apply_styles(); print(f"Done! Clicked {self.click_count} times."); self.click_count = 0

    def check_panic_key(self):
        if Quartz.CGEventSourceKeyState(Quartz.kCGEventSourceStateCombinedSessionState, 1):
            if self.is_running: self.comm.request_stop.emit()

    def run_sniper_single(self): QTimer.singleShot(3000, self.finish_snipe_single)
    def finish_snipe_single(self): x, y = pyautogui.position(); self.x_in.setText(str(x)); self.y_in.setText(str(y))
    def run_sniper_macro(self): QTimer.singleShot(3000, self.finish_snipe_macro)
    def finish_snipe_macro(self):
        x, y = pyautogui.position(); self.profiles[self.current_profile]["pts"].append((x, y))
        self.refresh_ui_lists(); self.save_state()

    def switch_profile(self, name):
        if name: self.current_profile = name; self.refresh_ui_lists()

    def add_profile(self):
        name, ok = QInputDialog.getText(self, "New Profile", "Name:")
        if ok and name: self.profiles[name] = {"pts":[], "saves":[], "history":[]}; self.prof_box.addItem(name); self.save_state()

    def refresh_ui_lists(self):
        self.macro_list.clear(); self.vault.clear(); self.history_list.clear(); self.ach_list.clear()
        p = self.profiles[self.current_profile]
        for pt in p["pts"]: self.macro_list.addItem(f"Pt: {pt[0]}, {pt[1]}")
        for s in p["saves"]: self.vault.addItem(s)
        for h in p["history"]: self.history_list.addItem(h)
        checks = [("Noob (100+)", 100), ("Clicker (1k+)", 1000), ("Pro (10k+)", 10000), ("God (50k+)", 50000)]
        for n, v in checks: self.ach_list.addItem(f"{'✅' if self.total_lifetime_clicks >= v else '❌'} {n}")

    def add_save(self):
        if self.save_in.text(): self.profiles[self.current_profile]["saves"].append(f"Save_{time.strftime('%H:%M')}: {self.save_in.text()}"); self.save_in.clear(); self.refresh_ui_lists(); self.save_state()

    def edit_save(self):
        row = self.vault.currentRow()
        if row >= 0: self.save_in.setText(self.profiles[self.current_profile]["saves"].pop(row).split(": ", 1)[1]); self.refresh_ui_lists(); self.save_state()

    def change_skin(self, name):
        skins = {"Hacker Green": "#006400", "Void Purple": "#4b0082", "Ruby Red": "#8b0000", "Aqua Blue": "#008b8b", "Gold Edition": "#d4af37"}
        self.active_skin = skins.get(name, "#006400"); self.apply_styles(); self.save_state()

    def apply_styles(self):
        color = "#ff0000" if self.super_mode else self.active_skin
        style = f"QWidget {{ background-color: black; color: white; font-family: 'Courier New'; }} QTabWidget::pane {{ border: 1px solid {color}; }} QLineEdit {{ border: 1px solid {color}; }} QListWidget {{ border: 1px solid {color}; }} QPushButton {{ border: 1px solid {color}; padding: 5px; }}"
        self.setStyleSheet(style)
        self.start_btn.setStyleSheet(f"background-color: {color}; font-weight: bold; border: 1px solid white;")
        self.panic_btn.setStyleSheet("background-color: #610000; font-weight: bold; border: 1px solid white;")

    def toggle_rgb(self):
        self.rgb_on = not self.rgb_on
        if self.rgb_on: self.rgb_timer.start(50); self.rgb_btn.setText("🌈 RAINBOW: ON")
        else: self.rgb_timer.stop(); self.apply_styles(); self.rgb_btn.setText("🌈 RAINBOW: OFF")

    def cycle_rainbow(self): self.hue = (self.hue + 5) % 360; self.setStyleSheet(f"background-color: black; color: white; border: 2px solid hsl({self.hue}, 100%, 50%);")
    def save_state(self): save_to_disk({"lifetime": self.total_lifetime_clicks, "profiles": self.profiles, "achievements": self.achievements, "skin": self.active_skin})
    def update_stats(self): self.life_label.setText(f"📈 Lifetime: {self.total_lifetime_clicks + self.click_count}"); self.sess_label.setText(f"✨ Session: {self.session_clicks}")

if __name__ == "__main__":
    app = QApplication(sys.argv); bot = NinoClicker(); bot.show(); sys.exit(app.exec())