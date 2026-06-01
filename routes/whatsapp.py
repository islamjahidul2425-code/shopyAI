from fastapi import APIRouter, Request
from database import get_products, log_whatsapp
import os

router = APIRouter()

def get_reply(msg: str) -> str:
    try:
        import google.generativeai as genai
        key = os.getenv("GEMINI_API_KEY", "")
        if not key or key == "your_gemini_key":
            return simple_reply(msg)
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        products = get_products()
        product_list = "\n".join([f"- {p['name']}: Rs.{p['price']}, stock: {p['stock']}" for p in products])
        prompt = f"""Tum ShopyAI dukan ke assistant ho. Urdu/Hinglish mein jawab do.
Hamare products:
{product_list}
Customer: {msg}
Short jawab do (2 lines max):"""
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except:
        return simple_reply(msg)

def simple_reply(msg: str) -> str:
    products = get_products()
    for p in products:
        if p["name"] in msg.lower():
            return f"{p['name']} ki qeemat Rs.{p['price']} hai, stock: {p['stock']}"
    return "Aapka shukriya! Kaunsa saman chahiye? Hamare paas sabun, chini, tel hai."

@router.get("/webhook")
async def verify(request: Request):
    p = dict(request.query_params)
    if p.get("hub.verify_token") == "shopyai123":
        return int(p.get("hub.challenge", 0))
    return {"error": "invalid token"}

@router.post("/webhook")
async def receive(request: Request):
    body = await request.json()
    try:
        msg = body["entry"][0]["changes"][0]["value"]["messages"][0]
        from_num = msg["from"]
        text = msg["text"]["body"] if msg["type"] == "text" else "image"
        reply = get_reply(text)
        log_whatsapp(from_num, text, reply)
        return {"status": "ok", "reply": reply}
    except Exception as e:
        return {"error": str(e)}

@router.post("/test-reply")
async def test_reply(payload: dict):
    reply = get_reply(payload.get("message", ""))
    return {"ai_reply": reply}