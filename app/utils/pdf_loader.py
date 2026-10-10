

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader

def extract_text_from_pdf(file_path: str):

    loader = PyPDFLoader(file_path)
    documents = loader.load()

    return documents