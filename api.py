from fastapi import FastAPI

from app.controllers.apartamentos import aps_ctrl
from app.controllers.sessions import sessions_controller

app = FastAPI()

app.include_router(aps_ctrl)
app.include_router(sessions_controller)

@app.get("/health")
async def health():
    return "ok"
