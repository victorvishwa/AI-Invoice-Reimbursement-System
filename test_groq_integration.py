#!/usr/bin/env python3
"""
Test script for Groq integration with the new model and parameters
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_service import llm_service
from app.config import settings

def test_groq_initialization():
    """Test Groq client initialization"""
    print("🔧 Testing Groq Client Initialization...")
    
    try:
        # Check if Groq API key is set
        if not settings.groq_api_key:
            print("❌ GROQ_API_KEY not set in environment")
            print("💡 Please set your Groq API key in the .env file")
            return False
        
        # Test client initialization
        print(f"✅ Provider: {llm_service.provider}")
        print(f"✅ Model: {llm_service.model}")
        print(f"✅ Client initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")
        return False

def test_groq_simple_query():
    """Test a simple query with Groq"""
    print("\n🧪 Testing Simple Groq Query...")
    
    try:
        # Simple test prompt
        test_prompt = "Hello! Please respond with a brief greeting and tell me what you can help with."
        
        print("📤 Sending query to Groq...")
        response = llm_service._call_groq(test_prompt, stream=False)
        
        print("📥 Response received:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to get response from Groq: {e}")
        return False

def test_groq_streaming():
    """Test streaming response with Groq"""
    print("\n🌊 Testing Groq Streaming Response...")
    
    try:
        # Test prompt for streaming
        test_prompt = "Please explain the benefits of using AI for invoice analysis in a detailed way."
        
        print("📤 Sending streaming query to Groq...")
        print("📥 Streaming response:")
        print("-" * 50)
        
        response = llm_service._call_groq(test_prompt, stream=True)
        print(response)
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to get streaming response from Groq: {e}")
        return False

def test_invoice_analysis_prompt():
    """Test invoice analysis prompt with Groq"""
    print("\n📊 Testing Invoice Analysis with Groq...")
    
    try:
        # Sample policy and invoice text
        policy_text = """
        IAI Solution Employee Reimbursement Policy
        Food & Beverages: ₹200 per meal
        Travel Expenses: ₹2,000 per trip
        Daily Cab: ₹150 per day
        Accommodation: ₹50 per night
        """
        
        invoice_text = """
        Restaurant Bill
        Business lunch meeting
        Amount: ₹180
        Date: 2024-01-15
        """
        
        # Create analysis prompt
        prompt = llm_service._create_analysis_prompt(policy_text, invoice_text, "test_invoice.pdf")
        
        print("📤 Sending invoice analysis query to Groq...")
        response = llm_service._call_groq(prompt, stream=False)
        
        print("📥 Analysis response:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to analyze invoice with Groq: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Groq Integration Test")
    print("=" * 50)
    
    # Test 1: Initialization
    if not test_groq_initialization():
        return
    
    # Test 2: Simple query
    if not test_groq_simple_query():
        return
    
    # Test 3: Streaming
    if not test_groq_streaming():
        return
    
    # Test 4: Invoice analysis
    if not test_invoice_analysis_prompt():
        return
    
    print("\n🎉 All Groq integration tests passed!")
    print("\n💡 Your Groq integration is working correctly!")
    print("   You can now use the system with the new 'deepseek-r1-distill-llama-70b' model.")

if __name__ == "__main__":
    main() 