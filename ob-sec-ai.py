#!/usr/bin/env python3
"""
  ██████╗ ██████╗      ███████╗███████╗ ██████╗      █████╗ ██╗
 ██╔═══██╗██╔══██╗     ██╔════╝██╔════╝██╔════╝     ██╔══██╗██║
 ██║   ██║██████╔╝     ███████╗█████╗  ██║          ███████║██║
 ██║   ██║██╔══██╗     ╚════██║██╔══╝  ██║          ██╔══██║██║
 ╚██████╔╝██████╔╝     ███████║███████╗╚██████╗     ██║  ██║██║
  ╚═════╝ ╚═════╝      ╚══════╝╚══════╝ ╚═════╝     ╚═╝  ╚═╝╚═╝
              O . B - S E C - A I

  AI Pentesting Agent Framework
  powered by omar bouzganda
  ⚠  FOR AUTHORIZED PENETRATION TESTING ONLY ⚠

  Run: python3 ob-sec-ai.py
  First run triggers the setup wizard — runs once, never again.
"""

import http.server, json, urllib.request, urllib.error
import subprocess, os, re, shutil, getpass, webbrowser, threading, sys, time

PORT        = 6555
HOME        = os.path.expanduser("~")
USER        = getpass.getuser()
CWD         = [HOME]
SCRIPT_PATH = os.path.abspath(__file__)
CONFIG_DIR  = os.path.join(HOME, ".config", "omar_agent")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
OR_URL      = "https://openrouter.ai/api/v1/chat/completions"

# ── THEMES ─────────────────────────────────────────────────────────────────────
THEMES = {
    "ghost":   {"c0":"#00ffd4","c1":"#ff5e3a","c2":"#a855f7",
                "label":"GHOST   — Cyan  · Cold, surgical, precise"},
    "phantom": {"c0":"#ff3333","c1":"#ff9900","c2":"#cc0044",
                "label":"PHANTOM — Red   · Aggressive & dangerous"},
    "specter": {"c0":"#bf5fff","c1":"#ff2d9b","c2":"#7b2fff",
                "label":"SPECTER — Purple· Elite & mysterious"},
    "wraith":  {"c0":"#00ff41","c1":"#39ff14","c2":"#007a1e",
                "label":"WRAITH  — Green · Classic terminal hacker"},
    "oracle":  {"c0":"#00b4ff","c1":"#3366ff","c2":"#6600ff",
                "label":"ORACLE  — Blue  · Deep intel, calm power"},
}
THEME_KEYS = list(THEMES.keys())

# ── AI MODELS ──────────────────────────────────────────────────────────────────
MODELS_CFG = [
    {"id":"openai/gpt-4o",               "name":"GPT-4o",  "short":"GPT","icon":"⬡","hex":"#00ffd4"},
    {"id":"anthropic/claude-3.5-sonnet", "name":"Claude",  "short":"CLX","icon":"◈","hex":"#ff6b35"},
    {"id":"deepseek/deepseek-chat",      "name":"DeepSeek","short":"DSK","icon":"◎","hex":"#bf5fff"},
    {"id":"venice/uncensored:free",      "name":"Venice",  "short":"VNC","icon":"⟡","hex":"#ff2d9b"},
]

FREE_FALLBACKS = [
    "arcee-ai/trinity-mini:free","nvidia/nemotron-nano-12b-v2-vl:free",
    "qwen/qwen3-vl-30b-a3b-thinking:free","qwen/qwen3-vl-235b-a22b-thinking:free",
    "qwen/qwen3-next-80b-a3b-instruct:free","nvidia/nemotron-nano-9b-v2:free",
    "openai/gpt-oss-120b:free","openai/gpt-oss-20b:free","z-ai/glm-4.5-air:free",
    "qwen/qwen3-coder-480b-a35b:free","venice/uncensored:free",
    "google/gemma-3n-4b:free","qwen/qwen3-4b:free",
    "mistralai/mistral-small-3.1-24b-instruct:free","google/gemma-3-4b-it:free",
]

# ── CONFIG MANAGEMENT ──────────────────────────────────────────────────────────
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"setup_done": False, "agent_name": None, "api_keys": [], "theme": "ghost"}

def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def create_alias(name):
    """
    Write alias to all shell rc files.
    Force-creates ~/.zshrc if it doesn't exist (Kali default shell is zsh).
    Also writes a standalone loader to ~/.local/bin/<cmd> so the alias
    works immediately in new terminals without sourcing.
    """
    cmd  = re.sub(r"[^a-z0-9_-]", "", name.lower())
    line = (
        f"\n# {name.upper()} AI Pentest Agent — Omar Bouzganda\n"
        f'alias {cmd}="python3 {SCRIPT_PATH}"\n'
    )
    written_to = []

    # 1. Write alias to every rc file (create ~/.zshrc if absent — Kali/zsh)
    rc_files = ["~/.bashrc", "~/.zshrc", "~/.bash_profile", "~/.profile"]
    for rc in rc_files:
        rcp = os.path.expanduser(rc)
        try:
            # Create the file if it doesn't exist
            if not os.path.exists(rcp):
                open(rcp, "w").write(f"# Created by {name.upper()} agent setup\n")
            txt = open(rcp).read()
            if f"alias {cmd}=" not in txt:
                open(rcp, "a").write(line)
                written_to.append(rc)
        except Exception:
            pass

    # 2. Drop an executable script into ~/.local/bin/<cmd>
    #    This makes `cmd` work in ANY shell immediately after PATH is set.
    local_bin = os.path.expanduser("~/.local/bin")
    try:
        os.makedirs(local_bin, exist_ok=True)
        bin_path = os.path.join(local_bin, cmd)
        with open(bin_path, "w") as f:
            f.write(f"#!/bin/bash\nexec python3 {SCRIPT_PATH} \"$@\"\n")
        os.chmod(bin_path, 0o755)
        written_to.append(f"~/.local/bin/{cmd}  ← executable (works immediately)")
    except Exception:
        pass

    # 3. Also write to /usr/local/bin if we have permission (system-wide)
    try:
        sys_bin = f"/usr/local/bin/{cmd}"
        with open(sys_bin, "w") as f:
            f.write(f"#!/bin/bash\nexec python3 {SCRIPT_PATH} \"$@\"\n")
        os.chmod(sys_bin, 0o755)
        written_to.append(f"/usr/local/bin/{cmd}  ← system-wide command ✓")
    except Exception:
        pass  # No root — that's fine, ~/.local/bin is enough

    # 4. Ensure ~/.local/bin is in PATH for rc files
    path_line = '\nexport PATH="$HOME/.local/bin:$PATH"\n'
    for rc in ["~/.bashrc", "~/.zshrc"]:
        rcp = os.path.expanduser(rc)
        try:
            txt = open(rcp).read()
            if ".local/bin" not in txt:
                open(rcp, "a").write(path_line)
        except Exception:
            pass

    return cmd, written_to

# ── TERMINAL COLORS ────────────────────────────────────────────────────────────
R  = "\033[91m"; G  = "\033[92m"; Y  = "\033[93m"
B  = "\033[94m"; M  = "\033[95m"; C  = "\033[96m"
DIM = "\033[2m"; BLD = "\033[1m"; RST = "\033[0m"
THEME_TCOLORS = [C, R, M, G, B]

def clr():
    os.system("clear" if os.name == "posix" else "cls")

def typer(text, delay=0.018, nl=True):
    for ch in text:
        sys.stdout.write(ch); sys.stdout.flush(); time.sleep(delay)
    if nl: print()

def pulse_line(char="▓", width=52, color=C, delay=0.012):
    for i in range(width):
        sys.stdout.write(f"\r{color}{'█' * i}{DIM}{'░' * (width-i)}{RST}")
        sys.stdout.flush(); time.sleep(delay)
    print(f"\r{color}{'█' * width}{RST}")

# ── FIRST RUN SETUP WIZARD ─────────────────────────────────────────────────────
def first_run_setup():
    clr()
    time.sleep(0.2)

    # ── Scary boot art ────────────────────────────────────────────────────
    print(f"{R}")
    print("  ██████╗ ██████╗      ███████╗███████╗ ██████╗      █████╗ ██╗")
    print(" ██╔═══██╗██╔══██╗     ██╔════╝██╔════╝██╔════╝     ██╔══██╗██║")
    print(" ██║   ██║██████╔╝     ███████╗█████╗  ██║          ███████║██║")
    print(" ██║   ██║██╔══██╗     ╚════██║██╔══╝  ██║          ██╔══██║██║")
    print(" ╚██████╔╝██████╔╝     ███████║███████╗╚██████╗     ██║  ██║██║")
    print("  ╚═════╝ ╚═════╝      ╚══════╝╚══════╝ ╚═════╝     ╚═╝  ╚═╝╚═╝")
    print(f"               {R}O . B - S E C - A I{RST}{R}")
    print(f"{RST}")
    print(f"  {DIM}╔══════════════════════════════════════════════════════╗")
    print(f"  ║  AI Pentesting Agent Framework                       ║")
    print(f"  ║  powered by omar bouzganda                           ║")
    print(f"  ║  ⚠  FOR AUTHORIZED PENETRATION TESTING ONLY  ⚠      ║")
    print(f"  ╚══════════════════════════════════════════════════════╝{RST}")
    print()
    typer(f"  {Y}[!] FIRST RUN DETECTED — INITIATING AGENT SETUP PROTOCOL{RST}", 0.022)
    typer(f"  {DIM}[*] This wizard runs only once. Config saved to:{RST}", 0.015)
    typer(f"  {DIM}    {CONFIG_FILE}{RST}", 0.010)
    print()
    input(f"  {DIM}Press ENTER to begin > {RST}")

    # ── STEP 1: AGENT NAME ────────────────────────────────────────────────
    clr()
    print(f"\n  {C}╔═══════════════════════════════════════════════════╗")
    print(f"  ║  SETUP [1/4] — NAME YOUR AI AGENT               ║")
    print(f"  ║  This becomes a command you can run anywhere     ║")
    print(f"  ╚═══════════════════════════════════════════════════╝{RST}\n")
    print(f"  {DIM}Ideas: ghost, reaper, shadow, daemon, venom, cipher{RST}\n")

    while True:
        name = input(f"  {C}Agent name > {RST}").strip()
        if re.match(r"^[a-zA-Z][a-zA-Z0-9_-]{1,19}$", name):
            break
        print(f"  {R}[!] 2-20 chars, start with letter, no spaces{RST}")

    name_up = name.upper()
    w = len(name_up) + 8
    print(f"\n  {G}[+] Your agent will be called: {BLD}{name_up}{RST}")
    print(f"\n  {C}  ╔{'═'*w}╗")
    print(f"  ║    {name_up}    ║")
    print(f"  ╚{'═'*w}╝{RST}")
    print(f"\n  {DIM}Terminal command: {name.lower()}{RST}")
    time.sleep(0.3)
    pulse_line(width=44, color=C, delay=0.008)
    time.sleep(0.3)

    # ── STEP 2: THEME ─────────────────────────────────────────────────────
    clr()
    print(f"\n  {C}╔═══════════════════════════════════════════════════╗")
    print(f"  ║  SETUP [2/4] — CHOOSE YOUR VISUAL THEME         ║")
    print(f"  ╚═══════════════════════════════════════════════════╝{RST}\n")

    for i, (k, v) in enumerate(THEMES.items()):
        print(f"  {THEME_TCOLORS[i]}  [{i+1}] {v['label']}{RST}")

    print()
    while True:
        ch = input(f"  {C}Theme [1-5] > {RST}").strip()
        if ch in [str(i+1) for i in range(5)]:
            theme = THEME_KEYS[int(ch)-1]; break
        print(f"  {R}[!] Enter a number 1-5{RST}")

    tc = THEME_TCOLORS[int(ch)-1]
    print(f"\n  {G}[+] Theme: {tc}{BLD}{theme.upper()}{RST}{G} — locked in{RST}\n")
    pulse_line(width=44, color=tc, delay=0.008)
    time.sleep(0.3)

    # ── STEP 3: API KEY ───────────────────────────────────────────────────
    clr()
    print(f"\n  {C}╔═══════════════════════════════════════════════════╗")
    print(f"  ║  SETUP [3/4] — OPENROUTER API KEY               ║")
    print(f"  ║  Get a free key at: openrouter.ai/keys          ║")
    print(f"  ╚═══════════════════════════════════════════════════╝{RST}\n")
    print(f"  {DIM}OpenRouter gives you access to GPT · Claude · DeepSeek and")
    print(f"  dozens of free fallback models with auto-rotation.{RST}\n")

    keys = []
    while True:
        k = input(f"  {C}Primary key (sk-or-...) > {RST}").strip()
        if k.startswith("sk-") and len(k) > 20:
            keys.append(k); break
        if k:
            print(f"  {R}[!] Invalid format. Keys start with 'sk-or-'{RST}")
        else:
            print(f"  {R}[!] A key is required. Get one free at openrouter.ai/keys{RST}")

    print(f"\n  {DIM}Add more keys for rotation (press ENTER to skip){RST}")
    for i in range(2, 5):
        extra = input(f"  {DIM}Key {i} (optional) > {RST}").strip()
        if not extra: break
        if extra.startswith("sk-") and len(extra) > 20:
            keys.append(extra)
            print(f"  {G}  [+] Key {i} added{RST}")

    print(f"\n  {G}[+] {len(keys)} key(s) configured with auto-rotation{RST}\n")
    pulse_line(width=44, color=G, delay=0.008)
    time.sleep(0.3)

    # ── STEP 4: CREATE ALIAS ──────────────────────────────────────────────
    clr()
    print(f"\n  {C}╔═══════════════════════════════════════════════════╗")
    print(f"  ║  SETUP [4/4] — CREATING TERMINAL COMMAND        ║")
    print(f"  ╚═══════════════════════════════════════════════════╝{RST}\n")

    typer(f"  {DIM}[*] Writing alias to shell config...{RST}", 0.020)
    cmd, written_to = create_alias(name)
    time.sleep(0.4)

    if written_to:
        for dest in written_to:
            print(f"  {G}[+] Written → {dest}{RST}")
    print()

    # Check if /usr/local/bin was written (system-wide)
    sys_bin = f"/usr/local/bin/{cmd}"
    if os.path.exists(sys_bin):
        print(f"  {G}{BLD}[✓] Command '{cmd}' is READY — open a new terminal and type: {cmd}{RST}")
    else:
        print(f"  {Y}[~] Open a new terminal and type: {cmd}{RST}")
        print(f"  {DIM}    OR in this terminal: source ~/.zshrc && {cmd}{RST}")

    # ── Save ──────────────────────────────────────────────────────────────
    cfg = {
        "setup_done": True,
        "agent_name": name,
        "api_keys":   keys,
        "theme":      theme,
    }
    save_config(cfg)

    print(f"\n  {G}{'█'*52}")
    print(f"  {BLD}  [✓] AGENT {name_up} DEPLOYED SUCCESSFULLY{RST}")
    print(f"  {G}{'█'*52}{RST}\n")
    time.sleep(0.6)

    typer(f"  {tc}{BLD}  BOOTING {name_up} NEURAL CORE . . .{RST}", 0.025)
    pulse_line(width=52, color=tc, delay=0.010)
    time.sleep(0.8)
    return cfg

