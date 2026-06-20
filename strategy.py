from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class BookSnapshot:
    bid: float
    ask: float
    bid_size: float
    ask_size: float

    @property
    def imbalance(self) -> float:
        if self.ask_size <= 0:
            return float("inf")
        return self.bid_size / self.ask_size

@dataclass
class Signal:
    index: int
    signal: str
    reason: str


def ema(values: List[float], period: int) -> List[Optional[float]]:
    if period <= 0 or not values:
        return []
    multiplier = 2 / (period + 1)
    result: List[Optional[float]] = [None] * len(values)
    result[period - 1] = sum(values[:period]) / period
    for i in range(period, len(values)):
        result[i] = (values[i] - result[i - 1]) * multiplier + result[i - 1]  # type: ignore
    return result


def tema(values: List[float], period: int) -> List[Optional[float]]:
    first = ema(values, period)
    first_values = [v for v in first if v is not None]
    if len(first_values) < period:
        return [None] * len(values)
    second = ema(first_values, period)
    if len(second) < period:
        return [None] * len(values)
    third = ema(second, period)
    if len(third) == 0:
        return [None] * len(values)
    result: List[Optional[float]] = [None] * len(values)
    for i in range(len(values)):
        if i < 3 * period - 3:
            continue
        e1 = first[i]
        e2 = second[i - (period - 1)] if i - (period - 1) < len(second) else None
        e3 = third[i - 2 * (period - 1)] if i - 2 * (period - 1) < len(third) else None
        if e1 is not None and e2 is not None and e3 is not None:
            result[i] = 3 * e1 - 3 * e2 + e3
    return result


def vwap(candles: List[Candle]) -> List[Optional[float]]:
    cumul_vol_price = 0.0
    cumul_vol = 0.0
    result: List[Optional[float]] = []
    for candle in candles:
        typical_price = (candle.high + candle.low + candle.close) / 3
        cumul_vol_price += typical_price * candle.volume
        cumul_vol += candle.volume
        result.append(cumul_vol_price / cumul_vol if cumul_vol else None)
    return result


def bollinger_bands(values: List[float], period: int = 20, std_multiplier: float = 2.0):
    result = []
    for i in range(len(values)):
        if i + 1 < period:
            result.append((None, None, None))
            continue
        window = values[i + 1 - period : i + 1]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = variance ** 0.5
        result.append((mean, mean + std_multiplier * std, mean - std_multiplier * std))
    return result


def rsi(values: List[float], period: int = 14) -> List[Optional[float]]:
    if len(values) < period + 1:
        return [None] * len(values)
    gains = [0.0]
    losses = [0.0]
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    avg_gain = sum(gains[1 : period + 1]) / period
    avg_loss = sum(losses[1 : period + 1]) / period
    result = [None] * (period)
    result.append(100 - 100 / (1 + avg_gain / avg_loss)) if avg_loss != 0 else result.append(100.0)
    for i in range(period + 1, len(values)):
        gain = gains[i]
        loss = losses[i]
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        result.append(100 - 100 / (1 + avg_gain / avg_loss)) if avg_loss != 0 else result.append(100.0)
    return result


def average_true_range(candles: List[Candle], period: int = 14) -> List[Optional[float]]:
    result: List[Optional[float]] = [None] * len(candles)
    if len(candles) < period + 1:
        return result
    tr_values: List[float] = []
    for i in range(1, len(candles)):
        high_low = candles[i].high - candles[i].low
        high_prev_close = abs(candles[i].high - candles[i - 1].close)
        low_prev_close = abs(candles[i].low - candles[i - 1].close)
        tr_values.append(max(high_low, high_prev_close, low_prev_close))
    avg_tr = sum(tr_values[:period]) / period
    result[period] = avg_tr
    for i in range(period + 1, len(candles)):
        avg_tr = (avg_tr * (period - 1) + tr_values[i - 1]) / period
        result[i] = avg_tr
        result[i] = avg_tr
    return result


