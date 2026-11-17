# Document Risk Detection

  Name : M.surya Varshitha
  Roll No: 23A81A6140

  Name : B.Durga Bhavani
  Roll No : 23A81A6140

Small local MVP for uploading documents, reviewing evidence-backed risks, and asking questions grounded in the uploaded text.

## Supported formats

PDF, DOCX, XLSX, PPTX, TXT, Markdown, CSV, JSON, and common image formats (OCR requires the Tesseract executable installed on your machine). Scanned PDF OCR and audio/video extraction are not included yet.

## Run locally

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Add `GROQ_API_KEY=your_key` to `.env`. The app reads the key locally and does not display it. Restart Streamlit after changing `.env`.
5. Run `streamlit run app.py`.

## Risk score

The displayed score is a prioritization index using impact (50%), likelihood (30%), and control gap (20%), each scored 1–5. It is not a probability. The model must provide document evidence for each finding, and users should review the evidence and suggested mitigations.

## Current MVP limits

- Extraction and retrieval happen in memory; uploads are not persisted by this app.
- Retrieval uses simple lexical matching, not embeddings or semantic search.
- Risk analysis splits text into roughly 5,000-character sections and sends them sequentially to stay below common free-tier token-per-minute limits. Each section consumes an API request; each chatbot question makes one additional request.
- Groq API calls send extracted document text to Groq for processing; review your data handling needs before uploading sensitive material.
- Long documents are capped at 300,000 extracted characters for this prototype.
- This is a screening aid, not a substitute for expert legal, safety, financial, or security review.
- Do not upload sensitive documents until your API provider, access controls, retention, and data handling are configured for your requirements.
