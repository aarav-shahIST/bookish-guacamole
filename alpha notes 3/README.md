# Alpha Notes

A minimal local Flask proof-of-concept note-taking app for PDF markup.

## Setup

```powershell
pip install -r requirements.txt
```

## Run

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Storage

- Uploaded PDFs are stored in `uploads/`.
- Annotation JSON files are stored in `annotations/`.
- The PDF sidebar is rebuilt from `uploads/` when Flask starts or the page reloads.

## Notes

PDF rendering uses PDF.js from the CDN. The local `static/pdf.worker.min.js` file points PDF.js at the matching CDN worker.
