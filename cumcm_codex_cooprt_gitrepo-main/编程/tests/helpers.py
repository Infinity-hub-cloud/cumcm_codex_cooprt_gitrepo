from __future__ import annotations

from pathlib import Path

import numpy as np

from q1_baseline.data_contract import Q1InputData
from q1_baseline.parameters import Q1Parameters
from q1_baseline.time_index import build_official_q1_intervals


def toy_data(params: Q1Parameters | None = None) -> Q1InputData:
    params = params or Q1Parameters()
    return Q1InputData(
        intervals=build_official_q1_intervals(),
        price=np.ones(params.interval_count, dtype=np.float64),
        load_kw=np.full(params.interval_count, 600.0, dtype=np.float64),
        pv_kw=np.zeros(params.interval_count, dtype=np.float64),
        source_path=Path("TOY_DATA_NOT_OFFICIAL.csv"),
        source_sha256="TOY",
    )

