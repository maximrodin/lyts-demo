from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from typing import List
from sqlmodel import Session, select, SQLModel

from models import Task, TaskCreate, TaskRead
from database import engine, get_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(title="Task Management API", version="1.0.0", lifespan=lifespan)


@app.post("/tasks/", response_model=TaskRead, status_code=201)
def create_task(*, session: Session = Depends(get_session), task: TaskCreate):
    """
    Create a new task with a title and description.

    - **title**: The title of the task.
    - **description**: A detailed description of the task.
    - **status**: The status of the task (default is 'pending').
    """
    db_task = Task.from_orm(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@app.get("/tasks/", response_model=List[TaskRead])
def read_tasks(session: Session = Depends(get_session)):
    """
    Retrieve all tasks.

    Returns a list of all tasks in the system.
    """
    tasks = session.exec(select(Task)).all()
    return tasks


@app.put("/tasks/{task_id}/", response_model=TaskRead)
def update_task_status(
        *, session: Session = Depends(get_session), task_id: int, status: str
):
    """
    Update a task's status.

    - **task_id**: The ID of the task to update.
    - **status**: The new status of the task.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = status
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.delete("/tasks/{task_id}/", status_code=204)
def delete_task(*, session: Session = Depends(get_session), task_id: int):
    """
    Delete a task.

    - **task_id**: The ID of the task to delete.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
