import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

@dataclass
class Config:
    path: Path
    raw: Dict[str, Any]

    @property
    def contracts(self) -> Dict[str, Any]:
        return self.raw.get("contracts", {})

    @property
    def risk_management(self) -> Dict[str, Any]:
        return self.raw.get("risk_management", {})

    def get_contract(self, symbol: str) -> Dict[str, Any]:
        return self.contracts.get(symbol.upper(), {})


def load_config(path: str | Path) -> Config:
    p = Path(path)
    with p.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return Config(path=p, raw=raw)
