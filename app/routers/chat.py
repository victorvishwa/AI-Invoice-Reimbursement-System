from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
from ..services.analysis_service import analysis_service
from ..models import ChatQueryRequest, ChatQueryResponse, SourceDocument
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat-query", tags=["Chat Query"])


@router.post("/", response_model=ChatQueryResponse)
async def chat_query(request: ChatQueryRequest):
    """
    Query past invoice analyses using natural language.
    
    This endpoint allows users to ask questions about previously analyzed invoices
    using natural language. The system uses vector search to find relevant invoice
    analyses and provides AI-generated responses based on the retrieved context.
    
    Example queries:
    - "Why was John's invoice rejected in June?"
    - "Show me all declined invoices for travel expenses"
    - "What was the total reimbursement amount for Sarah last month?"
    """
    try:
        # Validate query
        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )
        
        if len(request.query) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Query too long. Maximum length is 1000 characters"
            )
        
        logger.info(f"Processing chat query: {request.query[:50]}...")
        
        # Process the query
        response_text, sources, confidence_score = await analysis_service.process_chat_query(
            request.query
        )
        
        # Convert sources to SourceDocument objects
        source_documents = []
        for source in sources:
            try:
                # Handle date conversion
                date_value = source.get("date")
                if isinstance(date_value, str):
                    date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                elif not isinstance(date_value, datetime):
                    date_value = datetime.utcnow()
                
                source_doc = SourceDocument(
                    invoice_id=source.get("invoice_id", "Unknown"),
                    employee=source.get("employee", "Unknown"),
                    date=date_value,
                    status=source.get("status", "Unknown"),
                    similarity_score=source.get("similarity_score", 0.0)
                )
                source_documents.append(source_doc)
            except Exception as e:
                logger.warning(f"Failed to process source document: {e}")
                continue
        
        logger.info(f"Successfully processed chat query. Found {len(source_documents)} relevant sources")
        
        return ChatQueryResponse(
            response=response_text,
            sources=source_documents,
            confidence_score=confidence_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat_query: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your query"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for the chat service"""
    return {"status": "healthy", "service": "chat-query"}


@router.get("/examples")
async def get_example_queries():
    """Get example queries for the chat interface"""
    examples = [
        {
            "query": "Why was John's invoice rejected in June?",
            "description": "Ask about specific invoice rejections"
        },
        {
            "query": "Show me all declined invoices for travel expenses",
            "description": "Find invoices by status and expense type"
        },
        {
            "query": "What was the total reimbursement amount for Sarah last month?",
            "description": "Get reimbursement totals for specific employees"
        },
        {
            "query": "Which invoices were partially reimbursed due to policy violations?",
            "description": "Find invoices with specific analysis reasons"
        },
        {
            "query": "What are the most common reasons for invoice rejections?",
            "description": "Analyze rejection patterns"
        }
    ]
    
    return {
        "examples": examples,
        "description": "Example queries you can use with the chat interface"
    } 