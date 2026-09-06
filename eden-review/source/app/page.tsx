"use client";

import {
  Activity,
  BrainCircuit,
  ChevronDown,
  ChevronUp,
  CloudLightning,
  Crosshair,
  Droplets,
  Flame,
  HeartPulse,
  Home,
  Hammer,
  Handshake,
  Pause,
  Play,
  Plus,
  Route,
  ShieldAlert,
  Sparkles,
  Sprout,
  Stethoscope,
  Trees,
  Users,
  Utensils,
  Wind,
  Waves,
  Zap,
} from "lucide-react";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const WorldView = dynamic(
  () => import("./WorldView").then((module) => module.WorldView),
  {
    ssr: false,
    loading: () => (
      <div className="world-view">
        <div className="world-loader" role="status" aria-live="polite">
          <div className="world-loader-mark"><span /><span /><span /></div>
          <strong>Building the living world</strong>
          <p>Real-time 3D · rigged humans · living wilderness</p>
        </div>
      </div>
    ),
  },
);

type ActionName =
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

type Role =
  | "Coordinator"
  | "Forager"
  | "Builder"
  | "Medic"
  | "Water Carrier"
  | "Scout"
  | "Cook"
  | "Caretaker"
  | "Engineer"
  | "Guard"
  | "Farmer";

type Weather = "Clear" | "Rain" | "Storm" | "Cold snap" | "Heat";
type ResourceKind = "tree" | "berries" | "rock" | "herbs";
type BuildingKind = "fire" | "shelter" | "store" | "farm" | "water" | "clinic" | "workshop";
type ConstructionKind = Exclude<BuildingKind, "fire" | "store" | "farm">;
type TaskPhase = "outbound" | "working" | "returning";
type Directive = "balanced" | "water" | "food" | "build" | "care" | "watch";

interface Agent {
  id: string;
  name: string;
  age: number;
  role: Role;
  traits: string[];
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  action: ActionName;
  actionProgress: number;
  decisionDue: number;
  health: number;
  hunger: number;
  thirst: number;
  fatigue: number;
  cold: number;
  morale: number;
  alive: boolean;
  brain: "local" | "astra" | "waiting";
  thought: string;
  speech: string;
  speechUntil: number;
  memories: string[];
  relationships: Record<string, number>;
  color: string;
  skin: string;
  hair: string;
  seed: number;
  carrying: string;
  cargoAmount: number;
  taskPhase: TaskPhase;
}

interface ResourceNode {
  id: string;
  kind: ResourceKind;
  x: number;
  y: number;
  amount: number;
}

interface Building {
  id: string;
  kind: BuildingKind;
  x: number;
  y: number;
  level: number;
  progress?: number;
  condition?: number;
}

interface ConstructionProject {
  id: string;
  kind: ConstructionKind;
  x: number;
  y: number;
  progress: number;
  startedBy: string;
}

interface EventEntry {
  id: number;
  minute: number;
  tone: "good" | "warning" | "neutral" | "astra";
  text: string;
}

interface WorldState {
  layoutVersion: number;
  day: number;
  minute: number;
  elapsed: number;
  weather: Weather;
  weatherUntil: number;
  priority: string;
  food: number;
  water: number;
  wood: number;
  stone: number;
  medicine: number;
  fire: number;
  directive: Directive;
  directiveUntil: number;
  nextIncident: number;
  agents: Agent[];
  resources: ResourceNode[];
  buildings: Building[];
  projects: ConstructionProject[];
  events: EventEntry[];
  eventId: number;
  lastHour: number;
}

interface AstraStatus {
  configured: boolean;
  model: string;
}

interface AstraDecision {
  action: ActionName;
  target_id: string;
  thought: string;
  speech: string;
  memory: string;
  priority: number;
}

interface Snapshot {
  day: number;
  time: string;
  weather: Weather;
  priority: string;
  food: number;
  water: number;
  wood: number;
  stone: number;
  medicine: number;
  fire: number;
  directive: Directive;
  directiveRemaining: number;
  alive: number;
  total: number;
  shelter: number;
  averageHealth: number;
  readiness: number;
  cohesion: number;
  risk: "LOW" | "GUARDED" | "HIGH" | "CRITICAL";
  phase: string;
  phaseNumber: number;
  objectives: SettlementObjective[];
  teams: TeamSnapshot[];
  projects: ConstructionProject[];
  events: EventEntry[];
  agents: Agent[];
}

interface SettlementObjective {
  id: string;
  label: string;
  detail: string;
  progress: number;
  complete: boolean;
}

interface TeamSnapshot {
  id: string;
  name: string;
  mission: string;
  members: number;
  active: number;
}

const WORLD_W = 48;
const WORLD_H = 38;
const CAMP_X = 24;
const CAMP_Y = 20;
const SETTLEMENT_LAYOUT_VERSION = 3;
const SHELTER_OFFSETS = [
  [-5.5, -5.6],
  [1, -7],
  [6.6, -4.3],
  [7.4, 1.3],
  [3.3, 7.2],
  [-3, 7.2],
  [-7.4, 3],
  [-7, -2.7],
] as const;
const ALLOWED_ACTIONS: ActionName[] = [
  "drink",
  "eat",
  "rest",
  "gather_food",
  "gather_water",
  "gather_wood",
  "gather_stone",
  "gather_medicine",
  "build_shelter",
  "tend_fire",
  "heal",
  "assist",
  "explore",
  "socialize",
  "guard",
  "farm",
];
const CARRY_ACTIONS: ActionName[] = ["gather_food", "gather_water", "gather_wood", "gather_stone", "gather_medicine"];

const ACTION_LABELS: Record<ActionName, string> = {
  idle: "Thinking",
  drink: "Getting a drink",
  eat: "Eating a ration",
  rest: "Recovering",
  gather_food: "Foraging for food",
  gather_water: "Hauling water",
  gather_wood: "Gathering timber",
  gather_stone: "Collecting stone",
  gather_medicine: "Searching for medicine",
  build_shelter: "Advancing construction",
  tend_fire: "Tending the fire",
  heal: "Treating an injury",
  assist: "Helping a neighbor",
  explore: "Scouting terrain",
  socialize: "Strengthening bonds",
  guard: "Watching the perimeter",
  farm: "Working the food plots",
};

const BUILDING_NAMES: Record<ConstructionKind, string> = {
  shelter: "timber lodge",
  water: "water house",
  clinic: "field clinic",
  workshop: "makers' lodge",
};

const BUILDING_COSTS: Record<ConstructionKind, { wood: number; stone: number }> = {
  shelter: { wood: 10, stone: 3 },
  water: { wood: 16, stone: 8 },
  clinic: { wood: 20, stone: 12 },
  workshop: { wood: 26, stone: 18 },
};

const DIRECTIVE_LABELS: Record<Directive, string> = {
  balanced: "Balanced plan",
  water: "Secure water",
  food: "Stock food",
  build: "Accelerate building",
  care: "Protect the vulnerable",
  watch: "Scout and defend",
};

const NAMES = [
  "Mara", "Jonah", "Imani", "Elias", "Nia", "Mateo", "Sora", "David", "Amara", "Theo",
  "Leila", "Micah", "Zuri", "Noah", "Rina", "Caleb", "Ada", "Malik", "Esme", "Ren",
  "Talia", "Owen", "Priya", "Isaac", "June", "Samir", "Avery", "Lena", "Kai", "Naomi",
];

const ROLES: Role[] = [
  "Coordinator", "Forager", "Builder", "Medic", "Water Carrier", "Scout", "Cook", "Caretaker",
  "Engineer", "Guard", "Farmer", "Forager", "Builder", "Water Carrier", "Medic", "Scout",
  "Farmer", "Cook", "Builder", "Caretaker", "Guard", "Forager", "Engineer", "Farmer",
];

const TRAITS = [
  ["steady", "protective"], ["curious", "warm"], ["practical", "patient"], ["empathetic", "decisive"],
  ["resilient", "quiet"], ["bold", "observant"], ["inventive", "playful"], ["gentle", "communal"],
  ["analytical", "stubborn"], ["vigilant", "loyal"], ["optimistic", "methodical"], ["resourceful", "direct"],
];

const CLOTHES = ["#d97745", "#4f9f94", "#d6b25e", "#6879b7", "#a36078", "#6f9a63", "#bd6f50", "#5f8eb1"];
const SKINS = ["#f1c7a5", "#dca57e", "#bb7958", "#8b533d", "#673c2c", "#4a2a22"];
const HAIR = ["#201814", "#3b251a", "#5a3924", "#17191d", "#6a5547"];

function mulberry32(seed: number) {
  return () => {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function clamp(value: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, value));
}

function terrainAt(x: number, y: number) {
  const nx = (x - WORLD_W / 2) / (WORLD_W / 2);
  const ny = (y - WORLD_H / 2) / (WORLD_H / 2);
  const edge = 1 - Math.sqrt(nx * nx + ny * ny);
  const waves = Math.sin(x * 0.49) * 0.075 + Math.cos(y * 0.43) * 0.07 + Math.sin((x + y) * 0.21) * 0.06;
  const river = Math.abs(x - (9 + y * 0.2 + Math.sin(y * 0.31) * 2.4));
  if (edge + waves < 0.09 || river < 0.72) return { kind: "water", h: -1 } as const;
  if (edge + waves < 0.15 || river < 1.35) return { kind: "sand", h: 0 } as const;
  const ridge = Math.sin(x * 0.18) + Math.cos(y * 0.24) + Math.sin((x - y) * 0.13);
  if (ridge > 1.62 && x > 28) return { kind: "rock", h: 2 } as const;
  if (Math.sin(x * 0.31) + Math.cos(y * 0.38) > 0.78) return { kind: "forest", h: 1 } as const;
  return { kind: "grass", h: ridge > 0.7 ? 1 : 0 } as const;
}

function isLand(x: number, y: number) {
  const tile = terrainAt(Math.round(x), Math.round(y));
  return tile.kind !== "water" && x > 1 && y > 1 && x < WORLD_W - 2 && y < WORLD_H - 2;
}

function nearestLand(x: number, y: number) {
  if (isLand(x, y)) return { x, y };
  for (let radius = 1; radius < 10; radius += 1) {
    for (let a = 0; a < 24; a += 1) {
      const angle = (a / 24) * Math.PI * 2;
      const px = clamp(x + Math.cos(angle) * radius, 2, WORLD_W - 3);
      const py = clamp(y + Math.sin(angle) * radius, 2, WORLD_H - 3);
      if (isLand(px, py)) return { x: px, y: py };
    }
  }
  return { x: CAMP_X, y: CAMP_Y };
}

function settlementLocation(kind: BuildingKind, index = 0) {
  if (kind === "fire") return nearestLand(CAMP_X, CAMP_Y);
  if (kind === "shelter") {
    const [offsetX, offsetY] = SHELTER_OFFSETS[index % SHELTER_OFFSETS.length];
    const ring = Math.floor(index / SHELTER_OFFSETS.length);
    const spread = 1 + ring * 0.28;
    return nearestLand(CAMP_X + offsetX * spread, CAMP_Y + offsetY * spread);
  }
  const fixed: Record<Exclude<BuildingKind, "fire" | "shelter">, readonly [number, number]> = {
    store: [-2.6, 1.35],
    farm: [-1.2, -8.4],
    water: [-8.3, -0.6],
    clinic: [8, 5.1],
    workshop: [-2.8, 8.6],
  };
  const [offsetX, offsetY] = fixed[kind];
  return nearestLand(CAMP_X + offsetX, CAMP_Y + offsetY);
}

