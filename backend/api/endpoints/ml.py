from datetime import datetime
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from ...database.session import get_session
from ...schemas.packet import MLModelResponse
from ...repositories.threat_repository import MLModelRepository
from ...middleware.auth_middleware import get_current_user, require_roles

router = APIRouter()

def get_pipeline():
    try:
        from ...ml.pipeline import MLPipeline
        return MLPipeline()
    except ImportError as e:
        from fastapi.exceptions import HTTPException
        raise HTTPException(
            status_code=501,
            detail=f"ML dependencies not available in this environment: {e}. Install pandas, numpy, scikit-learn, xgboost."
        )


@router.get("/models", response_model=List[MLModelResponse])
async def list_models(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    repo = MLModelRepository(session)
    models, _ = await repo.get_all(limit=100, order_by="created_at", order_desc=True)
    return [MLModelResponse.model_validate(m) for m in models]


@router.get("/models/active", response_model=Optional[MLModelResponse])
async def get_active_model(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    repo = MLModelRepository(session)
    model = await repo.get_active_model()
    if not model:
        return None
    return MLModelResponse.model_validate(model)


@router.post("/train")
async def train_model(
    dataset_path: str = Query(..., description="Path to training dataset"),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(require_roles(["admin"])),
    session: AsyncSession = Depends(get_session),
):
    import os
    if not os.path.isfile(dataset_path):
        from fastapi.exceptions import HTTPException
        raise HTTPException(status_code=400, detail=f"Dataset file not found: {dataset_path}")

    repo = MLModelRepository(session)

    pipeline = get_pipeline()
    try:
        df = pipeline.load_dataset(dataset_path)
        df = pipeline.clean_data(df)
        X, y = pipeline.preprocess(df)

        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        results = pipeline.train_models(X_train, y_train)
        best_name = pipeline.select_best_model(results)
        best_model = results[best_name]["model"]

        metrics = pipeline.evaluate(best_model, X_test, y_test)

        model_path = os.path.join("trained_models", f"model_{best_name}.pkl")
        pipeline.save_model(best_model, model_path)

        ml_model = await repo.create(
            name=f"Model_{best_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            model_type=best_name,
            version="1.0.0",
            file_path=model_path,
            metrics=metrics,
            accuracy=metrics.get("accuracy"),
            precision_macro=metrics.get("precision_macro"),
            recall_macro=metrics.get("recall_macro"),
            f1_macro=metrics.get("f1_macro"),
            roc_auc=metrics.get("roc_auc"),
            confusion_matrix=metrics.get("confusion_matrix"),
            training_dataset=dataset_path,
            training_samples=len(X_train),
            is_trained=True,
            is_active=True,
            feature_columns=pipeline.feature_columns,
        )

        await repo.deactivate_all()
        ml_model.is_active = True
        await session.flush()

        return {
            "message": "Model trained successfully",
            "model_id": str(ml_model.id),
            "model_type": best_name,
            "metrics": metrics,
        }
    except HTTPException:
        raise
    except Exception as e:
        from ...middleware.error_handler import AppException
        raise AppException(message=str(e), status_code=500)


@router.post("/predict")
async def predict_from_flow(
    flow_data: dict,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    pipeline = get_pipeline()
    try:
        from ...feature_engine.extractor import FeatureExtractor
        extractor = FeatureExtractor()
        features = extractor.extract_from_flow(flow_data)

        import pandas as pd
        df = pd.DataFrame([features])
        result = pipeline.predict(df)

        return {
            "predicted_label": result["predicted_label"],
            "confidence": result["confidence"],
            "is_threat": result["is_threat"],
            "features_used": pipeline.feature_columns,
        }
    except Exception as e:
        from ...middleware.error_handler import AppException
        raise AppException(message=str(e), status_code=500)


@router.post("/models/{model_id}/activate")
async def activate_model(
    model_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_roles(["admin"])),
):
    pipeline = get_pipeline()
    repo = MLModelRepository(session)
    model = await repo.get(model_id)
    if not model:
        from ...middleware.error_handler import NotFoundException
        raise NotFoundException("Model", model_id)

    await repo.deactivate_all()
    model.is_active = True
    await session.flush()

    try:
        pipeline.load_model(model.file_path)
    except Exception:
        pass

    return {"message": f"Model {model_id} activated"}
