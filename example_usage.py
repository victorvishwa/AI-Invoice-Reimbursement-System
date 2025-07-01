#!/usr/bin/env python3
"""
Example usage of the Intelligent Invoice Reimbursement System
with integrated IAI Solution Employee Reimbursement Policy
"""

import requests
import json
from datetime import datetime

# API configuration
API_BASE_URL = "http://localhost:8000"

def test_policy_info():
    """Test getting policy information"""
    print("🔍 Getting IAI Solution Policy Information...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/analyze-invoices/policy", timeout=10)
        if response.status_code == 200:
            policy_data = response.json()
            print("✅ Policy Information Retrieved Successfully!")
            
            policy = policy_data.get('policy', {})
            print(f"Company: {policy.get('company_name')}")
            print(f"Policy: {policy.get('policy_title')}")
            print(f"Version: {policy.get('version')}")
            
            print("\n📋 Expense Categories & Limits:")
            categories = policy.get('categories', {})
            for category_key, category_data in categories.items():
                print(f"  • {category_data.get('name')}: ₹{category_data.get('max_amount')} - {category_data.get('description')}")
            
            return True
        else:
            print(f"❌ Failed to get policy info: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting policy info: {e}")
        return False

def test_api_health():
    """Test API health"""
    print("🏥 Checking API Health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy and running!")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("💡 Make sure to start the FastAPI server first:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False

def create_sample_invoice_text(category, amount, description):
    """Create sample invoice text for testing"""
    if category == "food_beverages":
        return f"Restaurant Bill\n{description}\nAmount: ₹{amount}\nDate: {datetime.now().strftime('%Y-%m-%d')}"
    elif category == "travel_expenses":
        return f"Taxi Fare\n{description}\nTotal: ₹{amount}\nDate: {datetime.now().strftime('%Y-%m-%d')}"
    elif category == "daily_cab":
        return f"Daily Office Cab\n{description}\nFare: ₹{amount}\nDate: {datetime.now().strftime('%Y-%m-%d')}"
    elif category == "accommodation":
        return f"Hotel Stay\n{description}\nRoom Charge: ₹{amount}\nDate: {datetime.now().strftime('%Y-%m-%d')}"
    else:
        return f"Expense\n{description}\nAmount: ₹{amount}\nDate: {datetime.now().strftime('%Y-%m-%d')}"

def test_policy_analysis():
    """Test policy analysis with sample data"""
    print("\n🧪 Testing Policy Analysis...")
    
    # Sample test cases
    test_cases = [
        {
            "category": "food_beverages",
            "amount": 180,
            "description": "Business lunch meeting",
            "expected_status": "Fully Reimbursed"
        },
        {
            "category": "food_beverages", 
            "amount": 250,
            "description": "Expensive dinner",
            "expected_status": "Partially Reimbursed"
        },
        {
            "category": "food_beverages",
            "amount": 150,
            "description": "Beer and food at pub",
            "expected_status": "Declined"
        },
        {
            "category": "travel_expenses",
            "amount": 1500,
            "description": "Client meeting taxi",
            "expected_status": "Fully Reimbursed"
        },
        {
            "category": "daily_cab",
            "amount": 120,
            "description": "Daily office commute",
            "expected_status": "Fully Reimbursed"
        },
        {
            "category": "accommodation",
            "amount": 45,
            "description": "Business trip hotel",
            "expected_status": "Fully Reimbursed"
        }
    ]
    
    print("📊 Test Results:")
    print("-" * 80)
    print(f"{'Category':<15} {'Amount':<10} {'Description':<25} {'Expected':<20} {'Status':<20}")
    print("-" * 80)
    
    for i, test_case in enumerate(test_cases):
        invoice_text = create_sample_invoice_text(
            test_case["category"],
            test_case["amount"], 
            test_case["description"]
        )
        
        # Simulate the analysis (in real usage, this would be done via API)
        from app.services.policy_service import policy_service
        
        result = policy_service.analyze_invoice_with_policy(
            invoice_text, 
            f"test_invoice_{i+1}.pdf"
        )
        
        status = result.get("status", "Unknown")
        expected = test_case["expected_status"]
        status_icon = "✅" if status == expected else "❌"
        
        print(f"{test_case['category']:<15} ₹{test_case['amount']:<9} {test_case['description']:<25} {expected:<20} {status_icon} {status:<20}")
    
    print("-" * 80)

def analyze_invoices(invoices_file, employee_name="Batch Analysis", policy_file=None, use_integrated_policy=True):
    """Send invoice analysis request to API"""
    try:
        files = {'invoices': ('invoices.zip', invoices_file, 'application/zip')}
        data = {'employee_name': employee_name}
        
        # Add policy file if provided
        if policy_file and not use_integrated_policy:
            files['policy'] = ('policy.pdf', policy_file, 'application/pdf')
        
        # Add query parameter for policy type
        params = {'use_integrated_policy': use_integrated_policy}
        
        response = requests.post(
            f"{API_BASE_URL}/analyze-invoices/",
            files=files,
            data=data,
            params=params,
            timeout=300
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# Example usage without employee name
def example_usage():
    """Example of how to use the system"""
    print("📝 Example Usage:")
    print("1. Upload ZIP file with invoice PDFs")
    print("2. System analyzes each PDF separately")
    print("3. Results show individual analysis for each invoice")
    print("4. No employee name required - uses 'Batch Analysis' by default")
    
    # Example API call
    print("\n🔧 API Usage:")
    print("POST /analyze-invoices/")
    print("Files: invoices.zip")
    print("Data: employee_name (optional)")
    print("Params: use_integrated_policy=true")

def main():
    """Main function to run all examples"""
    print("🚀 IAI Solution Invoice Reimbursement System - Example Usage")
    print("=" * 70)
    
    # Check API health first
    if not test_api_health():
        return
    
    # Get policy information
    test_policy_info()
    
    # Test policy analysis
    test_policy_analysis()
    
    print("\n🎉 Example completed successfully!")
    print("\n💡 Next Steps:")
    print("   1. Start the Streamlit UI: streamlit run app/streamlit_app.py")
    print("   2. Upload real invoice ZIP files for analysis")
    print("   3. Use the chat interface to query past analyses")
    print("   4. Check the API documentation at: http://localhost:8000/docs")

if __name__ == "__main__":
    main() 