function formatTime(minute: number) {
  const normalized = ((minute % 1440) + 1440) % 1440;
  const hour = Math.floor(normalized / 60);
  const mins = Math.floor(normalized % 60);
  const suffix = hour >= 12 ? "PM" : "AM";
  const h12 = hour % 12 || 12;
  return `${h12}:${String(mins).padStart(2, "0")} ${suffix}`;
}

function logEvent(world: WorldState, text: string, tone: EventEntry["tone"] = "neutral") {
  world.events.unshift({ id: ++world.eventId, minute: world.minute + (world.day - 1) * 1440, tone, text });
  world.events = world.events.slice(0, 45);
}

function createAgent(index: number, total: number): Agent {
  const random = mulberry32(5900 + index * 113);
  const angle = (index / total) * Math.PI * 2;
  const radius = 2.2 + (index % 4) * 0.55;
  const place = nearestLand(CAMP_X + Math.cos(angle) * radius, CAMP_Y + Math.sin(angle) * radius);
  return {
    id: `human-${index + 1}`,
    name: NAMES[index % NAMES.length],
    age: 21 + Math.floor(random() * 38),
    role: ROLES[index % ROLES.length],
    traits: TRAITS[index % TRAITS.length],
    x: place.x,
    y: place.y,
    targetX: place.x,
    targetY: place.y,
    action: "idle",
    actionProgress: 0,
    decisionDue: random() * 4,
    health: 82 + random() * 18,
    hunger: 15 + random() * 18,
    thirst: 12 + random() * 20,
    fatigue: 8 + random() * 20,
    cold: 3 + random() * 8,
    morale: 64 + random() * 25,
    alive: true,
    brain: "local",
    thought: "Taking stock of the camp and the people around me.",
    speech: "",
    speechUntil: 0,
    memories: ["We arrived together with only a few shared supplies."],
    relationships: {},
    color: CLOTHES[index % CLOTHES.length],
    skin: SKINS[Math.floor(random() * SKINS.length)],
    hair: HAIR[Math.floor(random() * HAIR.length)],
    seed: Math.floor(random() * 1_000_000),
    carrying: "",
    cargoAmount: 0,
    taskPhase: "outbound",
  };
}

function generateResources() {
  const random = mulberry32(82731);
  const nodes: ResourceNode[] = [];
  const desired: Array<[ResourceKind, number]> = [["tree", 120], ["berries", 44], ["rock", 42], ["herbs", 18]];
  for (const [kind, count] of desired) {
    let placed = 0;
    let attempts = 0;
    while (placed < count && attempts < count * 80) {
      attempts += 1;
      const x = 2 + random() * (WORLD_W - 4);
      const y = 2 + random() * (WORLD_H - 4);
      const terrain = terrainAt(Math.round(x), Math.round(y));
      const campDistance = Math.hypot(x - CAMP_X, y - CAMP_Y);
      const suitable = isLand(x, y) && campDistance > 4.2 &&
        (kind !== "tree" || terrain.kind === "forest" || random() > 0.55) &&
        (kind !== "rock" || terrain.kind === "rock" || random() > 0.7);
      if (!suitable) continue;
      nodes.push({ id: `${kind}-${placed}`, kind, x, y, amount: kind === "tree" ? 5 : kind === "rock" ? 4 : 3 });
      placed += 1;
    }
  }
  return nodes;
}

function createWorld(): WorldState {
  const agents = Array.from({ length: 24 }, (_, index) => createAgent(index, 24));
  for (const agent of agents) {
    for (const other of agents) {
      if (agent.id !== other.id) agent.relationships[other.id] = 38 + ((agent.seed + other.seed) % 34);
    }
  }
  return {
    layoutVersion: SETTLEMENT_LAYOUT_VERSION,
    day: 1,
    minute: 7 * 60 + 10,
    elapsed: 0,
    weather: "Clear",
    weatherUntil: 260,
    priority: "Build enough shelter before the first cold night",
    food: 48,
    water: 58,
    wood: 24,
    stone: 10,
    medicine: 4,
    fire: 32,
    directive: "balanced",
    directiveUntil: 0,
    nextIncident: 150,
    agents,
    resources: generateResources(),
    buildings: [
      { id: "fire-main", kind: "fire", ...settlementLocation("fire"), level: 1, condition: 100 },
      { id: "store-main", kind: "store", ...settlementLocation("store"), level: 1, condition: 100 },
      { id: "shelter-1", kind: "shelter", ...settlementLocation("shelter", 0), level: 1, condition: 100 },
      { id: "shelter-2", kind: "shelter", ...settlementLocation("shelter", 1), level: 1, condition: 100 },
    ],
    projects: [],
    events: [
      { id: 3, minute: 7 * 60 + 10, tone: "warning", text: "Twenty-four survivors reach the valley with supplies for only a few days." },
      { id: 2, minute: 7 * 60 + 5, tone: "good", text: "Mara proposes a shared store: no private stockpiles while lives depend on it." },
      { id: 1, minute: 7 * 60, tone: "neutral", text: "The first fire is lit beside the old river crossing." },
    ],
    eventId: 3,
    lastHour: 7,
  };
}

function migrateWorld(world: WorldState) {
  world.directive = world.directive ?? "balanced";
  world.directiveUntil = world.directiveUntil ?? 0;
  world.nextIncident = world.nextIncident ?? world.elapsed + 120;
  world.projects = Array.isArray(world.projects) ? world.projects : [];
  world.buildings = Array.isArray(world.buildings)
    ? world.buildings.map((building) => ({ ...building, level: building.level || 1, condition: building.condition ?? 100, progress: building.progress ?? 0 }))
    : createWorld().buildings;
  world.agents = Array.isArray(world.agents)
    ? world.agents.map((agent) => ({ ...agent, cargoAmount: agent.cargoAmount ?? 0, taskPhase: agent.taskPhase ?? "outbound", carrying: agent.carrying ?? "" }))
    : createWorld().agents;
  if ((world.layoutVersion ?? 0) < SETTLEMENT_LAYOUT_VERSION) {
    let shelterIndex = 0;
    world.buildings = world.buildings.map((building) => {
      const index = building.kind === "shelter" ? shelterIndex++ : 0;
      return { ...building, ...settlementLocation(building.kind, index) };
    });
    let pendingShelterIndex = shelterIndex;
    world.projects = world.projects.map((project) => ({
      ...project,
      ...settlementLocation(project.kind, project.kind === "shelter" ? pendingShelterIndex++ : 0),
    }));
    const activeProject = world.projects[0];
    if (activeProject) {
      world.agents.forEach((agent) => {
        if (agent.action !== "build_shelter") return;
        agent.targetX = activeProject.x;
        agent.targetY = activeProject.y;
      });
    }
    world.layoutVersion = SETTLEMENT_LAYOUT_VERSION;
  }
  return world;
}

function shelterCapacity(world: WorldState) {
  return world.buildings
    .filter((building) => building.kind === "shelter")
    .reduce((capacity, building) => capacity + 4 + Math.max(0, building.level - 1) * 2, 0);
}

function nextConstructionKind(world: WorldState): ConstructionKind | undefined {
  const alive = world.agents.filter((agent) => agent.alive).length;
  if (shelterCapacity(world) < alive) return "shelter";
  if (!world.buildings.some((building) => building.kind === "water")) return "water";
  if (!world.buildings.some((building) => building.kind === "clinic")) return "clinic";
  if (!world.buildings.some((building) => building.kind === "workshop")) return "workshop";
  return undefined;
}

function projectLocation(world: WorldState, kind: ConstructionKind) {
  const shelterIndex = world.buildings.filter((building) => building.kind === "shelter").length;
  return settlementLocation(kind, kind === "shelter" ? shelterIndex : 0);
}

function ensureConstructionProject(world: WorldState, agent: Agent) {
  const active = world.projects[0];
  if (active) return active;
  const kind = nextConstructionKind(world);
  if (!kind) return undefined;
  const cost = BUILDING_COSTS[kind];
  if (world.wood < cost.wood || world.stone < cost.stone) return undefined;
  const location = projectLocation(world, kind);
  world.wood -= cost.wood;
  world.stone -= cost.stone;
  const project: ConstructionProject = {
    id: `project-${kind}-${world.day}-${world.eventId + 1}`,
    kind,
    x: location.x,
    y: location.y,
    progress: 2,
    startedBy: agent.id,
  };
  world.projects.push(project);
  logEvent(world, `${agent.name} breaks ground on a ${BUILDING_NAMES[kind]}. Builders can now work the same site together.`, "neutral");
  return project;
}

function activeCount(world: WorldState, actions: ActionName[]) {
  return world.agents.filter((agent) => agent.alive && actions.includes(agent.action)).length;
}

function actionTeam(action: ActionName) {
  if (["gather_food", "farm", "eat"].includes(action)) return "food";
  if (["gather_water", "drink"].includes(action)) return "water";
  if (["gather_wood", "gather_stone", "build_shelter", "tend_fire"].includes(action)) return "build";
  if (["heal", "assist", "socialize", "gather_medicine"].includes(action)) return "care";
  if (["guard", "explore"].includes(action)) return "watch";
  return "recovery";
}

function roleTeam(role: Role) {
  if (["Forager", "Cook", "Farmer"].includes(role)) return "food";
  if (["Water Carrier"].includes(role)) return "water";
  if (["Builder", "Engineer"].includes(role)) return "build";
  if (["Medic", "Caretaker"].includes(role)) return "care";
  if (["Guard", "Scout"].includes(role)) return "watch";
  return "coordination";
}

function relationshipCohesion(world: WorldState) {
  const living = world.agents.filter((agent) => agent.alive);
  if (!living.length) return 0;
  let trust = 0;
  let connections = 0;
  for (const agent of living) {
    for (const other of living) {
      if (agent.id === other.id) continue;
      trust += agent.relationships[other.id] ?? 40;
      connections += 1;
    }
  }
  const averageTrust = connections ? trust / connections : 50;
  const averageMorale = living.reduce((sum, agent) => sum + agent.morale, 0) / living.length;
  return Math.round(clamp(averageTrust * 0.58 + averageMorale * 0.42));
}

