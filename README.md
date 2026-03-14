# O.B-SEC-AI — AI Pentesting Agent Framework

```
  ██████╗ ██████╗      ███████╗███████╗ ██████╗      █████╗ ██╗
 ██╔═══██╗██╔══██╗     ██╔════╝██╔════╝██╔════╝     ██╔══██╗██║
 ██║   ██║██████╔╝     ███████╗█████╗  ██║          ███████║██║
 ██║   ██║██╔══██╗     ╚════██║██╔══╝  ██║          ██╔══██║██║
 ╚██████╔╝██████╔╝     ███████║███████╗╚██████╗     ██║  ██║██║
  ╚═════╝ ╚═════╝      ╚══════╝╚══════╝ ╚═════╝     ╚═╝  ╚═╝╚═╝
               O . B - S E C - A I
```

> ⚠️ **FOR AUTHORIZED PENETRATION TESTING ONLY** ⚠️  
> By using this tool you confirm you have explicit written permission to test the target systems. The author is not responsible for any misuse.

---

## 🧠 What is OB-SEC-AI?

**OB-SEC-AI** is a self-contained AI-powered penetration testing agent that runs locally on Kali Linux. It launches a sleek, cyberpunk browser-based interface and connects to multiple cutting-edge AI models through [OpenRouter](https://openrouter.ai) to assist with real offensive security workflows — reconnaissance, enumeration, exploitation planning, shell execution, and file operations.

You ask. The AI thinks. The shell executes. Results come back. All in one place.

---

## ✨ Features

- 🤖 **Multi-model AI** — GPT-4o, Claude 3.5 Sonnet, DeepSeek, Venice Uncensored + 15 free fallback models with automatic rotation
- 🐚 **Real shell access** — the AI can run commands directly on your machine, read/write files, and chain tools
- 🖥️ **Browser-based UI** — cyberpunk-themed terminal interface, auto-launches on `http://localhost:6555`
- 🎨 **5 visual themes** — Ghost, Phantom, Specter, Wraith, Oracle
- 🔑 **Multi-key rotation** — add multiple OpenRouter API keys, rotate automatically when quota is hit
- ⚡ **Zero dependencies** — single Python 3 file, uses only stdlib
- 🛠️ **First-run setup wizard** — interactive CLI, runs once, saves config to `~/.config/omar_agent/`
- 🔗 **Alias installer** — creates a global terminal command (e.g. `ghost`, `reaper`) usable anywhere

---

## 🚀 Installation & Usage

### Requirements

- Kali Linux (or any Debian-based distro)
- Python 3.8+
- A free [OpenRouter API key](https://openrouter.ai/keys) (takes 30 seconds to get)

### Run

```bash
git clone https://github.com/omarbouzganda/ob-sec-ai.git
cd ob-sec-ai
python3 ob-sec-ai.py
```

### First Run — Setup Wizard

On first launch, a one-time interactive wizard walks you through 4 steps:

| Step | What happens |
|------|-------------|
| **1 — Name** | Choose your agent name (e.g. `ghost`, `reaper`) — becomes a terminal command |
| **2 — Theme** | Pick a visual theme for the browser UI |
| **3 — API Key** | Paste your OpenRouter key(s) — supports up to 4 keys with rotation |
| **4 — Alias** | Auto-installs a system command so you can type your agent name anywhere |

After setup, just open a new terminal and type your agent name:

```bash
ghost
# or whatever name you chose
```

The browser UI opens automatically at `http://localhost:6555`.

---

## 🤖 Supported AI Models

| Model | Provider | Best For |
|-------|----------|----------|
| GPT-4o | OpenAI | Reasoning & planning |
| Claude 3.5 Sonnet | Anthropic | Analysis & explanations |
| DeepSeek Chat | DeepSeek | Fast & technical |
| Venice Uncensored | Venice | Fewer content restrictions |
| 15+ free fallbacks | Various | Auto-used when quota runs out |

---

## 🎨 Themes

| Theme | Color | Vibe |
|-------|-------|------|
| GHOST | Cyan | Cold, surgical, precise |
| PHANTOM | Red | Aggressive & dangerous |
| SPECTER | Purple | Elite & mysterious |
| WRAITH | Green | Classic terminal hacker |
| ORACLE | Blue | Deep intel, calm power |

---

## 🐚 How the AI Uses Your Shell

The agent has real shell access via XML action tags in its responses:

```xml
<action type="shell">nmap -sV -p- 192.168.1.1</action>
<action type="write" path="/tmp/payload.sh">#!/bin/bash ...</action>
<action type="read" path="/etc/passwd"></action>
```

Results are fed back to the AI automatically — it reads the output and continues reasoning. You get a full loop: **prompt → think → execute → summarize.**

---

## ⚙️ Configuration

Config is stored at `~/.config/omar_agent/config.json`. You can:
- Add more API keys at runtime via the browser UI key manager (⚙ icon)
- Re-run setup by deleting the config file and restarting

---

## ⚠️ Legal Disclaimer

This tool is intended **exclusively** for:
- Authorized penetration testing engagements
- CTF (Capture The Flag) competitions  
- Personal lab environments you own
- Security research with explicit written permission

**Unauthorized use against systems you do not own is illegal.** The author accepts no liability.

---

## 👤 Author

**Omar Bouzganda**  
powered by omar bouzganda · AI Pentesting Agent Framework

---

## ☕ Support & Donations

If this tool helped you, consider supporting the project:

**Bitcoin (BTC):**
```
bc1qex88c788lfmkhsp8djxzn5t5j8w4xq99e0mzf6
```
