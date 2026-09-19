from __future__ import annotations

import json
from typing import Any, Dict


def encode_architecture(arch_dict: Dict[str, Any]) -> bytes:
    return json.dumps(arch_dict, separators=(",", ":")).encode("utf-8")


def decode_architecture(tape: bytes) -> Dict[str, Any]:
    if not tape:
        return {}
    return json.loads(tape.decode("utf-8"))
