"""Document loading and chunking for Kerala Ayurveda content"""
import os
from typing import List
import pandas as pd
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from src.config import config


class DocumentLoader:
    """Load and chunk documents from Kerala Ayurveda content pack"""
    
    def __init__(self, content_path: str = None):
        """Initialize document loader
        
        Args:
            content_path: Path to content pack directory
        """
        self.content_path = content_path or config.CONTENT_PACK_PATH
        self.documents = []
    
    def load_all_documents(self) -> List[Document]:
        """Load all documents from content pack
        
        Returns:
            List of Document objects with metadata
        """
        # Load markdown files
        md_docs = self._load_markdown_files()
        
        # Load CSV file
        csv_docs = self._load_csv_file()
        
        # Combine all documents
        self.documents = md_docs + csv_docs
        
        print(f"✓ Loaded {len(self.documents)} document chunks")
        return self.documents
    
    def _load_markdown_files(self) -> List[Document]:
        """Load and chunk markdown files
        
        Strategy: Split by headers to maintain semantic coherence
        Keep FAQ Q&A pairs together
        """
        md_docs = []
        
        # Define header splits for markdown
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
        
        # Additional recursive splitter for long sections
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Load all .md files
        for filename in os.listdir(self.content_path):
            if not filename.endswith('.md'):
                continue
            
            filepath = os.path.join(self.content_path, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by headers first
            header_chunks = markdown_splitter.split_text(content)
            
            # Further split long chunks
            for chunk in header_chunks:
                # Extract metadata from header split
                chunk_metadata = chunk.metadata if hasattr(chunk, 'metadata') else {}
                
                # Get content
                chunk_content = chunk.page_content if hasattr(chunk, 'page_content') else chunk
                
                # If chunk is too long, split recursively
                if len(chunk_content) > config.CHUNK_SIZE:
                    sub_chunks = text_splitter.split_text(chunk_content)
                    for i, sub_chunk in enumerate(sub_chunks):
                        doc = Document(
                            page_content=sub_chunk,
                            metadata={
                                "doc_id": filename.replace('.md', ''),
                                "section_id": f"{chunk_metadata.get('Header 2', 'intro')}_{i}",
                                "doc_type": self._classify_doc_type(filename),
                                "source_file": filename,
                                **chunk_metadata
                            }
                        )
                        md_docs.append(doc)
                else:
                    # Keep chunk as is
                    doc = Document(
                        page_content=chunk_content,
                        metadata={
                            "doc_id": filename.replace('.md', ''),
                            "section_id": chunk_metadata.get('Header 2', 'intro'),
                            "doc_type": self._classify_doc_type(filename),
                            "source_file": filename,
                            **chunk_metadata
                        }
                    )
                    md_docs.append(doc)
        
        return md_docs
    
    def _load_csv_file(self) -> List[Document]:
        """Load product catalog CSV
        
        Strategy: Each product row = one chunk to maintain product integrity
        """
        csv_docs = []
        csv_path = os.path.join(self.content_path, 'products_catalog.csv')
        
        if not os.path.exists(csv_path):
            return csv_docs
        
        df = pd.read_csv(csv_path)
        
        for idx, row in df.iterrows():
            # Create structured text representation
            product_text = f"""Product: {row['name']}
Category: {row['category']}
Format: {row['format']}
Target Concerns: {row['target_concerns']}
Key Herbs: {row['key_herbs']}
Contains Animal Products: {row['contains_animal_products']}
Contraindications: {row['contraindications_short']}
Tags: {row['internal_tags']}"""
            
            doc = Document(
                page_content=product_text,
                metadata={
                    "doc_id": row['product_id'],
                    "section_id": "product_info",
                    "doc_type": "product_catalog",
                    "source_file": "products_catalog.csv",
                    "product_name": row['name']
                }
            )
            csv_docs.append(doc)
        
        return csv_docs
    
    def _classify_doc_type(self, filename: str) -> str:
        """Classify document type based on filename"""
        if 'faq' in filename.lower():
            return 'faq'
        elif 'product' in filename.lower():
            return 'product'
        elif 'treatment' in filename.lower():
            return 'treatment'
        elif 'dosha' in filename.lower():
            return 'guide'
        elif 'foundation' in filename.lower():
            return 'foundation'
        elif 'style' in filename.lower() or 'tone' in filename.lower():
            return 'style_guide'
        else:
            return 'general'


# Convenience function
def load_documents() -> List[Document]:
    """Load all documents from content pack
    
    Returns:
        List of Document objects ready for embedding
    """
    loader = DocumentLoader()
    return loader.load_all_documents()
