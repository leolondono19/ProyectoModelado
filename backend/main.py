from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random
import geopandas as gpd
from shapely.geometry import Point

app = FastAPI()

# Configuración CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar polígonos de tierra
land_gdf = gpd.read_file("data/ne_110m_land.shp")

def is_on_land(lat, lon):
    point = Point(lon, lat)
    return land_gdf.contains(point).any()

class SimulationParams(BaseModel):
    population_size: int
    infection_rate: float
    initial_infected: Optional[int] = 1

simulation_state = {
    "population": [],
    "tick": 0,
    "running": False,
    "infection_rate": 0.1,
}

def create_population(size):
    population = []
    attempts = 0
    while len(population) < size:
        lat = random.uniform(-90, 90)
        lon = random.uniform(-180, 180)
        if is_on_land(lat, lon):
            population.append({"id": len(population), "lat": lat, "lon": lon, "state": "S"})
        else:
            attempts += 1
            if attempts > size * 10:
                break
    return population

@app.post("/start")
def start_simulation(params: SimulationParams):
    global simulation_state
    simulation_state["population"] = create_population(params.population_size)
    simulation_state["tick"] = 0
    simulation_state["running"] = True
    simulation_state["infection_rate"] = params.infection_rate
    return {"message": "Simulación iniciada", "population": simulation_state["population"]}

@app.get("/status")
def get_status():
    return {
        "tick": simulation_state["tick"],
        "population": simulation_state["population"],
        "running": simulation_state["running"]
    }

@app.post("/tick")
def advance_tick():
    if not simulation_state["running"]:
        return {"message": "Simulación no iniciada"}

    pop = simulation_state["population"]
    new_pop = [p.copy() for p in pop]

    # Infectar aleatoriamente a una persona en el primer tick
    if simulation_state["tick"] == 0:
        candidate = random.choice(new_pop)
        candidate["state"] = "I"

    for i, person in enumerate(pop):
        if person["state"] == "I":
            for j, other in enumerate(pop):
                if other["state"] == "S":
                    dist = ((person["lat"] - other["lat"])**2 + (person["lon"] - other["lon"])**2)**0.5
                    if dist < 10 and random.random() < simulation_state["infection_rate"]:
                        new_pop[j]["state"] = "I"
            if random.random() < 0.05:
                new_pop[i]["state"] = "R"

    simulation_state["population"] = new_pop
    simulation_state["tick"] += 1
    simulation_state["running"] = any(p["state"] == "I" for p in new_pop)

    return {"tick": simulation_state["tick"], "population": simulation_state["population"], "running": simulation_state["running"]}

@app.get("/simulate/tick")
def get_simulation_data():
    return [
        {
            "id": p["id"],
            "lat": p["lat"],
            "lon": p["lon"],
            "state": "infected" if p["state"] == "I" else "susceptible" if p["state"] == "S" else "recovered"
        }
        for p in simulation_state["population"]
    ]
