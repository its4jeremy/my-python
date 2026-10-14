import pdfplumber

with pdfplumber.open("papers/9618/paper_3/9618_w25_ms_31.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        
            print(f"\n--- PAGE {i+1} ---")
            print(page.extract_text())
