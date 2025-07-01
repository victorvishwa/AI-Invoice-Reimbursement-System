#!/usr/bin/env python3
"""
Comprehensive example of Groq integration with the Intelligent Invoice Reimbursement System
"""

import os
import sys
import json
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_service import llm_service
from app.services.policy_service import policy_service
from app.config import settings

def demonstrate_groq_integration():
    """Demonstrate the complete Groq integration"""
    print("🚀 Groq Integration Demonstration")
    print("=" * 60)
    
    # Check configuration
    print("1. 🔧 Configuration Check")
    print("-" * 30)
    print(f"LLM Provider: {settings.llm_provider}")
    print(f"Groq Model: {llm_service.model}")
    print(f"Groq API Key: {'✅ Set' if settings.groq_api_key else '❌ Not Set'}")
    
    if not settings.groq_api_key:
        print("\n❌ Please set your GROQ_API_KEY in the .env file")
        return
    
    # Test basic Groq functionality
    print("\n2. 🧪 Basic Groq Test")
    print("-" * 30)
    
    test_prompt = "Hello! I'm testing the Groq integration. Please respond with a brief greeting."
    
    try:
        response = llm_service._call_groq(test_prompt, stream=False)
        print(f"✅ Response: {response[:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test streaming functionality
    print("\n3. 🌊 Streaming Test")
    print("-" * 30)
    
    streaming_prompt = "Please explain the benefits of using AI for invoice analysis in 3 points."
    
    try:
        print("📤 Sending streaming request...")
        response = llm_service._call_groq(streaming_prompt, stream=True)
        print(f"✅ Streaming Response: {response[:150]}...")
    except Exception as e:
        print(f"❌ Streaming Error: {e}")
    
    # Test invoice analysis with Groq
    print("\n4. 📊 Invoice Analysis with Groq")
    print("-" * 30)
    
    # Sample invoice data
    sample_invoices = [
        {
            "text": "Restaurant Bill\nBusiness lunch meeting\nAmount: ₹180\nDate: 2024-01-15",
            "expected_category": "food_beverages"
        },
        {
            "text": "Taxi Fare\nClient meeting transport\nTotal: ₹500\nDate: 2024-01-16",
            "expected_category": "travel_expenses"
        },
        {
            "text": "Hotel Stay\nBusiness trip accommodation\nRoom Charge: ₹45\nDate: 2024-01-17",
            "expected_category": "accommodation"
        }
    ]
    
    for i, invoice in enumerate(sample_invoices, 1):
        print(f"\n📄 Invoice {i}:")
        print(f"Text: {invoice['text']}")
        print(f"Expected Category: {invoice['expected_category']}")
        
        # Use policy service for categorization
        category, amount = policy_service.validate_expense_category(invoice['text'])
        print(f"Detected Category: {category}")
        print(f"Detected Amount: ₹{amount}")
        
        # Use Groq for detailed analysis
        policy_text = policy_service.get_policy_text()
        analysis_prompt = llm_service._create_analysis_prompt(
            policy_text, invoice['text'], f"invoice_{i}.pdf"
        )
        
        try:
            groq_response = llm_service._call_groq(analysis_prompt, stream=False)
            print(f"Groq Analysis: {groq_response[:200]}...")
        except Exception as e:
            print(f"❌ Groq Analysis Error: {e}")
    
    # Test chat query functionality
    print("\n5. 💬 Chat Query with Groq")
    print("-" * 30)
    
    chat_query = "What are the spending limits for food and beverage expenses?"
    
    # Simulate context documents
    context_docs = [
        {
            "invoice_id": "sample_001.pdf",
            "employee_name": "John Doe",
            "analysis_result": {
                "status": "Fully Reimbursed",
                "reason": "Amount within policy limit",
                "policy_reference": "5.1 Food and Beverages"
            },
            "content": "Restaurant bill for business lunch"
        }
    ]
    
    try:
        chat_prompt = llm_service._create_chat_prompt(chat_query, context_docs)
        chat_response = llm_service._call_groq(chat_prompt, stream=False)
        print(f"Query: {chat_query}")
        print(f"Response: {chat_response[:200]}...")
    except Exception as e:
        print(f"❌ Chat Query Error: {e}")
    
    print("\n6. 🎯 Performance Comparison")
    print("-" * 30)
    
    # Test response time
    test_prompts = [
        "Brief response test",
        "Medium length response test with more details about invoice processing",
        "Long response test with comprehensive explanation of reimbursement policies and their application in real-world scenarios"
    ]
    
    for prompt in test_prompts:
        start_time = time.time()
        try:
            response = llm_service._call_groq(prompt, stream=False)
            end_time = time.time()
            response_time = end_time - start_time
            print(f"✅ '{prompt[:30]}...': {response_time:.2f}s")
        except Exception as e:
            print(f"❌ Error: {e}")

def show_groq_parameters():
    """Show the current Groq parameters"""
    print("\n🔧 Current Groq Parameters")
    print("-" * 30)
    print(f"Model: {llm_service.model}")
    print("Parameters:")
    print("  - temperature: 0.6")
    print("  - max_tokens: 4096")
    print("  - top_p: 0.95")
    print("  - stream: True/False (configurable)")
    print("  - stop: None")

def main():
    """Main function"""
    print("🎯 Groq Integration Example")
    print("=" * 60)
    
    # Show parameters
    show_groq_parameters()
    
    # Run demonstration
    demonstrate_groq_integration()
    
    print("\n🎉 Groq Integration Example Completed!")
    print("\n💡 Next Steps:")
    print("   1. Start the FastAPI server: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("   2. Start Streamlit UI: streamlit run app/streamlit_app.py")
    print("   3. Test with real invoice data")
    print("   4. Use the streaming chat feature in the UI")

if __name__ == "__main__":
    main() 