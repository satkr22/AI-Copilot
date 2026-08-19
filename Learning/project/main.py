from fastapi import FastAPI
from routers.user import router as user_router
from routers.product import router as product_router
from routers.auth import router as auth_router


app = FastAPI()


app.include_router(user_router)
app.include_router(product_router)
app.include_router(auth_router)

    
@app.get("/")
def root():
    return {
        "message": "This is root"
    }

