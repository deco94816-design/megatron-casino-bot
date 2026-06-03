"""Event service — golden hour, cashback, rain, deposit bonuses."""

# Event state (extracted from global variables)
golden_hour_active = False
golden_hour_multiplier = 1.0
golden_hour_end_time = None

cashback_active = False
cashback_rate = 0.0

double_deposit_active = False
triple_deposit_active = False

rain_event_active = False
rain_event_amount = 0


def is_golden_hour():
    """Check if golden hour is currently active."""
    return golden_hour_active


def get_golden_hour_multiplier():
    """Get the current golden hour multiplier."""
    return golden_hour_multiplier if golden_hour_active else 1.0


def is_cashback_active():
    """Check if cashback event is active."""
    return cashback_active


def get_cashback_rate():
    """Get the current cashback rate."""
    return cashback_rate if cashback_active else 0.0


def is_double_deposit():
    """Check if double deposit is active."""
    return double_deposit_active


def is_triple_deposit():
    """Check if triple deposit is active."""
    return triple_deposit_active
