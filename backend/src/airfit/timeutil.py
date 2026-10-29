from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9), "KST")


def from_unix(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, KST)


def from_airkorea(text: str) -> datetime:
    """에어코리아 시각("2026-10-29 10:00")을 KST로. 자정은 "24:00"으로 온다."""
    day, clock = text.split()
    if clock == "24:00":
        return datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=KST) + timedelta(days=1)
    return datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
