<h1 align="center">⚡ GitHub Username Checker</h1>

<p align="center">
  A modern, dark-themed GUI application to check the availability of GitHub usernames in bulk.
  <br />
  <strong>No API key required. No browser windows. No command line.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-purple?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Platform-Windows-purple?style=flat-square&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/GUI-CustomTkinter-purple?style=flat-square" />
  <img src="https://img.shields.io/badge/License-MIT-purple?style=flat-square" />
</p>

---

## ✨ Features

- 📂 **File picker** — select any `.txt` file with one username per line
- 📊 **Live stats** — see Total / Checked / Available / Taken counts update in real time
- ✅ **Instant results** — available usernames appear immediately as they're found
- 💾 **Auto-save** — all available usernames are saved to `available.txt` next to the `.exe`
- 📋 **Copy button** — copy any found username to clipboard with one click
- ⏳ **Rate-limit handling** — automatically waits and retries when GitHub rate-limits you
- ⏹ **Stop & Resume** — stop the scan at any time; restart with the same or a new file
- 🟣 **Clean UI** — dark purple theme inspired by [muezza.at](https://muezza.at)

---

## 🚀 Quick Start (EXE — No Python needed)

1. Go to the [**Releases**](../../releases) page
2. Download `GithubUsernameChecker.exe`
3. Run it — no installation required

> The `.exe` is fully self-contained (built with PyInstaller `--onefile`).  
> The only file it creates at runtime is `available.txt` in the same folder as the `.exe`.

---

## 📋 Username List Format

Create a plain `.txt` file with one username per line:

```
shadowbyte
neonrift
codex42
voidex
```

Lines starting with `#` are treated as comments and skipped.

---

## 🔧 Run from Source

**Requirements:** Python 3.10+

```bash
# 1. Clone the repo
git clone https://github.com/1870s/Github-Username-Checker.git
cd Github-Username-Checker

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

### Build the EXE yourself

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "GithubUsernameChecker" main.py
# Output: dist/GithubUsernameChecker.exe
```

---

## ⚙️ How It Works

The app sends a `GET` request to the GitHub public API for each username:

```
GET https://api.github.com/users/{username}
```

| Response Code | Meaning |
|:---:|:---|
| `404` | ✅ Username is **available** |
| `200` | ❌ Username is **taken** |
| `429` / `403` | ⏳ Rate limited — waits 35s then retries |

No authentication or API token is needed for this endpoint.

---

## 📁 Project Structure

```
Github-Username-Checker/
├── main.py              # Application source code
├── requirements.txt     # Python dependencies
├── .gitignore
└── README.md
```

---

## 🙏 Credits & Inspiration

This project was inspired by [**yTax/Github-Username-Checker**](https://github.com/yTax/Github-Username-Checker) — a CLI tool written in Go for checking GitHub username availability.

The core idea (using GitHub's public API to check 404 vs 200 responses) is the same, but this project is a **complete rewrite** in Python with a custom GUI. No code was taken from the original project.

---

## 📄 License

MIT License — feel free to use, modify and distribute.
