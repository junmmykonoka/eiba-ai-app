import os
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from .database import engine, Base, get_db
from .models import Race, Entry
from .schemas import RaceSummaryResponse, RaceDetailResponse, RaceCreate, ScrapeRequest
from .scraper import RaceCardScraper, ScheduleScraper
from .mock_data import MOCK_RACES
from .ml.predictor import KeibaPredictor
from .ml.trainer import train_model

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Keiba AI - 競馬予想＆出馬表システム",
    description="無料の競馬予想＆出馬表管理API (LightGBM/勾配ブースティングAI搭載)",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

race_scraper = RaceCardScraper()
schedule_scraper = ScheduleScraper()
ai_predictor = KeibaPredictor()

class BatchScrapeRequest(BaseModel):
    race_ids: List[str]

# Initialize DB with mock data if empty
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    if db.query(Race).count() == 0:
        seed_mock_data(db)

def seed_mock_data(db: Session):
    for r_data in MOCK_RACES:
        entries_data = r_data.get("entries", [])
        race_dict = {k: v for k, v in r_data.items() if k != "entries"}
        
        existing = db.query(Race).filter(Race.id == race_dict["id"]).first()
        if existing:
            continue
            
        race = Race(**race_dict)
        db.add(race)
        db.flush()

        for e_data in entries_data:
            entry = Entry(race_id=race.id, **e_data)
            db.add(entry)
    db.commit()

# API Endpoints
@app.get("/api/races", response_model=List[RaceSummaryResponse])
def get_races(db: Session = Depends(get_db)):
    races = db.query(Race).order_by(Race.race_date.desc(), Race.race_number.asc()).all()
    results = []
    for r in races:
        item = RaceSummaryResponse.from_orm(r)
        item.entry_count = len(r.entries)
        results.append(item)
    return results

@app.get("/api/races/{race_id}", response_model=RaceDetailResponse)
def get_race_detail(race_id: str, db: Session = Depends(get_db)):
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    return race

@app.get("/api/schedule")
def get_schedule(date: Optional[str] = Query(None, description="日付 (YYYY-MM-DD)")):
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    try:
        schedule = schedule_scraper.get_schedule_by_date(date)
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"開催日程の取得に失敗しました: {str(e)}")

@app.post("/api/seed")
def reseed_data(db: Session = Depends(get_db)):
    db.query(Entry).delete()
    db.query(Race).delete()
    db.commit()
    seed_mock_data(db)
    return {"message": "Sample races loaded successfully"}

@app.post("/api/scrape", response_model=RaceDetailResponse)
def scrape_and_save_race(req: ScrapeRequest, db: Session = Depends(get_db)):
    query = req.url_or_date.strip()
    import re
    m = re.search(r"race_id=(\d+)", query) or re.search(r"/race/(\d+)", query) or re.search(r"^(\d{10,16})$", query)
    if not m:
        raise HTTPException(
            status_code=400, 
            detail="有効なレースID（例: 202405021211）またはnetkeibaの出馬表URLを入力してください。"
        )
    
    race_id = m.group(1)
    
    try:
        data = race_scraper.scrape_shutuba_by_id(race_id)
        if not data or not data.get("entries"):
            raise HTTPException(status_code=404, detail="出馬表データの取得に失敗しました。")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"スクレイピングエラー: {str(e)}")

    existing = db.query(Race).filter(Race.id == data["id"]).first()
    if existing:
        db.delete(existing)
        db.commit()

    entries_data = data.pop("entries", [])
    race = Race(**data)
    db.add(race)
    db.flush()

    for e_data in entries_data:
        entry = Entry(race_id=race.id, **e_data)
        db.add(entry)
    
    db.commit()
    db.refresh(race)
    return race

@app.post("/api/scrape-batch")
def scrape_batch(req: BatchScrapeRequest, db: Session = Depends(get_db)):
    success_count = 0
    errors = []
    
    for race_id in req.race_ids:
        try:
            data = race_scraper.scrape_shutuba_by_id(race_id)
            if not data or not data.get("entries"):
                errors.append(f"{race_id}: データが見つかりませんでした")
                continue

            existing = db.query(Race).filter(Race.id == data["id"]).first()
            if existing:
                db.delete(existing)
                db.commit()

            entries_data = data.pop("entries", [])
            race = Race(**data)
            db.add(race)
            db.flush()

            for e_data in entries_data:
                entry = Entry(race_id=race.id, **e_data)
                db.add(entry)
            
            db.commit()
            success_count += 1
        except Exception as e:
            errors.append(f"{race_id}: {str(e)}")

    return {
        "success_count": success_count,
        "total": len(req.race_ids),
        "errors": errors
    }

# ------------------------------------------------------------------
# Machine Learning AI Prediction Endpoints
# ------------------------------------------------------------------
@app.post("/api/predict/{race_id}", response_model=RaceDetailResponse)
def predict_race_ai(race_id: str, db: Session = Depends(get_db)):
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    # Race dict for feature extraction
    race_dict = {
        "id": race.id,
        "race_name": race.race_name,
        "course": race.course,
        "track_type": race.track_type,
        "distance": race.distance,
        "weather": race.weather,
        "track_condition": race.track_condition,
        "entries": [
            {
                "id": e.id,
                "bracket_number": e.bracket_number,
                "horse_number": e.horse_number,
                "horse_name": e.horse_name,
                "sex_age": e.sex_age,
                "jockey_name": e.jockey_name,
                "impost": e.impost,
                "trainer_name": e.trainer_name,
                "horse_weight": e.horse_weight,
                "weight_diff": e.weight_diff,
                "odds": e.odds,
                "popularity": e.popularity
            }
            for e in race.entries
        ]
    }

    # Run ML Model
    predictions = ai_predictor.predict_race(race_dict)

    # Update DB entries with predicted scores & ranks
    pred_map = {p["horse_number"]: p for p in predictions}
    for e in race.entries:
        if e.horse_number in pred_map:
            p_info = pred_map[e.horse_number]
            e.ai_pred_score = p_info["ai_pred_score"]
            e.ai_pred_rank = p_info["ai_pred_rank"]

    db.commit()
    db.refresh(race)
    return race

@app.post("/api/train")
def train_ai_model(n_races: int = Query(1500, description="学習レース数")):
    try:
        metrics = train_model(n_races=n_races)
        ai_predictor._load_or_train_model()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"モデル学習エラー: {str(e)}")

@app.delete("/api/races/{race_id}")
def delete_race(race_id: str, db: Session = Depends(get_db)):
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    db.delete(race)
    db.commit()
    return {"message": "Race deleted"}

# Serve frontend static files
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
