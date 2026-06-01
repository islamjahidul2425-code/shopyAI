from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routes import whatsapp, cctv, dashboard

app = FastAPI(title="ShopyAI", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=[""], allow_methods=[""], allow_headers=["*"])

@app.on_event("startup")
def startup():
    init_db()
    print("ShopyAI Ready!")

app.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])
app.include_router(cctv.router, prefix="/cctv", tags=["CCTV"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

@app.get("/")
def root():
    return {"status": "ShopyAI chal raha hai!"}