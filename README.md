# Pomodoro Timer

A clean, minimal Pomodoro timer for Arch Linux / i3 window manager.

## Features
- 25 min focus / 5 min break / 15 min long break cycles
- Auto-plays lofi music via `lowfi` during focus sessions
- Custom chimes — 3-note chime on session end, fanfare after all 4 sessions
- Desktop notifications on session changes
- Skip break button when you're in the zone
- Skip music button to jump to the next track
- Stats tracker with Obsidian integration (daily notes auto-generated)
- Partial session saved on close if you focused for 5+ minutes
- Floats in the corner of your i3 desktop

## Dependencies
```bash
sudo pacman -S libnotify lowfi sox dunst
pip install customtkinter --user
```

## Usage
```bash
python3 pomodoro.py
```

Or add an alias to your `~/.bashrc`:
```bash
alias pomodoro='python3 /data/ai_learning/pomodoro/pomodoro.py'
```

Then reload: `source ~/.bashrc` and just type `pomodoro`.

## i3 Integration
Add to `~/.config/i3/config`:
```
for_window [title="Pomodoro"] floating enable, resize set 320 460, move position 1580 20
exec --no-startup-id dunst
```

---
🤖 Built with [Claude Code](https://claude.ai/code)
