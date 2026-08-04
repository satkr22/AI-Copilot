from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"action": "Get Root"}

@app.get("/users")
def get_users():
    return {"action": "Get all users"}

@app.get("/users/{user_id}")
def get_users_by_id(id: int):
    return {"message": "User fetched successfully",
            "user_id": id
    }

@app.post("/users")
def create_user():
    return {"action": "create user"}

@app.put("/users")
def replace_users():
    return {"action": "Replace users"}

@app.patch("/users")
def update_users():
    return {"action": "Update users"}

@app.delete("/users")
def delete_users():
    return {"action": "Delete users"}

@app.get("/products")
def get_products():
    return {"products": []}

@app.post("/products")
def create_product():
    return {"message": "Product created"}