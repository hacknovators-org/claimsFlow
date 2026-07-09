import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

EAT = ZoneInfo("Africa/Nairobi")

_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})")

HELP_TEXT = (
    "Claims bot commands:\n"
    "PROCESS - run claims processing now\n"
    "PROCESS 14:30 - schedule processing at 14:30 EAT\n"
    "STATUS - get last processing summary"
)


@dataclass
class SmsCommand:
    action: str  # "process_now" | "schedule" | "status" | "unknown"
    run_at: Optional[datetime] = None
    raw_text: str = ""


def parse_command(text: str) -> SmsCommand:
    raw = (text or "").strip()
    normalized = raw.upper()

    if normalized in ("STATUS", "STATS"):
        return SmsCommand(action="status", raw_text=raw)

    if normalized.startswith("PROCESS"):
        match = _TIME_RE.search(normalized)
        if not match:
            return SmsCommand(action="process_now", raw_text=raw)

        hour, minute = int(match.group(1)), int(match.group(2))
        if not (0 <= hour < 24 and 0 <= minute < 60):
            return SmsCommand(action="unknown", raw_text=raw)

        now = datetime.now(EAT)
        run_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if run_at <= now:
            run_at += timedelta(days=1)

        return SmsCommand(action="schedule", run_at=run_at, raw_text=raw)

    return SmsCommand(action="unknown", raw_text=raw)
