"""Schema validation for workflow.json — makes sure the file stays valid JSON
with the node structure ComfyUI expects. No network calls.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).resolve().parents[1] / "workflow.json"


@pytest.fixture(scope="module")
def workflow() -> dict:
    return json.loads(WORKFLOW.read_text())


def test_is_valid_json(workflow):
    assert isinstance(workflow, dict)


def test_has_required_nodes(workflow):
    """Expected chain: Checkpoint → LoRA → FreeU → IPAdapter → KSampler → VAEDecode → Save."""
    expected_classes = {
        "CheckpointLoaderSimple",
        "LoraLoader",
        "FreeU_V2",
        "IPAdapterModelLoader",
        "LoadImage",
        "IPAdapterAdvanced",
        "CLIPTextEncode",
        "EmptyLatentImage",
        "KSampler",
        "VAEDecode",
        "SaveImage",
    }
    found = {node.get("class_type") for node_id, node in workflow.items() if node_id != "_meta"}
    missing = expected_classes - found
    assert not missing, f"workflow.json is missing classes: {missing}"


def test_ipadapter_has_tune_placeholders(workflow):
    """IP-Adapter weight + end_at must be placeholders — readers fill them in.

    This is an intentional safety check: if someone accidentally commits our
    production values, this test fails.
    """
    ip = workflow["6"]["inputs"]
    assert ip["weight"] == "<tune>", "IP-Adapter weight must be <tune> in the template"
    assert ip["end_at"] == "<tune>", "IP-Adapter end_at must be <tune> in the template"


def test_lora_has_tune_placeholders(workflow):
    lora = workflow["2"]["inputs"]
    assert lora["strength_model"] == "<tune>"
    assert lora["strength_clip"]  == "<tune>"


def test_node_references_are_valid(workflow):
    """Every ["<id>", N] input reference must point to an existing node."""
    all_ids = {k for k in workflow.keys() if k != "_meta"}
    for node_id, node in workflow.items():
        if node_id == "_meta":
            continue
        for key, val in node.get("inputs", {}).items():
            if isinstance(val, list) and len(val) == 2 and isinstance(val[0], str):
                assert val[0] in all_ids, f"node {node_id}.{key} references unknown node {val[0]}"
