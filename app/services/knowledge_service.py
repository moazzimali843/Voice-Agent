import os
import re
from typing import List, Dict, Tuple
from pathlib import Path
import PyPDF2
# Fix imports to work from any directory
try:
    from ..models.schemas import KnowledgeChunk
    from ..config import settings
except ImportError:
    from models.schemas import KnowledgeChunk
    from config import settings
import logging

logger = logging.getLogger(__name__)

class KnowledgeService:
    """Service for managing knowledge base operations"""
    
    def __init__(self):
        self.knowledge_cache: Dict[str, List[KnowledgeChunk]] = {}
        self.session_knowledge: Dict[str, List[KnowledgeChunk]] = {}
    
    def load_knowledge_base(self, session_id: str) -> bool:
        """Load knowledge base from PDF files for a specific session"""
        try:
            knowledge_path = Path(settings.KNOWLEDGE_BASE_PATH)
            
            if not knowledge_path.exists():
                logger.error(f"Knowledge base path does not exist: {knowledge_path}")
                return False
            
            pdf_files = list(knowledge_path.glob("*.pdf"))
            
            if not pdf_files:
                logger.warning("No PDF files found in knowledge base directory")
                return False
            
            all_chunks = []
            
            for pdf_file in pdf_files:
                try:
                    chunks = self._extract_text_from_pdf(pdf_file)
                    all_chunks.extend(chunks)
                    logger.info(f"Loaded {len(chunks)} chunks from {pdf_file.name}")
                except Exception as e:
                    logger.error(f"Error processing PDF {pdf_file.name}: {str(e)}")
                    continue
            
            if all_chunks:
                self.session_knowledge[session_id] = all_chunks
                logger.info(f"Successfully loaded {len(all_chunks)} total knowledge chunks for session {session_id}")
                return True
            else:
                logger.error("No content could be extracted from PDF files")
                return False
                
        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
            return False
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> List[KnowledgeChunk]:
        """Extract text from a PDF file and split into chunks"""
        chunks = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    
                    if text.strip():
                        # Split text into paragraphs
                        paragraphs = self._split_into_paragraphs(text)
                        
                        for i, paragraph in enumerate(paragraphs):
                            if len(paragraph.strip()) > 50:  # Filter out very short paragraphs
                                chunk = KnowledgeChunk(
                                    content=paragraph.strip(),
                                    source=f"{pdf_path.name} - Page {page_num + 1} - Para {i + 1}",
                                    relevance_score=0.0
                                )
                                chunks.append(chunk)
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        # Split by double newlines, single newlines, or periods followed by spaces
        paragraphs = re.split(r'\n\s*\n|\n(?=\s*[A-Z])', text)
        
        # Further split long paragraphs
        result = []
        for para in paragraphs:
            para = para.strip()
            if len(para) > 500:  # Split long paragraphs
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk + sentence) < 500:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk.strip():
                            result.append(current_chunk.strip())
                        current_chunk = sentence + " "
                
                if current_chunk.strip():
                    result.append(current_chunk.strip())
            else:
                result.append(para)
        
        return [p for p in result if p.strip()]
    
    def search_knowledge(self, session_id: str, query: str, max_results: int = 5) -> List[KnowledgeChunk]:
        """Search knowledge base for relevant content"""
        if session_id not in self.session_knowledge:
            logger.warning(f"No knowledge base loaded for session {session_id}")
            return []
        
        knowledge_chunks = self.session_knowledge[session_id]
        
        # Simple keyword-based search with scoring
        query_terms = self._extract_keywords(query.lower())
        
        scored_chunks = []
        for chunk in knowledge_chunks:
            score = self._calculate_relevance_score(chunk.content.lower(), query_terms)
            if score > 0:
                chunk.relevance_score = score
                scored_chunks.append(chunk)
        
        # Sort by relevance score and return top results
        scored_chunks.sort(key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"Found {len(scored_chunks)} relevant chunks for query: {query}")
        return scored_chunks[:max_results]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from query text"""
        # Remove common stop words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'what', 'how', 'when', 'where', 'why',
            'hey', 'tell', 'me', 'about'
        }
        
        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b[a-zA-Z0-9]+\b', text)
        keywords = [word for word in words if word.lower() not in stop_words and len(word) > 2]
        
        # Also extract important phrases
        important_phrases = [
            'car accident', 'car accidents', 'auto accident', 'vehicle accident', 
            'car crash', 'auto crash', 'vehicle crash', 'traffic accident',
            'motor vehicle', 'collision', 'crash', 'accident'
        ]
        
        # Add matching phrases to keywords
        text_lower = text.lower()
        for phrase in important_phrases:
            if phrase in text_lower:
                keywords.extend(phrase.split())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword.lower() not in seen:
                seen.add(keyword.lower())
                unique_keywords.append(keyword)
        
        return unique_keywords
    
    def _calculate_relevance_score(self, content: str, query_terms: List[str]) -> float:
        """Calculate relevance score for a content chunk"""
        if not query_terms:
            return 0.0
        
        content_lower = content.lower()
        content_words = re.findall(r'\b[a-zA-Z0-9]+\b', content_lower)
        content_word_count = len(content_words)
        
        if content_word_count == 0:
            return 0.0
        
        # Count exact matches (case-insensitive)
        exact_matches = sum(1 for term in query_terms if term.lower() in content_lower)
        
        # Count partial matches (terms contained in content words)
        partial_matches = 0
        for term in query_terms:
            term_lower = term.lower()
            partial_matches += sum(1 for word in content_words if term_lower in word or word in term_lower)
        
        # Bonus for important keywords
        important_keywords = ['accident', 'crash', 'vehicle', 'car', 'auto', 'collision', 'injury', 'case', 'criteria']
        bonus_score = 0
        for keyword in important_keywords:
            if keyword in content_lower:
                bonus_score += 1.0
        
        # Calculate score with weights
        exact_score = exact_matches * 3.0  # Increased weight for exact matches
        partial_score = partial_matches * 1.0  # Increased weight for partial matches
        
        # Don't penalize longer content as much
        total_score = (exact_score + partial_score + bonus_score) / (content_word_count / 200)
        
        return total_score
    
    def clear_session_knowledge(self, session_id: str) -> bool:
        """Clear knowledge base for a specific session"""
        if session_id in self.session_knowledge:
            del self.session_knowledge[session_id]
            logger.info(f"Cleared knowledge base for session {session_id}")
            return True
        return False
    
    def get_session_status(self, session_id: str) -> Dict:
        """Get knowledge base status for a session"""
        return {
            "session_id": session_id,
            "knowledge_loaded": session_id in self.session_knowledge,
            "chunk_count": len(self.session_knowledge.get(session_id, [])),
            "sources": list(set(chunk.source.split(" - ")[0] for chunk in self.session_knowledge.get(session_id, [])))
        }

# Global knowledge service instance
knowledge_service = KnowledgeService() 