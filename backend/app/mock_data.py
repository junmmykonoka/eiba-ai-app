from typing import List, Dict, Any

MOCK_RACES: List[Dict[str, Any]] = [
    {
        "id": "202405021211",
        "race_name": "第91回 日本ダービー (G1)",
        "race_number": 11,
        "race_date": "2024-05-26",
        "course": "東京",
        "track_type": "芝",
        "distance": 2400,
        "weather": "晴",
        "track_condition": "良",
        "start_time": "15:40",
        "race_class": "G1",
        "entries": [
            {
                "bracket_number": 1, "horse_number": 1, "horse_name": "サンライズアース",
                "sex_age": "牡3", "jockey_name": "池添謙一", "impost": 57.0,
                "trainer_name": "石坂公一", "horse_weight": 508, "weight_diff": 4,
                "odds": 78.4, "popularity": 14, "ai_pred_score": 0.08, "ai_pred_rank": 12
            },
            {
                "bracket_number": 1, "horse_number": 2, "horse_name": "レガレイラ",
                "sex_age": "牝3", "jockey_name": "C.ルメール", "impost": 55.0,
                "trainer_name": "木村哲也", "horse_weight": 462, "weight_diff": 2,
                "odds": 4.2, "popularity": 2, "ai_pred_score": 0.28, "ai_pred_rank": 2
            },
            {
                "bracket_number": 2, "horse_number": 3, "horse_name": "ジューンテイク",
                "sex_age": "牡3", "jockey_name": "藤岡佑介", "impost": 57.0,
                "trainer_name": "武英智", "horse_weight": 492, "weight_diff": -2,
                "odds": 95.1, "popularity": 15, "ai_pred_score": 0.05, "ai_pred_rank": 15
            },
            {
                "bracket_number": 2, "horse_number": 4, "horse_name": "ミスタージーティー",
                "sex_age": "牡3", "jockey_name": "坂井瑠星", "impost": 57.0,
                "trainer_name": "矢作芳人", "horse_weight": 476, "weight_diff": 0,
                "odds": 62.3, "popularity": 12, "ai_pred_score": 0.09, "ai_pred_rank": 10
            },
            {
                "bracket_number": 3, "horse_number": 5, "horse_name": "ダノンデサイル",
                "sex_age": "牡3", "jockey_name": "横山典弘", "impost": 57.0,
                "trainer_name": "安田翔伍", "horse_weight": 504, "weight_diff": 2,
                "odds": 46.6, "popularity": 9, "ai_pred_score": 0.22, "ai_pred_rank": 3
            },
            {
                "bracket_number": 3, "horse_number": 6, "horse_name": "コスモキュランダ",
                "sex_age": "牡3", "jockey_name": "M.デムーロ", "impost": 57.0,
                "trainer_name": "加藤士津八", "horse_weight": 500, "weight_diff": -4,
                "odds": 14.8, "popularity": 6, "ai_pred_score": 0.16, "ai_pred_rank": 5
            },
            {
                "bracket_number": 4, "horse_number": 7, "horse_name": "シュガークン",
                "sex_age": "牡3", "jockey_name": "武豊", "impost": 57.0,
                "trainer_name": "清水久詞", "horse_weight": 502, "weight_diff": 0,
                "odds": 18.2, "popularity": 7, "ai_pred_score": 0.12, "ai_pred_rank": 8
            },
            {
                "bracket_number": 4, "horse_number": 8, "horse_name": "アーバンシック",
                "sex_age": "牡3", "jockey_name": "横山武史", "impost": 57.0,
                "trainer_name": "武井亮", "horse_weight": 510, "weight_diff": 2,
                "odds": 9.5, "popularity": 4, "ai_pred_score": 0.19, "ai_pred_rank": 4
            },
            {
                "bracket_number": 5, "horse_number": 9, "horse_name": "ダノンエアズロック",
                "sex_age": "牡3", "jockey_name": "J.モレイラ", "impost": 57.0,
                "trainer_name": "堀宣行", "horse_weight": 498, "weight_diff": -2,
                "odds": 12.1, "popularity": 5, "ai_pred_score": 0.14, "ai_pred_rank": 6
            },
            {
                "bracket_number": 5, "horse_number": 10, "horse_name": "サンライズジパング",
                "sex_age": "牡3", "jockey_name": "菅原明良", "impost": 57.0,
                "trainer_name": "音無秀孝", "horse_weight": 512, "weight_diff": 6,
                "odds": 55.4, "popularity": 11, "ai_pred_score": 0.07, "ai_pred_rank": 13
            },
            {
                "bracket_number": 6, "horse_number": 11, "horse_name": "シュバルツクーゲル",
                "sex_age": "牡3", "jockey_name": "北村友一", "impost": 57.0,
                "trainer_name": "鹿戸雄一", "horse_weight": 488, "weight_diff": 0,
                "odds": 156.0, "popularity": 17, "ai_pred_score": 0.03, "ai_pred_rank": 17
            },
            {
                "bracket_number": 6, "horse_number": 12, "horse_name": "シックスペンス",
                "sex_age": "牡3", "jockey_name": "川田将雅", "impost": 57.0,
                "trainer_name": "国枝栄", "horse_weight": 490, "weight_diff": -2,
                "odds": 5.8, "popularity": 3, "ai_pred_score": 0.13, "ai_pred_rank": 7
            },
            {
                "bracket_number": 7, "horse_number": 13, "horse_name": "シンエンペラー",
                "sex_age": "牡3", "jockey_name": "坂井瑠星", "impost": 57.0,
                "trainer_name": "矢作芳人", "horse_weight": 482, "weight_diff": -4,
                "odds": 21.5, "popularity": 8, "ai_pred_score": 0.11, "ai_pred_rank": 9
            },
            {
                "bracket_number": 7, "horse_number": 14, "horse_name": "ゴンバデカーブース",
                "sex_age": "牡3", "jockey_name": "松山弘平", "impost": 57.0,
                "trainer_name": "堀宣行", "horse_weight": 460, "weight_diff": 2,
                "odds": 48.9, "popularity": 10, "ai_pred_score": 0.06, "ai_pred_rank": 14
            },
            {
                "bracket_number": 7, "horse_number": 15, "horse_name": "ジャスティンミラノ",
                "sex_age": "牡3", "jockey_name": "戸崎圭太", "impost": 57.0,
                "trainer_name": "友道康夫", "horse_weight": 512, "weight_diff": 0,
                "odds": 2.2, "popularity": 1, "ai_pred_score": 0.35, "ai_pred_rank": 1
            },
            {
                "bracket_number": 8, "horse_number": 16, "horse_name": "ショウナンラプンタ",
                "sex_age": "牡3", "jockey_name": "鮫島克駿", "impost": 57.0,
                "trainer_name": "高野友和", "horse_weight": 530, "weight_diff": 4,
                "odds": 72.0, "popularity": 13, "ai_pred_score": 0.08, "ai_pred_rank": 11
            },
            {
                "bracket_number": 8, "horse_number": 17, "horse_name": "ビザンチンドリーム",
                "sex_age": "牡3", "jockey_name": "西村淳也", "impost": 57.0,
                "trainer_name": "坂口智康", "horse_weight": 454, "weight_diff": -2,
                "odds": 128.5, "popularity": 16, "ai_pred_score": 0.04, "ai_pred_rank": 16
            },
            {
                "bracket_number": 8, "horse_number": 18, "horse_name": "エコロヴァルツ",
                "sex_age": "牡3", "jockey_name": "岩田康誠", "impost": 57.0,
                "trainer_name": "牧浦充徳", "horse_weight": 484, "weight_diff": 2,
                "odds": 175.2, "popularity": 18, "ai_pred_score": 0.02, "ai_pred_rank": 18
            }
        ]
    },
    {
        "id": "202406050811",
        "race_name": "第69回 有馬記念 (G1)",
        "race_number": 11,
        "race_date": "2024-12-22",
        "course": "中山",
        "track_type": "芝",
        "distance": 2500,
        "weather": "晴",
        "track_condition": "良",
        "start_time": "15:25",
        "race_class": "G1",
        "entries": [
            {
                "bracket_number": 1, "horse_number": 1, "horse_name": "ドウデュース",
                "sex_age": "牡5", "jockey_name": "武豊", "impost": 58.0,
                "trainer_name": "友道康夫", "horse_weight": 506, "weight_diff": 2,
                "odds": 2.8, "popularity": 1, "ai_pred_score": 0.38, "ai_pred_rank": 1
            },
            {
                "bracket_number": 2, "horse_number": 2, "horse_name": "ジャスティンパレス",
                "sex_age": "牡5", "jockey_name": "坂井瑠星", "impost": 58.0,
                "trainer_name": "杉山晴紀", "horse_weight": 472, "weight_diff": -2,
                "odds": 6.5, "popularity": 3, "ai_pred_score": 0.20, "ai_pred_rank": 3
            },
            {
                "bracket_number": 3, "horse_number": 3, "horse_name": "ベラジオオペラ",
                "sex_age": "牡4", "jockey_name": "横山和生", "impost": 58.0,
                "trainer_name": "上村洋行", "horse_weight": 508, "weight_diff": 4,
                "odds": 8.9, "popularity": 4, "ai_pred_score": 0.17, "ai_pred_rank": 4
            },
            {
                "bracket_number": 4, "horse_number": 4, "horse_name": "スターズオンアース",
                "sex_age": "牝5", "jockey_name": "川田将雅", "impost": 56.0,
                "trainer_name": "高柳瑞樹", "horse_weight": 494, "weight_diff": 0,
                "odds": 5.1, "popularity": 2, "ai_pred_score": 0.25, "ai_pred_rank": 2
            }
        ]
    }
]
