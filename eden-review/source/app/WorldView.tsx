"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { CSS2DObject, CSS2DRenderer } from "three/examples/jsm/renderers/CSS2DRenderer.js";
import { DRACOLoader } from "three/examples/jsm/loaders/DRACOLoader.js";
import { GLTFLoader, type GLTF } from "three/examples/jsm/loaders/GLTFLoader.js";
import { RGBELoader } from "three/examples/jsm/loaders/RGBELoader.js";
import { clone as cloneSkeleton } from "three/examples/jsm/utils/SkeletonUtils.js";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";

type RenderAction =
  | "idle"
  | "drink"
  | "eat"
  | "rest"
  | "gather_food"
  | "gather_water"
  | "gather_wood"
  | "gather_stone"
  | "gather_medicine"
  | "build_shelter"
  | "tend_fire"
  | "heal"
  | "assist"
  | "explore"
  | "socialize"
  | "guard"
  | "farm";

interface RenderAgent {
  id: string;
  name: string;
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  action: RenderAction;
  health: number;
  alive: boolean;
  brain: "local" | "astra" | "waiting";
  speech: string;
  speechUntil: number;
  color: string;
  seed: number;
  carrying: string;
  cargoAmount: number;
  taskPhase: "outbound" | "working" | "returning";
}

interface RenderResource {
  id: string;
  kind: "tree" | "berries" | "rock" | "herbs";
  x: number;
  y: number;
  amount: number;
}

interface RenderBuilding {
  id: string;
  kind: "fire" | "shelter" | "store" | "farm" | "water" | "clinic" | "workshop";
  x: number;
  y: number;
  level: number;
  progress?: number;
}

interface RenderProject {
  id: string;
  kind: "shelter" | "water" | "clinic" | "workshop";
  x: number;
  y: number;
  progress: number;
}

interface RenderWorld {
  minute: number;
  elapsed: number;
  weather: "Clear" | "Rain" | "Storm" | "Cold snap" | "Heat";
  fire: number;
  agents: RenderAgent[];
  resources: RenderResource[];
  buildings: RenderBuilding[];
  projects: RenderProject[];
}

interface WorldViewProps {
  worldRef: { current: RenderWorld };
  selectedId: string;
  onSelect: (id: string) => void;
  paused: boolean;
  speed: number;
}

interface CharacterRuntime {
  id: string;
  root: THREE.Group;
  model: THREE.Object3D;
  mixer: THREE.AnimationMixer;
  clips: Record<"idle" | "walk" | "run", THREE.AnimationAction | undefined>;
  activeClip: "idle" | "walk" | "run";
  label: CSS2DObject;
  labelName: HTMLSpanElement;
  labelIntent: HTMLSpanElement;
  selection: THREE.Mesh;
  bones: {
    rightArm?: THREE.Bone;
    rightForeArm?: THREE.Bone;
    rightHand?: THREE.Bone;
    leftArm?: THREE.Bone;
    leftForeArm?: THREE.Bone;
    leftHand?: THREE.Bone;
    head?: THREE.Bone;
    spine?: THREE.Bone;
  };
  heading: number;
  taskWeight: number;
  phase: number;
  taskKit: Record<string, THREE.Group>;
  separation: THREE.Vector2;
}

interface SceneRuntime {
  renderer: THREE.WebGLRenderer;
  labels: CSS2DRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  characters: Map<string, CharacterRuntime>;
  hitTargets: THREE.Object3D[];
  buildings: Map<string, THREE.Object3D>;
  projects: Map<string, THREE.Object3D>;
  waterMaterial: THREE.ShaderMaterial;
  skyMaterial: THREE.ShaderMaterial;
  stars: THREE.Points;
  rain: THREE.Points;
  sun: THREE.DirectionalLight;
  hemi: THREE.HemisphereLight;
  fireLight: THREE.PointLight;
  fireFlames: THREE.Group;
  fireSmoke: THREE.Group;
  fireEmbers: THREE.Points;
  mist: THREE.Group;
  mixers: THREE.AnimationMixer[];
  templates: {
    people: THREE.Object3D[];
    animations: THREE.AnimationClip[];
    tree: THREE.Object3D;
    deadTree: THREE.Object3D;
    rock: THREE.Object3D;
    shrub: THREE.Object3D;
    fern: THREE.Object3D;
    house: THREE.Object3D;
  };
}

interface RenderVitals {
  fps: number;
  width: number;
  height: number;
  quality: "CINEMATIC" | "ULTRA" | "HIGH" | "ADAPTIVE" | "PERFORMANCE";
}

type QualityPreset = "AUTO" | "CINEMATIC" | "PERFORMANCE";
type CameraMode = "free" | "overview" | "camp" | "follow";

// Enabled only by the separate HTML review entry point. The deployed game never
// sets this flag. Captures use this renderer and the actual loaded scene assets.
declare global {
  interface Window {
    __EDEN_QA_ENABLED__?: boolean;
    __EDEN_QA__?: {
      view: (name: string) => void;
      inspect: () => Record<string, unknown>;
      sceneImage: () => string;
      pose: (value: { id: string; clip: "idle" | "walk" | "run"; phase: number } | null) => void;
      frames: number;
    };
    __EDEN_SIM_QA__?: { advance: (seconds: number) => Record<string, unknown> };
  }
}

const CAMP_X = 24;
const CAMP_Y = 20;
const WORLD_SCALE = 1.48;
const ACTION_NAMES: Record<RenderAction, string> = {
  idle: "Deciding",
  drink: "Drinking",
  eat: "Eating",
  rest: "Resting",
  gather_food: "Foraging",
  gather_water: "Hauling water",
  gather_wood: "Cutting timber",
  gather_stone: "Collecting stone",
  gather_medicine: "Gathering herbs",
  build_shelter: "Building shelter",
  tend_fire: "Tending the fire",
  heal: "Treating an injury",
  assist: "Helping a neighbor",
  explore: "Scouting",
  socialize: "Talking",
  guard: "On watch",
  farm: "Working the plots",
};

const ASSET_URLS = {
  soldier: "/assets/characters/soldier.glb",
  michelle: "/assets/characters/michelle.glb",
  readyPlayer: "/assets/characters/readyplayer.glb",
  tree: "/assets/nature/quiver_tree_02/quiver_tree_02_1k.gltf",
  rock: "/assets/nature/rock_moss_set_01/rock_moss_set_01_1k.gltf",
  shrub: "/assets/nature/shrub_03/shrub_03_1k.gltf",
  fern: "/assets/nature/fern_02/fern_02_1k.gltf",
  house: "/assets/settlement/forest_house.glb",
  environment: "/assets/environment/venice_sunset_1k.hdr",
  ground: "/assets/ground/aerial_ground_rock_diff_1k.jpg",
  groundNormal: "/assets/ground/aerial_ground_rock_nor_gl_1k.jpg",
  groundArm: "/assets/ground/aerial_ground_rock_arm_1k.jpg",
  groundHeight: "/assets/ground/aerial_ground_rock_disp_1k.jpg",
};

function seeded(seed: number) {
  let value = seed >>> 0;
  return () => {
    value += 0x6d2b79f5;
    let t = value;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function smoothstep(edge0: number, edge1: number, value: number) {
  const t = THREE.MathUtils.clamp((value - edge0) / (edge1 - edge0), 0, 1);
  return t * t * (3 - 2 * t);
}

function riverX(worldY: number) {
  return 9 + worldY * 0.2 + Math.sin(worldY * 0.31) * 2.4;
}

function terrainHeight(worldX: number, worldY: number) {
  const broad = Math.sin(worldX * 0.18) * 0.62 + Math.cos(worldY * 0.22) * 0.54;
  const detail = Math.sin((worldX + worldY) * 0.44) * 0.16 + Math.cos((worldX - worldY) * 0.37) * 0.13;
  const eastRidge = smoothstep(28, 45, worldX) * (0.5 + Math.max(0, Math.sin(worldY * 0.21)) * 1.75);
  const campFlatten = 1 - smoothstep(4.5, 10, Math.hypot(worldX - CAMP_X, worldY - CAMP_Y));
  const riverDistance = Math.abs(worldX - riverX(worldY));
  const channel = (1 - smoothstep(0.55, 2.2, riverDistance)) * 1.55;
  return (broad + detail + eastRidge) * (1 - campFlatten * 0.78) - channel - 0.18;
}

function scenePosition(worldX: number, worldY: number, out = new THREE.Vector3()) {
  return out.set(
    (worldX - CAMP_X) * WORLD_SCALE,
    terrainHeight(worldX, worldY) + 0.06,
    (worldY - CAMP_Y) * WORLD_SCALE,
  );
}

function configureTexture(texture: THREE.Texture, repeatX = 11, repeatY = 9, anisotropy = 4) {
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(repeatX, repeatY);
  texture.anisotropy = anisotropy;
  texture.colorSpace = texture.name.includes("diff") ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  return texture;
}

function prepareAsset(root: THREE.Object3D, anisotropy: number, shadows = true) {
  root.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (!mesh.isMesh) return;
    mesh.castShadow = shadows;
    mesh.receiveShadow = true;
    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    for (const material of materials) {
      const standard = material as THREE.MeshStandardMaterial;
      if (standard.map) {
        standard.map.anisotropy = anisotropy;
        standard.map.colorSpace = THREE.SRGBColorSpace;
      }
      if (standard.normalMap) standard.normalMap.anisotropy = anisotropy;
      if (/leaf|fern|shrub|grass/i.test(`${mesh.name} ${material.name}`)) {
        standard.side = THREE.DoubleSide;
        standard.alphaTest = Math.max(standard.alphaTest || 0, 0.34);
        standard.transparent = false;
      }
      material.needsUpdate = true;
    }
  });
}

function prepareSettlementAsset(root: THREE.Object3D, anisotropy: number) {
  prepareAsset(root, anisotropy);
  root.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (!mesh.isMesh) return;
    const descriptor = `${mesh.name} ${(Array.isArray(mesh.material) ? mesh.material : [mesh.material]).map((material) => material.name).join(" ")}`;
    const sources = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    const materials = sources.map((source) => {
      const material = source.clone() as THREE.MeshStandardMaterial;
      if (material.color) {
        if (/roof|moss|chimney/i.test(descriptor)) material.color.multiply(new THREE.Color(0x66705f));
        else if (/support|beam|plank|wood/i.test(descriptor)) material.color.multiply(new THREE.Color(0x725a43));
        else material.color.multiply(new THREE.Color(0x9a8b72));
      }
      material.roughness = Math.max(material.roughness ?? 0.8, 0.82);
      material.metalness = Math.min(material.metalness ?? 0, 0.04);
      material.envMapIntensity = 0.58;
      if (material.map) {
        material.map.anisotropy = anisotropy;
        material.map.colorSpace = THREE.SRGBColorSpace;
      }
      material.needsUpdate = true;
      return material;
    });
    mesh.material = Array.isArray(mesh.material) ? materials : materials[0];
  });
}

function extractTemplate(source: THREE.Object3D, pattern: RegExp) {
  source.updateMatrixWorld(true);
  const template = new THREE.Group();
  for (const child of source.children) {
    if (pattern.test(child.name)) template.add(child.clone(true));
  }
  if (!template.children.length) return source.clone(true);
  template.updateMatrixWorld(true);
  return template;
}

function varyMaterials(root: THREE.Object3D, seedValue: number, strength = 0.055) {
  const random = seeded(seedValue);
  root.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (!mesh.isMesh) return;
    const sources = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    const materials = sources.map((source) => {
      const material = source.clone() as THREE.MeshStandardMaterial;
      if (material.color) {
        material.color.offsetHSL((random() - 0.5) * strength, (random() - 0.5) * strength, (random() - 0.5) * strength);
      }
      material.roughness = THREE.MathUtils.clamp(material.roughness + (random() - 0.5) * 0.08, 0.45, 1);
      return material;
    });
    mesh.material = Array.isArray(mesh.material) ? materials : materials[0];
  });
  return root;
}

function cloneGrounded(template: THREE.Object3D, targetHeight: number, position: THREE.Vector3, rotation = 0) {
  const source = template.clone(true);
  source.updateMatrixWorld(true);
  const bounds = new THREE.Box3().setFromObject(source);
  const size = bounds.getSize(new THREE.Vector3());
  const center = bounds.getCenter(new THREE.Vector3());
  const scale = targetHeight / Math.max(size.y, 0.001);
  source.scale.setScalar(scale);
  source.position.set(-center.x * scale, -bounds.min.y * scale, -center.z * scale);
  const wrapper = new THREE.Group();
  wrapper.position.copy(position);
  wrapper.rotation.y = rotation;
  wrapper.add(source);
  return wrapper;
}

