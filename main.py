import os
import re
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from langchain_helper import get_answer
import uvicorn

session_data = {}

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Serve static files
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# Utility: Get vehicles (with picture filename only, no binary)
def get_vehicles():
    conn = psycopg2.connect(
        dbname="Earth_movers",
        user="postgres",
        password="0000",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT id, model_name, vehicle_type, plate_number, status, price_per_hour, notes, picture
        FROM vehicles;
    """)
    vehicles = cur.fetchall()
    cur.close()
    conn.close()
    return vehicles

# Save client info
def save_client_info(name, phone, email):
    conn = psycopg2.connect(
        dbname="Earth_movers",
        user="postgres",
        password="0000",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO clients (name, phone, email, created_at)
        VALUES (%s, %s, %s, NOW())
    """, (name, phone, email))
    conn.commit()
    cur.close()
    conn.close()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/about_us", response_class=HTMLResponse)
def about_us(request: Request):
    return templates.TemplateResponse("about_us.html", {"request": request})

@app.get("/contact_us", response_class=HTMLResponse)
def contact_us(request: Request):
    return templates.TemplateResponse("contact_us.html", {"request": request})

@app.get("/services", response_class=HTMLResponse)
def services(request: Request):
    vehicles = get_vehicles()
    return templates.TemplateResponse("services.html", {
        "request": request,
        "vehicles": vehicles
    })

@app.get("/chatbot_interface", response_class=HTMLResponse)
def chatbot_interface(request: Request):
    return templates.TemplateResponse("chatbot_interface.html", {"request": request})

@app.post("/ask")
async def ask_question(request: Request):
    data = await request.json()
    user_question = data.get("question", "").lower()

    # If it's a rental inquiry
    if "rent" in user_question and ("hw60" in user_question or "hw145" in user_question):
        return {"answer": "Please provide your name, phone, and email to proceed with the reservation."}

    # Check if the input contains a phone number and email
    phone_match = re.search(r"\+?\d[\d\s\-]{6,}", user_question)
    email_match = re.search(r"\S+@\S+", user_question)

    if phone_match and email_match:
        # Basic guess for name (first word in input)
        name = user_question.split(",")[0].strip().capitalize()
        phone = phone_match.group(0).strip()
        email = email_match.group(0).strip()

        # Save to DB
        save_client_info(name, phone, email)
        return {"answer": f"🎉 Thank you, {name}! We’ve saved your details and will contact you soon."}

    # Otherwise, use LangChain to answer
    answer = get_answer(user_question)
    return {"answer": answer}

# Download files from 'data' directory
@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join("data", filename)
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
