import re
import time
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from .client import SafeHttpClient
from .schedule import COURSE_CODE_MAP

class RaceCardScraper:
    def __init__(self, http_client: Optional[SafeHttpClient] = None):
        self.client = http_client or SafeHttpClient()

    def scrape_shutuba_by_id(self, race_id: str) -> Optional[Dict[str, Any]]:
        """
        race_id を指定して出馬表ページを取得・パースする。
        1. 過去レース・結果DB (db.netkeiba.com) を優先確認（確定オッズ・人気・調教師・馬体重が完全に入るため）
        2. 当日・直前の出馬表 (race.netkeiba.com) を確認
        """
        # 1. Try db.netkeiba.com race page
        url_db = f"https://db.netkeiba.com/race/{race_id}/"
        try:
            html_db = self.client.fetch(url_db, encoding="euc-jp")
            data_db = self.parse_db_race_html(html_db, race_id=race_id)
            if data_db and data_db.get("entries") and len(data_db["entries"]) > 0:
                return data_db
        except Exception as e:
            print(f"db.netkeiba fetch info: {e}")

        # 2. Try live race.netkeiba.com shutuba
        url_live = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
        try:
            html = self.client.fetch(url_live, encoding="euc-jp")
            data = self.parse_shutuba_html(html, race_id=race_id)
            if data and data.get("entries") and len(data["entries"]) > 0:
                return data
        except Exception as e:
            print(f"race.netkeiba fetch info: {e}")

        return None

    def parse_db_race_html(self, html: str, race_id: str = "") -> Optional[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        
        intro = soup.find("div", class_="data_intro")
        if not intro:
            return None

        # レース名
        h1 = intro.find("h1")
        race_name = h1.text.strip() if h1 else f"レース {race_id}"

        # レース番号
        race_num_span = intro.find("span", class_="race_num") or intro.find("dt")
        race_number = 11
        if race_num_span:
            m = re.search(r"(\d+)", race_num_span.text)
            if m:
                race_number = int(m.group(1))
        elif len(race_id) >= 12 and race_id[10:12].isdigit():
            race_number = int(race_id[10:12])

        # 条件・コース
        p_cond = intro.find("p")
        cond_text = p_cond.text if p_cond else ""
        
        track_type = "芝"
        if "ダ" in cond_text or "ダート" in cond_text:
            track_type = "ダート"
        elif "障" in cond_text:
            track_type = "障害"

        distance = 2000
        m_dist = re.search(r"(\d{3,4})m", cond_text)
        if m_dist:
            distance = int(m_dist.group(1))

        weather = "晴"
        m_w = re.search(r"天候\s*:\s*(\w+)", cond_text)
        if m_w:
            weather = m_w.group(1)

        track_cond = "良"
        m_c = re.search(r"(?:芝|ダート|馬場)\s*:\s*(\w+)", cond_text)
        if m_c:
            track_cond = m_c.group(1)

        start_time = "15:40"
        m_t = re.search(r"発走\s*:\s*(\d{1,2}:\d{2})", cond_text)
        if m_t:
            start_time = m_t.group(1)

        # 開催場
        course = "東京"
        if len(race_id) >= 6:
            code = race_id[4:6]
            course = COURSE_CODE_MAP.get(code, "東京")

        # クラス
        race_class = "オープン"
        for grade in ["G1", "GI", "G2", "GII", "G3", "GIII", "オープン", "OP", "3勝クラス", "2勝クラス", "1勝クラス", "新馬", "未勝利"]:
            if grade in race_name:
                race_class = grade.replace("GI", "G1").replace("GII", "G2").replace("GIII", "G3")
                break

        # 日付
        race_date = "2024-05-26"
        smalltxt = intro.find("p", class_="smalltxt")
        if smalltxt:
            m_date = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", smalltxt.text)
            if m_date:
                race_date = f"{m_date.group(1)}-{int(m_date.group(2)):02d}-{int(m_date.group(3)):02d}"

        # テーブル動的パース（カラム位置をヘッダー名から自動判定）
        entries = []
        table = soup.find("table", class_="race_table_01")
        if table:
            headers = [th.text.strip() for th in table.find_all("th")]

            def get_col_index(keywords):
                for i, h in enumerate(headers):
                    for k in keywords:
                        if k in h:
                            return i
                return -1

            idx_waku = get_col_index(["枠"])
            idx_uma = get_col_index(["馬番"])
            idx_name = get_col_index(["馬名"])
            idx_sex_age = get_col_index(["性齢"])
            idx_impost = get_col_index(["斤量"])
            idx_jockey = get_col_index(["騎手"])
            idx_odds = get_col_index(["単勝", "オッズ"])
            idx_pop = get_col_index(["人気"])
            idx_weight = get_col_index(["馬体重"])
            idx_trainer = get_col_index(["調教師"])

            rows = table.find_all("tr")[1:]  # ヘッダースキップ
            for row in rows:
                cols = row.find_all("td")
                if len(cols) <= max(idx_name, idx_uma, 3):
                    continue

                try:
                    # 枠番
                    waku = 1
                    if idx_waku >= 0 and idx_waku < len(cols):
                        txt = cols[idx_waku].text.strip()
                        if txt.isdigit(): waku = int(txt)

                    # 馬番
                    uma = 1
                    if idx_uma >= 0 and idx_uma < len(cols):
                        txt = cols[idx_uma].text.strip()
                        if txt.isdigit(): uma = int(txt)

                    # 馬名 & 馬ID
                    horse_name = ""
                    horse_id = None
                    if idx_name >= 0 and idx_name < len(cols):
                        horse_a = cols[idx_name].find("a")
                        horse_name = horse_a.text.strip() if horse_a else cols[idx_name].text.strip()
                        if horse_a and "horse/" in horse_a.get("href", ""):
                            m_h = re.search(r"horse/(\d+)", horse_a["href"])
                            if m_h: horse_id = m_h.group(1)

                    if not horse_name:
                        continue

                    # 性齢
                    sex_age = "牡3"
                    if idx_sex_age >= 0 and idx_sex_age < len(cols):
                        sex_age = cols[idx_sex_age].text.strip()

                    # 斤量
                    impost = 57.0
                    if idx_impost >= 0 and idx_impost < len(cols):
                        m_imp = re.search(r"\d+\.?\d*", cols[idx_impost].text.strip())
                        if m_imp: impost = float(m_imp.group(0))

                    # 騎手 & 騎手ID
                    jockey_name = ""
                    jockey_id = None
                    if idx_jockey >= 0 and idx_jockey < len(cols):
                        jockey_a = cols[idx_jockey].find("a")
                        jockey_name = jockey_a.text.strip() if jockey_a else cols[idx_jockey].text.strip()
                        if jockey_a and "jockey/" in jockey_a.get("href", ""):
                            m_j = re.search(r"jockey/(\d+)", jockey_a["href"])
                            if m_j: jockey_id = m_j.group(1)

                    # 調教師 & 調教師ID
                    trainer_name = "調教師"
                    trainer_id = None
                    if idx_trainer >= 0 and idx_trainer < len(cols):
                        tr_a = cols[idx_trainer].find("a")
                        raw_tr = tr_a.text.strip() if tr_a else cols[idx_trainer].text.strip()
                        # 西/東/地 などのプレフィックスを除去して綺麗にする
                        trainer_name = re.sub(r"\[.*?\]|\n|\r", "", raw_tr).strip()
                        if tr_a and "trainer/" in tr_a.get("href", ""):
                            m_t = re.search(r"trainer/(\d+)", tr_a["href"])
                            if m_t: trainer_id = m_t.group(1)

                    # 単勝オッズ
                    odds = None
                    if idx_odds >= 0 and idx_odds < len(cols):
                        txt_odds = cols[idx_odds].text.strip()
                        m_o = re.search(r"(\d+\.\d+)", txt_odds)
                        if m_o:
                            odds = float(m_o.group(1))

                    # 人気
                    popularity = None
                    if idx_pop >= 0 and idx_pop < len(cols):
                        txt_pop = cols[idx_pop].text.strip()
                        m_p = re.search(r"(\d+)", txt_pop)
                        if m_p:
                            popularity = int(m_p.group(1))

                    # 馬体重 & 増減
                    horse_weight = None
                    weight_diff = None
                    if idx_weight >= 0 and idx_weight < len(cols):
                        txt_w = cols[idx_weight].text.strip()
                        m_w = re.search(r"(\d{3})\(([\+\-]?\d+|0)\)", txt_w)
                        if m_w:
                            horse_weight = int(m_w.group(1))
                            weight_diff = int(m_w.group(2))
                        else:
                            m_w_only = re.search(r"(\d{3})", txt_w)
                            if m_w_only:
                                horse_weight = int(m_w_only.group(1))

                    entries.append({
                        "bracket_number": waku,
                        "horse_number": uma,
                        "horse_name": horse_name,
                        "horse_id": horse_id,
                        "sex_age": sex_age,
                        "jockey_name": jockey_name,
                        "jockey_id": jockey_id,
                        "impost": impost,
                        "trainer_name": trainer_name,
                        "trainer_id": trainer_id,
                        "horse_weight": horse_weight,
                        "weight_diff": weight_diff,
                        "odds": odds,
                        "popularity": popularity,
                        "ai_pred_score": None,
                        "ai_pred_rank": None
                    })
                except Exception as e:
                    print(f"Error parsing db row: {e}")
                    continue

        return {
            "id": race_id,
            "race_name": race_name,
            "race_number": race_number,
            "race_date": race_date,
            "course": course,
            "track_type": track_type,
            "distance": distance,
            "weather": weather,
            "track_condition": track_cond,
            "start_time": start_time,
            "race_class": race_class,
            "entries": entries
        }

    def parse_shutuba_html(self, html: str, race_id: str = "") -> Optional[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        race_data = self._parse_race_header(soup, race_id)
        if not race_data:
            return None
        entries = self._parse_entries(soup)
        race_data["entries"] = entries
        return race_data

    def _parse_race_header(self, soup: BeautifulSoup, race_id: str) -> Optional[Dict[str, Any]]:
        race_name_elem = soup.find("div", class_="RaceName") or soup.find("h1", class_="RaceName") or soup.find("h1")
        if not race_name_elem or not race_name_elem.text.strip():
            return None

        race_name = race_name_elem.text.strip()
        race_num_elem = soup.find("span", class_="RaceNum")
        race_number = 11
        if race_num_elem:
            m = re.search(r"(\d+)", race_num_elem.text)
            if m: race_number = int(m.group(1))

        race_data_01 = soup.find("div", class_="RaceData01")
        race_data_02 = soup.find("div", class_="RaceData02")
        text_01 = race_data_01.text if race_data_01 else ""
        text_02 = race_data_02.text if race_data_02 else ""

        start_time = "15:40"
        m_time = re.search(r"(\d{1,2}:\d{2})発走", text_01)
        if m_time: start_time = m_time.group(1)

        track_type = "芝"
        if "ダ" in text_01 or "ダート" in text_01: track_type = "ダート"
        elif "障" in text_01: track_type = "障害"

        distance = 2000
        m_dist = re.search(r"(\d{3,4})m", text_01)
        if m_dist: distance = int(m_dist.group(1))

        weather = "晴"
        m_weather = re.search(r"天候:(\w+)", text_01)
        if m_weather: weather = m_weather.group(1)

        track_condition = "良"
        m_cond = re.search(r"馬場:(\w+)", text_01)
        if m_cond: track_condition = m_cond.group(1)

        course = "東京"
        if len(race_id) >= 6:
            code = race_id[4:6]
            course = COURSE_CODE_MAP.get(code, "東京")
        else:
            for c in ["東京", "中山", "京都", "阪神", "新潟", "福島", "中京", "小倉", "札幌", "函館"]:
                if c in text_02:
                    course = c
                    break

        race_class = "オープン"
        for grade in ["G1", "G2", "G3", "オープン", "OP", "3勝クラス", "2勝クラス", "1勝クラス", "新馬", "未勝利"]:
            if grade in text_01 or grade in text_02 or grade in race_name:
                race_class = grade
                break

        race_date = "2024-05-26"
        return {
            "id": race_id if race_id else f"race_{int(time.time())}",
            "race_name": race_name,
            "race_number": race_number,
            "race_date": race_date,
            "course": course,
            "track_type": track_type,
            "distance": distance,
            "weather": weather,
            "track_condition": track_condition,
            "start_time": start_time,
            "race_class": race_class
        }

    def _parse_entries(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        entries = []
        table = soup.find("table", class_="Shutuba_Table") or soup.find("table", class_="race_table_01")
        if not table:
            return entries

        rows = table.find_all("tr", class_=re.compile(r"HorseList|tr_bg"))
        if not rows:
            rows = table.find_all("tr")[1:]

        for row in rows:
            try:
                waku_elem = row.find(class_=re.compile(r"Waku\d|waku\d|Waku"))
                bracket_num = 1
                if waku_elem:
                    m = re.search(r"(\d)", waku_elem.text.strip())
                    if m: bracket_num = int(m.group(1))

                umaban_elem = row.find(class_=re.compile(r"Umaban|umaban"))
                horse_num = 1
                if umaban_elem:
                    m = re.search(r"(\d+)", umaban_elem.text.strip())
                    if m: horse_num = int(m.group(1))

                horse_elem = row.find(class_=re.compile(r"Horse_Info|Horse_Name|horse_name|HorseInfo"))
                horse_name = ""
                horse_id = None
                if horse_elem:
                    a_tag = horse_elem.find("a")
                    if a_tag:
                        horse_name = a_tag.text.strip()
                        m_hid = re.search(r"horse/(\d+)", a_tag.get("href", "")) or re.search(r"horse/result/(\d+)", a_tag.get("href", ""))
                        if m_hid: horse_id = m_hid.group(1)
                    else:
                        horse_name = horse_elem.text.strip()

                if not horse_name:
                    continue

                sex_age_elem = row.find(class_=re.compile(r"Barei|barei"))
                sex_age = sex_age_elem.text.strip() if sex_age_elem else "牡3"

                impost_elem = row.find(class_=re.compile(r"Handicap|handicap|Txt_R"))
                impost = 57.0
                if impost_elem:
                    m_imp = re.search(r"(\d+\.?\d*)", impost_elem.text.strip())
                    if m_imp: impost = float(m_imp.group(1))

                jockey_elem = row.find(class_=re.compile(r"Jockey|jockey"))
                jockey_name = ""
                jockey_id = None
                if jockey_elem:
                    a_tag = jockey_elem.find("a")
                    if a_tag:
                        jockey_name = a_tag.text.strip()
                        m_jid = re.search(r"jockey/(\d+)", a_tag.get("href", "")) or re.search(r"jockey/result/(\d+)", a_tag.get("href", ""))
                        if m_jid: jockey_id = m_jid.group(1)
                    else:
                        jockey_name = jockey_elem.text.strip()

                trainer_elem = row.find(class_=re.compile(r"Trainer|trainer"))
                trainer_name = "調教師"
                trainer_id = None
                if trainer_elem:
                    a_tag = trainer_elem.find("a")
                    raw_tr = a_tag.text.strip() if a_tag else trainer_elem.text.strip()
                    trainer_name = re.sub(r"\[.*?\]|\n|\r", "", raw_tr).strip()
                    if a_tag:
                        m_tid = re.search(r"trainer/(\d+)", a_tag.get("href", "")) or re.search(r"trainer/result/(\d+)", a_tag.get("href", ""))
                        if m_tid: trainer_id = m_tid.group(1)

                weight_elem = row.find(class_=re.compile(r"Weight|weight"))
                horse_weight = None
                weight_diff = None
                if weight_elem:
                    m_w = re.search(r"(\d{3})\(([\+\-]?\d+|0)\)", weight_elem.text.strip())
                    if m_w:
                        horse_weight = int(m_w.group(1))
                        weight_diff = int(m_w.group(2))
                    else:
                        m_w_only = re.search(r"(\d{3})", weight_elem.text.strip())
                        if m_w_only: horse_weight = int(m_w_only.group(1))

                # オッズ & 人気
                odds = None
                popularity = None
                odds_val_elem = row.find(id=re.compile(r"odds-\d+")) or row.find(class_=re.compile(r"Popular|Odds_Ninki|odds"))
                if odds_val_elem:
                    m_odds = re.search(r"(\d+\.\d+)", odds_val_elem.text.strip())
                    if m_odds: odds = float(m_odds.group(1))

                pop_elem = row.find(class_=re.compile(r"Popular_Ninki|Ninki|ninki"))
                if pop_elem:
                    m_pop = re.search(r"(\d+)", pop_elem.text.strip())
                    if m_pop: popularity = int(m_pop.group(1))

                entries.append({
                    "bracket_number": bracket_num,
                    "horse_number": horse_num,
                    "horse_name": horse_name,
                    "horse_id": horse_id,
                    "sex_age": sex_age,
                    "jockey_name": jockey_name,
                    "jockey_id": jockey_id,
                    "impost": impost,
                    "trainer_name": trainer_name,
                    "trainer_id": trainer_id,
                    "horse_weight": horse_weight,
                    "weight_diff": weight_diff,
                    "odds": odds,
                    "popularity": popularity,
                    "ai_pred_score": None,
                    "ai_pred_rank": None
                })
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue

        return entries
