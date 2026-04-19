# Tutorial 04 · IP-Adapter + LoRA for product catalog rendering

Minimal demo of how to render a locked character (via LoRA) wearing a specific
reference item (via IP-Adapter Plus) — the pattern HoneyChat uses for its
outfit shop catalog. ComfyUI workflow + a stdlib Python client that talks to
any ComfyUI instance.

Companion article: [honeychat.bot/en/blog/ipadapter-lora-outfit-rendering](https://honeychat.bot/en/blog/ipadapter-lora-outfit-rendering/)

## What's inside

```
04-ipadapter/
├── workflow.json                    ← ComfyUI workflow, tunables left as <tune>
├── client.py                        ← minimal Python client (stdlib + requests)
├── tests/
│   └── test_workflow_validation.py  ← JSON schema + safety assertions
└── pyproject.toml
```

## Prerequisites (you bring these)

- A running ComfyUI instance (local GPU, rented GPU, or a friend's) with:
  - [ComfyUI_IPAdapter_plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus) installed
  - `ip-adapter-plus_sdxl_vit-h.safetensors` in `models/ipadapter/`
  - `CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors` in `models/clip_vision/`
  - Your own SDXL base checkpoint
  - Your own character LoRA (see [03-lora](../03-lora/) if you need to train one)
- An outfit reference image (clean product photo, ideally neutral lighting)

## Running

```bash
pip install -e .

export COMFY_URL=http://localhost:8188
export REFERENCE_IMAGE=./my-dress.png
export CHECKPOINT=sdxl-anime-base.safetensors
export LORA=my-character-v1.safetensors
export IPADAPTER_WEIGHT=0.4   # tune
export IPADAPTER_END_AT=0.8   # tune

python client.py
```

The client uploads your reference to ComfyUI, rewrites the workflow with your
tunables, queues the prompt, waits for it to render, and saves the output
images to `./out/`.

## The two knobs you have to tune

| Knob | What it does | Starting range |
|---|---|---|
| `IPADAPTER_WEIGHT` | how much the reference image's features bleed into the generation | **lower half of 0-1** (start around 0.3, sweep up in 0.05 steps) |
| `IPADAPTER_END_AT` | fraction of denoising steps where IP-Adapter is active | **upper half of 0-1** (e.g. 0.7–0.9) so the LoRA face reasserts on final steps |

Evaluation loop:
1. Generate with starting values.
2. Inspect: face still looks like your character? Outfit recognizable as the reference?
3. Face drifts → lower weight or lower end_at.
4. Outfit too generic → raise weight carefully, or raise end_at slightly.
5. Sweep in 0.05 increments, not 0.1. The usable range is narrower than you'd expect.

## Testing

```bash
pip install -e ".[dev]"
pytest -v
```

The test suite validates that `workflow.json`:
- Is valid JSON
- Contains every expected node class
- Still has `<tune>` placeholders on IP-Adapter weight / end_at and LoRA strengths
- Has no broken cross-node references

It does NOT hit a real ComfyUI. That belongs in your own integration harness.

## License

MIT.
