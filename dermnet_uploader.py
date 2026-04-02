import os
from pathlib import Path
from config import supabase_client
from datetime import datetime, timezone

# Adjust this path to where YOU stored dermnet_images
BASE_DIR = Path(__file__).resolve().parent.parent  # == flask-llm/
DERMNET_DIR = BASE_DIR / "flask-llm/dermnet_images"

BUCKET_NAME = "patient-images"

def upload_dermnet_images():
    if not DERMNET_DIR.exists():
        raise RuntimeError(f"DermNet directory not found: {DERMNET_DIR}")

    print(f"Uploading from: {DERMNET_DIR}")

    total_uploaded = 0

    # Walk condition folders
    for condition_dir in DERMNET_DIR.iterdir():
        if not condition_dir.is_dir():
            continue

        condition = condition_dir.name.lower().replace("_", " ")

        # Walk tones (light/medium/dark)
        for tone_dir in condition_dir.iterdir():
            if not tone_dir.is_dir():
                continue

            tone = tone_dir.name.lower()

            # Walk actual images
            for img_path in tone_dir.iterdir():
                if not img_path.is_file():
                    continue

                print(f"Uploading {img_path.name} (condition={condition}, tone={tone})")

                # Read bytes
                with open(img_path, "rb") as f:
                    image_bytes = f.read()

                # Upload to Supabase storage
                filename = f"dermnet_{condition}_{tone}_{img_path.stem}_{int(datetime.now().timestamp())}.png"

                try:
                    supabase_client.storage.from_(BUCKET_NAME).upload(
                        filename,
                        image_bytes,
                        file_options={"content-type": "image/png"}
                    )

                    public_url = supabase_client.storage.from_(BUCKET_NAME).get_public_url(filename)

                    # Insert into dermnet_images table
                    supabase_client.table("dermnet_images").insert({
                        "condition": condition,
                        "tone": tone,
                        "filename": filename,
                        "image_url": public_url,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }).execute()

                    total_uploaded += 1

                except Exception as e:
                    print(f"❌ Error uploading {img_path.name}: {e}")

    print(f"\n✅ Upload complete! Total images uploaded: {total_uploaded}")


if __name__ == "__main__":
    upload_dermnet_images()