def vwap_deviation_bands(vwap_values: List[Optional[float]], atr_values: List[Optional[float]], factor: float = 1.0) -> List[Tuple[Optional[float], Optional[float], Optional[float]]]:
    bands: List[Tuple[Optional[float], Optional[float], Optional[float]]] = []
    for vwap_value, atr_value in zip(vwap_values, atr_values):
        if vwap_value is None or atr_value is None:
            bands.append((None, None, None))
            continue
        upper = vwap_value + factor * atr_value
        lower = vwap_value - factor * atr_value
        bands.append((vwap_value, upper, lower))
    return bands


def low_volatility_regime(atr_values: List[Optional[float]], lookback: int = 20, threshold: float = 0.75) -> List[bool]:
    result: List[bool] = [False] * len(atr_values)
    for i in range(len(atr_values)):
        if atr_values[i] is None or i < lookback:
            result[i] = False
            continue
        window = [x for x in atr_values[i - lookback + 1 : i + 1] if x is not None]
        if len(window) < lookback:
            result[i] = False
            continue
        avg_atr = sum(window) / len(window)
        result[i] = atr_values[i] < avg_atr * threshold
    return result


def rsi_boundaries(is_low_vol: bool) -> Tuple[int, int]:
    return (60, 40) if is_low_vol else (70, 30)


def aggregate_candles(candles: List[Candle], factor: int) -> List[Candle]:
    if factor <= 1 or len(candles) < factor:
        return candles[:]
    aggregated: List[Candle] = []
    for start in range(0, len(candles), factor):
        block = candles[start : start + factor]
        if not block:
            continue
        aggregated.append(
            Candle(
                open=block[0].open,
                high=max(c.high for c in block),
                low=min(c.low for c in block),
                close=block[-1].close,
                volume=sum(c.volume for c in block),
            )
        )
    return aggregated


def recent_pivot_range(candles: List[Candle], index: int, lookback: int = 20) -> Tuple[float, float]:
    start = max(0, index - lookback)
    segment = candles[start:index]
    if not segment:
        return (0.0, 0.0)
    return (max(c.high for c in segment), min(c.low for c in segment))


def detect_fvg_zones(candles: List[Candle]) -> List[Tuple[Optional[str], float, float]]:
    result: List[Tuple[Optional[str], float, float]] = [ (None, 0.0, 0.0) for _ in candles]
    for i in range(2, len(candles)):
        previous = candles[i - 2]
        current = candles[i]
        if previous.high < current.low:
            result[i] = ("bullish", previous.high, current.low)
        elif previous.low > current.high:
            result[i] = ("bearish", current.high, previous.low)
    return result


def detect_order_block_zones(candles: List[Candle]) -> List[Tuple[Optional[str], float, float]]:
    result: List[Tuple[Optional[str], float, float]] = [ (None, 0.0, 0.0) for _ in candles]
    for i in range(1, len(candles)):
        prior = candles[i - 1]
        current = candles[i]
        if prior.close < prior.open and current.close > current.open and current.close > prior.high:
            result[i] = ("bullish", prior.low, prior.high)
        elif prior.close > prior.open and current.close < current.open and current.close < prior.low:
            result[i] = ("bearish", prior.low, prior.high)
    return result


def session_high_low(candles: List[Candle]) -> Tuple[float, float]:
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    return (max(highs), min(lows)) if candles else (0.0, 0.0)


def volume_value_area(candles: List[Candle], bins: int = 24, target: float = 0.7) -> Tuple[float, float, float]:
    if not candles:
        return 0.0, 0.0, 0.0
    low = min(c.low for c in candles)
    high = max(c.high for c in candles)
    if high <= low:
        return low, low, low
    bin_size = (high - low) / bins
    volumes = [0.0] * bins
    centers = [low + bin_size * (i + 0.5) for i in range(bins)]
    for candle in candles:
        price = (candle.high + candle.low + candle.close) / 3
        index = min(bins - 1, int((price - low) / bin_size))
        volumes[index] += candle.volume
    poc_index = max(range(bins), key=lambda i: volumes[i])
    total = sum(volumes)
    target_volume = total * target
    included = {poc_index}
    accumulated = volumes[poc_index]
    left = poc_index - 1
    right = poc_index + 1
    while accumulated < target_volume and (left >= 0 or right < bins):
        left_vol = volumes[left] if left >= 0 else -1.0
        right_vol = volumes[right] if right < bins else -1.0
        if left_vol >= right_vol and left >= 0:
            included.add(left)
            accumulated += left_vol
            left -= 1
        elif right < bins:
            included.add(right)
            accumulated += right_vol
            right += 1
        else:
            break
    area_low = min(centers[i] for i in included)
    area_high = max(centers[i] for i in included)
    return centers[poc_index], area_low, area_high


