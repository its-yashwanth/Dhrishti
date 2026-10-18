import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import {
  Plus,
  Minus,
  RotateCcw,
  Crosshair,
  Info,
  ShieldCheck,
  AlertTriangle,
  Anchor,
  Globe2,
  Navigation,
  Layers
} from 'lucide-react';
import { PortNode, AlternativePath, SeverityLevel } from '../../types/drishti';
import {
  resolvePortCoordinates,
  resolveCountryCoordinates,
  latLonToVector3,
  createGreatCircleArcPoints,
  computeOptimalCorridorCameraPosition,
  extractAlternativePorts,
  NormalizedAlternativePort
} from './portCoordinates';

export interface SupplyChainGlobe3DProps {
  criticalPorts: PortNode[];
  alternativePaths: any;
  selectedPortName?: string | null;
  selectedPort?: PortNode | null;
  hoveredPortName?: string | null;
  onSelectPortName?: (portName: string | null, portData?: any) => void;
  onSelectPort?: (port: PortNode) => void;
  onHoverPortName?: (portName: string | null) => void;
  eventCountry?: string;
  commodity?: string;
  focusPortTrigger?: { portName: string; timestamp: number } | null;
}

interface HoveredNodeInfo {
  type: 'port' | 'destination' | 'route';
  name: string;
  state?: string;
  status: string;
  statusColor: string;
  metrics?: { label: string; value: string }[];
  note?: string;
  x: number;
  y: number;
}

const GLOBE_RADIUS = 100;

