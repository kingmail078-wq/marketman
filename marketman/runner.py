import argparse
import csv
import logging
from pathlib import Path
from typing import List

from strategy import Candle, generate_signals
from .config import Config, load_config
from .signals import serialize_signals

LOG = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_candles_from_csv(path: Path) -> List[Candle]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        candles: List[Candle] = []
        for row in reader:
            candles.append(
                Candle(
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )
    return candles


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Marketman signal runner")
    parser.add_argument("--config", required=True, help="Path to thresholds/config JSON")
    parser.add_argument("--data", required=True, help="Path to CSV data file with open,high,low,close,volume columns")
    parser.add_argument("--symbol", default="", help="Contract symbol (MNQ or MES)")
    parser.add_argument("--warmup", type=int, default=25, help="Warmup bars before generating signals")
    parser.add_argument("--format", default="json", choices=["json", "lines"], help="Output format")
    parser.add_argument("--output", help="Optional output file for serialized signals")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.log_level)

    try:
        config: Config = load_config(args.config)
    except Exception as exc:
        LOG.exception("Failed to load configuration %s", args.config)
        return 1

    if args.symbol:
        contract = config.get_contract(args.symbol)
        if not contract:
            LOG.warning("No contract configuration found for %s", args.symbol)
        else:
            LOG.info("Loaded contract config for %s", args.symbol.upper())

    try:
        candles = load_candles_from_csv(Path(args.data))
    except Exception as exc:
        LOG.exception("Failed to load candles from %s", args.data)
        return 1

    if not candles:
        LOG.error("No candles loaded from %s", args.data)
        return 1

    signals = generate_signals(candles, warmup=args.warmup)
    payload = serialize_signals(signals, fmt=args.format)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(payload, encoding="utf-8")
        LOG.info("Wrote %d signals to %s", len(signals), output_path)
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
