import uvicorn, json
from fastapi import FastAPI
from fastapi.routing import APIRoute

# from bson import json_util
from pydantic import BaseModel
from typing import Dict
from common import router_common
from func.user.user import router_user
from func.file.store import router_store
from func.generate.generate_api import router_generate
from func.datamanager.datamanager_api import router_datamanager
from func.analysis.analysis_api import router_analysis
# from func.preprocess.api_pdf_processor import router_preprocess
# from func.regresstest.regresstest_api import router_regresstest
app = FastAPI()

app.include_router(router_common)
app.include_router(router_user)
app.include_router(router_store)
app.include_router(router_generate)
# app.include_router(router_preprocess)
app.include_router(router_datamanager)
# app.include_router(router_regresstest)
app.include_router(router_analysis)

class DBRequest(BaseModel):
    db_name: str
    coll_name: str
    
class DBData(BaseModel):
    db_name: str
    coll_name: str
    db_data: dict

@app.get("/")
def read_root():
    return {"Hello": "World"}
if __name__ == "__main__":
    uvicorn.run("MGDF_server:app", host="0.0.0.0", port=19008, reload=True, workers=4)
