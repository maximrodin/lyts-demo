import pytest
import requests
import allure
from models import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

TEST_DATABASE_URL = "sqlite:///./tasks.db"

engine = create_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session")
def prepare_database():
    SQLModel.metadata.create_all(engine)
    yield


@pytest.fixture(scope="session")
def client(prepare_database):
    return requests.Session()


@allure.feature("Task Management")
@allure.story("Create Task")
@allure.title("Test creating a task")
def test_create_task(client):
    with allure.step("Send POST request to create a task"):
        url = "http://127.0.0.1:8000/tasks/"
        payload = {"title": "Test Task", "description": "This is a test task."}
        response = client.post(url, json=payload)

        allure.attach(url, "Request URL", allure.attachment_type.TEXT)
        allure.attach(str(payload), "Request Body", allure.attachment_type.JSON)
        allure.attach(str(response.status_code), "Response Status", allure.attachment_type.TEXT)
        allure.attach(str(response.headers), "Response Headers", allure.attachment_type.TEXT)
        allure.attach(response.text, "Response Body", allure.attachment_type.JSON)

    with allure.step("Check if the task was created successfully"):
        expected_status_code = 201
        allure.attach(f"Expected: {expected_status_code}, Actual: {response.status_code}",
                      "Assertion: Status Code", allure.attachment_type.TEXT)
        assert response.status_code == expected_status_code

        data = response.json()
        allure.attach(str(data), "Response Data", allure.attachment_type.JSON)

        expected_title = "Test Task"
        expected_description = "This is a test task."

        allure.attach(f"Expected: {expected_title}, Actual: {data['title']}",
                      "Assertion: Title", allure.attachment_type.TEXT)
        assert data["title"] == expected_title

        allure.attach(f"Expected: {expected_description}, Actual: {data['description']}",
                      "Assertion: Description", allure.attachment_type.TEXT)
        assert data["description"] == expected_description


@allure.feature("Task Management")
@allure.story("Read Tasks")
@allure.title("Test reading all tasks")
def test_read_tasks(client):
    with allure.step("Send GET request to retrieve all tasks"):
        url = "http://127.0.0.1:8000/tasks/"
        response = client.get(url)

        allure.attach(url, "Request URL", allure.attachment_type.TEXT)
        allure.attach(str(response.status_code), "Response Status", allure.attachment_type.TEXT)
        allure.attach(str(response.headers), "Response Headers", allure.attachment_type.TEXT)
        allure.attach(response.text, "Response Body", allure.attachment_type.JSON)

    with allure.step("Check if tasks are retrieved successfully"):
        expected_status_code = 200
        allure.attach(f"Expected: {expected_status_code}, Actual: {response.status_code}",
                      "Assertion: Status Code", allure.attachment_type.TEXT)
        assert response.status_code == expected_status_code

        data = response.json()
        allure.attach(str(data), "Response Data", allure.attachment_type.JSON)

        allure.attach(f"Expected: List, Actual: {type(data)}",
                      "Assertion: Data Type", allure.attachment_type.TEXT)
        assert isinstance(data, list)

        allure.attach(f"Expected: At least 1 task, Actual: {len(data)}",
                      "Assertion: Task Count", allure.attachment_type.TEXT)
        assert len(data) >= 1


