#!/usr/bin/env python3

import subprocess
import sys
import shutil
import threading
import json
import os
import tty
import termios
import select

# ─── Colors & Styles ──────────────────────────────────────────────────────────

class C:
    BLUE      = '\033[94m'
    GREEN     = '\033[1;92m'
    YELLOW    = '\033[93m'
    RED       = '\033[91m'
    PURPLE    = '\033[95m'
    CYAN      = '\033[96m'
    WHITE     = '\033[97m'
    DIM       = '\033[2m'
    BOLD      = '\033[1m'
    RESET     = '\033[0m'
    ITALIC    = '\033[3m'
    UNDERLINE = '\033[4m'
    BG_BLUE   = '\033[44m'
    BG_DARK   = '\033[48;5;234m'
    BG_SEL    = '\033[48;5;24m'   # selection highlight
    FG_DARK   = '\033[38;5;240m'

RESET = C.RESET

# ─── Constants ────────────────────────────────────────────────────────────────

FAV_FILE   = os.path.join(os.path.expanduser("~"), ".yt_terminal_favs.json")
KEYMAP_LINES = [
    ("search",    "Type query + Enter"),
    ("fav",       "f  — add to favourites"),
    ("unfav",     "u  — remove current from favs"),
    ("skip",      "Enter — skip / search new"),
    ("quit",      "Ctrl+C — exit"),
    ("nav favs",  "j / k  — navigate fav list"),
    ("play fav",  "p  — play selected fav"),
    ("del fav",   "d  — delete selected fav"),
    ("autoplay",  "auto → next fav after song ends"),
]

# ─── Favourites persistence ───────────────────────────────────────────────────

