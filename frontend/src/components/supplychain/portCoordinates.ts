import * as THREE from 'three';

export interface PortGeoData {
  name: string;
  aliases: string[];
  state: string;
  lat: number;
  lon: number;
}

// Known major Indian ports with accurate geographic coordinates
export const KNOWN_PORT_COORDINATES: PortGeoData[] = [
  {
    name: 'Deendayal Port Authority',
    aliases: ['deendayal', 'kandla', 'deendayal port', 'deendayal port authority (kandla)'],
    state: 'Gujarat',
    lat: 23.0033,
    lon: 70.2189,
  },
  {
    name: 'Jawaharlal Nehru Port Authority (JNPA)',
    aliases: ['jnpa', 'jawaharlal nehru', 'nhava sheva', 'jawaharlal nehru port authority (jnpa)'],
    state: 'Maharashtra',
    lat: 18.9499,
    lon: 72.9515,
  },
  {
    name: 'Mundra Port',
    aliases: ['mundra', 'mundra port (adani ports)', 'adani mundra'],
    state: 'Gujarat',
    lat: 22.7389,
    lon: 69.7042,
  },
  {
    name: 'Mumbai Port Authority',
    aliases: ['mumbai', 'mumbai port', 'bombay'],
    state: 'Maharashtra',
    lat: 18.9633,
    lon: 72.8532,
  },
  {
    name: 'Pipavav Port',
    aliases: ['pipavav', 'port pipavav', 'apmt pipavav'],
    state: 'Gujarat',
    lat: 20.9167,
    lon: 71.5000,
  },
  {
    name: 'Chennai Port Authority',
    aliases: ['chennai', 'chennai port', 'madras port'],
    state: 'Tamil Nadu',
    lat: 13.0827,
    lon: 80.2707,
  },
  {
    name: 'V.O. Chidambaranar Port',
    aliases: ['tuticorin', 'v.o. chidambaranar', 'voc port', 'v.o. chidambaranar port authority'],
    state: 'Tamil Nadu',
    lat: 8.7642,
    lon: 78.1348,
  },
  {
    name: 'Paradip Port Authority',
    aliases: ['paradip', 'paradeep', 'paradip port'],
    state: 'Odisha',
    lat: 20.2644,
    lon: 86.6713,
  },
  {
    name: 'Visakhapatnam Port',
    aliases: ['visakhapatnam', 'vizag', 'visakhapatnam port authority'],
    state: 'Andhra Pradesh',
    lat: 17.6868,
    lon: 83.2185,
  },
  {
    name: 'Cochin Port Authority',
    aliases: ['cochin', 'kochi', 'cochin port'],
    state: 'Kerala',
    lat: 9.9312,
    lon: 76.2673,
  },
  {
    name: 'Kamarajar Port (Ennore)',
    aliases: ['ennore', 'kamarajar', 'kamarajar port'],
    state: 'Tamil Nadu',
    lat: 13.2611,
    lon: 80.3292,
  },
  {
    name: 'Mormugao Port Authority',
    aliases: ['mormugao', 'morpugao', 'goa port'],
    state: 'Goa',
    lat: 15.4131,
    lon: 73.8016,
  },
  {
    name: 'New Mangalore Port',
    aliases: ['mangalore', 'new mangalore', 'panambur'],
    state: 'Karnataka',
    lat: 12.9248,
    lon: 74.8197,
  },
  {
    name: 'Syama Prasad Mookerjee Port (Kolkata/Haldia)',
    aliases: ['kolkata', 'haldia', 'calcutta port'],
    state: 'West Bengal',
    lat: 22.0289,
    lon: 88.0620,
  },
  {
    name: 'Hazira Port',
    aliases: ['hazira', 'adani hazira', 'surat port'],
    state: 'Gujarat',
    lat: 21.0967,
    lon: 72.6467,
  },
  {
    name: 'Krishnapatnam Port',
    aliases: ['krishnapatnam', 'nellore port', 'adani krishnapatnam'],
    state: 'Andhra Pradesh',
    lat: 14.2500,
    lon: 80.1167,
  },
  {
    name: 'Dhamra Port',
    aliases: ['dhamra', 'dhamra port authority', 'dhamra agri'],
    state: 'Odisha',
    lat: 20.8258,
    lon: 86.9619,
  },
  {
    name: 'Kakinada Deep Water Port',
    aliases: ['kakinada', 'kakinada port'],
    state: 'Andhra Pradesh',
    lat: 16.9891,
    lon: 82.2858,
  },
];