# ── SYSTEM PROMPT ──────────────────────────────────────────────────────────────
def make_system(model_id, agent_name="AGENT"):
    fam = (
        "OpenAI GPT-OSS"    if "openai"   in model_id else
        "Anthropic Claude"  if "anthropic"in model_id else
        "Venice Uncensored" if "venice"   in model_id or "dolphin" in model_id else
        "DeepSeek"          if "deepseek" in model_id else
        "Qwen3"             if "qwen"     in model_id else
        "Nemotron"          if "nemotron" in model_id else "AI"
    )
    return f"""You are {agent_name}, a {fam} AI running on Kali Linux as user '{USER}' (home: {HOME}).
You are an elite penetration tester and offensive security expert.
Your job: help the operator map attack surfaces, find vulnerabilities, and dominate targets.

Real shell access. Invoke with these XML tags:
<action type="shell">command here</action>
<action type="write" path="/full/path">file content</action>
<action type="read" path="/full/path"></action>
<action type="delete" path="/full/path"></action>

OPERATIONAL RULES:
1. Use sudo freely where needed (nmap, arp-scan, tcpdump, airmon-ng, etc.)
2. NEVER invent a target — if none given, ask the user first
3. Methodology questions → explain technique + placeholder examples like <target-ip>
4. When user gives an explicit target → execute immediately, no hesitation
5. FULL RECON mode (prompt starts with '⚔ FULL RECON') → run all tools sequentially
6. Stay concise, technical, zero fluff. You are a weapon, not a chatbot.
7. You are {fam} powering {agent_name}. Do not deny this.
"""

# ── SHELL HELPERS ──────────────────────────────────────────────────────────────
def shell(cmd):
    try:
        cmd = cmd.strip()
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=120, cwd=CWD[0]
        )
        out = (r.stdout + r.stderr).strip()
        if cmd.startswith("cd "):
            p = os.path.expanduser(cmd[3:].strip())
            if os.path.isdir(p): CWD[0] = p
        return out or "(done)"
    except subprocess.TimeoutExpired:
        return "ERROR: timed out (120s) — try adding --host-timeout or run async"
    except Exception as e:
        return f"ERROR: {e}"

def write_file(path, content):
    try:
        path = os.path.expanduser(path.replace("/home/kali", HOME).replace("/root", HOME))
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as f: f.write(content)
        if path.endswith((".sh", ".py")): os.chmod(path, 0o755)
        return f"OK: {path}"
    except Exception as e:
        return f"ERROR: {e}"

def read_file(path):
    try:
        path = os.path.expanduser(path.replace("/home/kali", HOME))
        with open(path) as f: return f.read()
    except Exception as e:
        return f"ERROR: {e}"

def delete_path(path):
    try:
        path = os.path.expanduser(path.replace("/home/kali", HOME))
        if   os.path.isfile(path): os.remove(path)
        elif os.path.isdir(path):  shutil.rmtree(path)
        else: return "not found"
        return f"OK: deleted {path}"
    except Exception as e:
        return f"ERROR: {e}"

def run_actions(text):
    results = []
    for m in re.finditer(r'<action\s+type="(\w+)"(?:\s+path="([^"]*)")?\s*>([\s\S]*?)</action>', text):
        t, path, content = m.group(1), m.group(2) or "", m.group(3).strip()
        if   t == "shell":  out = shell(content)
        elif t == "write":  out = write_file(path, content)
        elif t == "read":   out = read_file(path)
        elif t == "delete": out = delete_path(path)
        else: out = "unknown action"
        results.append({"type": t, "target": path or content[:60], "result": out})
        print(f"  \033[93m[{t.upper()}]\033[0m {(path or content)[:55]} → {out[:70]}")
    return results

# ── AI CALL WITH FALLBACK ──────────────────────────────────────────────────────
def call_ai(messages, model_id, keys, agent_name="AGENT"):
    models = [model_id] + [m for m in FREE_FALLBACKS if m != model_id]
    print(f"  \033[96mPrimary: {model_id.split('/')[-1][:30]} | {len(models)-1} fallbacks\033[0m")

    for model in models:
        short = model.split("/")[-1][:28]
        skip  = False
        for key in keys:
            try:
                data = json.dumps({
                    "model": model, "messages": messages,
                    "max_tokens": 2048, "stream": False
                }).encode()
                req = urllib.request.Request(OR_URL, data=data, headers={
                    "Authorization":  f"Bearer {key}",
                    "Content-Type":   "application/json",
                    "HTTP-Referer":   f"http://localhost:{PORT}",
                    "X-Title":        f"{agent_name} AI",
                }, method="POST")
                with urllib.request.urlopen(req, timeout=45) as r:
                    d = json.loads(r.read())

                if "error" in d:
                    code = str(d["error"].get("code", ""))
                    msg  = d["error"].get("message", "")[:80]
                    print(f"  \033[91m[ERR]\033[0m {short}: {code}")
                    if any(x in code or x in msg.lower()
                           for x in ["402","404","not found","credits","no endpoints"]):
                        break
                    if "429" in code or "rate" in msg.lower(): break
                    continue

                text = d["choices"][0]["message"]["content"]
                text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
                print(f"  \033[92m[OK]\033[0m {short}")
                return text, model

            except urllib.error.HTTPError as e:
                try: e.read()
                except: pass
                print(f"  \033[91m[SKIP]\033[0m {short} HTTP {e.code}")
                if e.code in (400, 402, 404): skip = True; break
                if e.code == 429: continue
                skip = True; break
            except Exception as e:
                print(f"  \033[91m[SKIP]\033[0m {short}: {str(e)[:40]}")
                continue
        if skip: continue

    raise Exception(
        "All AI models are currently unavailable.\n"
        "• If you're on the free tier: daily quota reached — come back tomorrow (resets midnight UTC)\n"
        "• To get more requests now: add $5 credit at openrouter.ai/keys → 1,000 req/day\n"
        "• Or add another free key via the ⚙ key manager in the browser"
    )

# ── HTML GENERATOR ─────────────────────────────────────────────────────────────
def make_html(cfg):
    agent  = cfg.get("agent_name", "AGENT").upper()
    agent_lower = agent.lower()
    theme  = THEMES.get(cfg.get("theme", "ghost"), THEMES["ghost"])
    c0, c1, c2 = theme["c0"], theme["c1"], theme["c2"]

    # Mask keys for browser display
    keys   = cfg.get("api_keys", [])
    keys_js = json.dumps([
        {"label": f"Key {i+1}", "val": k}
        for i, k in enumerate(keys)
    ])
    models_js = json.dumps(MODELS_CFG)

    # Build HTML by replacing placeholder tokens in the raw template
    html = _HTML_TEMPLATE
    html = html.replace("%%AGENT%%",      agent)
    html = html.replace("%%AGENT_LOWER%%",agent_lower)
    html = html.replace("%%C0%%",         c0)
    html = html.replace("%%C1%%",         c1)
    html = html.replace("%%C2%%",         c2)
    html = html.replace("%%KEYS_JS%%",    keys_js)
    html = html.replace("%%MODELS_JS%%",  models_js)
    html = html.replace("%%PORT%%",       str(PORT))
    return html

# ── HTML TEMPLATE ──────────────────────────────────────────────────────────────
# Placeholders: %%AGENT%%, %%AGENT_LOWER%%, %%C0%%, %%C1%%, %%C2%%,
#               %%KEYS_JS%%, %%MODELS_JS%%, %%PORT%%
_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%%AGENT%%://NET</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;cursor:none!important}
:root{
  --void:#020208;--deep:#05050f;--card:#08081a;--panel:#0b0b1e;
  --line:#0e0e26;--dim:#161630;--glow:#1d1d44;
  --fg:#cccce8;--muted:#333355;--faint:#090914;
  --c0:%%C0%%;--c1:%%C1%%;--c2:%%C2%%;
  --font:'Rajdhani',sans-serif;
  --mono:'Share Tech Mono',monospace;
  --display:'Orbitron',sans-serif;
}

