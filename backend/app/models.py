from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base

class Race(Base):
    __tablename__ = "races"

    id = Column(String, primary_key=True, index=True)  # 例: 202408010111 または 日付+場所+R
    race_name = Column(String, index=True, nullable=False)
    race_number = Column(Integer, nullable=False)
    race_date = Column(String, index=True, nullable=False)  # YYYY-MM-DD
    course = Column(String, index=True, nullable=False)  # 東京, 中山, etc.
    track_type = Column(String, default="芝")  # 芝, ダート, 障害
    distance = Column(Integer, default=2000)  # 距離 (m)
    weather = Column(String, default="晴")
    track_condition = Column(String, default="良")  # 良, 稍重, 重, 不良
    start_time = Column(String, default="15:00")
    race_class = Column(String, default="オープン")  # G1, G2, G3, OP, 1勝クラス, etc.
    created_at = Column(DateTime, default=func.now())

    entries = relationship("Entry", back_populates="race", cascade="all, delete-orphan", order_by="Entry.horse_number")

class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(String, ForeignKey("races.id"), nullable=False, index=True)
    bracket_number = Column(Integer, nullable=False)  # 枠番 (1-8)
    horse_number = Column(Integer, nullable=False)  # 馬番 (1-18)
    horse_name = Column(String, nullable=False, index=True)
    horse_id = Column(String, nullable=True)  # 血統や過去データ紐付け用
    sex_age = Column(String, nullable=False)  # 牡3, 牝4, etc.
    jockey_name = Column(String, nullable=False)
    jockey_id = Column(String, nullable=True)
    impost = Column(Float, nullable=False)  # 斤量 (kg)
    trainer_name = Column(String, nullable=False)
    trainer_id = Column(String, nullable=True)
    horse_weight = Column(Integer, nullable=True)  # 馬体重 (kg)
    weight_diff = Column(Integer, nullable=True)  # 体重増減
    odds = Column(Float, nullable=True)  # 単勝オッズ
    popularity = Column(Integer, nullable=True)  # 人気順
    ai_pred_score = Column(Float, nullable=True)  # 将来のAI予測値
    ai_pred_rank = Column(Integer, nullable=True)  # 将来のAI予想順位

    race = relationship("Race", back_populates="entries")