function settlementAssessment(world: WorldState) {
  const living = world.agents.filter((agent) => agent.alive);
  const alive = living.length;
  const capacity = shelterCapacity(world);
  const farm = world.buildings.find((building) => building.kind === "farm");
  const project = world.projects[0];
  const structureProgress = (kind: ConstructionKind) => {
    if (world.buildings.some((building) => building.kind === kind)) return 100;
    return project?.kind === kind ? project.progress : 0;
  };
  const waterReserve = clamp((world.water / Math.max(1, alive * 3)) * 100);
  const foodReserve = clamp((world.food / Math.max(1, alive * 3)) * 100);
  const objectives: SettlementObjective[] = [
    {
      id: "shelter",
      label: "Shelter everyone",
      detail: `${Math.min(capacity, alive)} of ${alive} have protected beds`,
      progress: clamp((capacity / Math.max(1, alive)) * 100),
      complete: capacity >= alive,
    },
    {
      id: "water",
      label: "Secure clean water",
      detail: world.buildings.some((building) => building.kind === "water") ? "Water house online" : "Build a filtered water house",
      progress: clamp(structureProgress("water") * 0.72 + waterReserve * 0.28),
      complete: structureProgress("water") >= 100 && waterReserve >= 45,
    },
    {
      id: "food",
      label: "Grow a food system",
      detail: farm ? `Food plot level ${farm.level}` : "Establish and improve the first food plot",
      progress: clamp((farm ? Math.min(100, 42 + farm.level * 22 + (farm.progress ?? 0) * 0.14) : 0) + foodReserve * 0.22),
      complete: Boolean(farm && farm.level >= 2 && foodReserve >= 38),
    },
    {
      id: "care",
      label: "Open a field clinic",
      detail: `${Math.floor(world.medicine)} medicine in reserve`,
      progress: clamp(structureProgress("clinic") * 0.82 + clamp(world.medicine * 8) * 0.18),
      complete: structureProgress("clinic") >= 100 && world.medicine >= 5,
    },
    {
      id: "resilience",
      label: "Build long-term resilience",
      detail: "Workshop, health, and social trust",
      progress: clamp(structureProgress("workshop") * 0.72 + relationshipCohesion(world) * 0.18 + (living.reduce((sum, agent) => sum + agent.health, 0) / Math.max(1, alive)) * 0.1),
      complete: structureProgress("workshop") >= 100 && relationshipCohesion(world) >= 58,
    },
  ];
  const firstIncomplete = objectives.findIndex((objective) => !objective.complete);
  const phaseNumber = firstIncomplete < 0 ? objectives.length + 1 : firstIncomplete + 1;
  const phase = firstIncomplete < 0 ? "A resilient home" : objectives[firstIncomplete].label;
  const readiness = Math.round(objectives.reduce((sum, objective) => sum + objective.progress, 0) / objectives.length);
  const cohesion = relationshipCohesion(world);
  const assigned = (id: string) => living.filter((agent) => roleTeam(agent.role) === id || (id === "coordination" && agent.role === "Coordinator")).length;
  const working = (id: string) => living.filter((agent) => actionTeam(agent.action) === id).length;
  const teams: TeamSnapshot[] = [
    { id: "water", name: "River team", mission: world.water < alive * 3 ? "Restore the water margin" : "Keep reserves stable", members: assigned("water"), active: working("water") },
    { id: "food", name: "Food team", mission: farm?.level && farm.level >= 2 ? "Harvest and preserve" : "Establish reliable crops", members: assigned("food"), active: working("food") },
    { id: "build", name: "Build team", mission: project ? `Raise the ${BUILDING_NAMES[project.kind]}` : nextConstructionKind(world) ? "Prepare the next build" : "Maintain the settlement", members: assigned("build"), active: working("build") },
    { id: "care", name: "Care team", mission: living.some((agent) => agent.health < 65) ? "Stabilize the injured" : "Protect health and morale", members: assigned("care"), active: working("care") },
    { id: "watch", name: "Range team", mission: "Scout routes and hold the perimeter", members: assigned("watch"), active: working("watch") },
  ];
  let riskPoints = 0;
  if (world.water < alive * 1.25) riskPoints += 2;
  if (world.food < alive * 1.25) riskPoints += 2;
  if (capacity < alive) riskPoints += 1;
  if (world.fire < 18) riskPoints += 1;
  if (living.filter((agent) => agent.health < 55).length >= 2) riskPoints += 2;
  if (world.weather === "Storm" || world.weather === "Cold snap") riskPoints += 2;
  const risk = riskPoints >= 6 ? "CRITICAL" : riskPoints >= 4 ? "HIGH" : riskPoints >= 2 ? "GUARDED" : "LOW";
  return { objectives, phase, phaseNumber, readiness, cohesion, risk, teams } as const;
}

function chooseResource(world: WorldState, agent: Agent, kind: ResourceKind) {
  let best: ResourceNode | undefined;
  let bestDistance = Number.POSITIVE_INFINITY;
  for (const node of world.resources) {
    if (node.kind !== kind || node.amount <= 0) continue;
    const distance = Math.hypot(node.x - agent.x, node.y - agent.y);
    if (distance < bestDistance) {
      best = node;
      bestDistance = distance;
    }
  }
  return best;
}

function chooseWaterTarget(agent: Agent) {
  let best = { x: 9, y: CAMP_Y };
  let distance = Number.POSITIVE_INFINITY;
  for (let y = 2; y < WORLD_H - 2; y += 1) {
    for (let x = 2; x < WORLD_W - 2; x += 1) {
      if (terrainAt(x, y).kind !== "sand") continue;
      const adjacentWater = terrainAt(x + 1, y).kind === "water" || terrainAt(x - 1, y).kind === "water" ||
        terrainAt(x, y + 1).kind === "water" || terrainAt(x, y - 1).kind === "water";
      if (!adjacentWater) continue;
      const d = Math.hypot(x - agent.x, y - agent.y);
      if (d < distance) {
        distance = d;
        best = { x, y };
      }
    }
  }
  return best;
}

function randomLandNear(seed: number, x: number, y: number, radius = 8) {
  const random = mulberry32(seed);
  for (let i = 0; i < 40; i += 1) {
    const angle = random() * Math.PI * 2;
    const distance = 2 + random() * radius;
    const point = nearestLand(x + Math.cos(angle) * distance, y + Math.sin(angle) * distance);
    if (isLand(point.x, point.y)) return point;
  }
  return { x: CAMP_X, y: CAMP_Y };
}

function setAction(world: WorldState, agent: Agent, action: ActionName, targetId = "") {
  agent.action = action;
  agent.actionProgress = 0;
  agent.carrying = "";
  agent.cargoAmount = 0;
  agent.taskPhase = "outbound";
  const resourceFor: Partial<Record<ActionName, ResourceKind>> = {
    gather_food: "berries", gather_wood: "tree", gather_stone: "rock", gather_medicine: "herbs",
  };
  const resourceKind = resourceFor[action];
  if (resourceKind) {
    const explicit = targetId ? world.resources.find((node) => node.id === targetId && node.kind === resourceKind && node.amount > 0) : undefined;
    const node = explicit ?? chooseResource(world, agent, resourceKind);
    if (node) {
      agent.targetX = node.x;
      agent.targetY = node.y;
      return;
    }
  }
  if (action === "drink" || action === "gather_water") {
    const target = chooseWaterTarget(agent);
    agent.targetX = target.x;
    agent.targetY = target.y;
  } else if (["eat", "rest", "tend_fire", "socialize"].includes(action)) {
    const point = randomLandNear(agent.seed + Math.floor(world.elapsed), CAMP_X, CAMP_Y, 2.4);
    agent.targetX = point.x;
    agent.targetY = point.y;
  } else if (action === "build_shelter") {
    const project = ensureConstructionProject(world, agent);
    if (project) {
      agent.targetX = project.x;
      agent.targetY = project.y;
      agent.thought = `The ${BUILDING_NAMES[project.kind]} is our shared build. I can move it closer to completion.`;
    } else {
      const target = randomLandNear(agent.seed + Math.floor(world.elapsed), CAMP_X, CAMP_Y, 2.2);
      agent.targetX = target.x;
      agent.targetY = target.y;
      agent.thought = "The next build is designed, but the material stockpile is not ready yet.";
    }
  } else if (action === "farm") {
    const farm = world.buildings.find((building) => building.kind === "farm");
    if (farm) {
      agent.targetX = farm.x;
      agent.targetY = farm.y;
    } else {
      const target = nearestLand(CAMP_X - 4.5, CAMP_Y + 3.4);
      agent.targetX = target.x;
      agent.targetY = target.y;
    }
  } else if (action === "heal" || action === "assist") {
    const explicit = world.agents.find((other) => other.id === targetId && other.alive);
    const partner = explicit ?? [...world.agents]
      .filter((other) => other.alive && other.id !== agent.id)
      .sort((a, b) => (a.health + a.morale - a.thirst) - (b.health + b.morale - b.thirst))[0];
    if (partner) {
      agent.targetX = partner.x;
      agent.targetY = partner.y;
    }
  } else if (action === "guard") {
    const angle = ((agent.seed % 360) * Math.PI) / 180;
    const target = nearestLand(CAMP_X + Math.cos(angle) * 7, CAMP_Y + Math.sin(angle) * 7);
    agent.targetX = target.x;
    agent.targetY = target.y;
  } else {
    const point = randomLandNear(agent.seed + Math.floor(world.elapsed * 7), agent.x, agent.y, action === "explore" ? 11 : 4);
    agent.targetX = point.x;
    agent.targetY = point.y;
  }
}

function directiveDecision(world: WorldState, agent: Agent): { action: ActionName; thought: string } | undefined {
  if (world.directive === "balanced" || world.elapsed >= world.directiveUntil) return undefined;
  const alive = world.agents.filter((person) => person.alive).length;
  if (world.directive === "water" && activeCount(world, ["gather_water"]) < Math.min(8, Math.ceil(alive * 0.34))) {
    return { action: "gather_water" as ActionName, thought: "The council called for a stronger water margin. I am joining the river chain." };
  }
  if (world.directive === "food" && activeCount(world, ["gather_food", "farm"]) < Math.min(8, Math.ceil(alive * 0.36))) {
    const farmReady = world.buildings.some((building) => building.kind === "farm");
    const action: ActionName = agent.role === "Farmer" || (farmReady && agent.seed % 4 === 0) ? "farm" : "gather_food";
    return { action, thought: "The council wants food security, so I am reinforcing the harvest team." };
  }
  if (world.directive === "care" && activeCount(world, ["heal", "assist", "gather_medicine"]) < Math.min(6, Math.ceil(alive * 0.28))) {
    const patient = world.agents.some((person) => person.alive && person.health < 78);
    const action: ActionName = patient ? (world.medicine > 0 && (agent.role === "Medic" || agent.seed % 3 === 0) ? "heal" : "assist") : "gather_medicine";
    return { action, thought: "The council put people before output. I am strengthening the care rotation." };
  }
  if (world.directive === "watch" && activeCount(world, ["guard", "explore"]) < Math.min(7, Math.ceil(alive * 0.3))) {
    const night = world.minute < 6 * 60 || world.minute > 19 * 60;
    return { action: (night || agent.role === "Guard" ? "guard" : "explore") as ActionName, thought: "The council wants better warning and safer routes. I am joining the range team." };
  }
  if (world.directive === "build" && activeCount(world, ["build_shelter", "gather_wood", "gather_stone"]) < Math.min(8, Math.ceil(alive * 0.36))) {
    const project = world.projects[0];
    if (project) return { action: "build_shelter" as ActionName, thought: `The council is concentrating labor on the ${BUILDING_NAMES[project.kind]}. I am joining the crew.` };
    const kind = nextConstructionKind(world);
    if (kind) {
      const cost = BUILDING_COSTS[kind];
      const action: ActionName = world.wood < cost.wood ? "gather_wood" : world.stone < cost.stone ? "gather_stone" : "build_shelter";
      return { action, thought: `The council wants the ${BUILDING_NAMES[kind]} moving. I am clearing its next bottleneck.` };
    }
    return { action: world.wood < world.stone * 1.7 ? "gather_wood" : "gather_stone", thought: "The permanent buildings are standing. I am replenishing materials for repairs and expansion." };
  }
  return undefined;
}