function makeSky() {
  const material = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    uniforms: {
      dayMix: { value: 1 },
      stormMix: { value: 0 },
      sunDirection: { value: new THREE.Vector3(0.3, 0.8, -0.3) },
      warmMix: { value: 0 },
    },
    vertexShader: `
      varying vec3 vDirection;
      void main() {
        vDirection = normalize(position);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      varying vec3 vDirection;
      uniform float dayMix;
      uniform float stormMix;
      uniform float warmMix;
      uniform vec3 sunDirection;
      void main() {
        float h = clamp(vDirection.y * 0.5 + 0.5, 0.0, 1.0);
        vec3 nightTop = vec3(0.005, 0.012, 0.032);
        vec3 nightHorizon = vec3(0.035, 0.055, 0.075);
        vec3 dayTop = mix(vec3(0.055, 0.18, 0.31), vec3(0.10, 0.22, 0.29), warmMix);
        vec3 dayHorizon = mix(vec3(0.62, 0.77, 0.76), vec3(0.95, 0.52, 0.28), warmMix);
        vec3 night = mix(nightHorizon, nightTop, smoothstep(0.18, 0.88, h));
        vec3 daylight = mix(dayHorizon, dayTop, smoothstep(0.08, 0.92, h));
        vec3 color = mix(night, daylight, dayMix);
        float sun = pow(max(dot(normalize(vDirection), normalize(sunDirection)), 0.0), 720.0);
        float glow = pow(max(dot(normalize(vDirection), normalize(sunDirection)), 0.0), 18.0);
        color += vec3(1.0, 0.48, 0.17) * glow * (0.08 + warmMix * 0.26) * dayMix;
        color += vec3(1.0, 0.88, 0.62) * sun * 3.0 * dayMix;
        color = mix(color, vec3(0.045, 0.065, 0.075), stormMix * 0.75);
        gl_FragColor = vec4(color, 1.0);
      }
    `,
  });
  return { mesh: new THREE.Mesh(new THREE.SphereGeometry(160, 40, 22), material), material };
}

function makeStars() {
  const random = seeded(8091);
  const positions = new Float32Array(900 * 3);
  for (let i = 0; i < 900; i += 1) {
    const theta = random() * Math.PI * 2;
    const phi = Math.acos(0.05 + random() * 0.95);
    const radius = 112 + random() * 22;
    positions[i * 3] = Math.sin(phi) * Math.cos(theta) * radius;
    positions[i * 3 + 1] = Math.cos(phi) * radius;
    positions[i * 3 + 2] = Math.sin(phi) * Math.sin(theta) * radius;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  const material = new THREE.PointsMaterial({ color: 0xdcecff, size: 0.24, transparent: true, opacity: 0, depthWrite: false });
  return new THREE.Points(geometry, material);
}

function makeSoftParticleTexture(inner: string, middle: string) {
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const context = canvas.getContext("2d")!;
  const gradient = context.createRadialGradient(64, 64, 2, 64, 64, 62);
  gradient.addColorStop(0, inner);
  gradient.addColorStop(0.38, middle);
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  context.fillStyle = gradient;
  context.fillRect(0, 0, 128, 128);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function makeMist() {
  const random = seeded(18117);
  const group = new THREE.Group();
  const texture = makeSoftParticleTexture("rgba(225,237,230,.58)", "rgba(175,197,191,.18)");
  for (let index = 0; index < 18; index += 1) {
    const material = new THREE.SpriteMaterial({
      map: texture,
      color: index % 3 === 0 ? 0xc7d6d1 : 0xaabfba,
      transparent: true,
      opacity: 0.075 + random() * 0.06,
      depthWrite: false,
      fog: true,
    });
    const sprite = new THREE.Sprite(material);
    const worldY = 3 + random() * 32;
    const worldX = riverX(worldY) + (random() - 0.5) * 11;
    const position = scenePosition(worldX, worldY);
    sprite.position.set(position.x, position.y + 0.65 + random() * 1.35, position.z);
    const width = 6 + random() * 8;
    sprite.scale.set(width, 1.8 + random() * 1.9, 1);
    sprite.userData.baseX = sprite.position.x;
    sprite.userData.baseY = sprite.position.y;
    sprite.userData.speed = 0.08 + random() * 0.12;
    sprite.userData.phase = random() * Math.PI * 2;
    group.add(sprite);
  }
  group.renderOrder = 3;
  return group;
}

function makeRiver() {
  const segments = 90;
  const positions: number[] = [];
  const uvs: number[] = [];
  const indices: number[] = [];
  for (let i = 0; i <= segments; i += 1) {
    const worldY = 1.5 + (i / segments) * 35;
    const x = riverX(worldY);
    const nextX = riverX(Math.min(37, worldY + 0.2));
    const tangent = new THREE.Vector2((nextX - x) * WORLD_SCALE, 0.2 * WORLD_SCALE).normalize();
    const normal = new THREE.Vector2(-tangent.y, tangent.x);
    const width = (0.88 + Math.sin(worldY * 0.34) * 0.13) * WORLD_SCALE;
    const centerX = (x - CAMP_X) * WORLD_SCALE;
    const centerZ = (worldY - CAMP_Y) * WORLD_SCALE;
    const surfaceY = -0.72 + Math.sin(worldY * 0.18) * 0.035;
    positions.push(centerX + normal.x * width, surfaceY, centerZ + normal.y * width);
    positions.push(centerX - normal.x * width, surfaceY, centerZ - normal.y * width);
    uvs.push(0, i / segments * 8, 1, i / segments * 8);
    if (i < segments) {
      const a = i * 2;
      indices.push(a, a + 2, a + 1, a + 2, a + 3, a + 1);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  const material = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    uniforms: {
      time: { value: 0 },
      daylight: { value: 1 },
      storm: { value: 0 },
    },
    vertexShader: `
      varying vec2 vUv;
      varying vec3 vWorld;
      uniform float time;
      void main() {
        vUv = uv;
        vec3 p = position;
        p.y += sin(uv.y * 8.0 - time * 1.8 + uv.x * 2.0) * 0.035;
        vec4 world = modelMatrix * vec4(p, 1.0);
        vWorld = world.xyz;
        gl_Position = projectionMatrix * viewMatrix * world;
      }
    `,
    fragmentShader: `
      varying vec2 vUv;
      varying vec3 vWorld;
      uniform float time;
      uniform float daylight;
      uniform float storm;
      float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
      float noise(vec2 p) {
        vec2 i=floor(p); vec2 f=fract(p); f=f*f*(3.0-2.0*f);
        return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);
      }
      void main() {
        float ripple = noise(vec2(vUv.x * 12.0 + time * 0.2, vUv.y * 3.0 - time * 0.72));
        float ribbon = sin(vUv.y * 18.0 - time * 2.3 + ripple * 4.0) * 0.5 + 0.5;
        float edge = smoothstep(0.0, 0.14, vUv.x) * smoothstep(0.0, 0.14, 1.0 - vUv.x);
        float bankFoam = 1.0 - smoothstep(0.0, 0.2, min(vUv.x, 1.0 - vUv.x));
        vec3 viewDirection = normalize(cameraPosition - vWorld);
        float fresnel = pow(1.0 - clamp(dot(viewDirection, vec3(0.0, 1.0, 0.0)), 0.0, 1.0), 3.0);
        vec3 deep = mix(vec3(0.015,0.105,0.13), vec3(0.035,0.19,0.22), daylight);
        vec3 crest = mix(vec3(0.18,0.34,0.38), vec3(0.48,0.72,0.70), daylight);
        vec3 color = mix(deep, crest, ribbon * 0.28 + ripple * 0.24);
        color = mix(color, mix(vec3(0.16,0.27,0.31), vec3(0.43,0.59,0.63), daylight), fresnel * 0.42);
        color += vec3(0.58,0.71,0.68) * bankFoam * (0.18 + ribbon * 0.18) * daylight;
        color = mix(color, vec3(0.09,0.13,0.15), storm * 0.5);
        gl_FragColor = vec4(color, 0.79 + edge * 0.16);
      }
    `,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.renderOrder = 2;
  return { mesh, material };
}

function makeRain() {
  const random = seeded(2604);
  const count = 1050;
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i += 1) {
    positions[i * 3] = (random() - 0.5) * 62;
    positions[i * 3 + 1] = random() * 24;
    positions[i * 3 + 2] = (random() - 0.5) * 54;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  const material = new THREE.PointsMaterial({ color: 0xbfe5ec, size: 0.075, transparent: true, opacity: 0.58, depthWrite: false });
  const rain = new THREE.Points(geometry, material);
  rain.visible = false;
  return rain;
}

function makeSupplyCache() {
  const group = new THREE.Group();
  const wood = new THREE.MeshStandardMaterial({ color: 0x5b3923, roughness: 0.88, metalness: 0.02 });
  const darkWood = new THREE.MeshStandardMaterial({ color: 0x2e2118, roughness: 0.94 });
  const metal = new THREE.MeshStandardMaterial({ color: 0x57605d, roughness: 0.38, metalness: 0.62 });
  const crateGeometry = new RoundedBoxGeometry(0.86, 0.62, 0.78, 4, 0.055);
  for (let i = 0; i < 5; i += 1) {
    const crate = new THREE.Mesh(crateGeometry, wood);
    crate.position.set((i % 3 - 1) * 0.82, 0.31 + Math.floor(i / 3) * 0.62, (i % 2) * 0.52);
    crate.rotation.y = (i % 3 - 1) * 0.08;
    crate.castShadow = true;
    crate.receiveShadow = true;
    group.add(crate);
    for (const offset of [-0.25, 0.25]) {
      const brace = new THREE.Mesh(new RoundedBoxGeometry(0.075, 0.68, 0.82, 2, 0.018), darkWood);
      brace.position.copy(crate.position).add(new THREE.Vector3(offset, 0, 0));
      brace.rotation.copy(crate.rotation);
      brace.castShadow = true;
      group.add(brace);
    }
  }
  for (const x of [-1.25, 1.25]) {
    const barrel = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.36, 0.95, 18), metal);
    barrel.position.set(x, 0.48, -0.15);
    barrel.castShadow = true;
    group.add(barrel);
    for (const y of [0.18, 0.48, 0.78]) {
      const hoop = new THREE.Mesh(new THREE.TorusGeometry(0.355, 0.025, 6, 20), darkWood);
      hoop.rotation.x = Math.PI / 2;
      hoop.position.set(x, y, -0.15);
      group.add(hoop);
    }
  }
  return group;
}

function makeFarm(plantTemplate: THREE.Object3D) {
  const group = new THREE.Group();
  const soil = new THREE.MeshStandardMaterial({ color: 0x2c1d13, roughness: 1, vertexColors: false });
  const random = seeded(8277);
  for (let row = -2; row <= 2; row += 1) {
    const points: THREE.Vector3[] = [];
    for (let point = 0; point <= 12; point += 1) {
      const x = -2.4 + (point / 12) * 4.8;
      points.push(new THREE.Vector3(x, 0.07 + Math.sin(point * 0.9 + row) * 0.015, row * 0.72 + Math.sin(point * 0.55 + row) * 0.035));
    }
    const bed = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), 36, 0.17, 9, false), soil);
    bed.receiveShadow = true;
    group.add(bed);
    for (let plant = -5; plant <= 5; plant += 1) {
      const crop = cloneGrounded(
        plantTemplate,
        0.34 + random() * 0.16,
        new THREE.Vector3(plant * 0.4 + (random() - 0.5) * 0.08, 0.1, row * 0.72 + (random() - 0.5) * 0.06),
        random() * Math.PI * 2,
      );
      crop.scale.x *= 0.76;
      crop.scale.z *= 0.76;
      group.add(crop);
    }
  }
  return group;
}

function makeCabin(template: THREE.Object3D, seedValue: number, kind: "shelter" | "store") {
  const random = seeded(seedValue);
  const group = new THREE.Group();
  const cabin = varyMaterials(cloneGrounded(template, kind === "store" ? 3.45 : 3.05 + random() * 0.28, new THREE.Vector3()), seedValue, 0.018);
  group.add(cabin);
  if (kind === "store") {
    const supplies = makeSupplyCache();
    supplies.position.set(2.1, 0, 0.35);
    supplies.rotation.y = -0.42;
    group.add(supplies);
  }
  return group;
}

function makeFacilitySign(label: string, accent: string) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 128;
  const context = canvas.getContext("2d")!;
  context.fillStyle = "rgba(24,28,25,.92)";
  context.fillRect(0, 0, 512, 128);
  context.strokeStyle = accent;
  context.lineWidth = 7;
  context.strokeRect(8, 8, 496, 112);
  context.fillStyle = "#edf0e9";
  context.font = "700 42px system-ui";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(label.toUpperCase(), 256, 66);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 8;
  const group = new THREE.Group();
  const backing = new THREE.Mesh(
    new RoundedBoxGeometry(1.7, 0.5, 0.09, 4, 0.035),
    new THREE.MeshStandardMaterial({ color: 0x2c2922, roughness: 0.92 }),
  );
  backing.castShadow = true;
  group.add(backing);
  const face = new THREE.Mesh(
    new THREE.PlaneGeometry(1.55, 0.385),
    new THREE.MeshStandardMaterial({ map: texture, roughness: 0.82, metalness: 0.01 }),
  );
  face.position.z = 0.051;
  group.add(face);
  return group;
}

