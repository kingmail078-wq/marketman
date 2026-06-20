import json
from typing import Any, Dict, List


def serialize_signals(signals: List[Any], fmt: str = "json") -> str:
    records: List[Dict[str, Any]] = []
    for signal in signals:
        record: Dict[str, Any] = {
            "index": signal.index,
            "signal": signal.signal,
            "reason": signal.reason,
        }
        metadata = getattr(signal, "metadata", None)
        if metadata is not None:
            record["metadata"] = metadata
        records.append(record)

    if fmt == "json":
        return json.dumps(records, indent=2)
    if fmt == "lines":
        return "\n".join(json.dumps(record) for record in records)
    raise ValueError(f"Unsupported format: {fmt}")
