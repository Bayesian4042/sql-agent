from fastapi import FastAPI
from app.routes import base, sql_agent
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(base.router)
app.include_router(sql_agent.router)

@app.get("/")
async def root():
    return {"message": "SQL Agent API is running"}