function makeFacility(template: THREE.Object3D, seedValue: number, kind: "water" | "clinic" | "workshop") {
  const group = makeCabin(template, seedValue, kind === "clinic" ? "shelter" : "store");
  const wood = new THREE.MeshStandardMaterial({ color: 0x563a27, roughness: 0.92 });
  const metal = new THREE.MeshStandardMaterial({ color: 0x5f6967, roughness: 0.38, metalness: 0.58 });
  const canvasMaterial = new THREE.MeshStandardMaterial({ color: kind === "clinic" ? 0xb9b3a2 : 0x66786b, roughness: 0.9, side: THREE.DoubleSide });
  const sign = makeFacilitySign(kind === "water" ? "Water house" : kind === "clinic" ? "Field clinic" : "Makers' lodge", kind === "clinic" ? "#b86757" : kind === "water" ? "#5faaa8" : "#c39452");
  sign.position.set(0, 2.18, 1.35);
  sign.rotation.y = Math.PI;
  group.add(sign);
  if (kind === "water") {
    for (let i = 0; i < 4; i += 1) {
      const tank = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.48, 1.28, 22), metal);
      tank.position.set(-2.15 + (i % 2) * 0.98, 0.65, -0.7 + Math.floor(i / 2) * 1.04);
      tank.castShadow = true;
      group.add(tank);
      for (const y of [0.18, 0.65, 1.1]) {
        const hoop = new THREE.Mesh(new THREE.TorusGeometry(0.465, 0.027, 7, 24), wood);
        hoop.rotation.x = Math.PI / 2;
        hoop.position.set(tank.position.x, y, tank.position.z);
        group.add(hoop);
      }
    }
    const catchment = new THREE.Mesh(new THREE.PlaneGeometry(3.8, 2.5, 10, 6), canvasMaterial);
    catchment.rotation.set(-0.34, -0.1, 0.02);
    catchment.position.set(-1.25, 2.15, 0.05);
    catchment.castShadow = true;
    group.add(catchment);
  } else if (kind === "clinic") {
    const awning = new THREE.Mesh(new THREE.PlaneGeometry(3.6, 1.8, 8, 4), canvasMaterial);
    awning.rotation.set(-0.42, 0, 0);
    awning.position.set(0, 1.85, 1.85);
    awning.castShadow = true;
    group.add(awning);
    for (const x of [-1.55, 1.55]) {
      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.055, 1.7, 10), metal);
      pole.position.set(x, 0.86, 2.18);
      pole.castShadow = true;
      group.add(pole);
    }
    const cache = makeSupplyCache();
    cache.scale.setScalar(0.64);
    cache.position.set(2.1, 0, 1.1);
    group.add(cache);
  } else {
    for (const z of [-1.6, 1.55]) {
      const bench = new THREE.Mesh(new RoundedBoxGeometry(2.5, 0.18, 0.72, 4, 0.045), wood);
      bench.position.set(1.9, 0.82, z);
      bench.castShadow = true;
      group.add(bench);
      for (const x of [0.85, 2.95]) {
        const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.09, 0.78, 10), metal);
        leg.position.set(x, 0.4, z);
        group.add(leg);
      }
    }
    const rack = new THREE.Group();
    for (let i = 0; i < 6; i += 1) {
      const tool = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.035, 0.72, 8), i % 2 ? metal : wood);
      tool.position.set((i - 2.5) * 0.22, 1.25 + (i % 2) * 0.16, 0);
      tool.rotation.z = (i - 2.5) * 0.06;
      rack.add(tool);
    }
    rack.position.set(1.85, 0, -2.05);
    group.add(rack);
  }
  return group;
}

function makeConstructionSite(template: THREE.Object3D, seedValue: number) {
  const group = new THREE.Group();
  const preview = varyMaterials(cloneGrounded(template, 3.45, new THREE.Vector3()), seedValue, 0.025);
  const revealMaterials: THREE.Material[] = [];
  preview.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (!mesh.isMesh) return;
    const sources = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    const materials = sources.map((source) => {
      const material = source.clone();
      material.transparent = true;
      material.opacity = 0.08;
      material.depthWrite = false;
      revealMaterials.push(material);
      return material;
    });
    mesh.material = Array.isArray(mesh.material) ? materials : materials[0];
    mesh.castShadow = false;
  });
  group.add(preview);
  const scaffold = new THREE.Group();
  const timber = new THREE.MeshStandardMaterial({ color: 0x795331, roughness: 0.94 });
  const beam = new THREE.CylinderGeometry(0.055, 0.075, 3.8, 10);
  for (const x of [-1.7, 1.7]) {
    for (const z of [-1.35, 1.35]) {
      const post = new THREE.Mesh(beam, timber);
      post.position.set(x, 1.9, z);
      post.castShadow = true;
      scaffold.add(post);
    }
  }
  for (const y of [0.8, 2.1, 3.35]) {
    for (const z of [-1.35, 1.35]) {
      const rail = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.06, 3.45, 9), timber);
      rail.rotation.z = Math.PI / 2;
      rail.position.set(0, y, z);
      rail.castShadow = true;
      scaffold.add(rail);
    }
  }
  group.add(scaffold);
  group.userData.preview = preview;
  group.userData.scaffold = scaffold;
  group.userData.revealMaterials = revealMaterials;
  return group;
}

function makeFlameTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 256;
  const context = canvas.getContext("2d")!;
  const glow = context.createRadialGradient(64, 182, 8, 64, 154, 82);
  glow.addColorStop(0, "rgba(255,252,199,1)");
  glow.addColorStop(0.17, "rgba(255,196,69,.98)");
  glow.addColorStop(0.45, "rgba(255,92,22,.82)");
  glow.addColorStop(0.74, "rgba(180,28,8,.26)");
  glow.addColorStop(1, "rgba(80,8,0,0)");
  context.fillStyle = glow;
  context.beginPath();
  context.moveTo(64, 20);
  context.bezierCurveTo(108, 92, 116, 176, 64, 238);
  context.bezierCurveTo(12, 176, 22, 90, 64, 20);
  context.fill();
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function makeCampfire(rockTemplate: THREE.Object3D) {
  const group = new THREE.Group();
  const wood = new THREE.MeshStandardMaterial({ color: 0x3b1f12, roughness: 0.94 });
  const rockVariants = rockTemplate.children.length ? rockTemplate.children : [rockTemplate];
  for (let i = 0; i < 10; i += 1) {
    const angle = (i / 10) * Math.PI * 2;
    const stone = cloneGrounded(
      rockVariants[i % rockVariants.length],
      0.27 + (i % 3) * 0.025,
      new THREE.Vector3(Math.cos(angle) * 0.78, 0, Math.sin(angle) * 0.78),
      angle * 1.7,
    );
    stone.scale.set(1.05, 0.68, 0.88);
    group.add(stone);
  }
  for (let i = 0; i < 4; i += 1) {
    const log = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.16, 1.35, 10), wood);
    log.rotation.z = Math.PI / 2;
    log.rotation.y = (i / 4) * Math.PI;
    log.position.y = 0.28 + (i % 2) * 0.09;
    log.castShadow = true;
    group.add(log);
  }
  const flames = new THREE.Group();
  const flameTexture = makeFlameTexture();
  for (let i = 0; i < 7; i += 1) {
    const material = new THREE.SpriteMaterial({
      map: flameTexture,
      color: i % 3 === 0 ? 0xffe59a : i % 3 === 1 ? 0xff9a38 : 0xff5925,
      transparent: true,
      opacity: 0.74,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const flame = new THREE.Sprite(material);
    const size = 0.6 + (i % 4) * 0.12;
    flame.position.set(Math.cos(i * 2.13) * 0.22, 0.56 + (i % 3) * 0.14, Math.sin(i * 2.13) * 0.22);
    flame.scale.set(size, size * 1.65, 1);
    flame.userData.baseY = flame.position.y;
    flames.add(flame);
  }
  group.add(flames);
  const smoke = new THREE.Group();
  const smokeTexture = makeSoftParticleTexture("rgba(126,133,128,.32)", "rgba(82,91,88,.16)");
  for (let i = 0; i < 6; i += 1) {
    const puff = new THREE.Sprite(new THREE.SpriteMaterial({ map: smokeTexture, color: 0x7d8580, transparent: true, opacity: 0.1, depthWrite: false }));
    puff.position.set(Math.sin(i * 2.4) * 0.12, 1.1 + i * 0.42, Math.cos(i * 1.8) * 0.1);
    const size = 0.5 + i * 0.14;
    puff.scale.set(size, size, 1);
    puff.userData.phase = i * 1.7;
    smoke.add(puff);
  }
  group.add(smoke);
  const emberPositions = new Float32Array(42 * 3);
  const emberRandom = seeded(9091);
  for (let i = 0; i < 42; i += 1) {
    emberPositions[i * 3] = (emberRandom() - 0.5) * 0.55;
    emberPositions[i * 3 + 1] = 0.45 + emberRandom() * 1.65;
    emberPositions[i * 3 + 2] = (emberRandom() - 0.5) * 0.55;
  }
  const emberGeometry = new THREE.BufferGeometry();
  emberGeometry.setAttribute("position", new THREE.BufferAttribute(emberPositions, 3));
  const embers = new THREE.Points(emberGeometry, new THREE.PointsMaterial({ color: 0xffa646, size: 0.045, transparent: true, opacity: 0.84, blending: THREE.AdditiveBlending, depthWrite: false }));
  group.add(embers);
  return { group, flames, smoke, embers };
}

function makePathRibbon(points: Array<[number, number]>, width: number) {
  const positions: number[] = [];
  const uvs: number[] = [];
  const indices: number[] = [];
  let distance = 0;
  for (let index = 0; index < points.length; index += 1) {
    const [worldX, worldY] = points[index];
    const previous = points[Math.max(0, index - 1)];
    const next = points[Math.min(points.length - 1, index + 1)];
    const tangent = new THREE.Vector2(next[0] - previous[0], next[1] - previous[1]).normalize();
    const normal = new THREE.Vector2(-tangent.y, tangent.x);
    const center = scenePosition(worldX, worldY);
    if (index > 0) distance += Math.hypot(worldX - points[index - 1][0], worldY - points[index - 1][1]);
    const variation = Math.sin(index * 2.17) * width * 0.09;
    for (const side of [-1, 1]) {
      positions.push(
        center.x + normal.x * (width + variation) * side,
        center.y + 0.035,
        center.z + normal.y * (width + variation) * side,
      );
      uvs.push(side < 0 ? 0 : 1, distance * 0.28);
    }
    if (index < points.length - 1) {
      const start = index * 2;
      indices.push(start, start + 2, start + 1, start + 2, start + 3, start + 1);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  const material = new THREE.MeshStandardMaterial({
    color: 0x5d4a35,
    roughness: 1,
    transparent: true,
    opacity: 0.86,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
  });
  const path = new THREE.Mesh(geometry, material);
  path.receiveShadow = true;
  return path;
}

function makeBridge() {
  const group = new THREE.Group();
  const wood = new THREE.MeshStandardMaterial({ color: 0x4c3020, roughness: 0.86 });
  const wornWood = new THREE.MeshStandardMaterial({ color: 0x715039, roughness: 0.96 });
  const rope = new THREE.MeshStandardMaterial({ color: 0x81705a, roughness: 1 });
  const plankGeometry = new RoundedBoxGeometry(0.34, 0.12, 1.95, 3, 0.035);
  for (let index = -8; index <= 8; index += 1) {
    const plank = new THREE.Mesh(plankGeometry, index % 4 === 0 ? wornWood : wood);
    plank.position.set(index * 0.32, 0.08 + Math.sin(index * 0.7) * 0.025, 0);
    plank.rotation.y = Math.sin(index * 1.23) * 0.018;
    plank.castShadow = true;
    plank.receiveShadow = true;
    group.add(plank);
  }
  const postGeometry = new THREE.CylinderGeometry(0.07, 0.1, 1.18, 12);
  for (const x of [-2.55, -1.28, 0, 1.28, 2.55]) {
    for (const z of [-1.03, 1.03]) {
      const post = new THREE.Mesh(postGeometry, wood);
      post.position.set(x, 0.55, z);
      post.rotation.z = Math.sin(x * 1.7) * 0.025;
      post.castShadow = true;
      group.add(post);
    }
  }
  for (const z of [-1.03, 1.03]) {
    const points: THREE.Vector3[] = [];
    for (let index = 0; index <= 20; index += 1) {
      const x = -2.55 + (index / 20) * 5.1;
      points.push(new THREE.Vector3(x, 1.02 - Math.abs(Math.sin((index / 20) * Math.PI * 4)) * 0.13, z));
    }
    const rail = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), 60, 0.026, 7, false), rope);
    rail.castShadow = true;
    group.add(rail);
  }
  group.position.copy(scenePosition(riverX(CAMP_Y), CAMP_Y));
  group.position.y = -0.28;
  return group;
}

function makeCampDetails() {
  const group = new THREE.Group();
  const wood = new THREE.MeshStandardMaterial({ color: 0x41291a, roughness: 0.96 });
  const cutWood = new THREE.MeshStandardMaterial({ color: 0x8c6848, roughness: 0.93 });
  for (let stack = 0; stack < 3; stack += 1) {
    for (let logIndex = 0; logIndex < 5; logIndex += 1) {
      const log = new THREE.Mesh(new THREE.CylinderGeometry(0.105, 0.13, 1.12, 12), logIndex % 2 ? wood : cutWood);
      log.rotation.z = Math.PI / 2;
      log.rotation.y = (logIndex % 2) * 0.08;
      log.position.set(2.1 + (logIndex % 2) * 0.16, 0.13 + Math.floor(logIndex / 2) * 0.2, -1.7 + stack * 0.42);
      log.castShadow = true;
      group.add(log);
    }
  }
  for (const angle of [-0.85, 0.75, 2.4]) {
    const bench = new THREE.Group();
    const seat = new THREE.Mesh(new RoundedBoxGeometry(1.55, 0.16, 0.38, 3, 0.045), cutWood);
    seat.position.y = 0.48;
    seat.castShadow = true;
    bench.add(seat);
    for (const x of [-0.57, 0.57]) {
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.09, 0.48, 10), wood);
      leg.position.set(x, 0.24, 0);
      leg.castShadow = true;
      bench.add(leg);
    }
    bench.position.set(Math.cos(angle) * 2.15, 0, Math.sin(angle) * 2.15);
    bench.rotation.y = -angle + Math.PI / 2;
    group.add(bench);
  }
  group.position.copy(scenePosition(CAMP_X, CAMP_Y));
  return group;
}

