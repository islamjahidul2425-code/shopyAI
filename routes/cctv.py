from fastapi import APIRouter, UploadFile, File
from database import get_conn
from datetime import datetime

router = APIRouter()

@router.post("/analyze-frame")
async def analyze(camera_id: str = "cam_01", file: UploadFile = File(...)):
    return {"safe": True, "threats_found": False, "camera_id": camera_id}

@router.get("/alerts")
def get_alerts():
    conn = get_conn()
    rows = conn.execute('SELECT * FROM cctv_alerts ORDER BY id DESC LIMIT 50').fetchall()
    conn.close()
    return {"alerts": [dict(r) for r in rows]}