from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import os
from legal_ai.simplifier import simplify_text
from legal_ai.risk_rules import analyze_risks
from legal_ai.qa import answer_question
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {"txt"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    # Accept text or file upload
    raw_text = request.form.get("raw_text", "").strip()
    uploaded_text = ""
    if "file" in request.files:
        f = request.files["file"]
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            f.save(path)
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                uploaded_text = fh.read()
    document = uploaded_text if uploaded_text else raw_text
    if not document:
        return render_template("index.html", error="Please paste text or upload a .txt file.")

    simplified, mapping = simplify_text(document)
    risks = analyze_risks(document)

    return render_template("result.html",
                           original=document,
                           simplified=simplified,
                           mapping=mapping,
                           risks=risks)

@app.route("/api/qa", methods=["POST"])
def api_qa():
    data = request.get_json(force=True)
    document = data.get("document", "")
    question = data.get("question", "")
    if not document or not question:
        return jsonify({"error": "Missing document/question"}), 400
    answer, evidence = answer_question(document, question)
    return jsonify({"answer": answer, "evidence": evidence})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
