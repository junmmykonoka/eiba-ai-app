import re
import numpy as np
import pandas as pd
from typing import Dict, Any, List

# 騎手・調教師の基本レーティング辞書（実績複勝率ベース）
TOP_JOCKEYS = {
    "ルメール": 0.52, "C.ルメール": 0.52, "川田将雅": 0.50, "川田": 0.50,
    "モレイラ": 0.55, "J.モレイラ": 0.55, "レーン": 0.53, "D.レーン": 0.53,
    "坂井瑠星": 0.38, "武豊": 0.36, "横山武史": 0.35, "戸崎圭太": 0.36,
    "松山弘平": 0.33, "鮫島克駿": 0.30, "岩田望来": 0.32, "西村淳也": 0.31,
    "デムーロ": 0.33, "M.デムーロ": 0.33, "横山典弘": 0.32, "菅原明良": 0.29,
    "田辺裕信": 0.28, "津村明秀": 0.27, "三浦皇成": 0.26, "池添謙一": 0.28
}

TOP_TRAINERS = {
    "矢作芳人": 0.38, "友道康夫": 0.37, "木村哲也": 0.40, "杉山晴紀": 0.36,
    "中内田充": 0.42, "国枝栄": 0.34, "堀宣行": 0.37, "手塚貴久": 0.33,
    "宮田敬介": 0.34, "鹿戸雄一": 0.30, "安田翔伍": 0.32, "高野友和": 0.31,
    "斉藤崇史": 0.33, "武英智": 0.30, "上村洋行": 0.32, "音無秀孝": 0.29
}

COURSE_MAP = {
    "東京": 0, "中山": 1, "京都": 2, "阪神": 3, "中京": 4,
    "新潟": 5, "福島": 6, "小倉": 7, "札幌": 8, "函館": 9
}

def extract_horse_age_sex(sex_age_str: str):
    sex_code = 0 # 牡
    if "牝" in sex_age_str:
        sex_code = 1
    elif "セ" in sex_age_str or "せん" in sex_age_str:
        sex_code = 2

    m = re.search(r"(\d+)", sex_age_str)
    age = int(m.group(1)) if m else 4
    return sex_code, age

def extract_features_from_race(race_dict: Dict[str, Any]) -> pd.DataFrame:
    """
    1つのレース情報とその出走馬一覧から機械学習用の特徴量DataFrameを生成する
    """
    entries = race_dict.get("entries", [])
    if not entries:
        return pd.DataFrame()

    distance = float(race_dict.get("distance", 2000))
    track_type = race_dict.get("track_type", "芝")
    track_type_code = 1 if "ダ" in track_type else (2 if "障" in track_type else 0)
    
    course_name = race_dict.get("course", "東京")
    course_code = COURSE_MAP.get(course_name, 0)

    weather = race_dict.get("weather", "晴")
    weather_code = 0 if "晴" in weather else (1 if "曇" in weather else (2 if "雨" in weather else 3))

    condition = race_dict.get("track_condition", "良")
    condition_code = 0 if "良" in condition else (1 if "稍" in condition else (2 if "重" in condition else 3))

    total_horses = len(entries)

    rows = []
    for e in entries:
        odds = float(e.get("odds") or 25.0)
        pop = int(e.get("popularity") or 10)
        impost = float(e.get("impost") or 57.0)
        weight = float(e.get("horse_weight") or 480.0)
        weight_diff = float(e.get("weight_diff") or 0.0)
        waku = int(e.get("bracket_number") or 1)
        uma = int(e.get("horse_number") or 1)

        sex_code, age = extract_horse_age_sex(e.get("sex_age", "牡3"))

        # 関係者スコア
        j_name = e.get("jockey_name", "")
        j_score = 0.20 # default
        for k, v in TOP_JOCKEYS.items():
            if k in j_name:
                j_score = v
                break

        t_name = e.get("trainer_name", "")
        t_score = 0.20 # default
        for k, v in TOP_TRAINERS.items():
            if k in t_name:
                t_score = v
                break

        # 合成特徴量
        implied_prob = 1.0 / max(odds, 1.01)
        log_odds = np.log(max(odds, 1.01))
        weight_impost_ratio = impost / max(weight, 350.0)
        is_inner = 1.0 if waku <= 3 else 0.0
        is_outer = 1.0 if waku >= 7 else 0.0
        rel_horse_num = uma / max(total_horses, 1)

        rows.append({
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
            "distance": distance,
            "track_type_code": track_type_code,
            "course_code": course_code,
            "weather_code": weather_code,
            "condition_code": condition_code,
            "sex_code": sex_code,
            "age": age,
            "jockey_score": j_score,
            "trainer_score": t_score,
            "total_horses": total_horses
        })

    return pd.DataFrame(rows)

FEATURE_COLUMNS = [
    "bracket_number", "horse_number", "rel_horse_num", "is_inner_waku", "is_outer_waku",
    "impost", "odds", "log_odds", "implied_prob", "popularity",
    "horse_weight", "weight_diff", "weight_impost_ratio", "distance",
    "track_type_code", "course_code", "weather_code", "condition_code",
    "sex_code", "age", "jockey_score", "trainer_score", "total_horses"
]
