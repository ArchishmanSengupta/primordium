from __future__ import annotations

import json
import os
from typing import Any, Dict, List


class MetricsWriter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.path = os.path.join(output_dir, "metrics.jsonl")
        self._file = None

    def open(self, append: bool = False) -> None:
        mode = "a" if append else "w"
        self._file = open(self.path, mode, encoding="utf-8")

    def write(self, record: Dict[str, Any]) -> None:
        if self._file is None:
            raise RuntimeError("MetricsWriter not open")
        self._file.write(json.dumps(record) + "\n")

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None

    def read_all(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        records: List[Dict[str, Any]] = []
        with open(self.path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