def value_area_state(price: float, val: float, vah: float) -> str:
    if val <= price <= vah:
        return "inside"
    if price > vah:
        return "above"
    return "below"


def find_recent_zone(zones: List[Tuple[Optional[str], float, float]], index: int, lookback: int = 12) -> Tuple[Optional[str], float, float]:
    start = max(0, index - lookback)
    for i in range(index, start - 1, -1):
        direction, low, high = zones[i]
        if direction is not None:
            return direction, low, high
    return None, 0.0, 0.0


def is_retest(candles: List[Candle], index: int, level: float, direction: str, tolerance: float) -> bool:
    start = max(0, index - 4)
    for i in range(start, index):
        if direction == "long" and candles[i].low <= level + tolerance and candles[i].high >= level:
            return True
        if direction == "short" and candles[i].high >= level - tolerance and candles[i].low <= level:
            return True
    return False


def book_bias_strength(book: Optional[BookSnapshot]) -> Tuple[bool, bool]:
    if book is None:
        return False, False
    if book.imbalance >= 1.2:
        return True, False
    if book.imbalance <= 0.8:
        return False, True
    return False, False


def vwap_bounce_long(candles: List[Candle], index: int, vwap_val: float) -> bool:
    if index < 1 or vwap_val is None:
        return False
    close = candles[index].close
    low = candles[index].low
    return close > vwap_val and low <= vwap_val


def vwap_bounce_short(candles: List[Candle], index: int, vwap_val: float) -> bool:
    if index < 1 or vwap_val is None:
        return False
    close = candles[index].close
    high = candles[index].high
    return close < vwap_val and high >= vwap_val


def vwap_break_hold_long(vwap_values: List[Optional[float]], index: int, close: float, lookback: int = 3) -> bool:
    if index < lookback:
        return False
    segment = vwap_values[index - lookback : index + 1]
    if any(v is None for v in segment):
        return False
    return close > vwap_values[index] and all(segment[i] <= segment[i + 1] for i in range(len(segment) - 1))


def vwap_break_hold_short(vwap_values: List[Optional[float]], index: int, close: float, lookback: int = 3) -> bool:
    if index < lookback:
        return False
    segment = vwap_values[index - lookback : index + 1]
    if any(v is None for v in segment):
        return False
    return close < vwap_values[index] and all(segment[i] >= segment[i + 1] for i in range(len(segment) - 1))


def poc_reversion_long(candles: List[Candle], index: int, poc: float, lookback: int = 5) -> bool:
    if index < lookback or poc <= 0.0:
        return False
    start = index - lookback
    sweep = min(candles[start : index + 1], key=lambda c: c.low).low
    return sweep < poc and candles[index].close > poc


def poc_reversion_short(candles: List[Candle], index: int, poc: float, lookback: int = 5) -> bool:
    if index < lookback or poc <= 0.0:
        return False
    start = index - lookback
    sweep = max(candles[start : index + 1], key=lambda c: c.high).high
    return sweep > poc and candles[index].close < poc


def value_area_rotation_long(candles: List[Candle], index: int, val: float, vah: float, lookback: int = 5) -> bool:
    if index < lookback or val <= 0.0 or vah <= 0.0:
        return False
    prior_outside = any(candles[i].low < val for i in range(index - lookback, index))
    current_inside = val <= candles[index].close <= vah
    return prior_outside and current_inside


def value_area_rotation_short(candles: List[Candle], index: int, val: float, vah: float, lookback: int = 5) -> bool:
    if index < lookback or val <= 0.0 or vah <= 0.0:
        return False
    prior_outside = any(candles[i].high > vah for i in range(index - lookback, index))
    current_inside = val <= candles[index].close <= vah
    return prior_outside and current_inside


