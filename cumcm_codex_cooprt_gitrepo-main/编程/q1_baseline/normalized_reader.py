from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np

from .data_contract import DataContractError, Q1InputData
from .parameters import Q1Parameters
from .time_index import TemplateInterval, official_interval_label


REQUIRED_COLUMNS = {
    "interval_index",
    "sample_time_label",
    "sample_minute",
    "interval_start_day_offset",
    "interval_start_minute",
    "interval_end_day_offset",
    "interval_end_minute",
    "price_yuan_per_kwh",
    "load_kw",
    "pv_forecast_kw",
    "load_kwh",
    "pv_kwh",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_q1_normalized(path: str | Path, params: Q1Parameters) -> Q1InputData:
    source = Path(path).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames or ())
        if missing:
            raise DataContractError(f"normalized input missing columns: {sorted(missing)}")
        rows = list(reader)
    if len(rows) != params.interval_count:
        raise DataContractError(
            f"normalized input must contain {params.interval_count} rows, got {len(rows)}"
        )

    intervals: list[TemplateInterval] = []
    price: list[float] = []
    load_kw: list[float] = []
    pv_kw: list[float] = []
    for expected_slot, row in enumerate(rows, start=1):
        slot = int(row["interval_index"])
        start_day = int(row["interval_start_day_offset"])
        start_clock = int(row["interval_start_minute"])
        end_day = int(row["interval_end_day_offset"])
        end_clock = int(row["interval_end_minute"])
        absolute_start = 1440 * start_day + start_clock
        absolute_end = 1440 * end_day + end_clock
        intervals.append(
            TemplateInterval(
                template_slot=slot,
                sample_time_label=row["sample_time_label"],
                sample_minute=int(row["sample_minute"]),
                interval_start_day_offset=start_day,
                interval_start_minute=start_clock,
                interval_end_day_offset=end_day,
                interval_end_minute=end_clock,
                official_template_label=official_interval_label(
                    absolute_start, absolute_end
                ),
            )
        )
        if slot != expected_slot:
            raise DataContractError(f"interval_index mismatch at row {expected_slot}")
        price.append(float(row["price_yuan_per_kwh"]))
        load_kw.append(float(row["load_kw"]))
        pv_kw.append(float(row["pv_forecast_kw"]))

        expected_load = float(row["load_kw"]) * params.delta_t
        expected_pv = float(row["pv_forecast_kw"]) * params.delta_t
        if abs(float(row["load_kwh"]) - expected_load) > 5.1e-4:
            raise DataContractError(f"load kW-to-kWh mismatch at slot {slot}")
        if abs(float(row["pv_kwh"]) - expected_pv) > 5.1e-4:
            raise DataContractError(f"PV kW-to-kWh mismatch at slot {slot}")

    result = Q1InputData(
        intervals=tuple(intervals),
        price=np.asarray(price, dtype=np.float64),
        load_kw=np.asarray(load_kw, dtype=np.float64),
        pv_kw=np.asarray(pv_kw, dtype=np.float64),
        source_path=source,
        source_sha256=sha256_file(source),
    )
    result.validate(params)
    return result

