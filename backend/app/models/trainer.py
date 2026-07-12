import os
import pickle

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss, brier_score_loss
from sklearn.calibration import calibration_curve
import xgboost as xgb


MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")


class ModelTrainer:
    def __init__(self):
        self.models: dict[str, object] = {}
        self._metrics: dict[str, dict] = {}

    def get_metrics(self, model_name: str = "") -> dict:
        if model_name:
            return self._metrics.get(model_name, {})
        return self._metrics

    def save(self, path: str = "") -> str:
        if not path:
            os.makedirs(MODEL_DIR, exist_ok=True)
            path = os.path.join(MODEL_DIR, "trainer.pkl")
        with open(path, "wb") as f:
            pickle.dump(self, f)
        return path

    @staticmethod
    def load(path: str = "") -> "ModelTrainer":
        if not path:
            path = os.path.join(MODEL_DIR, "trainer.pkl")
        if not os.path.exists(path):
            return ModelTrainer()
        with open(path, "rb") as f:
            return pickle.load(f)

    def train_moneyline(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: list[str] | None = None,
        model_name: str = "moneyline",
    ) -> dict:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )

        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,
        )

        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )

        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)

        accuracy = float(np.mean(y_pred == y_test))
        loss = float(log_loss(y_test, y_prob))
        brier = float(brier_score_loss(y_test, y_prob))

        prob_true, prob_pred = calibration_curve(y_test, y_prob, n_bins=10)
        calib_error = float(np.mean(np.abs(prob_true - prob_pred)))

        feat_imp = {}
        if feature_names:
            imp = model.feature_importances_
            feat_imp = dict(zip(feature_names, [float(v) for v in imp]))

        self.models[model_name] = model
        self._metrics[model_name] = {
            "accuracy": accuracy,
            "log_loss": loss,
            "brier_score": brier,
            "calibration_error": calib_error,
            "n_train": len(X_train),
            "n_test": len(X_test),
            "calibration": {
                "prob_true": prob_true.tolist(),
                "prob_pred": prob_pred.tolist(),
            },
        }

        return self._metrics[model_name]

    def train_total_runs(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: list[str] | None = None,
        model_name: str = "total_runs",
    ) -> dict:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )

        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="rmse",
            random_state=42,
        )

        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )

        y_pred = model.predict(X_test)
        rmse = float(np.sqrt(np.mean((y_test - y_pred) ** 2)))
        mae = float(np.mean(np.abs(y_test - y_pred)))

        feat_imp = {}
        if feature_names:
            imp = model.feature_importances_
            feat_imp = dict(zip(feature_names, [float(v) for v in imp]))

        self.models[model_name] = model
        self._metrics[model_name] = {
            "rmse": rmse,
            "mae": mae,
            "n_train": len(X_train),
            "n_test": len(X_test),
        }

        return self._metrics[model_name]

    def predict_proba(self, X: np.ndarray, model_name: str = "moneyline") -> np.ndarray:
        model = self.models.get(model_name)
        if model is None:
            raise ValueError(f"Model '{model_name}' not trained yet")
        return model.predict_proba(X)[:, 1]

    def predict(self, X: np.ndarray, model_name: str = "total_runs") -> np.ndarray:
        model = self.models.get(model_name)
        if model is None:
            raise ValueError(f"Model '{model_name}' not trained yet")
        return model.predict(X)