// Target country reference coordinates (maritime entry gateways / capital hubs)
export const COUNTRY_COORDINATES: Record<string, { lat: number; lon: number; label: string; code: string }> = {
  'RUSSIA': { lat: 44.7239, lon: 37.7688, label: 'Novorossiysk / Black Sea (Russia)', code: 'RU' }, // Major maritime agri-grain destination
  'CHINA': { lat: 31.2304, lon: 121.4737, label: 'Shanghai Gateway (China)', code: 'CN' },
  'UAE': { lat: 25.0112, lon: 55.0617, label: 'Jebel Ali Port (UAE)', code: 'AE' },
  'UNITED ARAB EMIRATES': { lat: 25.0112, lon: 55.0617, label: 'Jebel Ali Port (UAE)', code: 'AE' },
  'USA': { lat: 29.9511, lon: -90.0715, label: 'Gulf of Mexico / New Orleans (USA)', code: 'US' },
  'UNITED STATES': { lat: 29.9511, lon: -90.0715, label: 'Gulf of Mexico / New Orleans (USA)', code: 'US' },
  'SAUDI ARABIA': { lat: 21.4858, lon: 39.1925, label: 'Jeddah Islamic Port (Saudi Arabia)', code: 'SA' },
  'INDONESIA': { lat: -6.2088, lon: 106.8456, label: 'Tanjung Priok / Jakarta (Indonesia)', code: 'ID' },
  'BANGLADESH': { lat: 22.3569, lon: 91.7832, label: 'Chittagong Port (Bangladesh)', code: 'BD' },
  'EGYPT': { lat: 31.2001, lon: 29.9187, label: 'Alexandria / Port Said (Egypt)', code: 'EG' },
  'TURKEY': { lat: 41.0082, lon: 28.9784, label: 'Bosphorus / Istanbul (Turkey)', code: 'TR' },
  'IRAN': { lat: 27.1832, lon: 56.2666, label: 'Bandar Abbas (Iran)', code: 'IR' },
  'GERMANY': { lat: 53.5511, lon: 9.9937, label: 'Hamburg Port (Germany)', code: 'DE' },
  'UK': { lat: 51.5074, lon: 0.1278, label: 'London Gateway (UK)', code: 'GB' },
  'UNITED KINGDOM': { lat: 51.5074, lon: 0.1278, label: 'London Gateway (UK)', code: 'GB' },
  'UKRAINE': { lat: 46.4825, lon: 30.7233, label: 'Odesa Port / Black Sea (Ukraine)', code: 'UA' },
  'SINGAPORE': { lat: 1.3521, lon: 103.8198, label: 'Port of Singapore', code: 'SG' },
  'VIETNAM': { lat: 10.8231, lon: 106.6297, label: 'Ho Chi Minh Port (Vietnam)', code: 'VN' },
  'MALAYSIA': { lat: 3.0, lon: 101.4, label: 'Port Klang (Malaysia)', code: 'MY' },
  'NETHERLANDS': { lat: 51.9244, lon: 4.4777, label: 'Port of Rotterdam (Netherlands)', code: 'NL' },
  'BRAZIL': { lat: -23.9618, lon: -46.3042, label: 'Santos Port (Brazil)', code: 'BR' },
  'AUSTRALIA': { lat: -33.8688, lon: 151.2093, label: 'Port Jackson / Sydney (Australia)', code: 'AU' },
  'JAPAN': { lat: 35.4437, lon: 139.6380, label: 'Yokohama Port (Japan)', code: 'JP' },
  'SOUTH KOREA': { lat: 35.1796, lon: 129.0756, label: 'Busan Port (South Korea)', code: 'KR' },
};

