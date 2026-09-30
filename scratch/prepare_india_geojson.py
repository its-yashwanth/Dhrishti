import urllib.request
import json
import math
import os

def p_dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def point_line_dist(pt, start, end):
    if start[0] == end[0] and start[1] == end[1]:
        return p_dist(pt, start)
    n = abs((end[1] - start[1]) * pt[0] - (end[0] - start[0]) * pt[1] + end[0] * start[1] - end[1] * start[0])
    d = math.hypot(end[1] - start[1], end[0] - start[0])
    return n / d if d > 0 else 0

def simplify_line(pts, eps):
    if len(pts) <= 3:
        return [[round(p[0], 3), round(p[1], 3)] for p in pts]
    
    # Keep closed ring closed
    is_closed = (pts[0][0] == pts[-1][0] and pts[0][1] == pts[-1][1])
    
    dmax = 0
    idx = 0
    for i in range(1, len(pts) - 1):
        d = point_line_dist(pts[i], pts[0], pts[-1])
        if d > dmax:
            dmax = d
            idx = i
            
    if dmax > eps:
        rec1 = simplify_line(pts[:idx + 1], eps)
        rec2 = simplify_line(pts[idx:], eps)
        res = rec1[:-1] + rec2
    else:
        res = [pts[0], pts[-1]]
        
    if is_closed and (res[0][0] != res[-1][0] or res[0][1] != res[-1][1]):
        res.append(res[0])
        
    return [[round(p[0], 3), round(p[1], 3)] for p in res]

def simplify_geometry(geom, eps):
    g_type = geom.get('type')
    coords = geom.get('coordinates', [])
    
    if g_type == 'Polygon':
        new_coords = []
        for ring in coords:
            s_ring = simplify_line(ring, eps)
            if len(s_ring) >= 4:
                new_coords.append(s_ring)
        if not new_coords and coords:
            new_coords = coords
        return {'type': 'Polygon', 'coordinates': new_coords}
        
    elif g_type == 'MultiPolygon':
        new_coords = []
        for poly in coords:
            new_poly = []
            for ring in poly:
                s_ring = simplify_line(ring, eps)
                if len(s_ring) >= 4:
                    new_poly.append(s_ring)
            if new_poly:
                new_coords.append(new_poly)
        if not new_coords and coords:
            new_coords = coords
        return {'type': 'MultiPolygon', 'coordinates': new_coords}
        
    return geom

def process_districts():
    url = "https://raw.githubusercontent.com/geohacker/india/master/district/india_district.geojson"
    print("Downloading India district boundaries...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        
    print(f"Downloaded {len(data['features'])} district features. Simplifying...")
    out_features = []
    
    for f in data['features']:
        props = f.get('properties', {})
        state = props.get('NAME_1', '')
        district = props.get('NAME_2', '')
        
        sim_geom = simplify_geometry(f.get('geometry', {}), eps=0.015)
        
        out_features.append({
            'type': 'Feature',
            'id': f"{state}_{district}".lower().replace(" ", "_"),
            'properties': {
                'district': district,
                'state': state,
                'name': district,
            },
            'geometry': sim_geom
        })
        
    out_geojson = {
        'type': 'FeatureCollection',
        'features': out_features
    }
    
    os.makedirs('frontend/public/data', exist_ok=True)
    out_path = 'frontend/public/data/india_districts.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out_geojson, f, separators=(',', ':'))
        
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Saved {out_path} ({size_mb:.2f} MB)")

def process_states():
    url = "https://raw.githubusercontent.com/geohacker/india/master/state/india_telengana.geojson"
    print("Downloading India state boundaries...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        
    print(f"Downloaded {len(data['features'])} state features. Simplifying...")
    out_features = []
    
    for f in data['features']:
        props = f.get('properties', {})
        state = props.get('NAME_1', props.get('name', ''))
        
        sim_geom = simplify_geometry(f.get('geometry', {}), eps=0.02)
        
        out_features.append({
            'type': 'Feature',
            'id': state.lower().replace(" ", "_"),
            'properties': {
                'state': state,
                'name': state,
            },
            'geometry': sim_geom
        })
        
    out_geojson = {
        'type': 'FeatureCollection',
        'features': out_features
    }
    
    os.makedirs('frontend/public/data', exist_ok=True)
    out_path = 'frontend/public/data/india_states.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out_geojson, f, separators=(',', ':'))
        
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Saved {out_path} ({size_mb:.2f} MB)")

if __name__ == '__main__':
    process_states()
    process_districts()