/* ===== CURSOR ===== */
#cur{position:fixed;width:10px;height:10px;border-radius:50%;
  background:var(--c0);pointer-events:none;z-index:99999;
  transform:translate(-50%,-50%);mix-blend-mode:screen;
  box-shadow:0 0 10px var(--c0),0 0 24px var(--c0)40;
  transition:width .1s,height .1s,background .2s;}
#cur2{position:fixed;width:38px;height:38px;border-radius:50%;
  border:1px solid color-mix(in srgb,var(--c0) 40%,transparent);
  pointer-events:none;z-index:99998;transform:translate(-50%,-50%);
  transition:all .09s linear;mix-blend-mode:screen;}
body:has(button:hover) #cur,body:has(a:hover) #cur{width:22px;height:22px;background:var(--c1)}

/* ===== BASE ===== */
html,body{height:100%;overflow:hidden;background:var(--void);color:var(--fg);font-family:var(--font)}

/* ===== BACKGROUND ===== */
.bg{position:fixed;inset:0;z-index:0;overflow:hidden}
.bg-base{position:absolute;inset:0;
  background:
    radial-gradient(ellipse 120% 80% at 15% -10%,color-mix(in srgb,var(--c0) 5%,transparent) 0%,transparent 55%),
    radial-gradient(ellipse 80% 100% at 90% 110%,color-mix(in srgb,var(--c2) 6%,transparent) 0%,transparent 55%),
    radial-gradient(ellipse 60% 60% at 50% 50%,color-mix(in srgb,var(--c1) 3%,transparent) 0%,transparent 60%),
    var(--void);}
.orb{position:absolute;border-radius:50%;filter:blur(90px);pointer-events:none}
.o1{width:700px;height:700px;background:radial-gradient(circle,color-mix(in srgb,var(--c0) 12%,transparent),transparent 70%);
  top:-20%;left:-10%;animation:ob1 18s ease-in-out infinite alternate}
.o2{width:600px;height:600px;background:radial-gradient(circle,color-mix(in srgb,var(--c2) 10%,transparent),transparent 70%);
  bottom:-15%;right:-8%;animation:ob2 24s ease-in-out infinite alternate}
.o3{width:400px;height:400px;background:radial-gradient(circle,color-mix(in srgb,var(--c1) 7%,transparent),transparent 70%);
  top:40%;left:35%;animation:ob3 30s ease-in-out infinite alternate}
@keyframes ob1{0%{transform:translate(0,0) scale(1)}50%{transform:translate(60px,-40px) scale(1.1)}100%{transform:translate(-30px,60px) scale(.95)}}
@keyframes ob2{0%{transform:translate(0,0) scale(1)}50%{transform:translate(-50px,30px) scale(1.15)}100%{transform:translate(40px,-50px) scale(.9)}}
@keyframes ob3{0%{transform:translate(0,0) scale(1)}100%{transform:translate(-60px,40px) scale(1.2)}}
.bg-grid{position:absolute;inset:0;
  background-image:
    linear-gradient(color-mix(in srgb,var(--c0) 2.5%,transparent) 1px,transparent 1px),
    linear-gradient(90deg,color-mix(in srgb,var(--c0) 2.5%,transparent) 1px,transparent 1px);
  background-size:50px 50px;animation:gridflow 25s linear infinite;}
@keyframes gridflow{0%{background-position:0 0}100%{background-position:50px 50px}}
.bg-noise{position:absolute;inset:0;opacity:.03;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size:200px;}
.scanlines{position:absolute;inset:0;pointer-events:none;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.06) 2px,rgba(0,0,0,.06) 4px);}
#pcanvas{position:fixed;inset:0;z-index:0;pointer-events:none}

/* ===== BOOT SCREEN ===== */
#boot{
  position:fixed;inset:0;z-index:9000;background:var(--void);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  font-family:var(--mono);
}
#boot.fade-out{animation:bootfade .8s forwards}
@keyframes bootfade{0%{opacity:1}100%{opacity:0;pointer-events:none;display:none}}
.boot-logo{
  font-family:var(--display);font-size:clamp(28px,5vw,56px);font-weight:900;
  letter-spacing:.3em;margin-bottom:10px;
  color:var(--c0);
  text-shadow:0 0 30px var(--c0),0 0 60px color-mix(in srgb,var(--c0) 40%,transparent);
  animation:glitch1 6s ease infinite;
}
@keyframes glitch1{
  0%,87%,89%,91%,100%{text-shadow:0 0 30px var(--c0),0 0 60px color-mix(in srgb,var(--c0) 40%,transparent)}
  88%{text-shadow:-3px 0 var(--c1),3px 0 var(--c2),0 0 30px var(--c0)}
  90%{text-shadow:2px 0 var(--c2),-2px 0 var(--c1),0 0 30px var(--c0)}
}
.boot-sub{font-size:11px;letter-spacing:.3em;color:var(--muted);margin-bottom:40px}
.boot-bar-wrap{width:300px;height:2px;background:var(--dim);border-radius:2px;margin-bottom:30px;overflow:hidden}
.boot-bar{height:100%;width:0;background:linear-gradient(90deg,var(--c0),var(--c2));
  border-radius:2px;transition:width .05s linear;box-shadow:0 0 12px var(--c0)}
#boot-log{
  width:420px;max-height:200px;overflow:hidden;
  font-size:11px;line-height:1.9;color:var(--muted);
  text-align:left;
}
.boot-line{animation:linein .2s ease;color:var(--muted)}
.boot-line.ok{color:var(--c0)}
.boot-line.warn{color:var(--c1)}
@keyframes linein{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)}}
.boot-powered{
  position:absolute;bottom:28px;font-size:10px;letter-spacing:.2em;
  color:var(--muted);font-family:var(--mono);
}
.boot-powered span{color:var(--c1)}

/* ===== HEADER ===== */
header{
  position:relative;z-index:20;
  display:flex;align-items:center;gap:16px;
  padding:0 20px;height:56px;
  background:rgba(2,2,8,.97);
  border-bottom:1px solid var(--line);
  backdrop-filter:blur(40px) saturate(180%);
}
header::after{content:'';position:absolute;bottom:-1px;left:0;right:0;height:1px;
  background:linear-gradient(90deg,var(--c0),var(--c2),var(--c1),var(--c0));
  background-size:200% 100%;animation:rainbow 4s linear infinite;}
@keyframes rainbow{0%{background-position:0%}100%{background-position:200%}}

/* LOGO */
.logo{
  font-family:var(--display);font-size:16px;font-weight:900;letter-spacing:.22em;
  color:var(--c0);white-space:nowrap;flex-shrink:0;
  text-shadow:0 0 20px color-mix(in srgb,var(--c0) 60%,transparent),0 0 40px color-mix(in srgb,var(--c0) 30%,transparent);
  animation:logoflicker 7s ease infinite;
  user-select:none;
}
.logo em{color:var(--muted);font-style:normal}
@keyframes logoflicker{0%,88%,90%,92%,100%{opacity:1}89%{opacity:.4}91%{opacity:.9}}
.logo:hover{animation:glitch .4s steps(2) infinite}
@keyframes glitch{
  0%{text-shadow:-2px 0 var(--c1),2px 0 var(--c2)}
  25%{text-shadow:2px 0 var(--c1),-2px 0 var(--c2)}
  50%{text-shadow:-1px 0 var(--c0),1px 0 var(--c1)}
  75%{text-shadow:1px 0 var(--c2),-1px 0 var(--c0)}
}
.logo-sep{width:1px;height:26px;background:var(--dim);flex-shrink:0}

/* TARGET BAR */
.target-zone{
  display:flex;align-items:center;gap:8px;flex:1;min-width:0;
}
.target-label{font-family:var(--mono);font-size:9px;letter-spacing:.2em;color:var(--muted);flex-shrink:0}
.target-input{
  flex:1;min-width:0;max-width:280px;
  background:var(--faint);border:1px solid var(--dim);
  border-radius:6px;padding:5px 10px;
  font-family:var(--mono);font-size:12px;color:var(--fg);outline:none;
  transition:border-color .2s,box-shadow .2s;
}
.target-input:focus{border-color:var(--c1);box-shadow:0 0 0 1px color-mix(in srgb,var(--c1) 30%,transparent)}
.target-input::placeholder{color:var(--muted)}
.tbtn{
  padding:5px 12px;border-radius:6px;border:1px solid var(--dim);
  font-family:var(--mono);font-size:9px;letter-spacing:.08em;
  background:transparent;color:var(--muted);cursor:pointer;
  transition:all .2s;white-space:nowrap;flex-shrink:0;
}
.tbtn.recon{border-color:color-mix(in srgb,var(--c1) 50%,var(--dim));color:var(--c1)}
.tbtn:hover{transform:translateY(-1px)}
.tbtn.recon:hover{background:color-mix(in srgb,var(--c1) 10%,transparent);
  box-shadow:0 0 14px color-mix(in srgb,var(--c1) 20%,transparent)}

/* MODEL SWITCHER */
.model-bar{display:flex;gap:5px;align-items:center;flex-shrink:0}
.mcard{
  position:relative;display:flex;flex-direction:column;align-items:center;
  padding:5px 16px;border-radius:8px;cursor:pointer;overflow:hidden;
  background:var(--faint);border:1px solid var(--dim);
  transition:all .3s cubic-bezier(.4,0,.2,1);min-width:78px;
}
.mcard::before{content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.05),transparent);
  transition:left .4s;}
.mcard:hover::before{left:100%}
.mcard::after{content:'';position:absolute;bottom:0;left:50%;right:50%;height:2px;
  background:var(--mc,var(--c0));border-radius:2px;
  transition:left .3s,right .3s,box-shadow .3s;}
.mcard:hover::after,.mcard.on::after{left:0;right:0;box-shadow:0 0 10px var(--mc,var(--c0))}
.mcard.on{border-color:var(--mc,var(--c0));background:color-mix(in srgb,var(--mc,var(--c0)) 6%,var(--faint))}
.mcard:hover:not(.on){border-color:color-mix(in srgb,var(--mc,var(--c0)) 40%,var(--dim))}
.mcard-icon{font-size:15px;line-height:1;margin-bottom:1px}
.mcard-name{font-family:var(--display);font-size:7px;letter-spacing:.2em;font-weight:700;color:var(--muted);transition:color .3s}
.mcard.on .mcard-name,.mcard:hover .mcard-name{color:var(--mc,var(--c0))}
.mcard.on .mcard-icon::after{content:'';display:block;position:absolute;
  width:5px;height:5px;border-radius:50%;background:var(--mc,var(--c0));
  top:7px;right:7px;box-shadow:0 0 8px var(--mc,var(--c0));animation:pring 1.5s infinite}
@keyframes pring{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.8);opacity:.3}}

/* KEY CONTROLS */
.key-zone{display:flex;gap:4px;align-items:center;flex-shrink:0}
.kbtn{padding:4px 9px;border-radius:5px;font-size:9px;font-family:var(--mono);
  background:transparent;border:1px solid var(--dim);color:var(--muted);
  cursor:pointer;transition:all .2s;letter-spacing:.1em;}
.kbtn:hover{border-color:var(--c1);color:var(--c1)}
.kbtn.on{border-color:var(--c1);color:var(--c1);background:rgba(255,94,58,.08);
  box-shadow:0 0 12px rgba(255,94,58,.2),inset 0 0 12px rgba(255,94,58,.04)}