function localDecision(world: WorldState, agent: Agent) {
  let action: ActionName;
  let thought: string;
  const alive = world.agents.filter((person) => person.alive).length;
  const project = world.projects[0];
  const desiredBuild = project?.kind ?? nextConstructionKind(world);
  const buildCost = desiredBuild ? BUILDING_COSTS[desiredBuild] : undefined;
  const careWorkers = activeCount(world, ["heal", "assist"]);
  const waterWorkers = activeCount(world, ["gather_water"]);
  const foodWorkers = activeCount(world, ["gather_food", "farm"]);
  const builders = activeCount(world, ["build_shelter"]);
  const watch = activeCount(world, ["guard"]);
  const injured = world.agents.filter((other) => other.alive && other.health < 62);
  const flexible = agent.role === "Coordinator" || agent.traits.includes("communal") || agent.traits.includes("protective");
  const isNight = world.minute < 6 * 60 || world.minute > 19 * 60;
  const directed = directiveDecision(world, agent);
  if (agent.health < 38) {
    action = "rest";
    thought = "I am no use to anyone if I collapse. I need to recover near the fire.";
  } else if (agent.thirst > 72) {
    action = world.water > 0 ? "drink" : "gather_water";
    thought = world.water > 0 ? "The shared water will keep me working." : "We need water immediately; I can make the river run.";
  } else if (agent.hunger > 75) {
    action = world.food > 0 ? "eat" : "gather_food";
    thought = world.food > 0 ? "One ration now will keep me useful." : "The stores are empty. I need to find something edible.";
  } else if (world.fire < 18 && world.wood >= 2) {
    action = "tend_fire";
    thought = "If the fire dies, tonight gets dangerous for everyone.";
  } else if (injured.length > 0 && careWorkers < Math.min(3, injured.length + 1) && ((["Medic", "Caretaker"] as Role[]).includes(agent.role) || flexible)) {
    action = agent.role === "Medic" || world.medicine > 0 ? "heal" : "assist";
    thought = `${injured[0].name} needs support. The care team is coordinating coverage now.`;
  } else if (directed) {
    action = directed.action;
    thought = directed.thought;
  } else if (world.water < alive * 2.2 && waterWorkers < Math.min(5, Math.ceil(alive / 6)) && (agent.role === "Water Carrier" || agent.role === "Caretaker" || flexible || world.water < alive)) {
    action = "gather_water";
    thought = `The river team has ${waterWorkers} carrier${waterWorkers === 1 ? "" : "s"} moving. I can close the water gap.`;
  } else if (world.food < alive * 2.2 && foodWorkers < Math.min(6, Math.ceil(alive / 5)) && ((["Forager", "Farmer", "Cook", "Scout"] as Role[]).includes(agent.role) || flexible || world.food < alive)) {
    action = agent.role === "Farmer" && world.wood >= 4 ? "farm" : "gather_food";
    thought = `The food team is below its reserve target. I can reinforce its ${foodWorkers} active workers.`;
  } else if (project && builders < 4 && ((["Builder", "Engineer"] as Role[]).includes(agent.role) || flexible)) {
    action = "build_shelter";
    thought = `The ${BUILDING_NAMES[project.kind]} is ${Math.round(project.progress)}% complete. The build team works faster together.`;
  } else if (desiredBuild && buildCost && world.wood < buildCost.wood && (["Builder", "Engineer", "Guard"] as Role[]).includes(agent.role)) {
    action = "gather_wood";
    thought = `The ${BUILDING_NAMES[desiredBuild]} needs ${buildCost.wood} timber. I am filling that exact bottleneck.`;
  } else if (desiredBuild && buildCost && world.stone < buildCost.stone && (["Builder", "Engineer", "Scout"] as Role[]).includes(agent.role)) {
    action = "gather_stone";
    thought = `The ${BUILDING_NAMES[desiredBuild]} needs ${buildCost.stone} stone. The build cannot start without it.`;
  } else if (desiredBuild && buildCost && world.wood >= buildCost.wood && world.stone >= buildCost.stone && builders < 3 && (["Builder", "Engineer", "Coordinator"] as Role[]).includes(agent.role)) {
    action = "build_shelter";
    thought = `Materials are ready. I am opening the ${BUILDING_NAMES[desiredBuild]} site for the whole build team.`;
  } else if ((!world.buildings.some((building) => building.kind === "farm") || (world.buildings.find((building) => building.kind === "farm")?.level ?? 0) < 2) && (["Farmer", "Forager"] as Role[]).includes(agent.role)) {
    action = "farm";
    thought = "Foraging buys days. Better soil and seed give us a future.";
  } else if (isNight && watch < 3 && (["Guard", "Scout", "Coordinator"] as Role[]).includes(agent.role)) {
    action = "guard";
    thought = `The night watch needs three people. I am taking position ${watch + 1}.`;
  } else if (world.wood < 26 && (["Builder", "Engineer", "Guard"] as Role[]).includes(agent.role)) {
    action = "gather_wood";
    thought = "Heat, repairs, and construction all draw from timber. I will keep the margin healthy.";
  } else if (world.stone < 18 && (["Builder", "Engineer"] as Role[]).includes(agent.role)) {
    action = "gather_stone";
    thought = "A stone reserve keeps the next project from stalling.";
  } else if (agent.fatigue > 74) {
    action = "rest";
    thought = "Pushing through this exhaustion would create another problem for the group.";
  } else if (agent.morale < 42) {
    action = "socialize";
    thought = "Survival is more than calories. I need a familiar voice for a minute.";
  } else {
    const roleAction: Record<Role, ActionName> = {
      Coordinator: "assist", Forager: "gather_food", Builder: desiredBuild && buildCost && world.wood >= buildCost.wood && world.stone >= buildCost.stone ? "build_shelter" : world.wood < 28 ? "gather_wood" : "gather_stone",
      Medic: "gather_medicine", "Water Carrier": "gather_water", Scout: "explore", Cook: world.food < 55 ? "gather_food" : "assist",
      Caretaker: "assist", Engineer: desiredBuild && buildCost && world.wood >= buildCost.wood && world.stone >= buildCost.stone ? "build_shelter" : world.wood < 30 ? "gather_wood" : "gather_stone", Guard: "guard", Farmer: "farm",
    };
    action = roleAction[agent.role];
    thought = `My best contribution right now is ${ACTION_LABELS[action].toLowerCase()}.`;
  }
  agent.brain = "local";
  agent.thought = thought;
  setAction(world, agent, action);
  agent.decisionDue = world.elapsed + 8 + (agent.seed % 8);
}

