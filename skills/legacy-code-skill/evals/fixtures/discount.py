"""Original fixture with an intentionally retained rounding defect."""


def discounted(cents: int, percent: int) -> int:
    if cents < 0 or not 0 <= percent <= 100:
        raise ValueError("Invalid price or percent")
    return cents - int(cents * percent / 100)
