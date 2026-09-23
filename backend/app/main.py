from fastapi import FastAPI

app = FastAPI(
    title="AI Job Outreach Agent",
    description="Backend API for the AI Job Outreach Agent",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "AI Job Outreach Agent API is running"
    }