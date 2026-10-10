from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from pathlib import Path
import os

from app.database.session import get_db
from app.authentication.dependencies import get_current_admin
from app.models.user import User
from app.services.dataset_service import DatasetService
from app.services.storage_service import BaseStorageService
from app.schemas.dataset import DatasetResponse

router = APIRouter()

# Setup storage
BASE_DIR = Path(__file__).resolve().parents[4]
UPLOAD_DIR = BASE_DIR / "uploads" / "datasets"
dataset_service = DatasetService(UPLOAD_DIR)
storage_service = BaseStorageService(UPLOAD_DIR)

@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Upload a CSV or Excel dataset.
    Only accessible by Administrators.
    """
    # Validating file types
    if not (file.content_type == "text/csv" or
            file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and XLSX files are allowed"
        )

    try:
        # 1. Save file and get hash
        file_path, file_hash = await storage_service.save_file(file)

        # 2. Process dataset with hash check
        dataset = dataset_service.process_and_import_dataset(
            file_path=file_path,
            filename=file.filename,
            content_type=file.content_type,
            uploaded_by=current_admin.id,
            file_hash=file_hash,
            db=db
        )

        # 3. If the dataset already existed (duplicate), remove the redundant file we just saved
        if dataset.file_hash == file_hash and dataset.id is not None:
            # Check if the saved file path is different from the stored file path
            # If they are different, it means we just saved a duplicate and should remove it
            if str(file_path) != dataset.file_path:
                if os.path.exists(file_path):
                    os.remove(file_path)

        return dataset
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process dataset: {str(e)}"
        )