def load_favs() -> list:
    if os.path.exists(FAV_FILE):
        try:
            with open(FAV_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_favs(favs: list):
    with open(FAV_FILE, "w") as f:
        json.dump(favs, f, indent=2)

# ─── Dependency checker / installer ───────────────────────────────────────────

def check_dependency(cmd: str, install_hint: str, pip_pkg: str | None = None,
                     apt_pkg: str | None = None, brew_pkg: str | None = None) -> bool:
    """Return True if command found, else prompt user to install."""
    if shutil.which(cmd):
        return True

    print(f"\n{C.RED}✗  '{cmd}' is not installed.{RESET}")
    print(f"   {C.YELLOW}{install_hint}{RESET}\n")

    # Offer auto-install where feasible
    if pip_pkg and shutil.which("pip3"):
        ans = input(f"   Auto-install via pip? [y/N]: ").strip().lower()
        if ans == "y":
            subprocess.run([sys.executable, "-m", "pip", "install", pip_pkg])
            if shutil.which(cmd):
                return True

    if apt_pkg and shutil.which("apt"):
        ans = input(f"   Auto-install via apt? [y/N]: ").strip().lower()
        if ans == "y":
            subprocess.run(["sudo", "apt", "install", "-y", apt_pkg])
            if shutil.which(cmd):
                return True

    if brew_pkg and shutil.which("brew"):
        ans = input(f"   Auto-install via brew? [y/N]: ").strip().lower()
        if ans == "y":
            subprocess.run(["brew", "install", brew_pkg])
            if shutil.which(cmd):
                return True

    print(f"   {C.RED}Please install '{cmd}' manually and re-run.{RESET}\n")
    return False

def check_all_deps() -> bool:
    ok = True
    ok &= check_dependency(
        "yt-dlp",
        "Install with:  pip install yt-dlp   OR   brew install yt-dlp",
        pip_pkg="yt-dlp",
        brew_pkg="yt-dlp",
    )
    ok &= check_dependency(
        "mpv",
        "Install with:  sudo apt install mpv   OR   brew install mpv",
        apt_pkg="mpv",
        brew_pkg="mpv",
    )
    return ok

# ─── Terminal helpers ──────────────────────────────────────────────────────────

def term_size():
    return shutil.get_terminal_size()

def move_to(row: int, col: int):
    sys.stdout.write(f"\033[{row};{col}H")

def clear_screen():
    sys.stdout.write("\033[2J")

def hide_cursor():
    sys.stdout.write("\033[?25l")

def show_cursor():
    sys.stdout.write("\033[?25h")

def save_pos():
    sys.stdout.write("\033[s")

def restore_pos():
    sys.stdout.write("\033[u")

# ─── UI Layout ────────────────────────────────────────────────────────────────

FAV_PANEL_WIDTH = 34   # characters wide (right panel)
SIDE_PAD        = 1

class UI:
    """
    Manages the split-terminal layout:
      Left  : main player area
      Right : favourites panel (FAV_PANEL_WIDTH cols)
    """

    def __init__(self):
        self.favs: list       = load_favs()    # [{title, url}]
        self.fav_sel: int     = 0              # selected index in panel
        self.current_title    = ""
        self.current_url      = ""
        self.status_msg       = ""
        self.status_color     = C.CYAN
        self._lock            = threading.Lock()

    # ── Geometry ──────────────────────────────────────────────────────────────

    def cols(self):
        return term_size().columns

    def rows(self):
        return term_size().lines

    def main_width(self):
        return max(20, self.cols() - FAV_PANEL_WIDTH - 1)

    def panel_start_col(self):
        return self.main_width() + 2    # 1-indexed

    # ── Drawing ───────────────────────────────────────────────────────────────

    def redraw_all(self):
        with self._lock:
            sys.stdout.write("\033[?25l")  # hide cursor
            self._draw_banner()
            self._draw_keymap()
            self._draw_divider()
            self._draw_fav_panel()
            self._draw_status()
            sys.stdout.flush()

    def _draw_banner(self):
        banner = [
            r"██╗   ██╗████████╗     ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗     ",
            r"╚██╗ ██╔╝╚══██╔══╝     ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║     ",
            r" ╚████╔╝    ██║           ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║     ",
            r"  ╚██╔╝     ██║           ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║     ",
            r"   ██║      ██║           ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗",
            r"   ╚═╝      ╚═╝           ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝",
            r"                               [ yt-terminal ]  v2.0  >> Developed by kai1ax <<"                     
            ]
        
        for i, line in enumerate(banner):
            move_to(i + 1, 1)
            sys.stdout.write(f"\033[K{C.BLUE}{line}{RESET}")

    def _draw_keymap(self):
        row = 8
        move_to(row, 1)
        sys.stdout.write(f"\033[K{C.BOLD}{C.CYAN}  KEY BINDINGS{RESET}")
        row += 1
        col_w = self.main_width() // 2
        for i, (action, key) in enumerate(KEYMAP_LINES):
            r = row + i // 2
            c = 1 if i % 2 == 0 else col_w
            move_to(r, c)
            sys.stdout.write(
                f"{C.DIM}{C.YELLOW}  {action:<10}{RESET}"
                f"{C.WHITE}{key:<24}{RESET}"
            )
        self._keymap_end_row = row + (len(KEYMAP_LINES) + 1) // 2

    def _draw_divider(self):
        rows = self.rows()
        col  = self.main_width() + 1
        for r in range(1, rows + 1):
            move_to(r, col)
            sys.stdout.write(f"{C.FG_DARK}│{RESET}")

    def _draw_fav_panel(self):
        pc   = self.panel_start_col()
        rows = self.rows()
        pw   = FAV_PANEL_WIDTH - 1

        # Title bar
        title_str = " ★  FAVOURITES "
        move_to(1, pc)
        sys.stdout.write(f"{C.BOLD}{C.YELLOW}{'─' * pw}{RESET}")
        move_to(2, pc)
        sys.stdout.write(f"{C.BOLD}{C.YELLOW}{title_str.center(pw)}{RESET}")
        move_to(3, pc)
        sys.stdout.write(f"{C.YELLOW}{'─' * pw}{RESET}")

        list_start = 4
        list_end   = rows - 4
        visible    = list_end - list_start + 1

        # Scroll window
        offset = max(0, self.fav_sel - visible + 1)
        for i in range(visible):
            idx = i + offset
            move_to(list_start + i, pc)
            if idx < len(self.favs):
                name  = self.favs[idx]["title"]
                short = (name[:pw - 5] + "…") if len(name) > pw - 4 else name
                if idx == self.fav_sel:
                    sys.stdout.write(
                        f"{C.BG_SEL}{C.BOLD}{C.WHITE} ▶ {short:<{pw-3}}{RESET}"
                    )
                else:
                    num   = f"{idx+1:>2}."
                    sys.stdout.write(
                        f"{C.DIM} {num} {RESET}{C.WHITE}{short:<{pw-5}}{RESET}"
                    )
            else:
                sys.stdout.write(" " * pw)

        # Footer hint
        move_to(rows - 3, pc)
        sys.stdout.write(f"{C.YELLOW}{'─' * pw}{RESET}")
        move_to(rows - 2, pc)
        sys.stdout.write(f"{C.DIM}  ↑↓ navigate  p play  d del{RESET}")
        move_to(rows - 1, pc)
        sys.stdout.write(
            f"{C.DIM}  {len(self.favs)} song{'s' if len(self.favs) != 1 else ''} saved{RESET}"
        )

    def _draw_status(self):
        rows = self.rows()
        mw   = self.main_width()

        # Now playing
        np_row = self._keymap_end_row + 2
        move_to(np_row, 1)
        sys.stdout.write(f"\033[K{C.BOLD}{C.CYAN}  NOW PLAYING{RESET}")
        move_to(np_row + 1, 1)
        title = self.current_title or "—"
        short = (title[:mw - 5] + "…") if len(title) > mw - 4 else title
        sys.stdout.write(f"\033[K  {C.BLUE}{C.ITALIC}{short}{RESET}")

        # Status line
        move_to(rows, 1)
        msg = self.status_msg or ""
        sys.stdout.write(f"\033[K  {self.status_color}{msg}{RESET}")

        sys.stdout.write("\033[?25h")  # show cursor (at bottom)

    def set_status(self, msg: str, color: str = C.CYAN):
        self.status_msg   = msg
        self.status_color = color
        self._draw_status()
        sys.stdout.flush()

    def add_fav(self, title: str, url: str):
        for f in self.favs:
            if f["url"] == url:
                self.set_status("★  Already in favourites", C.YELLOW)
                return
        self.favs.append({"title": title, "url": url})
        save_favs(self.favs)
        self.set_status(f"★  Added: {title[:40]}", C.GREEN)
        self._draw_fav_panel()
        sys.stdout.flush()

    def remove_fav_by_url(self, url: str):
        before = len(self.favs)
        self.favs = [f for f in self.favs if f["url"] != url]
        if len(self.favs) < before:
            save_favs(self.favs)
            self.fav_sel = min(self.fav_sel, max(0, len(self.favs) - 1))
            self.set_status("✕  Removed from favourites", C.RED)
            self._draw_fav_panel()
            sys.stdout.flush()
        else:
            self.set_status("Not in favourites", C.YELLOW)

    def remove_selected_fav(self):
        if not self.favs:
            self.set_status("Favourites list is empty", C.YELLOW)
            return
        removed = self.favs.pop(self.fav_sel)
        save_favs(self.favs)
        self.fav_sel = min(self.fav_sel, max(0, len(self.favs) - 1))
        self.set_status(f"✕  Deleted: {removed['title'][:40]}", C.RED)
        self._draw_fav_panel()
        sys.stdout.flush()

    def nav_up(self):
        if self.favs:
            self.fav_sel = (self.fav_sel - 1) % len(self.favs)
            self._draw_fav_panel()
            sys.stdout.flush()

    def nav_down(self):
        if self.favs:
            self.fav_sel = (self.fav_sel + 1) % len(self.favs)
            self._draw_fav_panel()
            sys.stdout.flush()

    def selected_fav(self):
        if self.favs and 0 <= self.fav_sel < len(self.favs):
            return self.favs[self.fav_sel]
        return None

    def next_fav(self, current_url: str):
        """Return next fav after current_url, wrapping around."""
        if not self.favs:
            return None
        urls = [f["url"] for f in self.favs]
        if current_url in urls:
            idx = (urls.index(current_url) + 1) % len(self.favs)
        else:
            idx = 0
        return self.favs[idx]

# ─── Search & Play ────────────────────────────────────────────────────────────

def search_song(query: str, ui: UI):
    ui.set_status(f"⟳  Searching: {query[:50]} …", C.YELLOW)
    try:
        result = subprocess.run(
            ["yt-dlp", f"ytsearch1:{query} song", "-f", "bestaudio",
             "--get-url", "--get-title"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        lines = result.stdout.strip().splitlines()
        if result.returncode != 0 or len(lines) < 2:
            ui.set_status("✕  Nothing found. Try again.", C.RED)
            return None, None

        title = lines[0]
        url   = lines[1]
        ui.current_title = title
        ui.current_url   = url
        ui._draw_status()
        ui.set_status("▶  Playing — f:fav  u:unfav  Enter:skip", C.GREEN)
        return title, url

    except FileNotFoundError:
        ui.set_status("✕  yt-dlp not found!", C.RED)
        sys.exit(1)
    except Exception as e:
        ui.set_status(f"✕  Error: {e}", C.RED)
        return None, None


def play_song(url: str, ui: UI) -> str:
    """
    Play url with mpv.
    Returns reason: 'skip' | 'autoplay' | 'play_fav'
    The caller decides what to do next.
    Listens for keypresses in a non-blocking way.
    """
    action_result = {"reason": "autoplay"}

    try:
        process = subprocess.Popen(
            ["mpv", "--no-video", "--really-quiet", url],
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        ui.set_status("✕  mpv not found!", C.RED)
        sys.exit(1)

    # ── Non-blocking key reader (raw terminal mode) ────────────────────────
    fd   = sys.stdin.fileno()
    old  = termios.tcgetattr(fd)
    done = threading.Event()

    def key_reader():
        try:
            tty.setraw(fd)
            while not done.is_set():
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if not r:
                    continue
                ch = os.read(fd, 1)
                if ch in (b"\r", b"\n"):    # Enter → skip
                    action_result["reason"] = "skip"
                    process.terminate()
                    done.set()
                elif ch == b"k":            # k → nav up
                    ui.nav_up()
                elif ch == b"j":            # j → nav down
                    ui.nav_down()
                elif ch == b"f":            # add fav
                    if ui.current_title and ui.current_url:
                        ui.add_fav(ui.current_title, ui.current_url)
                elif ch == b"u":            # unfav current
                    if ui.current_url:
                        ui.remove_fav_by_url(ui.current_url)
                elif ch == b"p":            # play selected fav
                    fav = ui.selected_fav()
                    if fav:
                        action_result["reason"] = "play_fav"
                        action_result["fav"]    = fav
                        process.terminate()
                        done.set()
                elif ch == b"d":            # delete selected fav
                    ui.remove_selected_fav()
                elif ch == b"\x1b":         # swallow any stray escape sequences
                    # drain up to 2 more bytes so arrow keys don't bleed through
                    for _ in range(2):
                        if sys.stdin in select.select([sys.stdin], [], [], 0.05)[0]:
                            os.read(fd, 1)
                elif ch == b"\x03":         # Ctrl+C
                    process.terminate()
                    done.set()
                    raise KeyboardInterrupt
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    kt = threading.Thread(target=key_reader, daemon=True)
    kt.start()

    process.wait()
    done.set()
    kt.join(timeout=1)

    return action_result

# ─── Search prompt (drawn at bottom of main area) ─────────────────────────────

def draw_search_prompt(ui: UI, partial: str = ""):
    rows = term_size().lines
    move_to(rows - 4, 1)
    label = f"  {C.CYAN}search ❯ {C.WHITE}"
    sys.stdout.write(f"\033[K{label}{partial}")
    sys.stdout.flush()


def get_search_query(ui: UI):
    """
    Line-editing search input drawn in-place.
    When the buffer is empty, j/k/p act as hotkeys (nav/play fav).
    Once the user starts typing a real query they become normal letters.
    Returns:
      str          – a search query to run
      None         – user pressed Enter on empty buffer (no-op, loop again)
      {"play_fav": fav}  – user pressed p with a fav selected
    """
    buf = ""
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        draw_search_prompt(ui, buf)
        while True:
            r, _, _ = select.select([sys.stdin], [], [], 0.05)
            if not r:
                continue
            ch = os.read(fd, 1)

            # ── always-active ──────────────────────────────────────────────
            if ch in (b"\r", b"\n"):
                break
            elif ch == b"\x03":
                raise KeyboardInterrupt
            elif ch == b"\x1b":                        # swallow escape seqs
                for _ in range(2):
                    if sys.stdin in select.select([sys.stdin], [], [], 0.05)[0]:
                        os.read(fd, 1)
            elif ch in (b"\x7f", b"\x08"):             # backspace
                buf = buf[:-1]
                draw_search_prompt(ui, buf)

            # ── hotkeys only when buffer is empty ──────────────────────────
            elif buf == "" and ch == b"k":
                ui.nav_up()
            elif buf == "" and ch == b"j":
                ui.nav_down()
            elif buf == "" and ch == b"p":
                fav = ui.selected_fav()
                if fav:
                    return {"play_fav": fav}
                ui.set_status("Favourites list is empty", C.YELLOW)

            # ── normal typing ──────────────────────────────────────────────
            else:
                try:
                    buf += ch.decode("utf-8")
                except Exception:
                    pass
                draw_search_prompt(ui, buf)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return buf.strip() or None

# ─── Main loop ────────────────────────────────────────────────────────────────

def main():
    if not check_all_deps():
        sys.exit(1)

    clear_screen()
    ui = UI()
    ui.redraw_all()

    last_url = ""

    while True:
        # Show search prompt
        ui.set_status("Type to search  |  j/k navigate favs  |  p play fav", C.DIM)
        draw_search_prompt(ui)

        result = get_search_query(ui)

        # p hotkey pressed from search screen → play fav directly
        if isinstance(result, dict) and "play_fav" in result:
            fav = result["play_fav"]
            ui.current_title = fav["title"]
            ui.current_url   = fav["url"]
            url      = fav["url"]
            last_url = url
            ui._draw_status()
            ui.set_status("▶  Playing fav — f:fav  u:unfav  Enter:skip", C.GREEN)

        elif not result:    # empty input → loop back
            continue

        else:
            # normal search query
            query = result
            title, url = search_song(query, ui)
            if not url:
                continue
            last_url = url
            ui.redraw_all()

        # Play loop (handles autoplay, play_fav, skip)
        while url:
            result = play_song(url, ui)
            reason = result.get("reason", "autoplay")

            if reason == "skip":
                ui.set_status("⏭  Skipped — search a new song", C.YELLOW)
                url = None  # break inner loop → go to search

            elif reason == "play_fav":
                fav = result["fav"]
                ui.current_title = fav["title"]
                ui.current_url   = fav["url"]
                url = fav["url"]
                last_url = url
                ui._draw_status()
                ui.set_status("▶  Playing fav — f:fav  u:unfav  Enter:skip", C.GREEN)

            elif reason == "autoplay":
                # Auto-play next fav after song ends
                next_fav = ui.next_fav(last_url)
                if next_fav:
                    ui.current_title = next_fav["title"]
                    ui.current_url   = next_fav["url"]
                    url      = next_fav["url"]
                    last_url = url
                    ui._draw_status()
                    ui.set_status("▶  Autoplay next fav — Enter to skip", C.PURPLE)
                else:
                    ui.set_status("⏹  Done — search a new song", C.YELLOW)
                    url = None

        ui.redraw_all()

# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        show_cursor()
        print(f"\n{C.YELLOW}  Bye bye ✦{RESET}\n")
        sys.exit(0)