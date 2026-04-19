"""Minimal Python client for POSTing the IP-Adapter workflow to a ComfyUI instance.

Usage:

    COMFY_URL=http://my-comfy:8188 \
    REFERENCE_IMAGE=./dress.png \
    OUTPUT_DIR=./out \
    python client.py

The client uploads the outfit reference to ComfyUI's /upload/image, rewrites
the workflow JSON with the correct filename + the tunable values from env,
queues the prompt, polls /history, and saves the resulting image.

Zero framework deps — stdlib + requests. No business logic.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Send the IP-Adapter + LoRA workflow to ComfyUI.")
    p.add_argument("--comfy",    default=os.getenv("COMFY_URL", "http://localhost:8188"))
    p.add_argument("--workflow", default=os.getenv("WORKFLOW_JSON", "workflow.json"))
    p.add_argument("--reference", default=os.getenv("REFERENCE_IMAGE", "reference.png"))
    p.add_argument("--checkpoint", default=os.getenv("CHECKPOINT", ""))
    p.add_argument("--lora", default=os.getenv("LORA", ""))
    p.add_argument("--prompt", default=os.getenv("POSITIVE_PROMPT", "full body portrait, natural lighting, neutral pose"))
    p.add_argument("--weight",  type=float, default=float(os.getenv("IPADAPTER_WEIGHT",  "0.4")),
                   help="IP-Adapter weight. Tune in the lower half of 0-1 for identity preservation.")
    p.add_argument("--end-at",  type=float, default=float(os.getenv("IPADAPTER_END_AT",  "0.8")),
                   help="IP-Adapter end_at. Tune in the upper half of 0-1 so LoRA reasserts late.")
    p.add_argument("--lora-strength", type=float, default=float(os.getenv("LORA_STRENGTH", "0.85")))
    p.add_argument("--output-dir",    default=os.getenv("OUTPUT_DIR", "./out"))
    return p.parse_args()


def upload_image(comfy_url: str, path: Path) -> str:
    url = urljoin(comfy_url, "/upload/image")
    with path.open("rb") as f:
        r = requests.post(url, files={"image": (path.name, f, "image/png")}, timeout=30)
    r.raise_for_status()
    return r.json().get("name") or path.name


def rewrite_workflow(wf: dict[str, Any], args: argparse.Namespace, ref_filename: str) -> dict[str, Any]:
    """Fill in the `<tune>` and `<path>` placeholders with actual values."""
    wf = json.loads(json.dumps(wf))  # deep copy

    # 1. Checkpoint
    if args.checkpoint:
        wf["1"]["inputs"]["ckpt_name"] = args.checkpoint
    # 2. LoRA
    if args.lora:
        wf["2"]["inputs"]["lora_name"] = args.lora
    wf["2"]["inputs"]["strength_model"] = args.lora_strength
    wf["2"]["inputs"]["strength_clip"]  = args.lora_strength
    # 5. Reference image
    wf["5"]["inputs"]["image"] = ref_filename
    # 6. IP-Adapter weight / end_at
    wf["6"]["inputs"]["weight"] = args.weight
    wf["6"]["inputs"]["end_at"] = args.end_at
    # 7. Positive prompt
    wf["7"]["inputs"]["text"] = args.prompt
    # 10. Random seed
    wf["10"]["inputs"]["seed"] = int(time.time()) & 0xFFFFFFFF
    return wf


def queue_prompt(comfy_url: str, prompt: dict) -> str:
    url = urljoin(comfy_url, "/prompt")
    r = requests.post(url, json={"prompt": prompt}, timeout=30)
    r.raise_for_status()
    return r.json()["prompt_id"]


def wait_for_result(comfy_url: str, prompt_id: str, timeout_s: int = 300) -> dict:
    deadline = time.time() + timeout_s
    history_url = urljoin(comfy_url, f"/history/{prompt_id}")
    while time.time() < deadline:
        r = requests.get(history_url, timeout=10)
        if r.ok and r.json():
            return r.json()[prompt_id]
        time.sleep(2)
    raise TimeoutError(f"ComfyUI prompt {prompt_id} didn't finish in {timeout_s}s")


def save_outputs(comfy_url: str, history: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for node_id, node_output in (history.get("outputs") or {}).items():
        for img in node_output.get("images", []):
            url = urljoin(comfy_url, f"/view?filename={img['filename']}&type={img.get('type','output')}&subfolder={img.get('subfolder','')}")
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            dest = out_dir / img["filename"]
            dest.write_bytes(r.content)
            saved.append(dest)
    return saved


def main() -> int:
    args = parse_args()

    ref_path = Path(args.reference)
    if not ref_path.exists():
        print(f"reference image not found: {ref_path}", file=sys.stderr)
        return 2

    wf_path = Path(args.workflow)
    workflow = json.loads(wf_path.read_text())
    # Strip the _meta block — ComfyUI doesn't understand it.
    workflow.pop("_meta", None)

    print(f"→ uploading reference: {ref_path}")
    ref_filename = upload_image(args.comfy, ref_path)

    print(f"→ rewriting workflow (weight={args.weight}, end_at={args.end_at})")
    prompt = rewrite_workflow(workflow, args, ref_filename)

    print("→ queueing prompt")
    pid = queue_prompt(args.comfy, prompt)
    print(f"  prompt_id={pid}")

    print("→ waiting for result…")
    history = wait_for_result(args.comfy, pid)

    saved = save_outputs(args.comfy, history, Path(args.output_dir))
    for p in saved:
        print(f"  saved: {p}")
    return 0 if saved else 1


if __name__ == "__main__":
    sys.exit(main())