def value_area_breakout_long(candles: List[Candle], index: int, vah: float, book: Optional[BookSnapshot] = None) -> bool:
    if candles[index].close <= vah:
        return False
    bid_agg = book is not None and book.imbalance >= 1.2 if book else True
    return bid_agg


def value_area_breakout_short(candles: List[Candle], index: int, val: float, book: Optional[BookSnapshot] = None) -> bool:
    if candles[index].close >= val:
        return False
    ask_agg = book is not None and book.imbalance <= 0.8 if book else True
    return ask_agg


def dom_bias_long(candles: List[Candle], index: int) -> bool:
    """Detect aggressive buying: delta rising, high ask pressure, absorption of selling."""
    if index < 3:
        return False
    close = candles[index].close
    open_ = candles[index].open
    vol = candles[index].volume
    low = candles[index].low
    
    # Delta proxy
    delta_bar = vol if close > open_ else -vol if close < open_ else 0
    
    # Bid/Ask pressure approximation
    ask_pressure = vol if close > open_ else vol * 0.3
    bid_pressure = vol if close < open_ else vol * 0.3
    pressure_total = ask_pressure + bid_pressure
    buy_aggression = ask_pressure / pressure_total if pressure_total > 0 else 0
    
    # Delta trend (rising for 3+ bars)
    delta_segment = [
        candles[index - 3].volume if candles[index - 3].close > candles[index - 3].open else -candles[index - 3].volume,
        candles[index - 2].volume if candles[index - 2].close > candles[index - 2].open else -candles[index - 2].volume,
        candles[index - 1].volume if candles[index - 1].close > candles[index - 1].open else -candles[index - 1].volume,
        delta_bar,
    ]
    delta_up = all(delta_segment[i] <= delta_segment[i + 1] for i in range(len(delta_segment) - 1))
    
    # Absorption: low but delta positive (less selling pressure absorbed)
    low_absorption = low < candles[index - 1].low and delta_bar > (delta_segment[-2] if len(delta_segment) > 1 else 0)
    
    # Imbalance: ask > bid * 1.5
    imbalance = ask_pressure > bid_pressure * 1.5
    
    return (buy_aggression > 0.60) or delta_up or low_absorption or imbalance


def dom_bias_short(candles: List[Candle], index: int) -> bool:
    """Detect aggressive selling: delta falling, high bid pressure, absorption of buying."""
    if index < 3:
        return False
    close = candles[index].close
    open_ = candles[index].open
    vol = candles[index].volume
    high = candles[index].high
    
    # Delta proxy
    delta_bar = vol if close > open_ else -vol if close < open_ else 0
    
    # Bid/Ask pressure approximation
    ask_pressure = vol if close > open_ else vol * 0.3
    bid_pressure = vol if close < open_ else vol * 0.3
    pressure_total = ask_pressure + bid_pressure
    sell_aggression = bid_pressure / pressure_total if pressure_total > 0 else 0
    
    # Delta trend (falling for 3+ bars)
    delta_segment = [
        candles[index - 3].volume if candles[index - 3].close > candles[index - 3].open else -candles[index - 3].volume,
        candles[index - 2].volume if candles[index - 2].close > candles[index - 2].open else -candles[index - 2].volume,
        candles[index - 1].volume if candles[index - 1].close > candles[index - 1].open else -candles[index - 1].volume,
        delta_bar,
    ]
    delta_down = all(delta_segment[i] >= delta_segment[i + 1] for i in range(len(delta_segment) - 1))
    
    # Absorption: high but delta negative (less buying pressure absorbed)
    high_absorption = high > candles[index - 1].high and delta_bar < (delta_segment[-2] if len(delta_segment) > 1 else 0)
    
    # Imbalance: bid > ask * 1.5
    imbalance = bid_pressure > ask_pressure * 1.5
    
    return (sell_aggression > 0.60) or delta_down or high_absorption or imbalance


