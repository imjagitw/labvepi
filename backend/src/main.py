from fastapi import FastAPI
from src.controllers.animal_controller import router as animal_router
from src.controllers.especie_controller import router as especie_router
from src.controllers.amostra_controller import router as amostra_router
from src.controllers.exame_controller import router as exame_router
from src.controllers.estoque_reagente_controller import router as estoque_reagente_router
from src.controllers.reagente_controller import router as reagente_router
from src.models.Especie.especie_details import EspecieDetails
from src.models.Animal.animal import Animal

# Garante a resolução completa de referências bidirecionais para os schemas OpenAPI
EspecieDetails.model_rebuild(_types_namespace={"Animal": Animal})

app = FastAPI(
    title="LABVEPI API",
    description="API do Laboratório de Vigilância de Epizootias — UFPI",
    version="1.0.0",
)

app.include_router(animal_router)
app.include_router(especie_router)
app.include_router(amostra_router)
app.include_router(exame_router)
app.include_router(estoque_reagente_router)
app.include_router(reagente_router)

@app.get("/")
def root():
    return {"message": "API labvepi no ar!"}