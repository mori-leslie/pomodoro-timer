# Pomodoro Timer

A clean, minimal Pomodoro timer for Arch Linux / i3 window manager.

## Features
- 25 min focus / 5 min break / 15 min long break cycles
- Auto-plays lofi music via `lowfi` during focus sessions
- Desktop notifications on session changes
- Skip break button when you're in the zone
- Stats tracker with Obsidian integration
- Floats in the corner of your i3 desktop

## Dependencies
```bash
sudo pacman -S libnotify lowfi
pip install customtkinter
```

## Usage
```bash
python pomodoro.py
```

Or add an alias to your `~/.bashrc`:
```bash
alias pomodoro='/path/to/ai_env/bin/python /path/to/pomodoro.py'
```

## i3 Integration
Add to `~/.config/i3/config`:
```
for_window [title="Pomodoro"] floating enable, resize set 320 460, move position 1580 20
```

---
🤖 Built with [Claude Code](https://claude.ai/code)
