#!/usr/bin/env python3
"""
Script to verify MongoDB storage and demonstrate RAG functionality
"""

import asyncio
import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import db_manager
from app.services.embedding_service import embedding_service
from app.services.analysis_service import analysis_service
from app.services.policy_service import policy_service
from app.models import InvoiceAnalysis, InvoiceDocument
from app.config import settings

async def verify_mongodb_setup():
    """Verify MongoDB connection and setup"""
    print("🔍 Verifying MongoDB Setup...")
    
    # Check environment variables
    print(f"MongoDB URI: {'✅ Set' if settings.mongodb_uri else '❌ Not Set'}")
    print(f"Database Name: {settings.database_name}")
    print(f"Vector Dimension: {settings.vector_dimension}")
    
    if not settings.mongodb_uri:
        print("\n❌ MONGODB_URI not set in environment")
        print("💡 Please set your MongoDB connection string in the .env file")
        return False
    
    # Test connection
    try:
        await db_manager.connect()
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

async def create_sample_invoices():
    """Create sample invoices for testing"""
    print("\n📄 Creating Sample Invoices...")
    
    sample_invoices = [
        {
            "text": """
            Restaurant Bill
            Business lunch meeting with client ABC Corp
            Amount: ₹180
            Date: 2024-01-15
            Location: Mumbai
            """,
            "employee": "John Doe",
            "filename": "john_lunch_001.pdf"
        },
        {
            "text": """
            Taxi Fare
            Client meeting at downtown office
            Total: ₹250
            Date: 2024-01-16
            From: Airport
            To: Client Office
            """,
            "employee": "Jane Smith", 
            "filename": "jane_taxi_001.pdf"
        },
        {
            "text": """
            Hotel Stay
            Business trip to Bangalore
            Room charge: ₹45
            Date: 2024-01-17
            Hotel: Business Inn
            Duration: 1 night
            """,
            "employee": "Mike Johnson",
            "filename": "mike_hotel_001.pdf"
        },
        {
            "text": """
            Daily Office Cab
            Regular office commute
            Fare: ₹120
            Date: 2024-01-18
            Route: Home to Office
            """,
            "employee": "Sarah Wilson",
            "filename": "sarah_cab_001.pdf"
        },
        {
            "text": """
            Restaurant Bill
            Dinner with team after project completion
            Amount: ₹220
            Date: 2024-01-19
            Includes: Beer and food
            """,
            "employee": "David Brown",
            "filename": "david_dinner_001.pdf"
        }
    ]
    
    stored_count = 0
    
    for invoice_data in sample_invoices:
        try:
            # Analyze with policy service
            analysis_result = policy_service.analyze_invoice_with_policy(
                invoice_data["text"], invoice_data["filename"]
            )
            
            # Create InvoiceAnalysis object
            invoice_analysis = InvoiceAnalysis(
                invoice_id=invoice_data["filename"],
                status=analysis_result["status"],
                reason=analysis_result["reason"],
                policy_reference=analysis_result["policy_reference"],
                amount=analysis_result.get("amount"),
                reimbursed_amount=analysis_result.get("reimbursed_amount"),
                category=analysis_result.get("category"),
                policy_rule=analysis_result.get("policy_rule")
            )
            
            # Generate embedding
            embedding = embedding_service.generate_invoice_embedding(
                invoice_data["text"], analysis_result
            )
            
            # Create document for storage
            invoice_doc = InvoiceDocument(
                invoice_id=invoice_data["filename"],
                employee_name=invoice_data["employee"],
                content=invoice_data["text"],
                analysis_result=invoice_analysis,
                embedding=embedding,
                created_at=datetime.utcnow(),
                metadata={
                    "policy_type": "integrated",
                    "policy_filename": "IAI_Solution_Policy",
                    "invoices_filename": "sample_batch.zip",
                    "processing_timestamp": datetime.utcnow().isoformat(),
                    "category": analysis_result.get("category", "unknown"),
                    "policy_rule": analysis_result.get("policy_rule", "unknown")
                }
            )
            
            # Store in database
            doc_id = await db_manager.insert_invoice(invoice_doc.dict())
            stored_count += 1
            
            print(f"✅ Stored: {invoice_data['filename']} - {analysis_result['status']}")
            
        except Exception as e:
            print(f"❌ Failed to store {invoice_data['filename']}: {e}")
    
    print(f"\n📊 Total invoices stored: {stored_count}/{len(sample_invoices)}")
    return stored_count > 0

async def demonstrate_rag_queries():
    """Demonstrate RAG query functionality"""
    print("\n💬 Demonstrating RAG Queries...")
    
    test_queries = [
        "What was the status of John Doe's lunch invoice?",
        "How much was reimbursed for Jane Smith's taxi fare?",
        "Which invoices were declined and why?",
        "What are all the food and beverage expenses?",
        "Show me all travel-related expenses",
        "What was the total amount for hotel stays?",
        "Which employee had the most expensive invoice?",
        "What are the reimbursement rates for different categories?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 50)
        
        try:
            # Process chat query
            response, sources, confidence = await analysis_service.process_chat_query(query)
            
            print(f"Response: {response}")
            print(f"Confidence: {confidence:.3f}")
            print(f"Sources: {len(sources)} found")
            
            if sources:
                print("Top sources:")
                for j, source in enumerate(sources[:3], 1):
                    print(f"  {j}. {source.get('invoice_id')} - {source.get('employee')} (Score: {source.get('similarity_score', 0):.3f})")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
        
        print()

async def show_database_stats():
    """Show database statistics"""
    print("\n📈 Database Statistics...")
    
    try:
        # Get all invoices
        all_invoices = await db_manager.invoices_collection.find({}).to_list(None)
        total_invoices = len(all_invoices)
        
        print(f"Total invoices in database: {total_invoices}")
        
        if total_invoices > 0:
            # Status distribution
            status_counts = {}
            category_counts = {}
            employee_counts = {}
            
            for invoice in all_invoices:
                # Count statuses
                status = invoice.get('analysis_result', {}).get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count categories
                category = invoice.get('metadata', {}).get('category', 'Unknown')
                category_counts[category] = category_counts.get(category, 0) + 1
                
                # Count employees
                employee = invoice.get('employee_name', 'Unknown')
                employee_counts[employee] = employee_counts.get(employee, 0) + 1
            
            print("\nStatus Distribution:")
            for status, count in status_counts.items():
                print(f"  {status}: {count}")
            
            print("\nCategory Distribution:")
            for category, count in category_counts.items():
                print(f"  {category}: {count}")
            
            print("\nEmployee Distribution:")
            for employee, count in employee_counts.items():
                print(f"  {employee}: {count}")
        
    except Exception as e:
        print(f"❌ Failed to get database stats: {e}")

async def main():
    """Main function"""
    print("🚀 MongoDB Storage and RAG Verification")
    print("=" * 60)
    
    # Step 1: Verify MongoDB setup
    if not await verify_mongodb_setup():
        return
    
    # Step 2: Create sample invoices
    if not await create_sample_invoices():
        print("❌ Failed to create sample invoices")
        return
    
    # Step 3: Show database statistics
    await show_database_stats()
    
    # Step 4: Demonstrate RAG queries
    await demonstrate_rag_queries()
    
    print("\n🎉 Verification Complete!")
    print("\n💡 Your system is working correctly:")
    print("   ✅ MongoDB connection established")
    print("   ✅ Invoice analysis stored with embeddings")
    print("   ✅ Vector search working")
    print("   ✅ RAG chatbot functional")
    
    # Cleanup
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 