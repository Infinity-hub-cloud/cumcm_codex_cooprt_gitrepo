import datetime as dt
import tempfile
import unittest
from pathlib import Path

from preprocess_audit import (
    expected_sample_minutes,
    map_instantaneous_sample,
    map_hourly_target,
    parse_clock_minutes,
    parse_interval_label,
    parse_date_value,
    collect_manifest,
)


class TimeParsingTests(unittest.TestCase):
    def test_parse_midnight_next_day_label(self):
        self.assertEqual(parse_clock_minutes("0:00+1"), 1440)

    def test_parse_ten_minutes_after_midnight_next_day_label(self):
        self.assertEqual(parse_clock_minutes("0:10+1"), 1450)

    def test_parse_excel_time(self):
        self.assertEqual(parse_clock_minutes(dt.time(1, 10)), 70)

    def test_parse_interval_label_with_next_day_end(self):
        self.assertEqual(parse_interval_label("23:50-0:00+1"), (1430, 1440))

    def test_parse_template_last_interval_with_implicit_next_day_start(self):
        self.assertEqual(parse_interval_label("0:00-0:10+1"), (1440, 1450))

    def test_parse_unpadded_minute_label(self):
        self.assertEqual(parse_interval_label("7:0-7:10"), (420, 430))

    def test_expected_sample_instants_are_contiguous(self):
        sample_minutes = expected_sample_minutes(interval_count=144, delta_minutes=10)
        self.assertEqual(sample_minutes[0], 10)
        self.assertEqual(sample_minutes[-1], 1440)
        self.assertEqual(len(sample_minutes), 144)

    def test_instantaneous_sample_maps_to_following_interval(self):
        mapped = map_instantaneous_sample(
            sample_date=dt.date(2025, 1, 1),
            sample_minutes=10,
            delta_minutes=10,
        )
        self.assertEqual(mapped.interval_start_date, dt.date(2025, 1, 1))
        self.assertEqual(mapped.interval_start_minute, 10)
        self.assertEqual(mapped.interval_end_date, dt.date(2025, 1, 1))
        self.assertEqual(mapped.interval_end_minute, 20)

    def test_midnight_sample_maps_to_next_day_first_interval(self):
        mapped = map_instantaneous_sample(
            sample_date=dt.date(2025, 1, 1),
            sample_minutes=1440,
            delta_minutes=10,
        )
        self.assertEqual(mapped.interval_start_date, dt.date(2025, 1, 2))
        self.assertEqual(mapped.interval_start_minute, 0)
        self.assertEqual(mapped.interval_end_date, dt.date(2025, 1, 2))
        self.assertEqual(mapped.interval_end_minute, 10)

    def test_parse_date_value_accepts_unpadded_text(self):
        self.assertEqual(parse_date_value("2025-1-1"), dt.date(2025, 1, 1))


class Attachment3MappingTests(unittest.TestCase):
    def test_hourly_forecast_after_18_crosses_to_next_date(self):
        mapped = map_hourly_target(
            issue_date=dt.date(2025, 1, 1),
            issue_minutes=18 * 60,
            lead_hour=7,
            delta_minutes=10,
            hourly_step_minutes=60,
        )
        self.assertEqual(mapped.target_date, dt.date(2025, 1, 2))
        self.assertEqual(mapped.target_start_minute, 0)
        self.assertEqual(mapped.target_end_minute, 60)
        self.assertEqual(mapped.interval_indices, (1, 2, 3, 4, 5, 6))


class ManifestTests(unittest.TestCase):
    def test_manifest_skips_excel_lock_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "input.xlsx").write_bytes(b"data")
            (root / "~$input.xlsx").write_bytes(b"lock")
            manifest = collect_manifest(root)
        self.assertEqual([item["relative_path"] for item in manifest], ["input.xlsx"])


if __name__ == "__main__":
    unittest.main()
