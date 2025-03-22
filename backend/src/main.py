
from fastapi import FastAPI # type: ignore
from routes.authRoute import router as auth_router
from config.db import client


db = client.get_database("chatappp") 
collection = db.get_collection("collection")

print("Connected to MongoDB database:", db.name)

app = FastAPI()

# Take route
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/")
def root():
    return {"message": "Welcome to the Authentication System"}

if __name__ == "__main__":
    import uvicorn  # type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)