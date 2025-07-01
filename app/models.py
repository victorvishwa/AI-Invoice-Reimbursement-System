from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ReimbursementStatus(str, Enum):
    FULLY_REIMBURSED = "Fully Reimbursed"
    PARTIALLY_REIMBURSED = "Partially Reimbursed"
    DECLINED = "Declined"


class InvoiceAnalysis(BaseModel):
    invoice_id: str
    status: ReimbursementStatus
    reason: str
    policy_reference: str
    amount: Optional[float] = None
    reimbursed_amount: Optional[float] = None
    category: Optional[str] = None
    policy_rule: Optional[str] = None


class AnalysisRequest(BaseModel):
    employee_name: str


class AnalysisResponse(BaseModel):
    status: str
    results: List[InvoiceAnalysis]
    total_invoices: int
    processing_time: float


class ChatQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)


class SourceDocument(BaseModel):
    invoice_id: str
    employee: str
    date: datetime
    status: ReimbursementStatus
    similarity_score: float


class ChatQueryResponse(BaseModel):
    response: str
    sources: List[SourceDocument]
    confidence_score: float


class InvoiceDocument(BaseModel):
    id: Optional[str] = None
    invoice_id: str
    employee_name: str
    content: str
    analysis_result: InvoiceAnalysis
    embedding: List[float]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) 