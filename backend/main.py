from fastapi import FastAPI
import models
from database import engine
from routes import auth, profile, match

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sakina Matrimony Backend")

# Register routes
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(match.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Sakina Matrimony API"}
