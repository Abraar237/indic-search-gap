#!/usr/bin/env python3
"""Generate the Figure 1 pipeline schematic with a Gemini image model (Nano Banana) via OpenRouter.

The image is a schematic, not data. Every string is fixed in the prompt and must be checked by eye
after each generation, because image models can misspell.

    python3 paper/gen_schematic.py [out.png] [model]
"""
import base64, json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "paper", "acl", "assets", "fig1_schematic.png")
MODEL = sys.argv[2] if len(sys.argv) > 2 else "google/gemini-3-pro-image-preview"

PROMPT = """Create a clean scientific diagram for an academic research paper. Flat vector style, pure white background, thin dark-gray outlines, soft pastel fills, a clear sans-serif typeface, generous spacing. No shadows, no gradients, no 3D, no decoration, no title, no watermark. Portrait layout, four sections stacked top to bottom, joined by three short thick downward arrows.

SECTION 1. Small heading: "1. Same question, two languages". Below it two rounded cards side by side, joined by a thin double-headed arrow labelled "parallel". Left card, light orange fill: "Hindi or Telugu question". Right card, light blue fill: "English question".

SECTION 2. Small heading: "2. The agent searches (up to 3 queries)". Below it a small friendly robot icon. To its right four small pill-shaped tags in one row: "free", "match", "english", "dual". Under the tags, small text: "query language logged, then forced".

SECTION 3. Small heading: "3. A frozen two-language web". Below it three database cylinder icons side by side with labels underneath: "English only" (light blue), "Indic only" (light orange), "Both" (light green). Under the cylinders one line of small text: "1.9M Wikipedia passages". Below that, two small boxes side by side: "Dense retriever" and "Keyword retriever (BM25)".

SECTION 4. Small heading: "4. Score the answer". Below it two rounded result boxes side by side. Left box, light green fill, text on two lines: "Dense" and "Hindi gap: 9 pts". Right box, light red fill, text on two lines: "BM25" and "Hindi gap: 19 pts".

At the very bottom, one line of larger bold text: "Is the gap the query, the web, or the reading?"

Spell every quoted string exactly as written. All text must be large and easy to read when the image is printed 8 centimetres wide. Do not add any other words, numbers or labels."""


def main():
    key = None
    for line in open(os.path.join(ROOT, ".env")):
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
    if not key:
        sys.exit("OPENROUTER_API_KEY missing from .env")
    body = {"model": MODEL, "modalities": ["image", "text"],
            "messages": [{"role": "user", "content": PROMPT}],
            "image_config": {"aspect_ratio": "3:4"}}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read()[:400].decode('utf-8', 'replace')}")
    for img in r["choices"][0]["message"].get("images", []):
        url = img["image_url"]["url"]
        open(OUT, "wb").write(base64.b64decode(url.split(",", 1)[1]))
        print("wrote", OUT)
        return
    sys.exit("no image in response: " + json.dumps(r)[:400])


if __name__ == "__main__":
    main()
