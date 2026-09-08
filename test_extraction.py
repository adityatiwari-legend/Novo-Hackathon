import os
from backend.app.services.document_parser import extract_structured_gxp_entities, extract_document_id, parse_docx

docs_dir = 'data/pasx_documents'
for f in os.listdir(docs_dir):
    if f.endswith('.docx'):
        file_path = os.path.join(docs_dir, f)
        text, _, _ = parse_docx(file_path)
        reqs, risks, gates = extract_structured_gxp_entities(text, extract_document_id(f, text))
        print(f"{f}: {len(reqs)} reqs, {len(risks)} risks, {len(gates)} gates")
