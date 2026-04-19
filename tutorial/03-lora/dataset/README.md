# Dataset curation for character LoRA

A LoRA memorizes exactly what's in the dataset. The quality of your training
run is bounded above by the quality of this folder.

## Structure

Kohya expects subfolders named `N_name` where `N` is the repeat count:

```
dataset/
├── train/
│   └── 5_character/            ← subject will be "character", repeated 5x/epoch
│       ├── img001.png
│       ├── img001.txt
│       ├── img002.png
│       ├── img002.txt
│       └── …
└── reg/                         ← optional regularization images (same class)
    └── 1_person/
```

## Rules that matter

1. **15–30 images is usually enough.** More is not better if they're samey.
2. **Vary pose, angle, lighting, expression.** Keep the face consistent.
3. **Use clean captions.** Describe the *scene* — not the character token.
   Good: `"woman standing in a garden, sunlight, green dress, smiling"`.
   Bad:  `"anna, garden, dress"`.
4. **Don't scrape.** Respect licensing. For personal-use character LoRAs of
   your own OC, use your own art / commissions.
5. **Full-body shots matter** if you need full-body consistency. A face-only
   dataset will lock the face but not proportions.

## Caption format

Kohya reads `.txt` sidecar files with the same stem as the image. One caption
per line is fine; Kohya tokenizes on commas. Typical shape:

```
a woman with long silver hair and green eyes, three-quarter view, natural
daylight, outdoor setting, casual clothing, neutral expression
```

No identifier token at the front (e.g. `"anna,"`). Let the model infer identity
from the visual training signal.

## Dedup before training

Duplicate or near-duplicate images waste steps and bias the LoRA. A quick CLIP
embedding dedup pass with `imagededup` or `fastdup` helps.

## Quality check

Before training, eyeball your dataset:
- Is the face clearly visible and consistent across most images?
- Is pose/lighting varied?
- Are captions scene-descriptive without leaning on a identity token?

If you answer "yes" three times, you're ready.
