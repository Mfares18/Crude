# Building CrudeAI – Asphaltene Predictor (.exe)

## Prerequisites
- Windows 10/11 (64-bit)
- Python 3.10 or 3.11 (64-bit) — https://www.python.org/downloads/
- Microsoft WebView2 Runtime (already installed on most Windows 11 systems)
  Download if missing: https://developer.microsoft.com/en-us/microsoft-edge/webview2/

## 1. Install dependencies

```bat
pip install -r requirements.txt
```

## 2. Test in development mode

```bat
python main.py
```

The app window should open. Close it to stop.

## 3. Build the .exe

```bat
pyinstaller build.spec
```

The final executable is at:
```
dist\CrudeAI_AsphaltenePredictor.exe
```

### First run after build
Double-click the `.exe`.  
A `models\` folder is created automatically next to it — trained models are saved there at runtime.

## Notes
- `console=False` in the spec means **no black terminal window** appears.
- The app uses your system's EdgeChromium (WebView2) renderer — no bundled browser.
- `data\C1_cleaned.xlsx` and `templates\` are embedded inside the exe.
- If you want to ship an `.ico` icon, uncomment the `icon=` line in `build.spec`.
