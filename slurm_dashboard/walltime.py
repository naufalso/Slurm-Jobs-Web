from dataclasses import dataclass
from typing import Optional

@dataclass
class WallTime:
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: int = 0

    def __post_init__(self):
        for attr in (self.days, self.hours, self.minutes, self.seconds):
            if attr < 0:
                raise ValueError("WallTime components must be non-negative")
        self._normalize()

    def _normalize(self):
        if self.seconds >= 60:
            self.minutes += self.seconds // 60
            self.seconds %= 60
        if self.minutes >= 60:
            self.hours += self.minutes // 60
            self.minutes %= 60
        if self.hours >= 24:
            self.days += self.hours // 24
            self.hours %= 24

    @staticmethod
    def from_string(time: str) -> 'WallTime':
        """Parse strings like D-HH:MM:SS or HH:MM:SS or MM:SS or SS"""
        if not time:
            raise ValueError("Invalid time string")
        if '-' in time:
            day_part, time = time.split('-', 1)
            days = int(day_part)
        else:
            days = 0
        parts = time.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
        elif len(parts) == 2:
            hours = 0
            minutes, seconds = map(int, parts)
        elif len(parts) == 1:
            hours = minutes = 0
            seconds = int(parts[0])
        else:
            raise ValueError(f"Invalid time string {time}")
        return WallTime(days, hours, minutes, seconds)

    def to_seconds(self) -> int:
        return self.seconds + self.minutes * 60 + self.hours * 3600 + self.days * 86400

    def __str__(self) -> str:
        if self.days:
            return f"{self.days}-{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}"
        if self.hours:
            return f"{self.hours}:{self.minutes:02d}:{self.seconds:02d}"
        if self.minutes:
            return f"{self.minutes:02d}:{self.seconds:02d}"
        return f"{self.seconds:02d}"