interface LandscapePlacement {
  x: number;
  y: number;
  height: number;
  rotation: number;
  widthScale?: number;
  tilt?: number;
  tint?: THREE.Color;
}

function idSeed(id: string) {
  return id.split("").reduce((value, character) => Math.imul(value ^ character.charCodeAt(0), 16777619), 2166136261) >>> 0;
}

function addInstancedAsset(
  scene: THREE.Scene,
  template: THREE.Object3D,
  placements: LandscapePlacement[],
  castShadow: boolean,
) {
  if (!placements.length) return;
  template.updateMatrixWorld(true);
  const bounds = new THREE.Box3().setFromObject(template);
  const size = bounds.getSize(new THREE.Vector3());
  const center = bounds.getCenter(new THREE.Vector3());
  const normalize = new THREE.Matrix4().makeTranslation(-center.x, -bounds.min.y, -center.z);
  template.traverse((object) => {
    const source = object as THREE.Mesh;
    if (!source.isMesh || !source.geometry) return;
    const geometry = source.geometry.clone();
    geometry.applyMatrix4(source.matrixWorld);
    geometry.applyMatrix4(normalize);
    const mesh = new THREE.InstancedMesh(geometry, source.material, placements.length);
    const matrix = new THREE.Matrix4();
    const quaternion = new THREE.Quaternion();
    const position = new THREE.Vector3();
    const scale = new THREE.Vector3();
    for (let index = 0; index < placements.length; index += 1) {
      const placement = placements[index];
      scenePosition(placement.x, placement.y, position);
      quaternion.setFromEuler(new THREE.Euler(placement.tilt ?? 0, placement.rotation, (placement.tilt ?? 0) * 0.55));
      const normalizedScale = placement.height / Math.max(size.y, 0.001);
      scale.set(normalizedScale * (placement.widthScale ?? 1), normalizedScale, normalizedScale * (placement.widthScale ?? 1));
      matrix.compose(position, quaternion, scale);
      mesh.setMatrixAt(index, matrix);
      if (placement.tint) mesh.setColorAt(index, placement.tint);
    }
    mesh.instanceMatrix.setUsage(THREE.StaticDrawUsage);
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    mesh.castShadow = castShadow;
    mesh.receiveShadow = true;
    mesh.computeBoundingSphere();
    scene.add(mesh);
  });
}

function populateLandscape(runtime: SceneRuntime, world: RenderWorld, mobile: boolean) {
  const makePlacement = (node: RenderResource, minHeight: number, maxHeight: number): LandscapePlacement => {
    const random = seeded(idSeed(node.id));
    return {
      x: node.x,
      y: node.y,
      height: minHeight + random() * (maxHeight - minHeight),
      rotation: random() * Math.PI * 2,
      widthScale: 0.84 + random() * 0.34,
      tilt: (random() - 0.5) * 0.055,
      tint: new THREE.Color(0xffffff).offsetHSL((random() - 0.5) * 0.025, (random() - 0.5) * 0.04, (random() - 0.5) * 0.05),
    };
  };
  const resources = world.resources.filter((node) => node.amount > 0);
  const campClearance = mobile ? 10.5 : 8.2;
  const treeNodes = resources.filter((node) => node.kind === "tree" && Math.hypot(node.x - CAMP_X, node.y - CAMP_Y) > campClearance);
  const forestTrees = treeNodes.filter((_, index) => index % (mobile ? 3 : 1) === 0 && index % 6 !== 0).map((node) => makePlacement(node, 5.8, 9.5));
  const weatheredTrees = treeNodes.filter((_, index) => index % (mobile ? 9 : 6) === 0).map((node) => makePlacement(node, 4.6, 7.8));
  const rocks = resources.filter((node) => node.kind === "rock").filter((_, index) => index % (mobile ? 2 : 1) === 0).map((node) => makePlacement(node, 0.8, 1.75));
  const shrubs = resources.filter((node) => node.kind === "berries").filter((_, index) => index % (mobile ? 2 : 1) === 0).map((node) => makePlacement(node, 0.72, 1.25));
  const ferns = resources.filter((node) => node.kind === "herbs").map((node) => makePlacement(node, 0.42, 0.78));
  const random = seeded(91737);
  const fillerCount = mobile ? 44 : 150;
  for (let index = 0; index < fillerCount; index += 1) {
    const x = 2.5 + random() * 43;
    const y = 2.5 + random() * 33;
    if (Math.abs(x - riverX(y)) < 2 || Math.hypot(x - CAMP_X, y - CAMP_Y) < (mobile ? 8.5 : 6.8)) {
      index -= 1;
      continue;
    }
    ferns.push({
      x,
      y,
      height: 0.32 + random() * 0.52,
      rotation: random() * Math.PI * 2,
      widthScale: 0.78 + random() * 0.5,
      tint: new THREE.Color(0xffffff).offsetHSL((random() - 0.5) * 0.02, 0, (random() - 0.5) * 0.04),
    });
  }
  addInstancedAsset(runtime.scene, runtime.templates.tree, forestTrees, !mobile);
  addInstancedAsset(runtime.scene, runtime.templates.deadTree, weatheredTrees, !mobile);
  addInstancedAsset(runtime.scene, runtime.templates.rock, rocks, false);
  addInstancedAsset(runtime.scene, runtime.templates.shrub, shrubs, false);
  addInstancedAsset(runtime.scene, runtime.templates.fern, ferns, false);
}

function normalizeRigNames(root: THREE.Object3D) {
  const known = new Set([
    "Hips", "Spine", "Spine1", "Spine2", "Neck", "Head", "HeadTop_End",
    "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase", "LeftToe_End",
    "RightShoulder", "RightArm", "RightForeArm", "RightHand", "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase", "RightToe_End",
  ]);
  root.traverse((object) => {
    if ((object as THREE.Bone).isBone && known.has(object.name)) object.name = `mixamorig${object.name}`;
  });
}

function cloneCharacterModel(template: THREE.Object3D, agent: RenderAgent, variant: number) {
  const model = cloneSkeleton(template);
  normalizeRigNames(model);
  model.updateMatrixWorld(true);
  const bounds = new THREE.Box3().setFromObject(model);
  const size = bounds.getSize(new THREE.Vector3());
  const center = bounds.getCenter(new THREE.Vector3());
  const scale = (1.66 + (agent.seed % 12) * 0.015) / Math.max(size.y, 0.001);
  model.scale.setScalar(scale);
  model.position.set(-center.x * scale, -bounds.min.y * scale, -center.z * scale);
  model.rotation.y = Math.PI;
  const tint = new THREE.Color(agent.color);
  model.traverse((object) => {
    const mesh = object as THREE.SkinnedMesh;
    if (!mesh.isMesh) return;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    const sourceMaterials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    const materials = sourceMaterials.map((source) => {
      const material = source.clone() as THREE.MeshStandardMaterial;
      if (/body|outfit|shirt|bottom|vanguard|ch03/i.test(`${mesh.name} ${source.name}`) && material.color) {
        material.color.lerp(tint, variant === 0 ? 0.3 : 0.42);
      }
      return material;
    });
    mesh.material = Array.isArray(mesh.material) ? materials : materials[0];
    if (/beard/i.test(mesh.name)) mesh.visible = agent.seed % 4 !== 0;
    if (/headwear|visor/i.test(mesh.name)) mesh.visible = agent.seed % 3 === 0;
    mesh.userData.agentId = agent.id;
  });
  return model;
}

function findBone(model: THREE.Object3D, suffix: string) {
  let result: THREE.Bone | undefined;
  model.traverse((object) => {
    if (result || !(object as THREE.Bone).isBone) return;
    const compact = object.name.replace(/[:_]/g, "").toLowerCase();
    if (compact.endsWith(suffix.toLowerCase())) result = object as THREE.Bone;
  });
  return result;
}

function makeLabel(agent: RenderAgent) {
  const element = document.createElement("div");
  element.className = "world-nameplate";
  const name = document.createElement("span");
  name.className = "world-nameplate-name";
  name.textContent = agent.name;
  const intent = document.createElement("span");
  intent.className = "world-nameplate-intent";
  intent.textContent = ACTION_NAMES[agent.action];
  element.append(name, intent);
  const label = new CSS2DObject(element);
  label.position.set(0, 2.15, 0);
  return { label, element, name, intent };
}

function switchClip(character: CharacterRuntime, next: "idle" | "walk" | "run") {
  if (character.activeClip === next) return;
  const previous = character.clips[character.activeClip];
  const upcoming = character.clips[next] ?? character.clips.idle;
  previous?.fadeOut(0.28);
  upcoming?.reset().fadeIn(0.28).play();
  character.activeClip = next;
}

function makeTaskKit(agent: RenderAgent) {
  const kit: Record<string, THREE.Group> = {};
  const wood = new THREE.MeshStandardMaterial({ color: 0x6f4a2c, roughness: 0.94 });
  const cutWood = new THREE.MeshStandardMaterial({ color: 0xb4875f, roughness: 0.9 });
  const metal = new THREE.MeshStandardMaterial({ color: 0x68716f, roughness: 0.32, metalness: 0.68 });
  const darkMetal = new THREE.MeshStandardMaterial({ color: 0x343b3a, roughness: 0.38, metalness: 0.62 });
  const cloth = new THREE.MeshStandardMaterial({ color: new THREE.Color(agent.color).multiplyScalar(0.62), roughness: 0.96 });
  const makeGroup = (name: string) => {
    const group = new THREE.Group();
    group.name = `task-${name}`;
    group.visible = false;
    kit[name] = group;
    return group;
  };
  const axe = makeGroup("axe");
  const axeHandle = new THREE.Mesh(new THREE.CylinderGeometry(0.027, 0.035, 0.98, 10), wood);
  axeHandle.position.y = 0.48;
  axe.add(axeHandle);
  const axeHead = new THREE.Mesh(new THREE.ConeGeometry(0.2, 0.34, 4), darkMetal);
  axeHead.rotation.z = Math.PI / 2;
  axeHead.position.set(0.12, 0.94, 0);
  axe.add(axeHead);

  const hammer = makeGroup("hammer");
  const hammerHandle = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.032, 0.72, 9), wood);
  hammerHandle.position.y = 0.35;
  hammer.add(hammerHandle);
  const hammerHead = new THREE.Mesh(new RoundedBoxGeometry(0.38, 0.15, 0.15, 3, 0.025), darkMetal);
  hammerHead.position.y = 0.72;
  hammer.add(hammerHead);

  const bucket = makeGroup("bucket");
  const bucketBody = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.17, 0.42, 18, 1, true), metal);
  bucketBody.position.y = 0.23;
  bucket.add(bucketBody);
  const bucketBase = new THREE.Mesh(new THREE.CircleGeometry(0.17, 18), metal);
  bucketBase.rotation.x = -Math.PI / 2;
  bucketBase.position.y = 0.02;
  bucket.add(bucketBase);
  const bucketHandle = new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.018, 6, 22, Math.PI), darkMetal);
  bucketHandle.rotation.z = Math.PI;
  bucketHandle.position.y = 0.43;
  bucket.add(bucketHandle);

  const basket = makeGroup("basket");
  const basketBody = new THREE.Mesh(new THREE.CylinderGeometry(0.27, 0.2, 0.34, 18, 1, true), cutWood);
  basketBody.position.y = 0.2;
  basket.add(basketBody);
  const basketHandle = new THREE.Mesh(new THREE.TorusGeometry(0.26, 0.025, 6, 24, Math.PI), wood);
  basketHandle.rotation.z = Math.PI;
  basketHandle.position.y = 0.42;
  basket.add(basketHandle);
  for (let i = 0; i < 7; i += 1) {
    const food = new THREE.Mesh(new THREE.IcosahedronGeometry(0.055 + (i % 2) * 0.012, 1), new THREE.MeshStandardMaterial({ color: i % 3 === 0 ? 0x8f3233 : 0x596f35, roughness: 0.82 }));
    food.position.set(((i % 3) - 1) * 0.1, 0.36 + Math.floor(i / 3) * 0.045, ((i * 7) % 3 - 1) * 0.07);
    basket.add(food);
  }

  const medkit = makeGroup("medkit");
  const caseMesh = new THREE.Mesh(new RoundedBoxGeometry(0.42, 0.32, 0.18, 4, 0.045), cloth);
  caseMesh.position.y = 0.2;
  medkit.add(caseMesh);
  const crossMaterial = new THREE.MeshStandardMaterial({ color: 0xd9d8ca, roughness: 0.8 });
  const crossA = new THREE.Mesh(new RoundedBoxGeometry(0.2, 0.065, 0.012, 2, 0.01), crossMaterial);
  crossA.position.set(0, 0.2, 0.098);
  medkit.add(crossA);
  const crossB = crossA.clone();
  crossB.rotation.z = Math.PI / 2;
  medkit.add(crossB);

  const logs = makeGroup("logs");
  for (let i = 0; i < 4; i += 1) {
    const log = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.075, 0.9, 10), i % 2 ? wood : cutWood);
    log.rotation.z = Math.PI / 2;
    log.position.set(0, 0.17 + Math.floor(i / 2) * 0.13, (i % 2 - 0.5) * 0.15);
    logs.add(log);
  }

  const stone = makeGroup("stone");
  const sack = new THREE.Mesh(new RoundedBoxGeometry(0.46, 0.36, 0.3, 5, 0.1), cloth);
  sack.position.y = 0.21;
  stone.add(sack);
  for (let i = 0; i < 4; i += 1) {
    const rock = new THREE.Mesh(new THREE.DodecahedronGeometry(0.09 + (i % 2) * 0.02, 1), darkMetal);
    rock.position.set((i - 1.5) * 0.1, 0.43 + (i % 2) * 0.03, 0);
    stone.add(rock);
  }

  const hoe = makeGroup("hoe");
  const hoeHandle = new THREE.Mesh(new THREE.CylinderGeometry(0.024, 0.035, 1.25, 9), wood);
  hoeHandle.position.y = 0.62;
  hoe.add(hoeHandle);
  const hoeHead = new THREE.Mesh(new RoundedBoxGeometry(0.48, 0.07, 0.16, 3, 0.02), metal);
  hoeHead.position.set(0.16, 0.05, 0);
  hoeHead.rotation.z = -0.18;
  hoe.add(hoeHead);

  const ration = makeGroup("ration");
  const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.075, 0.2, 16), metal);
  cup.position.y = 0.11;
  ration.add(cup);

  for (const group of Object.values(kit)) {
    group.position.set(0.38, 0.48, -0.18);
    group.rotation.set(0.08, 0, -0.18);
    group.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (mesh.isMesh) mesh.castShadow = true;
    });
  }
  return kit;
}

