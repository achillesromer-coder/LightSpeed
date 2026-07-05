# Trinity.py — Z+4 (Simulation / Predictive Horizon)
# Drop-in plugin for N.py loader.
#
# Provides:
#  - Scenario presets (left), job queue & status, per-workspace pin-to-lobby
#  - Safe runner for local .py tools (subprocess, captured logs)
#  - Time-horizon slider; persists state ./data/layers/ZP4_trinity.json
#  - Optional telemetry via psutil (CPU/Mem)
#
# Compatible with The Construct (Z) lobby windows out-of-the-box.

from __future__ import annotations

import json, time, threading, subprocess, queue, os, sys, shlex
from dataclasses import dataclass, asdict
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Optional telemetry
try:
    import psutil  # type: ignore
except Exception:
    psutil = None

LAYER_ID    = "ZP4_TRINITY"
LAYER_NAME  = "Z+4 — Trinity"
LAYER_FLOOR = +4

# ---------- Paths ----------
THIS_FILE    = Path(__file__).resolve()
LAUNCHER_DIR = THIS_FILE.parents[1]           # ./Launcher
ROOT         = LAUNCHER_DIR.parent
DATA_DIR     = ROOT / "data" / "layers"; DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE   = DATA_DIR / "ZP4_trinity.json"
WORKSPACES   = ROOT / "workspaces"; WORKSPACES.mkdir(parents=True, exist_ok=True)

# ---------- State ----------
@dataclass
class Job:
    id: str
    title: str
    script: str
    args: list[str]
    horizon_days: int = 30
    status: str = "queued"   # queued | running | done | error | cancelled
    rc: int | None = None
    ts_submit: float = 0.0
    ts_start: float = 0.0
    ts_end: float = 0.0

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Defaults
    return {
        "scenarios": [
            {"title":"Forecast: Orbital Logistics", "script":"", "args":[]},
            {"title":"Monte Carlo: Supply Risk",    "script":"", "args":[]},
            {"title":"Heatmap: EM Field",           "script":"", "args":[]},
        ],
        "jobs": []
    }

def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

# ---------- Lobby pin (compatible with Construct layout) ----------
def _ws_lobby_layout_path(ws: str) -> Path:
    return WORKSPACES / f"z_lobby_{ws or 'default'}.json"

def _pin_to_lobby(workspace: str, title: str, floor: int = LAYER_FLOOR, color: str = "#ef4444"):
    p = _ws_lobby_layout_path(workspace)
    try:
        data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {
            "active_floor":0, "neighbor_visibility":True, "neighbor_opacity":0.7, "windows":[]
        }
    except Exception:
        data = {"active_floor":0,"neighbor_visibility":True,"neighbor_opacity":0.7,"windows":[]}
    wid = f"w{int(time.time()*1000)%1_000_000}"
    data["windows"].append({
        "id": wid,
        "title": f"{title} (queued)",
        "floor": floor,
        "x": 88 + (len(data["windows"])%7)*24,
        "y": 88 + (len(data["windows"])%5)*24,
        "w": 340, "h": 200,
        "color": color,
        "urgency": "blue"
    })
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")

# ---------- Runner ----------
class Runner:
    def __init__(self, text_sink: tk.Text):
        self.text = text_sink
        self.proc: subprocess.Popen | None = None
        self.q = queue.Queue()

    def log(self, line: str):
        try:
            self.text.insert("end", line)
            self.text.see("end")
        except Exception:
            pass

    def _pump(self, pipe, label: str):
        for raw in iter(pipe.readline, b""):
            try:
                self.q.put(f"[{label}] {raw.decode(errors='replace')}")
            except Exception:
                self.q.put(f"[{label}] <decode error>\n")

    def start(self, argv: list[str], on_exit):
        if self.proc:
            self.log("[warn] a job is already running\n")
            return
        try:
            # Use the current venv’s Python where possible
            py = sys.executable or "python"
            cmd = [py, *argv]
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                bufsize=1, universal_newlines=False
            )
        except Exception as e:
            self.log(f"[error] spawn failed: {e}\n")
            on_exit(-1)
            return

        t1 = threading.Thread(target=self._pump, args=(self.proc.stdout, "out"), daemon=True)
        t2 = threading.Thread(target=self._pump, args=(self.proc.stderr, "err"), daemon=True)
        t1.start(); t2.start()

        text_sink = self.text
        def ui_poller():
            try:
                while True:
                    try:
                        line = self.q.get_nowait()
                    except queue.Empty:
                        break
                    self.log(line)
            finally:
                if self.proc and self.proc.poll() is None:
                    text_sink.after(50, ui_poller)
        text_sink.after(50, ui_poller)

        def waiter():
            rc = self.proc.wait()
            on_exit(rc)
            self.proc = None
        threading.Thread(target=waiter, daemon=True).start()

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass

