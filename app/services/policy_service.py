import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PolicyRule:
    """Represents a policy rule with validation logic"""
    category: str
    description: str
    max_amount: float
    conditions: List[str]
    restrictions: List[str]
    policy_section: str


class PolicyService:
    """Service to handle IAI Solution Employee Reimbursement Policy"""
    
    def __init__(self):
        self.company_name = "IAI Solution"
        self.policy_version = "1.0"
        self.policy_title = "Employee Reimbursement Policy"
        self.submission_deadline_days = 30
        self.approval_deadline_days = 10
        
        # Initialize policy rules
        self.policy_rules = self._initialize_policy_rules()
        
        # Policy text for LLM analysis
        self.policy_text = self._get_policy_text()
    
    def _initialize_policy_rules(self) -> Dict[str, PolicyRule]:
        """Initialize the policy rules based on IAI Solution policy"""
        return {
            "food_beverages": PolicyRule(
                category="Food and Beverages",
                description="Meals during work travel or business meetings",
                max_amount=200.0,  # ₹200 per meal
                conditions=[
                    "Traveling for work",
                    "Attending business meetings"
                ],
                restrictions=[
                    "Alcoholic beverages not reimbursable"
                ],
                policy_section="5.1 Food and Beverages"
            ),
            
            "travel_expenses": PolicyRule(
                category="Travel Expenses",
                description="Work-related travel expenses",
                max_amount=2000.0,  # ₹2,000 per trip
                conditions=[
                    "Work-related travel only"
                ],
                restrictions=[
                    "Personal travel expenses not reimbursed"
                ],
                policy_section="5.2 Travel Expenses"
            ),
            
            "cab": PolicyRule(
                category="Cab Expenses",
                description="Regular cab/taxi expenses for work",
                max_amount=200.0,  # ₹200 per trip
                conditions=[
                    "Work-related cab rides"
                ],
                restrictions=[
                    "Personal cab rides not reimbursed"
                ],
                policy_section="5.2 Travel Expenses"
            ),
            
            "daily_cab": PolicyRule(
                category="Daily Office Cab",
                description="Daily office cab allowance",
                max_amount=150.0,  # ₹150 per day
                conditions=[
                    "Daily office commute"
                ],
                restrictions=[
                    "Only for office commute"
                ],
                policy_section="5.2 Travel Expenses"
            ),
            
            "accommodation": PolicyRule(
                category="Accommodation",
                description="Hotel stays for overnight business travel",
                max_amount=50.0,  # ₹50 per night
                conditions=[
                    "Overnight business travel"
                ],
                restrictions=[
                    "Use company-approved hotels when available",
                    "Excludes taxes and fees"
                ],
                policy_section="5.3 Accommodation"
            )
        }
    
    def _get_policy_text(self) -> str:
        """Get the complete policy text for LLM analysis"""
        return f"""
Company Name: {self.company_name}
Policy Title: {self.policy_title}
Version: {self.policy_version}

1. Purpose
The purpose of this policy is to outline the guidelines and procedures for the reimbursement of expenses incurred by employees while performing work-related duties. This policy ensures transparency and consistency in the reimbursement process.

2. Scope
This policy applies to all employees of {self.company_name} who incur expenses in the course of their work duties.

3. Reimbursement Categories
The following categories of expenses are eligible for reimbursement under this policy:
● Food and Beverages
● Travel Expenses
● Cab Expenses
● Daily Office Cab
● Accommodations

4. General Guidelines
● All reimbursements must be supported by original receipts and submitted within {self.submission_deadline_days} days of the expense incurred.
● Employees must complete the reimbursement request form and submit it along with the required documentation to the HR department.

5. Specific Expense Guidelines

5.1 Food and Beverages
● Eligibility: Reimbursement for meals is allowed when traveling for work or attending business meetings.
● Limits: We have set food allowances for food reimbursements of ₹200 per meal.
● Restrictions: Alcoholic beverages are not reimbursable.

5.2 Travel Expenses
● Eligibility: Travel expenses are reimbursable for work-related travel only.
● Limits: We have set allowances for travel reimbursements of ₹2,000 per trip, depending on the location and the employee's level.
● Restrictions: Any travel-related expenses incurred for personal reasons will not be reimbursed.

5.2.1 Cab Expenses
● Eligibility: Regular cab/taxi expenses for work-related purposes.
● Limits: ₹200 per cab ride.
● Restrictions: Personal cab rides are not reimbursed.

5.2.2 Daily Office Cab
● Eligibility: Daily office commute cab allowance.
● Limits: ₹150 per day.
● Restrictions: Only for office commute.

5.3 Accommodation
● Eligibility: Reimbursement for hotel stays is allowed for overnight business travel.
● Limits: Up to ₹50 per night, excluding taxes and fees.
● Restrictions: Employees must use company-approved hotels when available.

6. Submission Process
1. Complete the reimbursement request form.
2. Attach all relevant receipts.
3. Submit to the HR department for approval.

7. Review and Approval
HR will review submissions for compliance with this policy and will either approve or deny the request within {self.approval_deadline_days} business days.

8. Policy Amendments
This policy may be amended at any time with prior notice to employees.
"""
    
    def get_policy_text(self) -> str:
        """Get the policy text for analysis"""
        return self.policy_text
    
    def validate_expense_category(self, invoice_text: str) -> Tuple[str, float]:
        """Determine expense category and extract amount from invoice text"""
        invoice_lower = invoice_text.lower()
        
        # Extract amount using regex
        amount_patterns = [
            r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'rupees?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'amount[:\s]*₹?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'total[:\s]*₹?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        amount = 0.0
        for pattern in amount_patterns:
            matches = re.findall(pattern, invoice_lower)
            if matches:
                # Convert to float, removing commas
                amount_str = matches[0].replace(',', '')
                try:
                    amount = float(amount_str)
                    break
                except ValueError:
                    continue
        
        # Determine category based on keywords
        if any(word in invoice_lower for word in ['food', 'meal', 'restaurant', 'cafe', 'dining', 'lunch', 'dinner', 'breakfast']):
            return "food_beverages", amount
        elif any(word in invoice_lower for word in ['hotel', 'accommodation', 'lodging', 'stay', 'room']):
            return "accommodation", amount
        elif any(word in invoice_lower for word in ['cab', 'taxi', 'uber', 'ola']):
            # Check for daily office cab first
            if any(word in invoice_lower for word in ['daily', 'office', 'commute', 'regular']):
                return "daily_cab", amount
            # Check for business travel context
            elif any(word in invoice_lower for word in ['client', 'meeting', 'business', 'trip', 'visit']):
                return "travel_expenses", amount
            else:
                # Regular cab expenses
                return "cab", amount
        elif any(word in invoice_lower for word in ['transport', 'travel', 'flight', 'train', 'bus']):
            return "travel_expenses", amount
        else:
            # Default to travel expenses if unclear (higher limit ₹2000)
            return "travel_expenses", amount
    
    def validate_against_policy(self, category: str, amount: float, invoice_text: str) -> Dict[str, Any]:
        """Validate expense against specific policy rules"""
        if category not in self.policy_rules:
            return {
                "status": "Declined",
                "reason": f"Unknown expense category: {category}",
                "policy_reference": "Policy does not cover this category",
                "amount": amount,
                "reimbursed_amount": 0.0
            }
        
        rule = self.policy_rules[category]
        invoice_lower = invoice_text.lower()
        
        # Check for restrictions
        if category == "food_beverages" and any(word in invoice_lower for word in ['alcohol', 'beer', 'wine', 'liquor']):
            return {
                "status": "Declined",
                "reason": "Alcoholic beverages are not reimbursable according to policy",
                "policy_reference": rule.policy_section,
                "amount": amount,
                "reimbursed_amount": 0.0
            }
        
        # Check amount limits
        if amount > rule.max_amount:
            return {
                "status": "Partially Reimbursed",
                "reason": f"Amount (₹{amount}) exceeds policy limit of ₹{rule.max_amount} for {rule.category}",
                "policy_reference": rule.policy_section,
                "amount": amount,
                "reimbursed_amount": rule.max_amount
            }
        
        # Check if within limits
        if amount <= rule.max_amount:
            return {
                "status": "Fully Reimbursed",
                "reason": f"Amount (₹{amount}) is within policy limit of ₹{rule.max_amount} for {rule.category}",
                "policy_reference": rule.policy_section,
                "amount": amount,
                "reimbursed_amount": amount
            }
        
        return {
            "status": "Declined",
            "reason": "Unable to determine reimbursement status",
            "policy_reference": rule.policy_section,
            "amount": amount,
            "reimbursed_amount": 0.0
        }
    
    def analyze_invoice_with_policy(self, invoice_text: str, invoice_id: str) -> Dict[str, Any]:
        """Analyze invoice using the integrated policy rules"""
        try:
            # Determine category and extract amount
            category, amount = self.validate_expense_category(invoice_text)
            
            # Validate against policy
            validation_result = self.validate_against_policy(category, amount, invoice_text)
            
            # Add category information
            validation_result["category"] = category
            validation_result["policy_rule"] = self.policy_rules[category].description
            
            logger.info(f"Analyzed invoice {invoice_id}: {validation_result['status']} for {category}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to analyze invoice {invoice_id} with policy: {e}")
            return {
                "status": "Declined",
                "reason": f"Policy analysis failed: {str(e)}",
                "policy_reference": "Error in policy analysis",
                "amount": 0.0,
                "reimbursed_amount": 0.0,
                "category": "unknown"
            }
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Get a summary of the policy rules"""
        summary = {
            "company_name": self.company_name,
            "policy_title": self.policy_title,
            "version": self.policy_version,
            "submission_deadline_days": self.submission_deadline_days,
            "approval_deadline_days": self.approval_deadline_days,
            "categories": {}
        }
        
        for category, rule in self.policy_rules.items():
            summary["categories"][category] = {
                "name": rule.category,
                "max_amount": rule.max_amount,
                "description": rule.description,
                "conditions": rule.conditions,
                "restrictions": rule.restrictions,
                "policy_section": rule.policy_section
            }
        
        return summary


# Global policy service instance
policy_service = PolicyService() 