function taskProp(agent: RenderAgent) {
  if (agent.taskPhase === "returning") {
    if (agent.carrying === "timber") return "logs";
    if (agent.carrying === "stone") return "stone";
    if (agent.carrying === "water") return "bucket";
    if (agent.carrying === "food" || agent.carrying === "medicine") return "basket";
  }
  if (agent.action === "gather_wood") return "axe";
  if (agent.action === "gather_stone" || agent.action === "build_shelter") return "hammer";
  if (agent.action === "gather_water" || agent.action === "drink") return "bucket";
  if (agent.action === "gather_food" || agent.action === "gather_medicine") return "basket";
  if (agent.action === "farm") return "hoe";
  if (agent.action === "heal") return "medkit";
  if (agent.action === "eat" || agent.action === "tend_fire") return "ration";
  return "";
}

const taskRight = new THREE.Vector3();
const taskLeft = new THREE.Vector3();
const taskTarget = new THREE.Vector3();

function syncTaskProp(character: CharacterRuntime, agent: RenderAgent, elapsed: number, dt: number) {
  const active = agent.action === "idle" ? "" : taskProp(agent);
  for (const [key, prop] of Object.entries(character.taskKit)) prop.visible = key === active;
  if (!active) return;
  const prop = character.taskKit[active];
  character.root.updateMatrixWorld(true);
  const rightHand = character.bones.rightHand;
  const leftHand = character.bones.leftHand;
  if (rightHand) {
    rightHand.getWorldPosition(taskRight);
    character.root.worldToLocal(taskRight);
  } else taskRight.set(0.38, 0.78, -0.14);
  if (leftHand) {
    leftHand.getWorldPosition(taskLeft);
    character.root.worldToLocal(taskLeft);
  } else taskLeft.set(-0.38, 0.78, -0.14);
  const twoHanded = active === "medkit" || (agent.taskPhase === "returning" && ["logs", "stone", "basket"].includes(active));
  if (twoHanded) taskTarget.copy(taskRight).lerp(taskLeft, 0.5);
  else taskTarget.copy(taskRight);
  if (!Number.isFinite(taskTarget.x + taskTarget.y + taskTarget.z) || taskTarget.lengthSq() > 4.84) {
    taskTarget.set(twoHanded ? 0 : 0.34, twoHanded ? 0.82 : 0.76, -0.12);
  }
  if (active === "bucket") taskTarget.y -= 0.42;
  else if (active === "basket") taskTarget.y -= twoHanded ? 0.28 : 0.4;
  else if (active === "logs" || active === "stone") {
    taskTarget.y -= 0.24;
    taskTarget.z -= 0.1;
  } else if (active === "medkit") {
    taskTarget.y -= 0.18;
    taskTarget.z -= 0.08;
  } else if (active === "ration") taskTarget.y -= 0.08;
  const blend = 1 - Math.exp(-dt * 18);
  prop.position.lerp(taskTarget, blend);
  const working = agent.taskPhase === "working" && Math.hypot(agent.targetX - agent.x, agent.targetY - agent.y) <= 0.34;
  const cycle = Math.sin(elapsed * (["axe", "hammer", "hoe"].includes(active) ? 3.8 : 2.7) + character.phase) * 0.5 + 0.5;
  const targetX = active === "logs" ? 0 : active === "medkit" ? -0.04 : 0.08;
  const targetY = active === "logs" || active === "stone" ? 0 : active === "bucket" ? 0.05 : -0.12;
  const targetZ = working && ["axe", "hammer", "hoe"].includes(active) ? THREE.MathUtils.lerp(-1.02, 0.34, cycle) : active === "logs" ? 0 : -0.2;
  prop.rotation.x = THREE.MathUtils.damp(prop.rotation.x, targetX, 14, dt);
  prop.rotation.y = THREE.MathUtils.damp(prop.rotation.y, targetY, 14, dt);
  prop.rotation.z = THREE.MathUtils.damp(prop.rotation.z, targetZ, 16, dt);
}

function addCharacter(runtime: SceneRuntime, agent: RenderAgent) {
  const variant = (Number(agent.id.split("-")[1]) - 1) % runtime.templates.people.length;
  const model = cloneCharacterModel(runtime.templates.people[variant], agent, variant);
  const root = new THREE.Group();
  root.userData.agentId = agent.id;
  root.add(model);
  const taskKit = makeTaskKit(agent);
  Object.values(taskKit).forEach((tool) => root.add(tool));
  const start = scenePosition(agent.x, agent.y);
  root.position.copy(start);
  const selection = new THREE.Mesh(
    new THREE.RingGeometry(0.58, 0.72, 48),
    new THREE.MeshBasicMaterial({ color: 0x82ead4, transparent: true, opacity: 0.88, side: THREE.DoubleSide, depthWrite: false }),
  );
  selection.rotation.x = -Math.PI / 2;
  selection.position.y = 0.045;
  selection.visible = false;
  root.add(selection);
  const labelBits = makeLabel(agent);
  root.add(labelBits.label);
  const mixer = new THREE.AnimationMixer(model);
  const animation = (name: string) => runtime.templates.animations.find((clip) => clip.name.toLowerCase() === name);
  const idle = animation("idle");
  const walk = animation("walk");
  const run = animation("run");
  const clips = {
    idle: idle ? mixer.clipAction(idle) : undefined,
    walk: walk ? mixer.clipAction(walk) : undefined,
    run: run ? mixer.clipAction(run) : undefined,
  };
  clips.idle?.play();
  const character: CharacterRuntime = {
    id: agent.id,
    root,
    model,
    mixer,
    clips,
    activeClip: "idle",
    label: labelBits.label,
    labelName: labelBits.name,
    labelIntent: labelBits.intent,
    selection,
    bones: {
      rightArm: findBone(model, "RightArm"),
      rightForeArm: findBone(model, "RightForeArm"),
      rightHand: findBone(model, "RightHand"),
      leftArm: findBone(model, "LeftArm"),
      leftForeArm: findBone(model, "LeftForeArm"),
      leftHand: findBone(model, "LeftHand"),
      head: findBone(model, "Head"),
      spine: findBone(model, "Spine2") ?? findBone(model, "Spine"),
    },
    heading: 0,
    taskWeight: 0,
    phase: (agent.seed % 1000) / 100,
    taskKit,
    separation: new THREE.Vector2(),
  };
  model.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (mesh.isMesh) runtime.hitTargets.push(mesh);
  });
  runtime.scene.add(root);
  runtime.mixers.push(mixer);
  runtime.characters.set(agent.id, character);
}

function taskGesture(character: CharacterRuntime, agent: RenderAgent, elapsed: number, dt: number) {
  const moving = Math.hypot(agent.targetX - agent.x, agent.targetY - agent.y) > 0.34;
  const working = !moving && agent.action !== "idle" && agent.action !== "guard";
  character.taskWeight = THREE.MathUtils.damp(character.taskWeight, working ? 1 : 0, 5.5, dt);
  const phase = elapsed * (["gather_wood", "gather_stone", "build_shelter"].includes(agent.action) ? 3.8 : 2.7) + character.phase;
  const cycle = Math.sin(phase) * 0.5 + 0.5;
  const activeProp = taskProp(agent);
  if (character.taskWeight < 0.01 && agent.taskPhase !== "returning") return;
  const weight = character.taskWeight;
  const breath = Math.sin(phase * 0.52) * 0.035;
  if (agent.taskPhase === "returning") {
    if (character.bones.rightArm) character.bones.rightArm.rotation.x -= 0.32;
    if (character.bones.leftArm) character.bones.leftArm.rotation.x -= activeProp === "bucket" ? 0.08 : 0.32;
    if (character.bones.rightForeArm && activeProp !== "bucket") character.bones.rightForeArm.rotation.x -= 0.48;
    if (character.bones.leftForeArm && activeProp !== "bucket") character.bones.leftForeArm.rotation.x -= 0.48;
    return;
  }
  if (["gather_wood", "gather_stone", "build_shelter"].includes(agent.action)) {
    if (character.bones.rightArm) {
      character.bones.rightArm.rotation.x += THREE.MathUtils.lerp(-1.28, -0.28, cycle) * weight;
      character.bones.rightArm.rotation.z += (0.18 + cycle * 0.13) * weight;
    }
    if (character.bones.rightForeArm) character.bones.rightForeArm.rotation.x += THREE.MathUtils.lerp(-0.72, -1.08, cycle) * weight;
    if (character.bones.leftArm) {
      character.bones.leftArm.rotation.x += THREE.MathUtils.lerp(-0.78, -0.22, cycle) * weight;
      character.bones.leftArm.rotation.z -= 0.16 * weight;
    }
    if (character.bones.leftForeArm) character.bones.leftForeArm.rotation.x += (-0.62 + cycle * 0.16) * weight;
    if (character.bones.spine) character.bones.spine.rotation.x += (0.07 + (1 - cycle) * 0.13) * weight;
  } else if (["gather_food", "gather_medicine", "farm", "tend_fire"].includes(agent.action)) {
    if (character.bones.spine) character.bones.spine.rotation.x += (0.16 + cycle * 0.12) * weight;
    if (character.bones.rightArm) character.bones.rightArm.rotation.x += (-0.38 - cycle * 0.4) * weight;
    if (character.bones.rightForeArm) character.bones.rightForeArm.rotation.x += (-0.5 + cycle * 0.24) * weight;
    if (character.bones.leftArm) character.bones.leftArm.rotation.x += (-0.22 - (1 - cycle) * 0.36) * weight;
    if (character.bones.head) character.bones.head.rotation.x += (0.08 + cycle * 0.04) * weight;
  } else if (["assist", "socialize", "heal"].includes(agent.action)) {
    if (character.bones.leftArm) {
      character.bones.leftArm.rotation.x -= (0.18 + cycle * 0.17) * weight;
      character.bones.leftArm.rotation.z += (0.12 + cycle * 0.1) * weight;
    }
    if (character.bones.rightArm) {
      character.bones.rightArm.rotation.x -= (0.16 + (1 - cycle) * 0.15) * weight;
      character.bones.rightArm.rotation.z -= (0.1 + cycle * 0.08) * weight;
    }
    if (character.bones.head) character.bones.head.rotation.y += Math.sin(phase * 0.62) * 0.075 * weight;
  } else if (["drink", "eat"].includes(agent.action)) {
    if (character.bones.rightArm) character.bones.rightArm.rotation.x += (-0.88 + cycle * 0.12) * weight;
    if (character.bones.rightForeArm) character.bones.rightForeArm.rotation.x += (-1.12 + cycle * 0.08) * weight;
    if (character.bones.head) character.bones.head.rotation.x -= 0.04 * weight;
  } else if (agent.action === "rest") {
    if (character.bones.spine) character.bones.spine.rotation.x += (0.15 + breath) * weight;
    if (character.bones.head) character.bones.head.rotation.x += (0.07 - breath) * weight;
  } else {
    if (character.bones.head) character.bones.head.rotation.y += Math.sin(phase * 0.55) * 0.055 * weight;
  }
}

