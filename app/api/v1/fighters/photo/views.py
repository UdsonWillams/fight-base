"""
Endpoints para gerenciar fotos de lutadores.
"""

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.v1.auth.firebase_dependencies import get_current_user
from app.database.repositories.fighter_firestore import FighterFirestoreRepository
from app.schemas.auth import AuthenticatedUser
from app.services.cloud_storage import CloudStorageService, get_storage_service
from app.services.domain.fighter_photo import FighterPhotoService

router = APIRouter(prefix="/fighters", tags=["Fighter Photos"])


def get_fighter_photo_service(
    fighter_repo: FighterFirestoreRepository = Depends(
        lambda: FighterFirestoreRepository()
    ),
    storage: CloudStorageService = Depends(get_storage_service),
) -> FighterPhotoService:
    """Dependency para obter service de fotos de lutadores."""
    return FighterPhotoService(fighter_repo, storage)


@router.post(
    "/{fighter_id}/photo",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Upload de foto do lutador",
)
async def upload_fighter_photo(
    fighter_id: str,
    file: UploadFile = File(..., description="Arquivo de imagem (JPEG, PNG, WEBP)"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: FighterPhotoService = Depends(get_fighter_photo_service),
):
    """
    Faz upload de uma foto para um lutador.

    Validações:
    - Apenas criador do lutador ou admin pode adicionar fotos
    - Tamanho máximo: 5MB
    - Formatos aceitos: JPEG, PNG, WEBP

    A foto é salva no Cloud Storage e a URL é adicionada ao lutador.
    """
    return await service.upload_photo(fighter_id, file, current_user)


@router.delete(
    "/{fighter_id}/photo",
    response_model=dict,
    summary="Remover foto principal do lutador",
)
async def delete_fighter_photo(
    fighter_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: FighterPhotoService = Depends(get_fighter_photo_service),
):
    """
    Remove a foto principal de um lutador.

    Validações:
    - Apenas criador do lutador ou admin pode remover fotos

    A foto é deletada do Cloud Storage e a URL é removida do lutador.
    """
    return await service.delete_photo(fighter_id, current_user)


@router.get(
    "/{fighter_id}/photos",
    response_model=dict,
    summary="Listar todas as fotos de um lutador",
)
async def list_fighter_photos(
    fighter_id: str,
    service: FighterPhotoService = Depends(get_fighter_photo_service),
):
    """
    Lista todas as fotos de um lutador específico.

    Retorna:
    - photo_url: Foto principal atual
    - photo_urls: Todas as fotos já enviadas
    - storage_photos: Fotos encontradas no Cloud Storage (pode incluir fotos antigas)
    """
    return await service.list_photos(fighter_id)
