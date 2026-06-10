from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, SessionLocal
from models import Base
from auth import init_default_users
from routers import auth, trenches, strata, artifacts, audits, relations

Base.metadata.create_all(bind=engine)

db = SessionLocal()
init_default_users(db)
db.close()

app = FastAPI(title="考古发掘记录系统", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(trenches.router)
app.include_router(strata.router)
app.include_router(artifacts.router)
app.include_router(audits.router)
app.include_router(relations.router)


@app.get("/")
async def root():
    return {"message": "考古发掘记录系统 API", "docs": "/docs"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
