import json
from pathlib import Path

import pytest

from common import (frames_for, shot_starts, snap32, total_length,
                    xfade_offsets)
from storyboard import validate

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("seconds,frames", [(4, 97), (5, 121), (5.5, 129),
                                            (10, 241)])
def test_frames_are_8k_plus_1(seconds, frames):
    assert frames_for(seconds) == frames
    assert frames_for(seconds) % 8 == 1


def test_snap32():
    assert snap32(1080) == 1088
    assert snap32(576) == 576
    assert snap32(1024) == 1024


def test_one_minute_timeline():
    d = [frames_for(5.5) / 24] * 12
    assert total_length(d, 0.4) == pytest.approx(60.1)
    offs = xfade_offsets(d, 0.4)
    assert len(offs) == 11
    assert offs[0] == pytest.approx(5.375 - 0.4)
    assert shot_starts(d, 0.4)[0] == 0.0


def test_example_storyboard_is_valid():
    doc = json.loads((ROOT / "examples" / "water_cycle.json")
                     .read_text(encoding="utf-8"))
    assert validate(doc, n=12, seconds=doc["seconds"]) == []


def test_validate_flags_long_narration():
    doc = {"shots": [{"id": 1, "continue": False,
                      "narration_pt": "palavra " * 20,
                      "narration_en": "ok"}]}
    errs = validate(doc, seconds=5.5)
    assert any("narration_pt" in e for e in errs)
