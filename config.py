# Pomodoro Timer Configuration

WORK_MINUTES = 25
SHORT_BREAK_MINUTES = 5
LONG_BREAK_MINUTES = 15
CYCLES_BEFORE_LONG_BREAK = 4

for _name, _val in [("WORK_MINUTES", WORK_MINUTES), ("SHORT_BREAK_MINUTES", SHORT_BREAK_MINUTES),
                    ("LONG_BREAK_MINUTES", LONG_BREAK_MINUTES), ("CYCLES_BEFORE_LONG_BREAK", CYCLES_BEFORE_LONG_BREAK)]:
    if not isinstance(_val, int) or _val < 1:
        raise ValueError(f"config.py: {_name} must be a positive integer (got {_val!r})")

MOTIVATIONAL_MESSAGES = [
    "Let's get it.",
    "One session at a time.",
    "You've got this.",
    "Stay locked in.",
    "Build something today.",
    "Small steps, big progress.",
    "Focus. Then rest. Repeat.",
    "Present moment only.",
]