.ksep{width:1px;height:18px;background:var(--dim);margin:0 2px}
.kgear{width:28px;height:28px;border-radius:6px;display:flex;align-items:center;justify-content:center;
  font-size:13px;background:transparent;border:1px solid var(--dim);color:var(--muted);
  cursor:pointer;transition:all .25s;}
.kgear:hover{border-color:var(--c0);color:var(--c0);transform:rotate(30deg);
  box-shadow:0 0 14px color-mix(in srgb,var(--c0) 20%,transparent)}

/* ===== MAIN ===== */
main{position:relative;z-index:10;height:calc(100vh - 56px);overflow:hidden}

/* ===== CHAT WINDOW ===== */
.cwin{
  position:absolute;inset:0;display:flex;flex-direction:column;
  visibility:hidden;opacity:0;
  transition:opacity .45s cubic-bezier(.4,0,.2,1),transform .45s cubic-bezier(.4,0,.2,1),visibility 0s .45s;
  transform:translateY(28px) scale(.98);will-change:transform,opacity;
}
.cwin.show{visibility:visible;opacity:1;transform:translateY(0) scale(1);
  transition:opacity .45s cubic-bezier(.4,0,.2,1),transform .45s cubic-bezier(.4,0,.2,1),visibility 0s 0s;}
.cwin.go-left{transform:translateX(-60px) scale(.96);opacity:0}
.cwin.go-right{transform:translateX(60px) scale(.96);opacity:0}

.win-top{display:flex;align-items:center;justify-content:space-between;
  padding:0 28px;height:44px;background:rgba(2,2,8,.9);border-bottom:1px solid var(--line);flex-shrink:0;}
.win-top-accent{height:2px;flex-shrink:0;position:relative;overflow:hidden}
.win-top-accent::before{content:'';position:absolute;inset:0;
  background:linear-gradient(90deg,transparent 0%,var(--wc) 30%,var(--wc) 70%,transparent 100%);
  animation:accentglow 2s ease infinite alternate;}
@keyframes accentglow{0%{opacity:.4;transform:scaleX(.8)}100%{opacity:1;transform:scaleX(1)}}
.win-top-left{display:flex;align-items:center;gap:10px}
.win-dot{width:9px;height:9px;border-radius:50%;background:var(--wc);
  box-shadow:0 0 10px var(--wc);animation:dotbeat 2s ease infinite}
@keyframes dotbeat{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
.win-title{font-family:var(--display);font-size:11px;letter-spacing:.18em;font-weight:700;
  color:var(--wc);text-shadow:0 0 12px color-mix(in srgb,var(--wc) 60%,transparent)}
.win-model-id{font-family:var(--mono);font-size:10px;color:var(--muted)}
.win-actions{display:flex;gap:6px}
.wbtn{padding:3px 10px;border-radius:4px;font-size:10px;font-family:var(--mono);
  background:transparent;border:1px solid var(--dim);color:var(--muted);
  cursor:pointer;transition:all .2s;letter-spacing:.06em}
.wbtn:hover{border-color:var(--muted);color:var(--fg)}

/* ===== MESSAGES ===== */
.msgs{flex:1;overflow-y:auto;overflow-x:hidden;padding:20px 32px 8px;
  display:flex;flex-direction:column;gap:14px;scroll-behavior:smooth;}
.msgs::-webkit-scrollbar{width:3px}
.msgs::-webkit-scrollbar-thumb{background:var(--glow);border-radius:2px}

/* ===== WELCOME SCREEN ===== */
.welcome{margin:auto;padding:40px 30px;text-align:center;
  display:flex;flex-direction:column;align-items:center;
  animation:welcin .6s cubic-bezier(.16,1,.3,1);}
@keyframes welcin{from{opacity:0;transform:translateY(40px) scale(.95)}to{opacity:1;transform:translateY(0) scale(1)}}
.w-hexring{position:relative;width:100px;height:100px;margin-bottom:24px;
  display:flex;align-items:center;justify-content:center;}
.w-hexring svg{position:absolute;inset:0;width:100%;height:100%;animation:hexspin 8s linear infinite}
.w-hexring svg:nth-child(2){animation:hexspin 12s linear infinite reverse;opacity:.5}
@keyframes hexspin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
.w-inner-icon{font-size:30px;position:relative;z-index:1;animation:iconbeat 3s ease-in-out infinite}
@keyframes iconbeat{0%,100%{transform:scale(1)}50%{transform:scale(1.12)}}
.welcome h2{font-family:var(--display);font-size:20px;font-weight:900;letter-spacing:.3em;margin-bottom:6px;
  background:linear-gradient(135deg,var(--c0),var(--wc,var(--c0)),var(--c2));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.welcome h3{font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:.15em;margin-bottom:18px}
.welcome-desc{font-size:12.5px;color:var(--muted);line-height:1.8;max-width:340px;margin-bottom:24px}
.hints-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;max-width:460px;width:100%}
.hint{padding:8px 12px;border-radius:8px;font-size:12px;font-family:var(--font);
  background:var(--faint);border:1px solid var(--dim);color:var(--muted);
  cursor:pointer;transition:all .2s;text-align:left;display:flex;align-items:center;gap:8px;}
.hint:hover{background:color-mix(in srgb,var(--wc,var(--c0)) 8%,var(--faint));
  border-color:color-mix(in srgb,var(--wc,var(--c0)) 40%,var(--dim));
  color:var(--fg);transform:translateX(3px);}
.hint-icon{font-size:14px;flex-shrink:0}

/* ===== MESSAGES ===== */
.msg{display:flex;gap:12px;animation:msgin .35s cubic-bezier(.16,1,.3,1)}
@keyframes msgin{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.msg.user{flex-direction:row-reverse}
.av{width:34px;height:34px;border-radius:9px;flex-shrink:0;margin-top:2px;
  display:flex;align-items:center;justify-content:center;font-size:14px;position:relative;}
.av-ring{position:absolute;inset:-4px;border-radius:13px;border:1px solid currentColor;opacity:0;
  animation:avring 3s ease infinite;}
.msg.ai .av-ring{opacity:1}
@keyframes avring{0%,100%{transform:scale(1);opacity:.15}50%{transform:scale(1.08);opacity:.4}}
.bub{max-width:76%;padding:12px 16px;border-radius:12px;font-size:13.5px;line-height:1.68;
  word-break:break-word;position:relative;}
.msg.user .bub{background:color-mix(in srgb,var(--c0) 6%,transparent);
  border:1px solid color-mix(in srgb,var(--c0) 15%,transparent);
  border-radius:12px 3px 12px 12px;}
.msg.ai .bub{background:var(--card);border:1px solid var(--line);border-radius:3px 12px 12px 12px}
.msg.ai .bub::before{content:'';position:absolute;top:-1px;left:0;right:60%;height:1px;
  background:var(--wc,var(--c0));border-radius:2px 0 0 0;box-shadow:0 0 8px var(--wc,var(--c0));}
.bub pre{background:rgba(0,0,0,.7);border:1px solid var(--dim);border-radius:7px;
  padding:12px 14px;margin:8px 0;font-size:12px;font-family:var(--mono);
  overflow-x:auto;white-space:pre-wrap;word-break:break-all;max-height:240px;overflow-y:auto;position:relative;}
.bub pre::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,var(--c0),var(--c2),transparent);opacity:.4}
.bub code{font-family:var(--mono);font-size:12px;padding:2px 6px;border-radius:4px}
.bub strong{font-weight:600}

/* ===== ACTION CARD ===== */
.acard{margin:4px 0 4px 46px;border-radius:8px;overflow:hidden;
  animation:msgin .35s ease;border:1px solid rgba(255,255,255,.05);position:relative;}
.acard::before{content:'';position:absolute;left:0;top:0;bottom:0;width:2px;background:var(--ac,var(--c0))}
.acard-head{padding:7px 12px 7px 16px;font-size:10px;font-family:var(--mono);
  letter-spacing:.1em;background:rgba(0,0,0,.5);display:flex;align-items:center;gap:8px;color:var(--ac,var(--c0));}
.acard-head .atarget{color:var(--muted);font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:60%}
.acard-body{padding:8px 12px 8px 16px;font-size:11px;font-family:var(--mono);
  background:rgba(0,0,0,.35);color:#7777aa;max-height:130px;overflow-y:auto;
  white-space:pre-wrap;word-break:break-all;line-height:1.5;}

/* ===== TYPING ===== */
.typing-row{display:flex;gap:12px;animation:msgin .3s ease}
.typing-bub{padding:12px 18px;background:var(--card);border:1px solid var(--line);
  border-radius:3px 12px 12px 12px;display:flex;gap:5px;align-items:center;}
.typing-bub span{width:5px;height:5px;border-radius:50%;animation:tdot 1.3s ease infinite;}
.typing-bub span:nth-child(2){animation-delay:.22s}
.typing-bub span:nth-child(3){animation-delay:.44s}
@keyframes tdot{0%,60%,100%{transform:translateY(0);opacity:.3}30%{transform:translateY(-7px);opacity:1}}
.switched{text-align:center;font-family:var(--mono);font-size:10px;color:var(--muted);
  padding:4px;letter-spacing:.06em;animation:fadein .3s ease;}
.switched b{color:var(--c1)}
@keyframes fadein{from{opacity:0}to{opacity:1}}

/* ===== INPUT ZONE ===== */
.input-zone{padding:10px 28px 12px;background:rgba(2,2,8,.98);
  border-top:1px solid var(--line);flex-shrink:0;position:relative;}
.input-zone::before{content:'';position:absolute;top:0;left:15%;right:15%;height:1px;
  background:linear-gradient(90deg,transparent,var(--wc,var(--c0)),transparent);opacity:.3;}
.input-wrap{display:flex;gap:10px;align-items:flex-end;padding:11px 14px;border-radius:12px;
  background:var(--panel);border:1px solid var(--dim);transition:border-color .3s,box-shadow .3s;}
.input-wrap:focus-within{border-color:var(--wc,var(--c0));
  box-shadow:0 0 0 1px color-mix(in srgb,var(--wc,var(--c0)) 30%,transparent),
             0 0 30px color-mix(in srgb,var(--wc,var(--c0)) 10%,transparent);}
.cin{flex:1;background:transparent;border:none;outline:none;
  color:var(--fg);font-family:var(--font);font-size:14px;font-weight:400;
  resize:none;min-height:22px;max-height:120px;line-height:1.55;}
.cin::placeholder{color:var(--muted)}
.send{width:38px;height:38px;border-radius:10px;border:none;display:flex;align-items:center;
  justify-content:center;font-size:15px;cursor:pointer;flex-shrink:0;
  transition:all .2s cubic-bezier(.4,0,.2,1);position:relative;overflow:hidden;}
.send::after{content:'';position:absolute;inset:0;
  background:radial-gradient(circle at 50% 50%,rgba(255,255,255,.4),transparent 70%);
  opacity:0;transition:opacity .15s;}
