import math
from typing import Dict, Any, List, Tuple, Optional
from shapely.geometry import shape, LineString, MultiLineString, Polygon, MultiPolygon

def distance_sq(pt1: Tuple[float, float], pt2: Tuple[float, float]) -> float:
    return (pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2

def extract_coords_from_geojson(geojson_data: Dict[str, Any], center_lat: Optional[float] = None, center_lng: Optional[float] = None) -> List[Tuple[float, float]]:
    """
    Extracts (lng, lat) coordinates from GeoJSON.
    Picks the single primary continuous waterbody feature closest to (center_lat, center_lng).
    """
    coords: List[Tuple[float, float]] = []
    if not geojson_data:
        return coords

    g_type = geojson_data.get("type", "LineString")
    if g_type == "FeatureCollection":
        features = geojson_data.get("features", [])
        if not features:
            return coords
        
        target_pt = (center_lng, center_lat) if (center_lng is not None and center_lat is not None) else None
        
        # If target point is provided, pick the feature closest to target_pt
        if target_pt:
            def feat_dist(f):
                pts = extract_coords_from_geometry(f.get("geometry", {}))
                if not pts:
                    return float("inf")
                return min(distance_sq(p, target_pt) for p in pts)
            
            best_feat = min(features, key=feat_dist)
            coords = extract_coords_from_geometry(best_feat.get("geometry", {}))
        else:
            # Otherwise pick the feature with the highest point count
            best_feat = max(features, key=lambda f: len(extract_coords_from_geometry(f.get("geometry", {}))))
            coords = extract_coords_from_geometry(best_feat.get("geometry", {}))
            
    elif g_type == "Feature":
        geom = geojson_data.get("geometry", {})
        coords.extend(extract_coords_from_geometry(geom))
    elif g_type in ("LineString", "MultiLineString", "Polygon", "MultiPolygon", "Point"):
        coords.extend(extract_coords_from_geometry(geojson_data))
        
    return coords

def detect_geometry_type(geojson_data: Dict[str, Any]) -> str:
    """Detects whether GeoJSON represents a LineString, MultiLineString, Polygon, or MultiPolygon."""
    if not geojson_data:
        return "LineString"
    g_type = geojson_data.get("type", "LineString")
    if g_type == "FeatureCollection":
        features = geojson_data.get("features", [])
        if features:
            return features[0].get("geometry", {}).get("type", "LineString")
    elif g_type == "Feature":
        return geojson_data.get("geometry", {}).get("type", "LineString")
    return g_type

def extract_coords_from_geometry(geom: Dict[str, Any]) -> List[Tuple[float, float]]:
    coords: List[Tuple[float, float]] = []
    g_type = geom.get("type")
    c = geom.get("coordinates", [])
    
    if g_type == "LineString":
        for pt in c:
            if len(pt) >= 2:
                coords.append((float(pt[0]), float(pt[1])))
    elif g_type == "MultiLineString":
        for line in c:
            for pt in line:
                if len(pt) >= 2:
                    coords.append((float(pt[0]), float(pt[1])))
    elif g_type == "Polygon":
        if c and len(c) > 0:
            for pt in c[0]:
                if len(pt) >= 2:
                    coords.append((float(pt[0]), float(pt[1])))
    elif g_type == "MultiPolygon":
        for poly in c:
            if poly and len(poly) > 0:
                for pt in poly[0]:
                    if len(pt) >= 2:
                        coords.append((float(pt[0]), float(pt[1])))
    elif g_type == "Point":
        if len(c) >= 2:
            coords.append((float(c[0]), float(c[1])))
            
    return coords

def simplify_geometry(
    geojson_data: Dict[str, Any],
    center_lat: Optional[float] = None,
    center_lng: Optional[float] = None
) -> Dict[str, Any]:
    """
    Parses GeoJSON flowline/waterbody network.
    - For Rivers: Samples 10 points along the continuous river channel from start to end without wrapping across land.
    - For Lakes/Ponds: Scans for the section closest to the entered location and focuses bounding box & sample points.
    """
    coords = extract_coords_from_geojson(geojson_data, center_lat=center_lat, center_lng=center_lng)
    geom_type = detect_geometry_type(geojson_data)
    
    if not coords:
        if center_lat is not None and center_lng is not None:
            bbox = [round(center_lng - 0.02, 5), round(center_lat - 0.02, 5), round(center_lng + 0.02, 5), round(center_lat + 0.02, 5)]
            bank_points = [{"lat": round(center_lat + i * 0.002, 5), "lng": round(center_lng + i * 0.002, 5)} for i in range(10)]
            return {"bbox": bbox, "bank_points": bank_points}
        raise ValueError("Cannot simplify geometry: empty coordinate set and no center point provided.")

    target_pt = (center_lng, center_lat) if (center_lng is not None and center_lat is not None) else None
    is_polygon = geom_type in ("Polygon", "MultiPolygon")

    if is_polygon and target_pt:
        # Sort polygon vertices by distance to the user's entered location
        sorted_coords = sorted(coords, key=lambda p: distance_sq(p, target_pt))
        closest_cluster = sorted_coords[:max(10, min(30, len(sorted_coords)))]
        
        c_lngs = [c[0] for c in closest_cluster]
        c_lats = [c[1] for c in closest_cluster]
        
        min_lng, max_lng = min(c_lngs), max(c_lngs)
        min_lat, max_lat = min(c_lats), max(c_lats)
        
        bbox = [round(min_lng - 0.005, 5), round(min_lat - 0.005, 5), round(max_lng + 0.005, 5), round(max_lat + 0.005, 5)]
        step = max(1, len(closest_cluster) // 5)
        sampled_coords = closest_cluster[::step][:5]
        bank_points = [{"lat": round(lat, 5), "lng": round(lng, 5)} for lng, lat in sampled_coords]
    else:
        # River: Keep continuous natural LineString order from start to end
        lngs = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        min_lng, max_lng = min(lngs), max(lngs)
        min_lat, max_lat = min(lats), max(lats)
        bbox = [round(min_lng, 5), round(min_lat, 5), round(max_lng, 5), round(max_lat, 5)]
        
        # Sample exactly 10 points along the river length continuously
        step = max(1, len(coords) // 10)
        sampled_coords = coords[::step][:10]
        while len(sampled_coords) < 10 and len(coords) > 0:
            sampled_coords.append(coords[-1])
            
        bank_points = [{"lat": round(lat, 5), "lng": round(lng, 5)} for lng, lat in sampled_coords]

    return {
        "bbox": bbox,
        "bank_points": bank_points
    }