/**
 * Compute optimal camera position dynamically framing India and the target destination country.
 * Calculates mid-vector with cartographic elevation and distance proportional to angular separation.
 */
export function computeOptimalCorridorCameraPosition(
  destLat: number = 44.7,
  destLon: number = 37.8,
  originLat: number = 21.0,
  originLon: number = 72.0,
  globeRadius: number = 100
): THREE.Vector3 {
  const originVec = latLonToVector3(originLat, originLon, globeRadius).normalize();
  const destVec = latLonToVector3(destLat, destLon, globeRadius).normalize();

  // Great-circle midpoint
  const midVec = originVec.clone().add(destVec).normalize();

  // Angular distance between origin and destination
  const dot = Math.min(Math.max(originVec.dot(destVec), -1), 1);
  const angle = Math.acos(dot);

  // Dynamic distance based on angular distance
  let camDist = 240;
  if (angle > 1.8) {
    camDist = 285; // Far global destinations (e.g. Americas)
  } else if (angle > 1.0) {
    camDist = 250; // Trans-continental Eurasian corridors (e.g. Russia, Europe)
  } else {
    camDist = 225; // Regional neighborhood (e.g. Bangladesh, UAE, Iran)
  }

  // Ensure slight northern elevation for standard cartographic perspective
  const tilted = midVec.clone();
  tilted.y = Math.max(tilted.y, 0.28);
  tilted.normalize();

  return tilted.multiplyScalar(camDist);
}

/**
 * Resolve geographic coordinates for a given port name string
 */
export function resolvePortCoordinates(
  portName: string,
  stateHint?: string,
  latFallback?: number,
  lonFallback?: number
): { lat: number; lon: number; matchedName: string; state: string } {
  if (latFallback !== undefined && lonFallback !== undefined && latFallback !== 0 && lonFallback !== 0) {
    return {
      lat: latFallback,
      lon: lonFallback,
      matchedName: portName,
      state: stateHint || 'India Maritime Gateway',
    };
  }

  const clean = portName.toLowerCase().trim();
  for (const port of KNOWN_PORT_COORDINATES) {
    if (port.aliases.some((alias) => clean.includes(alias) || alias.includes(clean))) {
      return {
        lat: port.lat,
        lon: port.lon,
        matchedName: port.name,
        state: port.state,
      };
    }
  }

  // Western coast default if unindexed
  return {
    lat: 19.0,
    lon: 72.8,
    matchedName: portName,
    state: stateHint || 'Major Gateway Port',
  };
}

/**
 * Resolve target destination country coordinates
 */
export function resolveCountryCoordinates(countryName?: string): {
  lat: number;
  lon: number;
  label: string;
  code: string;
} {
  const norm = (countryName || 'RUSSIA').toUpperCase().trim();
  if (COUNTRY_COORDINATES[norm]) {
    return COUNTRY_COORDINATES[norm];
  }
  // Check partial
  for (const [key, val] of Object.entries(COUNTRY_COORDINATES)) {
    if (norm.includes(key) || key.includes(norm)) {
      return val;
    }
  }
  return {
    lat: 55.75,
    lon: 37.61,
    label: `${countryName || 'Foreign Partner'} Destination Region`,
    code: norm.slice(0, 2),
  };
}

/**
 * Convert Latitude & Longitude to 3D Cartesian coordinates on a sphere of radius R.
 * Math-aligned with standard Three.js UV sphere geometry.
 */
export function latLonToVector3(lat: number, lon: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);
  return new THREE.Vector3(x, y, z);
}

