"""
Skinology Clinic — Flask вэб сайт.

Хуудсууд:
  /               - Нүүр хуудас (премиум арьс судлал / гоо сайхны клиник)
  /register       - Цаг захиалах / бүртгэлийн форм
  /admin          - Бүртгэгдсэн мэдээллийг харах (нууц үгтэй)
  /admin/export   - Бүртгэлийг Excel (.xlsx) файлаар татах

Мэдээлэл "Register" SQLite датабаазад (register.db) хадгалагдана.

Зураг, видео файлууд AWS S3 дээр байрлах бөгөөд S3 дээрх зам нь `media`
таблицад хадгалагдана (upload_to_s3.py-г үзнэ үү). Датабазад бүртгэгдээгүй
файлыг локал /static-аас үзүүлнэ.
"""

import io
import json
import os
import re
import sqlite3
from datetime import datetime
from urllib.parse import quote

from dotenv import load_dotenv
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from openpyxl import Workbook

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# .env файлаас орчны хувьсагчдыг уншина (аль хэдийн тохируулсныг дарахгүй).
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-солиорой")

# --- Тохиргоо ---------------------------------------------------------------

DB_PATH = os.path.join(BASE_DIR, "register.db")

# Admin хуудсанд нэвтрэх нууц үг (орчны хувьсагчаар дарж болно).
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# S3 тохиргоо. MEDIA_BASE_URL-д CloudFront домэйн өгч болно, эс бөгөөс
# bucket-ийн нийтийн URL-ийг ашиглана.
S3_BUCKET = os.environ.get("S3_BUCKET", "")
AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-2")
MEDIA_BASE_URL = os.environ.get("MEDIA_BASE_URL", "").rstrip("/") or (
    f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com" if S3_BUCKET else ""
)

# Имэйлийн формат. Жишээ: ner.ovog@gmail.com
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
EMAIL_EXAMPLE = "ner.ovog@gmail.com"

# Утасны дугаар: Монголын 8 оронтой дугаар. Жишээ: 99112233
PHONE_RE = re.compile(r"^\d{8}$")
PHONE_EXAMPLE = "99112233"

# "Эмчилгээний видео" хэсэг static/videos доторх файлуудыг уншина.
# Гарчиг нь файлын нэрнээс гарна: "Уруулын_филлер.mp4" -> "Уруулын филлер".
VIDEOS_DIR = os.path.join(BASE_DIR, "static", "videos")
VIDEO_EXTS = {".mp4", ".m4v", ".webm"}

EXCEL_HEADERS = ["#", "Овог", "Нэр", "Утасны дугаар", "Имэйл", "Бүртгүүлсэн огноо"]


# --- Датабаз (SQLite) ---------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """register таблиц байхгүй бол үүсгэнэ (одоо байгаа өгөгдлийг хөндөхгүй)."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS register (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name   TEXT NOT NULL,
                first_name  TEXT NOT NULL,
                phone       TEXT NOT NULL,
                email       TEXT NOT NULL UNIQUE,
                created_at  TEXT NOT NULL
            )
            """
        )
        # static/ доторх зам (жишээ: img/laser.jpg) -> S3 дээрх key.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS media (
                path          TEXT PRIMARY KEY,
                s3_key        TEXT NOT NULL,
                content_type  TEXT NOT NULL,
                size          INTEGER NOT NULL,
                uploaded_at   TEXT NOT NULL
            )
            """
        )


def email_already_registered(email):
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM register WHERE lower(email) = lower(?) LIMIT 1",
            (email,),
        ).fetchone()
    return row is not None


def save_registration(last_name, first_name, phone, email):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO register (last_name, first_name, phone, email, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                last_name,
                first_name,
                phone,
                email,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )


def fetch_all_registrations():
    with get_db() as conn:
        return conn.execute("SELECT * FROM register ORDER BY id DESC").fetchall()


def fetch_media_keys():
    """{static зам: S3 key} толь буцаана."""
    with get_db() as conn:
        rows = conn.execute("SELECT path, s3_key FROM media").fetchall()
    return {r["path"]: r["s3_key"] for r in rows}


# --- Валидац -------------------------------------------------------------

