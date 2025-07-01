#!/usr/bin/env python3
"""
Test script to verify database storage and RAG functionality
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

async def test_database_connection():
    """Test database connection"""
    print("🔌 Testing Database Connection...")
    
    try:
        await db_manager.connect()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure MongoDB is running and MONGODB_URI is set correctly")
        return False

async def test_database_storage():
    """Test storing invoice data in database"""
    print("\n💾 Testing Database Storage...")
    
    try:
        # Create sample invoice data
        sample_invoice_text = """
        Restaurant Bill
        Business lunch meeting with client
        Amount: ₹180
        Date: 2024-01-15
        """
        
        # Analyze with policy service
        analysis_result = policy_service.analyze_invoice_with_policy(
            sample_invoice_text, "test_invoice_001.pdf"
        )
        
        # Create InvoiceAnalysis object
        invoice_analysis = InvoiceAnalysis(
            invoice_id="test_invoice_001.pdf",
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
            sample_invoice_text, analysis_result
        )
        
        # Create document for storage
        invoice_doc = InvoiceDocument(
            invoice_id="test_invoice_001.pdf",
            employee_name="John Doe",
            content=sample_invoice_text,
            analysis_result=invoice_analysis,
            embedding=embedding,
            created_at=datetime.utcnow(),
            metadata={
                "policy_type": "integrated",
                "policy_filename": "IAI_Solution_Policy",
                "invoices_filename": "test_batch.zip",
                "processing_timestamp": datetime.utcnow().isoformat(),
                "category": analysis_result.get("category", "unknown"),
                "policy_rule": analysis_result.get("policy_rule", "unknown")
            }
        )
        
        # Store in database
        doc_id = await db_manager.insert_invoice(invoice_doc.dict())
        print(f"✅ Invoice stored with ID: {doc_id}")
        
        # Verify storage
        stored_doc = await db_manager.get_invoice_by_id("test_invoice_001.pdf")
        if stored_doc:
            print("✅ Invoice retrieved from database")
            print(f"   Status: {stored_doc.get('analysis_result', {}).get('status')}")
            print(f"   Category: {stored_doc.get('metadata', {}).get('category')}")
        else:
            print("❌ Failed to retrieve stored invoice")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database storage test failed: {e}")
        return False

async def test_vector_search():
    """Test vector search functionality"""
    print("\n🔍 Testing Vector Search...")
    
    try:
        # Test query
        test_query = "What are the food and beverage expenses?"
        
        # Generate query embedding
        query_embedding = embedding_service.generate_embedding(test_query)
        
        # Perform vector search
        search_results = await db_manager.vector_search(
            query_embedding=query_embedding,
            limit=5
        )
        
        print(f"✅ Vector search returned {len(search_results)} results")
        
        if search_results:
            print("📋 Search Results:")
            for i, result in enumerate(search_results, 1):
                print(f"  {i}. Invoice: {result.get('invoice_id')}")
                print(f"     Employee: {result.get('employee_name')}")
                print(f"     Status: {result.get('analysis_result', {}).get('status')}")
                print(f"     Score: {result.get('score', 0):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector search test failed: {e}")
        return False

async def test_rag_chat_query():
    """Test RAG chat query functionality"""
    print("\n💬 Testing RAG Chat Query...")
    
    try:
        # Test chat query
        test_query = "What was the status of John Doe's invoice?"
        
        # Process chat query
        response, sources, confidence = await analysis_service.process_chat_query(test_query)
        
        print(f"✅ Chat query processed successfully")
        print(f"📝 Response: {response[:100]}...")
        print(f"🎯 Confidence: {confidence:.3f}")
        print(f"📚 Sources: {len(sources)} found")
        
        for i, source in enumerate(sources, 1):
            print(f"  {i}. Invoice: {source.get('invoice_id')}")
            print(f"     Employee: {source.get('employee')}")
            print(f"     Similarity: {source.get('similarity_score', 0):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG chat query test failed: {e}")
        return False

async def test_batch_storage():
    """Test batch storage functionality"""
    print("\n📦 Testing Batch Storage...")
    
    try:
        # Create multiple sample invoices
        sample_invoices = [
            {
                "text": "Restaurant Bill\nBusiness lunch\nAmount: ₹150\nDate: 2024-01-15",
                "employee": "Alice Smith",
                "filename": "alice_lunch.pdf"
            },
            {
                "text": "Taxi Fare\nClient meeting\nTotal: ₹300\nDate: 2024-01-16", 
                "employee": "Bob Johnson",
                "filename": "bob_taxi.pdf"
            },
            {
                "text": "Hotel Stay\nBusiness trip\nRoom: ₹45\nDate: 2024-01-17",
                "employee": "Carol Davis", 
                "filename": "carol_hotel.pdf"
            }
        ]
        
        invoice_documents = []
        
        for invoice_data in sample_invoices:
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
            
            # Create document
            invoice_doc = InvoiceDocument(
                invoice_id=invoice_data["filename"],
                employee_name=invoice_data["employee"],
                content=invoice_data["text"],
                analysis_result=invoice_analysis,
                embedding=embedding,
                created_at=datetime.utcnow(),
                metadata={
                    "policy_type": "integrated",
                    "category": analysis_result.get("category", "unknown"),
                    "policy_rule": analysis_result.get("policy_rule", "unknown")
                }
            )
            
            invoice_documents.append(invoice_doc.dict())
        
        # Store batch
        doc_ids = await db_manager.insert_invoices_batch(invoice_documents)
        print(f"✅ Batch stored {len(doc_ids)} invoices")
        
        # Verify batch retrieval
        for employee in ["Alice Smith", "Bob Johnson", "Carol Davis"]:
            invoices = await db_manager.get_invoices_by_employee(employee)
            print(f"   {employee}: {len(invoices)} invoices found")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch storage test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Database Storage and RAG Test")
    print("=" * 50)
    
    # Test 1: Database connection
    if not await test_database_connection():
        return
    
    # Test 2: Single invoice storage
    if not await test_database_storage():
        return
    
    # Test 3: Vector search
    if not await test_vector_search():
        return
    
    # Test 4: RAG chat query
    if not await test_rag_chat_query():
        return
    
    # Test 5: Batch storage
    if not await test_batch_storage():
        return
    
    print("\n🎉 All database storage and RAG tests passed!")
    print("\n💡 Your system is correctly storing analysis results in MongoDB")
    print("   and the RAG chatbot is working properly!")
    
    # Cleanup
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 