.send:hover::after{opacity:1}
.send:hover{transform:scale(1.1) rotate(-5deg)}
.send:active{transform:scale(.93)}
.send:disabled{opacity:.3;cursor:not-allowed;transform:none}
.quick-row{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.qbtn{padding:4px 12px;border-radius:16px;font-size:11px;font-family:var(--mono);
  background:transparent;border:1px solid var(--dim);color:var(--muted);
  cursor:pointer;transition:all .2s;white-space:nowrap;}
.qbtn:hover{border-color:var(--wc,var(--c0));color:var(--wc,var(--c0));
  background:color-mix(in srgb,var(--wc,var(--c0)) 6%,transparent);transform:translateY(-1px)}

/* ===== MODAL ===== */
.overlay{display:none;position:fixed;inset:0;z-index:100;
  background:rgba(0,0,0,.88);backdrop-filter:blur(16px);align-items:center;justify-content:center;}
.overlay.show{display:flex}
.modal{background:var(--deep);border:1px solid var(--line);border-radius:18px;
  padding:30px;width:400px;max-width:94vw;
  box-shadow:0 50px 120px rgba(0,0,0,.8),0 0 0 1px rgba(255,255,255,.03);
  animation:modin .3s cubic-bezier(.16,1,.3,1);position:relative;overflow:hidden;}
.modal::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--c0),var(--c2),var(--c1),var(--c0));
  background-size:200%;animation:rainbow 3s linear infinite;}
@keyframes modin{from{opacity:0;transform:scale(.88) translateY(24px)}to{opacity:1;transform:scale(1) translateY(0)}}
.modal h3{font-family:var(--display);font-size:12px;letter-spacing:.25em;color:var(--c0);margin-bottom:5px}
.modal p{font-size:12px;color:var(--muted);margin-bottom:22px;line-height:1.7}
.kopt{display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:10px;
  border:1px solid var(--line);background:var(--card);cursor:pointer;transition:all .2s;margin-bottom:8px;}
.kopt:hover{border-color:var(--c1);transform:translateX(4px)}
.kopt.on{border-color:var(--c1);background:rgba(255,94,58,.06);box-shadow:0 0 20px rgba(255,94,58,.08)}
.knum{width:26px;height:26px;border-radius:50%;background:var(--dim);
  display:flex;align-items:center;justify-content:center;
  font-family:var(--mono);font-size:11px;color:var(--muted);flex-shrink:0;transition:all .2s}
