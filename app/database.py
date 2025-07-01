import motor.motor_asyncio
from pymongo import MongoClient
from typing import List, Dict, Any, Optional
import logging
from .config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.invoices_collection = None
        
    async def connect(self):
        """Initialize database connection"""
        try:
            # Async client for FastAPI
            self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_uri)
            self.db = self.client[settings.database_name]
            self.invoices_collection = self.db.invoices
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Ensure vector search index exists
            await self._ensure_vector_index()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _ensure_vector_index(self):
        """Ensure vector search index exists on the invoices collection"""
        try:
            # Check if index already exists
            indexes = await self.invoices_collection.list_indexes().to_list(None)
            index_names = [index['name'] for index in indexes]
            
            if 'vector_index' not in index_names:
                # Create vector search index
                index_definition = {
                    "mappings": {
                        "dynamic": True,
                        "fields": {
                            "embedding": {
                                "dimensions": settings.vector_dimension,
                                "similarity": "cosine",
                                "type": "knnVector"
                            }
                        }
                    }
                }
                
                await self.db.command({
                    "createSearchIndex": "invoices",
                    "definition": index_definition
                })
                logger.info("Created vector search index")
            else:
                logger.info("Vector search index already exists")
                
        except Exception as e:
            logger.warning(f"Could not create vector search index: {e}")
            logger.info("Vector search functionality may not work without proper index")
    
    async def insert_invoice(self, invoice_doc: Dict[str, Any]) -> str:
        """Insert a single invoice document"""
        try:
            result = await self.invoices_collection.insert_one(invoice_doc)
            logger.info(f"Inserted invoice {invoice_doc.get('invoice_id')}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to insert invoice: {e}")
            raise
    
    async def insert_invoices_batch(self, invoice_docs: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple invoice documents"""
        try:
            result = await self.invoices_collection.insert_many(invoice_docs)
            logger.info(f"Inserted {len(result.inserted_ids)} invoices")
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            logger.error(f"Failed to insert invoices batch: {e}")
            raise
    
    async def vector_search(self, query_embedding: List[float], 
                          limit: int = 10, 
                          filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        try:
            # Build search pipeline
            pipeline = [
                {
                    "$search": {
                        "index": "vector_index",
                        "knnBeta": {
                            "vector": query_embedding,
                            "path": "embedding",
                            "k": limit
                        }
                    }
                }
            ]
            
            # Add filters if provided
            if filters:
                pipeline.append({"$match": filters})
            
            # Add projection to include similarity score
            pipeline.append({
                "$addFields": {
                    "score": {"$meta": "searchScore"}
                }
            })
            
            # Execute search
            cursor = self.invoices_collection.aggregate(pipeline)
            results = await cursor.to_list(None)
            
            logger.info(f"Vector search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            # Fallback to regular text search if vector search fails
            return await self.text_search(filters or {})
    
    async def text_search(self, filters: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Fallback text-based search"""
        try:
            cursor = self.invoices_collection.find(filters).limit(limit)
            results = await cursor.to_list(None)
            logger.info(f"Text search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []
    
    async def get_invoice_by_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice by ID"""
        try:
            return await self.invoices_collection.find_one({"invoice_id": invoice_id})
        except Exception as e:
            logger.error(f"Failed to get invoice {invoice_id}: {e}")
            return None
    
    async def get_invoices_by_employee(self, employee_name: str) -> List[Dict[str, Any]]:
        """Get all invoices for a specific employee"""
        try:
            cursor = self.invoices_collection.find({"employee_name": employee_name})
            return await cursor.to_list(None)
        except Exception as e:
            logger.error(f"Failed to get invoices for {employee_name}: {e}")
            return []
    
    async def get_invoices_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all invoices with a specific status"""
        try:
            cursor = self.invoices_collection.find({"analysis_result.status": status})
            return await cursor.to_list(None)
        except Exception as e:
            logger.error(f"Failed to get invoices with status {status}: {e}")
            return []


# Global database manager instance
db_manager = DatabaseManager() 