@allure.feature("Task Management")
@allure.story("Update Task Status")
@allure.title("Test updating task status")
def test_update_task_status(client):
    with allure.step("Create a task for updating status"):
        url = "http://127.0.0.1:8000/tasks/"
        payload = {"title": "Task to Update", "description": "Update status."}
        response = client.post(url, json=payload)
        task_id = response.json()["id"]

        allure.attach(url, "Request URL", allure.attachment_type.TEXT)
        allure.attach(str(payload), "Request Body", allure.attachment_type.JSON)
        allure.attach(str(response.status_code), "Response Status", allure.attachment_type.TEXT)
        allure.attach(str(response.headers), "Response Headers", allure.attachment_type.TEXT)
        allure.attach(response.text, "Response Body", allure.attachment_type.JSON)

    with allure.step("Send PUT request to update task status"):
        url = f"http://127.0.0.1:8000/tasks/{task_id}/"
        params = {"status": "completed"}
        response = client.put(url, params=params)

        allure.attach(url, "Request URL", allure.attachment_type.TEXT)
        allure.attach(str(params), "Request Parameters", allure.attachment_type.JSON)
        allure.attach(str(response.status_code), "Response Status", allure.attachment_type.TEXT)
        allure.attach(str(response.headers), "Response Headers", allure.attachment_type.TEXT)
        allure.attach(response.text, "Response Body", allure.attachment_type.JSON)

    with allure.step("Check if the task status was updated successfully"):
        expected_status_code = 200
        allure.attach(f"Expected: {expected_status_code}, Actual: {response.status_code}",
                      "Assertion: Status Code", allure.attachment_type.TEXT)
        assert response.status_code == expected_status_code

        data = response.json()
        allure.attach(str(data), "Response Data", allure.attachment_type.JSON)

        expected_status = "completed"
        allure.attach(f"Expected: {expected_status}, Actual: {data['status']}",
                      "Assertion: Status", allure.attachment_type.TEXT)
        assert data["status"] == expected_status

    with allure.step("Validate the task status in the database"):
        session = TestingSessionLocal()
        task_in_db = session.get(Task, task_id)

        sql_query = f"SELECT * FROM tasks WHERE id={task_id}"
        allure.attach(sql_query, "SQL Query", allure.attachment_type.TEXT)
        allure.attach(str(task_in_db), "Database Data", allure.attachment_type.JSON)

        allure.attach(f"Expected: {expected_status}, Actual: {task_in_db.status}",
                      "Assertion: Database Status", allure.attachment_type.TEXT)
        assert task_in_db.status == expected_status
        session.close()


@allure.feature("Task Management")
@allure.story("Delete Task")
@allure.title("Test deleting a task")
def test_delete_task(client):
    with allure.step("Create a task for deletion"):
        url = "http://127.0.0.1:8000/tasks/"
        payload = {"title": "Task to Delete", "description": "Delete me."}
        response = client.post(url, json=payload)
        task_id = response.json()["id"]

        allure.attach(url, "Request URL", allure.attachment_type.TEXT)
        allure.attach(str(payload), "Request Body", allure.attachment_type.JSON)
        allure.attach(str(response.status_code), "Response Status", allure.attachment_type.TEXT)
        allure.attach(str(response.headers), "Response Headers", allure.attachment_type.TEXT)
        allure.attach(response.text, "Response Body", allure.attachment_type.JSON)

    with allure.step("Send DELETE request to delete the task"):
        url = f"http://127.0.0.1:8000/tasks/{task_id}/"
        response = client.delete(url)

        allure.attach(url, "Request URL", allure.attachment_type.TEXT)
        allure.attach(str(response.status_code), "Response Status", allure.attachment_type.TEXT)
        allure.attach(str(response.headers), "Response Headers", allure.attachment_type.TEXT)
        allure.attach(response.text, "Response Body", allure.attachment_type.JSON)

    with allure.step("Check if the task was deleted successfully"):
        expected_status_code = 204
        allure.attach(f"Expected: {expected_status_code}, Actual: {response.status_code}",
                      "Assertion: Status Code", allure.attachment_type.TEXT)
        assert response.status_code == expected_status_code

    with allure.step("Validate the task deletion in the database"):
        session = TestingSessionLocal()
        task_in_db = session.get(Task, task_id)

        sql_query = f"SELECT * FROM tasks WHERE id={task_id}"
        allure.attach(sql_query, "SQL Query", allure.attachment_type.TEXT)
        allure.attach(str(task_in_db), "Database Data", allure.attachment_type.JSON)

        allure.attach(f"Expected: None, Actual: {task_in_db}",
                      "Assertion: Database Record", allure.attachment_type.TEXT)
        assert task_in_db is None
        session.close()
