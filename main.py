"""
GitHub Username Checker
A modern GUI application to check GitHub username availability.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import threading
import time
import os
import sys

# ─── Theme ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─── Constants ────────────────────────────────────────────────────────────────
GITHUB_API_URL = "https://api.github.com/users/{}"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "GitHubUsernameChecker/1.0",
}
RATE_LIMIT_WAIT = 35  # seconds to wait on rate limit

# ─── Muezza-inspired Color Palette ────────────────────────────────────────────
BG_PRIMARY    = "#0a0a0f"   # main background
BG_SECONDARY  = "#111118"   # header / panel background
BG_CARD       = "#1a1a24"   # cards / chips
BG_INPUT      = "#13131a"   # input fields
ACCENT        = "#7c5cbf"   # primary purple
ACCENT_HOVER  = "#9370d8"   # lighter purple on hover
ACCENT_LIGHT  = "#a78de0"   # even lighter for highlights
ACCENT_RED    = "#c0392b"
ACCENT_YELLOW = "#d4a017"
BORDER        = "#2a2a3a"   # subtle border
TEXT_PRIMARY  = "#e8e8f0"
TEXT_SECONDARY= "#a0a0b8"
TEXT_MUTED    = "#55556a"
SUCCESS       = "#4caf82"   # green for available
TAG_AVAIL_BG  = "#12201a"
TAG_AVAIL_BOR = "#2a6b4a"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GitHub Username Checker")
        self.geometry("920x700")
        self.minsize(800, 600)
        self.configure(fg_color=BG_PRIMARY)

        # State
        self.usernames: list[str] = []
        self.available: list[str] = []
        self.is_running = False
        self.stop_event = threading.Event()
        self.txt_path: str = ""
        self.checked_count = 0
        self.available_count = 0
        self.unavailable_count = 0

        self._build_ui()

    # ──────────────────────────────────────────── UI BUILD ────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_main()
        self._build_footer()

    # ── Header ──────────────────────────────────────────────────────────────

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=BG_SECONDARY, corner_radius=0, height=66)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=22, pady=14, sticky="w")

        # Lightning bolt icon (matches muezza.at ⚡ style)
        ctk.CTkLabel(
            logo_frame,
            text="⚡",
            font=ctk.CTkFont(size=22),
            text_color=ACCENT_LIGHT,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            logo_frame,
            text="GitHub Username Checker",
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        self.status_badge = ctk.CTkLabel(
            header,
            text="  ● Ready  ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_SECONDARY,
            fg_color=BG_CARD,
            corner_radius=10,
        )
        self.status_badge.grid(row=0, column=2, padx=22, pady=14, sticky="e")

    # ── Main ────────────────────────────────────────────────────────────────

    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        self._build_control_panel(main)
        self._build_results_panel(main)

    # ── Control Panel ───────────────────────────────────────────────────────

    def _build_control_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=BG_SECONDARY, corner_radius=0, height=126)
        panel.grid(row=0, column=0, sticky="ew", pady=(1, 0))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_propagate(False)

        # File row
        file_row = ctk.CTkFrame(panel, fg_color="transparent")
        file_row.grid(row=0, column=0, sticky="ew", padx=22, pady=(16, 8))
        file_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            file_row,
            text="File:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_SECONDARY,
            width=40,
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.file_entry = ctk.CTkEntry(
            file_row,
            placeholder_text="No file selected...",
            font=ctk.CTkFont(size=12),
            fg_color=BG_INPUT,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
            height=36,
            state="readonly",
        )
        self.file_entry.grid(row=0, column=1, padx=(0, 10), sticky="ew")

        ctk.CTkButton(
            file_row,
            text="📂  Browse",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=BG_CARD,
            hover_color=BORDER,
            border_color=BORDER,
            border_width=1,
            text_color=TEXT_PRIMARY,
            height=36,
            width=130,
            command=self._browse_file,
        ).grid(row=0, column=2, sticky="e")

        # Stats + buttons row
        action_row = ctk.CTkFrame(panel, fg_color="transparent")
        action_row.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 16))
        action_row.grid_columnconfigure(0, weight=1)

        stats_frame = ctk.CTkFrame(action_row, fg_color="transparent")
        stats_frame.grid(row=0, column=0, sticky="w")

        self.stat_total      = self._stat_chip(stats_frame, "0", "Total",       TEXT_SECONDARY)
        self.stat_checked    = self._stat_chip(stats_frame, "0", "Checked",     ACCENT_LIGHT)
        self.stat_available  = self._stat_chip(stats_frame, "0", "Available",   SUCCESS)
        self.stat_unavailable= self._stat_chip(stats_frame, "0", "Taken",       ACCENT_RED)

        btn_frame = ctk.CTkFrame(action_row, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        self.btn_clear = ctk.CTkButton(
            btn_frame,
            text="Clear",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=BG_CARD,
            border_color=BORDER,
            border_width=1,
            text_color=TEXT_SECONDARY,
            height=36,
            width=80,
            command=self._clear_results,
        )
        self.btn_clear.pack(side="left", padx=(0, 8))

        self.btn_start = ctk.CTkButton(
            btn_frame,
            text="▶  Start",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#ffffff",
            height=36,
            width=110,
            command=self._toggle_scan,
        )
        self.btn_start.pack(side="left")

    def _stat_chip(self, parent, value, label, color):
        frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=8)
        frame.pack(side="left", padx=(0, 8))

        val_lbl = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=color,
        )
        val_lbl.pack(padx=14, pady=(7, 0))

        ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=10),
            text_color=TEXT_MUTED,
        ).pack(padx=14, pady=(0, 7))

        return val_lbl

    # ── Results Panel ───────────────────────────────────────────────────────

    def _build_results_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")
        panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=14)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        # Header row
        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr,
            text="✅  Available Usernames",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        self.save_label = ctk.CTkLabel(
            hdr,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        )
        self.save_label.grid(row=0, column=1, sticky="e")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            panel,
            progress_color=ACCENT,
            fg_color=BG_CARD,
            height=3,
            corner_radius=2,
        )
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.progress_bar.grid_remove()

        # Scrollable results list
        self.results_frame = ctk.CTkScrollableFrame(
            panel,
            fg_color=BG_SECONDARY,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=TEXT_MUTED,
            corner_radius=10,
        )
        self.results_frame.grid(row=2, column=0, sticky="nsew")

        self.empty_label = ctk.CTkLabel(
            self.results_frame,
            text="No file selected.\nChoose a .txt file with usernames and press Start.",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
            justify="center",
        )
        self.empty_label.pack(expand=True, pady=60)

        # Log line
        self.log_label = ctk.CTkLabel(
            panel,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self.log_label.grid(row=3, column=0, sticky="ew", pady=(6, 0))

    # ── Footer ──────────────────────────────────────────────────────────────

    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color=BG_SECONDARY, corner_radius=0, height=26)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)

        ctk.CTkLabel(
            footer,
            text="GitHub Username Checker  •  No API key required  •  Rate-limit handled automatically",
            font=ctk.CTkFont(size=10),
            text_color=TEXT_MUTED,
        ).place(relx=0.5, rely=0.5, anchor="center")

    # ──────────────────────────────────────────── ACTIONS ─────────────────────

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select username list file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        self.txt_path = path
        self._set_entry_text(self.file_entry, path)
        self._load_usernames(path)

    def _set_entry_text(self, entry, text):
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, text)
        entry.configure(state="readonly")

    def _load_usernames(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f.readlines()]
            self.usernames = [ln for ln in lines if ln and not ln.startswith("#")]
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")
            return

        count = len(self.usernames)
        self.stat_total.configure(text=str(count))
        self._set_log(f"📄  Loaded {count} usernames from: {os.path.basename(path)}")
        self._clear_results(reset_file=False)

    def _toggle_scan(self):
        if self.is_running:
            self._stop_scan()
        else:
            self._start_scan()

    def _start_scan(self):
        if not self.usernames:
            messagebox.showwarning("No Data", "Please select a file first.")
            return

        self.is_running = True
        self.stop_event.clear()
        self.available = []
        self.checked_count = 0
        self.available_count = 0
        self.unavailable_count = 0

        self._clear_results(reset_file=False)
        self.btn_start.configure(text="■  Stop", fg_color=ACCENT_RED, hover_color="#922b21")
        self._update_status("●", "Scanning...", "#c084fc")
        self.progress_bar.grid()
        self.progress_bar.set(0)

        thread = threading.Thread(target=self._scan_worker, daemon=True)
        thread.start()

    def _stop_scan(self):
        self.stop_event.set()
        self.is_running = False
        self.btn_start.configure(text="▶  Start", fg_color=ACCENT, hover_color=ACCENT_HOVER)
        self._update_status("●", "Stopped", ACCENT_YELLOW)
        self._set_log("⏹  Scan stopped.")

    def _scan_worker(self):
        total = len(self.usernames)
        output_path = self._get_output_path()

        for i, username in enumerate(self.usernames):
            if self.stop_event.is_set():
                break

            self._set_log(f"🔍  Checking: {username}  ({i+1}/{total})")
            result = self._check_username(username)

            if result == "available":
                self.available.append(username)
                self.available_count += 1
                self._append_result(username)
                self._save_to_file(username, output_path)
                self.after(0, lambda: self.save_label.configure(
                    text=f"💾  Saved to available.txt  ({self.available_count} found)"
                ))
            elif result == "unavailable":
                self.unavailable_count += 1
            elif result == "rate_limited":
                self._set_log(f"⏳  Rate limited! Waiting {RATE_LIMIT_WAIT}s...")
                self._update_status("●", f"Rate limited – waiting {RATE_LIMIT_WAIT}s...", ACCENT_YELLOW)
                for _ in range(RATE_LIMIT_WAIT):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                if not self.stop_event.is_set():
                    self._update_status("●", "Scanning...", "#c084fc")
                    result2 = self._check_username(username)
                    if result2 == "available":
                        self.available.append(username)
                        self.available_count += 1
                        self._append_result(username)
                        self._save_to_file(username, output_path)
                    elif result2 == "unavailable":
                        self.unavailable_count += 1
                continue
            else:
                self.unavailable_count += 1

            self.checked_count += 1
            progress = (i + 1) / total
            self.after(0, lambda p=progress: self.progress_bar.set(p))
            self.after(0, self._update_stats)
            time.sleep(0.3)

        self.after(0, self._scan_complete)

    def _check_username(self, username: str) -> str:
        """Returns: 'available', 'unavailable', 'rate_limited', 'error'"""
        try:
            resp = requests.get(
                GITHUB_API_URL.format(username),
                headers=HEADERS,
                timeout=10,
            )
            if resp.status_code == 404:
                return "available"
            elif resp.status_code == 200:
                return "unavailable"
            elif resp.status_code in (429, 403):
                return "rate_limited"
            else:
                return "error"
        except requests.exceptions.Timeout:
            return "error"
        except Exception:
            return "error"

    def _scan_complete(self):
        self.is_running = False
        self.btn_start.configure(text="▶  Start", fg_color=ACCENT, hover_color=ACCENT_HOVER)
        self.progress_bar.set(1)
        self._update_status("●", "Done ✓", SUCCESS)
        self._set_log(
            f"✅  Scan complete – {self.available_count} available, "
            f"{self.unavailable_count} taken, {self.checked_count} checked."
        )

    def _append_result(self, username: str):
        self.after(0, lambda u=username: self._add_result_card(u))

    def _add_result_card(self, username: str):
        if self.empty_label.winfo_viewable():
            self.empty_label.pack_forget()

        card = ctk.CTkFrame(
            self.results_frame,
            fg_color=TAG_AVAIL_BG,
            corner_radius=8,
            border_color=TAG_AVAIL_BOR,
            border_width=1,
        )
        card.pack(fill="x", padx=8, pady=3)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="✓",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=SUCCESS,
            width=30,
        ).grid(row=0, column=0, padx=(12, 8), pady=10)

        ctk.CTkLabel(
            card,
            text=username,
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=SUCCESS,
            anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=10)

        ctk.CTkLabel(
            card,
            text="AVAILABLE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#2a9d6a",
            fg_color="#0e2018",
            corner_radius=6,
        ).grid(row=0, column=2, padx=12, pady=10)

        def copy_name():
            self.clipboard_clear()
            self.clipboard_append(username)
            self._set_log(f"📋  '{username}' copied to clipboard.")

        ctk.CTkButton(
            card,
            text="Copy",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color="#1a3025",
            border_color=TAG_AVAIL_BOR,
            border_width=1,
            text_color=SUCCESS,
            height=28,
            width=70,
            command=copy_name,
        ).grid(row=0, column=3, padx=(0, 12), pady=10)

    def _save_to_file(self, username: str, path: str):
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(username + "\n")
        except Exception as e:
            self._set_log(f"⚠  Save error: {e}")

    def _get_output_path(self) -> str:
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, "available.txt")

    def _clear_results(self, reset_file: bool = True):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.empty_label = ctk.CTkLabel(
            self.results_frame,
            text="No results yet.\nStart the scan to find available usernames.",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
            justify="center",
        )
        self.empty_label.pack(expand=True, pady=60)

        if reset_file:
            self.usernames = []
            self._set_entry_text(self.file_entry, "")
            self.txt_path = ""
            self.stat_total.configure(text="0")
            self._update_status("●", "Ready", TEXT_SECONDARY)
            self.save_label.configure(text="")
            self.progress_bar.grid_remove()

        self.available = []
        self.checked_count = 0
        self.available_count = 0
        self.unavailable_count = 0
        self._update_stats()
        self._set_log("")

    def _update_stats(self):
        self.stat_checked.configure(text=str(self.checked_count))
        self.stat_available.configure(text=str(self.available_count))
        self.stat_unavailable.configure(text=str(self.unavailable_count))

    def _set_log(self, text: str):
        self.after(0, lambda: self.log_label.configure(text=text))

    def _update_status(self, icon: str, text: str, color: str):
        self.after(0, lambda: self.status_badge.configure(
            text=f"  {icon} {text}  ",
            text_color=color,
        ))


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
