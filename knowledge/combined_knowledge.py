from agno.knowledge.combined import CombinedKnowledgeBase
from agno.knowledge.pdf import PDFKnowledgeBase 
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://agno:agno@db/agno"

knowledge_base = CombinedKnowledgeBase(
    # TODO: add more sources 
    sources=[
        PDFKnowledgeBase(
            vector_db=PgVector(table_name="documents_pdf", db_url=db_url), path=""
        )
    ],
    vector_db=PgVector(table_name="documents_combined", db_url=db_url)
)

