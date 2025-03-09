from agno.knowledge.combined import CombinedKnowledgeBase
from agno.knowledge.csv import CSVKnowledgeBase
from agno.knowledge.docx import DocxKnowledgeBase
from agno.knowledge.json import JSONKnowledgeBase
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.knowledge.text import TextKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType

# Chunking Strategy 
from agno.document.chunking.semantic import SemanticChunking

# Embedder
from agno.embedder.openai import OpenAIEmbedder 

db_url = "postgresql+psycopg://agno:agno@db/agno"

knowledge_base = CombinedKnowledgeBase(
    sources=[
        PDFKnowledgeBase(
            vector_db=PgVector(table_name="recipes_pdf", db_url=db_url), path=""
        ),
        CSVKnowledgeBase(
            vector_db=PgVector(table_name="recipes_csv", db_url=db_url), path=""
        ),
        DocxKnowledgeBase(
            vector_db=PgVector(table_name="recipes_docx", db_url=db_url), path=""
        ),
        JSONKnowledgeBase(
            vector_db=PgVector(table_name="recipes_json", db_url=db_url), path=""
        ),
        TextKnowledgeBase(
            vector_db=PgVector(table_name="recipes_text", db_url=db_url), path=""
        ),
        
    ],
    vector_db=PgVector(
        table_name="recipes_combined", 
        db_url=db_url,
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
    chunking_strategy=SemanticChunking(), 
)