function makeTerrain(textures: THREE.Texture[], anisotropy: number) {
  const [diffuse, normal, arm, height] = textures;
  diffuse.name = "ground_diff";
  normal.name = "ground_normal";
  arm.name = "ground_arm";
  height.name = "ground_height";
  configureTexture(diffuse, 12, 9, anisotropy);
  configureTexture(normal, 12, 9, anisotropy);
  configureTexture(arm, 12, 9, anisotropy);
  configureTexture(height, 12, 9, anisotropy);
  const width = 48 * WORLD_SCALE;
  const depth = 38 * WORLD_SCALE;
  const geometry = new THREE.PlaneGeometry(width, depth, 168, 132);
  geometry.rotateX(-Math.PI / 2);
  const position = geometry.getAttribute("position") as THREE.BufferAttribute;
  const colors = new Float32Array(position.count * 3);
  const grass = new THREE.Color(0x6d7458);
  const earth = new THREE.Color(0x81725d);
  const stone = new THREE.Color(0x7d7d72);
  for (let i = 0; i < position.count; i += 1) {
    const worldX = position.getX(i) / WORLD_SCALE + CAMP_X;
    const worldY = position.getZ(i) / WORLD_SCALE + CAMP_Y;
    const h = terrainHeight(worldX, worldY);
    position.setY(i, h);
    const wet = 1 - smoothstep(1.8, 4.2, Math.abs(worldX - riverX(worldY)));
    const ridge = smoothstep(0.75, 2.2, h);
    const color = grass.clone().lerp(earth, 0.38 + wet * 0.25).lerp(stone, ridge * 0.6);
    colors[i * 3] = color.r;
    colors[i * 3 + 1] = color.g;
    colors[i * 3 + 2] = color.b;
  }
  position.needsUpdate = true;
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute("uv1", geometry.getAttribute("uv"));
  geometry.computeVertexNormals();
  const material = new THREE.MeshStandardMaterial({
    map: diffuse,
    normalMap: normal,
    normalScale: new THREE.Vector2(0.72, 0.72),
    aoMap: arm,
    aoMapIntensity: 0.65,
    roughnessMap: arm,
    displacementMap: height,
    displacementScale: 0.13,
    displacementBias: -0.035,
    roughness: 0.96,
    metalness: 0,
    vertexColors: true,
  });
  const terrain = new THREE.Mesh(geometry, material);
  terrain.receiveShadow = true;
  return terrain;
}

function syncBuildings(runtime: SceneRuntime, world: RenderWorld) {
  for (const building of world.buildings) {
    let object = runtime.buildings.get(building.id);
    if (!object) {
      const buildingSeed = idSeed(building.id) + runtime.buildings.size * 37;
      if (building.kind === "shelter") object = makeCabin(runtime.templates.house, buildingSeed, "shelter");
      else if (building.kind === "farm") object = makeFarm(runtime.templates.fern);
      else if (building.kind === "store") {
        object = makeSupplyCache();
        object.scale.setScalar(0.86);
      }
      else if (building.kind === "water" || building.kind === "clinic" || building.kind === "workshop") object = makeFacility(runtime.templates.house, buildingSeed, building.kind);
      else {
        const fire = makeCampfire(runtime.templates.rock);
        object = fire.group;
        runtime.fireFlames = fire.flames;
        runtime.fireSmoke = fire.smoke;
        runtime.fireEmbers = fire.embers;
      }
      object.position.copy(scenePosition(building.x, building.y));
      object.rotation.y = (building.id.length * 0.71 + runtime.buildings.size * 1.7) % (Math.PI * 2);
      runtime.scene.add(object);
      runtime.buildings.set(building.id, object);
    }
    if (building.kind === "farm") object.scale.setScalar(1 + Math.max(0, building.level - 1) * 0.09);
  }
  const activeProjects = new Set(world.projects.map((project) => project.id));
  for (const [id, object] of runtime.projects) {
    if (activeProjects.has(id)) continue;
    runtime.scene.remove(object);
    runtime.projects.delete(id);
  }
  for (const project of world.projects) {
    let site = runtime.projects.get(project.id);
    if (!site) {
      site = makeConstructionSite(runtime.templates.house, idSeed(project.id));
      site.position.copy(scenePosition(project.x, project.y));
      site.rotation.y = (idSeed(project.id) % 628) / 100;
      runtime.scene.add(site);
      runtime.projects.set(project.id, site);
    }
    const progress = THREE.MathUtils.clamp(project.progress / 100, 0.02, 1);
    const materials = site.userData.revealMaterials as THREE.Material[] | undefined;
    materials?.forEach((material) => { material.opacity = 0.07 + progress * 0.58; });
    const scaffold = site.userData.scaffold as THREE.Group | undefined;
    if (scaffold) {
      scaffold.visible = progress < 0.98;
      scaffold.scale.y = 0.28 + progress * 0.72;
      scaffold.children.forEach((child) => { child.visible = child.position.y <= 0.6 + progress * 3.5; });
    }
  }
}

function updateWeather(runtime: SceneRuntime, world: RenderWorld, dt: number, clock: number) {
  const hour = world.minute / 60;
  const solar = Math.sin(((hour - 6) / 24) * Math.PI * 2);
  const day = smoothstep(-0.16, 0.18, solar);
  const twilight = 1 - smoothstep(0.12, 0.72, Math.abs(solar));
  const storm = world.weather === "Storm" ? 1 : world.weather === "Rain" ? 0.46 : 0;
  const heat = world.weather === "Heat" ? 1 : 0;
  const cold = world.weather === "Cold snap" ? 1 : 0;
  const azimuth = ((hour - 6) / 24) * Math.PI * 2;
  const sunDirection = new THREE.Vector3(Math.cos(azimuth), Math.max(-0.16, solar), Math.sin(azimuth) * 0.66).normalize();
  runtime.sun.position.copy(sunDirection).multiplyScalar(58);
  runtime.sun.intensity = (0.12 + day * 2.7) * (1 - storm * 0.68);
  runtime.sun.color.set(0xfff0d4).lerp(new THREE.Color(0xff9b5d), twilight * 0.46);
  runtime.hemi.intensity = 0.16 + day * 1.25 - storm * 0.38;
  runtime.hemi.color.set(0x9dc5dd).lerp(new THREE.Color(0x788a90), storm);
  runtime.hemi.groundColor.set(0x2d251d).lerp(new THREE.Color(0x273137), cold * 0.7);
  runtime.skyMaterial.uniforms.dayMix.value = day;
  runtime.skyMaterial.uniforms.stormMix.value = storm;
  runtime.skyMaterial.uniforms.warmMix.value = Math.max(heat, twilight * 0.72);
  runtime.skyMaterial.uniforms.sunDirection.value.copy(sunDirection);
  runtime.waterMaterial.uniforms.time.value = clock;
  runtime.waterMaterial.uniforms.daylight.value = day;
  runtime.waterMaterial.uniforms.storm.value = storm;
  (runtime.stars.material as THREE.PointsMaterial).opacity = (1 - day) * (1 - storm * 0.65) * 0.92;
  runtime.stars.rotation.y = clock * 0.004;
  runtime.rain.visible = storm > 0;
  if (runtime.rain.visible) {
    const attribute = runtime.rain.geometry.getAttribute("position") as THREE.BufferAttribute;
    for (let i = 0; i < attribute.count; i += 1) {
      let y = attribute.getY(i) - dt * (world.weather === "Storm" ? 25 : 17);
      if (y < -1.5) y = 18 + ((i * 37) % 700) / 45;
      attribute.setY(i, y);
      attribute.setX(i, attribute.getX(i) + dt * (world.weather === "Storm" ? 2.6 : 0.7));
      if (attribute.getX(i) > 34) attribute.setX(i, -34);
    }
    attribute.needsUpdate = true;
  }
  runtime.mist.visible = true;
  runtime.mist.children.forEach((child, index) => {
    const sprite = child as THREE.Sprite;
    const material = sprite.material as THREE.SpriteMaterial;
    const baseX = Number(sprite.userData.baseX ?? 0);
    const baseY = Number(sprite.userData.baseY ?? 0);
    const phase = Number(sprite.userData.phase ?? index);
    const drift = Number(sprite.userData.speed ?? 0.1);
    sprite.position.x = baseX + Math.sin(clock * drift + phase) * 2.2 + ((clock * drift * 0.22 + index) % 2.4);
    sprite.position.y = baseY + Math.sin(clock * 0.09 + phase) * 0.16;
    material.opacity = (0.045 + storm * 0.12 + (1 - day) * 0.035 + cold * 0.055) * (0.72 + Math.sin(clock * 0.12 + phase) * 0.2);
  });
  const fogColor = new THREE.Color(0x758b86)
    .lerp(new THREE.Color(0x07111c), 1 - day)
    .lerp(new THREE.Color(0x34434a), storm * 0.75)
    .lerp(new THREE.Color(0x81939b), cold * 0.24);
  (runtime.scene.fog as THREE.FogExp2).color.copy(fogColor);
  (runtime.scene.fog as THREE.FogExp2).density = 0.0085 + storm * 0.009 + (1 - day) * 0.002;
  runtime.renderer.toneMappingExposure = 0.48 + day * 0.68 + heat * 0.05;
  const lightningWave = world.weather === "Storm" ? Math.max(0, Math.sin(clock * 0.73 + Math.sin(clock * 0.19) * 4.2)) : 0;
  const lightning = Math.pow(lightningWave, 34) * (0.6 + Math.pow(Math.max(0, Math.sin(clock * 2.17)), 18));
  runtime.sun.intensity += lightning * 6.5;
  runtime.hemi.intensity += lightning * 2.4;
  runtime.renderer.toneMappingExposure += lightning * 0.22;
  const fireStrength = THREE.MathUtils.clamp(world.fire / 55, 0.12, 1.25);
  runtime.fireLight.intensity = (1.8 + (1 - day) * 3.8) * fireStrength * (0.9 + Math.sin(clock * 15) * 0.08 + Math.sin(clock * 23) * 0.05);
  runtime.fireFlames.scale.set(0.8 + fireStrength * 0.28, 0.55 + fireStrength * 0.68, 0.8 + fireStrength * 0.28);
  runtime.fireFlames.children.forEach((child, index) => {
    child.rotation.y = clock * (0.8 + index * 0.17) + index;
    child.scale.x = 0.82 + Math.sin(clock * 9 + index) * 0.09;
  });
  runtime.fireSmoke.children.forEach((child, index) => {
    const puff = child as THREE.Sprite;
    const material = puff.material as THREE.SpriteMaterial;
    const life = (clock * (0.12 + index * 0.007) + Number(puff.userData.phase ?? 0)) % 1;
    puff.position.y = 0.95 + life * 3.1;
    puff.position.x = Math.sin(clock * 0.38 + index * 2.1) * (0.08 + life * 0.28);
    puff.position.z = Math.cos(clock * 0.31 + index * 1.6) * (0.06 + life * 0.2);
    puff.scale.setScalar(0.46 + life * 1.25);
    material.opacity = (1 - life) * 0.13 * fireStrength * (0.7 + (1 - day) * 0.3);
  });
  const emberAttribute = runtime.fireEmbers.geometry.getAttribute("position") as THREE.BufferAttribute | undefined;
  if (emberAttribute) {
    for (let index = 0; index < emberAttribute.count; index += 1) {
      let y = emberAttribute.getY(index) + dt * (0.35 + (index % 7) * 0.045) * fireStrength;
      if (y > 2.25) y = 0.42 + (index % 5) * 0.045;
      emberAttribute.setY(index, y);
      emberAttribute.setX(index, emberAttribute.getX(index) + Math.sin(clock * 2 + index) * dt * 0.025);
    }
    emberAttribute.needsUpdate = true;
  }
}

function disposeScene(scene: THREE.Scene) {
  const textures = new Set<THREE.Texture>();
  scene.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (!mesh.isMesh && !(object as THREE.Points).isPoints && !(object as THREE.Line).isLine) return;
    (mesh.geometry as THREE.BufferGeometry | undefined)?.dispose?.();
    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    for (const material of materials) {
      if (!material) continue;
      for (const value of Object.values(material)) if (value instanceof THREE.Texture) textures.add(value);
      material.dispose();
    }
  });
  textures.forEach((texture) => texture.dispose());
}

async function loadSceneAssets(manager: THREE.LoadingManager, renderer: THREE.WebGLRenderer) {
  const gltfLoader = new GLTFLoader(manager);
  const draco = new DRACOLoader(manager);
  draco.setDecoderPath("/assets/draco/");
  gltfLoader.setDRACOLoader(draco);
  const textureLoader = new THREE.TextureLoader(manager);
  const hdrLoader = new RGBELoader(manager);
  const [soldier, michelle, readyPlayer, tree, rock, shrub, fern, house, environment, ...ground] = await Promise.all([
    gltfLoader.loadAsync(ASSET_URLS.soldier),
    gltfLoader.loadAsync(ASSET_URLS.michelle),
    gltfLoader.loadAsync(ASSET_URLS.readyPlayer),
    gltfLoader.loadAsync(ASSET_URLS.tree),
    gltfLoader.loadAsync(ASSET_URLS.rock),
    gltfLoader.loadAsync(ASSET_URLS.shrub),
    gltfLoader.loadAsync(ASSET_URLS.fern),
    gltfLoader.loadAsync(ASSET_URLS.house),
    hdrLoader.loadAsync(ASSET_URLS.environment),
    textureLoader.loadAsync(ASSET_URLS.ground),
    textureLoader.loadAsync(ASSET_URLS.groundNormal),
    textureLoader.loadAsync(ASSET_URLS.groundArm),
    textureLoader.loadAsync(ASSET_URLS.groundHeight),
  ]) as [GLTF, GLTF, GLTF, GLTF, GLTF, GLTF, GLTF, GLTF, THREE.DataTexture, ...THREE.Texture[]];
  draco.dispose();
  const anisotropy = Math.min(16, renderer.capabilities.getMaxAnisotropy());
  [soldier.scene, michelle.scene, readyPlayer.scene, tree.scene, rock.scene, shrub.scene, fern.scene].forEach((asset) => prepareAsset(asset, anisotropy));
  prepareSettlementAsset(house.scene, anisotropy);
  environment.mapping = THREE.EquirectangularReflectionMapping;
  const houseTemplate = extractTemplate(house.scene, /House_|Chimney_|SupportBeams_/i);
  const forestTree = extractTemplate(house.scene, /BTree_BrichTree/i);
  return { soldier, michelle, readyPlayer, tree, rock, shrub, fern, house, houseTemplate, forestTree, environment, ground, anisotropy };
}

