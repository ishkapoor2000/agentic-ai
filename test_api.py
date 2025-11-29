from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    """Get all users from the database."""
    return [{"name": "Alice"}, {"name": "Bob"}]

@app.post("/users")
def create_user(user: dict):
    """Create a new user."""
    return user

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete a user by ID."""
    return {"status": "deleted"}
