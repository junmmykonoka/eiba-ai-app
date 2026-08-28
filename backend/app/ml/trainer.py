import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, log_loss
from sklearn.ensemble import HistGradientBoostingClassifier
from .data_loader import generate_synthetic_training_data
from .features import FEATURE_COLUMNS

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "keiba_model.pkl")

def get_classifier():
    # LightGBM equivalent native histogram gradient boosting
    return HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.04,
        max_leaf_nodes=31,
        max_depth=6,
        random_state=42
    )

def train_model(n_races: int = 1500) -> dict:
    """
    勾配ブースティング決定木（LightGBM同等アルゴリズム）モデルを訓練して keiba_model.pkl に保存する
    """
    print(f"Generating training data from {n_races} races...")
    X, y = generate_synthetic_training_data(n_races=n_races)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Training Gradient Boosting (Histogram) Classifier...")
    model = get_classifier()
    model.fit(X_train, y_train)

    val_preds = model.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, val_preds)
    loss = log_loss(y_val, val_preds)

    print(f"Model Training Completed! Validation AUC: {auc:.4f}, LogLoss: {loss:.4f}")

    # モデル保存
    joblib.dump(model, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")

    return {
        "status": "success",
        "sample_count": len(X),
        "val_auc": float(auc),
        "val_loss": float(loss),
        "model_path": MODEL_PATH
    }

if __name__ == "__main__":
    train_model()