export const SupplyChainGlobe3D: React.FC<SupplyChainGlobe3DProps> = ({
  criticalPorts,
  alternativePaths,
  selectedPortName,
  selectedPort,
  hoveredPortName,
  onSelectPortName,
  onSelectPort,
  onHoverPortName,
  eventCountry = 'RUSSIA',
  commodity = 'Wheat',
  focusPortTrigger = null,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [hoveredNode, setHoveredNode] = useState<HoveredNodeInfo | null>(null);

  // Active selection / hover states supporting both prop variants
  const activeSelectedPortName = useMemo(() => {
    if (selectedPortName !== undefined) return selectedPortName;
    return selectedPort?.port || null;
  }, [selectedPortName, selectedPort]);

  const activeHoveredPortName = hoveredPortName || null;

  // Normalized alternative ports from backend data
  const normalizedAltPorts = useMemo(() => {
    return extractAlternativePorts(alternativePaths);
  }, [alternativePaths]);

  // Target destination coordinates (e.g. Russia, Bangladesh, China, etc.)
  const destCoords = useMemo(() => resolveCountryCoordinates(eventCountry), [eventCountry]);
  const destVec = useMemo(
    () => latLonToVector3(destCoords.lat, destCoords.lon, GLOBE_RADIUS),
    [destCoords]
  );

  // Unified port nodes: combines critical gateway ports and all modeled alternative ports
  const unifiedPorts = useMemo(() => {
    const list: any[] = [];
    const addedNames = new Set<string>();

    const normalizeKey = (str: string) => str.toLowerCase().replace(/[^a-z0-9]/g, '');

    // 1. Critical gateway ports
    criticalPorts.forEach((cp) => {
      const coords = resolvePortCoordinates(cp.port, cp.state, cp.lat, cp.lon);
      const vec3 = latLonToVector3(coords.lat, coords.lon, GLOBE_RADIUS);
      const altMatch = normalizedAltPorts.find((ap) => {
        const k1 = normalizeKey(ap.port);
        const k2 = normalizeKey(cp.port);
        return k1.includes(k2) || k2.includes(k1);
      });

      const item = {
        id: `gateway-${cp.port}`,
        port: cp.port,
        resolvedName: coords.matchedName,
        state: cp.state || coords.state,
        lat: coords.lat,
        lon: coords.lon,
        vec3,
        isGateway: true,
        risk_level: cp.risk_level,
        cargo_share_pct: cp.cargo_share_pct,
        betweenness_centrality: cp.betweenness_centrality,
        composite_importance: cp.composite_importance,
        identification_basis: cp.identification_basis,
        note: cp.note,
        isAlternative: !!altMatch,
        altData: altMatch || null,
        raw: cp,
      };
      list.push(item);
      addedNames.add(normalizeKey(cp.port));
      addedNames.add(normalizeKey(coords.matchedName));
    });

    // 2. Modeled alternative ports not already included (e.g. Pipavav Port)
    normalizedAltPorts.forEach((ap) => {
      const cleanKey = normalizeKey(ap.port);
      const alreadyPresent = Array.from(addedNames).some(
        (name) => cleanKey.includes(name) || name.includes(cleanKey)
      );

      if (!alreadyPresent) {
        const coords = resolvePortCoordinates(ap.port, ap.state);
        const vec3 = latLonToVector3(coords.lat, coords.lon, GLOBE_RADIUS);
        const item = {
          id: `alt-${ap.port}`,
          port: ap.port,
          resolvedName: coords.matchedName,
          state: ap.state || coords.state,
          lat: coords.lat,
          lon: coords.lon,
          vec3,
          isGateway: false,
          risk_level: 'LOW' as SeverityLevel,
          cargo_share_pct: ap.share_pct,
          betweenness_centrality: undefined,
          composite_importance: undefined,
          identification_basis: 'Modeled Alternative Handling Port',
          note: `Inferred alternative handling port with ${(ap.affinity_score * 100).toFixed(0)}% modeled affinity to absorb diverted flows.`,
          isAlternative: true,
          altData: ap,
          raw: ap.raw || ap,
        };
        list.push(item);
        addedNames.add(cleanKey);
        addedNames.add(normalizeKey(coords.matchedName));
      }
    });

    return list;
  }, [criticalPorts, normalizedAltPorts]);

  // Primary scenario bottleneck gateway (source of the RED primary connection)
  const primaryPort = useMemo(() => {
    // If selected port is a primary bottleneck
    if (activeSelectedPortName) {
      const match = unifiedPorts.find((p) =>
        p.port.toLowerCase().includes(activeSelectedPortName.toLowerCase()) ||
        activeSelectedPortName.toLowerCase().includes(p.port.toLowerCase())
      );
      if (match && (match.risk_level === 'HIGH' || match.risk_level === 'CRITICAL')) {
        return match;
      }
    }
    // Otherwise top bottleneck port
    const highRisk = unifiedPorts.find((p) => p.risk_level === 'HIGH' || p.risk_level === 'CRITICAL');
    return highRisk || unifiedPorts[0] || null;
  }, [unifiedPorts, activeSelectedPortName]);

  // Dynamic corridor camera position framing both India and destination country
  const corridorCameraPos = useMemo(() => {
    return computeOptimalCorridorCameraPosition(
      destCoords.lat,
      destCoords.lon,
      21.0,
      72.0,
      GLOBE_RADIUS
    );
  }, [destCoords]);

  // References for Three.js objects
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const animFrameIdRef = useRef<number | null>(null);
  const particlesGroupRef = useRef<THREE.Group | null>(null);
  const routesGroupRef = useRef<THREE.Group | null>(null);
  const markersGroupRef = useRef<THREE.Group | null>(null);
  const interactiveHitboxesRef = useRef<{ mesh: THREE.Mesh; data: any; type: 'port' | 'destination' | 'route' }[]>([]);

  // Camera smooth transition helper
  const animateCameraTo = useCallback((targetPos: THREE.Vector3, duration = 850) => {
    if (!cameraRef.current || !controlsRef.current) return;
    const cam = cameraRef.current;
    const controls = controlsRef.current;

    const startPos = cam.position.clone();
    const startTime = performance.now();

    function step(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Smooth cubic bezier easing
      const ease =
        progress < 0.5
          ? 4 * progress * progress * progress
          : 1 - Math.pow(-2 * progress + 2, 3) / 2;

      cam.position.lerpVectors(startPos, targetPos, ease);
      controls.target.set(0, 0, 0);
      controls.update();

      if (progress < 1) {
        requestAnimationFrame(step);
      }
    }
    requestAnimationFrame(step);
  }, []);

  // Reset Camera View handler
  const handleResetView = useCallback(() => {
    animateCameraTo(corridorCameraPos, 800);
  }, [animateCameraTo, corridorCameraPos]);

  // Focus on Selected Port
  const handleFocusPort = useCallback((portVec: THREE.Vector3) => {
    const targetDir = portVec.clone().normalize();
    const targetPos = targetDir.multiplyScalar(215);
    animateCameraTo(targetPos, 750);
  }, [animateCameraTo]);

  // Handle focusPortTrigger when right-side card is clicked
  useEffect(() => {
    if (!focusPortTrigger || !focusPortTrigger.portName) return;
    const target = unifiedPorts.find((p) =>
      p.port.toLowerCase().includes(focusPortTrigger.portName.toLowerCase()) ||
      focusPortTrigger.portName.toLowerCase().includes(p.port.toLowerCase())
    );
    if (target && target.vec3) {
      handleFocusPort(target.vec3);
    }
  }, [focusPortTrigger, unifiedPorts, handleFocusPort]);

  // Main Three.js Scene Setup & Render Loop
  useEffect(() => {
    if (!containerRef.current || !canvasRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    // 1. Scene
    const scene = new THREE.Scene();
    sceneRef.current = scene;
    scene.background = new THREE.Color(0x040711);

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 1, 2000);
    camera.position.copy(corridorCameraPos);
    cameraRef.current = camera;

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current,
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    rendererRef.current = renderer;

    // 4. Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.rotateSpeed = 0.75;
    controls.zoomSpeed = 0.9;
    controls.minDistance = 125;
    controls.maxDistance = 450;
    controls.enablePan = false;
    controlsRef.current = controls;

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0x223348, 1.25);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 2.4);
    dirLight1.position.set(250, 200, -250);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x38bdf8, 0.85);
    dirLight2.position.set(-200, -100, 200);
    scene.add(dirLight2);

    // 6. Globe Base Sphere with Real NASA Earth Texture & Ocean Specular
    const textureLoader = new THREE.TextureLoader();
    const earthTexture = textureLoader.load('/data/earth_atmos_2048.jpg', () => {
      setIsLoading(false);
    });
    const specularTexture = textureLoader.load('/data/earth_specular_2048.jpg');

    const earthGeo = new THREE.SphereGeometry(GLOBE_RADIUS, 64, 64);
    const earthMat = new THREE.MeshStandardMaterial({
      map: earthTexture,
      roughnessMap: specularTexture,
      roughness: 0.55,
      metalness: 0.12,
      color: 0xcccccc,
    });
    const earthMesh = new THREE.Mesh(earthGeo, earthMat);
    scene.add(earthMesh);

    // 7. Atmospheric Glow Rim
    const atmosGeo = new THREE.SphereGeometry(GLOBE_RADIUS * 1.018, 64, 64);
    const atmosMat = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.68 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.2);
          gl_FragColor = vec4(0.02, 0.72, 0.85, 1.0) * intensity * 0.75;
        }
      `,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true,
    });
    const atmosMesh = new THREE.Mesh(atmosGeo, atmosMat);
    scene.add(atmosMesh);

    // 8. Groups for dynamic elements
    const routesGroup = new THREE.Group();
    routesGroupRef.current = routesGroup;
    scene.add(routesGroup);

    const markersGroup = new THREE.Group();
    markersGroupRef.current = markersGroup;
    scene.add(markersGroup);

    const particlesGroup = new THREE.Group();
    particlesGroupRef.current = particlesGroup;
    scene.add(particlesGroup);

    // 9. Load Country Boundaries (GeoJSON Vector Outlines on 3D Sphere)
    fetch('/data/world_countries.json')
      .then((res) => res.json())
      .then((geoData) => {
        const linesGroup = new THREE.Group();
        const baseMat = new THREE.LineBasicMaterial({
          color: 0x334e68,
          transparent: true,
          opacity: 0.42,
          linewidth: 1,
        });
        const indiaMat = new THREE.LineBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.95,
          linewidth: 2,
        });
        const targetMat = new THREE.LineBasicMaterial({
          color: 0xf43f5e,
          transparent: true,
          opacity: 0.85,
          linewidth: 2,
        });

        const targetNorm = eventCountry.toLowerCase().trim();

        geoData.features.forEach((feature: any) => {
          const name = (feature.properties?.name || '').toLowerCase();
          const isIndia = name === 'india';
          const isTarget = name === targetNorm || name.includes(targetNorm) || targetNorm.includes(name);

          const mat = isIndia ? indiaMat : isTarget ? targetMat : baseMat;
          const geomType = feature.geometry?.type;
          const coordinates = feature.geometry?.coordinates;

          if (!coordinates) return;

          const renderRings = (rings: number[][][]) => {
            rings.forEach((ring) => {
              const points: THREE.Vector3[] = [];
              ring.forEach(([lon, lat]) => {
                points.push(latLonToVector3(lat, lon, GLOBE_RADIUS * 1.0025));
              });
              if (points.length > 2) {
                const geom = new THREE.BufferGeometry().setFromPoints(points);
                const line = new THREE.LineLoop(geom, mat);
                linesGroup.add(line);
              }
            });
          };

          if (geomType === 'Polygon') {
            renderRings(coordinates);
          } else if (geomType === 'MultiPolygon') {
            coordinates.forEach((poly: any) => renderRings(poly));
          }
        });

        scene.add(linesGroup);
      })
      .catch((err) => console.warn('Could not load world boundaries:', err));

    // Resize handler
    const handleResize = () => {
      if (!containerRef.current || !cameraRef.current || !rendererRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // Animation Render Loop
    let particleClock = 0;
    const animate = () => {
      animFrameIdRef.current = requestAnimationFrame(animate);
      controls.update();

      // Flowing particle streams along trade corridors
      particleClock += 0.007;
      if (particlesGroupRef.current) {
        particlesGroupRef.current.children.forEach((child: any) => {
          if (child.userData?.curvePoints) {
            const curvePts: THREE.Vector3[] = child.userData.curvePoints;
            const offset: number = child.userData.offset || 0;
            const speed: number = child.userData.speed || 1;
            const progress = (particleClock * speed + offset) % 1;
            const idx = Math.floor(progress * (curvePts.length - 1));
            const nextIdx = Math.min(idx + 1, curvePts.length - 1);
            const subT = progress * (curvePts.length - 1) - idx;
            child.position.lerpVectors(curvePts[idx], curvePts[nextIdx], subT);
          }
        });
      }

      // Gentle pulsing of beacon rings
      if (markersGroupRef.current) {
        const pulse = 1 + Math.sin(particleClock * 7.5) * 0.14;
        markersGroupRef.current.children.forEach((child: any) => {
          if (child.userData?.isPulseRing) {
            child.scale.set(pulse, pulse, pulse);
          }
        });
      }

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current);
      controls.dispose();
      renderer.dispose();
    };
  }, [eventCountry, corridorCameraPos]);

  // Clean memory helper
  const cleanGroup = (group: THREE.Group) => {
    while (group.children.length > 0) {
      const obj: any = group.children[0];
      group.remove(obj);
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) {
          obj.material.forEach((m: any) => m.dispose());
        } else {
          obj.material.dispose();
        }
      }
    }
  };

  // Match helper
  const isPortMatch = useCallback((name1?: string | null, name2?: string | null) => {
    if (!name1 || !name2) return false;
    const clean1 = name1.toLowerCase().replace(/[^a-z0-9]/g, '');
    const clean2 = name2.toLowerCase().replace(/[^a-z0-9]/g, '');
    return clean1.includes(clean2) || clean2.includes(clean1);
  }, []);

  // Update Dynamic Visual Elements: Routes, Markers, Beacons, and Particle Streams
  useEffect(() => {
    if (!routesGroupRef.current || !markersGroupRef.current || !particlesGroupRef.current) return;

    const routesGroup = routesGroupRef.current;
    const markersGroup = markersGroupRef.current;
    const particlesGroup = particlesGroupRef.current;
    interactiveHitboxesRef.current = [];

    cleanGroup(routesGroup);
    cleanGroup(markersGroup);
    cleanGroup(particlesGroup);

    // -------------------------------------------------------------
    // 1. Destination Marker (Target Foreign Region / Port)
    // -------------------------------------------------------------
    const destGroup = new THREE.Group();
    destGroup.position.copy(destVec);

    // Destination Core Sphere
    const destCoreGeo = new THREE.SphereGeometry(2.1, 16, 16);
    const destCoreMat = new THREE.MeshBasicMaterial({ color: 0xef4444 });
    const destCoreMesh = new THREE.Mesh(destCoreGeo, destCoreMat);
    destGroup.add(destCoreMesh);

    // Destination Pulsing Halo Ring
    const destRingGeo = new THREE.RingGeometry(2.7, 4.0, 32);
    const destRingMat = new THREE.MeshBasicMaterial({
      color: 0xf43f5e,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.72,
    });
    const destRingMesh = new THREE.Mesh(destRingGeo, destRingMat);
    destRingMesh.lookAt(destVec.clone().multiplyScalar(2));
    destRingMesh.userData = { isPulseRing: true };
    destGroup.add(destRingMesh);

    // Destination Vertical Luminous Beacon
    const destBeaconGeo = new THREE.CylinderGeometry(0.3, 0.3, 15, 8);
    destBeaconGeo.translate(0, 7.5, 0);
    const destBeaconMat = new THREE.MeshBasicMaterial({
      color: 0xef4444,
      transparent: true,
      opacity: 0.75,
    });
    const destBeaconMesh = new THREE.Mesh(destBeaconGeo, destBeaconMat);
    destBeaconMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), destVec.clone().normalize());
    destGroup.add(destBeaconMesh);

    // Hitbox for Destination
    const destHitboxGeo = new THREE.SphereGeometry(5.2, 8, 8);
    const destHitboxMat = new THREE.MeshBasicMaterial({ visible: false });
    const destHitboxMesh = new THREE.Mesh(destHitboxGeo, destHitboxMat);
    destHitboxMesh.position.copy(destVec);
    destGroup.add(destHitboxMesh);
    interactiveHitboxesRef.current.push({
      mesh: destHitboxMesh,
      data: { name: destCoords.label, state: eventCountry, status: 'Scenario Destination Region' },
      type: 'destination',
    });

    markersGroup.add(destGroup);

    // -------------------------------------------------------------
    // 2. PRIMARY SCENARIO CONNECTION — RED
    // Elevated Great-Circle Arc from Primary Indian Gateway to Destination
    // -------------------------------------------------------------
    if (primaryPort) {
      const isPrimarySelected = isPortMatch(activeSelectedPortName, primaryPort.port);
      const isPrimaryHovered = isPortMatch(activeHoveredPortName, primaryPort.port);
      const primaryHighlighted = isPrimarySelected || isPrimaryHovered;

      const primaryPoints = createGreatCircleArcPoints(primaryPort.vec3, destVec, GLOBE_RADIUS, 72, 0.23);
      const primaryCurve = new THREE.CatmullRomCurve3(primaryPoints);

      // Elevated 3D Tube: Visually prominent scenario connection
      const primaryRadius = primaryHighlighted ? 1.05 : 0.85;
      const primaryTubeGeo = new THREE.TubeGeometry(primaryCurve, 72, primaryRadius, 8, false);
      const primaryTubeMat = new THREE.MeshBasicMaterial({
        color: 0xef4444,
        transparent: true,
        opacity: primaryHighlighted ? 0.98 : 0.85,
      });
      const primaryTubeMesh = new THREE.Mesh(primaryTubeGeo, primaryTubeMat);
      routesGroup.add(primaryTubeMesh);

      // Directional Flow Particles along Primary Corridor (Red/White)
      const numParticles = 8;
      const particleGeo = new THREE.SphereGeometry(1.2, 8, 8);
      const particleMat = new THREE.MeshBasicMaterial({ color: 0xffffff });

      for (let i = 0; i < numParticles; i++) {
        const particleMesh = new THREE.Mesh(particleGeo, particleMat);
        particleMesh.userData = {
          curvePoints: primaryPoints,
          offset: i / numParticles,
          speed: 1.05,
        };
        particlesGroup.add(particleMesh);
      }
    }

    // -------------------------------------------------------------
    // 3. MODELED ALTERNATIVE HANDLING PATHS — GREEN
    // Elevated Great-Circle Arcs from each Alternative Port to Destination
    // -------------------------------------------------------------
    normalizedAltPorts.forEach((altPort, altIdx) => {
      // Find matching port in unified ports list
      const matchedUnified = unifiedPorts.find((p) => isPortMatch(p.port, altPort.port));
      const portVec = matchedUnified ? matchedUnified.vec3 : latLonToVector3(20.0, 72.5, GLOBE_RADIUS);

      const isThisAltHovered = isPortMatch(activeHoveredPortName, altPort.port);
      const isThisAltSelected = isPortMatch(activeSelectedPortName, altPort.port);
      const isHighlighted = isThisAltHovered || isThisAltSelected;

      // Stagger altitude slightly so paths from nearby western ports don't overlap
      const altitudeFraction = 0.16 + (altIdx % 3) * 0.018;
      const altPoints = createGreatCircleArcPoints(portVec, destVec, GLOBE_RADIUS, 64, altitudeFraction);
      const altCurve = new THREE.CatmullRomCurve3(altPoints);

      // Tube Geometry for Modeled Alternative Handling Path
      const tubeRadius = isHighlighted ? 0.72 : 0.44;
      const altTubeGeo = new THREE.TubeGeometry(altCurve, 64, tubeRadius, 6, false);
      const altTubeMat = new THREE.MeshBasicMaterial({
        color: isHighlighted ? 0x34d399 : 0x10b981,
        transparent: true,
        opacity: isHighlighted ? 1.0 : activeHoveredPortName ? 0.45 : 0.72,
      });
      const altTubeMesh = new THREE.Mesh(altTubeGeo, altTubeMat);
      routesGroup.add(altTubeMesh);

      // Emerald Directional Flow Particles along Alternative Handling Path
      const numAltParticles = 5;
      const altParticleGeo = new THREE.SphereGeometry(isHighlighted ? 1.1 : 0.8, 6, 6);
      const altParticleMat = new THREE.MeshBasicMaterial({
        color: isHighlighted ? 0x6ee7b7 : 0x34d399,
      });

      for (let j = 0; j < numAltParticles; j++) {
        const altParticle = new THREE.Mesh(altParticleGeo, altParticleMat);
        altParticle.userData = {
          curvePoints: altPoints,
          offset: j / numAltParticles,
          speed: 0.92,
        };
        particlesGroup.add(altParticle);
      }
    });

    // -------------------------------------------------------------
    // 4. PORT MARKERS (Unified Primary, Alternative & Gateway Nodes)
    // -------------------------------------------------------------
    unifiedPorts.forEach((port) => {
      const isSelected = isPortMatch(activeSelectedPortName, port.port);
      const isHovered = isPortMatch(activeHoveredPortName, port.port);
      const isPrimary = primaryPort ? isPortMatch(primaryPort.port, port.port) : false;
      const isAlt = port.isAlternative;

      // Color coding per strict specifications:
      // - Primary bottleneck gateway: RED
      // - Modeled alternative handling port: GREEN
      // - Selected state: CYAN highlight
      // - Evaluated Indian Gateway: Risk tier or cyan/slate
      let markerColor = 0x64748b; // Neutral slate
      if (isSelected) {
        markerColor = 0x06b6d4; // Cyan selected
      } else if (isPrimary) {
        markerColor = 0xef4444; // Red primary scenario bottleneck
      } else if (isAlt) {
        markerColor = 0x10b981; // Green modeled alternative
      } else if (port.risk_level === 'HIGH' || port.risk_level === 'CRITICAL') {
        markerColor = 0xef4444;
      } else if (port.risk_level === 'MODERATE') {
        markerColor = 0xf59e0b; // Amber
      } else {
        markerColor = 0x38bdf8; // Cyan/blue
      }

      const portGroup = new THREE.Group();
      portGroup.position.copy(port.vec3);

      // Core Marker Sphere
      let baseRadius = isPrimary ? 1.85 : isAlt ? 1.55 : 1.15;
      if (isHovered || isSelected) baseRadius *= 1.25;

      const coreGeo = new THREE.SphereGeometry(baseRadius, 16, 16);
      const coreMat = new THREE.MeshBasicMaterial({ color: markerColor });
      const coreMesh = new THREE.Mesh(coreGeo, coreMat);
      portGroup.add(coreMesh);

      // Pulsing Halo Ring for Primary Bottleneck, Alternative Port, or Selected Node
      if (isPrimary || isAlt || isSelected) {
        const ringGeo = new THREE.RingGeometry(baseRadius * 1.35, baseRadius * 2.15, 24);
        const ringMat = new THREE.MeshBasicMaterial({
          color: markerColor,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: isHovered || isSelected ? 0.95 : 0.65,
        });
        const ringMesh = new THREE.Mesh(ringGeo, ringMat);
        ringMesh.lookAt(port.vec3.clone().multiplyScalar(2));
        ringMesh.userData = { isPulseRing: true };
        portGroup.add(ringMesh);

        // Vertical Luminous Beacon
        const beaconHeight = isPrimary ? 13 : isAlt ? 9.5 : 7;
        const beaconGeo = new THREE.CylinderGeometry(0.2, 0.2, beaconHeight, 8);
        beaconGeo.translate(0, beaconHeight / 2, 0);
        const beaconMat = new THREE.MeshBasicMaterial({
          color: markerColor,
          transparent: true,
          opacity: isHovered || isSelected ? 0.9 : 0.65,
        });
        const beaconMesh = new THREE.Mesh(beaconGeo, beaconMat);
        beaconMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), port.vec3.clone().normalize());
        portGroup.add(beaconMesh);
      }

      // Interactive Raycast Hitbox
      const hitboxGeo = new THREE.SphereGeometry(4.8, 8, 8);
      const hitboxMat = new THREE.MeshBasicMaterial({ visible: false });
      const hitboxMesh = new THREE.Mesh(hitboxGeo, hitboxMat);
      portGroup.add(hitboxMesh);
      interactiveHitboxesRef.current.push({
        mesh: hitboxMesh,
        data: port,
        type: 'port',
      });

      markersGroup.add(portGroup);
    });
  }, [
    unifiedPorts,
    normalizedAltPorts,
    primaryPort,
    destVec,
    destCoords,
    activeSelectedPortName,
    activeHoveredPortName,
    eventCountry,
    isPortMatch,
  ]);

  // Mouse Raycaster for Interactivity & Tooltips
  const handlePointerMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current || !cameraRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(new THREE.Vector2(mouseX, mouseY), cameraRef.current);

    const hitboxes = interactiveHitboxesRef.current.map((h) => h.mesh);
    const intersects = raycaster.intersectObjects(hitboxes);

    if (intersects.length > 0) {
      const hit = interactiveHitboxesRef.current.find((h) => h.mesh === intersects[0].object);
      if (hit) {
        if (hit.type === 'port') {
          const port = hit.data;
          const isPrimary = primaryPort ? isPortMatch(primaryPort.port, port.port) : false;
          const isAlt = port.isAlternative;

          // Scientifically precise status classification
          let statusLabel = 'EVALUATED INDIAN GATEWAY';
          let statusColor = 'text-cyan-400';
          if (isPrimary) {
            statusLabel = 'PRIMARY SCENARIO BOTTLENECK GATEWAY';
            statusColor = 'text-rose-400';
          } else if (isAlt) {
            statusLabel = 'MODELED ALTERNATIVE HANDLING PORT';
            statusColor = 'text-emerald-400';
          }

          const metrics = [];
          if (isAlt && port.altData) {
            const affinityPct = (port.altData.affinity_score * 100).toFixed(0);
            metrics.push({ label: 'Modeled Affinity', value: `${affinityPct}%` });
            if (port.altData.handling_capacity_pct !== undefined) {
              metrics.push({ label: 'Buffer Capacity', value: `${port.altData.handling_capacity_pct}%` });
            } else if (port.altData.cargo_mt !== undefined) {
              metrics.push({ label: 'Cargo Context', value: `${port.altData.cargo_mt} MT` });
            }
          }

          if (port.cargo_share_pct !== undefined) {
            metrics.push({ label: 'National Cargo Share', value: `${port.cargo_share_pct}%` });
          }
          if (port.betweenness_centrality !== undefined) {
            metrics.push({ label: 'Betweenness Centrality', value: port.betweenness_centrality.toFixed(3) });
          }
          if (port.risk_level && !isAlt) {
            metrics.push({ label: 'Gateway Risk Tier', value: port.risk_level });
          }

          setHoveredNode({
            type: 'port',
            name: port.port,
            state: port.state,
            status: statusLabel,
            statusColor,
            metrics,
            note: port.note || 'MoPSW Maritime Gateway Reference Node',
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
          });

          if (onHoverPortName) onHoverPortName(port.port);
        } else if (hit.type === 'destination') {
          setHoveredNode({
            type: 'destination',
            name: destCoords.label,
            state: eventCountry,
            status: 'SCENARIO DESTINATION REGION',
            statusColor: 'text-rose-400',
            metrics: [
              { label: 'Commodity', value: commodity },
              { label: 'Corridor Type', value: 'Scenario-Exposed Connection' },
              { label: 'Origin Hub', value: primaryPort?.port || 'Indian Maritime Gateways' },
            ],
            note: 'Model scenario partner destination receiving scenario-diverted trade flows.',
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
          });
          if (onHoverPortName) onHoverPortName(null);
        }

        if (containerRef.current) containerRef.current.style.cursor = 'pointer';
        return;
      }
    }

    setHoveredNode(null);
    if (onHoverPortName) onHoverPortName(null);
    if (containerRef.current) containerRef.current.style.cursor = 'default';
  };

  // Click Handler for Ports
  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current || !cameraRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(new THREE.Vector2(mouseX, mouseY), cameraRef.current);

    const hitboxes = interactiveHitboxesRef.current.map((h) => h.mesh);
    const intersects = raycaster.intersectObjects(hitboxes);

    if (intersects.length > 0) {
      const hit = interactiveHitboxesRef.current.find((h) => h.mesh === intersects[0].object);
      if (hit && hit.type === 'port') {
        const portData = hit.data;
        if (onSelectPortName) onSelectPortName(portData.port, portData);
        if (onSelectPort && portData.raw) onSelectPort(portData.raw);
        handleFocusPort(portData.vec3);
        return;
      }
    } else {
      // If clicking background or empty space, clear selection
      if (onSelectPortName) onSelectPortName(null);
    }
  };

  // Zoom handlers
  const handleZoomIn = () => {
    if (!cameraRef.current || !controlsRef.current) return;
    cameraRef.current.position.multiplyScalar(0.85);
    controlsRef.current.update();
  };

  const handleZoomOut = () => {
    if (!cameraRef.current || !controlsRef.current) return;
    cameraRef.current.position.multiplyScalar(1.18);
    controlsRef.current.update();
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handlePointerMove}
      onClick={handleClick}
      className="flex-1 w-full h-full relative flex flex-col bg-[#03060e] overflow-hidden select-none"
    >
      {/* Three.js Canvas */}
      <canvas ref={canvasRef} className="w-full h-full flex-1 block" />

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/85 z-20 space-y-3">
          <div className="w-10 h-10 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
          <div className="text-xs font-mono text-cyan-300">
            Initializing 3D Orbital Earth & Maritime Logistics Mesh...
          </div>
        </div>
      )}

      {/* Top Left Intelligence Badge */}
      <div className="absolute top-4 left-4 z-10 flex flex-col space-y-1.5 pointer-events-none">
        <div className="flex items-center space-x-2 bg-slate-950/85 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800 shadow-xl">
          <Globe2 className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono font-bold text-white tracking-wider">
            3D GLOBAL MARITIME TRADE GLOBE
          </span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300 font-semibold">
            WebGL
          </span>
        </div>
        <div className="text-[10px] font-mono text-slate-400 bg-slate-950/75 backdrop-blur-sm px-2.5 py-1 rounded border border-slate-900 max-w-xs">
          Interactive Earth: Drag to rotate, scroll to zoom, click port to focus.
        </div>
      </div>

      {/* Compact Top-Right Standard Legend */}
      <div className="absolute top-4 right-16 z-10 hidden sm:flex flex-col space-y-1.5 bg-slate-950/90 backdrop-blur-md p-3 rounded-lg border border-slate-800 text-[10px] font-mono shadow-2xl pointer-events-auto">
        <div className="text-[9px] uppercase tracking-wider text-slate-400 font-bold border-b border-slate-800 pb-1 mb-0.5">
          CORRIDOR TOPOLOGY
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-glow-red animate-pulse shrink-0" />
          <span className="text-rose-300 font-semibold">Scenario-Exposed Connection</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-glow-green shrink-0" />
          <span className="text-emerald-300 font-semibold">Modeled Alternative Handling Path</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shrink-0" />
          <span className="text-cyan-300 font-medium">Evaluated Indian Gateway</span>
        </div>
        <div className="flex items-center space-x-2 pt-1 border-t border-slate-800/80">
          <span className="w-2 h-2 rounded-full bg-slate-400 shrink-0" />
          <span className="text-slate-400">Port Node (MoPSW Geocoded)</span>
        </div>
      </div>

      {/* Compact Map Control Buttons */}
      <div className="absolute top-4 right-4 flex flex-col space-y-1.5 z-20">
        <button
          onClick={handleZoomIn}
          title="Zoom In (+)"
          className="w-8 h-8 rounded-md bg-slate-900/90 hover:bg-slate-800 border border-slate-700 hover:border-cyan-500 text-slate-200 flex items-center justify-center transition-colors shadow-lg cursor-pointer"
        >
          <Plus className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          title="Zoom Out (-)"
          className="w-8 h-8 rounded-md bg-slate-900/90 hover:bg-slate-800 border border-slate-700 hover:border-cyan-500 text-slate-200 flex items-center justify-center transition-colors shadow-lg cursor-pointer"
        >
          <Minus className="w-4 h-4" />
        </button>
        <button
          onClick={handleResetView}
          title="Reset to Scenario Corridor View"
          className="w-8 h-8 rounded-md bg-slate-900/90 hover:bg-slate-800 border border-slate-700 hover:border-cyan-500 text-slate-200 flex items-center justify-center transition-colors shadow-lg cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => primaryPort && handleFocusPort(primaryPort.vec3)}
          title="Focus on Primary Bottleneck Port"
          className="w-8 h-8 rounded-md bg-slate-900/90 hover:bg-slate-800 border border-slate-700 hover:border-rose-500 text-rose-400 flex items-center justify-center transition-colors shadow-lg cursor-pointer"
        >
          <Crosshair className="w-4 h-4" />
        </button>
      </div>

      {/* Floating Hover Tooltip */}
      {hoveredNode && (
        <div
          className="absolute pointer-events-none z-30 p-3 rounded-lg bg-slate-950/95 border border-cyan-500/80 shadow-2xl backdrop-blur-md text-xs font-mono transition-opacity"
          style={{
            left: `${Math.min(hoveredNode.x + 14, (containerRef.current?.clientWidth || 800) - 250)}px`,
            top: `${Math.max(hoveredNode.y - 95, 12)}px`,
          }}
        >
          <div className="flex items-center justify-between space-x-3 border-b border-slate-800 pb-1.5 mb-1.5">
            <span className="font-bold text-white text-sm">{hoveredNode.name}</span>
            <span className={`text-[9px] font-bold uppercase ${hoveredNode.statusColor}`}>
              {hoveredNode.type === 'port' ? 'PORT' : 'DESTINATION'}
            </span>
          </div>
          {hoveredNode.state && (
            <div className="text-[10px] text-slate-400 mb-1">
              Location: <span className="text-slate-200 font-semibold">{hoveredNode.state}</span>
            </div>
          )}
          <div className={`text-[10px] font-bold ${hoveredNode.statusColor} mb-1.5`}>
            {hoveredNode.status}
          </div>
          {hoveredNode.metrics && hoveredNode.metrics.length > 0 && (
            <div className="grid grid-cols-2 gap-1.5 text-[9px] border-t border-slate-800/80 pt-1.5 text-slate-300">
              {hoveredNode.metrics.map((m, idx) => (
                <div key={idx}>
                  <span className="text-slate-500">{m.label}:</span>{' '}
                  <span className="text-cyan-300 font-semibold">{m.value}</span>
                </div>
              ))}
            </div>
          )}
          {hoveredNode.note && (
            <div className="text-[8px] text-slate-500 mt-1.5 italic max-w-xs">{hoveredNode.note}</div>
          )}
        </div>
      )}

      {/* Bottom Status Bar */}
      <div className="absolute bottom-3 left-3 right-3 bg-slate-950/90 backdrop-blur-md border border-slate-800/90 rounded-lg p-2.5 flex flex-wrap items-center justify-between text-xs font-mono z-10 shadow-2xl">
        <div className="flex items-center space-x-2 truncate">
          <span className="text-slate-400">Primary Corridor:</span>
          <span className="text-white font-bold">
            {primaryPort?.port || 'Indian Gateway'} → {destCoords.label}
          </span>
          <span className="text-rose-400 font-semibold text-[10px] ml-1 bg-rose-950/80 px-1.5 py-0.5 rounded border border-rose-800">
            SCENARIO-EXPOSED
          </span>
        </div>

        <div className="flex items-center space-x-4 text-[11px] text-slate-400">
          <div>
            Modeled Alternatives:{' '}
            <strong className="text-emerald-400 font-bold">{normalizedAltPorts.length} Gateways</strong>
          </div>
          <button
            onClick={handleResetView}
            className="text-cyan-400 hover:text-cyan-300 text-[10px] font-bold underline cursor-pointer"
          >
            Reset Corridor View
          </button>
        </div>
      </div>
    </div>
  );
};
