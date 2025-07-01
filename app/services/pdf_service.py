import fitz  # PyMuPDF
import zipfile
import tempfile
import os
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFService:
    def __init__(self):
        from ..config import settings
        self.supported_extensions = settings.allowed_pdf_extensions_list
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a single PDF file"""
        try:
            doc = fitz.open(pdf_path)
            text_content = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text_content += page.get_text()
            
            doc.close()
            logger.info(f"Successfully extracted text from {pdf_path}")
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            raise
    
    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes, filename: str) -> str:
        """Extract text content from PDF bytes"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_file_path = temp_file.name
            
            try:
                text_content = self.extract_text_from_pdf(temp_file_path)
                return text_content
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Failed to extract text from PDF bytes: {e}")
            raise
    
    def extract_invoices_from_zip(self, zip_bytes: bytes) -> List[Tuple[str, str]]:
        """Extract and process all PDF invoices from a ZIP file"""
        invoices = []
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write ZIP file to temporary directory
                zip_path = os.path.join(temp_dir, "invoices.zip")
                with open(zip_path, 'wb') as f:
                    f.write(zip_bytes)
                
                # Extract ZIP contents
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Process all PDF files
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_ext = Path(file).suffix.lower()
                        
                        if file_ext in self.supported_extensions:
                            try:
                                text_content = self.extract_text_from_pdf(file_path)
                                if text_content.strip():  # Only add non-empty content
                                    invoices.append((file, text_content))
                                    logger.info(f"Processed invoice: {file}")
                                else:
                                    logger.warning(f"Empty content in {file}")
                            except Exception as e:
                                logger.error(f"Failed to process {file}: {e}")
                                continue
                
                logger.info(f"Successfully processed {len(invoices)} invoices from ZIP")
                return invoices
                
        except Exception as e:
            logger.error(f"Failed to extract invoices from ZIP: {e}")
            raise
    
    def validate_pdf_file(self, pdf_bytes: bytes, filename: str) -> bool:
        """Validate that the file is a valid PDF"""
        try:
            # Check file extension
            if not filename.lower().endswith('.pdf'):
                return False
            
            # Try to open with PyMuPDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_file_path = temp_file.name
            
            try:
                doc = fitz.open(temp_file_path)
                if len(doc) == 0:
                    return False
                doc.close()
                return True
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"PDF validation failed for {filename}: {e}")
            return False
    
    def validate_zip_file(self, zip_bytes: bytes, filename: str) -> bool:
        """Validate that the file is a valid ZIP containing PDFs"""
        try:
            # Check file extension
            if not filename.lower().endswith('.zip'):
                return False
            
            # Try to open as ZIP
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                temp_file.write(zip_bytes)
                temp_file_path = temp_file.name
            
            try:
                with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                    # Check if ZIP contains at least one PDF
                    pdf_files = [f for f in zip_ref.namelist() 
                               if f.lower().endswith('.pdf')]
                    return len(pdf_files) > 0
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"ZIP validation failed for {filename}: {e}")
            return False
    
    def get_pdf_metadata(self, pdf_bytes: bytes) -> Dict[str, any]:
        """Extract metadata from PDF"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_file_path = temp_file.name
            
            try:
                doc = fitz.open(temp_file_path)
                metadata = {
                    'page_count': len(doc),
                    'title': doc.metadata.get('title', ''),
                    'author': doc.metadata.get('author', ''),
                    'subject': doc.metadata.get('subject', ''),
                    'creator': doc.metadata.get('creator', ''),
                    'producer': doc.metadata.get('producer', ''),
                    'creation_date': doc.metadata.get('creationDate', ''),
                    'modification_date': doc.metadata.get('modDate', '')
                }
                doc.close()
                return metadata
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Failed to extract PDF metadata: {e}")
            return {}


# Global PDF service instance
pdf_service = PDFService() 