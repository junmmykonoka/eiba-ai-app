import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from .features import extract_features_from_race, FEATURE_COLUMNS
from .trainer import MODEL_PATH, train_model

class KeibaPredictor:
    def __init__(self):
        self.model = None
        self._load_or_train_model()

    def _load_or_train_model(self):
        if not os.path.exists(MODEL_PATH):
            print("Model not found. Triggering initial model training...")
            train_model(n_races=1200)
        
        try:
            self.model = joblib.load(MODEL_PATH)
            print(f"Loaded LightGBM model from {MODEL_PATH}")
        except Exception as e:
            print(f"Failed to load model: {e}. Retraining...")
            train_model(n_races=1200)
            self.model = joblib.load(MODEL_PATH)

    def predict_race(self, race_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        出馬表データから各馬の好走確率・期待値・予想印を算出する
        """
        entries = race_dict.get("entries", [])
        if not entries or len(entries) == 0:
            return []

        # 特徴量抽出
        df_features = extract_features_from_race(race_dict)
        if df_features.empty:
            return entries

        # モデル推論 (Top-3好走確率)
        X = df_features[FEATURE_COLUMNS]
        raw_probs = self.model.predict_proba(X)[:, 1]

        # 単勝勝率に正規化（ソフトマックス / 正規化）
        prob_sum = np.sum(raw_probs)
        normalized_probs = raw_probs / max(prob_sum, 1e-6)

        results = []
        for idx, e in enumerate(entries):
            p = float(normalized_probs[idx])
            odds = float(e.get("odds") or 20.0)
            
            # 期待値 = 予測勝率 × 単勝オッズ (1.0を超えれば期待値プラス)
            expected_roi = float(p * odds)

            results.append({
                "entry_id": e.get("id"),
                "horse_number": e.get("horse_number"),
                "horse_name": e.get("horse_name"),
                "odds": odds,
                "popularity": e.get("popularity"),
                "ai_pred_score": round(p, 4), # 例: 0.2835 (28.35%)
                "expected_value": round(expected_roi, 2), # 例: 1.35
                "raw_prob": float(raw_probs[idx])
            })

        # 総合スコア（勝率と期待値のハイブリッド）でランキング
        # 総合順位
        results.sort(key=lambda x: (x["ai_pred_score"] * 0.7 + (min(x["expected_value"], 2.5) / 2.5) * 0.3), reverse=True)
        
        # 予想印の付与ロジック
        # 1位: ◎ (本命)
        # 2位: ◯ (対抗)
        # オッズ8倍以上で期待値最高馬: ▲ (単穴・推奨穴馬)
        assigned_ana = False
        
        for rank, item in enumerate(results, start=1):
            item["ai_pred_rank"] = rank

        # 穴馬(▲)の選定
        for item in results:
            if item["odds"] >= 8.0 and item["expected_value"] >= 1.05 and not assigned_ana and item["ai_pred_rank"] > 2:
                item["ai_mark"] = "▲"
                assigned_ana = True
                break

        for item in results:
            if "ai_mark" not in item:
                if item["ai_pred_rank"] == 1:
                    item["ai_mark"] = "◎"
                elif item["ai_pred_rank"] == 2:
                    item["ai_mark"] = "◯"
                elif item["ai_pred_rank"] == 3 and not assigned_ana:
                    item["ai_mark"] = "▲"
                elif item["ai_pred_rank"] <= 5:
                    item["ai_mark"] = "△"
                else:
                    item["ai_mark"] = "-"

        # 馬番順に並び戻して返す（または呼び出し側で利用）
        results.sort(key=lambda x: x["horse_number"])
        return results
