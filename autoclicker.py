"""AutoClicker - シンプルな自動クリッカー"""

import signal
import threading
import tkinter as tk
from tkinter import ttk

from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Button, Controller as MouseController

MOUSE_BUTTONS = {
    "Left": Button.left,
    "Right": Button.right,
    "Middle": Button.middle,
}

HOTKEY_START = "F6"    # 開始
HOTKEY_STOP = "F7"     # 停止（常に止まる）


class AutoClicker:
    def __init__(self) -> None:
        self.mouse = MouseController()
        self.clicking = False
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._kb_listener: KeyboardListener | None = None

        self.root = tk.Tk()
        self.root.title("AutoClicker")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._cleanup)

        self._setup_ui()
        self._setup_hotkeys()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        pad = {"padx": 10, "pady": 4}

        # --- Hotkey info ---
        info_frame = ttk.Frame(self.root)
        info_frame.pack(fill="x", padx=10, pady=(8, 0))
        ttk.Label(info_frame, text=f"[{HOTKEY_START}] Start", foreground="gray").pack(side="left")
        ttk.Label(info_frame, text=f"  [{HOTKEY_STOP}] Stop", foreground="red").pack(side="left")

        # --- Click Interval ---
        interval_frame = ttk.LabelFrame(self.root, text="Click Interval")
        interval_frame.pack(fill="x", **pad)

        self.hours = tk.IntVar(value=0)
        self.minutes = tk.IntVar(value=0)
        self.seconds = tk.IntVar(value=0)
        self.milliseconds = tk.IntVar(value=100)

        for col, (label, var, max_val) in enumerate(
            [
                ("Hours", self.hours, 23),
                ("Minutes", self.minutes, 59),
                ("Seconds", self.seconds, 59),
                ("Milliseconds", self.milliseconds, 999),
            ]
        ):
            ttk.Label(interval_frame, text=label).grid(row=0, column=col, padx=6, pady=2)
            ttk.Spinbox(
                interval_frame,
                from_=0,
                to=max_val,
                textvariable=var,
                width=6,
                justify="center",
            ).grid(row=1, column=col, padx=6, pady=4)

        # --- Click Options ---
        options_frame = ttk.LabelFrame(self.root, text="Click Options")
        options_frame.pack(fill="x", **pad)

        ttk.Label(options_frame, text="Button:").grid(row=0, column=0, sticky="w", padx=6, pady=2)
        self.mouse_button = tk.StringVar(value="Left")
        for col, btn in enumerate(["Left", "Right", "Middle"], start=1):
            ttk.Radiobutton(
                options_frame, text=btn, variable=self.mouse_button, value=btn
            ).grid(row=0, column=col, padx=4)

        ttk.Label(options_frame, text="Type:").grid(row=1, column=0, sticky="w", padx=6, pady=2)
        self.click_type = tk.StringVar(value="single")
        ttk.Radiobutton(
            options_frame, text="Single", variable=self.click_type, value="single"
        ).grid(row=1, column=1, padx=4)
        ttk.Radiobutton(
            options_frame, text="Double", variable=self.click_type, value="double"
        ).grid(row=1, column=2, padx=4)

        # --- Repeat ---
        repeat_frame = ttk.LabelFrame(self.root, text="Repeat")
        repeat_frame.pack(fill="x", **pad)

        self.repeat_type = tk.StringVar(value="infinite")
        ttk.Radiobutton(
            repeat_frame,
            text="Repeat until stopped",
            variable=self.repeat_type,
            value="infinite",
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=6, pady=2)

        fixed_row = ttk.Frame(repeat_frame)
        fixed_row.grid(row=1, column=0, sticky="w", padx=6, pady=2)
        ttk.Radiobutton(
            fixed_row, text="Repeat", variable=self.repeat_type, value="fixed"
        ).pack(side="left")
        self.repeat_count = tk.IntVar(value=10)
        ttk.Spinbox(fixed_row, from_=1, to=99999, textvariable=self.repeat_count, width=7).pack(
            side="left", padx=4
        )
        ttk.Label(fixed_row, text="times").pack(side="left")

        # --- Start / Stop buttons ---
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=8)

        self.start_btn = ttk.Button(
            btn_frame,
            text=f"Start  [{HOTKEY_START}]",
            command=self.start,
        )
        self.start_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.stop_btn = ttk.Button(
            btn_frame,
            text=f"Stop  [{HOTKEY_STOP}]",
            command=self.stop,
            state="disabled",
        )
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # --- Always on Top ---
        self.always_on_top = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.root,
            text="Always on Top",
            variable=self.always_on_top,
            command=self._on_always_on_top_changed,
        ).pack(anchor="w", padx=12, pady=(0, 4))

        # --- Status ---
        self.status_var = tk.StringVar(value="Status: Stopped")
        ttk.Label(self.root, textvariable=self.status_var, anchor="center").pack(pady=(0, 8))

    # ------------------------------------------------------------------
    # Hotkeys  (pynput on_press: HotKey クラスと異なり press のみで発火)
    # ------------------------------------------------------------------

    def _setup_hotkeys(self) -> None:
        def on_press(key):
            if key == Key.f6:
                self.start()
            elif key == Key.f7:
                self.stop()

        self._kb_listener = KeyboardListener(on_press=on_press, daemon=True)
        self._kb_listener.start()

    # ------------------------------------------------------------------
    # Click control
    # ------------------------------------------------------------------

    def start(self) -> None:
        with self._lock:
            if not self.clicking:
                self._do_start()

    def stop(self) -> None:
        """緊急停止。常に確実に停止する。"""
        with self._lock:
            if self.clicking:
                self._do_stop()

    def _do_start(self) -> None:
        interval = (
            self.hours.get() * 3600
            + self.minutes.get() * 60
            + self.seconds.get()
            + self.milliseconds.get() / 1000
        )
        if interval <= 0:
            interval = 0.001

        count = None if self.repeat_type.get() == "infinite" else self.repeat_count.get()
        button = MOUSE_BUTTONS[self.mouse_button.get()]
        double = self.click_type.get() == "double"

        self.clicking = True
        self._stop_event.clear()

        threading.Thread(
            target=self._click_loop,
            args=(interval, count, button, double),
            daemon=True,
        ).start()

        self.root.after(0, self._on_started)

    def _do_stop(self) -> None:
        self.clicking = False
        self._stop_event.set()  # Event.wait() を即座に解除

    def _click_loop(self, interval: float, count: int | None, button: Button, double: bool) -> None:
        i = 0
        while not self._stop_event.is_set():
            if count is not None and i >= count:
                break
            self.mouse.click(button, 2 if double else 1)
            i += 1
            # time.sleep の代わりに wait → 停止シグナルに即応
            if self._stop_event.wait(timeout=interval):
                break

        self.clicking = False
        self.root.after(0, self._on_stopped)

    # ------------------------------------------------------------------
    # UI state callbacks
    # ------------------------------------------------------------------

    def _on_always_on_top_changed(self) -> None:
        self.root.attributes("-topmost", self.always_on_top.get())

    def _on_started(self) -> None:
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("Status: Running ...")

    def _on_stopped(self) -> None:
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("Status: Stopped")

    # ------------------------------------------------------------------
    # Cleanup  (×ボタン / Ctrl+C 共通)
    # ------------------------------------------------------------------

    def _cleanup(self) -> None:
        self._stop_event.set()
        self.clicking = False
        if self._kb_listener is not None:
            self._kb_listener.stop()
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = AutoClicker()

    # Ctrl+C (SIGINT) を受け取ったらクリーンアップして終了
    def handle_sigint(sig, frame):
        app._cleanup()

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        app.run()
    except KeyboardInterrupt:
        app._cleanup()


if __name__ == "__main__":
    main()
