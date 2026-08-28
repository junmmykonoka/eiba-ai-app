import re
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from .client import SafeHttpClient

COURSE_CODE_MAP = {
    # JRA
    "01": "札幌", "02": "函館", "03": "福島", "04": "新潟", "05": "東京",
    "06": "中山", "07": "中京", "08": "京都", "09": "阪神", "10": "小倉",
    # NAR
    "30": "門別", "35": "門別", "36": "帯広", "42": "浦和", "43": "船橋",
    "44": "大井", "45": "川崎", "46": "金沢", "47": "笠松", "48": "名古屋",
    "50": "園田", "51": "姫路", "54": "金沢", "55": "笠松", "65": "高知", "83": "佐賀"
}

class ScheduleScraper:
    def __init__(self, http_client: SafeHttpClient = None):
        self.client = http_client or SafeHttpClient()

    def get_schedule_by_date(self, date_str: str) -> Dict[str, Any]:
        """
        date_str: 'YYYY-MM-DD' または 'YYYYMMDD'
        その日の競馬場一覧と各場の1R〜12R一覧を返す。
        1. 当日・直前の速報ページ (race.netkeiba.com/top/race_list_sub.html) を確認
        2. 過去レースデータベース (db.netkeiba.com/race/list/...) を確認
        """
        clean_date = date_str.replace("-", "").strip()
        venues_dict: Dict[str, List[Dict[str, Any]]] = {}

        # 1. Try race.netkeiba.com live schedule (直前・当日・翌日等)
        try:
            url_live = f"https://race.netkeiba.com/top/race_list_sub.html?kaisai_date={clean_date}"
            html_live = self.client.fetch(url_live, encoding="euc-jp", use_cache=False)
            soup_live = BeautifulSoup(html_live, "lxml")
            links = soup_live.find_all("a", href=re.compile(r"race_id=(\d{12})"))
            
            for a in links:
                m = re.search(r"race_id=(\d{12})", a.get("href", ""))
                if not m:
                    continue
                race_id = m.group(1)
                
                # レース名の抽出
                name_elem = a.find(class_=re.compile(r"RaceName|ItemTitle|Race_Name")) or a
                name_text = name_elem.text.strip()
                name_text = re.sub(r"^\d+R\s*", "", name_text).strip()
                if not name_text:
                    name_text = f"第{int(race_id[10:12])}レース"

                code = race_id[4:6]
                venue_name = COURSE_CODE_MAP.get(code, f"場{code}")
                race_num = int(race_id[10:12])

                if venue_name not in venues_dict:
                    venues_dict[venue_name] = []

                if not any(r["race_id"] == race_id for r in venues_dict[venue_name]):
                    venues_dict[venue_name].append({
                        "race_id": race_id,
                        "race_number": race_num,
                        "race_name": name_text.split("\n")[0].strip(),
                        "course": venue_name
                    })
        except Exception as e:
            print(f"Live schedule fetch notice: {e}")

        # 2. If not found or empty, try db.netkeiba.com archive
        if not venues_dict:
            try:
                url_db = f"https://db.netkeiba.com/race/list/{clean_date}/"
                html_db = self.client.fetch(url_db, encoding="euc-jp", use_cache=False)
                soup_db = BeautifulSoup(html_db, "lxml")
                
                race_links = soup_db.find_all("a", href=re.compile(r"/race/(\d{12})/"))
                for a in race_links:
                    href = a.get("href", "")
                    m = re.search(r"/race/(\d{12})/", href)
                    if not m:
                        continue
                    race_id = m.group(1)
                    race_name = a.text.strip()
                    if not race_name:
                        continue

                    code = race_id[4:6]
                    venue_name = COURSE_CODE_MAP.get(code, f"場{code}")
                    race_num = int(race_id[10:12])

                    if venue_name not in venues_dict:
                        venues_dict[venue_name] = []

                    if not any(r["race_id"] == race_id for r in venues_dict[venue_name]):
                        venues_dict[venue_name].append({
                            "race_id": race_id,
                            "race_number": race_num,
                            "race_name": race_name,
                            "course": venue_name
                        })
            except Exception as e:
                print(f"DB archive schedule fetch notice: {e}")

        # レース番号順にソート
        venues_list = []
        for v_name, r_list in venues_dict.items():
            r_list.sort(key=lambda x: x["race_number"])
            venues_list.append({
                "course": v_name,
                "race_count": len(r_list),
                "races": r_list
            })

        # JRA場（東京、中山、京都、阪神等）を優先表示
        jra_order = ["東京", "中山", "京都", "阪神", "中京", "新潟", "小倉", "福島", "札幌", "函館"]
        venues_list.sort(key=lambda v: (0 if v["course"] in jra_order else 1, jra_order.index(v["course"]) if v["course"] in jra_order else v["course"]))

        formatted_date = f"{clean_date[:4]}-{clean_date[4:6]}-{clean_date[6:8]}" if len(clean_date) == 8 else date_str

        return {
            "date": formatted_date,
            "venue_count": len(venues_list),
            "venues": venues_list
        }
