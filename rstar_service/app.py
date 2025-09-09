from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import rstar

app = FastAPI()


class PatchRequest(BaseModel):
    data: str


@app.post("/patch")
def patch(req: PatchRequest):
    if not hasattr(rstar, "patch"):
        raise HTTPException(status_code=501, detail="rstar.patch not implemented")
    result = rstar.patch(req.data)
    return {"result": result}