def confluence_score_long(
    vwap_bounce: bool,
    vwap_break: bool,
    poc_rev: bool,
    va_rot: bool,
    va_breakout: bool,
    price_at_val: bool,
    price_at_vwap_lower: bool,
    rsi_val: float,
    dom_bias: bool,
    ny_open: bool,
    pm_phase: bool,
) -> int:
    score = 0
    if vwap_bounce:
        score += 1
    if vwap_break:
        score += 2
    if poc_rev:
        score += 2
    if va_rot:
        score += 1
    if va_breakout:
        score += 2
    if price_at_val:
        score += 1
    if price_at_vwap_lower:
        score += 1
    if rsi_val < 40:
        score += 1
    if dom_bias:
        score += 2
    if ny_open or pm_phase:
        score += 1
    return score


def confluence_score_short(
    vwap_bounce: bool,
    vwap_break: bool,
    poc_rev: bool,
    va_rot: bool,
    va_breakout: bool,
    price_at_vah: bool,
    price_at_vwap_upper: bool,
    rsi_val: float,
    dom_bias: bool,
    ask_strong: bool,
    ny_open: bool,
    pm_phase: bool,
) -> int:
    score = 0
    if vwap_bounce:
        score += 1
    if vwap_break:
        score += 2
    if poc_rev:
        score += 2
    if va_rot:
        score += 1
    if va_breakout:
        score += 2
    if price_at_vah:
        score += 1
    if price_at_vwap_upper:
        score += 1
    if rsi_val > 60:
        score += 1
    if dom_bias:
        score += 2
    if ny_open or pm_phase:
        score += 1
    return score


def delta_divergence_long(candles: List[Candle], index: int) -> bool:
    """Detect DOM exhaustion on long: price new high but delta lower."""
    if index < 1:
        return False
    high_now = candles[index].high
    high_prev = candles[index - 1].high
    close_now = candles[index].close
    close_prev = candles[index - 1].close
    open_now = candles[index].open
    open_prev = candles[index - 1].open
    
    delta_now = candles[index].volume if close_now > open_now else -candles[index].volume
    delta_prev = candles[index - 1].volume if close_prev > open_prev else -candles[index - 1].volume
    
    return high_now > high_prev and delta_now < delta_prev


def delta_divergence_short(candles: List[Candle], index: int) -> bool:
    """Detect DOM exhaustion on short: price new low but delta higher."""
    if index < 1:
        return False
    low_now = candles[index].low
    low_prev = candles[index - 1].low
    close_now = candles[index].close
    close_prev = candles[index - 1].close
    open_now = candles[index].open
    open_prev = candles[index - 1].open
    
    delta_now = candles[index].volume if close_now > open_now else -candles[index].volume
    delta_prev = candles[index - 1].volume if close_prev > open_prev else -candles[index - 1].volume
    
    return low_now < low_prev and delta_now > delta_prev


