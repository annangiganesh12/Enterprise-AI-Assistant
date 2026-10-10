
from app.utils.pdf_loader import extract_text_from_pdf

documents = extract_text_from_pdf("uploads/02b08f6b-17ff-4408-820b-e65b8256a690_Lab1.pdf")

print("Number of pages:" , len(documents))

for document in documents:

    print("\n ---- PAGE ----")

    print(document.page_content[:500])
    