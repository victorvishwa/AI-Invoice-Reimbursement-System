import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.analysis_service import AnalysisService
from app.models import InvoiceAnalysis, AnalysisResponse
from app.services.pdf_service import PDFService
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService


class TestAnalysisService:
    @pytest.fixture
    def analysis_service(self):
        return AnalysisService()
    
    @pytest.fixture
    def mock_policy_text(self):
        return """
        HR REIMBURSEMENT POLICY
        
        Section 1: Travel Expenses
        - Hotel expenses up to $200/night
        - Meal expenses up to $50/day
        - Transportation expenses up to $30/day
        
        Section 2: Office Supplies
        - Office supplies up to $100/month
        - Equipment purchases require approval
        """
    
    @pytest.fixture
    def mock_invoice_text(self):
        return """
        INVOICE
        
        Date: 2024-01-15
        Invoice #: INV-001
        Employee: John Doe
        
        Description: Business Travel Expenses
        Amount: $250.00
        
        Details:
        - Hotel: $150.00
        - Meals: $75.00
        - Transportation: $25.00
        
        Total: $250.00
        """
    
    @pytest.mark.asyncio
    async def test_analyze_invoices_success(self, analysis_service, mock_policy_text, mock_invoice_text):
        """Test successful invoice analysis"""
        # Mock dependencies
        with patch.object(analysis_service.pdf_service, 'validate_pdf_file', return_value=True), \
             patch.object(analysis_service.pdf_service, 'validate_zip_file', return_value=True), \
             patch.object(analysis_service.pdf_service, 'extract_text_from_pdf_bytes', return_value=mock_policy_text), \
             patch.object(analysis_service.pdf_service, 'extract_invoices_from_zip', return_value=[('invoice1.pdf', mock_invoice_text)]), \
             patch.object(analysis_service.llm_service, 'analyze_invoice', return_value={
                 'status': 'Fully Reimbursed',
                 'reason': 'All expenses comply with policy',
                 'policy_reference': 'Section 1 - Travel Expenses',
                 'amount': 250.0,
                 'reimbursed_amount': 250.0
             }), \
             patch.object(analysis_service.embedding_service, 'generate_invoice_embedding', return_value=[0.1] * 384), \
             patch('app.services.analysis_service.db_manager') as mock_db:
            
            mock_db.insert_invoices_batch = AsyncMock()
            
            # Test the method
            result = await analysis_service.analyze_invoices(
                policy_bytes=b'fake_policy',
                policy_filename='policy.pdf',
                invoices_bytes=b'fake_invoices',
                invoices_filename='invoices.zip',
                employee_name='John Doe'
            )
            
            # Assertions
            assert result.status == 'success'
            assert result.total_invoices == 1
            assert len(result.results) == 1
            assert result.results[0].status == 'Fully Reimbursed'
            assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_analyze_invoices_invalid_policy(self, analysis_service):
        """Test analysis with invalid policy file"""
        with patch.object(analysis_service.pdf_service, 'validate_pdf_file', return_value=False):
            result = await analysis_service.analyze_invoices(
                policy_bytes=b'invalid',
                policy_filename='invalid.pdf',
                invoices_bytes=b'fake_invoices',
                invoices_filename='invoices.zip',
                employee_name='John Doe'
            )
            
            assert result.status == 'error'
            assert result.total_invoices == 0
    
    @pytest.mark.asyncio
    async def test_analyze_invoices_invalid_zip(self, analysis_service):
        """Test analysis with invalid ZIP file"""
        with patch.object(analysis_service.pdf_service, 'validate_pdf_file', return_value=True), \
             patch.object(analysis_service.pdf_service, 'validate_zip_file', return_value=False):
            
            result = await analysis_service.analyze_invoices(
                policy_bytes=b'valid_policy',
                policy_filename='policy.pdf',
                invoices_bytes=b'invalid_zip',
                invoices_filename='invalid.zip',
                employee_name='John Doe'
            )
            
            assert result.status == 'error'
            assert result.total_invoices == 0
    
    @pytest.mark.asyncio
    async def test_analyze_invoices_empty_policy(self, analysis_service):
        """Test analysis with empty policy text"""
        with patch.object(analysis_service.pdf_service, 'validate_pdf_file', return_value=True), \
             patch.object(analysis_service.pdf_service, 'validate_zip_file', return_value=True), \
             patch.object(analysis_service.pdf_service, 'extract_text_from_pdf_bytes', return_value=''):
            
            result = await analysis_service.analyze_invoices(
                policy_bytes=b'empty_policy',
                policy_filename='policy.pdf',
                invoices_bytes=b'fake_invoices',
                invoices_filename='invoices.zip',
                employee_name='John Doe'
            )
            
            assert result.status == 'error'
            assert result.total_invoices == 0
    
    @pytest.mark.asyncio
    async def test_analyze_invoices_no_invoices(self, analysis_service, mock_policy_text):
        """Test analysis with no invoices in ZIP"""
        with patch.object(analysis_service.pdf_service, 'validate_pdf_file', return_value=True), \
             patch.object(analysis_service.pdf_service, 'validate_zip_file', return_value=True), \
             patch.object(analysis_service.pdf_service, 'extract_text_from_pdf_bytes', return_value=mock_policy_text), \
             patch.object(analysis_service.pdf_service, 'extract_invoices_from_zip', return_value=[]):
            
            result = await analysis_service.analyze_invoices(
                policy_bytes=b'valid_policy',
                policy_filename='policy.pdf',
                invoices_bytes=b'empty_zip',
                invoices_filename='invoices.zip',
                employee_name='John Doe'
            )
            
            assert result.status == 'error'
            assert result.total_invoices == 0
    
    def test_get_analysis_summary(self, analysis_service):
        """Test analysis summary generation"""
        # Create sample results
        results = [
            InvoiceAnalysis(
                invoice_id='inv1.pdf',
                status='Fully Reimbursed',
                reason='Valid expenses',
                policy_reference='Section 1',
                amount=100.0,
                reimbursed_amount=100.0
            ),
            InvoiceAnalysis(
                invoice_id='inv2.pdf',
                status='Partially Reimbursed',
                reason='Some expenses exceed limits',
                policy_reference='Section 1',
                amount=200.0,
                reimbursed_amount=150.0
            ),
            InvoiceAnalysis(
                invoice_id='inv3.pdf',
                status='Declined',
                reason='Non-business expenses',
                policy_reference='Section 4',
                amount=50.0,
                reimbursed_amount=0.0
            )
        ]
        
        summary = analysis_service.get_analysis_summary(results)
        
        assert summary['total_invoices'] == 3
        assert summary['status_distribution']['Fully Reimbursed'] == 1
        assert summary['status_distribution']['Partially Reimbursed'] == 1
        assert summary['status_distribution']['Declined'] == 1
        assert summary['total_amount'] == 350.0
        assert summary['total_reimbursed'] == 250.0
        assert summary['reimbursement_rate'] == pytest.approx(71.43, rel=0.01)
    
    def test_get_analysis_summary_empty(self, analysis_service):
        """Test analysis summary with empty results"""
        summary = analysis_service.get_analysis_summary([])
        
        assert summary['total_invoices'] == 0
        assert summary['total_amount'] == 0.0
        assert summary['total_reimbursed'] == 0.0
        assert summary['reimbursement_rate'] == 0.0


if __name__ == "__main__":
    pytest.main([__file__]) 