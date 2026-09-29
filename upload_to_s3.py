"""
static/ доторх зураг, видеог AWS S3 руу хуулж, замыг `media` таблицад хадгална.

Ажиллуулах:
  $env:S3_BUCKET = "skinology-media"
  $env:AWS_REGION = "ap-northeast-2"
  $env:AWS_ACCESS_KEY_ID = "..."
  $env:AWS_SECRET_ACCESS_KEY = "..."
  python upload_to_s3.py            # шинэ/өөрчлөгдсөн файлуудыг хуулна
  python upload_to_s3.py --force    # бүгдийг дахин хуулна
  python upload_to_s3.py --dry-run  # юу хуулагдахыг л харуулна
  python upload_to_s3.py --from-s3  # хуулахгүй, bucket-д байгаа файлуудаар
                                    # media таблицыг бөглөнө (Render build)

Аль хэдийн ижил хэмжээтэйгээр бүртгэгдсэн файлыг алгасна.
"""

import argparse
import mimetypes
import os
import sys
from datetime import datetime

import boto3

from app import AWS_REGION, BASE_DIR, S3_BUCKET, get_db, init_db

STATIC_DIR = os.path.join(BASE_DIR, "static")
MEDIA_DIRS = ("img", "video")
MEDIA_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".mp4", ".webm"}

# Сайтад ашиглагддаггүй том эх файлууд.
EXCLUDE = {"video/clinic_original.mp4"}

# S3 дээрх key-ийн угтвар: static/img/laser.jpg
S3_PREFIX = "static/"

CACHE_CONTROL = "public, max-age=31536000"


def iter_media_files():
    for media_dir in MEDIA_DIRS:
        root_dir = os.path.join(STATIC_DIR, media_dir)
        for root, _dirs, files in os.walk(root_dir):
            for name in sorted(files):
                if os.path.splitext(name)[1].lower() not in MEDIA_EXTS:
                    continue
                full = os.path.join(root, name)
                path = os.path.relpath(full, STATIC_DIR).replace(os.sep, "/")
                if path in EXCLUDE:
                    continue
                yield path, full


def save_media(path, key, content_type, size):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO media (path, s3_key, content_type, size, uploaded_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                s3_key = excluded.s3_key,
                content_type = excluded.content_type,
                size = excluded.size,
                uploaded_at = excluded.uploaded_at
            """,
            (path, key, content_type, size,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )


def sync_from_s3(s3):
    """Bucket-ийн static/ доторх файлуудыг media таблицад бүртгэнэ."""
    count = 0
    for page in s3.get_paginator("list_objects_v2").paginate(
        Bucket=S3_BUCKET, Prefix=S3_PREFIX
    ):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            path = key[len(S3_PREFIX):]
            if os.path.splitext(path)[1].lower() not in MEDIA_EXTS:
                continue
            content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
            save_media(path, key, content_type, obj["Size"])
            count += 1
    print(f"Дууслаа: S3-аас {count} файл бүртгэсэн.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--force", action="store_true", help="бүгдийг дахин хуулах")
    parser.add_argument("--dry-run", action="store_true", help="хуулахгүй, зөвхөн жагсаах")
    parser.add_argument("--from-s3", action="store_true",
                        help="хуулахгүй, bucket-аас media таблицыг бөглөх")
    args = parser.parse_args()
    # Windows консол дээр кирилл файлын нэр хэвлэхэд алдаа гаргахгүйн тулд.
    sys.stdout.reconfigure(encoding="utf-8")

    if not S3_BUCKET:
        sys.exit("S3_BUCKET орчны хувьсагч тохируулаагүй байна.")

    init_db()
    s3 = boto3.client("s3", region_name=AWS_REGION)

    if args.from_s3:
        sync_from_s3(s3)
        return

    with get_db() as conn:
        existing = {
            r["path"]: r["size"]
            for r in conn.execute("SELECT path, size FROM media").fetchall()
        }

    uploaded = skipped = 0
    for path, full in iter_media_files():
        size = os.path.getsize(full)
        if not args.force and existing.get(path) == size:
            skipped += 1
            continue

        key = S3_PREFIX + path
        content_type = mimetypes.guess_type(full)[0] or "application/octet-stream"
        print(f"{'[dry-run] ' if args.dry_run else ''}{path} -> s3://{S3_BUCKET}/{key} "
              f"({size / 1048576:.1f} MB)")
        if args.dry_run:
            continue

        s3.upload_file(
            full,
            S3_BUCKET,
            key,
            ExtraArgs={"ContentType": content_type, "CacheControl": CACHE_CONTROL},
        )
        save_media(path, key, content_type, size)
        uploaded += 1

    print(f"Дууслаа: {uploaded} хуулсан, {skipped} алгассан.")


if __name__ == "__main__":
    main()
