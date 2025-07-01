import logging
import time
from typing import List, Dict, Any, Tuple
from datetime import datetime
from .pdf_service import pdf_service
from .llm_service import llm_service
from .embedding_service import embedding_service
from .policy_service import policy_service
from ..database import db_manager
from ..models import InvoiceAnalysis, AnalysisResponse, InvoiceDocument

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self):
        self.pdf_service = pdf_service
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self.policy_service = policy_service
    
    async def analyze_invoices(self, invoices_bytes: bytes, invoices_filename: str,
                             employee_name: str, policy_bytes: bytes = None, 
                             policy_filename: str = None, use_integrated_policy: bool = True) -> AnalysisResponse:
        """Main method to analyze invoices against HR policy"""
        start_time = time.time()
        
        try:
            # Validate input files
            if not self.pdf_service.validate_zip_file(invoices_bytes, invoices_filename):
                raise ValueError("Invalid invoices ZIP file")
            
            # Get policy text - use integrated policy by default
            if use_integrated_policy:
                policy_text = self.policy_service.get_policy_text()
                logger.info("Using integrated IAI Solution policy")
            else:
                if not policy_bytes or not policy_filename:
                    raise ValueError("Policy file required when not using integrated policy")
                if not self.pdf_service.validate_pdf_file(policy_bytes, policy_filename):
                    raise ValueError("Invalid policy PDF file")
                policy_text = self.pdf_service.extract_text_from_pdf_bytes(policy_bytes, policy_filename)
                if not policy_text.strip():
                    raise ValueError("Could not extract text from policy PDF")
                logger.info("Using uploaded policy file")
            
            # Extract invoice texts
            logger.info("Extracting invoice texts...")
            invoices = self.pdf_service.extract_invoices_from_zip(invoices_bytes)
            if not invoices:
                raise ValueError("No valid invoices found in ZIP file")
            
            # Analyze each invoice
            logger.info(f"Analyzing {len(invoices)} invoices...")
            analysis_results = []
            invoice_documents = []
            
            for invoice_filename, invoice_text in invoices:
                try:
                    # Use integrated policy analysis
                    if use_integrated_policy:
                        analysis_result = self.policy_service.analyze_invoice_with_policy(
                            invoice_text, invoice_filename
                        )
                    else:
                        # Use LLM analysis for custom policies
                        analysis_result = self.llm_service.analyze_invoice(
                            policy_text, invoice_text, invoice_filename
                        )
                    
                    # Create InvoiceAnalysis object
                    invoice_analysis = InvoiceAnalysis(
                        invoice_id=invoice_filename,
                        status=analysis_result["status"],
                        reason=analysis_result["reason"],
                        policy_reference=analysis_result["policy_reference"],
                        amount=analysis_result.get("amount"),
                        reimbursed_amount=analysis_result.get("reimbursed_amount"),
                        category=analysis_result.get("category"),
                        policy_rule=analysis_result.get("policy_rule")
                    )
                    
                    analysis_results.append(invoice_analysis)
                    
                    # Generate embedding for storage
                    embedding = self.embedding_service.generate_invoice_embedding(
                        invoice_text, analysis_result
                    )
                    
                    # Create document for database storage
                    invoice_doc = InvoiceDocument(
                        invoice_id=invoice_filename,
                        employee_name=employee_name,
                        content=invoice_text,
                        analysis_result=invoice_analysis,
                        embedding=embedding,
                        created_at=datetime.utcnow(),
                        metadata={
                            "policy_type": "integrated" if use_integrated_policy else "uploaded",
                            "policy_filename": policy_filename if not use_integrated_policy else "IAI_Solution_Policy",
                            "invoices_filename": invoices_filename,
                            "processing_timestamp": datetime.utcnow().isoformat(),
                            "category": analysis_result.get("category", "unknown"),
                            "policy_rule": analysis_result.get("policy_rule", "unknown")
                        }
                    )
                    
                    invoice_documents.append(invoice_doc.dict())
                    
                    logger.info(f"Analyzed invoice {invoice_filename}: {analysis_result['status']}")
                    
                except Exception as e:
                    logger.error(f"Failed to analyze invoice {invoice_filename}: {e}")
                    # Add fallback analysis
                    fallback_analysis = InvoiceAnalysis(
                        invoice_id=invoice_filename,
                        status="Declined",
                        reason=f"Analysis failed: {str(e)}",
                        policy_reference="Error in processing"
                    )
                    analysis_results.append(fallback_analysis)
            
            # Store results in database
            if invoice_documents:
                logger.info("Storing analysis results in database...")
                await db_manager.insert_invoices_batch(invoice_documents)
            
            processing_time = time.time() - start_time
            
            return AnalysisResponse(
                status="success",
                results=analysis_results,
                total_invoices=len(invoices),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Invoice analysis failed: {e}")
            processing_time = time.time() - start_time
            return AnalysisResponse(
                status="error",
                results=[],
                total_invoices=0,
                processing_time=processing_time
            )
    
    async def process_chat_query(self, query: str) -> Tuple[str, List[Dict[str, Any]], float]:
        """Process a chat query using vector search"""
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Perform vector search
            search_results = await db_manager.vector_search(
                query_embedding=query_embedding,
                limit=10
            )
            
            if not search_results:
                logger.warning("No relevant documents found for query")
                return "I couldn't find any relevant invoice analyses to answer your query.", [], 0.0
            
            # Get confidence score from top result
            confidence_score = search_results[0].get('score', 0.0) if search_results else 0.0
            
            # Answer query using LLM
            response = self.llm_service.answer_chat_query(query, search_results)
            
            # Format sources for response
            sources = []
            for result in search_results[:5]:  # Top 5 results
                source = {
                    "invoice_id": result.get("invoice_id", "Unknown"),
                    "employee": result.get("employee_name", "Unknown"),
                    "date": result.get("created_at", datetime.utcnow()),
                    "status": result.get("analysis_result", {}).get("status", "Unknown"),
                    "similarity_score": result.get("score", 0.0)
                }
                sources.append(source)
            
            return response, sources, confidence_score
            
        except Exception as e:
            logger.error(f"Chat query processing failed: {e}")
            return f"Sorry, I encountered an error while processing your query: {str(e)}", [], 0.0
    
    def get_analysis_summary(self, results: List[InvoiceAnalysis]) -> Dict[str, Any]:
        """Generate summary statistics from analysis results"""
        try:
            total_invoices = len(results)
            status_counts = {}
            total_amount = 0.0
            total_reimbursed = 0.0
            
            for result in results:
                # Count statuses
                status = result.status
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Sum amounts
                if result.amount:
                    total_amount += result.amount
                if result.reimbursed_amount:
                    total_reimbursed += result.reimbursed_amount
            
            return {
                "total_invoices": total_invoices,
                "status_distribution": status_counts,
                "total_amount": total_amount,
                "total_reimbursed": total_reimbursed,
                "reimbursement_rate": (total_reimbursed / total_amount * 100) if total_amount > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to generate analysis summary: {e}")
            return {
                "total_invoices": 0,
                "status_distribution": {},
                "total_amount": 0.0,
                "total_reimbursed": 0.0,
                "reimbursement_rate": 0.0
            }


# Global analysis service instance
analysis_service = AnalysisService() 