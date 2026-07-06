ENGINE_MAP = {
    "SVG_VECTOR": "vector",
    "SVG_LAYER": "layer",
    "SVG_RASTER": "raster",
    "RASTER_TRACE": "raster",
}


def route_engine(recommended_engine: str) -> str:
    return ENGINE_MAP.get(recommended_engine, "vector")
