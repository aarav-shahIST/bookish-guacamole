import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
ANNOTATION_DIR = BASE_DIR / "annotations"

UPLOAD_DIR.mkdir(exist_ok=True)
ANNOTATION_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024


def pdfs():
    return sorted(p.name for p in UPLOAD_DIR.glob("*.pdf"))


def blank_documents():
    docs = []
    for path in sorted(ANNOTATION_DIR.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        meta = data.get("meta", {})
        if meta.get("type") == "blank":
            docs.append({
                "name": path.name.removesuffix(".json"),
                "title": meta.get("title") or path.name.removesuffix(".json"),
                "type": "blank",
            })
    return docs


def annotation_path(filename):
    safe = secure_filename(filename)
    return ANNOTATION_DIR / f"{safe}.json"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_pdf():
    file = request.files.get("pdf")
    if not file or not file.filename:
        return jsonify({"error": "No PDF selected"}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    file.save(UPLOAD_DIR / filename)
    return jsonify({"filename": filename})


@app.route("/pdfs", methods=["GET"])
def list_pdfs():
    return jsonify({"pdfs": pdfs()})


@app.route("/documents", methods=["GET"])
def list_documents():
    documents = [{"name": name, "title": name, "type": "pdf"} for name in pdfs()]
    documents.extend(blank_documents())
    return jsonify({"documents": documents})


@app.route("/blank-documents", methods=["POST"])
def create_blank_document():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "Lined notes").strip()[:80]
    filename = secure_filename(title) or "lined-notes"
    candidate = filename
    index = 2

    while annotation_path(candidate).exists():
        candidate = f"{filename}-{index}"
        index += 1

    clean = {
        "meta": {
            "type": "blank",
            "title": title,
            "pageCount": 1,
            "lineSpacing": 34,
        },
        "strokes": [],
        "spaces": [],
    }

    with annotation_path(candidate).open("w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2)

    return jsonify({"name": candidate, "title": title, "type": "blank"})


@app.route("/pdf/<path:filename>", methods=["GET"])
def open_pdf(filename):
    safe = secure_filename(filename)
    return send_from_directory(UPLOAD_DIR, safe)


@app.route("/annotations/<path:filename>", methods=["GET"])
def load_annotations(filename):
    path = annotation_path(filename)
    if not path.exists():
        return jsonify({"strokes": [], "spaces": []})

    with path.open("r", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/annotations/<path:filename>", methods=["POST"])
def save_annotations(filename):
    data = request.get_json(silent=True) or {}
    clean = {
        "meta": data.get("meta", {}),
        "strokes": data.get("strokes", []),
        "spaces": data.get("spaces", []),
    }

    path = annotation_path(filename)
    with path.open("w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2)

    return jsonify({"saved": True})


@app.route("/annotations/<path:filename>", methods=["DELETE"])
def delete_annotations(filename):
    path = annotation_path(filename)
    if path.exists():
        path.unlink()

    return jsonify({"deleted": True})


if __name__ == "__main__":
    app.run(debug=True)