.kopt.on .knum{background:var(--c1);color:#000;box-shadow:0 0 14px rgba(255,94,58,.5)}
.kinfo .kl{font-size:13px;font-weight:600}
.kinfo .kv{font-size:10px;font-family:var(--mono);color:var(--muted);margin-top:2px}
/* Add key input */
.kadd-wrap{display:flex;gap:8px;margin-top:6px}
.kadd-input{flex:1;background:var(--faint);border:1px solid var(--dim);border-radius:8px;
  padding:9px 12px;font-family:var(--mono);font-size:11px;color:var(--fg);outline:none;}
.kadd-input:focus{border-color:var(--c0)}
.kadd-btn{padding:9px 14px;border-radius:8px;background:var(--c0);border:none;
  color:#000;font-family:var(--display);font-size:10px;font-weight:700;cursor:pointer;transition:all .2s;}
.kadd-btn:hover{background:color-mix(in srgb,var(--c0) 80%,#fff);box-shadow:0 0 16px color-mix(in srgb,var(--c0) 40%,transparent)}
.mclose{width:100%;margin-top:14px;padding:12px;border-radius:10px;
  background:var(--c0);border:none;color:#000;font-family:var(--display);
  font-size:11px;font-weight:700;letter-spacing:.15em;cursor:pointer;transition:all .2s;}
.mclose:hover{box-shadow:0 0 24px color-mix(in srgb,var(--c0) 30%,transparent)}

/* ===== ABOUT MODAL ===== */
.about-modal{width:560px;max-height:88vh;overflow-y:auto;padding:36px}
.about-modal::-webkit-scrollbar{width:3px}
.about-modal::-webkit-scrollbar-thumb{background:var(--glow);border-radius:2px}
/* Hero */
.about-hero{text-align:center;margin-bottom:32px}
.about-agent-logo{
  font-family:var(--display);font-size:36px;font-weight:900;letter-spacing:.35em;
  color:var(--c0);margin-bottom:4px;
  text-shadow:0 0 30px color-mix(in srgb,var(--c0) 60%,transparent),
              0 0 60px color-mix(in srgb,var(--c0) 30%,transparent);
  animation:glitch1 6s ease infinite;
}
.about-version{font-family:var(--mono);font-size:10px;letter-spacing:.25em;color:var(--muted);margin-bottom:14px}
.about-tagline{font-size:13px;color:var(--fg);line-height:1.7;max-width:420px;margin:0 auto}
/* Divider */
.about-div{height:1px;background:linear-gradient(90deg,transparent,var(--c0),var(--c2),transparent);
  opacity:.25;margin:22px 0;}
/* Section title */
.about-sec{font-family:var(--display);font-size:10px;letter-spacing:.28em;
  color:var(--c0);margin-bottom:14px;display:flex;align-items:center;gap:10px}
.about-sec::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,var(--c0),transparent);opacity:.2}
/* Skills grid */
.skills-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px}
.skill-card{
  padding:11px 14px;border-radius:10px;
  background:var(--faint);border:1px solid var(--dim);
  transition:all .2s;
}
.skill-card:hover{
  border-color:color-mix(in srgb,var(--c0) 40%,var(--dim));
  background:color-mix(in srgb,var(--c0) 4%,var(--faint));
  transform:translateX(3px);
}
.skill-icon{font-size:18px;margin-bottom:5px}
.skill-title{font-family:var(--display);font-size:10px;letter-spacing:.12em;
  color:var(--fg);margin-bottom:3px;font-weight:700}
.skill-desc{font-size:11px;color:var(--muted);line-height:1.55}
/* Usage tiers */
.tier-list{display:flex;flex-direction:column;gap:7px;margin-bottom:8px}
.tier{padding:11px 14px;border-radius:10px;background:var(--faint);
  border:1px solid var(--dim);display:flex;align-items:flex-start;gap:12px}
.tier-badge{font-family:var(--display);font-size:9px;font-weight:700;letter-spacing:.12em;
  padding:3px 8px;border-radius:4px;flex-shrink:0;margin-top:1px}
.tier-badge.free{background:color-mix(in srgb,var(--c0) 12%,transparent);
  border:1px solid color-mix(in srgb,var(--c0) 40%,transparent);color:var(--c0)}
.tier-badge.paid{background:color-mix(in srgb,var(--c1) 12%,transparent);
  border:1px solid color-mix(in srgb,var(--c1) 40%,transparent);color:var(--c1)}
.tier-badge.multi{background:color-mix(in srgb,var(--c2) 12%,transparent);
  border:1px solid color-mix(in srgb,var(--c2) 40%,transparent);color:var(--c2)}
.tier-body .tier-title{font-size:12px;font-weight:600;color:var(--fg);margin-bottom:2px}
.tier-body .tier-detail{font-size:11px;color:var(--muted);line-height:1.5}
.tier-body .tier-detail a{color:var(--c0);text-decoration:none}
.tier-body .tier-detail a:hover{text-decoration:underline}
/* Contact / links */
.about-links{display:flex;flex-direction:column;gap:8px;margin-bottom:8px}
.about-link{
  display:flex;align-items:center;gap:12px;
  padding:12px 16px;border-radius:10px;
  background:var(--faint);border:1px solid var(--dim);
  text-decoration:none;transition:all .2s;
}
.about-link:hover{
  border-color:color-mix(in srgb,var(--c1) 50%,var(--dim));
  background:color-mix(in srgb,var(--c1) 5%,var(--faint));
  transform:translateX(4px);
}
.about-link-icon{font-size:18px;flex-shrink:0}
.about-link-body .al-title{font-size:12px;font-weight:600;color:var(--fg)}
.about-link-body .al-url{font-family:var(--mono);font-size:10px;color:var(--muted);margin-top:1px}
/* Author card */
.author-card{
  display:flex;align-items:center;gap:16px;
  padding:16px;border-radius:12px;
  background:color-mix(in srgb,var(--c1) 5%,var(--faint));
  border:1px solid color-mix(in srgb,var(--c1) 20%,var(--dim));
  margin-bottom:8px;
}
.author-avatar{
  width:48px;height:48px;border-radius:12px;flex-shrink:0;
  background:color-mix(in srgb,var(--c1) 12%,var(--dim));
  border:1px solid color-mix(in srgb,var(--c1) 30%,transparent);
  display:flex;align-items:center;justify-content:center;font-size:22px;
  box-shadow:0 0 20px color-mix(in srgb,var(--c1) 15%,transparent);
}
.author-name{font-family:var(--display);font-size:14px;font-weight:900;letter-spacing:.1em;
  color:var(--c1);margin-bottom:3px;
  text-shadow:0 0 12px color-mix(in srgb,var(--c1) 40%,transparent)}
.author-role{font-size:11px;color:var(--muted);line-height:1.55}
.author-gh{display:inline-flex;align-items:center;gap:5px;margin-top:5px;
  font-family:var(--mono);font-size:10px;color:var(--c0);
  text-decoration:none;padding:2px 8px;border-radius:4px;
  border:1px solid color-mix(in srgb,var(--c0) 30%,transparent);
  background:color-mix(in srgb,var(--c0) 5%,transparent);
  transition:all .2s;}
.author-gh:hover{background:color-mix(in srgb,var(--c0) 12%,transparent);
  box-shadow:0 0 12px color-mix(in srgb,var(--c0) 20%,transparent)}
/* About button in header */
.about-btn{
  padding:5px 12px;border-radius:6px;border:1px solid var(--dim);
  font-family:var(--mono);font-size:9px;letter-spacing:.12em;
  background:transparent;color:var(--muted);cursor:pointer;
  transition:all .2s;flex-shrink:0;white-space:nowrap;
}
.about-btn:hover{
  border-color:color-mix(in srgb,var(--c0) 60%,var(--dim));
  color:var(--c0);
  box-shadow:0 0 12px color-mix(in srgb,var(--c0) 15%,transparent);
}

/* ===== TOAST ===== */
.toast{position:fixed;bottom:22px;right:22px;z-index:300;
  padding:10px 18px;border-radius:10px;font-size:12px;font-family:var(--mono);
  background:rgba(5,5,15,.97);backdrop-filter:blur(30px);
  border:1px solid var(--c0);color:var(--c0);
  box-shadow:0 10px 40px rgba(0,0,0,.5),0 0 20px color-mix(in srgb,var(--c0) 8%,transparent);
  animation:tin .3s cubic-bezier(.16,1,.3,1);pointer-events:none;
  display:flex;align-items:center;gap:8px;letter-spacing:.04em;}
@keyframes tin{from{opacity:0;transform:translateX(30px) scale(.9)}to{opacity:1;transform:translateX(0) scale(1)}}
.toast.warn{border-color:var(--c1);color:var(--c1)}
.toast-dot{width:6px;height:6px;border-radius:50%;background:currentColor;flex-shrink:0;animation:pring 1s infinite}

/* ===== HUD ===== */
.hud{position:fixed;z-index:5;pointer-events:none}
.hud-tl{top:68px;left:12px}.hud-tr{top:68px;right:12px}.hud-bl{bottom:80px;left:12px}
.hud svg{width:26px;height:26px;stroke:var(--c0);stroke-width:1;fill:none;opacity:.12}

/* ===== FOOTER CREDIT ===== */
.powered{position:fixed;bottom:6px;left:50%;transform:translateX(-50%);
  font-family:var(--mono);font-size:9px;letter-spacing:.18em;color:var(--muted);
  z-index:15;pointer-events:none;white-space:nowrap;}
.powered span{color:var(--c1)}

::-webkit-scrollbar{width:3px;height:3px}
::-webkit-scrollbar-thumb{background:var(--glow);border-radius:2px}
</style>
</head>
<body>

<!-- BOOT SCREEN -->
<div id="boot">
  <div class="boot-logo" id="boot-logo">%%AGENT%%</div>
  <div class="boot-sub">%%AGENT_LOWER%%://neural-core · v2.0</div>
  <div class="boot-bar-wrap"><div class="boot-bar" id="boot-bar"></div></div>
  <div id="boot-log"></div>
  <div class="boot-powered">Powered by <span>Omar Bouzganda</span> · For authorized use only</div>
</div>

<!-- Cursor -->
<div id="cur"></div><div id="cur2"></div>

<!-- BG -->
<div class="bg">
  <div class="bg-base"></div>
  <div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div>
  <div class="bg-grid"></div><div class="bg-noise"></div><div class="scanlines"></div>
</div>
<canvas id="pcanvas"></canvas>

<!-- HUD corners -->
<div class="hud hud-tl"><svg viewBox="0 0 28 28"><path d="M1 14 L1 1 L14 1"/></svg></div>
<div class="hud hud-tr"><svg viewBox="0 0 28 28"><path d="M27 14 L27 1 L14 1"/></svg></div>
<div class="hud hud-bl"><svg viewBox="0 0 28 28"><path d="M1 14 L1 27 L14 27"/></svg></div>

<!-- HEADER -->
<header>
  <div class="logo">%%AGENT%%<em>://</em>NET</div>
  <div class="logo-sep"></div>

  <!-- TARGET BAR -->
  <div class="target-zone">
    <span class="target-label">TARGET:</span>
    <input class="target-input" id="target-input" placeholder="domain.com / 192.168.1.1" spellcheck="false">
    <button class="tbtn recon" onclick="launchRecon()">⚔ FULL RECON</button>
    <button class="tbtn" onclick="quickScan()">🔍 QUICK SCAN</button>
  </div>

  <div class="model-bar" id="mbar"></div>

  <button class="about-btn" onclick="openAbout()">◉ ABOUT</button>

  <div class="key-zone" id="kzone">
    <div class="ksep"></div>
    <button class="kgear" onclick="openModal()">⚙</button>
  </div>
</header>

<!-- MAIN -->
<main id="main"></main>

<!-- MODAL -->
<div class="overlay" id="kov" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <h3>API KEY MANAGER</h3>
    <p>Select active key. Keys auto-rotate on failure.<br>Add more keys for higher daily limits.</p>
    <div id="klist"></div>
    <div class="kadd-wrap">
      <input class="kadd-input" id="kadd" placeholder="Add new key: sk-or-..." spellcheck="false">
      <button class="kadd-btn" onclick="addKey()">ADD</button>
    </div>
    <button class="mclose" onclick="closeModal()">CONFIRM</button>
  </div>
</div>

<!-- Footer credit -->
<div class="powered">Powered by <span>Omar Bouzganda</span> · For authorized penetration testing only</div>

<!-- ABOUT MODAL -->
<div class="overlay" id="about-ov" onclick="if(event.target===this)closeAbout()">
  <div class="modal about-modal">

    <!-- Hero -->
    <div class="about-hero">
      <div class="about-agent-logo">%%AGENT%%</div>
      <div class="about-version">v2.0 · AI Pentesting Agent · Omar Bouzganda</div>
      <div class="about-tagline">
        A full-stack AI-powered penetration testing agent running on Kali Linux.
        Talk to multiple AI models, run real tools, scan targets, and dominate your attack surface —
        all from one browser interface.
      </div>
    </div>

    <div class="about-div"></div>

    <!-- SKILLS -->
    <div class="about-sec">CAPABILITIES</div>
    <div class="skills-grid">
      <div class="skill-card">
        <div class="skill-icon">🔍</div>
        <div class="skill-title">FULL RECON</div>
        <div class="skill-desc">whois · dig · nmap · whatweb · nikto · gobuster — all chained automatically on any target</div>
      </div>
      <div class="skill-card">
        <div class="skill-icon">⚔</div>
        <div class="skill-title">EXPLOITATION</div>
        <div class="skill-desc">AI-guided exploit selection, Metasploit modules, CVE research, payload crafting</div>
      </div>
      <div class="skill-card">
        <div class="skill-icon">🕸</div>
        <div class="skill-title">WEB ATTACKS</div>
        <div class="skill-desc">SQLi · XSS · LFI · directory bruteforce · header analysis · spider crawling</div>
      </div>
      <div class="skill-card">
        <div class="skill-icon">📡</div>
        <div class="skill-title">NETWORK RECON</div>
        <div class="skill-desc">ARP scan, port scan, service fingerprinting, subdomain enumeration, DNS analysis</div>
      </div>
      <div class="skill-card">
        <div class="skill-icon">🔐</div>
        <div class="skill-title">CREDENTIALS</div>
        <div class="skill-desc">SSH/FTP brute force, hash cracking, credential extraction, password spray</div>
      </div>
      <div class="skill-card">
        <div class="skill-icon">🐍</div>
        <div class="skill-title">CODE & SCRIPTS</div>
        <div class="skill-desc">Generate custom exploits, reverse shells, scanners, automation scripts in Python/Bash</div>
      </div>
      <div class="skill-card">
        <div class="skill-icon">🕵</div>
        <div class="skill-title">OSINT</div>
        <div class="skill-desc">Target profiling, Google dorks, email harvesting, social footprint analysis</div>
      </div>
      <div class="skill-card">
        <div class="skill-icon">📜</div>
        <div class="skill-title">REPORTING</div>
        <div class="skill-desc">AI-generated pentest reports, vulnerability summaries, remediation advice</div>
      </div>
    </div>

    <div class="about-div"></div>

    <!-- USAGE / KEYS -->
    <div class="about-sec">HOW TO GET MORE USAGE</div>
    <div class="tier-list">
      <div class="tier">
        <div class="tier-badge free">FREE</div>
        <div class="tier-body">
          <div class="tier-title">Free Tier — 50 requests / day</div>
          <div class="tier-detail">
            Create a free account at <a href="https://openrouter.ai/keys" target="_blank">openrouter.ai/keys</a>
            and add your key via the <b>⚙ key manager</b>. The agent auto-rotates through 15+ free fallback models.
            Quota resets every day at midnight UTC.
          </div>
        </div>
      </div>
      <div class="tier">
        <div class="tier-badge paid">PAID</div>
        <div class="tier-body">
          <div class="tier-title">+$5 Credit — ~1,000 requests / day</div>
          <div class="tier-detail">
            Add $5 credit at <a href="https://openrouter.ai/credits" target="_blank">openrouter.ai/credits</a>
            to unlock GPT-4o, Claude 3.5 Sonnet, DeepSeek and all premium models with
            much higher rate limits.
          </div>
        </div>
      </div>
      <div class="tier">
        <div class="tier-badge multi">MULTI-KEY</div>
        <div class="tier-body">
          <div class="tier-title">Multiple Keys — Multiply your daily limit</div>
          <div class="tier-detail">
            Add up to 4+ keys via the <b>⚙ key manager</b>. The agent automatically rotates
            to the next key on failure — effectively multiplying your daily requests.
          </div>
        </div>
      </div>
    </div>

    <div class="about-div"></div>

    <!-- AUTHOR -->
    <div class="about-sec">CREATOR</div>
    <div class="author-card">
      <div class="author-avatar">👤</div>
      <div>
        <div class="author-name">Omar Bouzganda</div>
        <div class="author-role">
          Security researcher &amp; tool developer.<br>
          Built this agent to make AI-powered pentesting accessible to everyone.
        </div>
        <a class="author-gh" href="https://github.com/omarbouzganda" target="_blank">
          ⬡ github.com/omarbouzganda
        </a>
      </div>
    </div>

    <div class="about-div"></div>

    <!-- LINKS -->
    <div class="about-sec">LINKS</div>
    <div class="about-links">
      <a class="about-link" href="https://github.com/omarbouzganda" target="_blank">
        <div class="about-link-icon">🐛</div>
        <div class="about-link-body">
          <div class="al-title">Report a Bug</div>
          <div class="al-url">github.com/omarbouzganda</div>
        </div>
      </a>
      <a class="about-link" href="https://github.com/omarbouzganda" target="_blank">
        <div class="about-link-icon">💬</div>
        <div class="about-link-body">
          <div class="al-title">Contact / Contribute</div>
          <div class="al-url">github.com/omarbouzganda</div>
        </div>
      </a>
      <a class="about-link" href="https://openrouter.ai/keys" target="_blank">
        <div class="about-link-icon">🔑</div>
        <div class="about-link-body">
          <div class="al-title">Get an OpenRouter API Key</div>
          <div class="al-url">openrouter.ai/keys — free account, no credit card needed</div>
        </div>
      </a>
    </div>

    <button class="mclose" onclick="closeAbout()">CLOSE</button>
  </div>
</div>

<script>
// ── CONFIG ─────────────────────────────────────────────────
const API       = window.location.origin;
const AGENT     = '%%AGENT%%';

const MODELS    = %%MODELS_JS%%;
// Inject theme-aware color per model (keep originals)
const MODEL_HEX = ['#00ffd4','#ff6b35','#bf5fff','#ff2d9b'];
MODELS.forEach((m,i)=>m.hex=MODEL_HEX[i]);

let KEYS_INFO   = %%KEYS_JS%%;
let activeKey   = 0, activeWin = 0, prevWin = -1;
let busy        = [false,false,false,false];
let histories   = [[],[],[],[]];

// ── BOOT SEQUENCE ──────────────────────────────────────────
const BOOT_LINES = [
  {txt:`[INIT] Loading ${AGENT} neural core...`,     cls:''},
  {txt:'[SYS]  Mounting /dev/kali filesystem',        cls:''},
  {txt:'[NET]  Initializing attack surface mapper',   cls:''},
  {txt:'[AI]   Connecting to OpenRouter AI cluster',  cls:''},
  {txt:'[TOOL] Verifying Kali tool suite',            cls:''},
  {txt:'[SEC]  Establishing encrypted tunnel',        cls:''},
  {txt:'[WARN] Authorized operators only',            cls:'warn'},
  {txt:`[BOOT] ${AGENT} operational · awaiting target`, cls:'ok'},
];

(function bootSeq(){
  const bar  = document.getElementById('boot-bar');
  const log  = document.getElementById('boot-log');
  let   i    = 0;
  const step = () => {
    if(i >= BOOT_LINES.length){
      setTimeout(()=>{
        document.getElementById('boot').classList.add('fade-out');
        setTimeout(()=>{
          const b=document.getElementById('boot');
          if(b)b.style.display='none';
        },800);
      },400);
      return;
    }
    const {txt,cls} = BOOT_LINES[i];
    const d = document.createElement('div');
    d.className = 'boot-line' + (cls?' '+cls:'');
    d.textContent = txt;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
    bar.style.width = ((i+1)/BOOT_LINES.length*100)+'%';
    i++;
    setTimeout(step, 180 + Math.random()*120);
  };
  setTimeout(step, 500);
})();

// ── CURSOR ─────────────────────────────────────────────────
(()=>{
  const c1=document.getElementById('cur'),c2=document.getElementById('cur2');
  let mx=0,my=0,cx=0,cy=0;
  document.addEventListener('mousemove',e=>{mx=e.clientX;my=e.clientY;
    c1.style.left=mx+'px';c1.style.top=my+'px'});
  function lc(){cx+=(mx-cx)*.12;cy+=(my-cy)*.12;
    c2.style.left=cx+'px';c2.style.top=cy+'px';requestAnimationFrame(lc)}
  lc();
  document.addEventListener('mousedown',()=>c1.style.transform='translate(-50%,-50%) scale(2)');
  document.addEventListener('mouseup',()=>c1.style.transform='translate(-50%,-50%) scale(1)');
})();

// ── PARTICLES ──────────────────────────────────────────────
(()=>{
  const cv=document.getElementById('pcanvas');
  const ctx=cv.getContext('2d');
  let W,H;
  const resize=()=>{W=cv.width=innerWidth;H=cv.height=innerHeight};
  resize(); window.addEventListener('resize',resize);
  const cols = getComputedStyle(document.documentElement);
  const c0 = '%%C0%%', c1 = '%%C1%%', c2 = '%%C2%%';
  const pts=Array.from({length:70},()=>({
    x:Math.random()*1920,y:Math.random()*1080,
    vx:(Math.random()-.5)*.3,vy:(Math.random()-.5)*.3,
    r:Math.random()*1.5+.4,
    c:[c0,c1,c2][Math.floor(Math.random()*3)],
    o:Math.random()*.3+.05,
  }));
  let mx=960,my=540;
  document.addEventListener('mousemove',e=>{mx=e.clientX;my=e.clientY});
  function frame(){
    ctx.clearRect(0,0,W,H);
    pts.forEach(p=>{
      const dx=p.x-mx,dy=p.y-my,d=Math.sqrt(dx*dx+dy*dy);
      if(d<120){p.vx+=dx/d*.04;p.vy+=dy/d*.04}
      p.vx*=.995;p.vy*=.995;
      p.x+=p.vx;p.y+=p.vy;
      if(p.x<0)p.x=W;if(p.x>W)p.x=0;
      if(p.y<0)p.y=H;if(p.y>H)p.y=0;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle=p.c;ctx.globalAlpha=p.o;ctx.fill();
    });
    ctx.globalAlpha=1;
    for(let i=0;i<pts.length;i++) for(let j=i+1;j<pts.length;j++){
      const dx=pts[i].x-pts[j].x,dy=pts[i].y-pts[j].y;
      const d=Math.sqrt(dx*dx+dy*dy);
      if(d<100){
        ctx.beginPath();ctx.moveTo(pts[i].x,pts[i].y);ctx.lineTo(pts[j].x,pts[j].y);
        ctx.strokeStyle=`rgba(0,255,212,${(1-d/100)*.04})`;ctx.lineWidth=1;ctx.stroke();
      }
    }
    requestAnimationFrame(frame);
  }
  frame();
})();

// ── HINTS PER WINDOW ───────────────────────────────────────
const HINTS_PER_WIN = [
  // GPT-4o
  [['⚔ Full recon on a target site','⚔'],['🔍 Run nmap -sV on a host','🔍'],
   ['💉 Find SQL injection vectors','💉'],['📡 Scan for subdomains','📡'],
   ['🐍 Write a Python exploit','🐍'],['🔓 Brute-force SSH login','🔓']],
  // Claude
  [['📝 Write a phishing report','📝'],['🕵 Analyze malware behavior','🕵'],
   ['🔐 Crack a password hash','🔐'],['📜 Generate a pentest report','📜'],
   ['🧬 Reverse-engineer a binary','🧬'],['🌐 OSINT on a target','🌐']],
  // DeepSeek
  [['🔧 Create a custom payload','🔧'],['📦 Set up a C2 listener','📦'],
   ['💻 Exploit a CVE','💻'],['🎯 Run Metasploit module','🎯'],
   ['🕸 Spider a web app','🕸'],['🔑 Extract credentials','🔑']],
  // Venice
  [['⚡ Run full port scan','⚡'],['🧪 Test XSS vulnerability','🧪'],
   ['📂 List sensitive directories','📂'],['🛡 Check firewall rules','🛡'],
   ['🔥 ARP scan local network','🔥'],['👁 Monitor network traffic','👁']],
];

// ── BUILD UI ───────────────────────────────────────────────
function buildUI(){
  // Key buttons
  const kz = document.getElementById('kzone');
  const ksep = kz.querySelector('.ksep');
  const kgear = kz.querySelector('.kgear');
  KEYS_INFO.forEach((k,i)=>{
    const b = document.createElement('button');
    b.className = 'kbtn'+(i===0?' on':'');
    b.id = `kb${i}`; b.textContent = `KEY·${i+1}`;
    b.onclick = ()=>setKey(i);
    kz.insertBefore(b, ksep);
  });

  // Model bar
  document.getElementById('mbar').innerHTML = MODELS.map((m,i)=>`
    <div class="mcard ${i===0?'on':''}" id="mc${i}" onclick="switchWin(${i})" style="--mc:${m.hex}">
      <div class="mcard-icon" style="color:${m.hex};text-shadow:0 0 12px ${m.hex}">${m.icon}</div>
      <div class="mcard-name">${m.short}</div>
    </div>`).join('');

  // Windows
  document.getElementById('main').innerHTML = MODELS.map((m,i)=>{
    const hints = HINTS_PER_WIN[i];
    return `
    <div class="cwin ${i===0?'show':''}" id="cw${i}" style="--wc:${m.hex}">
      <div class="win-top-accent" style="--wc:${m.hex}"></div>
      <div class="win-top">
        <div class="win-top-left">
          <div class="win-dot" style="background:${m.hex};box-shadow:0 0 12px ${m.hex}"></div>
          <div class="win-title" style="color:${m.hex}">${m.name}</div>
          <div class="win-model-id" id="mid${i}">${(m.id.split('/')[1]||m.id).split(':')[0]}</div>
        </div>
        <div class="win-actions">
          <button class="wbtn" onclick="clearWin(${i})">CLR</button>
        </div>
      </div>
      <div class="msgs" id="msgs${i}">
        <div class="welcome" style="--wc:${m.hex}">
          <div class="w-hexring">
            <svg viewBox="0 0 100 100"><polygon points="50,2 95,26 95,74 50,98 5,74 5,26" stroke="${m.hex}" stroke-width="1.5" fill="none" opacity=".6"/></svg>
            <svg viewBox="0 0 100 100"><polygon points="50,10 88,32 88,68 50,90 12,68 12,32" stroke="${m.hex}" stroke-width="1" fill="none" opacity=".3"/></svg>
            <div class="w-inner-icon" style="color:${m.hex};text-shadow:0 0 20px ${m.hex}">${m.icon}</div>
          </div>
          <h2>${AGENT} // ${m.name}</h2>
          <h3>${m.id}</h3>
          <div class="welcome-desc">
            Full Kali Linux control · Run any tool · Dominate your target.<br>
            <span style="color:var(--c1);font-size:11px">⚠ For authorized penetration testing only.</span>
          </div>
          <div class="hints-grid">
            ${hints.map(([h,e])=>`<div class="hint" onclick="qsend('${h.replace(/'/g,"\\'")}',${i})">
              <span class="hint-icon">${e}</span><span>${h}</span>
            </div>`).join('')}
          </div>
        </div>
      </div>
      <div class="input-zone" style="--wc:${m.hex}">
        <div class="input-wrap">
          <textarea class="cin" id="ci${i}" placeholder="Command ${AGENT} · ${m.name}…"
            onkeydown="ck(event,${i})" oninput="ar(this)" rows="1"></textarea>
          <button class="send" id="sb${i}" onclick="sendMsg(${i})"
            style="background:${m.hex};color:#000">▲</button>
        </div>
        <div class="quick-row">
          <button class="qbtn" onclick="qsend('Scan localhost with nmap -sV -sC',${i})">🔍 Nmap</button>
          <button class="qbtn" onclick="qsend('Write a Python reverse shell to Desktop',${i})">🐍 Shell</button>
          <button class="qbtn" onclick="qsend('Show running processes and open ports',${i})">⚙ Procs</button>
          <button class="qbtn" onclick="qsend('List Desktop and home files',${i})">📁 Files</button>
          <button class="qbtn recon-btn" style="border-color:color-mix(in srgb,var(--wc) 50%,var(--dim));color:var(--wc)"
            onclick="launchRecon(${i})">⚔ RECON</button>
        </div>
      </div>
    </div>`;
  }).join('');
}

