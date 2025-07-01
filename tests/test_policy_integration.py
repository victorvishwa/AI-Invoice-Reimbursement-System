import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.policy_service import policy_service


def test_policy_service_initialization():
    """Test that the policy service initializes correctly"""
    assert policy_service.company_name == "IAI Solution"
    assert policy_service.policy_version == "1.0"
    assert policy_service.policy_title == "Employee Reimbursement Policy"
    assert len(policy_service.policy_rules) == 5  # 5 categories (added cab)


def test_policy_text_generation():
    """Test that policy text is generated correctly"""
    policy_text = policy_service.get_policy_text()
    assert "IAI Solution" in policy_text
    assert "Employee Reimbursement Policy" in policy_text
    assert "₹200" in policy_text  # Food allowance
    assert "₹2,000" in policy_text  # Travel allowance
    assert "₹150" in policy_text  # Daily cab allowance
    assert "₹50" in policy_text  # Accommodation allowance


def test_expense_category_detection():
    """Test expense category detection from invoice text"""
    # Test food and beverages
    food_invoice = "Restaurant bill for lunch meeting - Amount: ₹150"
    category, amount = policy_service.validate_expense_category(food_invoice)
    assert category == "food_beverages"
    assert amount == 150.0
    
    # Test travel expenses
    travel_invoice = "Taxi fare for client meeting - Total: ₹500"
    category, amount = policy_service.validate_expense_category(travel_invoice)
    assert category == "travel_expenses"
    assert amount == 500.0
    
    # Test daily cab
    cab_invoice = "Daily office cab fare - Amount: ₹120"
    category, amount = policy_service.validate_expense_category(cab_invoice)
    assert category == "daily_cab"
    assert amount == 120.0
    
    # Test accommodation
    hotel_invoice = "Hotel stay for business trip - Room charge: ₹45"
    category, amount = policy_service.validate_expense_category(hotel_invoice)
    assert category == "accommodation"
    assert amount == 45.0


def test_policy_validation():
    """Test policy validation against different scenarios"""
    # Test food within limit
    food_invoice = "Lunch at restaurant - Amount: ₹180"
    category, amount = policy_service.validate_expense_category(food_invoice)
    result = policy_service.validate_against_policy(category, amount, food_invoice)
    assert result["status"] == "Fully Reimbursed"
    assert result["reimbursed_amount"] == 180.0
    
    # Test food over limit
    food_invoice_over = "Dinner at expensive restaurant - Amount: ₹250"
    category, amount = policy_service.validate_expense_category(food_invoice_over)
    result = policy_service.validate_against_policy(category, amount, food_invoice_over)
    assert result["status"] == "Partially Reimbursed"
    assert result["reimbursed_amount"] == 200.0  # Max limit
    
    # Test alcohol restriction
    alcohol_invoice = "Beer and food at pub - Amount: ₹150"
    category, amount = policy_service.validate_expense_category(alcohol_invoice)
    result = policy_service.validate_against_policy(category, amount, alcohol_invoice)
    assert result["status"] == "Declined"
    assert result["reimbursed_amount"] == 0.0


def test_complete_invoice_analysis():
    """Test complete invoice analysis workflow"""
    # Test valid food invoice
    food_invoice = "Business lunch meeting - Amount: ₹180"
    result = policy_service.analyze_invoice_with_policy(food_invoice, "test_invoice_1.pdf")
    assert result["status"] == "Fully Reimbursed"
    assert result["category"] == "food_beverages"
    assert result["amount"] == 180.0
    assert result["reimbursed_amount"] == 180.0
    assert "5.1 Food and Beverages" in result["policy_reference"]
    
    # Test travel expense over limit
    travel_invoice = "Long distance taxi for client visit - Amount: ₹2500"
    result = policy_service.analyze_invoice_with_policy(travel_invoice, "test_invoice_2.pdf")
    assert result["status"] == "Partially Reimbursed"
    assert result["category"] == "travel_expenses"
    assert result["amount"] == 2500.0
    assert result["reimbursed_amount"] == 2000.0  # Max limit
    assert "5.2 Travel Expenses" in result["policy_reference"]


def test_policy_summary():
    """Test policy summary generation"""
    summary = policy_service.get_policy_summary()
    assert summary["company_name"] == "IAI Solution"
    assert summary["policy_title"] == "Employee Reimbursement Policy"
    assert summary["version"] == "1.0"
    assert "categories" in summary
    
    categories = summary["categories"]
    assert "food_beverages" in categories
    assert "travel_expenses" in categories
    assert "cab" in categories
    assert "daily_cab" in categories
    assert "accommodation" in categories
    
    # Check food category details
    food_category = categories["food_beverages"]
    assert food_category["name"] == "Food and Beverages"
    assert food_category["max_amount"] == 200.0
    assert "5.1 Food and Beverages" in food_category["policy_section"]


if __name__ == "__main__":
    # Run tests
    test_policy_service_initialization()
    test_policy_text_generation()
    test_expense_category_detection()
    test_policy_validation()
    test_complete_invoice_analysis()
    test_policy_summary()
    print("✅ All policy integration tests passed!") 