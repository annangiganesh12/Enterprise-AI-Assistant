from pathlib import Path
import hashlib
from uuid import uuid4
from fastapi import UploadFile

class BaseStorageService:
    def __init__(self, base_upload_dir: Path):
        self.base_upload_dir = base_upload_dir
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: UploadFile, sub_dir: str = "") -> tuple[Path, str]:
        """
        Saves an uploaded file to the filesystem and returns the path and SHA-256 hash.
        If a file with the same hash already exists in the directory, returns the existing path.
        """
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()

        # Resolve directory
        target_dir = self.base_upload_dir / sub_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # Check if any existing file in this directory has the same hash
        # We search for files that match the hash pattern if stored that way,
        # but since we use uuid_filename, we must check file contents or
        # rely on the database. However, to prevent physical duplicates:
        for existing_file in target_dir.iterdir():
            if existing_file.is_file():
                # Fast check: if we stored hash in filename, we'd check that.
                # Since we didn't, we calculate hash of existing files.
                # Optimization: Only check files of similar size.
                if existing_file.stat().st_size == len(content):
                    with existing_file.open("rb") as f:
                        if hashlib.sha256(f.read()).hexdigest() == file_hash:
                            return existing_file, file_hash

        # Generate unique filename
        unique_filename = f"{uuid4()}_{file.filename}"
        file_path = target_dir / unique_filename

        with file_path.open("wb") as buffer:
            buffer.write(content)

        return file_path, file_hash
