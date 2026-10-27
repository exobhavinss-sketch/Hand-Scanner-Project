from datetime import datetime
import csv

from src.history_manager import HistoryManager


def test_history_deduplicates_consecutive_gestures():
    history = HistoryManager(max_entries=3)
    moment = datetime(2026, 1, 2, 3, 4, 5)
    assert history.record("Open Palm", moment)
    assert not history.record("Open Palm", moment)
    assert history.record("Closed Fist", moment)
    assert [event.gesture for event in history.events] == ["Open Palm", "Closed Fist"]
    assert history.events[0].time_text == "03:04:05"


def test_history_keeps_latest_entries():
    history = HistoryManager(max_entries=2)
    for gesture in ("A", "B", "C"):
        history.record(gesture)
    assert [event.gesture for event in history.events] == ["B", "C"]


def test_history_records_only_changes_and_preserves_timestamps():
    history = HistoryManager(max_entries=5)
    first = datetime(2026, 5, 1, 10, 11, 12)
    second = datetime(2026, 5, 1, 10, 11, 13)
    assert history.record("Open Palm", first)
    assert not history.record("Open Palm", second)
    assert history.record("Peace Sign", second)
    assert history.events[0].timestamp == first
    assert history.events[1].timestamp == second
    assert len(history) == 2


def test_history_clear_and_csv_export(tmp_path):
    history = HistoryManager()
    moment = datetime(2026, 5, 1, 10, 11, 12)
    history.record("Open Palm", moment)
    output = tmp_path / "history.csv"
    history.export_csv(output)
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows == [["timestamp", "gesture"], [moment.isoformat(), "Open Palm"]]
    history.clear()
    assert history.events == []

