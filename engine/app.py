import asyncio
import json
import time
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models import AnalyzeRequest, AnalyzeResponse, ConvertRequest, TaskStatus
from analyzer import analyze_svg, route_engine
from engines import VectorEngine, LayerEngine, RasterEngine
from exporters import export_glb
from tasks import task_manager

ENGINES = {
    "vector": VectorEngine(),
    "layer": LayerEngine(),
    "raster": RasterEngine(),
}

app = FastAPI(title=settings.app_name, version=settings.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.version}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest):
    try:
        result = analyze_svg(body.svg_content)
        engine = route_engine(result["recommended_engine"])
        return AnalyzeResponse(
            type=result["type"],
            layers=result["layers"],
            shapes=result["shapes"],
            colors=result["colors"],
            warnings=result["warnings"],
            recommended_engine=engine,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/analyze/upload")
async def analyze_upload(file: UploadFile = File(...)):
    content = await file.read()
    svg_str = content.decode("utf-8")
    result = analyze_svg(svg_str)
    engine = route_engine(result["recommended_engine"])
    return AnalyzeResponse(
        type=result["type"],
        layers=result["layers"],
        shapes=result["shapes"],
        colors=result["colors"],
        warnings=result["warnings"],
        recommended_engine=engine,
    )


@app.post("/convert")
async def convert(body: ConvertRequest):
    task_id = task_manager.create_task()
    task_manager.update(task_id, 0.1, "Analyzing SVG")

    try:
        result = analyze_svg(body.svg_content)
        engine_name = route_engine(result["recommended_engine"])
        task_manager.update(task_id, 0.3, f"Selected engine: {engine_name}")

        depth = body.settings.depth if body.settings else 0.5
        bevel = body.settings.bevel if body.settings else 0.05
        smoothness = body.settings.smoothness if body.settings else 5
        material_color = body.material.color if body.material else "#6366f1"
        material_metalness = body.material.metalness if body.material else 0.2
        material_roughness = body.material.roughness if body.material else 0.3

        settings_dict = {
            "depth": depth,
            "bevel": bevel,
            "smoothness": smoothness,
            "material": {
                "color": material_color,
                "metalness": material_metalness,
                "roughness": material_roughness,
            },
        }

        task_manager.update(task_id, 0.5, f"Converting with {engine_name} engine")

        engine = ENGINES.get(engine_name)
        if engine is None:
            task_manager.fail(task_id, f"Engine '{engine_name}' not available")
            raise HTTPException(status_code=400, detail=f"Engine '{engine_name}' not found")

        try:
            scene = engine.convert(body.svg_content, settings_dict)
        except NotImplementedError as e:
            task_manager.fail(task_id, str(e))
            raise HTTPException(status_code=501, detail=str(e))

        task_manager.update(task_id, 0.9, "Exporting GLB")

        glb_bytes = export_glb(scene)
        task_manager.complete(task_id)

        return Response(
            content=glb_bytes,
            media_type="model/gltf-binary",
            headers={
                "Content-Disposition": f'attachment; filename="{body.file_name or "model"}.glb"',
                "X-Task-Id": task_id,
            },
        )
    except Exception as e:
        task_manager.fail(task_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/convert/upload")
async def convert_upload(file: UploadFile = File(...)):
    content = await file.read()
    svg_str = content.decode("utf-8")
    req = ConvertRequest(svg_content=svg_str, file_name=file.filename)
    return await convert(req)


@app.get("/progress/{task_id}", response_model=TaskStatus)
async def get_progress(task_id: str):
    task = task_manager.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        message=task["message"],
    )


@app.get("/progress/{task_id}/stream")
async def stream_progress(task_id: str):
    task = task_manager.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_stream() -> AsyncGenerator[str, None]:
        while True:
            t = task_manager.get(task_id)
            if not t:
                break
            data = json.dumps({
                "task_id": task_id,
                "progress": t["progress"],
                "message": t["message"],
                "status": t["status"],
            })
            yield f"data: {data}\n\n"
            if t["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=settings.host, port=settings.port, reload=True)
