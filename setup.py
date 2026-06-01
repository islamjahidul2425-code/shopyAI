import os

os.makedirs('routes', exist_ok=True)

main_code = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routes import whatsapp, cctv, dashboard

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("ShopyAI Ready!")
    yield

app = FastAPI(title="ShopyAI", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])
app.include_router(cctv.router, prefix="/cctv", tags=["CCTV"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

@app.get("/")
async def root():
    return {"status": "ShopyAI chal raha hai!"}
"""

db_code = """from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from datetime import datetime

DATABASE_URL = "sqlite+aiosqlite:///./shopyai.db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    stock = Column(Integer, default=0)
    price = Column(Float, nullable=False)
    category = Column(String, default="general")
    shop_name = Column(String, default="ShopyAI Dukan")
    location = Column(String, default="")

class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String, nullable=False)
    qty = Column(Integer, default=1)
    amount = Column(Float, nullable=False)
    sale_time = Column(DateTime, default=datetime.utcnow)

class WhatsAppLog(Base):
    __tablename__ = "whatsapp_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_number = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    ai_reply = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class CCTVAlert(Base):
    __tablename__ = "cctv_alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String, nullable=False)
    confidence = Column(Float, default=0.0)
    camera_id = Column(String, default="cam_01")
    notified = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(Product).limit(1))
        if not result.scalar():
            seeds = [
                Product(name="sabun", stock=50, price=30.0),
                Product(name="chini", stock=50, price=44.0),
                Product(name="tel", stock=15, price=120.0),
            ]
            session.add_all(seeds)
            await session.commit()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
"""

config_code = """from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    WHATSAPP_TOKEN: str = "your_token"
    WHATSAPP_PHONE_ID: str = "your_phone_id"
    WHATSAPP_VERIFY_TOKEN: str = "shopyai123"
    GEMINI_API_KEY: str = "your_gemini_key"
    OWNER_WHATSAPP: str = "+923001234567"
    CCTV_CONFIDENCE_THRESHOLD: float = 0.65
    CCTV_ALERT_COOLDOWN_SECONDS: int = 60
    class Config:
        env_file = ".env"
settings = Settings()
"""

dashboard_code = """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from database import get_db, Product, Sale

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
async def summary(db: AsyncSession = Depends(get_db)):
    prods = (await db.execute(select(Product))).scalars().all()
    sales = (await db.execute(select(Sale))).scalars().all()
    today = datetime.utcnow().date()
    today_sales = [s for s in sales if s.sale_time.date() == today]
    return {
        "aaj_ki_kamai": sum(s.amount for s in today_sales),
        "kul_kamai": sum(s.amount for s in sales),
        "total_products": len(prods),
        "low_stock": [{"name":p.name,"stock":p.stock} for p in prods if p.stock<=10],
        "products": [{"id":p.id,"name":p.name,"stock":p.stock,"price":p.price} for p in prods],
    }

@router.post("/sell")
async def sell(req: SellRequest, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Product).where(Product.name==req.product_name))).scalar_one_or_none()
    if not p: raise HTTPException(404, "Product nahi mila")
    if p.stock < req.qty: raise HTTPException(400, f"Sirf {p.stock} bacha hai")
    p.stock -= req.qty
    db.add(Sale(product_name=p.name, qty=req.qty, amount=p.price*req.qty))
    await db.commit()
    return {"success": True, "amount": p.price*req.qty, "remaining": p.stock}

@router.post("/add-product")
async def add_product(req: AddProductRequest, db: AsyncSession = Depends(get_db)):
    db.add(Product(name=req.name.lower(), stock=req.stock, price=req.price, category=req.category, location=req.location))
    await db.commit()
    return {"success": True, "message": f"{req.name} add ho gaya!"}

@router.get("/sales")
async def get_sales(db: AsyncSession = Depends(get_db)):
    sales = (await db.execute(select(Sale).order_by(Sale.sale_time.desc()).limit(50))).scalars().all()
    return {"sales": [{"product":s.product_name,"qty":s.qty,"amount":s.amount,"time":str(s.sale_time)} for s in sales]}
"""

whatsapp_code = """from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, Product, WhatsAppLog
from config import settings

router = APIRouter()

@router.get("/webhook")
async def verify(request: Request):
    p = dict(request.query_params)
    if p.get("hub.verify_token") == settings.WHATSAPP_VERIFY_TOKEN:
        return int(p.get("hub.challenge", 0))
    return {"error": "invalid token"}

@router.post("/webhook")
async def receive(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    try:
        msg = body["entry"][0]["changes"][0]["value"]["messages"][0]
        from_num = msg["from"]
        text = msg["text"]["body"] if msg["type"] == "text" else "image"
        reply = await get_reply(text, db)
        db.add(WhatsAppLog(from_number=from_num, message=text, ai_reply=reply))
        await db.commit()
        return {"status": "ok", "reply": reply}
    except Exception as e:
        return {"error": str(e)}

async def get_reply(msg: str, db: AsyncSession) -> str:
    prods = (await db.execute(select(Product))).scalars().all()
    for p in prods:
        if p.name in msg.lower():
            return f"{p.name} ki qeemat Rs.{p.price} hai, stock: {p.stock}"
    return "Aapka shukriya! Kaunsa saman chahiye?"

@router.post("/test-reply")
async def test_reply(payload: dict, db: AsyncSession = Depends(get_db)):
    reply = await get_reply(payload.get("message",""), db)
    return {"ai_reply": reply}
"""

cctv_code = """from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, CCTVAlert
from config import settings
import time, base64, json

router = APIRouter()
_last_alert = {}

@router.post("/analyze-frame")
async def analyze(background_tasks: BackgroundTasks, camera_id: str = "cam_01",
                  file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    image_bytes = await file.read()
    detection = {"safe": True, "threats_found": False, "detections": []}
    return detection

@router.get("/alerts")
async def get_alerts(db: AsyncSession = Depends(get_db)):
    result = (await db.execute(select(CCTVAlert).order_by(CCTVAlert.timestamp.desc()).limit(50))).scalars().all()
    return {"alerts": [{"type":a.alert_type,"camera":a.camera_id,"time":str(a.timestamp)} for a in result]}
"""

with open("main.py","w") as f: f.write(main_code)
with open("database.py","w") as f: f.write(db_code)
with open("config.py","w") as f: f.write(config_code)
with open("routes/__init__.py","w") as f: f.write("")
with open("routes/dashboard.py","w") as f: f.write(dashboard_code)
with open("routes/whatsapp.py","w") as f: f.write(whatsapp_code)
with open("routes/cctv.py","w") as f: f.write(cctv_code)

print("SHOPYAI READY!")