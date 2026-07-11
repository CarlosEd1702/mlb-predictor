import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss, brier_score_loss
from sklearn.calibration import calibration_curve
import xgboost as xgb


class ModelTrainer:
    def __init__(self):
        self.models: dict[str, xgb.XGBClassifier] = {}

    def train_moneyline(
        self,
        X: np.ndarray,
        y: np.ndarray,
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

        accuracy = np.mean(y_pred == y_test)
        loss = log_loss(y_test, y_prob)
        brier = brier_score_loss(y_test, y_prob)

        prob_true, prob_pred = calibration_curve(y_test, y_prob, n_bins=10)

        self.models[model_name] = model

        return {
            "accuracy": float(accuracy),
            "log_loss": float(loss),
            "brier_score": float(brier),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "calibration": {
                "prob_true": prob_true.tolist(),
                "prob_pred": prob_pred.tolist(),
            },
        }

    def train_total_runs(
        self,
        X: np.ndarray,
        y: np.ndarray,
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

        self.models[model_name] = model

        return {
            "rmse": rmse,
            "mae": mae,
            "n_train": len(X_train),
            "n_test": len(X_test),
        }

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
