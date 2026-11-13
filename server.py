"""
FastAPI Server phục vụ giao diện Extej Dashboard chuẩn Pixel-Perfect
Khởi chạy trên http://localhost:8000
"""

import os
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd

from config import (
    SALES_REPS, SALES_MANAGER, POLICY_RULES,
    STATUS_QUALIFIED, STATUS_NEEDS_INFO, STATUS_INFEASIBLE, STATUS_PENDING_APPROVAL,
    GEMINI_API_KEY
)
from data_loader import (
    load_from_csv, load_from_excel, load_from_google_sheets,
    get_default_sample_dataframe
)
from pipeline import SalesOpportunityPipeline
from trace_logger import GlobalTraceRegistry

app = FastAPI(title="Extej B2B Agent Dashboard")

# Trạng thái trong bộ nhớ
current_df = get_default_sample_dataframe()
dossiers, summary_stats = SalesOpportunityPipeline.process_dataframe(current_df)

@app.get("/api/state")
def get_state():
    """Lấy toàn bộ dữ liệu cơ hội, thống kê tài chính và trace logs"""
    traces = [t.to_dict() for t in GlobalTraceRegistry.get_all()]
    return {
        "summary": summary_stats,
        "dossiers": dossiers,
        "traces": traces,
        "sales_reps": SALES_REPS,
        "manager": SALES_MANAGER,
        "policy": POLICY_RULES,
        "gemini_active": bool(GEMINI_API_KEY)
    }

@app.post("/api/load_sample")
def load_sample():
    global current_df, dossiers, summary_stats
    current_df = get_default_sample_dataframe()
    dossiers, summary_stats = SalesOpportunityPipeline.process_dataframe(current_df)
    return {"status": "success", "message": "Đã nạp 8 tình huống kiểm thử chuẩn AI301"}

@app.post("/api/load_google_sheet")
def load_google_sheet(payload: Dict[str, str]):
    global current_df, dossiers, summary_stats
    url = payload.get("url", "").strip()
    df_loaded, msg = load_from_google_sheets(url)
    if df_loaded is None:
        return JSONResponse(status_code=400, content={"status": "error", "message": msg})
    current_df = df_loaded
    dossiers, summary_stats = SalesOpportunityPipeline.process_dataframe(df_loaded)
    return {"status": "success", "message": msg}

@app.post("/api/upload_file")
async def upload_file(file: UploadFile = File(...)):
    global current_df, dossiers, summary_stats
    contents = await file.read()
    filename = file.filename.lower()
    import io
    if filename.endswith(".csv"):
        df_loaded, msg = load_from_csv(io.BytesIO(contents))
    elif filename.endswith((".xlsx", ".xls")):
        df_loaded, msg = load_from_excel(io.BytesIO(contents))
    else:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Chỉ hỗ trợ file .csv, .xlsx, .xls"})

    if df_loaded is None:
        return JSONResponse(status_code=400, content={"status": "error", "message": msg})

    current_df = df_loaded
    dossiers, summary_stats = SalesOpportunityPipeline.process_dataframe(df_loaded)
    return {"status": "success", "message": msg}

@app.get("/", response_class=HTMLResponse)
def serve_index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)