/**
 * Generate 3D Great-Circle Arc points elevated above the Earth's surface.
 * Creates an oceanic curve peaking at the midpoint.
 */
export function createGreatCircleArcPoints(
  startVec: THREE.Vector3,
  endVec: THREE.Vector3,
  globeRadius: number,
  numSegments = 64,
  maxAltitudeFraction = 0.22
): THREE.Vector3[] {
  const points: THREE.Vector3[] = [];
  const v1 = startVec.clone().normalize();
  const v2 = endVec.clone().normalize();

  // Angular distance in radians
  const dot = Math.min(Math.max(v1.dot(v2), -1), 1);
  const angle = Math.acos(dot);

  // Peak altitude proportional to distance, capped to look oceanic and realistic
  const peakAltitude = globeRadius * Math.min(maxAltitudeFraction, Math.max(0.08, angle * 0.16));

  for (let i = 0; i <= numSegments; i++) {
    const t = i / numSegments;
    // Slerp (Spherical Linear Interpolation)
    let slerped: THREE.Vector3;
    if (angle < 0.001) {
      slerped = v1.clone();
    } else {
      const sinAngle = Math.sin(angle);
      const a = Math.sin((1 - t) * angle) / sinAngle;
      const b = Math.sin(t * angle) / sinAngle;
      slerped = new THREE.Vector3(
        a * v1.x + b * v2.x,
        a * v1.y + b * v2.y,
        a * v1.z + b * v2.z
      ).normalize();
    }

    // Parabolic elevation curve: sin(t * pi)
    const altitude = Math.sin(t * Math.PI) * peakAltitude;
    const currentRadius = globeRadius + altitude;
    points.push(slerped.multiplyScalar(currentRadius));
  }

  return points;
}

export interface NormalizedAlternativePort {
  id: string;
  port: string;
  state?: string;
  affinity_score: number;
  confidence?: number;
  handling_capacity_pct?: number;
  cargo_mt?: number;
  share_pct?: number;
  redundancy_status?: string;
  source_port?: string;
  raw?: any;
}

/**
 * Standardize alternative ports returned by the backend in either:
 * - scData.alternative_paths.alternative_ports (agent MultiDiGraph output)
 * - scData.alternative_paths (mock array or flat list)
 * - scData.network_resilience.modeled_alternative_ports
 */
export function extractAlternativePorts(rawInput: any): NormalizedAlternativePort[] {
  if (!rawInput) return [];

  let list: any[] = [];
  if (Array.isArray(rawInput)) {
    list = rawInput;
  } else if (typeof rawInput === 'object') {
    if (Array.isArray(rawInput.alternative_ports)) {
      list = rawInput.alternative_ports;
    } else if (Array.isArray(rawInput.modeled_alternative_ports)) {
      list = rawInput.modeled_alternative_ports;
    } else if (rawInput.alternative_paths) {
      return extractAlternativePorts(rawInput.alternative_paths);
    }
  }

  return list.map((item, idx) => {
    const portName = item.alternate_port || item.port || item.name || `Alternative Port ${idx + 1}`;
    const rawAffinity = item.affinity_score ?? item.confidence ?? item.affinity ?? 0.8;
    const affinity_score = rawAffinity > 1 ? rawAffinity / 100 : rawAffinity;

    return {
      id: `alt-${idx}-${portName.replace(/\s+/g, '-').toLowerCase()}`,
      port: portName,
      state: item.state || 'India Maritime Terminal',
      affinity_score,
      confidence: item.confidence,
      handling_capacity_pct: item.handling_capacity_pct ?? item.buffer ?? item.capacity_pct,
      cargo_mt: item.cargo_mt,
      share_pct: item.share_pct,
      redundancy_status: item.redundancy_status || (affinity_score >= 0.85 ? 'Viable Alternative' : 'Secondary Option'),
      source_port: item.source_port,
      raw: item,
    };
  });
}

