"""Generate DALL-E 3 assets for the FitHub app.

Usage:
    cd fithub-backend
    python3 scripts/dalle_assets.py --asset ai_avatar      # single
    python3 scripts/dalle_assets.py --asset all            # batch

Output:
    scripts/dalle_output/<asset_name>.png  (saved locally)
    Copy the ones you like to flutter-app/assets/images/ai/

Cost notes (Jan 2026):
    DALL-E 3 standard 1024x1024 : ~$0.040 / image
    DALL-E 3 HD       1024x1024 : ~$0.080 / image
    DALL-E 3 standard 1024x1792 : ~$0.080 / image (portrait)
    Total batch (all 6 assets standard) ≈ $0.30
"""
import argparse
import os
import sys
import time
from pathlib import Path
from urllib.request import urlopen

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai SDK required. Run: pip install openai")
    sys.exit(1)


OUT_DIR = Path(__file__).parent / "dalle_output"
OUT_DIR.mkdir(exist_ok=True)


# Asset registry — id → (prompt, size, quality)
ASSETS = {
    # AI Coach avatar — used in generating screen, chat, profile card
    "ai_avatar": {
        "prompt": (
            "Premium AI fitness coach avatar, futuristic minimalist 3D render, "
            "abstract humanoid silhouette made of glowing teal and purple "
            "neural network nodes and connection lines, holographic translucent "
            "effect, deep dark background with subtle gradient (charcoal to "
            "midnight blue), professional tech brand identity, centered "
            "composition, soft inner glow, no text, no logos, no body parts "
            "visible, just an abstract symbolic representation of intelligence."
        ),
        "size": "1024x1024",
        "quality": "hd",  # avatar uses HD for clarity
    },
    # Tier card decorative backgrounds — abstract, blend with dark UI
    "starter_bg": {
        "prompt": (
            "Abstract gradient background, calm flowing emerald green to teal "
            "shapes, soft flowing curves, beginning/sprout feeling, minimalist, "
            "low contrast, dark navy base, fits behind UI as decorative element, "
            "no text, no figures, no objects."
        ),
        "size": "1024x1024",
        "quality": "standard",
    },
    "pro_bg": {
        "prompt": (
            "Abstract gradient background, dynamic flowing purple to violet "
            "energy ribbons, electric subtle particles, premium feeling, dark "
            "base, fits behind UI as decorative element, no text, no figures, "
            "no objects, smooth not chaotic."
        ),
        "size": "1024x1024",
        "quality": "standard",
    },
    "elite_bg": {
        "prompt": (
            "Abstract gradient background, luxurious gold to amber liquid metal "
            "flowing, subtle particle effects, premium gala feeling, dark "
            "charcoal base, fits behind UI as decorative element, no text, no "
            "figures, no objects, very subtle and elegant."
        ),
        "size": "1024x1024",
        "quality": "standard",
    },
    # Onboarding hero — optional, ileride kullanılabilir
    "onboarding_hero": {
        "prompt": (
            "Abstract premium fitness app hero illustration, dark background, "
            "geometric shapes representing strength and progress, glowing "
            "teal accents, minimalist 3D render, professional brand aesthetic, "
            "no people, no equipment, no text."
        ),
        "size": "1024x1792",  # portrait — hero
        "quality": "standard",
    },
    # Goal visualization sample — Elite feature mockup
    "goal_visualization_sample": {
        "prompt": (
            "Abstract motivational silhouette, athletic toned body composition "
            "shown as glowing wireframe outline against dark background, "
            "subtle teal and gold gradient highlights, minimalist art-style, "
            "no specific person, no face, anonymous representation of fitness "
            "goal, professional aesthetic, no text."
        ),
        "size": "1024x1024",
        "quality": "standard",
    },
}


def generate_asset(client: OpenAI, asset_id: str, spec: dict) -> Path | None:
    """Generate one asset via DALL-E 3 and save locally."""
    print(f"  Generating: {asset_id} ({spec['size']}, {spec['quality']})...")
    try:
        t0 = time.time()
        response = client.images.generate(
            model="dall-e-3",
            prompt=spec["prompt"],
            size=spec["size"],
            quality=spec["quality"],
            n=1,
        )
        img_url = response.data[0].url
        elapsed = time.time() - t0

        out_path = OUT_DIR / f"{asset_id}.png"
        with urlopen(img_url) as r:
            out_path.write_bytes(r.read())

        size_kb = out_path.stat().st_size // 1024
        print(f"  ✓ {asset_id} → {out_path}  ({size_kb}KB, {elapsed:.1f}s)")
        return out_path

    except Exception as e:
        print(f"  ✗ {asset_id} failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate DALL-E assets")
    parser.add_argument(
        "--asset",
        default="ai_avatar",
        help="Asset id (or 'all' for batch). Choices: " + ", ".join(ASSETS.keys()) + ", all",
    )
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: OPENAI_API_KEY env var not set (check .env)")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    if args.asset == "all":
        targets = list(ASSETS.keys())
        print(f"Generating ALL {len(targets)} assets (~$0.30 total cost)...")
    elif args.asset in ASSETS:
        targets = [args.asset]
    else:
        print(f"Unknown asset: {args.asset}")
        print(f"Available: {', '.join(ASSETS.keys())}, all")
        sys.exit(1)

    print(f"Output dir: {OUT_DIR}")
    print()

    results = []
    for asset_id in targets:
        result = generate_asset(client, asset_id, ASSETS[asset_id])
        results.append((asset_id, result))
        if len(targets) > 1:
            time.sleep(1)  # small breather between calls

    print()
    print("=" * 60)
    print("Summary:")
    success = sum(1 for _, r in results if r is not None)
    print(f"  Success: {success}/{len(results)}")
    print(f"  Output:  {OUT_DIR}")
    print()
    print("Next step: review each .png, then copy the ones you like to:")
    print("  flutter-app/assets/images/ai/")
    print()


if __name__ == "__main__":
    main()
