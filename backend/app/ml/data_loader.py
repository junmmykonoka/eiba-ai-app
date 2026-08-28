import numpy as np
import pandas as pd
from typing import Tuple
from .features import FEATURE_COLUMNS

def generate_synthetic_training_data(n_races: int = 1500) -> Tuple[pd.DataFrame, pd.Series]:
    """
    機械学習モデルの初期学習用データセット（JRAの統計的分布に基づいた1500レース分のデータ）を生成する
    """
    np.random.seed(42)
    rows = []
    targets = []

    courses = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] # 東京, 中山, 京都, etc.
    distances = [1200, 1400, 1600, 1800, 2000, 2200, 2400, 2500, 3000]

    for race_idx in range(n_races):
        total_horses = np.random.choice([14, 15, 16, 17, 18], p=[0.1, 0.1, 0.3, 0.2, 0.3])
        dist = float(np.random.choice(distances))
        track_type = int(np.random.choice([0, 1], p=[0.7, 0.3])) # 芝70%, ダート30%
        course = int(np.random.choice(courses))
        weather = int(np.random.choice([0, 1, 2], p=[0.7, 0.2, 0.1]))
        condition = int(np.random.choice([0, 1, 2], p=[0.75, 0.15, 0.1]))

        # オッズのシミュレーション（典型的な競馬のオッズ分布）
        # 1番人気: 2.0-4.0倍, 2番人気: 3.5-7.0倍, ..., 穴馬: 50-200倍
        raw_odds = []
        for i in range(total_horses):
            base = np.exp(np.random.normal(loc=1.2 + i * 0.25, scale=0.3))
            raw_odds.append(max(base, 1.4))
        raw_odds.sort()

        # 各馬の実力スコア（オッズ・騎手・枠順・馬体重などの潜在値）
        abilities = []
        for i in range(total_horses):
            pop = i + 1
            odds = raw_odds[i]
            waku = min(int((i / total_horses) * 8) + 1, 8)
            uma = i + 1
            rel_horse_num = uma / total_horses
            is_inner = 1.0 if waku <= 3 else 0.0
            is_outer = 1.0 if waku >= 7 else 0.0
            impost = float(np.random.choice([54.0, 55.0, 56.0, 57.0, 58.0]))
            weight = float(np.random.normal(loc=485, scale=20))
            weight_diff = float(np.random.choice([-6, -4, -2, 0, 2, 4, 6], p=[0.05, 0.15, 0.25, 0.3, 0.15, 0.08, 0.02]))
            sex = int(np.random.choice([0, 1, 2], p=[0.65, 0.3, 0.05]))
            age = int(np.random.choice([3, 4, 5, 6, 7], p=[0.35, 0.35, 0.18, 0.08, 0.04]))
            
            # 騎手スコア
            j_score = float(np.random.choice([0.52, 0.38, 0.32, 0.26, 0.18], p=[0.1, 0.2, 0.3, 0.25, 0.15]))
            t_score = float(np.random.choice([0.40, 0.34, 0.28, 0.22, 0.15], p=[0.1, 0.2, 0.3, 0.25, 0.15]))

            implied_prob = 1.0 / odds
            log_odds = np.log(odds)
            weight_impost_ratio = impost / weight

            # 実際のレース好走潜在スコア（ノイズを含む）
            true_ability = (
                (implied_prob * 4.0) +
                (j_score * 1.5) +
                (t_score * 1.2) +
                (is_inner * 0.15 if dist >= 2000 else 0.0) -
                (abs(weight_diff) * 0.03) +
                np.random.gumbel(loc=0, scale=0.45) # 極値分布のノイズ
            )

            abilities.append((true_ability, {
                "bracket_number": waku,
                "horse_number": uma,
                "rel_horse_num": rel_horse_num,
                "is_inner_waku": is_inner,
                "is_outer_waku": is_outer,
                "impost": impost,
                "odds": odds,
                "log_odds": log_odds,
                "implied_prob": implied_prob,
                "popularity": pop,
                "horse_weight": weight,
                "weight_diff": weight_diff,
                "weight_impost_ratio": weight_impost_ratio,
                "distance": dist,
                "track_type_code": track_type,
                "course_code": course,
                "weather_code": weather,
                "condition_code": condition,
                "sex_code": sex,
                "age": age,
                "jockey_score": j_score,
                "trainer_score": t_score,
                "total_horses": total_horses
            }))

        # 順位決定（Top3を好走とする）
        abilities.sort(key=lambda x: x[0], reverse=True)
        for rank, (ability, row_dict) in enumerate(abilities, start=1):
            rows.append(row_dict)
            targets.append(1 if rank <= 3 else 0)

    X = pd.DataFrame(rows)[FEATURE_COLUMNS]
    y = pd.Series(targets)
    return X, y
