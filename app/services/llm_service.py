import logging
import json
from typing import Dict, Any, List, Optional
import groq
import openai
import google.generativeai as genai
from ..config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client based on provider"""
        try:
            if self.provider == "groq":
                if not settings.groq_api_key:
                    raise ValueError("GROQ_API_KEY not set in environment")
                self.client = groq.Groq(api_key=settings.groq_api_key)
                self.model = "deepseek-r1-distill-llama-70b"
                
            elif self.provider == "openai":
                if not settings.openai_api_key:
                    raise ValueError("OPENAI_API_KEY not set in environment")
                self.client = openai.OpenAI(api_key=settings.openai_api_key)
                self.model = "gpt-4"
                
            elif self.provider == "google":
                if not settings.google_api_key:
                    raise ValueError("GOOGLE_API_KEY not set in environment")
                genai.configure(api_key=settings.google_api_key)
                self.client = genai
                self.model = "gemini-pro"
                
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
                
            logger.info(f"Initialized {self.provider} LLM client with model {self.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise
    
    def analyze_invoice(self, policy_text: str, invoice_text: str, invoice_id: str) -> Dict[str, Any]:
        """Analyze a single invoice against the HR policy"""
        try:
            prompt = self._create_analysis_prompt(policy_text, invoice_text, invoice_id)
            
            if self.provider == "groq":
                response = self._call_groq(prompt)
            elif self.provider == "openai":
                response = self._call_openai(prompt)
            elif self.provider == "google":
                response = self._call_google(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Parse the response
            analysis_result = self._parse_analysis_response(response)
            logger.info(f"Successfully analyzed invoice {invoice_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Failed to analyze invoice {invoice_id}: {e}")
            # Return fallback analysis
            return self._get_fallback_analysis(invoice_id)
    
    def answer_chat_query(self, query: str, context_documents: List[Dict[str, Any]]) -> str:
        """Answer a chat query using context from vector search"""
        try:
            prompt = self._create_chat_prompt(query, context_documents)
            
            if self.provider == "groq":
                response = self._call_groq(prompt)
            elif self.provider == "openai":
                response = self._call_openai(prompt)
            elif self.provider == "google":
                response = self._call_google(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            logger.info(f"Successfully answered chat query: {query[:50]}...")
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to answer chat query: {e}")
            return self._get_fallback_chat_response(query)
    
    def answer_chat_query_stream(self, query: str, context_documents: List[Dict[str, Any]]):
        """Answer a chat query using streaming response"""
        try:
            prompt = self._create_chat_prompt(query, context_documents)
            
            if self.provider == "groq":
                response = self._call_groq(prompt, stream=True)
                return response
            elif self.provider == "openai":
                # For OpenAI, we'll use non-streaming for now
                response = self._call_openai(prompt)
                return response
            elif self.provider == "google":
                response = self._call_google(prompt)
                return response
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
        except Exception as e:
            logger.error(f"Failed to answer chat query with streaming: {e}")
            return self._get_fallback_chat_response(query)

    def _create_analysis_prompt(self, policy_text: str, invoice_text: str, invoice_id: str) -> str:
        """Create prompt for invoice analysis"""
        return f"""You are a financial auditor specializing in HR reimbursement policies. 

Given the following HR reimbursement policy and an employee invoice, determine the reimbursement status and provide a detailed explanation.

HR POLICY:
{policy_text[:4000]}  # Limit policy text to avoid token limits

INVOICE ({invoice_id}):
{invoice_text[:2000]}  # Limit invoice text to avoid token limits

Please analyze this invoice against the policy and provide your response in the following JSON format:

{{
    "status": "Fully Reimbursed" | "Partially Reimbursed" | "Declined",
    "reason": "Detailed explanation of why this status was chosen",
    "policy_reference": "Specific section or rule from the policy that applies",
    "amount": <total_invoice_amount_if_mentioned>,
    "reimbursed_amount": <amount_to_be_reimbursed>
}}

Focus on:
1. Whether the expenses are covered by the policy
2. Any policy violations or limitations
3. Specific policy sections that apply
4. Clear reasoning for the decision

Respond only with valid JSON."""

    def _create_chat_prompt(self, query: str, context_documents: List[Dict[str, Any]]) -> str:
        """Create prompt for chat query"""
        context_text = ""
        for i, doc in enumerate(context_documents[:5]):  # Limit to top 5 results
            context_text += f"""
Document {i+1}:
- Invoice ID: {doc.get('invoice_id', 'Unknown')}
- Employee: {doc.get('employee_name', 'Unknown')}
- Status: {doc.get('analysis_result', {}).get('status', 'Unknown')}
- Reason: {doc.get('analysis_result', {}).get('reason', 'Unknown')}
- Policy Reference: {doc.get('analysis_result', {}).get('policy_reference', 'Unknown')}
- Content: {doc.get('content', '')[:500]}
"""

        return f"""You are an intelligent assistant that answers queries about past invoice analyses.

User Query: {query}

Context from previous invoice analyses:
{context_text}

Based on the provided context, answer the user's query in a clear and helpful manner. If the context doesn't contain enough information to answer the query, say so. Format your response in markdown and be specific about which invoices or employees you're referring to.

Focus on:
1. Providing accurate information based on the context
2. Explaining the reasoning behind reimbursement decisions
3. Referencing specific policy sections when relevant
4. Being helpful and professional in tone"""

    def _call_groq(self, prompt: str, stream: bool = False) -> str:
        """Call Groq API with updated parameters"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=4096,
                top_p=0.95,
                stream=stream,
                stop=None,
            )
            
            if stream:
                # Handle streaming response
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                return full_response
            else:
                # Handle non-streaming response
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2048
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    def _call_google(self, prompt: str) -> str:
        """Call Google Gemini API"""
        try:
            model = self.client.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Google API call failed: {e}")
            raise

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response for invoice analysis"""
        try:
            # Try to extract JSON from response
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            
            # Parse JSON
            result = json.loads(response_clean)
            
            # Validate required fields
            required_fields = ["status", "reason", "policy_reference"]
            for field in required_fields:
                if field not in result:
                    result[field] = "Not specified"
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response}")
            return self._get_fallback_analysis("unknown")

    def _get_fallback_analysis(self, invoice_id: str) -> Dict[str, Any]:
        """Return fallback analysis when LLM fails"""
        return {
            "status": "Declined",
            "reason": "Unable to analyze invoice due to processing error",
            "policy_reference": "Error in analysis",
            "amount": None,
            "reimbursed_amount": None
        }

    def _get_fallback_chat_response(self, query: str) -> str:
        """Return fallback response when chat query fails"""
        return f"I apologize, but I'm unable to process your query at the moment. Please try again later or contact support if the issue persists.\n\nYour query was: {query}"


# Global LLM service instance
llm_service = LLMService() 