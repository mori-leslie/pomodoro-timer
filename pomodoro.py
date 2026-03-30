import customtkinter as ctk
import subprocess
import random
import signal
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import config
import stats as statsmod

# ── Appearance ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLOR_WORK   = "#e06c75"   # warm red
COLOR_BREAK  = "#98c379"   # soft green
COLOR_LONG   = "#61afef"   # calm blue
COLOR_BG     = "#1e2127"
COLOR_PANEL  = "#282c34"

# ── State ─────────────────────────────────────────────────────────────────────
class PomodoroState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.cycle         = 1        # current pomodoro number (1-based)
        self.session       = "work"   # "work" | "short_break" | "long_break"
        self.running       = False
        self.seconds_left  = config.WORK_MINUTES * 60
        self.mpv_proc      = None
        self._timer_thread = None

    def total_seconds(self):
        if self.session == "work":
            return config.WORK_MINUTES * 60
        elif self.session == "short_break":
            return config.SHORT_BREAK_MINUTES * 60
        else:
            return config.LONG_BREAK_MINUTES * 60

# ── Music ──────────────────────────────────────────────────────────────────────
def start_music(state):
    if state.mpv_proc and state.mpv_proc.poll() is None:
        return  # already playing
    try:
        state.mpv_proc = subprocess.Popen(
            ["lowfi", "--minimalist"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        pass

def stop_music(state):
    if state.mpv_proc and state.mpv_proc.poll() is None:
        state.mpv_proc.terminate()
        state.mpv_proc = None

def skip_music(state):
    """Kill and restart lowfi to jump to next track."""
    stop_music(state)
    start_music(state)

# ── Notifications ──────────────────────────────────────────────────────────────
def notify(title, body):
    try:
        subprocess.Popen(
            ["notify-send", "-u", "normal", "-t", "8000", title, body],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        pass
    # Audio chime as backup
    try:
        subprocess.Popen(
            ["paplay", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        pass

# ── App ────────────────────────────────────────────────────────────────────────
class PomodoroApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.pstate = PomodoroState()
        self._after_id = None  # tracks pending tick callback

        self.title("Pomodoro")
        self.geometry("320x460")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        self._build_ui()
        self._update_display()
        self._refresh_stats()

    # ── UI Construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        self.panel = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=16)
        self.panel.pack(fill="both", expand=True, padx=16, pady=16)

        # Session label
        self.lbl_session = ctk.CTkLabel(
            self.panel, text="FOCUS",
            font=ctk.CTkFont(family="monospace", size=13, weight="bold"),
            text_color=COLOR_WORK
        )
        self.lbl_session.pack(pady=(24, 0))

        # Countdown
        self.lbl_timer = ctk.CTkLabel(
            self.panel, text="25:00",
            font=ctk.CTkFont(family="monospace", size=72, weight="bold"),
            text_color="#ffffff"
        )
        self.lbl_timer.pack(pady=(4, 0))

        # Cycle counter
        self.lbl_cycle = ctk.CTkLabel(
            self.panel, text="Pomodoro  1 / 4",
            font=ctk.CTkFont(size=12),
            text_color="#6b7280"
        )
        self.lbl_cycle.pack(pady=(0, 4))

        # Progress bar
        self.progress = ctk.CTkProgressBar(self.panel, width=240, height=6,
                                           progress_color=COLOR_WORK,
                                           fg_color="#3a3f4b")
        self.progress.set(1.0)
        self.progress.pack(pady=(8, 0))

        # Motivational message
        self.lbl_msg = ctk.CTkLabel(
            self.panel, text=random.choice(config.MOTIVATIONAL_MESSAGES),
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#6b7280", wraplength=260
        )
        self.lbl_msg.pack(pady=(12, 0))

        # Start / Skip music row
        btn_row = ctk.CTkFrame(self.panel, fg_color="transparent")
        btn_row.pack(pady=(20, 0))

        self.btn_start = ctk.CTkButton(
            btn_row, text="Start", width=140, height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLOR_WORK, hover_color="#c0545d",
            command=self._toggle_start
        )
        self.btn_start.grid(row=0, column=0, padx=(0, 8))

        self.btn_skip_music = ctk.CTkButton(
            btn_row, text="⏭", width=44, height=44,
            font=ctk.CTkFont(size=18),
            fg_color="#3a3f4b", hover_color="#4a5060",
            command=self._skip_music
        )
        self.btn_skip_music.grid(row=0, column=1)

        # Skip break button (only visible during breaks)
        self.btn_skip_break = ctk.CTkButton(
            self.panel, text="Skip break →", width=120, height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#3a3f4b", hover_color="#4a5060",
            text_color="#9ca3af",
            command=self._skip_break
        )
        self.btn_skip_break.pack(pady=(10, 0))
        self.btn_skip_break.pack_forget()  # hidden by default

        # Stats row
        stats_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        stats_frame.pack(pady=(16, 0))

        self.lbl_stats = ctk.CTkLabel(
            stats_frame, text="",
            font=ctk.CTkFont(size=11),
            text_color="#6b7280"
        )
        self.lbl_stats.pack()

        # Reset link
        self.btn_reset = ctk.CTkButton(
            self.panel, text="Reset", width=60, height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", hover_color="#3a3f4b",
            text_color="#6b7280",
            command=self._reset
        )
        self.btn_reset.pack(pady=(6, 0))

    # ── Timer Logic ────────────────────────────────────────────────────────────
    def _toggle_start(self):
        if self.pstate.running:
            self._pause()
        else:
            self._start()

    def _start(self):
        self._cancel_tick()
        self.pstate.running = True
        self.btn_start.configure(text="Pause")
        if self.pstate.session == "work":
            start_music(self.pstate)
        self._tick()

    def _pause(self):
        self._cancel_tick()
        self.pstate.running = False
        self.btn_start.configure(text="Resume")
        stop_music(self.pstate)
        notify("Pomodoro paused", "Take a breath — resume when ready.")

    def _cancel_tick(self):
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

    def _tick(self):
        self._after_id = None
        if not self.pstate.running:
            return
        if self.pstate.seconds_left > 0:
            self.pstate.seconds_left -= 1
            self._update_display()
            self._after_id = self.after(1000, self._tick)
        else:
            self._session_complete()

    def _skip_music(self):
        skip_music(self.pstate)

    def _skip_break(self):
        self._cancel_tick()
        self.pstate.running = False
        stop_music(self.pstate)
        self.pstate.session = "work"
        if self.pstate.cycle == 0:
            self.pstate.cycle = 1
        self.pstate.seconds_left = self.pstate.total_seconds()
        self.btn_start.configure(text="Start")
        self._update_display()
        self._start()

    def _refresh_stats(self):
        sessions, minutes, streak = statsmod.get_today_stats()
        flame = " 🔥" if streak > 1 else ""
        self.lbl_stats.configure(
            text=f"Today: {sessions} sessions · {minutes} min   |   Streak: {streak}d{flame}"
        )

    def _session_complete(self):
        self.pstate.running = False
        stop_music(self.pstate)

        if self.pstate.session == "work":
            statsmod.record_session(config.WORK_MINUTES)
            self._refresh_stats()
            notify("Focus session done!", "Time for a well-earned break.")
            if self.pstate.cycle >= config.CYCLES_BEFORE_LONG_BREAK:
                self.pstate.session = "long_break"
                self.pstate.cycle = 0
            else:
                self.pstate.session = "short_break"
        else:
            notify("Break over!", "Back to it — you've got this.")
            if self.pstate.session == "long_break":
                self.pstate.cycle = 1
            else:
                self.pstate.cycle += 1
            self.pstate.session = "work"
            self.lbl_msg.configure(text=random.choice(config.MOTIVATIONAL_MESSAGES))

        self.pstate.seconds_left = self.pstate.total_seconds()
        self._update_display()
        # Auto-start next session
        self._start()

    def _reset(self):
        self._cancel_tick()
        self.pstate.running = False
        stop_music(self.pstate)
        self.pstate.session = "work"
        self.pstate.cycle = 1
        self.pstate.seconds_left = config.WORK_MINUTES * 60
        self.btn_start.configure(text="Start")
        self._update_display()

    # ── Display ────────────────────────────────────────────────────────────────
    def _update_display(self):
        s = self.pstate
        mins, secs = divmod(s.seconds_left, 60)
        self.lbl_timer.configure(text=f"{mins:02d}:{secs:02d}")

        total = s.total_seconds()
        progress = s.seconds_left / total if total > 0 else 1.0
        self.progress.set(progress)

        if s.session == "work":
            color = COLOR_WORK
            label = "FOCUS"
            cycle_text = f"Pomodoro  {s.cycle} / {config.CYCLES_BEFORE_LONG_BREAK}"
        elif s.session == "short_break":
            color = COLOR_BREAK
            label = "SHORT BREAK"
            cycle_text = f"Pomodoro  {s.cycle} / {config.CYCLES_BEFORE_LONG_BREAK}"
        else:
            color = COLOR_LONG
            label = "LONG BREAK"
            cycle_text = "Long break — you earned it"

        self.lbl_session.configure(text=label, text_color=color)
        self.progress.configure(progress_color=color)
        self.btn_start.configure(fg_color=color)
        self.lbl_cycle.configure(text=cycle_text)

        if s.session == "work":
            self.btn_skip_break.pack_forget()
        else:
            self.btn_skip_break.pack(pady=(10, 0))

    def destroy(self):
        stop_music(self.pstate)
        super().destroy()


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = PomodoroApp()
    signal.signal(signal.SIGINT, lambda *_: app.destroy())
    app.mainloop()