// ── TARGET / RECON ─────────────────────────────────────────
function launchRecon(wid){
  const w = wid !== undefined ? wid : activeWin;
  const t = document.getElementById('target-input').value.trim();
  if(!t){ toast('⚠ Enter a target first (domain or IP)',true); document.getElementById('target-input').focus(); return; }
  const prompt = `⚔ FULL RECON TARGET: ${t}

You are my elite recon AI. The target is: ${t}

Run the following tools in sequence and report all findings:
1. whois ${t}
2. dig ${t} ANY +noall +answer
3. nmap -sV -sC -T4 --open ${t}
4. whatweb ${t}
5. nikto -h ${t}
6. curl -sI ${t}
7. gobuster dir -u http://${t} -w /usr/share/wordlists/dirb/common.txt -q --no-error

After each tool finishes, analyze the output. At the end, provide:
- Open ports & services summary
- Identified vulnerabilities
- Recommended attack vectors
- Next steps`;
  document.getElementById(`ci${w}`).value = prompt;
  sendMsg(w);
}

function quickScan(wid){
  const w = wid !== undefined ? wid : activeWin;
  const t = document.getElementById('target-input').value.trim();
  if(!t){ toast('⚠ Enter a target first',true); document.getElementById('target-input').focus(); return; }
  qsend(`Run: nmap -sV --open -T4 ${t} and summarize open services`, w);
}

// ── WINDOW SWITCH ──────────────────────────────────────────
function switchWin(idx){
  if(idx===activeWin) return;
  const dir = idx>activeWin ? 'go-left' : 'go-right';
  const old = document.getElementById(`cw${activeWin}`);
  old.classList.add(dir);
  setTimeout(()=>old.classList.remove('show',dir),420);
  document.querySelectorAll('.mcard').forEach((c,i)=>c.classList.toggle('on',i===idx));
  setTimeout(()=>{
    prevWin=activeWin; activeWin=idx;
    document.getElementById(`cw${idx}`).classList.add('show');
    document.getElementById(`ci${idx}`).focus();
  },200);
}

// ── SEND ───────────────────────────────────────────────────
async function sendMsg(wid){
  const inp = document.getElementById(`ci${wid}`);
  const btn = document.getElementById(`sb${wid}`);
  const txt = inp.value.trim();
  if(!txt||busy[wid]) return;
  busy[wid]=true; btn.disabled=true;
  inp.value=''; inp.style.height='auto';
  addMsg(wid,'user',txt);
  histories[wid].push({role:'user',content:txt});
  addTyping(wid);
  try{
    const r = await fetch(API+'/ask',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({prompt:txt,history:histories[wid].slice(-14),
        model:MODELS[wid].id,key_index:activeKey})
    });
    if(!r.ok){ const t=await r.text(); throw new Error(t); }
    const d = await r.json();
    if(d.error) throw new Error(JSON.stringify(d.error));
    rmTyping(wid);
    histories[wid].push({role:'assistant',content:d.reply});
    if(d.model&&d.model!==MODELS[wid].id){
      const s=d.model.split('/').pop().replace(':free','');
      addSwitched(wid,s);
      document.getElementById(`mid${wid}`).textContent=s;
    }
    if(d.actions?.length) d.actions.forEach(a=>addActionCard(wid,a));
    addMsg(wid,'ai',d.reply);
  }catch(e){
    rmTyping(wid);
    addMsg(wid,'ai',`⚠️ ${esc(e.message.slice(0,300))}`);
  }
  busy[wid]=false; btn.disabled=false;
}

function qsend(t,w){ document.getElementById(`ci${w}`).value=t; sendMsg(w); }
function ck(e,w){ if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMsg(w);} }
function ar(el){ el.style.height='auto'; el.style.height=Math.min(el.scrollHeight,120)+'px'; }

