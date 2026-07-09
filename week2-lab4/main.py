from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="Validated To-Do API")

# --- PYDANTIC MODELS (SCHEMAS) ---

# Schema for incoming request data (id is handled by the server)
class TodoCreate(BaseModel):
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="The title of the to-do item. Cannot be empty."
    )
    completed: bool = Field(
        default=False, 
        description="Completion status of the task."
    )
    description: Optional[str] = Field(
        default=None, 
        max_length=500, 
        description="Optional detailed description."
    )

# Schema for database records and API responses (includes auto-generated ID)
class Todo(BaseModel):
    id: int
    title: str
    completed: bool
    description: Optional[str] = None


# --- IN-MEMORY DATABASE ---
todos_db: List[Todo] = []


# --- HELPER FUNCTIONS ---
def get_next_id() -> int:
    """Helper to automatically increment and return the next unique ID."""
    if not todos_db:
        return 1
    return max(todo.id for todo in todos_db) + 1


# --- API ENDPOINTS ---

@app.post("/todos/", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(todo_in: TodoCreate):
    # Edge Case: Prevent empty or whitespace-only titles
    clean_title = todo_in.title.strip()
    if not clean_title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Title cannot consist of only spaces."
        )
    
    # Edge Case: Prevent duplicate tasks with the exact same title
    for existing_todo in todos_db:
        if existing_todo.title.lower() == clean_title.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A to-do item with the title '{clean_title}' already exists."
            )
            
    # Auto-generate unique ID and save
    new_todo = Todo(
        id=get_next_id(),
        title=clean_title,
        completed=todo_in.completed,
        description=todo_in.description.strip() if todo_in.description else None
    )
    todos_db.append(new_todo)
    return new_todo


@app.get("/todos/", response_model=List[Todo])
def get_todos():
    return todos_db


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    # Edge Case: Reject invalid IDs early
    if todo_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="ID must be a positive integer."
        )

    for todo in todos_db:
        if todo.id == todo_id:
            return todo
            
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail=f"To-Do with ID {todo_id} not found"
    )


@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, updated_todo: TodoCreate):
    if todo_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="ID must be a positive integer."
        )

    clean_title = updated_todo.title.strip()
    if not clean_title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Title cannot consist of only spaces."
        )

    for index, todo in enumerate(todos_db):
        if todo.id == todo_id:
            # Edge Case: Check duplicate title excluding itself
            for existing_todo in todos_db:
                if existing_todo.id != todo_id and existing_todo.title.lower() == clean_title.lower():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Another to-do item with the title '{clean_title}' already exists."
                    )
            
            # Map updated values while preserving the original ID
            todos_db[index] = Todo(
                id=todo_id,
                title=clean_title,
                completed=updated_todo.completed,
                description=updated_todo.description.strip() if updated_todo.description else None
            )
            return todos_db[index]
            
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail=f"To-Do with ID {todo_id} not found"
    )


@app.delete("/todos/{todo_id}", status_code=status.HTTP_200_OK)
def delete_todo(todo_id: int):
    if todo_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="ID must be a positive integer."
        )

    for index, todo in enumerate(todos_db):
        if todo.id == todo_id:
            del todos_db[index]
            return {"message": f"To-Do with ID {todo_id} deleted successfully"}
            
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail=f"To-Do with ID {todo_id} not found"
    )