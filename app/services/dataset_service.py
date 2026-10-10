import pandas as pd
from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from pathlib import Path
from uuid import uuid4

class DatasetService:
    def process_and_import_dataset(self, db: Session,file_path: Path, filename: str, content_type: str, uploaded_by: int, file_hash: str, is_global: bool = False):
        """
        Processes a tabular file (CSV/XLSX) already saved to disk and imports it into a SQL table.
        If a dataset with the same hash already exists, it reuses the existing record.
        """
        # 1. Check for duplicate based on content hash
        existing_dataset = db.query(Dataset).filter(Dataset.file_hash == file_hash).first()
        if existing_dataset:
            return existing_dataset

        # 2. Read from disk to avoid issues with file pointers
        if "csv" in content_type:
            df = pd.read_csv(file_path)
        elif "spreadsheetml" in content_type or "excel" in content_type:
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file type. Please upload CSV or XLSX.")

        # Data Sanitization: Clean column names for SQL
        df.columns = [col.strip().replace(" ", "_").replace("-", "_").lower() for col in df.columns]

        # Generate unique table name
        table_name = f"dataset_{uuid4().hex[:8]}"

        # Import to SQL
        engine = db.get_bind()
        df.to_sql(table_name, con=engine, if_exists="replace", index=False)

        # Save metadata
        dataset = Dataset(
            name=filename,
            file_path=str(file_path),
            table_name=table_name,
            uploaded_by=uploaded_by,
            file_hash=file_hash,
            is_global=is_global
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        return dataset
