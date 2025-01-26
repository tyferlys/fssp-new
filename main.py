import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.task.router import router as task_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(task_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9004)