function completeAction(world: WorldState, agent: Agent) {
  const current = agent.action;
  const partners = world.agents.filter((other) =>
    other.alive &&
    other.id !== agent.id &&
    other.action === current &&
    other.taskPhase !== "returning" &&
    Math.hypot(other.x - agent.x, other.y - agent.y) < 3.4,
  );
  const teamMultiplier = 1 + Math.min(0.52, partners.length * 0.16);
  const buildBonds = (amount = 1.5) => {
    for (const partner of partners.slice(0, 3)) {
      agent.relationships[partner.id] = clamp((agent.relationships[partner.id] ?? 40) + amount);
      partner.relationships[agent.id] = clamp((partner.relationships[agent.id] ?? 40) + amount);
      agent.morale = clamp(agent.morale + amount * 0.35);
      partner.morale = clamp(partner.morale + amount * 0.2);
    }
  };

  if (CARRY_ACTIONS.includes(current)) {
    if (agent.taskPhase !== "returning") {
      const resourceFor: Partial<Record<ActionName, ResourceKind>> = {
        gather_food: "berries", gather_wood: "tree", gather_stone: "rock", gather_medicine: "herbs",
      };
      const kind = resourceFor[current];
      const node = kind ? chooseResource(world, agent, kind) : undefined;
      if (node && Math.hypot(node.x - agent.x, node.y - agent.y) < 2.6) node.amount = Math.max(0, node.amount - 1);
      const baseGain = current === "gather_food" ? (node ? 4 : 2) : current === "gather_water" ? (world.buildings.some((building) => building.kind === "water") ? 11 : 8) : current === "gather_wood" ? 6 : current === "gather_stone" ? 4 : 1;
      agent.cargoAmount = Math.max(1, Math.round(baseGain * teamMultiplier));
      agent.carrying = current === "gather_food" ? "food" : current === "gather_water" ? "water" : current === "gather_wood" ? "timber" : current === "gather_stone" ? "stone" : "medicine";
      agent.taskPhase = "returning";
      agent.actionProgress = 0;
      const drop = randomLandNear(agent.seed + Math.floor(world.elapsed * 3), CAMP_X, CAMP_Y, 2.1);
      agent.targetX = drop.x;
      agent.targetY = drop.y;
      agent.thought = `I have ${agent.cargoAmount} ${agent.carrying}. Now it only counts if I get it back to the shared store.`;
      buildBonds();
      return;
    }
    if (current === "gather_food") world.food += agent.cargoAmount;
    else if (current === "gather_water") world.water += agent.cargoAmount;
    else if (current === "gather_wood") world.wood += agent.cargoAmount;
    else if (current === "gather_stone") world.stone += agent.cargoAmount;
    else world.medicine += agent.cargoAmount;
    if (current === "gather_food" || current === "gather_medicine") agent.morale = clamp(agent.morale + 1.2);
  } else if (current === "drink") {
    if (world.water > 0) world.water = Math.max(0, world.water - 1);
    agent.thirst = clamp(agent.thirst - 54);
  } else if (current === "eat") {
    if (world.food > 0) {
      world.food = Math.max(0, world.food - 1);
      agent.hunger = clamp(agent.hunger - 52);
      agent.morale = clamp(agent.morale + 2);
    }
  } else if (current === "rest") {
    agent.fatigue = clamp(agent.fatigue - 38);
    agent.health = clamp(agent.health + 5);
    agent.cold = clamp(agent.cold - 12);
  } else if (current === "tend_fire" && world.wood >= 2) {
    world.wood -= 2;
    world.fire = clamp(world.fire + 30);
    if (world.fire > 35) logEvent(world, `${agent.name} feeds the central fire enough to carry the camp through the next watch.`, "good");
  } else if (current === "build_shelter") {
    const project = world.projects.find((candidate) => Math.hypot(candidate.x - agent.x, candidate.y - agent.y) < 3.2) ?? world.projects[0];
    if (project) {
      project.progress = clamp(project.progress + 24 * teamMultiplier);
      buildBonds(2.2);
      if (project.progress >= 100) {
        world.buildings.push({ id: `${project.kind}-${world.buildings.length + 1}`, kind: project.kind, x: project.x, y: project.y, level: 1, condition: 100, progress: 0 });
        world.projects = world.projects.filter((candidate) => candidate.id !== project.id);
        const crew = [agent, ...partners].slice(0, 4).map((person) => person.name).join(", ");
        logEvent(world, `${crew} complete the ${BUILDING_NAMES[project.kind]}. A coordinated crew turned shared materials into permanent capacity.`, "good");
        agent.speech = `The ${BUILDING_NAMES[project.kind]} is ready. Good work, everyone.`;
      } else {
        agent.speech = project.progress > 70 ? "Roof team, stay with me. We are almost weather-tight." : "Materials are staged. Keep the crew on this section.";
      }
      agent.speechUntil = world.elapsed + 8;
    }
  } else if (current === "farm") {
    let farm = world.buildings.find((building) => building.kind === "farm");
    if (!farm && world.wood >= 4) {
      world.wood -= 4;
      farm = { id: "farm-main", kind: "farm", x: agent.targetX, y: agent.targetY, level: 1, progress: 12, condition: 100 };
      world.buildings.push(farm);
      logEvent(world, `${agent.name} marks out the settlement's first food plot.`, "good");
    } else if (farm) {
      world.food += Math.round((4 + farm.level * 2) * teamMultiplier);
      farm.progress = (farm.progress ?? 0) + 22 * teamMultiplier;
      buildBonds(1.8);
      if (farm.progress >= 100 && farm.level < 3 && world.wood >= 4 + farm.level * 2) {
        world.wood -= 4 + farm.level * 2;
        farm.level += 1;
        farm.progress = 0;
        logEvent(world, `${agent.name}'s food team improves the plots to level ${farm.level}. Each harvest now feeds more people.`, "good");
      } else if (farm.progress >= 100) {
        farm.progress = farm.level >= 3 ? 100 : 88;
      }
    }
  } else if (current === "heal") {
    const patient = [...world.agents].filter((other) => other.alive && other.id !== agent.id).sort((a, b) => a.health - b.health)[0];
    if (patient) {
      const boost = (world.medicine > 0 ? 18 : 7) * teamMultiplier;
      if (world.medicine > 0) world.medicine -= 1;
      patient.health = clamp(patient.health + boost);
      patient.morale = clamp(patient.morale + 7);
      patient.relationships[agent.id] = clamp((patient.relationships[agent.id] ?? 40) + 4);
      agent.relationships[patient.id] = clamp((agent.relationships[patient.id] ?? 40) + 4);
      logEvent(world, `${agent.name} treats ${patient.name}, restoring them to the work rotation.`, "good");
      buildBonds(2);
    }
  } else if (current === "assist") {
    const partner = [...world.agents].filter((other) => other.alive && other.id !== agent.id).sort((a, b) => a.morale - b.morale)[0];
    if (partner) {
      partner.morale = clamp(partner.morale + 8);
      partner.fatigue = clamp(partner.fatigue - 4);
      agent.morale = clamp(agent.morale + 3);
      agent.relationships[partner.id] = clamp((agent.relationships[partner.id] ?? 40) + 3);
      partner.relationships[agent.id] = clamp((partner.relationships[agent.id] ?? 40) + 4);
    }
  } else if (current === "socialize") {
    const nearby = world.agents.filter((other) => other.alive && other.id !== agent.id && Math.hypot(other.x - agent.x, other.y - agent.y) < 4);
    agent.morale = clamp(agent.morale + 11);
    nearby.slice(0, 3).forEach((other) => {
      other.morale = clamp(other.morale + 3);
      agent.relationships[other.id] = clamp((agent.relationships[other.id] ?? 40) + 2);
    });
  } else if (current === "guard") {
    agent.morale = clamp(agent.morale + 1);
  } else if (current === "explore" && (agent.seed + Math.floor(world.elapsed)) % 5 === 0) {
    world.food += 2;
    agent.speech = "Found a patch worth returning to.";
    agent.speechUntil = world.elapsed + 7;
  }
  agent.action = "idle";
  agent.actionProgress = 0;
  agent.carrying = "";
  agent.cargoAmount = 0;
  agent.taskPhase = "outbound";
  agent.decisionDue = world.elapsed + 2 + (agent.seed % 4);
}

function recalculatePriority(world: WorldState) {
  const alive = world.agents.filter((agent) => agent.alive).length;
  const shelters = shelterCapacity(world);
  const injured = world.agents.filter((agent) => agent.alive && agent.health < 55).length;
  const project = world.projects[0];
  const desired = nextConstructionKind(world);
  const secured = alive > 0 && settlementAssessment(world).objectives.every((objective) => objective.complete);
  let next = "Grow reserves, deepen trust, and prepare for the next season";
  if (alive === 0) next = "Settlement lost — no survivors remain";
  else if (secured) next = "Eden-7 is a resilient home — protect what the survivors built";
  else if (world.water < alive * 1.35) next = "Water first — every able carrier to the river";
  else if (world.food < alive * 1.25) next = "Find and grow food before supplies run out";
  else if (world.fire < 20 && (world.weather === "Cold snap" || world.minute > 18 * 60 || world.minute < 6 * 60)) next = "Protect the fire through the cold hours";
  else if (injured >= 2) next = "Stabilize the injured and cover their essential work";
  else if (world.directive !== "balanced" && world.elapsed < world.directiveUntil) next = `Council directive: ${DIRECTIVE_LABELS[world.directive]}`;
  else if (project) next = `Finish the ${BUILDING_NAMES[project.kind]} as one coordinated crew`;
  else if (shelters < alive) next = "Build enough shelter before the next hard night";
  else if (desired) next = `Gather materials and raise the next ${BUILDING_NAMES[desired]}`;
  else if ((world.buildings.find((building) => building.kind === "farm")?.level ?? 0) < 2) next = "Turn the first food plot into a reliable harvest";
  else if (world.wood < 20) next = "Rebuild timber reserves for heat and construction";
  if (next !== world.priority) {
    world.priority = next;
    logEvent(world, `Council priority: ${next}.`, "neutral");
  }
}

function runHourlyWorld(world: WorldState) {
  const hour = Math.floor(world.minute / 60);
  if (hour === world.lastHour) return;
  world.lastHour = hour;
  const waterHouse = world.buildings.find((building) => building.kind === "water");
  const farm = world.buildings.find((building) => building.kind === "farm");
  const clinic = world.buildings.find((building) => building.kind === "clinic");
  if (waterHouse) world.water += 1.8 + waterHouse.level * 0.8;
  if (farm && hour >= 7 && hour <= 18) world.food += farm.level * 0.45;
  if (clinic && world.medicine > 0) {
    const patient = [...world.agents].filter((agent) => agent.alive && agent.health < 88).sort((a, b) => a.health - b.health)[0];
    if (patient) patient.health = clamp(patient.health + 1.4 + clinic.level * 0.5);
  }
  recalculatePriority(world);
  if (hour === 6) logEvent(world, `Day ${world.day}: the settlement wakes and divides the morning work.`, "neutral");
  if (hour === 20) logEvent(world, "Night watch begins. The fire and shelter are now critical.", "warning");
  if (world.elapsed > world.weatherUntil) {
    const roll = ((world.day * 17 + hour * 31) % 100) / 100;
    world.weather = roll < 0.12 ? "Storm" : roll < 0.26 ? "Rain" : roll > 0.91 ? "Cold snap" : roll > 0.82 ? "Heat" : "Clear";
    world.weatherUntil = world.elapsed + 90 + ((world.day * 29 + hour * 7) % 90);
    if (world.weather !== "Clear") logEvent(world, `${world.weather} moves across the valley. Work plans begin to shift.`, "warning");
  }
}

function runWorldIncident(world: WorldState) {
  if (world.elapsed < world.nextIncident) return;
  const living = world.agents.filter((agent) => agent.alive);
  if (!living.length) return;
  const guards = activeCount(world, ["guard"]);
  const scouts = activeCount(world, ["explore"]);
  const carers = activeCount(world, ["heal", "assist"]);
  const roll = (world.day * 29 + world.eventId * 17 + Math.floor(world.elapsed / 30)) % 5;
  if (roll === 0) {
    if (guards >= 2) {
      world.food += 3;
      logEvent(world, "The watch spots boar tracks before they reach the stores and turns the animals away. The prepared team even recovers usable food.", "good");
    } else {
      world.food = Math.max(0, world.food - 7);
      living.forEach((agent) => { agent.morale = clamp(agent.morale - 1.8); });
      logEvent(world, "Wild boars break into the edge of camp before the watch can respond. Food is lost and the settlement feels exposed.", "warning");
    }
  } else if (roll === 1) {
    if (world.buildings.some((building) => building.kind === "water")) {
      world.water += 5;
      logEvent(world, "Heavy silt reaches the river, but the water house filters it. The protected reserve grows instead of collapsing.", "good");
    } else {
      world.water = Math.max(0, world.water * 0.68);
      logEvent(world, "A wall of river silt contaminates the open water containers. The camp urgently needs a protected water system.", "warning");
    }
  } else if (roll === 2) {
    if (scouts >= 2) {
      world.medicine += 3;
      world.food += 5;
      logEvent(world, "Two scouts compare routes and locate an abandoned emergency cache: medicine and sealed food return to the shared store.", "good");
    } else {
      logEvent(world, "Smoke is seen beyond the ridge, but the range team is too thin to investigate safely. The opportunity passes.", "neutral");
    }
  } else if (roll === 3) {
    const patient = [...living].sort((a, b) => a.health - b.health)[0];
    const clinic = world.buildings.some((building) => building.kind === "clinic");
    if (clinic && carers >= 1) {
      patient.health = clamp(patient.health + 7);
      logEvent(world, `A fever reaches ${patient.name}, but the clinic and care rotation contain it before the illness spreads.`, "good");
    } else {
      patient.health = clamp(patient.health - 14);
      patient.fatigue = clamp(patient.fatigue + 18);
      logEvent(world, `${patient.name} develops a dangerous fever. Without a staffed clinic, recovery will cost the settlement time and strength.`, "warning");
    }
  } else {
    const workshop = world.buildings.some((building) => building.kind === "workshop");
    if (workshop) {
      world.wood += 4;
      world.stone += 3;
      logEvent(world, "The makers' lodge salvages broken tools and construction offcuts into usable material. Nothing valuable is wasted.", "good");
    } else {
      world.wood = Math.max(0, world.wood - 3);
      logEvent(world, "Several essential tools fail during the workday. Without a workshop, good timber is consumed by improvised repairs.", "warning");
    }
  }
  world.nextIncident = world.elapsed + 250 + ((world.day * 43 + world.eventId * 23) % 170);
  recalculatePriority(world);
}

