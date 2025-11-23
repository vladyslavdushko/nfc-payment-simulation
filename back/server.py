"""FastAPI backend for receiving NFC transactions and serving dashboard data."""
import os
import time
import math
from typing import Optional, Literal, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import MongoClient

# MongoDB connection
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://vladyslavdusko_db_user:SM8tbv5R6zRJmvKS@payment.vrplirm.mongodb.net/")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    client.admin.command('ping')
    print("✅ MongoDB connected successfully!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    client = None

db = client["nfc_payments"] if client else None
transactions = db["transactions"] if db else None

app = FastAPI(title="NFC Payments API")

# CORS for local Vite dev and Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nfc-payment-simulation.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://localhost:5173",
        "https://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TransactionIn(BaseModel):
    """Incoming transaction payload."""
    uid: str = Field(min_length=1)
    status: Literal["GRANTED", "DENIED", "granted", "denied"]
    timestamp: Optional[float] = None  # seconds since epoch


class TransactionOut(BaseModel):
    """Response model for write acknowledgement."""
    ok: bool
    id: Optional[str] = None


@app.post("/transactions", response_model=TransactionOut)
def create_transaction(txn: TransactionIn):
    """Insert a transaction document into MongoDB."""
    if not transactions:
        raise HTTPException(status_code=503, detail="Database not connected")
    status_norm = txn.status.upper()
    ts = txn.timestamp if txn.timestamp is not None else time.time()
    doc = {"uid": txn.uid.strip(), "status": status_norm, "timestamp": float(ts)}
    try:
        res = transactions.insert_one(doc)
        return TransactionOut(ok=True, id=str(res.inserted_id))
    except Exception as e:  
        raise HTTPException(status_code=500, detail=str(e)) from e



# Health check
@app.get("/health")
def health():
    """Ping database and report service health."""
    if not client:
        raise HTTPException(status_code=503, detail="Database not connected")
    try:
        client.admin.command("ping")
        return {"ok": True}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/transactions")
def list_transactions(
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="GRANTED or DENIED"),
    uid: Optional[str] = Query(None),
    since: Optional[float] = Query(
        None, description="Unix seconds; return txns with timestamp >= since"
    ),
) -> List[Dict[str, Any]]:
    """Return recent transactions with optional filters."""
    if not transactions:
        raise HTTPException(status_code=503, detail="Database not connected")
    q: Dict[str, Any] = {}
    if status:
        q["status"] = status.upper()
    if uid:
        q["uid"] = uid
    if since is not None:
        try:
            q["timestamp"] = {"$gte": float(since)}
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="Invalid 'since'") from e

    try:
        cursor = transactions.find(q).sort("timestamp", -1).skip(skip).limit(limit)
        out = []
        for d in cursor:
            d["_id"] = str(d.get("_id"))
            out.append(d)
        return out
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/stats")
def stats(
    hours: int = Query(24, ge=1, le=24*14),
) -> Dict[str, Any]:
    """Return simple stats for the last N hours: per-hour granted/denied counts and totals."""
    if not transactions:
        raise HTTPException(status_code=503, detail="Database not connected")
    now = time.time()
    start = now - hours * 3600
    try:
        cursor = transactions.find({"timestamp": {"$gte": start}})
        # bucket by hour
        buckets: Dict[int, Dict[str, int]] = {}
        total = {"GRANTED": 0, "DENIED": 0}
        for d in cursor:
            ts = float(d.get("timestamp", 0.0))
            status = str(d.get("status", "")).upper()
            hour_bucket = int(math.floor(ts / 3600.0) * 3600)
            b = buckets.setdefault(hour_bucket, {"GRANTED": 0, "DENIED": 0})
            if status in ("GRANTED", "DENIED"):
                b[status] += 1
                total[status] += 1
        # produce sorted timeline
        timeline = []
        for h in sorted(buckets.keys()):
            timeline.append(
                {"t": h, "granted": buckets[h]["GRANTED"], "denied": buckets[h]["DENIED"]}
            )
        return {"since": start, "now": now, "total": total, "timeline": timeline}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e