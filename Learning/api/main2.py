from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "This is Root"}

@app.get("/users")
def get_users(page: int = 1):
    return {"Page": page}

@app.get("/users/{user_id}")
def get_users_by_id(user_id: int, viewer_page: int = 1):
    return {"user_id": user_id, 
            "viewer_page": viewer_page
    }
    
    
@app.get("/users/{user_id}/posts")
def get_posts(
    user_id: int,
    page: int = 1,
    limit: int = 15
):
    return {
        "user_id": user_id,
        "page": page,
        "limit": limit
    }
    

@app.get("/products/{user_id}")
def get_products(
    user_id: int,
    page: int,
    limit: int = 15,
    sort: str = "price"   
):
    return{
        "user_id": user_id,
        "page": page,
        "limit": limit,
        "sort": sort
    }
    