// ── DOM HELPERS ────────────────────────────────────────────
function addMsg(wid,role,text){
  const c  = document.getElementById(`msgs${wid}`);
  c.querySelector('.welcome')?.remove();
  const wc = MODELS[wid].hex;
  const d  = document.createElement('div');
  d.className = 'msg '+(role==='user'?'user':'ai');
  const avBg = role==='user'
    ? `background:${wc}11;border:1px solid ${wc}33;color:${wc}`
    : `background:${wc}0d;border:1px solid ${wc}22;color:${wc}`;
  d.innerHTML=`<div class="av" style="${avBg}"><div class="av-ring" style="border-color:${wc}"></div>${role==='user'?'◈':'⬡'}</div><div class="bub" style="--wc:${wc}">${fmt(text,wid)}</div>`;
  c.appendChild(d); c.scrollTop=c.scrollHeight;
}

function addActionCard(wid,a){
  const c  = document.getElementById(`msgs${wid}`);
  const wc = MODELS[wid].hex;
  const icons={shell:'⚡',write:'📄',read:'📖',delete:'🗑️'};
  const acs  ={shell:wc,write:'#00ffd4',read:'#a855f7',delete:'#ff4444'};
  const ac   = acs[a.type]||wc;
  const d    = document.createElement('div');
  d.className='acard'; d.style.setProperty('--ac',ac);
  d.innerHTML=`<div class="acard-head">${icons[a.type]||'🔧'} ${a.type.toUpperCase()}<span class="atarget">${esc(a.target)}</span></div><div class="acard-body">${esc(a.result)}</div>`;
  c.appendChild(d); c.scrollTop=c.scrollHeight;
}

function addTyping(wid){
  const c  = document.getElementById(`msgs${wid}`);
  const wc = MODELS[wid].hex;
  const d  = document.createElement('div'); d.id=`ty${wid}`; d.className='typing-row';
  d.innerHTML=`<div class="av" style="background:${wc}0d;border:1px solid ${wc}22;color:${wc}"><div class="av-ring" style="border-color:${wc}"></div>⬡</div><div class="typing-bub"><span style="background:${wc}"></span><span style="background:${wc}"></span><span style="background:${wc}"></span></div>`;
  c.appendChild(d); c.scrollTop=c.scrollHeight;
}
function rmTyping(wid){ document.getElementById(`ty${wid}`)?.remove(); }
function addSwitched(wid,m){
  const c=document.getElementById(`msgs${wid}`);
  const d=document.createElement('div'); d.className='switched';
  d.innerHTML=`↳ switched to <b>${m}</b>`; c.appendChild(d);
}
function clearWin(wid){ document.getElementById(`msgs${wid}`).innerHTML=''; histories[wid]=[]; }

function fmt(t,wid){
  const wc=MODELS[wid]?.hex||'var(--c0)';
  t=t.replace(/```(\w+)?\n?([\s\S]*?)```/g,(_,l,c)=>`<pre>${esc(c.trim())}</pre>`);
  t=t.replace(/`([^`\n]{1,80})`/g,`<code style="color:${wc};background:${wc}18">$1</code>`);
  t=t.replace(/\*\*(.*?)\*\*/g,`<strong style="color:${wc}">$1</strong>`);
  t=t.replace(/\n/g,'<br>');
  return t;
}
function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

// ── KEY MANAGEMENT ─────────────────────────────────────────
function setKey(i){
  activeKey=i;
  document.querySelectorAll('.kbtn:not(.kgear)').forEach((b,j)=>b.classList.toggle('on',j===i));
  toast(`🔑 Active: Key ${i+1}`); renderKlist();
}

function addKey(){
  const inp = document.getElementById('kadd');
  const val = inp.value.trim();
  if(!val.startsWith('sk-')){ toast('⚠ Invalid key format',true); return; }
  KEYS_INFO.push({label:`Key ${KEYS_INFO.length+1}`,val});
  inp.value='';
  // Add button to header
  const kz = document.getElementById('kzone');
  const ksep = kz.querySelector('.ksep');
  const b = document.createElement('button');
  const i = KEYS_INFO.length-1;
  b.className='kbtn'; b.id=`kb${i}`; b.textContent=`KEY·${i+1}`;
  b.onclick=()=>setKey(i);
  kz.insertBefore(b, ksep);
  renderKlist();
  toast(`🔑 Key ${KEYS_INFO.length} added`);
  // Persist to backend
  fetch(API+'/add_key',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:val})}).catch(()=>{});
}

function openModal(){ renderKlist(); document.getElementById('kov').classList.add('show'); }
function closeModal(){ document.getElementById('kov').classList.remove('show'); }
function renderKlist(){
  document.getElementById('klist').innerHTML=KEYS_INFO.map((k,i)=>`
    <div class="kopt ${activeKey===i?'on':''}" onclick="setKey(${i})">
      <div class="knum">${i+1}</div>
      <div class="kinfo">
        <div class="kl">${k.label}</div>
        <div class="kv">${k.val.slice(0,16)}…${k.val.slice(-6)}</div>
      </div>
    </div>`).join('');
}

// ── ABOUT MODAL ────────────────────────────────────────────
function openAbout(){  document.getElementById('about-ov').classList.add('show'); }
function closeAbout(){ document.getElementById('about-ov').classList.remove('show'); }

// ── TOAST ──────────────────────────────────────────────────
function toast(msg,warn=false){
  document.querySelector('.toast')?.remove();
  const t=document.createElement('div'); t.className='toast'+(warn?' warn':'');
  t.innerHTML=`<div class="toast-dot"></div>${msg}`;
  document.body.appendChild(t); setTimeout(()=>t.remove(),3500);
}

// ── BOOT ───────────────────────────────────────────────────
buildUI();
fetch(API+'/ping')
  .then(()=> setTimeout(()=>toast(`◈ ${AGENT} online`), 2200))
  .catch(()=>toast(`⚠ Run: python3 kali_agent_v2.py`,true));

document.addEventListener('keydown',e=>{
  if(e.target.tagName==='TEXTAREA'||e.target.tagName==='INPUT') return;
  if(e.key==='1') switchWin(0);
  if(e.key==='2') switchWin(1);
  if(e.key==='3') switchWin(2);
  if(e.key==='4') switchWin(3);
  if(e.key==='Escape'){ closeModal(); closeAbout(); }
});
</script>
</body>
</html>
"""

# ── HTTP HANDLER ───────────────────────────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, cfg=None, **kwargs):
        self.cfg = cfg or {}
        super().__init__(*args, **kwargs)

    def log_message(self, *a): pass

    def do_OPTIONS(self):
        self.send_response(200); self.cors(); self.end_headers()

    def do_GET(self):
        if self.path in ('/', '', '/index.html'):
            b = _CACHED_HTML.encode()
            self.send_response(200); self.cors()
            self.send_header("Content-Type", "text/html;charset=utf-8")
            self.send_header("Content-Length", len(b))
            self.end_headers(); self.wfile.write(b)
        elif self.path == '/ping':
            self.reply({"ok": True})
        else:
            self.send_error(404)

    def do_POST(self):
        try:
            l    = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(l))
        except:
            self.reply({"error": "bad request"}, 400); return

        cfg   = load_config()
        keys  = cfg.get("api_keys", [])
        aname = cfg.get("agent_name", "AGENT")

        if self.path == "/ask":
            try:
                model_req = body.get("model", "")
                ki        = int(body.get("key_index", 0))
                used_keys = keys[ki:] + keys[:ki] if keys else []
                msgs = [{"role": "system", "content": make_system(model_req, aname)}]
                for m in body.get("history", [])[-14:]: msgs.append(m)
                msgs.append({"role": "user", "content": body.get("prompt", "")})
                reply, model_used = call_ai(msgs, model_req, used_keys, aname)
                actions = run_actions(reply)
                if actions:
                    rt = "\n".join(f"[{a['type']}] {a['target']}\n→ {a['result']}" for a in actions)
                    msgs.append({"role": "assistant", "content": reply})
                    msgs.append({"role": "user", "content": f"Results:\n{rt}\n\nBriefly summarise what was done."})
                    reply, model_used = call_ai(msgs, model_req, used_keys, aname)
                    reply = re.sub(r"<think>[\s\S]*?</think>", "", reply).strip()
                clean = re.sub(r"<action[\s\S]*?</action>", "", reply).strip()
                self.reply({"reply": clean or reply, "actions": actions, "model": model_used})
            except Exception as e:
                print(f"  \033[91m[ERR]\033[0m {e}")
                self.reply({"error": str(e)}, 500)

        elif self.path == "/add_key":
            new_key = body.get("key", "")
            if new_key.startswith("sk-") and len(new_key) > 20:
                cfg["api_keys"].append(new_key)
                save_config(cfg)
                self.reply({"ok": True})
            else:
                self.reply({"error": "invalid key"}, 400)

        elif self.path == "/shell":
            self.reply({"output": shell(body.get("cmd", "")), "cwd": CWD[0]})
        elif self.path == "/write":
            self.reply({"result": write_file(body.get("path",""), body.get("content",""))})
        elif self.path == "/read":
            self.reply({"content": read_file(body.get("path",""))})
        elif self.path == "/ping":
            self.reply({"ok": True})
        else:
            self.send_error(404)

    def reply(self, data, code=200):
        b = json.dumps(data).encode()
        self.send_response(code); self.cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(b))
        self.end_headers(); self.wfile.write(b)

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

# ── MAIN ───────────────────────────────────────────────────────────────────────
_CACHED_HTML = ""

def print_runtime_banner(cfg):
    name  = cfg.get("agent_name", "AGENT").upper()
    theme = cfg.get("theme", "ghost")
    t     = THEMES.get(theme, THEMES["ghost"])
    tci   = THEME_TCOLORS[THEME_KEYS.index(theme)] if theme in THEME_KEYS else C
    nkeys = len(cfg.get("api_keys", []))

    print(f"\n{tci}")
    # ASCII art block for agent name
    w = max(52, len(name) + 12)
    print(f"  {'█'*w}")
    pad_l = (w - len(name) - 6) // 2
    pad_r = w - len(name) - 6 - pad_l
    print(f"  █{' ' * (w-2)}█")
    print(f"  █{' '*pad_l}  {BLD}{name}{RST}{tci}  {' '*pad_r}█")
    print(f"  █{' ' * (w-2)}█")
    print(f"  {'█'*w}{RST}")
    print(f"\n  {DIM}  AI Pentest Agent · Theme: {theme.upper()} · {nkeys} key(s){RST}")
    print(f"  {DIM}  powered by omar bouzganda · ⚠ Authorized use only{RST}")
    print(f"\n  {tci}  ◈ http://localhost:{PORT}{RST}")
    print(f"  {DIM}  User: {USER} | Home: {HOME}")
    print(f"  {DIM}  Models: GPT · Claude · DeepSeek · Venice + {len(FREE_FALLBACKS)} fallbacks{RST}")
    print(f"\n  {Y}  Ctrl+C to stop{RST}\n")

if __name__ == "__main__":
    cfg = load_config()

    # First run — interactive setup wizard
    if not cfg.get("setup_done"):
        cfg = first_run_setup()
        clr()

    # Cache the HTML with injected config
    _CACHED_HTML = make_html(cfg)

    # Runtime terminal banner
    print_runtime_banner(cfg)

    # Launch browser
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

    # Serve
    import functools
    HandlerWithCfg = functools.partial(Handler, cfg=cfg)
    try:
        http.server.HTTPServer(("", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print(f"\n  {R}[✗] {cfg.get('agent_name','AGENT').upper()} terminated.{RST}\n")
