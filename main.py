from fastapi import FastAPI
from routes.chat import router as chat_router
from routes.webhook import router as webhook_router

app = FastAPI(title="NBABot API")

app.include_router(chat_router)
app.include_router(webhook_router)


@app.get("/")
def root():
    return {"message": "NBABot API is running!"}