def validate(form):
    """Формын өгөгдлийг шалгаж, (цэвэрлэсэн утга, алдаанууд) буцаана."""
    last_name = (form.get("last_name") or "").strip()
    first_name = (form.get("first_name") or "").strip()
    phone = (form.get("phone") or "").strip()
    email = (form.get("email") or "").strip()

    errors = {}

    if len(last_name) < 2:
        errors["last_name"] = "Овгоо зөв оруулна уу (доод тал нь 2 үсэг)."
    if len(first_name) < 2:
        errors["first_name"] = "Нэрээ зөв оруулна уу (доод тал нь 2 үсэг)."
    if not PHONE_RE.match(phone):
        errors["phone"] = f"Утасны дугаар 8 оронтой тоо байх ёстой. Жишээ: {PHONE_EXAMPLE}"
    if not EMAIL_RE.match(email):
        errors["email"] = f"Имэйл буруу форматтай байна. Жишээ: {EMAIL_EXAMPLE}"
    elif email_already_registered(email):
        errors["email"] = "Энэ имэйл хаяг аль хэдийн бүртгэгдсэн байна."

    values = {
        "last_name": last_name,
        "first_name": first_name,
        "phone": phone,
        "email": email,
    }
    return values, errors


def list_treatment_videos():
    """static/videos доторх тоглуулж болох видеонуудыг буцаана.

    Гарчиг, дарааллыг static/videos/titles.json-оос авна
    ({"файл.mp4": "Гарчиг"}); тэнд байхгүй файлын гарчиг файлын нэрнээс гарна.
    """
    if not os.path.isdir(VIDEOS_DIR):
        return []

    titles = {}
    titles_path = os.path.join(VIDEOS_DIR, "titles.json")
    if os.path.isfile(titles_path):
        try:
            with open(titles_path, encoding="utf-8") as f:
                titles = json.load(f)
        except (OSError, ValueError):
            titles = {}

    files = [
        name for name in os.listdir(VIDEOS_DIR)
        if os.path.splitext(name)[1].lower() in VIDEO_EXTS
        and os.path.isfile(os.path.join(VIDEOS_DIR, name))
        and os.path.getsize(os.path.join(VIDEOS_DIR, name)) > 0
    ]
    order = list(titles)
    files.sort(key=lambda n: (order.index(n) if n in titles else len(order), n.lower()))

    videos = []
    for name in files:
        title = titles.get(name)
        if not title:
            # "1_Уруулын_филлер" -> "Уруулын филлер" (эхний дугаар нь зөвхөн эрэмбэд).
            stem = re.sub(r"^\d+[\s._\-]+", "", os.path.splitext(name)[0])
            title = re.sub(r"[_\-]+", " ", stem).strip()
        videos.append({"file": f"videos/{name}", "title": title})
    return videos


# --- Нийтлэг контекст --------------------------------------------------

@app.context_processor
def inject_globals():
    media_keys = fetch_media_keys() if MEDIA_BASE_URL else {}

    def media_url(path):
        """S3 дээр байршсан бол S3 URL, үгүй бол локал /static URL."""
        key = media_keys.get(path)
        if key:
            return f"{MEDIA_BASE_URL}/{quote(key)}"
        return url_for("static", filename=path)

    return {"current_year": datetime.now().year, "media_url": media_url}


# --- Нүүр хуудас -----------------------------------------------------

@app.route("/")
def index():
    return render_template("home.html", treatment_videos=list_treatment_videos())


# --- Цаг захиалах / бүртгэл ------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    context = {
        "email_example": EMAIL_EXAMPLE,
        "phone_example": PHONE_EXAMPLE,
        "values": {"last_name": "", "first_name": "", "phone": "", "email": ""},
        "errors": {},
        "success": None,
    }

    if request.method == "POST":
        values, errors = validate(request.form)
        context["values"] = values
        context["errors"] = errors

        if not errors:
            save_registration(
                values["last_name"],
                values["first_name"],
                values["phone"],
                values["email"],
            )
            context["success"] = (
                f"{values['last_name']} {values['first_name']}, таны цаг захиалгын "
                f"хүсэлт амжилттай бүртгэгдлээ. Манай ажилтан тантай удахгүй холбогдоно."
            )
            context["values"] = {"last_name": "", "first_name": "", "phone": "", "email": ""}

    return render_template("register.html", **context)


# --- Admin хэсэг -----------------------------------------------------

def admin_required():
    return session.get("is_admin") is True


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin"))
        error = "Нууц үг буруу байна."
    return render_template("login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
def admin():
    if not admin_required():
        return redirect(url_for("admin_login"))
    rows = fetch_all_registrations()
    return render_template("admin.html", rows=rows, total=len(rows))


@app.route("/admin/export")
def admin_export():
    if not admin_required():
        return redirect(url_for("admin_login"))

    rows = fetch_all_registrations()

    wb = Workbook()
    ws = wb.active
    ws.title = "Register"
    ws.append(EXCEL_HEADERS)
    for r in rows:
        ws.append([
            r["id"],
            r["last_name"],
            r["first_name"],
            r["phone"],
            r["email"],
            r["created_at"],
        ])

    widths = [6, 18, 18, 16, 30, 22]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"Register_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        buf,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


init_db()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000, threaded=True)
