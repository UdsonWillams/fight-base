import contextlib
import os
from typing import AsyncIterator

from alembic.command import upgrade
from alembic.config import Config as alembic_config
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.applications import Starlette
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.logger import logger
from app.core.settings import get_settings
from app.exceptions.exceptions import DefaultApiException
from app.middlewares.response_time import ResponseTimeMiddleware
from app.middlewares.trace_id import CreateTraceIdMiddleware
from app.services.ml.model_loader import ml_model_loader

from app.services.system_admin import create_admin

from fastapi.concurrency import run_in_threadpool


config_file = alembic_config()
settings = get_settings()

config_file.set_main_option("script_location", settings.APP_MIGRATIONS_FOLDER)
# ConfigParser requer que '%' seja escapado como '%%' para evitar erro de interpolação
safe_url = settings.DATABASE_URL.replace("%", "%%")
config_file.set_main_option("sqlalchemy.url", safe_url)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator:
    logger.info("Running database migrations in background thread...")
    await run_in_threadpool(upgrade, config_file, "head")

    # Carregar modelo ML
    logger.info("🤖 Inicializando modelo ML...")
    await ml_model_loader.load_model()

    # Carregar system-admin
    logger.info("🤖 Inicializando system-admin...")
    await create_admin()

    yield


app = FastAPI(
    title="🥊 FightBase API",
    description="""
    ## FightBase - MMA Fighter Database & Simulation API

    Sistema completo para gerenciar lutadores de MMA e simular lutas baseadas em estatísticas realistas.

    ### Principais Recursos:

    - 🥋 **Gestão de Lutadores**: CRUD completo com atributos detalhados (striking, grappling, defense, etc)
    - ⚔️ **Simulação de Lutas**: Algoritmo inteligente que simula lutas round a round
    - 📊 **Comparação**: Compare lutadores e veja vantagens/desvantagens
    - 🎯 **Previsões**: Calcule probabilidades antes de simular
    - 🏆 **Rankings**: Melhores lutadores por organização e categoria
    - 📈 **Estatísticas**: Histórico completo de simulações e análises

    ### Organizações Suportadas:
    UFC, Bellator, ONE Championship, PFL, Rizin, Glory, K-1 e outras

    ### Categorias de Peso:
    Todas as categorias oficiais do MMA, desde peso-palha até peso-pesado

    ---

    **Criado para fãs de MMA que querem explorar matchups impossíveis! 🥊**
    """,
    version="2.0.0",
    docs_url="/swagger",
    redoc_url="/docs",
    separate_input_output_schemas=True,
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Handle general exceptions. For ApiException types, re-raise them to be handled
    by FastAPI's built-in exception handlers. For other exceptions, return a generic
    error response while logging the actual error details.
    """
    logger.error(f"Erro ao processar execução | Tipo do erro: {type(exc)} | {exc}")
    if isinstance(exc, DefaultApiException):
        raise exc
    if settings.APP_ENVIRONMENT in ["local"]:
        return JSONResponse(
            content={"message": f"Error: {type(exc)} - {exc}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return JSONResponse(
        content={"message": "An Internal Error Occurred"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.APP_CORS_LIST if settings.APP_CORS != "*" else ["*"],
    allow_credentials=True if settings.APP_CORS != "*" else False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CreateTraceIdMiddleware)
app.add_middleware(ResponseTimeMiddleware)
app.include_router(router=api_router)

# Serve Vue.js build if available, fallback to vanilla frontend
frontend_dir = "frontend-vue/dist" if os.path.isdir("frontend-vue/dist") else "frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