function makeRetargetableClips(clips: THREE.AnimationClip[]) {
  return clips.map((clip) => new THREE.AnimationClip(
    clip.name,
    clip.duration,
    clip.tracks.filter((track) => track.name.endsWith(".quaternion")).map((track) => track.clone()),
  ));
}

export function WorldView({ worldRef, selectedId, onSelect, paused, speed }: WorldViewProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const selectedRef = useRef(selectedId);
  const onSelectRef = useRef(onSelect);
  const pausedRef = useRef(paused);
  const speedRef = useRef(speed);
  const qualityPresetRef = useRef<QualityPreset>("AUTO");
  const cameraModeRef = useRef<CameraMode>("overview");
  const [loading, setLoading] = useState(0);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [vitals, setVitals] = useState<RenderVitals>({ fps: 60, width: 0, height: 0, quality: "ULTRA" });
  const [qualityPreset, setQualityPreset] = useState<QualityPreset>("AUTO");
  const [cameraMode, setCameraMode] = useState<CameraMode>("overview");

  useEffect(() => { selectedRef.current = selectedId; }, [selectedId]);
  useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);
  useEffect(() => { pausedRef.current = paused; }, [paused]);
  useEffect(() => { speedRef.current = speed; }, [speed]);
  useEffect(() => { qualityPresetRef.current = qualityPreset; }, [qualityPreset]);
  useEffect(() => { cameraModeRef.current = cameraMode; }, [cameraMode]);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    let alive = true;
    let animationFrame = 0;
    let runtime: SceneRuntime | undefined;
    let resizeObserver: ResizeObserver | undefined;
    let pointerStart: { x: number; y: number; time: number } | undefined;
    let reviewPose: { id: string; clip: "idle" | "walk" | "run"; phase: number } | null = null;
    const manager = new THREE.LoadingManager();
    manager.onProgress = (_url, loaded, total) => {
      if (alive) setLoading(Math.min(98, Math.round((loaded / Math.max(total, 1)) * 100)));
    };
    manager.onError = (url) => {
      console.error(`Could not load 3D asset: ${url}`);
    };

    const initialize = async () => {
      try {
        const renderer = new THREE.WebGLRenderer({
          antialias: true,
          alpha: false,
          powerPreference: "high-performance",
          precision: "highp",
        });
        const mobile = window.innerWidth < 760;
        const nativePixelRatio = Math.min(window.devicePixelRatio || 1, mobile ? 1.45 : 2);
        let qualityScale = 1;
        let appliedQualityPreset = qualityPresetRef.current;
        const renderSize = new THREE.Vector2();
        const applyRenderResolution = () => {
          const width = Math.max(1, mount.clientWidth);
          const height = Math.max(1, mount.clientHeight);
          const requestedPixels = width * height * nativePixelRatio * nativePixelRatio;
          const fourKPixels = 3840 * 2160;
          const pixelBudgetScale = Math.min(1, Math.sqrt(fourKPixels / Math.max(requestedPixels, 1)));
          const presetScale = qualityPresetRef.current === "PERFORMANCE" ? 0.68 : qualityPresetRef.current === "CINEMATIC" ? 1 : qualityScale;
          renderer.setPixelRatio(nativePixelRatio * presetScale * pixelBudgetScale);
          renderer.setSize(width, height, false);
          renderer.getDrawingBufferSize(renderSize);
          return renderSize;
        };
        applyRenderResolution();
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.shadowMap.autoUpdate = false;
        renderer.shadowMap.needsUpdate = true;
        renderer.domElement.className = "world-webgl";
        renderer.domElement.setAttribute("aria-label", "A living 3D survival settlement. Drag to orbit, pinch or scroll to zoom, and select a survivor.");
        renderer.domElement.tabIndex = 0;
        mount.appendChild(renderer.domElement);

        const labels = new CSS2DRenderer();
        labels.domElement.className = "world-label-layer";
        mount.appendChild(labels.domElement);

        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x758b86, 0.009);
        const camera = new THREE.PerspectiveCamera(mobile ? 55 : 48, 1, 0.08, 260);
        camera.position.set(mobile ? 27 : 24, mobile ? 14 : 14.5, mobile ? 35 : 30);
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.target.set(0, 1.05, 0);
        controls.enableDamping = true;
        controls.dampingFactor = 0.065;
        controls.minDistance = 10;
        controls.maxDistance = 74;
        controls.minPolarAngle = 0.62;
        controls.maxPolarAngle = 1.45;
        controls.zoomToCursor = true;
        controls.screenSpacePanning = false;
        const onControlStart = () => {
          if (cameraModeRef.current === "free") return;
          cameraModeRef.current = "free";
          if (alive) setCameraMode("free");
        };
        controls.addEventListener("start", onControlStart);

        const hemi = new THREE.HemisphereLight(0x9dc5dd, 0x2d251d, 1.2);
        scene.add(hemi);
        const sun = new THREE.DirectionalLight(0xfff0d4, 2.7);
        sun.castShadow = true;
        const shadowResolution = mobile ? 1024 : window.innerWidth * nativePixelRatio >= 3000 ? 4096 : 2048;
        sun.shadow.mapSize.set(shadowResolution, shadowResolution);
        sun.shadow.camera.left = -38;
        sun.shadow.camera.right = 38;
        sun.shadow.camera.top = 34;
        sun.shadow.camera.bottom = -34;
        sun.shadow.camera.near = 1;
        sun.shadow.camera.far = 125;
        sun.shadow.bias = -0.00016;
        sun.shadow.normalBias = 0.028;
        scene.add(sun);
        const fireLight = new THREE.PointLight(0xff7f32, 5, 16, 1.8);
        fireLight.position.copy(scenePosition(CAMP_X, CAMP_Y)).add(new THREE.Vector3(0, 1.25, 0));
        scene.add(fireLight);

        const sky = makeSky();
        scene.add(sky.mesh);
        const stars = makeStars();
        scene.add(stars);
        const river = makeRiver();
        scene.add(river.mesh);
        const rain = makeRain();
        scene.add(rain);
        const mist = makeMist();
        scene.add(mist);

        const assets = await loadSceneAssets(manager, renderer);
        if (!alive) return;
        scene.environment = assets.environment;
        scene.environmentIntensity = 0.72;
        scene.add(makeTerrain(assets.ground, assets.anisotropy));

        scene.add(makePathRibbon([[24, 20], [21, 19.9], [18, 20.2], [15.4, 20], [12.8, 20]], 0.62));
        scene.add(makePathRibbon([[24, 20], [22.4, 22.2], [19.5, 23.5]], 0.48));
        scene.add(makePathRibbon([[24, 20], [26.8, 18.3], [29.3, 17.3]], 0.52));
        scene.add(makeBridge());
        scene.add(makeCampDetails());
        const emptyFlames = new THREE.Group();
        const emptySmoke = new THREE.Group();
        const emptyEmbers = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ visible: false }));

        runtime = {
          renderer,
          labels,
          scene,
          camera,
          controls,
          characters: new Map(),
          hitTargets: [],
          buildings: new Map(),
          projects: new Map(),
          waterMaterial: river.material,
          skyMaterial: sky.material,
          stars,
          rain,
          sun,
          hemi,
          fireLight,
          fireFlames: emptyFlames,
          fireSmoke: emptySmoke,
          fireEmbers: emptyEmbers,
          mist,
          mixers: [],
          templates: {
            people: [assets.readyPlayer.scene, assets.michelle.scene, assets.readyPlayer.scene, assets.michelle.scene],
            animations: makeRetargetableClips(assets.soldier.animations),
            tree: assets.forestTree,
            deadTree: assets.tree.scene,
            rock: assets.rock.scene,
            shrub: assets.shrub.scene,
            fern: assets.fern.scene,
            house: assets.houseTemplate,
          },
        };

        populateLandscape(runtime, worldRef.current, mobile);
        syncBuildings(runtime, worldRef.current);
        worldRef.current.agents.forEach((agent) => addCharacter(runtime!, agent));

        if (window.__EDEN_QA_ENABLED__) {
          qualityPresetRef.current = "CINEMATIC";
          setQualityPreset("CINEMATIC");
          const gl = renderer.getContext();
          const debug = gl.getExtension("WEBGL_debug_renderer_info");
          window.__EDEN_QA__ = {
            frames: 0,
            pose(value) {
              if (value && (!runtime!.characters.has(value.id) || !["idle", "walk", "run"].includes(value.clip) || value.phase < 0 || value.phase > 1)) {
                throw new Error("Invalid character pose capture");
              }
              reviewPose = value;
              if (value) {
                selectedRef.current = value.id;
                onSelectRef.current(value.id);
              }
            },
            sceneImage() {
              renderer.render(scene, camera);
              return renderer.domElement.toDataURL("image/png");
            },
            view(name) {
              syncBuildings(runtime!, worldRef.current);
              for (const person of worldRef.current.agents) {
                const character = runtime!.characters.get(person.id);
                if (character) character.root.position.copy(scenePosition(person.x, person.y));
              }
              const views: Record<string, [number, number, number]> = {
                world: mobile ? [27, 14, 35] : [24, 14.5, 30],
                camp: mobile ? [20, 9, 25.5] : [15.5, 8, 19],
                east: [-21, 10, 19],
                north: [4, 11, -27],
                "human-front": [0, 1.15, 3.8],
                "human-side": [3.8, 1.15, 0],
                "human-rear": [0, 1.15, -3.8],
              };
              if (!views[name]) throw new Error(`Unknown capture view: ${name}`);
              cameraModeRef.current = "free";
              setCameraMode("free");
              controls.enableDamping = false;
              controls.minDistance = 1;
              controls.target.set(0, 1.05, 0);
              camera.position.fromArray(views[name]);
              if (name.startsWith("human-")) {
                const focus = runtime!.characters.get(selectedRef.current);
                if (!focus) throw new Error("The selected human has not loaded");
                camera.position.applyQuaternion(focus.root.quaternion).add(focus.root.position);
                controls.target.copy(focus.root.position).add(new THREE.Vector3(0, 0.95, 0));
              }
              controls.update();
              renderer.render(scene, camera);
              labels.render(scene, camera);
            },
            inspect() {
              renderer.getDrawingBufferSize(renderSize);
              return {
                webgl: gl.getParameter(gl.VERSION),
                renderer: gl.getParameter(debug ? debug.UNMASKED_RENDERER_WEBGL : gl.RENDERER),
                contextLost: gl.isContextLost(),
                width: renderSize.x,
                height: renderSize.y,
                camera: camera.position.toArray(),
                target: controls.target.toArray(),
                drawCalls: renderer.info.render.calls,
                triangles: renderer.info.render.triangles,
                humans: runtime!.characters.size,
                worldElapsed: worldRef.current.elapsed,
                frames: window.__EDEN_QA__?.frames ?? 0,
                astraAgents: worldRef.current.agents.filter((person) => person.brain === "astra").length,
                selected: (() => {
                  const person = worldRef.current.agents.find((person) => person.id === selectedRef.current);
                  const character = runtime!.characters.get(selectedRef.current);
                  return {
                    id: person?.id,
                    rig: person && Number(person.id.split("-")[1]) % 2 === 0 ? "Michelle" : "ReadyPlayer",
                    action: person?.action,
                    clip: character?.activeClip,
                    clipTime: character?.clips[character.activeClip]?.time,
                    clipDuration: character?.clips[character.activeClip]?.getClip().duration,
                    position: character?.root.position.toArray(),
                    controlledPose: reviewPose,
                  };
                })(),
              };
            },
          };
        }

        const raycaster = new THREE.Raycaster();
        const pointer = new THREE.Vector2();
        const raycast = (event: PointerEvent) => {
          if (!runtime) return undefined;
          const bounds = renderer.domElement.getBoundingClientRect();
          pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
          pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;
          raycaster.setFromCamera(pointer, camera);
          const hit = raycaster.intersectObjects(runtime.hitTargets, false)[0];
          return hit?.object.userData.agentId as string | undefined;
        };
        const onPointerDown = (event: PointerEvent) => {
          pointerStart = { x: event.clientX, y: event.clientY, time: performance.now() };
        };
        const onPointerUp = (event: PointerEvent) => {
          if (!pointerStart) return;
          const moved = Math.hypot(event.clientX - pointerStart.x, event.clientY - pointerStart.y);
          const quick = performance.now() - pointerStart.time < 650;
          pointerStart = undefined;
          if (moved > 8 || !quick) return;
          const id = raycast(event);
          if (id) onSelectRef.current(id);
        };
        const onPointerMove = (event: PointerEvent) => {
          renderer.domElement.style.cursor = raycast(event) ? "pointer" : "grab";
        };
        renderer.domElement.addEventListener("pointerdown", onPointerDown);
        renderer.domElement.addEventListener("pointerup", onPointerUp);
        renderer.domElement.addEventListener("pointermove", onPointerMove);

        resizeObserver = new ResizeObserver(() => {
          const width = Math.max(1, mount.clientWidth);
          const height = Math.max(1, mount.clientHeight);
          camera.aspect = width / height;
          camera.updateProjectionMatrix();
          const buffer = applyRenderResolution();
          labels.setSize(width, height);
          if (alive) setVitals((previous) => ({ ...previous, width: Math.round(buffer.x), height: Math.round(buffer.y) }));
        });
        resizeObserver.observe(mount);

        let previous = performance.now();
        let clock = 0;
        let syncAccumulator = 0;
        let fpsElapsed = 0;
        let fpsFrames = 0;
        let lowFpsWindows = 0;
        let highFpsWindows = 0;
        let shadowAccumulator = 0;
        const targetPosition = new THREE.Vector3();
        const targetQuaternion = new THREE.Quaternion();
        const cameraDestination = new THREE.Vector3();
        const cameraLook = new THREE.Vector3();
        const animate = (now: number) => {
          if (!alive || !runtime) return;
          const elapsedFrameTime = Math.max(0, (now - previous) / 1000);
          const dt = Math.min(0.05, elapsedFrameTime);
          previous = now;
          if (!pausedRef.current) clock += dt * Math.min(3.2, 0.9 + speedRef.current * 0.18);
          syncAccumulator += dt;
          shadowAccumulator += dt;
          fpsElapsed += elapsedFrameTime;
          fpsFrames += 1;
          if (appliedQualityPreset !== qualityPresetRef.current) {
            appliedQualityPreset = qualityPresetRef.current;
            qualityScale = appliedQualityPreset === "PERFORMANCE" ? 0.68 : 1;
            lowFpsWindows = 0;
            highFpsWindows = 0;
            renderer.shadowMap.enabled = appliedQualityPreset !== "PERFORMANCE" || !mobile;
            renderer.shadowMap.needsUpdate = true;
            applyRenderResolution();
          }
          if (shadowAccumulator > 0.48) {
            shadowAccumulator = 0;
            renderer.shadowMap.needsUpdate = true;
          }
          if (fpsElapsed >= 1) {
            const fps = fpsFrames / fpsElapsed;
            if (fps < 51) {
              lowFpsWindows += 1;
              highFpsWindows = 0;
            } else if (fps > 58) {
              highFpsWindows += 1;
              lowFpsWindows = 0;
            } else {
              lowFpsWindows = 0;
              highFpsWindows = 0;
            }
            if (qualityPresetRef.current === "AUTO" && lowFpsWindows >= 2 && qualityScale > 0.62) {
              qualityScale = Math.max(0.62, qualityScale - 0.1);
              lowFpsWindows = 0;
              applyRenderResolution();
            } else if (qualityPresetRef.current === "AUTO" && highFpsWindows >= 4 && qualityScale < 1) {
              qualityScale = Math.min(1, qualityScale + 0.05);
              highFpsWindows = 0;
              applyRenderResolution();
            }
            renderer.getDrawingBufferSize(renderSize);
            if (alive) {
              setVitals({
                fps: Math.round(fps),
                width: Math.round(renderSize.x),
                height: Math.round(renderSize.y),
                quality: qualityPresetRef.current === "CINEMATIC" ? "CINEMATIC" : qualityPresetRef.current === "PERFORMANCE" ? "PERFORMANCE" : qualityScale > 0.92 ? "ULTRA" : qualityScale > 0.74 ? "HIGH" : "ADAPTIVE",
              });
            }
            fpsElapsed = 0;
            fpsFrames = 0;
          }
          if (syncAccumulator > 0.75) {
            syncAccumulator = 0;
            for (const agent of worldRef.current.agents) if (!runtime.characters.has(agent.id)) addCharacter(runtime, agent);
            syncBuildings(runtime, worldRef.current);
          }
          const agents = new Map(worldRef.current.agents.map((agent) => [agent.id, agent]));
          for (const character of runtime.characters.values()) {
            const agent = agents.get(character.id);
            if (!agent) continue;
            const selected = selectedRef.current === agent.id;
            character.selection.visible = selected && agent.alive;
            if (selected) {
              const pulse = 1 + Math.sin(clock * 3.4) * 0.08;
              character.selection.scale.setScalar(pulse);
              character.selection.rotation.z = clock * 0.32;
              (character.selection.material as THREE.MeshBasicMaterial).opacity = 0.72 + Math.sin(clock * 3.4) * 0.16;
            }
            (character.label.element as HTMLElement).classList.toggle("selected", selected);
            (character.label.element as HTMLElement).classList.toggle("speaking", Boolean(agent.speech && agent.speechUntil > worldRef.current.elapsed));
            (character.label.element as HTMLElement).classList.toggle("astra", agent.brain === "astra" || agent.brain === "waiting");
            character.labelName.textContent = agent.speech && agent.speechUntil > worldRef.current.elapsed ? `${agent.name}: “${agent.speech}”` : agent.name;
            character.labelIntent.textContent = agent.brain === "waiting" ? "Astra is thinking" : ACTION_NAMES[agent.action];
            character.label.visible = selected || Boolean(agent.speech && agent.speechUntil > worldRef.current.elapsed);
            character.root.visible = agent.alive;
            if (!agent.alive) continue;
            scenePosition(agent.x, agent.y, targetPosition);
            let separateX = 0;
            let separateZ = 0;
            for (const other of agents.values()) {
              if (!other.alive || other.id === agent.id) continue;
              let dx = agent.x - other.x;
              let dz = agent.y - other.y;
              let distance = Math.hypot(dx, dz);
              if (distance >= 0.82) continue;
              if (distance < 0.001) {
                const angle = (idSeed(agent.id) % 628) / 100;
                dx = Math.cos(angle);
                dz = Math.sin(angle);
                distance = 1;
              }
              const push = (0.82 - distance) * 0.48 * WORLD_SCALE;
              separateX += (dx / distance) * push;
              separateZ += (dz / distance) * push;
            }
            const separationLength = Math.hypot(separateX, separateZ);
            if (separationLength > 0.52) {
              separateX = (separateX / separationLength) * 0.52;
              separateZ = (separateZ / separationLength) * 0.52;
            }
            character.separation.x = THREE.MathUtils.damp(character.separation.x, separateX, 9, dt);
            character.separation.y = THREE.MathUtils.damp(character.separation.y, separateZ, 9, dt);
            targetPosition.x += character.separation.x;
            targetPosition.z += character.separation.y;
            character.root.position.x = THREE.MathUtils.damp(character.root.position.x, targetPosition.x, 11, dt);
            character.root.position.y = THREE.MathUtils.damp(character.root.position.y, targetPosition.y, 13, dt);
            character.root.position.z = THREE.MathUtils.damp(character.root.position.z, targetPosition.z, 11, dt);
            const remaining = Math.hypot(agent.targetX - agent.x, agent.targetY - agent.y);
            const moving = remaining > 0.34;
            if (moving) {
              const destination = scenePosition(agent.targetX, agent.targetY, targetPosition);
              character.heading = Math.atan2(destination.x - character.root.position.x, destination.z - character.root.position.z);
              targetQuaternion.setFromAxisAngle(new THREE.Vector3(0, 1, 0), character.heading);
              character.root.quaternion.slerp(targetQuaternion, 1 - Math.exp(-dt * 9));
            }
            const locomotion: "idle" | "walk" | "run" = reviewPose?.id === agent.id ? reviewPose.clip : moving ? (speedRef.current >= 4 ? "run" : "walk") : "idle";
            switchClip(character, locomotion);
            const clipSpeed = pausedRef.current ? 0 : locomotion === "run" ? Math.min(2.2, 0.75 + speedRef.current * 0.22) : Math.min(1.7, 0.72 + speedRef.current * 0.12);
            character.mixer.update(dt * clipSpeed);
            if (reviewPose?.id === agent.id) {
              for (const action of Object.values(character.clips)) action?.setEffectiveWeight(0);
              const action = character.clips[reviewPose.clip];
              if (action) {
                action.stopFading().setEffectiveWeight(1).play();
                action.time = action.getClip().duration * reviewPose.phase;
                character.mixer.update(0);
              }
            }
            if (!pausedRef.current) taskGesture(character, agent, worldRef.current.elapsed, dt);
            syncTaskProp(character, agent, worldRef.current.elapsed, dt);
          }
          updateWeather(runtime, worldRef.current, dt, clock);
          if (cameraModeRef.current !== "free") {
            if (cameraModeRef.current === "follow") {
              const focus = runtime.characters.get(selectedRef.current);
              if (focus?.root.visible) {
                cameraLook.copy(focus.root.position).add(new THREE.Vector3(0, 1.05, 0));
                cameraDestination.copy(focus.root.position).add(new THREE.Vector3(mobile ? 10 : 7.8, mobile ? 4.7 : 4.8, mobile ? 11.5 : 8.4));
              } else {
                cameraLook.set(0, 1.05, 0);
                cameraDestination.set(mobile ? 20 : 14, mobile ? 9 : 10, mobile ? 25 : 16);
              }
            } else if (cameraModeRef.current === "camp") {
              cameraLook.set(0, 1.05, 0);
              cameraDestination.set(mobile ? 20 : 15.5, mobile ? 9 : 8, mobile ? 25.5 : 19);
            } else {
              cameraLook.set(0, 1.05, 0);
              cameraDestination.set(mobile ? 27 : 24, mobile ? 14 : 14.5, mobile ? 35 : 30);
            }
            const cameraDamping = cameraModeRef.current === "follow" ? 4.8 : 3.2;
            const blend = 1 - Math.exp(-dt * cameraDamping);
            controls.target.lerp(cameraLook, blend);
            camera.position.lerp(cameraDestination, blend);
          }
          controls.update();
          renderer.render(scene, camera);
          labels.render(scene, camera);
          if (window.__EDEN_QA__) window.__EDEN_QA__.frames += 1;
          animationFrame = requestAnimationFrame(animate);
        };
        setLoading(100);
        setReady(true);
        animationFrame = requestAnimationFrame(animate);

        return () => {
          controls.removeEventListener("start", onControlStart);
          renderer.domElement.removeEventListener("pointerdown", onPointerDown);
          renderer.domElement.removeEventListener("pointerup", onPointerUp);
          renderer.domElement.removeEventListener("pointermove", onPointerMove);
        };
      } catch (reason) {
        if (alive) {
          console.error(reason);
          setError("The production 3D scene could not start on this device. WebGL 2 and hardware acceleration are required.");
        }
      }
      return undefined;
    };

    let removePointerListeners: (() => void) | undefined;
    void initialize().then((cleanup) => { removePointerListeners = cleanup; });
    return () => {
      alive = false;
      cancelAnimationFrame(animationFrame);
      resizeObserver?.disconnect();
      removePointerListeners?.();
      if (window.__EDEN_QA_ENABLED__) delete window.__EDEN_QA__;
      if (runtime) {
        runtime.controls.dispose();
        runtime.mixers.forEach((mixer) => mixer.stopAllAction());
        disposeScene(runtime.scene);
        runtime.renderer.dispose();
        runtime.renderer.forceContextLoss();
        runtime.labels.domElement.remove();
        runtime.renderer.domElement.remove();
      }
    };
  }, [worldRef]);

  const cycleQuality = () => {
    const options: QualityPreset[] = ["AUTO", "CINEMATIC", "PERFORMANCE"];
    const next = options[(options.indexOf(qualityPreset) + 1) % options.length];
    qualityPresetRef.current = next;
    setQualityPreset(next);
  };

  const chooseCamera = (mode: CameraMode) => {
    cameraModeRef.current = mode;
    setCameraMode(mode);
  };

  return (
    <div className="world-view" ref={mountRef}>
      {ready && !error ? (
        <div className="world-render-vitals" aria-label={`Real-time 3D renderer, ${vitals.fps} frames per second`}>
          <strong>REALTIME 3D</strong>
          <span>{vitals.width}×{vitals.height}</span>
          <span>{vitals.quality}</span>
          <span>{vitals.fps} FPS</span>
        </div>
      ) : null}
      {ready && !error ? (
        <div className="world-view-controls" aria-label="3D world controls">
          <span>CAMERA</span>
          <button className={cameraMode === "overview" ? "active" : ""} onClick={() => chooseCamera("overview")}>World</button>
          <button className={cameraMode === "camp" ? "active" : ""} onClick={() => chooseCamera("camp")}>Camp</button>
          <button className={cameraMode === "follow" ? "active" : ""} onClick={() => chooseCamera("follow")}>Follow</button>
          <i />
          <button className={`quality ${qualityPreset.toLowerCase()}`} onClick={cycleQuality} title="Cycle adaptive, cinematic, and performance rendering">
            {qualityPreset === "AUTO" ? "Auto · 60" : qualityPreset === "CINEMATIC" ? "Cinema" : "Performance"}
          </button>
        </div>
      ) : null}
      {!ready && !error ? (
        <div className="world-loader" role="status" aria-live="polite">
          <div className="world-loader-mark"><span /><span /><span /></div>
          <strong>Building the living world</strong>
          <p>Rigged humans · terrain · weather · settlement</p>
          <div className="world-loader-track"><span style={{ width: `${loading}%` }} /></div>
          <small>{loading}%</small>
        </div>
      ) : null}
      {error ? <div className="world-error" role="alert"><strong>3D renderer unavailable</strong><p>{error}</p></div> : null}
    </div>
  );
}