function tickWorld(world: WorldState, dt: number, speed: number) {
  const scaled = dt * speed;
  world.elapsed += scaled;
  if (world.directive !== "balanced" && world.elapsed >= world.directiveUntil) {
    world.directive = "balanced";
    world.directiveUntil = 0;
    logEvent(world, "The focused council directive ends. Teams return to the balanced survival plan.", "neutral");
    recalculatePriority(world);
  }
  world.minute += scaled * 2.05;
  if (world.minute >= 1440) {
    world.minute -= 1440;
    world.day += 1;
  }
  runWorldIncident(world);
  runHourlyWorld(world);
  const night = world.minute < 6 * 60 || world.minute > 20 * 60;
  const harshCold = world.weather === "Cold snap" || (world.weather === "Storm" && night);
  world.fire = clamp(world.fire - scaled * (harshCold ? 0.04 : 0.022));
  for (const agent of world.agents) {
    if (!agent.alive) continue;
    agent.hunger = clamp(agent.hunger + scaled * 0.042);
    agent.thirst = clamp(agent.thirst + scaled * (world.weather === "Heat" ? 0.092 : 0.065));
    agent.fatigue = clamp(agent.fatigue + scaled * (agent.action === "rest" ? -0.25 : 0.036));
    agent.cold = clamp(agent.cold + scaled * (harshCold ? (world.fire < 20 ? 0.13 : 0.055) : -0.05));
    const distress = Math.max(agent.hunger - 82, 0) + Math.max(agent.thirst - 78, 0) * 1.4 + Math.max(agent.cold - 76, 0);
    if (distress > 0) agent.health = clamp(agent.health - scaled * distress * 0.0025);
    else if (agent.hunger < 60 && agent.thirst < 60 && agent.fatigue < 65) agent.health = clamp(agent.health + scaled * 0.008);
    if (agent.health <= 0) {
      agent.alive = false;
      logEvent(world, `${agent.name} has died. The settlement stops to absorb the loss.`, "warning");
      world.agents.forEach((other) => {
        if (other.alive) other.morale = clamp(other.morale - Math.max(3, (other.relationships[agent.id] ?? 40) / 12));
      });
      continue;
    }
    if (agent.action === "idle" && agent.brain !== "waiting" && world.elapsed >= agent.decisionDue) localDecision(world, agent);
    const dx = agent.targetX - agent.x;
    const dy = agent.targetY - agent.y;
    const distance = Math.hypot(dx, dy);
    if (distance > 0.28) {
      const travel = Math.min(distance, scaled * (agent.fatigue > 80 ? 0.32 : 0.56));
      const nextX = agent.x + (dx / distance) * travel;
      const nextY = agent.y + (dy / distance) * travel;
      if (isLand(nextX, nextY)) {
        agent.x = nextX;
        agent.y = nextY;
      } else {
        const safe = nearestLand(nextX, nextY);
        agent.x = safe.x;
        agent.y = safe.y;
      }
    } else if (agent.action !== "idle") {
      if (agent.taskPhase === "returning" && CARRY_ACTIONS.includes(agent.action)) {
        completeAction(world, agent);
      } else {
        agent.taskPhase = "working";
        agent.actionProgress += scaled;
        const duration = agent.action === "build_shelter" ? 8.5 : ["rest", "socialize", "farm"].includes(agent.action) ? 7 : 4.2;
        if (agent.actionProgress >= duration) completeAction(world, agent);
      }
    }
  }
}

function makeSnapshot(world: WorldState): Snapshot {
  const living = world.agents.filter((agent) => agent.alive);
  const assessment = settlementAssessment(world);
  return {
    day: world.day,
    time: formatTime(world.minute),
    weather: world.weather,
    priority: world.priority,
    food: Math.floor(world.food),
    water: Math.floor(world.water),
    wood: Math.floor(world.wood),
    stone: Math.floor(world.stone),
    medicine: Math.floor(world.medicine),
    fire: Math.floor(world.fire),
    directive: world.directive,
    directiveRemaining: Math.max(0, Math.ceil(world.directiveUntil - world.elapsed)),
    alive: living.length,
    total: world.agents.length,
    shelter: shelterCapacity(world),
    averageHealth: living.length ? Math.round(living.reduce((sum, agent) => sum + agent.health, 0) / living.length) : 0,
    readiness: assessment.readiness,
    cohesion: assessment.cohesion,
    risk: assessment.risk,
    phase: assessment.phase,
    phaseNumber: assessment.phaseNumber,
    objectives: assessment.objectives,
    teams: assessment.teams,
    projects: world.projects.map((project) => ({ ...project })),
    events: world.events.slice(0, 12),
    agents: [...world.agents],
  };
}

function metricTone(value: number) {
  return value > 65 ? "good" : value > 35 ? "warn" : "danger";
}

function needTone(value: number) {
  return value > 75 ? "danger" : value > 52 ? "warn" : "good";
}

function Meter({ label, value, reverse = false }: { label: string; value: number; reverse?: boolean }) {
  const tone = reverse ? needTone(value) : metricTone(value);
  const display = reverse ? 100 - value : value;
  return (
    <div className="meter-row">
      <div className="meter-label"><span>{label}</span><b>{Math.round(display)}</b></div>
      <div className="meter-track"><span className={`meter-fill ${tone}`} style={{ width: `${clamp(display)}%` }} /></div>
    </div>
  );
}

function ResourcePill({ icon, value, label, warning }: { icon: React.ReactNode; value: number; label: string; warning?: boolean }) {
  return <div className={`resource-pill ${warning ? "low" : ""}`} title={label}>{icon}<strong>{value}</strong><span>{label}</span></div>;
}

