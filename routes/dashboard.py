from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import init_db, get_products, sell_product, get_sales

router = APIRouter()

class SellRequest(BaseModel):
    product_name: str
    qty: int = 1

class AddProductRequest(BaseModel):
    name: str
    stock: int
    price: float
    category: str = "general"
    location: str = ""

@router.get("/summary")
def summary():
    products = get_products()
    sales = get_sales()
    today = __import__('datetime').date.today().isoformat()
    today_sales = [s for s in sales if s["sale_time"] and s["sale_time"].startswith(today)]
    return {
        "aaj_ki_kamai": sum(s["amount"] for s in today_sales),
        "kul_kamai": sum(s["amount"] for s in sales),
        "total_products": len(products),
        "low_stock": [p for p in products if p["stock"] <= 10],
        "products": products,
    }

@router.post("/sell")
def sell(req: SellRequest):
    amount = sell_product(req.product_name, req.qty)
    if amount is None:
        raise HTTPException(400, "Product nahi mila ya stock kam hai")
    return {"success": True, "amount": amount}

@router.get("/sales")
def sales():
    return {"sales": get_sales()}