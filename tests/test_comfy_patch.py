import pytest

from render_clips import find_video, patch_workflow


def workflow():
    return {
        "3": {"class_type": "CLIPTextEncode", "_meta": {"title": "PROMPT"},
              "inputs": {"text": "old", "clip": ["4", 0]}},
        "5": {"class_type": "LoadImage", "_meta": {"title": "IMAGE"},
              "inputs": {"image": "x.png"}},
        "7": {"class_type": "EmptyLTXVLatentVideo", "_meta": {"title": "E"},
              "inputs": {"width": 1024, "height": 576, "length": 97}},
        "8": {"class_type": "RandomNoise", "_meta": {"title": "Noise"},
              "inputs": {"noise_seed": 1}},
        "9": {"class_type": "CLIPTextEncode", "_meta": {"title": "Negative"},
              "inputs": {"text": "neg"}},
    }


def test_patch_sets_prompt_image_length_seed():
    wf = workflow()
    new, edits = patch_workflow(wf, "P", 129, 42, "start.png")
    assert new["3"]["inputs"]["text"] == "P"
    assert new["5"]["inputs"]["image"] == "start.png"
    assert new["7"]["inputs"]["length"] == 129
    assert new["8"]["inputs"]["noise_seed"] == 42
    assert new["9"]["inputs"]["text"] == "neg"      # negative untouched
    assert new["7"]["inputs"]["width"] == 1024      # resolution untouched
    assert wf["3"]["inputs"]["text"] == "old"       # original not mutated
    assert len(edits) == 4


def test_patch_requires_prompt_title():
    wf = workflow()
    wf["3"]["_meta"]["title"] = "Positive"
    with pytest.raises(SystemExit):
        patch_workflow(wf, "P", 129, 42)


def test_find_video_in_history():
    h = {"outputs": {"12": {"images": [{"filename": "LTX_00001_.mp4",
                                        "subfolder": "video",
                                        "type": "output"}],
                            "animated": [True]}}}
    assert find_video(h)["filename"] == "LTX_00001_.mp4"
    assert find_video({"outputs": {}}) is None
