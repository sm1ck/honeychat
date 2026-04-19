# Tutorial 03 · Character LoRA training template (Kohya SDXL)

Companion-style chatbots need **visual identity locked per character** — prompt
engineering + seed-pinning alone won't do it. This tutorial is a *config-only*
template for training an SDXL character LoRA with
[Kohya_ss](https://github.com/bmaltais/kohya_ss).

Companion article: [honeychat.bot/en/blog/character-consistency-custom-lora](https://honeychat.bot/en/blog/character-consistency-custom-lora/)

## Why there's no `docker compose up` here

LoRA training is GPU-heavy (24 GB VRAM class for SDXL). Shipping a docker-compose
that expects a consumer GPU would mislead — and a no-op compose would be worse.

Instead: this folder gives you the **config and recipe**. You run the actual
training on your own GPU, or rent one (Vast.ai, RunPod, Modal, Paperspace).

## What's inside

```
03-lora/
├── kohya-config.toml   ← generic SDXL LoRA training config (you tune <tune> slots)
├── dataset/
│   └── README.md       ← how to curate and caption your dataset
└── train.sh            ← Kohya invocation wrapper
```

## The parameters you have to pick

Every `<tune>` in `kohya-config.toml` is a decision *you* make based on your
subject and base model. There is no universal "best" setting:

| Parameter | What it controls | Typical range |
|---|---|---|
| `learning_rate` | how fast the LoRA weights update | 1e-5 ≤ LR ≤ 2e-4 |
| `max_train_steps` | total training steps | 500 – 5000 |
| `train_batch_size` | images per step | 1 – 8 (VRAM-bound) |
| `network_dim` (rank) | LoRA capacity | 8 – 64 |
| `network_alpha` | scaling | usually `dim` or `dim/2` |
| `resolution` | crop size | 1024 (SDXL default) |

Anime-style bases behave differently from realistic ones. **Iterate**: train,
evaluate on test prompts, adjust, retrain.

## Dataset curation matters more than size

20 well-curated, varied-pose images beat 100 messy ones. See `dataset/README.md`
for the curation checklist.

**Rule of thumb:** describe the *scene* in captions, not the *character*. Let
the model learn the face from context, not from a token like "Anna". Over-using
a unique token as an identifier typically encodes pose/lighting noise into it.

## Running

```bash
# 1. Clone Kohya somewhere separate
git clone https://github.com/bmaltais/kohya_ss ~/kohya_ss
cd ~/kohya_ss && ./setup.sh

# 2. Put 15–30 images + .txt captions in ./dataset/
#    See dataset/README.md for details

# 3. Edit kohya-config.toml — fill in <tune> placeholders + paths

# 4. Train
bash train.sh
```

Checkpoint lands in `./output/<output_name>.safetensors`. Use it with ComfyUI
or Diffusers like any other SDXL LoRA.

## Next step

Once your character LoRA is solid, combine it with IP-Adapter to render your
character wearing arbitrary reference items (shop catalog, user uploads). See
the next tutorial: [04-ipadapter](../04-ipadapter/).

## License

MIT on this config template. The Kohya trainer itself is under its own license.
