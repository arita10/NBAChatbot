from fastapi import FastAPI
from routes.chat import router as chat_router

app = FastAPI(title="NBABot API")

app.include_router(chat_router)


@app.get("/")
def root():
    return {"message": "NBABot API is running!"}
