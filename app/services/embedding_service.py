import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np
from ..config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.model = None
        self.model_name = settings.embedding_model
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            if not text.strip():
                logger.warning("Empty text provided for embedding")
                return [0.0] * self.model.get_sentence_embedding_dimension()
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_tensor=False)
            
            # Convert to list of floats
            embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            
            logger.debug(f"Generated embedding with dimension: {len(embedding_list)}")
            return embedding_list
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.model.get_sentence_embedding_dimension()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            if not texts:
                return []
            
            # Filter out empty texts
            valid_texts = [text for text in texts if text.strip()]
            if not valid_texts:
                logger.warning("No valid texts provided for batch embedding")
                return []
            
            # Generate embeddings in batch
            embeddings = self.model.encode(valid_texts, convert_to_tensor=False)
            
            # Convert to list of lists
            if len(embeddings.shape) == 1:
                embeddings = embeddings.reshape(1, -1)
            
            embedding_lists = embeddings.tolist()
            
            logger.info(f"Generated {len(embedding_lists)} embeddings in batch")
            return embedding_lists
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            # Return empty list as fallback
            return []
    
    def generate_invoice_embedding(self, invoice_content: str, analysis_result: Dict[str, Any]) -> List[float]:
        """Generate embedding for invoice with analysis result"""
        try:
            # Combine invoice content with analysis for better search
            combined_text = f"""
            Invoice Content: {invoice_content}
            Analysis Status: {analysis_result.get('status', '')}
            Reason: {analysis_result.get('reason', '')}
            Policy Reference: {analysis_result.get('policy_reference', '')}
            """
            
            return self.generate_embedding(combined_text)
            
        except Exception as e:
            logger.error(f"Failed to generate invoice embedding: {e}")
            return self.generate_embedding(invoice_content)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], 
                         candidate_embeddings: List[List[float]], 
                         threshold: float = None) -> List[tuple]:
        """Find most similar embeddings above threshold"""
        try:
            if threshold is None:
                threshold = settings.similarity_threshold
            
            similarities = []
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.calculate_similarity(query_embedding, candidate)
                if similarity >= threshold:
                    similarities.append((i, similarity))
            
            # Sort by similarity score (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"Found {len(similarities)} similar embeddings above threshold {threshold}")
            return similarities
            
        except Exception as e:
            logger.error(f"Failed to find similar embeddings: {e}")
            return []
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding model"""
        try:
            return self.model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to get embedding dimension: {e}")
            return 384  # Default for all-MiniLM-L6-v2


# Global embedding service instance
embedding_service = EmbeddingService() 