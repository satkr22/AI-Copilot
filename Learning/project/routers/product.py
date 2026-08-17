from fastapi import APIRouter

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.get("")
def get_products():
    return {
        "message": "all products"
    }

@router.get("/page")
def get_products_by_page(limit: int = 20, offset: int = 0):
    return {
        "limit": limit,
        "offset": offset
    }