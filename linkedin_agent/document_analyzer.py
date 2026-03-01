"""Document analyzer module for extracting business information from documents."""

import os
from typing import List, Dict
from pathlib import Path
import pypdf
import pdfplumber
from docx import Document


class DocumentAnalyzer:
    """Analyzes business documents to extract key information."""

    def __init__(self, documents_path: str = "./"):
        """Initialize the document analyzer.

        Args:
            documents_path: Path to the directory containing documents
        """
        self.documents_path = Path(documents_path)
        self.supported_extensions = {'.pdf', '.doc', '.docx'}

    def find_documents(self) -> List[Path]:
        """Find all supported documents in the documents path.

        Returns:
            List of Path objects for found documents
        """
        documents = []
        for ext in self.supported_extensions:
            documents.extend(self.documents_path.glob(f"*{ext}"))
        return documents

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        text_content = []

        try:
            # Try with pdfplumber first (better for complex PDFs)
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
        except Exception as e:
            print(f"pdfplumber failed for {pdf_path.name}, trying pypdf: {e}")
            # Fallback to pypdf
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = pypdf.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(page_text)
            except Exception as e:
                print(f"Failed to extract text from {pdf_path.name}: {e}")

        return "\n\n".join(text_content)

    def extract_text_from_docx(self, docx_path: Path) -> str:
        """Extract text from a Word document.

        Args:
            docx_path: Path to the Word document

        Returns:
            Extracted text content
        """
        try:
            doc = Document(docx_path)
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            return "\n\n".join(text_content)
        except Exception as e:
            print(f"Failed to extract text from {docx_path.name}: {e}")
            return ""

    def analyze_documents(self) -> Dict[str, str]:
        """Analyze all documents and extract their content.

        Returns:
            Dictionary mapping document names to their extracted content
        """
        documents = self.find_documents()
        analyzed_docs = {}

        print(f"\nFound {len(documents)} documents to analyze:")
        for doc_path in documents:
            print(f"  - {doc_path.name}")

        for doc_path in documents:
            print(f"\nAnalyzing: {doc_path.name}...")

            if doc_path.suffix == '.pdf':
                content = self.extract_text_from_pdf(doc_path)
            elif doc_path.suffix in ['.doc', '.docx']:
                content = self.extract_text_from_docx(doc_path)
            else:
                continue

            if content:
                analyzed_docs[doc_path.name] = content
                print(f"  ✓ Extracted {len(content)} characters")
            else:
                print(f"  ✗ No content extracted")

        return analyzed_docs

    def create_business_summary(self, analyzed_docs: Dict[str, str]) -> str:
        """Create a comprehensive summary of all analyzed documents.

        Args:
            analyzed_docs: Dictionary of document names to content

        Returns:
            Combined business summary
        """
        if not analyzed_docs:
            return "No documents were successfully analyzed."

        summary_parts = [
            "BUSINESS DOCUMENTS ANALYSIS",
            "=" * 50,
            ""
        ]

        for doc_name, content in analyzed_docs.items():
            summary_parts.append(f"\n### Document: {doc_name}")
            summary_parts.append("-" * 50)
            # Limit content to first 2000 characters per document
            summary_parts.append(content[:2000])
            if len(content) > 2000:
                summary_parts.append(f"\n... (truncated, {len(content) - 2000} more characters)")
            summary_parts.append("")

        return "\n".join(summary_parts)


if __name__ == "__main__":
    # Test the analyzer
    analyzer = DocumentAnalyzer("./")
    docs = analyzer.analyze_documents()
    summary = analyzer.create_business_summary(docs)
    print("\n" + summary)
