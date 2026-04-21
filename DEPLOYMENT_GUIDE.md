# CDR Analytics — Windows Server Deployment Guide
## Running Streamlit Continuously with Auto-Start & Auto-Restart

---

## Prerequisites

Before starting, make sure you have on the server:
- **Python 3.10+** installed ([python.org](https://python.org))
- **pip** (comes with Python)
- Your `app.py` and any supporting files copied to the server

---

## Step 1 — Install dependencies

Open **Command Prompt as Administrator** and run:

```cmd
pip install streamlit pandas openpyxl plotly
```

Test manually first:

```cmd
cd C:\CDR_Dashboard
streamlit run app.py --server.port 8501 --server.headless true
```

Open a browser → `http://localhost:8501` — you should see the dashboard.  
Press `Ctrl+C` to stop it. Now we'll make it run automatically.

---

## Step 2 — Create the launch `.bat` file

Create a file called `start_cdr_dashboard.bat` in `C:\CDR_Dashboard\`:

```bat
@echo off
REM ─────────────────────────────────────────────────────────────
REM  CDR Analytics Dashboard — Launcher
REM  Starts Streamlit and keeps it running if it crashes
REM ─────────────────────────────────────────────────────────────

:START
echo [%DATE% %TIME%] Starting CDR Dashboard... >> C:\CDR_Dashboard\logs\startup.log

cd /d C:\CDR_Dashboard

python -m streamlit run app.py ^
    --server.port 8501 ^
    --server.headless true ^
    --server.enableCORS false ^
    --server.address 0.0.0.0

REM If Streamlit exits for any reason, wait 5 seconds and restart
echo [%DATE% %TIME%] Dashboard stopped. Restarting in 5 seconds... >> C:\CDR_Dashboard\logs\startup.log
timeout /t 5 /nobreak >nul
goto START
```

> **What this does:** The `:START` / `goto START` loop means if Streamlit ever
> crashes or stops, the `.bat` file automatically restarts it after 5 seconds.

Also create the logs folder:

```cmd
mkdir C:\CDR_Dashboard\logs
```

---

## Step 3 — Run in the background (hidden window)

Normally `.bat` files open a visible CMD window. To run silently in the
background, create a second file called `launch_hidden.vbs` in
`C:\CDR_Dashboard\`:

```vbscript
' launch_hidden.vbs — runs the .bat with no visible window
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "C:\CDR_Dashboard\start_cdr_dashboard.bat", 0, False
Set WshShell = Nothing
```

Double-clicking `launch_hidden.vbs` will start the dashboard invisibly.

---

## Step 4 — Auto-start with Windows Task Scheduler

This makes the dashboard start automatically when the server boots.

1. Press `Win + R` → type `taskschd.msc` → press Enter
2. Click **"Create Basic Task…"** in the right panel
3. Fill in:
   - **Name:** `CDR Dashboard Auto-Start`
   - **Description:** Starts the CDR Analytics Streamlit dashboard on boot
4. **Trigger:** Choose **"When the computer starts"**
5. **Action:** Choose **"Start a program"**
6. **Program/script:** Browse to `C:\CDR_Dashboard\launch_hidden.vbs`  
   (or type `wscript.exe`)  
   **Add arguments:** `C:\CDR_Dashboard\launch_hidden.vbs`
7. Click **Finish**
8. Right-click the new task → **Properties**:
   - Check ✅ **"Run whether user is logged on or not"**
   - Check ✅ **"Run with highest privileges"**
   - Under **Settings** tab, check ✅ **"If the task fails, restart every: 1 minute"** (set attempts to 3)
9. Click **OK** — enter your Windows password when prompted

---

## Step 5 — Keep it running if it crashes (double protection)

The `.bat` loop already restarts Streamlit if the Python process dies.
For extra protection, also configure Task Scheduler's **restart on failure**:

In the task Properties → **Settings** tab:
- ✅ If the task fails, restart every: **5 minutes**
- Attempt to restart up to: **99 times**
- ✅ Stop the task if it runs longer than: **(uncheck / set to 0 — no limit)**

---

## Step 6 — Allow firewall access (optional, for network access)

If other computers on the network need to access the dashboard:

```cmd
netsh advfirewall firewall add rule ^
  name="CDR Dashboard" ^
  dir=in ^
  action=allow ^
  protocol=TCP ^
  localport=8501
```

Users on the network access it via: `http://<server-IP>:8501`

---

## Folder structure on the server

```
C:\CDR_Dashboard\
├── app.py                       ← Your Streamlit application
├── start_cdr_dashboard.bat      ← Main launcher with auto-restart loop
├── launch_hidden.vbs            ← Runs the .bat silently (no window)
└── logs\
    └── startup.log              ← Restart/crash log
```

---

## Quick troubleshooting

| Problem | Solution |
|---|---|
| Page not loading | Check `startup.log` for errors. Run `app.py` manually from CMD to see error output. |
| `streamlit` not found | Use full path: `C:\Python311\Scripts\streamlit.exe run app.py` |
| App loads but shows error | Check the technical details box inside the app |
| Task Scheduler not starting it | Make sure "Run with highest privileges" is checked and the user account has permission |
| Port 8501 already in use | Change `--server.port 8501` to `8502` in the `.bat` file |

---

## Testing the full setup

1. Reboot the server
2. Wait ~60 seconds
3. Open a browser → `http://localhost:8501`
4. If it loads — your auto-start is working ✅