def generate_signals(candles: List[Candle], book: Optional[BookSnapshot] = None, warmup: int = 25) -> List[Signal]:
    closes = [c.close for c in candles]
    ema20 = ema(closes, 20)
    tema21 = tema(closes, 21)
    vwap_values = vwap(candles)
    atr_values = average_true_range(candles, period=14)
    vwap_bands = vwap_deviation_bands(vwap_values, atr_values, factor=1.0)
    rsi_values = rsi(closes, period=14)
    low_vol = low_volatility_regime(atr_values, lookback=20, threshold=0.75)
    fvg_zones = detect_fvg_zones(candles)
    order_blocks = detect_order_block_zones(candles)
    session_high, session_low = session_high_low(candles)
    poc, value_low, value_high = volume_value_area(candles, bins=24, target=0.7)
    va_state = value_area_state(closes[-1], value_low, value_high) if candles else "inside"
    htf_candles = aggregate_candles(candles, factor=3)
    htf_ema = ema([c.close for c in htf_candles], 20) if len(htf_candles) >= 20 else [None] * len(htf_candles)
    book_long, book_short = book_bias_strength(book)

    signals: List[Signal] = []
    if warmup < 0:
        warmup = 0
    for i in range(len(candles)):
        if i < warmup:
            continue
        close = closes[i]
        current_ema = ema20[i]
        current_vwap = vwap_values[i]
        current_rsi = rsi_values[i]
        atr = atr_values[i] or 0.0
        vwap_center, vwap_upper, vwap_lower = vwap_bands[i]
        low_vol_regime = low_vol[i]
        rsi_high, rsi_low = rsi_boundaries(low_vol_regime)
        if current_ema is None or current_vwap is None or current_rsi is None or vwap_center is None or vwap_upper is None or vwap_lower is None:
            continue

        ny_hour = i % 10
        session_phase_open = ny_hour < 1
        session_phase_pm = 8 <= ny_hour < 9

        vwap_bounce_lng = vwap_bounce_long(candles, i, current_vwap)
        vwap_bounce_sht = vwap_bounce_short(candles, i, current_vwap)
        vwap_break_lng = vwap_break_hold_long(vwap_values, i, close, lookback=3)
        vwap_break_sht = vwap_break_hold_short(vwap_values, i, close, lookback=3)
        poc_rev_lng = poc_reversion_long(candles, i, poc, lookback=5)
        poc_rev_sht = poc_reversion_short(candles, i, poc, lookback=5)
        va_rot_lng = value_area_rotation_long(candles, i, value_low, value_high, lookback=5)
        va_rot_sht = value_area_rotation_short(candles, i, value_low, value_high, lookback=5)
        va_breakout_lng = value_area_breakout_long(candles, i, value_high, book)
        va_breakout_sht = value_area_breakout_short(candles, i, value_low, book)

        price_at_val = close <= value_low + atr * 0.5
        price_at_vah = close >= value_high - atr * 0.5
        price_at_vwap_lower = close <= vwap_lower + atr * 0.25
        price_at_vwap_upper = close >= vwap_upper - atr * 0.25

        score_long = confluence_score_long(
            vwap_bounce_lng,
            vwap_break_lng,
            poc_rev_lng,
            va_rot_lng,
            va_breakout_lng,
            price_at_val,
            price_at_vwap_lower,
            current_rsi,
            book_long,
            session_phase_open,
            session_phase_pm,
        )
        score_short = confluence_score_short(
            vwap_bounce_sht,
            vwap_break_sht,
            poc_rev_sht,
            va_rot_sht,
            va_breakout_sht,
            price_at_vah,
            price_at_vwap_upper,
            current_rsi,
            book_short,
            book_short,
            session_phase_open,
            session_phase_pm,
        )

        if score_long >= 4 and current_rsi < rsi_low + 15:
            reason = (
                f"VWAP+POC+VA confluence (score={score_long}): "
                f"{'bounce' if vwap_bounce_lng else ''} {'break' if vwap_break_lng else ''} "
                f"{'poc_rev' if poc_rev_lng else ''} {'va_rot' if va_rot_lng else ''} {'va_breakout' if va_breakout_lng else ''}; "
                f"Price at VAL/VWAP-lower; RSI={current_rsi:.0f} < {rsi_low + 15}; session={'Open' if session_phase_open else 'PM'}."
            )
            signals.append(Signal(i, "BUY", reason))

        if score_short >= 4 and current_rsi > rsi_high - 15:
            reason = (
                f"VWAP+POC+VA confluence (score={score_short}): "
                f"{'bounce' if vwap_bounce_sht else ''} {'break' if vwap_break_sht else ''} "
                f"{'poc_rev' if poc_rev_sht else ''} {'va_rot' if va_rot_sht else ''} {'va_breakout' if va_breakout_sht else ''}; "
                f"Price at VAH/VWAP-upper; RSI={current_rsi:.0f} > {rsi_high - 15}; session={'Open' if session_phase_open else 'PM'}."
            )
            signals.append(Signal(i, "SELL", reason))

        # Exit signals: DOM divergence and bias flips
        div_long = delta_divergence_long(candles, i)
        div_short = delta_divergence_short(candles, i)
        
        if div_long:
            reason = f"DOM exhaustion on long: price new high ({candles[i].high:.2f}) but delta declining; tighten stop or exit."
            signals.append(Signal(i, "EXIT_LONG", reason))
        
        if div_short:
            reason = f"DOM exhaustion on short: price new low ({candles[i].low:.2f}) but delta rising; tighten stop or exit."
            signals.append(Signal(i, "EXIT_SHORT", reason))

    return signals