export default function HomePage() {
  const [initialWorld] = useState(createWorld);
  const worldRef = useRef<WorldState>(initialWorld);
  const [snapshot, setSnapshot] = useState<Snapshot>(() => makeSnapshot(initialWorld));
  const [selectedId, setSelectedId] = useState("human-1");
  const [paused, setPaused] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [panel, setPanel] = useState<"person" | "plan" | "people" | "log">("person");
  const [inspectorCollapsed, setInspectorCollapsed] = useState(true);
  const [commandsExpanded, setCommandsExpanded] = useState(false);
  const [astraStatus, setAstraStatus] = useState<AstraStatus>({ configured: false, model: "gpt-6-astra" });
  const [astraEnabled, setAstraEnabled] = useState(true);
  const astraEnabledRef = useRef(true);
  const astraInFlight = useRef(false);
  const lastAstraCall = useRef(0);

  useEffect(() => { astraEnabledRef.current = astraEnabled; }, [astraEnabled]);

  useEffect(() => {
    if (!window.__EDEN_QA_ENABLED__) return;
    window.__EDEN_SIM_QA__ = {
      advance(seconds) {
        if (!Number.isFinite(seconds) || seconds < 0 || seconds > 300) throw new Error("Invalid simulation capture interval");
        for (let step = 0; step < Math.floor(seconds * 60); step++) tickWorld(worldRef.current, 1 / 60, 1);
        setSnapshot(makeSnapshot(worldRef.current));
        return {
          elapsed: worldRef.current.elapsed,
          buildings: worldRef.current.buildings,
          projects: worldRef.current.projects,
          agents: worldRef.current.agents.map(({ id, action, carrying, taskPhase, x, y }) => ({ id, action, carrying, taskPhase, x, y })),
          events: worldRef.current.events.slice(0, 15),
        };
      },
    };
    return () => { delete window.__EDEN_SIM_QA__; };
  }, []);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem("eden-7-world-v2") ?? window.localStorage.getItem("eden-7-world-v1");
      if (saved) {
        const parsed = JSON.parse(saved) as { version?: number; world?: WorldState };
        if ((parsed.version === 1 || parsed.version === 2) && parsed.world && Array.isArray(parsed.world.agents) && parsed.world.agents.length > 0) {
          const restored = migrateWorld(parsed.world);
          worldRef.current = restored;
          window.queueMicrotask(() => {
            setSnapshot(makeSnapshot(restored));
            setSelectedId(restored.agents.find((agent) => agent.alive)?.id ?? restored.agents[0].id);
          });
        }
      }
    } catch {
      window.localStorage.removeItem("eden-7-world-v2");
      window.localStorage.removeItem("eden-7-world-v1");
    }
    const saveTimer = window.setInterval(() => {
      try {
        window.localStorage.setItem("eden-7-world-v2", JSON.stringify({ version: 2, world: worldRef.current }));
      } catch {
        // The simulation keeps running if private browsing blocks local storage.
      }
    }, 10_000);
    return () => window.clearInterval(saveTimer);
  }, []);

  useEffect(() => {
    let active = true;
    fetch("/api/astra/status")
      .then((response) => response.json())
      .then((data: AstraStatus) => { if (active) setAstraStatus({ configured: Boolean(data.configured), model: data.model || "gpt-6-astra" }); })
      .catch(() => undefined);
    return () => { active = false; };
  }, []);

  const requestAstraDecision = useCallback(async () => {
    if (!astraStatus.configured || !astraEnabledRef.current || astraInFlight.current || paused) return;
    const now = performance.now();
    if (now - lastAstraCall.current < 7000) return;
    const world = worldRef.current;
    const agent = world.agents
      .filter((person) => person.alive && person.brain !== "waiting" && person.action === "idle" && world.elapsed >= person.decisionDue)
      .sort((a, b) => a.decisionDue - b.decisionDue)[0];
    if (!agent) return;
    astraInFlight.current = true;
    lastAstraCall.current = now;
    agent.brain = "waiting";
    const controller = new AbortController();
    const decisionTimeout = window.setTimeout(() => controller.abort(), 12_000);
    const assessment = settlementAssessment(world);
    const closest = world.agents
      .filter((other) => other.alive && other.id !== agent.id)
      .sort((a, b) => Math.hypot(a.x - agent.x, a.y - agent.y) - Math.hypot(b.x - agent.x, b.y - agent.y))
      .slice(0, 5)
      .map((other) => ({ id: other.id, name: other.name, role: other.role, action: other.action, team: actionTeam(other.action), health: Math.round(other.health), morale: Math.round(other.morale), trust: agent.relationships[other.id] ?? 40 }));
    const visibleResources = world.resources
      .filter((node) => node.amount > 0)
      .sort((a, b) => Math.hypot(a.x - agent.x, a.y - agent.y) - Math.hypot(b.x - agent.x, b.y - agent.y))
      .slice(0, 9)
      .map((node) => ({ id: node.id, kind: node.kind, distance: Math.round(Math.hypot(node.x - agent.x, node.y - agent.y) * 10) / 10, amount: node.amount }));
    try {
      const response = await fetch("/api/astra/decide", {
        method: "POST",
        headers: { "content-type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          agent: {
            id: agent.id, name: agent.name, age: agent.age, role: agent.role, traits: agent.traits,
            health: Math.round(agent.health), hunger: Math.round(agent.hunger), thirst: Math.round(agent.thirst),
            fatigue: Math.round(agent.fatigue), cold: Math.round(agent.cold), morale: Math.round(agent.morale),
            memories: agent.memories.slice(-6),
          },
          world: {
            day: world.day, time: formatTime(world.minute), weather: world.weather, shared_priority: world.priority,
            stores: { food: Math.floor(world.food), water: Math.floor(world.water), wood: Math.floor(world.wood), stone: Math.floor(world.stone), medicine: Math.floor(world.medicine), fire: Math.floor(world.fire) },
            shelter_capacity: shelterCapacity(world),
            population: world.agents.filter((person) => person.alive).length,
            recent_events: world.events.slice(0, 5).map((event) => event.text),
            settlement_phase: assessment.phase,
            settlement_readiness: assessment.readiness,
            cohesion: assessment.cohesion,
            risk: assessment.risk,
            council_directive: world.directive === "balanced" ? null : DIRECTIVE_LABELS[world.directive],
            directive_seconds_remaining: Math.max(0, Math.ceil(world.directiveUntil - world.elapsed)),
            objectives: assessment.objectives.map((objective) => ({ label: objective.label, progress: Math.round(objective.progress), complete: objective.complete })),
            active_project: world.projects[0] ? { kind: world.projects[0].kind, progress: Math.round(world.projects[0].progress) } : null,
          },
          team_assignment: { natural_team: roleTeam(agent.role), current_team: actionTeam(agent.action) },
          nearby_people: closest,
          visible_resources: visibleResources,
          allowed_actions: ALLOWED_ACTIONS,
        }),
      });
      if (!response.ok) throw new Error("Astra request unavailable");
      const decision = (await response.json()) as AstraDecision;
      if (!ALLOWED_ACTIONS.includes(decision.action)) throw new Error("Invalid decision");
      if (!agent.alive || agent.brain !== "waiting" || agent.action !== "idle") return;
      agent.brain = "astra";
      agent.thought = decision.thought;
      agent.speech = decision.speech;
      agent.speechUntil = world.elapsed + (decision.speech ? 10 : 0);
      if (decision.memory) agent.memories = [...agent.memories, decision.memory].slice(-10);
      setAction(world, agent, decision.action, decision.target_id);
      agent.decisionDue = world.elapsed + 20 + decision.priority * 3;
      if (decision.speech) logEvent(world, `${agent.name}: “${decision.speech}”`, "astra");
    } catch {
      if (agent.alive) localDecision(world, agent);
    } finally {
      window.clearTimeout(decisionTimeout);
      astraInFlight.current = false;
    }
  }, [astraStatus.configured, paused]);

  useEffect(() => {
    let frame = 0;
    let previous = performance.now();
    let uiAccumulator = 0;
    let astraAccumulator = 0;
    const animate = (now: number) => {
      const dt = Math.min(0.06, (now - previous) / 1000);
      previous = now;
      if (!paused) {
        tickWorld(worldRef.current, dt, speed);
        uiAccumulator += dt;
        astraAccumulator += dt;
        if (astraAccumulator > 1.5) {
          astraAccumulator = 0;
          void requestAstraDecision();
        }
        if (uiAccumulator > 0.45) {
          uiAccumulator = 0;
          setSnapshot(makeSnapshot(worldRef.current));
        }
      }
      frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [paused, requestAstraDecision, speed]);

  const selected = snapshot.agents.find((agent) => agent.id === selectedId) ?? snapshot.agents[0];
  const closestFriend = useMemo(() => {
    if (!selected) return undefined;
    return snapshot.agents.filter((agent) => agent.alive && agent.id !== selected.id)
      .sort((a, b) => (selected.relationships[b.id] ?? 0) - (selected.relationships[a.id] ?? 0))[0];
  }, [selected, snapshot.agents]);

  const addSurvivor = () => {
    const world = worldRef.current;
    const index = world.agents.length;
    const agent = createAgent(index, index + 1);
    for (const other of world.agents) {
      agent.relationships[other.id] = 38;
      // The simulation intentionally owns mutable agent state outside React rendering.
      // eslint-disable-next-line react-hooks/immutability
      other.relationships[agent.id] = 38;
    }
    world.agents.push(agent);
    logEvent(world, `${agent.name}, a ${agent.role.toLowerCase()}, follows the river smoke into camp and asks to join.`, "good");
    setSelectedId(agent.id);
    setSnapshot(makeSnapshot(world));
  };

  const issueDirective = (directive: Directive) => {
    const world = worldRef.current;
    world.directive = directive;
    world.directiveUntil = directive === "balanced" ? 0 : world.elapsed + 180;
    logEvent(world, directive === "balanced" ? "The council returns labor to the balanced survival plan." : `Council directive: ${DIRECTIVE_LABELS[directive]}. Available survivors reorganize without abandoning urgent personal needs.`, "neutral");
    recalculatePriority(world);
    world.agents.forEach((agent) => {
      if (agent.alive && agent.action === "idle") agent.decisionDue = Math.min(agent.decisionDue, world.elapsed + (agent.seed % 4) * 0.25);
    });
    setCommandsExpanded(false);
    setSnapshot(makeSnapshot(world));
  };

  const injectCrisis = (kind: "storm" | "cold" | "injury" | "blight") => {
    const world = worldRef.current;
    if (kind === "storm") {
      world.weather = "Storm";
      world.weatherUntil = world.elapsed + 150;
      world.fire = clamp(world.fire - 18);
      logEvent(world, "A violent storm hits the valley. The river rises and the central fire gutters.", "warning");
    } else if (kind === "cold") {
      world.weather = "Cold snap";
      world.weatherUntil = world.elapsed + 190;
      logEvent(world, "The temperature falls without warning. Exposed survivors begin searching for heat.", "warning");
    } else if (kind === "blight") {
      world.food = Math.max(3, world.food * 0.38);
      world.resources.filter((resource) => resource.kind === "berries").forEach((resource) => (resource.amount = Math.max(0, resource.amount - 1)));
      logEvent(world, "A mold bloom ruins much of the shared food and several berry patches.", "warning");
    } else {
      const healthy = world.agents.filter((agent) => agent.alive).sort((a, b) => b.health - a.health)[0];
      if (healthy) {
        healthy.health = Math.max(24, healthy.health - 56);
        healthy.fatigue = clamp(healthy.fatigue + 24);
        healthy.memories.push("I was badly injured while working near camp.");
        logEvent(world, `${healthy.name} is badly injured in a falling-tree accident. The camp needs a medic.`, "warning");
      }
    }
    recalculatePriority(world);
    world.agents.forEach((agent) => { if (agent.alive) agent.decisionDue = Math.min(agent.decisionDue, world.elapsed + (agent.seed % 5)); });
    setSnapshot(makeSnapshot(world));
  };

  const startNewWorld = () => {
    const world = createWorld();
    worldRef.current = world;
    astraInFlight.current = false;
    lastAstraCall.current = 0;
    setPaused(false);
    setSpeed(1);
    setSelectedId("human-1");
    setPanel("person");
    setInspectorCollapsed(false);
    setCommandsExpanded(false);
    setSnapshot(makeSnapshot(world));
    try {
      window.localStorage.removeItem("eden-7-world-v2");
      window.localStorage.removeItem("eden-7-world-v1");
    } catch {
      // Reset still succeeds if local storage is unavailable.
    }
  };

  return (
    <main className="simulation-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true"><Sparkles size={18} /></div>
          <div><h1>ASTRA // EDEN-7</h1><p>Cooperative survival simulation</p></div>
        </div>
        <div className="world-clock" aria-label={`Day ${snapshot.day}, ${snapshot.time}, weather ${snapshot.weather}`}>
          <strong>DAY {String(snapshot.day).padStart(2, "0")}</strong>
          <span>{snapshot.time}</span>
          <span className={`weather ${snapshot.weather !== "Clear" ? "active" : ""}`}>
            {snapshot.weather === "Storm" ? <CloudLightning size={15} /> : snapshot.weather === "Clear" ? <Sparkles size={14} /> : <Wind size={15} />}{snapshot.weather}
          </span>
        </div>
        <div className="top-controls">
          <button className="icon-button" onClick={() => setPaused((value) => !value)} aria-label={paused ? "Resume simulation" : "Pause simulation"}>
            {paused ? <Play size={17} /> : <Pause size={17} />}
          </button>
          <div className="speed-control" aria-label="Simulation speed">
            {[1, 4, 12].map((option) => <button key={option} className={speed === option ? "active" : ""} onClick={() => setSpeed(option)}>{option}×</button>)}
          </div>
          <button
            className={`astra-toggle ${astraStatus.configured && astraEnabled ? "online" : ""}`}
            onClick={() => setAstraEnabled((value) => !value)}
            title={astraStatus.configured ? `Decisions use ${astraStatus.model}` : "The Astra bridge is ready; a server key is required for live model decisions"}
          >
            <BrainCircuit size={16} /><span>{astraStatus.configured && astraEnabled ? "ASTRA LIVE" : astraStatus.configured ? "ASTRA PAUSED" : "LOCAL BRAIN"}</span>
          </button>
        </div>
      </header>

      <section className="resource-strip" aria-label="Shared settlement stores">
        <ResourcePill icon={<Users size={16} />} value={snapshot.alive} label="alive" warning={snapshot.alive < snapshot.total} />
        <ResourcePill icon={<Utensils size={16} />} value={snapshot.food} label="food" warning={snapshot.food < snapshot.alive} />
        <ResourcePill icon={<Droplets size={16} />} value={snapshot.water} label="water" warning={snapshot.water < snapshot.alive} />
        <ResourcePill icon={<Trees size={16} />} value={snapshot.wood} label="wood" warning={snapshot.wood < 12} />
        <ResourcePill icon={<Crosshair size={16} />} value={snapshot.stone} label="stone" warning={snapshot.stone < 5} />
        <ResourcePill icon={<Stethoscope size={16} />} value={snapshot.medicine} label="medicine" warning={snapshot.medicine < 5} />
        <ResourcePill icon={<Home size={16} />} value={snapshot.shelter} label="sheltered" warning={snapshot.shelter < snapshot.alive} />
        <ResourcePill icon={<Flame size={16} />} value={snapshot.fire} label="fire" warning={snapshot.fire < 20} />
        <ResourcePill icon={<HeartPulse size={16} />} value={snapshot.averageHealth} label="avg health" warning={snapshot.averageHealth < 55} />
        <ResourcePill icon={<Handshake size={16} />} value={snapshot.cohesion} label="cohesion" warning={snapshot.cohesion < 45} />
      </section>

      <section className="world-stage">
        <WorldView worldRef={worldRef} selectedId={selectedId} onSelect={(id) => { setSelectedId(id); setPanel("person"); setInspectorCollapsed(false); }} paused={paused} speed={speed} />
        <div className="priority-card">
          <div className="priority-meta"><span>PHASE {Math.min(snapshot.phaseNumber, 5)} · {snapshot.phase}</span><b>{snapshot.readiness}% READY</b><i className={snapshot.risk.toLowerCase()}>{snapshot.risk} RISK</i></div>
          <strong>{snapshot.priority}</strong><small>All {snapshot.alive} minds share the plan, then independently choose how to help.</small>
        </div>
        <div className="camera-hint">Drag to orbit · Right-drag to move · Scroll to zoom · Select a person</div>
        <aside className={`command-deck ${commandsExpanded ? "expanded" : ""}`} aria-label="Issue a settlement directive">
          <div className="command-heading">
            <span>COUNCIL DIRECTIVE</span>
            <strong className="mobile-directive-name">{DIRECTIVE_LABELS[snapshot.directive]}</strong>
            <b>{snapshot.directive === "balanced" ? "AUTONOMOUS" : `${snapshot.directiveRemaining}s`}</b>
            <button
              className="mobile-command-toggle"
              aria-label={commandsExpanded ? "Collapse council directives" : "Open council directives"}
              aria-expanded={commandsExpanded}
              onClick={() => setCommandsExpanded((value) => !value)}
            >
              {commandsExpanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
            </button>
          </div>
          <p>{DIRECTIVE_LABELS[snapshot.directive]}</p>
          <div className="directive-grid">
            <button aria-label="Return to the balanced plan" aria-pressed={snapshot.directive === "balanced"} className={snapshot.directive === "balanced" ? "active" : ""} onClick={() => issueDirective("balanced")}><Sparkles size={15} /><span>Balance</span></button>
            <button aria-label="Secure the water supply" aria-pressed={snapshot.directive === "water"} className={snapshot.directive === "water" ? "active" : ""} onClick={() => issueDirective("water")}><Droplets size={15} /><span>Water</span></button>
            <button aria-label="Stock the food supply" aria-pressed={snapshot.directive === "food"} className={snapshot.directive === "food" ? "active" : ""} onClick={() => issueDirective("food")}><Utensils size={15} /><span>Food</span></button>
            <button aria-label="Accelerate construction" aria-pressed={snapshot.directive === "build"} className={snapshot.directive === "build" ? "active" : ""} onClick={() => issueDirective("build")}><Hammer size={15} /><span>Build</span></button>
            <button aria-label="Protect vulnerable survivors" aria-pressed={snapshot.directive === "care"} className={snapshot.directive === "care" ? "active" : ""} onClick={() => issueDirective("care")}><HeartPulse size={15} /><span>Care</span></button>
            <button aria-label="Scout and defend the settlement" aria-pressed={snapshot.directive === "watch"} className={snapshot.directive === "watch" ? "active" : ""} onClick={() => issueDirective("watch")}><ShieldAlert size={15} /><span>Watch</span></button>
          </div>
        </aside>

        <aside className={`inspector ${inspectorCollapsed ? "collapsed" : ""}`}>
          <div className="mobile-tabs" role="tablist" aria-label="Settlement panels">
            <button role="tab" aria-selected={panel === "person"} className={panel === "person" ? "active" : ""} onClick={() => { setPanel("person"); setInspectorCollapsed(false); }}>Person</button>
            <button role="tab" aria-selected={panel === "plan"} className={panel === "plan" ? "active" : ""} onClick={() => { setPanel("plan"); setInspectorCollapsed(false); }}>Plan</button>
            <button role="tab" aria-selected={panel === "people"} className={panel === "people" ? "active" : ""} onClick={() => { setPanel("people"); setInspectorCollapsed(false); }}>People</button>
            <button role="tab" aria-selected={panel === "log"} className={panel === "log" ? "active" : ""} onClick={() => { setPanel("log"); setInspectorCollapsed(false); }}>Log</button>
            <button className="inspector-collapse" onClick={() => setInspectorCollapsed((value) => !value)} aria-label={inspectorCollapsed ? "Open settlement details" : "Collapse settlement details"}>
              {inspectorCollapsed ? <ChevronUp size={17} /> : <ChevronDown size={17} />}
            </button>
          </div>
          <div className={`panel-content person-panel ${panel !== "person" ? "mobile-hidden" : ""}`}>
            {selected ? <>
              <div className="person-heading">
                <div className={`agent-sigil ${selected.brain}`} style={{ "--agent-color": selected.color } as React.CSSProperties} aria-hidden="true">
                  <BrainCircuit size={20} /><span>{selected.name.slice(0, 1)}</span>
                </div>
                <div>
                  <div className="eyebrow">{selected.brain === "astra" ? "ASTRA DIRECTED" : selected.brain === "waiting" ? "ASTRA THINKING" : "LOCAL AUTONOMY"}</div>
                  <h2>{selected.name}</h2><p>{selected.role} · age {selected.age}</p>
                </div>
                <span className={`alive-badge ${selected.alive ? "" : "dead"}`}>{selected.alive ? "ALIVE" : "LOST"}</span>
              </div>
              <div className="trait-row">{selected.traits.map((trait) => <span key={trait}>{trait}</span>)}</div>
              <div className="current-action">
                <span className={`brain-orb ${selected.brain}`}><BrainCircuit size={17} /></span>
                <div><small>{selected.action === "idle" ? "AVAILABLE FOR ASSIGNMENT" : `${actionTeam(selected.action).toUpperCase()} TEAM · ${selected.taskPhase.toUpperCase()}`}</small><strong>{selected.carrying ? `Returning with ${selected.cargoAmount} ${selected.carrying}` : ACTION_LABELS[selected.action]}</strong></div>
              </div>
              <blockquote>“{selected.thought}”</blockquote>
              <div className="meters">
                <Meter label="Health" value={selected.health} /><Meter label="Morale" value={selected.morale} />
                <Meter label="Fed" value={selected.hunger} reverse /><Meter label="Hydrated" value={selected.thirst} reverse />
                <Meter label="Rested" value={selected.fatigue} reverse /><Meter label="Warm" value={selected.cold} reverse />
              </div>
              <div className="relationship-card"><small>STRONGEST BOND</small><div><span>{closestFriend?.name ?? "—"}</span><b>{closestFriend ? Math.round(selected.relationships[closestFriend.id] ?? 0) : 0}% trust</b></div></div>
              <div className="memory-card"><small>LATEST MEMORY</small><p>{selected.memories.at(-1)}</p></div>
            </> : null}
          </div>

          <div className={`panel-content plan-panel ${panel !== "plan" ? "mobile-hidden" : ""}`}>
            <div className="panel-title-row"><div><span>SETTLEMENT PLAN</span><strong>From survival to a permanent home</strong></div><Route size={18} /></div>
            <div className="readiness-card">
              <div><span>EDEN READINESS</span><strong>{snapshot.readiness}%</strong></div>
              <div className="readiness-track"><span style={{ width: `${snapshot.readiness}%` }} /></div>
              <p>Phase {Math.min(snapshot.phaseNumber, 5)} · {snapshot.phase}</p>
            </div>
            {snapshot.projects[0] ? (
              <div className="active-project">
                <div><Hammer size={17} /><span>ACTIVE BUILD</span><b>{Math.round(snapshot.projects[0].progress)}%</b></div>
                <strong>{BUILDING_NAMES[snapshot.projects[0].kind]}</strong>
                <div className="readiness-track"><span style={{ width: `${snapshot.projects[0].progress}%` }} /></div>
                <p>Every builder at the site adds a cooperation bonus.</p>
              </div>
            ) : null}
            <div className="objective-list">
              {snapshot.objectives.map((objective, index) => (
                <article key={objective.id} className={objective.complete ? "complete" : ""}>
                  <span>{objective.complete ? "✓" : String(index + 1).padStart(2, "0")}</span>
                  <div><strong>{objective.label}</strong><small>{objective.detail}</small><div className="objective-track"><i style={{ width: `${objective.progress}%` }} /></div></div>
                  <b>{Math.round(objective.progress)}%</b>
                </article>
              ))}
            </div>
            <div className="team-heading"><span>WORK TEAMS</span><b>{snapshot.cohesion}% cohesion</b></div>
            <div className="team-list">
              {snapshot.teams.map((team) => (
                <article key={team.id}>
                  <span className={`team-icon ${team.id}`}>{team.id === "water" ? <Waves size={15} /> : team.id === "food" ? <Sprout size={15} /> : team.id === "build" ? <Hammer size={15} /> : team.id === "care" ? <Stethoscope size={15} /> : <ShieldAlert size={15} />}</span>
                  <div><strong>{team.name}</strong><small>{team.mission}</small></div>
                  <b title={`${team.members} core team members`}>{team.active}<small> active</small></b>
                </article>
              ))}
            </div>
            <div className="scenario-tools">
              <div><span>PRESSURE TESTS</span><small>Optional survival events</small></div>
              <div>
                <button onClick={() => injectCrisis("storm")}><CloudLightning size={14} /> Storm</button>
                <button onClick={() => injectCrisis("cold")}><Wind size={14} /> Cold</button>
                <button onClick={() => injectCrisis("injury")}><ShieldAlert size={14} /> Injury</button>
                <button onClick={() => injectCrisis("blight")}><Activity size={14} /> Blight</button>
              </div>
            </div>
          </div>

          <div className={`panel-content people-panel ${panel !== "people" ? "mobile-hidden" : ""}`}>
            <div className="panel-title-row"><div><span>POPULATION</span><strong>{snapshot.alive} survivors</strong></div><button className="add-button" onClick={addSurvivor}><Plus size={14} /> Add survivor</button></div>
            <div className="people-list">
              {snapshot.agents.map((agent) => (
                <button key={agent.id} className={`${agent.id === selectedId ? "selected" : ""} ${!agent.alive ? "lost" : ""}`} onClick={() => { setSelectedId(agent.id); setPanel("person"); setInspectorCollapsed(false); }}>
                  <span className="mini-avatar" style={{ background: agent.color }}>{agent.name.slice(0, 1)}</span>
                  <span><strong>{agent.name}</strong><small>{agent.role} · {agent.carrying ? `carrying ${agent.carrying}` : ACTION_LABELS[agent.action]}</small></span>
                  <span className={`agent-state ${agent.brain}`} title={agent.brain === "astra" ? "Last decision by Astra" : agent.brain === "waiting" ? "Astra is deciding" : "Using local survival brain"} />
                  <b>{Math.round(agent.health)}%</b>
                </button>
              ))}
            </div>
          </div>

          <div className={`panel-content log-panel ${panel !== "log" ? "mobile-hidden" : ""}`}>
            <div className="panel-title-row"><div><span>SOCIETY MEMORY</span><strong>What the group has lived through</strong></div></div>
            <div className="event-list">
              {snapshot.events.map((event) => <article key={event.id} className={event.tone}><time>DAY {Math.floor(event.minute / 1440) + 1} · {formatTime(event.minute % 1440)}</time><p>{event.text}</p></article>)}
            </div>
          </div>
        </aside>
        {snapshot.alive === 0 ? (
          <div className="world-outcome" role="alertdialog" aria-labelledby="settlement-lost-title" aria-describedby="settlement-lost-description">
            <span><ShieldAlert size={18} /> SETTLEMENT LOST</span>
            <strong id="settlement-lost-title">Eden-7 went silent.</strong>
            <p id="settlement-lost-description">The next world starts clean, but the decisions that failed this one remain in the society log until you begin again.</p>
            <button onClick={startNewWorld}><Sparkles size={16} /> Begin a new world</button>
          </div>
        ) : null}
      </section>

      <footer className="bottom-status">
        <div><span className={`status-dot ${astraStatus.configured && astraEnabled ? "online" : ""}`} /><strong>{astraStatus.configured && astraEnabled ? astraStatus.model : "Autonomous fallback"}</strong><span>{astraStatus.configured && astraEnabled ? "One independent Astra identity per survivor" : "The world remains fully playable without a model connection"}</span></div>
        <div><Zap size={14} /><span>{snapshot.readiness}% settlement readiness · {snapshot.agents.filter((agent) => agent.brain === "astra").length} Astra decisions embodied</span></div>
      </footer>
    </main>
  );
}
