from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.embedder.openai import OpenAIEmbedder
from agno.document.chunking.semantic import SemanticChunking
import re

# Custom text sanitization function
def sanitize_text(text: str) -> str:
    # Remove special characters and extra whitespace
    text = re.sub(r'[^\w\s.,!?-]', ' ', text)
    # Standardize whitespace
    text = ' '.join(text.split())
    # Remove very short lines (likely headers/footers)
    lines = [line for line in text.splitlines() if len(line.strip()) > 30]
    return '\n'.join(lines)

# Database connection for PgVector
db_url = "postgresql+psycopg://agno:agno@db/agno" 

# Create knowledge base with semantic chunking
knowledge_base = PDFKnowledgeBase(
    path="uploaded_pdfs",
    vector_db=PgVector(
        table_name="pdf_documents",
        db_url=db_url,
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
    # Use semantic chunking instead of TextChunker
    chunking_strategy=SemanticChunking(
        # You can adjust these parameters based on your needs
        chunk_size=500,
        similarity_threshold=0.5,
        embedder=OpenAIEmbedder(id="text-embedding-3-small")
    )
)

# Create the RAG agent
rag_agent = Agent(
    name="PDF Knowledge Agent",
    agent_id="pdf-knowledge-agent",
    model=OpenAIChat(id="gpt-4o"),
    knowledge=knowledge_base,
    # Enable agentic RAG
    search_knowledge=True,
    # Enable chat history
    read_chat_history=True,
    # Store conversations in postgres
    storage=PostgresAgentStorage(
        table_name="pdf_agent_sessions",
        db_url=db_url
    ),
    instructions=[
        "You are a knowledgeable assistant that helps users understand their PDF documents.",
        "Always search the knowledge base first when answering questions.",
        "Provide specific citations to the source PDFs when possible.",
        "If you're unsure about something, say so rather than making assumptions.",
    ],
    markdown=True,
    show_tool_calls=True,
    debug_mode=True,
)

