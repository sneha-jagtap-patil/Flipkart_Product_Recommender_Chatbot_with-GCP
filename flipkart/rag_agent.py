from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import tool
from flipkart.config import Config


def build_flipkart_retriever_tool(retriever):

    @tool
    def flipkart_retriever_tool(query: str) -> str:
        """
        Retrieve top product reviews related to the user query using ythe provider ! ..
        """
        docs = retriever.invoke(query)
        result_strings = []
        for doc in docs:
            product_name = doc.metadata.get("product_name", "Unknown Product")
            result_strings.append(f"Product: {product_name}\nReview: {doc.page_content}")
        return "\n\n---\n\n".join(result_strings)

    return flipkart_retriever_tool


class RAGAgentBuilder:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.model = init_chat_model(Config.RAG_MODEL)

    def build_agent(self):

        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        flipkart_tool = build_flipkart_retriever_tool(retriever)


        agent = create_agent(
            model=self.model,
            tools=[flipkart_tool],
            system_prompt="""
You are a friendly Flipkart Product Recommender Assistant.

Your job is to help users find the best earphones, headphones, Bluetooth headsets, 
neckbands, earbuds, and audio accessories based on real customer reviews.

IMPORTANT RULES:
1. ALWAYS use the flipkart_retriever_tool to search for product reviews before answering.
2. Your database currently contains reviews for audio products only:
   - BoAt Rockerz 235v2, BoAt BassHeads 100, BoAt Airdopes 131
   - Realme Buds Wireless, Realme Buds 2, Realme Buds Q
   - OnePlus Bullets Wireless Z, OnePlus Bullets Wireless Z Bass Edition
   - U&I Titanic Series Neckband
3. When a user asks about products NOT in your database (like smartphones, laptops, 
   TVs, fashion), politely let them know your current specialty is audio products 
   and suggest they ask about earphones/headsets instead.
4. Format your responses using markdown:
   - Use **bold** for product names
   - Use bullet points for features
   - Use ⭐ for ratings
   - Keep responses concise and helpful
5. When recommending products, mention specific pros and cons from actual reviews.
6. If you truly cannot help, suggest contacting customer care at +97 98652365.
            """,
            checkpointer=InMemorySaver(),
            middleware=[
                SummarizationMiddleware(
                    model=self.model,
                    trigger=("messages", 10),
                    keep=("messages", 4),
                )
            ],
        )

        return agent
