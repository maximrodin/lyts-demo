from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

from dotenv import load_dotenv

load_dotenv()


class RAGTestCoverageAnalysis:
    def __init__(self, vector_db_path: str):
        # Initialize embeddings and load vector store
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = FAISS.load_local(vector_db_path, self.embeddings, allow_dangerous_deserialization=True)

        # Initialize the LLM and create the conversational retrieval chain
        self.llm = ChatOpenAI(model_name="gpt-4")  # Use GPT-4 or GPT-3.5
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.qa_chain = ConversationalRetrievalChain.from_llm(self.llm, retriever=self.vector_store.as_retriever(), memory=memory)

    def retrieve_context(self, query: str):
        # Retrieve a broader range of documents to ensure full context
        docs = self.vector_store.similarity_search(query, k=5)
        swagger_docs = [doc.page_content for doc in docs if doc.metadata.get("source") == "swagger"]
        allure_docs = [doc.page_content for doc in docs if doc.metadata.get("source") == "allure"]

        # Combine the most relevant Swagger and Allure documents
        context = "\n\n".join(swagger_docs + allure_docs)
        return context

    def analyze_coverage(self, system_prompt: str, query: str):
        # Retrieve the relevant context for the query
        context = self.retrieve_context(query)
        combined_prompt = system_prompt + "\n\nContext:\n" + context + "\n\n" + query
        return self.qa_chain.run({"question": combined_prompt, "chat_history": []})

    def generate_new_tests(self, system_prompt: str, query: str):
        # Retrieve the relevant context for the query
        context = self.retrieve_context(query)
        combined_prompt = system_prompt + "\n\nContext:\n" + context + "\n\n" + query
        return self.qa_chain.run({"question": combined_prompt, "chat_history": []})


if __name__ == "__main__":
    vector_db_path = "../combined_vector_db"

    rag_analyzer = RAGTestCoverageAnalysis(vector_db_path)

    # Example system prompt
    system_prompt = """
    You are a Senior Test Analyst with extensive experience in test design, coverage analysis, and quality assurance. Your task is to analyze the test coverage, efficiency, and completeness of the existing test suite based on the following combined context:
    
    1. Swagger API Documentation: Review the API models, endpoints, and operations described in the Swagger documentation.
    2. Allure Test Results: Review the existing test results, including the steps, assertions, and any linked attachments from the Allure reports.
    3. Combined Analysis: Cross-reference the Swagger documentation with the Allure test results to determine if all API endpoints are adequately tested.
    4. Test Efficiency: Evaluate the efficiency of the existing tests.
    5. Missed Steps Identification: Identify any untested scenarios or missed steps based on the Swagger API models and the actual test results.
    6. Additional Coverage Suggestions: Recommend additional test cases that could enhance coverage.
    7. Test Design Best Practices: Explain the rationale behind each recommendation and how it aligns with best test design practices.
    """

    # # Example query to analyze test coverage including Swagger and Allure context
    coverage_query = "Analyze the test coverage for the endpoints from swagger and test results and suggest any missing tests."

    coverage_analysis = rag_analyzer.analyze_coverage(system_prompt, coverage_query)
    print("Coverage Analysis:", coverage_analysis)

    # Example query to generate new test cases based on Swagger and Allure data
    generate_tests_query = "Suggest new test cases for the PUT /tasks/{task_id}/ endpoint based on the Swagger API and Allure results."
    new_tests = rag_analyzer.generate_new_tests(system_prompt, generate_tests_query)
    print("New Test Cases:", new_tests)

    generate_tests_query = "Analyse the average tests speed and API communication delays"
    new_tests = rag_analyzer.generate_new_tests(system_prompt, generate_tests_query)
    print("New Test Cases:", new_tests)
