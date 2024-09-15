import os
import json
import requests
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from dotenv import load_dotenv

load_dotenv()


class CombinedVectorizer:
    def __init__(self, swagger_url: str, allure_results_dir: str, vector_db_path: str):
        self.swagger_url = swagger_url
        self.allure_results_dir = allure_results_dir
        self.vector_db_path = vector_db_path
        self.embeddings = OpenAIEmbeddings()

    def fetch_swagger_json(self):
        response = requests.get(self.swagger_url)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Failed to fetch Swagger JSON: {response.status_code}")


    def vectorize_swagger(self, swagger_json):
        documents = []
        for path, methods in swagger_json.get("paths", {}).items():
            for method, details in methods.items():
                summary = details.get("summary", "No summary provided")
                description = details.get("description", "No description provided")
                request_body = details.get("requestBody", {})
                responses = details.get("responses", {})
                parameters = details.get("parameters", [])

                # Consolidate all relevant information into one document
                doc_content = f"""
                API Path: {path}
                Method: {method.upper()}
                Summary: {summary}
                Description: {description}
                Parameters: {json.dumps(parameters, indent=2)}
                Request Body: {json.dumps(request_body, indent=2)}
                Responses: {json.dumps(responses, indent=2)}
                """
                doc_metadata = {"source": "swagger", "path": path, "method": method}
                documents.append(Document(page_content=doc_content, metadata=doc_metadata))
        return documents

    def fetch_allure_results(self):
        allure_results = []
        for root, _, filenames in os.walk(self.allure_results_dir):
            for filename in filenames:
                if filename.endswith("-result.json"):
                    filepath = os.path.join(root, filename)
                    with open(filepath, "r") as file:
                        allure_results.append(json.load(file))
        return allure_results

    def load_attachment(self, source):
        attachment_path = os.path.join(self.allure_results_dir, source)
        if os.path.exists(attachment_path):
            with open(attachment_path, "r") as file:
                return file.read()
        return None


    def vectorize_allure_results(self, allure_results):
        documents = []
        for result in allure_results:
            # Extracting labels
            labels = result.get("labels", [])
            feature = next((label["value"] for label in labels if label["name"] == "feature"), "No feature")
            story = next((label["value"] for label in labels if label["name"] == "story"), "No story")
            title = result.get("name", "No title")

            # Collecting main test details
            test_name = result.get("name")
            test_status = result.get("status")
            test_uuid = result.get("uuid")
            test_fullname = result.get("fullName")
            labels_text = json.dumps(labels, indent=2)
            start_time = result.get("start")
            stop_time = result.get("stop")
            duration = stop_time - start_time if start_time and stop_time else "N/A"

            # Start creating the full test context
            full_test_content = f"Test Name: {test_name}\nStatus: {test_status}\nUUID: {test_uuid}\nFull Name: {test_fullname}\nDuration: {duration}ms\nLabels: {labels_text}\n"

            # Process each step and its attachments
            for step in result.get("steps", []):
                step_name = step.get("name")
                step_status = step.get("status")
                step_start = step.get("start")
                step_stop = step.get("stop")
                step_duration = step_stop - step_start if step_start and step_stop else "N/A"

                full_test_content += f"\nStep Name: {step_name}\nStatus: {step_status}\nDuration: {step_duration}ms\n"

                for attachment in step.get("attachments", []):
                    attachment_content = self.load_attachment(attachment["source"])
                    if attachment_content:
                        full_test_content += f"\nAttachment ({attachment['name']}):\n{attachment_content}\n"

            # Finalize the document content
            doc_metadata = {
                "source": "allure",
                "uuid": test_uuid,
                "feature": feature,
                "story": story,
                "title": title,
            }
            documents.append(Document(page_content=full_test_content, metadata=doc_metadata))

        return documents

    def store_vectors(self, documents):
        vector_store = FAISS.from_documents(documents, self.embeddings)
        vector_store.save_local(self.vector_db_path)
        return vector_store

    def process_and_store(self):
        # Fetch and vectorize Swagger data
        swagger_json = self.fetch_swagger_json()
        swagger_docs = self.vectorize_swagger(swagger_json)

        # Fetch and vectorize Allure results
        allure_results = self.fetch_allure_results()
        allure_docs = self.vectorize_allure_results(allure_results)

        # Combine all documents and store them
        all_docs = swagger_docs + allure_docs
        self.store_vectors(all_docs)

if __name__ == "__main__":
    swagger_url = "http://127.0.0.1:8000/openapi.json"
    allure_results_dir = "./allure-results"
    vector_db_path = "./combined_vector_db"

    vectorizer = CombinedVectorizer(swagger_url, allure_results_dir, vector_db_path)
    vectorizer.process_and_store()