# ---------- UI ----------
def build(app, parent) -> tk.Frame:
    state = _load_state()

    frm = ttk.Frame(parent)
    frm.rowconfigure(1, weight=1)
    frm.columnconfigure(1, weight=1)

    # Header: presets + controls
    hdr = ttk.Frame(frm); hdr.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=6)
    ttk.Label(hdr, text="Scenario").pack(side="left")
    preset_var = tk.StringVar(value=state["scenarios"][0]["title"] if state["scenarios"] else "")
    preset = ttk.Combobox(hdr, width=40, textvariable=preset_var,
                          values=[s["title"] for s in state["scenarios"]])
    preset.pack(side="left", padx=(6,10))

    ttk.Label(hdr, text="Time Horizon (days)").pack(side="left", padx=(8,2))
    horizon = tk.IntVar(value=30)
    ttk.Scale(hdr, from_=1, to=365, variable=horizon, orient="horizontal", length=260).pack(side="left")

    # Buttons
    btn_run   = ttk.Button(hdr, text="Run")
    btn_stop  = ttk.Button(hdr, text="Stop")
    btn_add   = ttk.Button(hdr, text="Add .py…")
    btn_pin   = ttk.Button(hdr, text="Pin to Lobby")
    for b in (btn_run, btn_stop, btn_add, btn_pin):
        b.pack(side="right", padx=4)

    # Left: queue
    left = ttk.Labelframe(frm, text="Queue"); left.grid(row=1, column=0, sticky="ns", padx=8, pady=8)
    cols = ("title","status","rc","submitted")
    tv = ttk.Treeview(left, columns=cols, show="headings", height=18)
    for c, w in (("title",220),("status",90),("rc",50),("submitted",140)):
        tv.heading(c, text=c.capitalize()); tv.column(c, width=w, stretch=False)
    tv.pack(fill="both", expand=False)

    for j in state.get("jobs", []):
        submitted = time.strftime("%Y-%m-%d %H:%M", time.localtime(j.get("ts_submit", 0)))
        tv.insert("", "end", iid=j["id"], values=(j["title"], j["status"], j.get("rc"), submitted))

    # Right: console
    right = ttk.Labelframe(frm, text="Console"); right.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)
    right.rowconfigure(0, weight=1); right.columnconfigure(0, weight=1)
    text = tk.Text(right, wrap="word"); text.grid(row=0, column=0, sticky="nsew")

    runner = Runner(text)

    # Footer: telemetry (optional)
    ftr = ttk.Frame(frm); ftr.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,8))
    stat = ttk.Label(ftr, text="Ready"); stat.pack(side="left")
    def tick():
        if psutil:
            try:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory().percent
                stat.config(text=f"CPU {cpu:.0f}% | RAM {mem:.0f}%")
            except Exception:
                pass
        frm.after(1000, tick)
    frm.after(1000, tick)

    # ---- actions ----
    def add_script():
        p = filedialog.askopenfilename(
            title="Select Python script",
            filetypes=[("Python", "*.py")],
        )
        if not p: return
        title = Path(p).name
        state["scenarios"].append({"title":title, "script":p, "args":[]})
        _save_state(state)
        preset.configure(values=[s["title"] for s in state["scenarios"]])
        preset_var.set(title)

    def enqueue_current(pin=True):
        # Resolve script
        sel = next((s for s in state["scenarios"] if s["title"] == preset_var.get()), None)
        if not sel:
            messagebox.showwarning("No scenario", "Pick or add a scenario first.")
            return
        script = sel.get("script") or ""
        if script == "":
            messagebox.showinfo("Script", "No script path set for this scenario yet.")
            return

        jid = f"j{int(time.time()*1000)%1_000_000}"
        j = Job(
            id=jid, title=sel["title"], script=script, args=list(sel.get("args", [])),
            horizon_days=int(horizon.get()), ts_submit=time.time()
        )
        state.setdefault("jobs", []).append(asdict(j))
        _save_state(state)
        submitted = time.strftime("%Y-%m-%d %H:%M", time.localtime(j.ts_submit))
        tv.insert("", "end", iid=jid, values=(j.title, j.status, j.rc, submitted))
        if pin:
            ws = getattr(getattr(app, "state", None), "workspace_name", "default")
            _pin_to_lobby(ws, j.title)

        # auto-run newest by default
        run_job(jid)

    def run_job(jid: str):
        # Locate job
        jdict = next((x for x in state["jobs"] if x["id"] == jid), None)
        if not jdict:
            return
        if runner.proc:
            messagebox.showwarning("Busy", "Another job is already running.")
            return

        jdict["status"] = "running"; jdict["ts_start"] = time.time(); _save_state(state)
        tv.set(jid, "status", "running")

        argv = [jdict["script"], *jdict.get("args", [])]
        title = jdict["title"]
        runner.log(f"[info] running {title}: {shlex.join(argv)}\n")

        def on_exit(rc: int):
            jdict["rc"] = rc
            jdict["status"] = "done" if rc == 0 else "error"
            jdict["ts_end"] = time.time()
            _save_state(state)
            tv.set(jid, "rc", rc); tv.set(jid, "status", jdict["status"])
            runner.log(f"[info] finished {title} rc={rc}\n")

        runner.start(argv, on_exit)

    def stop_job():
        runner.stop()

    def pin_to_lobby():
        sel = tv.selection()
        title = "Queued run" if not sel else tv.item(sel[0], "values")[0]
        ws = getattr(getattr(app, "state", None), "workspace_name", "default")
        _pin_to_lobby(ws, title)
        messagebox.showinfo("Pinned", f"Pinned “{title}” to Z — The Construct lobby windows.")

    # Button wiring
    btn_add.configure(command=add_script)
    btn_run.configure(command=lambda: enqueue_current(pin=True))
    btn_stop.configure(command=stop_job)
    btn_pin.configure(command=pin_to_lobby)

    # Double-click a queued job to run it
    def on_dclick(evt):
        row = tv.identify_row(evt.y)
        if row:
            run_job(row)
    tv.bind("<Double-1>", on_dclick)

    return frm
