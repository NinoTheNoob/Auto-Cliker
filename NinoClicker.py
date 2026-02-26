import sys, time, threading, pyautogui, webbrowser, json, os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QLabel, QListWidget, QTabWidget, QSlider, QFrame, QComboBox)
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
        self.click_count = 0 
        self.session_clicks = 0
        self.rgb_on = False
        self.hue = 0
        self.current_profile = "Nino"

        # 2. LOAD DATA (WITH ACHIEVEMENT SUPPORT)
        saved = load_from_disk()
        if saved:
            self.total_lifetime_clicks = saved.get("lifetime", 0)
            self.profiles = saved.get("profiles", {"Nino": {"pts":[], "saves":[], "history":[]}})
            self.achievements = saved.get("achievements", {"noob": False, "pro": False, "god": False})
        else:
            self.total_lifetime_clicks = 0
            self.profiles = {"Nino": {"pts":[], "saves":[], "history":[]}}
            self.achievements = {"noob": False, "pro": False, "god": False}
        
        # Fix missing keys in profiles
        for p in self.profiles:
            for key in ["pts", "saves", "history"]:
                if key not in self.profiles[p]: self.profiles[p][key] = []

        self.comm = Communicate()
        self.comm.request_stop.connect(self.stop_all)

        # 3. STYLES
        self.box_style = "border: 1px solid #d3d3d3; color: white; background: transparent; font-family: 'Courier New';"
        self.btn_ready = "background-color: #006400; color: white; border: 1px solid white; padding: 8px; font-weight: bold;"
        self.btn_active = "background-color: #8b0000; color: white; border: 1px solid white; padding: 8px; font-weight: bold;"
        self.btn_normal = "background-color: transparent; color: white; border: 1px solid #7a7a7a; padding: 5px;"

        self.setup_ui()
        
        self.panic_timer = QTimer(); self.panic_timer.timeout.connect(self.check_panic_key); self.panic_timer.start(100)
        self.ui_timer = QTimer(); self.ui_timer.timeout.connect(self.update_stats); self.ui_timer.start(1000)
        self.rgb_timer = QTimer(); self.rgb_timer.timeout.connect(self.cycle_rainbow)

    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        
        # PROFILE SELECTOR
        prof_layout = QHBoxLayout()
        self.prof_box = QComboBox()
        for p in self.profiles.keys(): self.prof_box.addItem(p)
        self.prof_box.currentTextChanged.connect(self.switch_profile)
        btn_new_prof = QPushButton("➕ NEW"); btn_new_prof.clicked.connect(self.add_profile)
        prof_layout.addWidget(QLabel("Account:")); prof_layout.addWidget(self.prof_box); prof_layout.addWidget(btn_new_prof)
        self.main_layout.addLayout(prof_layout)

        self.tabs = QTabWidget()

        # TAB: SINGLE
        self.tab1 = QWidget(); t1 = QVBoxLayout()
        self.x_in = QLineEdit(); self.y_in = QLineEdit(); self.cps_in = QLineEdit("10")
        self.start_btn = QPushButton("🚀 START SINGLE"); self.start_btn.clicked.connect(self.toggle_single)
        for w in [QLabel("X POS:"), self.x_in, QLabel("Y POS:"), self.y_in, QLabel("CPS:"), self.cps_in, self.start_btn]: t1.addWidget(w)
        self.tab1.setLayout(t1); self.tabs.addTab(self.tab1, "Single")

        # TAB: MACRO
        self.tab2 = QWidget(); t2 = QVBoxLayout()
        self.macro_list = QListWidget()
        btn_add_pt = QPushButton("➕ SNIPE POINT"); btn_add_pt.clicked.connect(self.run_sniper_macro)
        self.macro_btn = QPushButton("🔥 START MACRO"); self.macro_btn.clicked.connect(self.toggle_macro)
        for w in [QLabel("Points:"), self.macro_list, btn_add_pt, self.macro_btn]: t2.addWidget(w)
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
        self.rgb_btn = QPushButton("🌈 RAINBOW: OFF"); self.rgb_btn.clicked.connect(self.toggle_rgb)
        self.op_slider = QSlider(Qt.Orientation.Horizontal); self.op_slider.setMinimum(20); self.op_slider.setValue(100); self.op_slider.valueChanged.connect(lambda v: self.setWindowOpacity(v/100))
        for w in [QLabel("History:"), self.history_list, self.rgb_btn, QLabel("Ghost Mode:"), self.op_slider]: t4.addWidget(w)
        self.tab4.setLayout(t4); self.tabs.addTab(self.tab4, "Advanced")

        # TAB: STATS & ACHIEVEMENTS
        self.tab5 = QWidget(); ts = QVBoxLayout()
        self.life_label = QLabel(f"📈 Lifetime: {self.total_lifetime_clicks}")
        self.sess_label = QLabel("✨ Session: 0")
        self.ach_list = QListWidget()
        ts.addWidget(self.life_label); ts.addWidget(self.sess_label); ts.addWidget(QLabel("Achievements:")); ts.addWidget(self.ach_list)
        self.tab5.setLayout(ts); self.tabs.addTab(self.tab5, "Stats")

        self.main_layout.addWidget(self.tabs)
        self.panic_btn = QPushButton("🛑 PANIC (S)"); self.panic_btn.setFixedHeight(60); self.panic_btn.clicked.connect(self.stop_all)
        self.main_layout.addWidget(self.panic_btn)
        
        self.setLayout(self.main_layout)
        self.refresh_ui_lists()
        self.apply_styles()

    def switch_profile(self, name):
        if name:
            self.current_profile = name
            self.refresh_ui_lists()

    def add_profile(self):
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New Profile", "Enter name:")
        if ok and name:
            self.profiles[name] = {"pts":[], "saves":[], "history":[]}
            self.prof_box.addItem(name)
            self.prof_box.setCurrentText(name)
            self.save_state()

    def refresh_ui_lists(self):
        self.macro_list.clear(); self.vault.clear(); self.history_list.clear(); self.ach_list.clear()
        p = self.profiles[self.current_profile]
        for pt in p["pts"]: self.macro_list.addItem(f"Pt: {pt[0]}, {pt[1]}")
        for s in p["saves"]: self.vault.addItem(s)
        for h in p["history"]: self.history_list.addItem(h)
        
        # Check Achievements
        checks = [("Noob (100+)", 100), ("Clicker (1k+)", 1000), ("Pro (10k+)", 10000), ("God (50k+)", 50000)]
        for name, val in checks:
            status = "✅" if self.total_lifetime_clicks >= val else "❌"
            self.ach_list.addItem(f"{status} {name}")

    def apply_styles(self):
        self.setStyleSheet("background-color: black; color: white; font-family: 'Courier New';")
        self.start_btn.setStyleSheet(self.btn_ready); self.panic_btn.setStyleSheet(self.btn_active)
        for i in [self.x_in, self.y_in, self.cps_in, self.msg_in, self.save_in, self.spam_delay]: i.setStyleSheet(self.box_style)
        for l in [self.macro_list, self.vault, self.history_list, self.ach_list]: l.setStyleSheet(self.box_style)

    def check_panic_key(self):
        if Quartz.CGEventSourceKeyState(Quartz.kCGEventSourceStateCombinedSessionState, 1): # 'S' key
            if self.is_running: self.comm.request_stop.emit()

    def stop_all(self):
        if self.is_running:
            self.is_running = False
            self.total_lifetime_clicks += self.click_count
            hist_entry = f"{time.strftime('%H:%M')} - {self.click_count} clicks"
            self.profiles[self.current_profile]["history"].insert(0, hist_entry)
            self.save_state()
            self.refresh_ui_lists()
            self.start_btn.setText("🚀 START"); self.start_btn.setStyleSheet(self.btn_ready)
            print(f"Stopped. Session: {self.click_count}")
            self.click_count = 0

    def toggle_single(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.start_btn.setText("🛑 PANIC"); self.start_btn.setStyleSheet(self.btn_active)
            threading.Thread(target=self.work_click, daemon=True).start()
        else: self.stop_all()

    def work_click(self):
        try:
            x, y, d = int(self.x_in.text()), int(self.y_in.text()), 1.0/float(self.cps_in.text())
            while self.is_running: pyautogui.click(x, y); self.click_count += 1; self.session_clicks += 1; time.sleep(d)
        except: self.is_running = False

    def toggle_macro(self):
        self.is_running = not self.is_running
        if self.is_running: threading.Thread(target=self.work_macro, daemon=True).start()
        else: self.stop_all()

    def work_macro(self):
        pts = self.profiles[self.current_profile]["pts"]
        while self.is_running and pts:
            for px, py in pts:
                if not self.is_running: break
                pyautogui.click(px, py); self.click_count += 1; self.session_clicks += 1; time.sleep(0.5)

    def toggle_spam(self):
        self.is_running = not self.is_running
        if self.is_running: threading.Thread(target=self.work_spam, daemon=True).start()
        else: self.stop_all()

    def work_spam(self):
        try:
            msg, d = self.msg_in.text(), float(self.spam_delay.text())
            while self.is_running: pyautogui.write(msg); pyautogui.press('enter'); time.sleep(d)
        except: self.is_running = False

    def add_save(self):
        code = self.save_in.text()
        if code:
            entry = f"Save_{time.strftime('%H:%M')}: {code}"
            self.profiles[self.current_profile]["saves"].append(entry)
            self.refresh_ui_lists(); self.save_in.clear(); self.save_state()

    def edit_save(self):
        row = self.vault.currentRow()
        if row >= 0:
            text = self.profiles[self.current_profile]["saves"].pop(row)
            self.save_in.setText(text.split(": ", 1)[1])
            self.refresh_ui_lists(); self.save_state()

    def run_sniper_macro(self): QTimer.singleShot(3000, self.finish_snipe_macro)
    def finish_snipe_macro(self):
        x, y = pyautogui.position(); self.profiles[self.current_profile]["pts"].append((x, y))
        self.refresh_ui_lists(); self.save_state()

    def toggle_rgb(self):
        self.rgb_on = not self.rgb_on
        if self.rgb_on: self.rgb_timer.start(50); self.rgb_btn.setText("🌈 RAINBOW: ON")
        else: self.rgb_timer.stop(); self.apply_styles(); self.rgb_btn.setText("🌈 RAINBOW: OFF")

    def cycle_rainbow(self):
        self.hue = (self.hue + 5) % 360
        self.setStyleSheet(f"background-color: black; color: white; border: 2px solid hsl({self.hue}, 100%, 50%);")

    def save_state(self): 
        data = {"lifetime": self.total_lifetime_clicks, "profiles": self.profiles, "achievements": self.achievements}
        save_to_disk(data)
    
    def update_stats(self):
        total = self.total_lifetime_clicks + self.click_count
        self.life_label.setText(f"📈 Lifetime: {total}")
        self.sess_label.setText(f"✨ Session: {self.session_clicks}")

if __name__ == "__main__":
    app = QApplication(sys.argv); bot = NinoClicker(); bot.show(); sys.exit(app.exec())