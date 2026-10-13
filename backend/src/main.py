from fastapi import FastAPI
from src.controllers.animal_controller import router as animal_router
from src.controllers.especie_controller import router as especie_router

app = FastAPI(
    title="LABVEPI API",
    description="API do Laboratório de Vigilância de Epizootias — UFPI",
    version="1.0.0",
)

app.include_router(animal_router)
app.include_router(especie_router)

@app.get("/")
def root():
    return {"message": "API labvepi no ar!"}