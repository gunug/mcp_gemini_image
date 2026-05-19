import io
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Keep MCP stdio stdout clean: route 3rd-party logs to stderr at WARNING+.
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
for noisy in ("google_genai", "google.genai", "httpx", "urllib3"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

DEFAULT_MODEL = "gemini-2.5-flash-image"

ASPECT_RATIOS = {
    (1, 1): "1:1",
    (16, 9): "16:9",
    (9, 16): "9:16",
    (4, 3): "4:3",
    (3, 4): "3:4",
    (3, 2): "3:2",
    (2, 3): "2:3",
}


def require_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.\n"
            "Windows PowerShell에서 영구 등록하려면:\n"
            '  setx GEMINI_API_KEY "your-api-key-here"\n'
            "등록 후 새 터미널을 열어 다시 시도하세요.\n"
            "API 키 발급: https://aistudio.google.com/apikey"
        )
    return key


def pick_aspect_ratio(width: int, height: int) -> str:
    target = width / height
    best = min(ASPECT_RATIOS.items(), key=lambda kv: abs((kv[0][0] / kv[0][1]) - target))
    return best[1]


def sanitize_title(title: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", title).strip("_")
    return cleaned or "untitled"


mcp = FastMCP("gemini-image")


@mcp.tool()
def generate_image(
    prompt: str,
    title: str,
    width: int = 1920,
    height: int = 1080,
    model: str = DEFAULT_MODEL,
) -> str:
    """Generate an image with a Gemini image model and save it as PNG.

    Args:
        prompt: Text prompt describing the image.
        title: English title used in the filename (will be sanitized).
        width: Output width in pixels. Default 1920.
        height: Output height in pixels. Default 1080.
        model: Gemini image model ID. Examples:
            - "gemini-2.5-flash-image" (default, Nano Banana)
            - "gemini-3.1-flash-image-preview"
            - "gemini-3-pro-image-preview"

    Returns:
        Absolute path to the saved PNG file.
    """
    from google import genai
    from google.genai import types
    from PIL import Image

    api_key = require_api_key()

    if width <= 0 or height <= 0:
        raise ValueError("width/height는 양의 정수여야 합니다.")

    aspect = pick_aspect_ratio(width, height)
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=aspect),
        ),
    )

    image_bytes = None
    for cand in response.candidates or []:
        for part in (cand.content.parts if cand.content else []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                image_bytes = inline.data
                break
        if image_bytes:
            break

    if not image_bytes:
        raise RuntimeError("Gemini 응답에서 이미지 데이터를 찾지 못했습니다.")

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if img.size != (width, height):
        img = img.resize((width, height), Image.LANCZOS)

    out_dir = Path.cwd() / "png"
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{sanitize_title(title)}.png"
    out_path = out_dir / filename
    img.save(out_path, format="PNG")

    return str(out_path.resolve())


def main() -> None:
    print("[mcp-gemini-image] starting on stdio...", file=sys.stderr, flush=True)
    try:
        mcp.run()
    except Exception as e:
        print(f"[mcp-gemini-image] error: {e}", file=sys.stderr, flush=True)
        raise


if __name__ == "__main__":
    main()
