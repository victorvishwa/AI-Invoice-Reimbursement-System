from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
import logging
from typing import Optional
from ..services.analysis_service import analysis_service
from ..services.policy_service import policy_service
from ..models import AnalysisResponse, ErrorResponse
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze-invoices", tags=["Invoice Analysis"])


@router.post("/", response_model=AnalysisResponse)
async def analyze_invoices(
    invoices: UploadFile = File(..., description="ZIP file containing employee invoice PDFs"),
    employee_name: str = Form("Batch Analysis", description="Employee name (optional - defaults to 'Batch Analysis')"),
    policy: Optional[UploadFile] = File(None, description="HR Policy PDF file (optional - uses integrated policy if not provided)"),
    use_integrated_policy: bool = Query(True, description="Use integrated IAI Solution policy (default: True)"),
):
    """
    Analyze employee invoices against HR policy.
    
    This endpoint processes a ZIP file containing employee invoice PDFs and analyzes them
    against the HR policy. By default, it uses the integrated IAI Solution policy.
    
    You can also provide a custom policy PDF file by setting use_integrated_policy=False
    and uploading a policy file.
    
    The system uses AI to classify each invoice as:
    - Fully Reimbursed
    - Partially Reimbursed  
    - Declined
    
    The results are stored in the database with vector embeddings for future querying.
    """
    try:
        # Validate file types
        if not invoices.filename.lower().endswith('.zip'):
            raise HTTPException(
                status_code=400, 
                detail="Invoices file must be a ZIP"
            )
        
        # Validate file sizes
        if invoices.size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"Invoices file too large. Maximum size is {settings.max_file_size / (1024*1024):.1f}MB"
            )
        
        # Handle policy file if provided
        policy_bytes = None
        policy_filename = None
        
        if not use_integrated_policy:
            if not policy:
                raise HTTPException(
                    status_code=400,
                    detail="Policy file is required when use_integrated_policy is False"
                )
            
            if not policy.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400, 
                    detail="Policy file must be a PDF"
                )
            
            if policy.size > settings.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"Policy file too large. Maximum size is {settings.max_file_size / (1024*1024):.1f}MB"
                )
            
            try:
                policy_bytes = await policy.read()
                policy_filename = policy.filename
            except Exception as e:
                logger.error(f"Failed to read policy file: {e}")
                raise HTTPException(
                    status_code=400,
                    detail="Failed to read policy file"
                )
        
        # Read invoices file
        try:
            invoices_bytes = await invoices.read()
        except Exception as e:
            logger.error(f"Failed to read invoices file: {e}")
            raise HTTPException(
                status_code=400,
                detail="Failed to read invoices file"
            )
        
        # Use default employee name if not provided
        if not employee_name.strip():
            employee_name = "Batch Analysis"
        
        logger.info(f"Starting invoice analysis for employee: {employee_name}")
        logger.info(f"Invoices file: {invoices.filename}")
        logger.info(f"Using integrated policy: {use_integrated_policy}")
        
        # Perform analysis
        result = await analysis_service.analyze_invoices(
            invoices_bytes=invoices_bytes,
            invoices_filename=invoices.filename,
            employee_name=employee_name,
            policy_bytes=policy_bytes,
            policy_filename=policy_filename,
            use_integrated_policy=use_integrated_policy
        )
        
        if result.status == "error":
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze invoices. Please check your files and try again."
            )
        
        logger.info(f"Successfully analyzed {result.total_invoices} invoices for {employee_name}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_invoices: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request"
        )


@router.get("/policy")
async def get_policy_info():
    """Get information about the integrated IAI Solution policy"""
    try:
        policy_summary = policy_service.get_policy_summary()
        return {
            "status": "success",
            "policy": policy_summary
        }
    except Exception as e:
        logger.error(f"Failed to get policy info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve policy information"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for the analysis service"""
    return {"status": "healthy", "service": "invoice-analysis"} 