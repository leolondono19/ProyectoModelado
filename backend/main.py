from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import random
import geopandas as gpd
from shapely.geometry import Point
import reverse_geocoder as rg
import os
import json
from collections import defaultdict

app = FastAPI()

# Configuración CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
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

def get_country(lat, lon):
    try:
        result = rg.search((lat, lon), mode=1)
        return result[0]['cc']
    except:
        return "Unknown"

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
            population.append({
                "id": len(population),
                "lat": lat,
                "lon": lon,
                "state": "S",
                "country": get_country(lat, lon)
            })
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

    return {
        "tick": simulation_state["tick"],
        "population": simulation_state["population"],
        "running": simulation_state["running"]
    }

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

# Cargar JSON countries_data solo 1 vez al iniciar la app para eficiencia
DATA_PATH = os.path.join("data", "countries_data.json")
with open(DATA_PATH, "r", encoding="utf-8") as f:
    countries_data = json.load(f)

@app.get("/report")
def get_country_report():
    report = defaultdict(lambda: {
        "infectados": 0,
        "muertes": 0,
        "vacunados": 0,
        "centros_medicos": 0,
        "incidencia": 0,
        "recuperados": 0,
        "graves": 0,
        "capacidad_hospitalaria": 0,
        "tasa_vacunacion": 0,
        "total": 0,
    })

    for person in simulation_state["population"]:
        code = person.get("country", "Unknown")
        report[code]["total"] += 1
        if person["state"] == "I":
            report[code]["infectados"] += 1
        if person["state"] == "R" and random.random() < 0.1:
            report[code]["muertes"] += 1

    for code, data in report.items():
        data["vacunados"] = random.randint(0, data["total"])
        data["centros_medicos"] = random.randint(0, 20)
        data["incidencia"] = round((data["infectados"] / data["total"]) * 100, 2) if data["total"] > 0 else 0
        data["recuperados"] = random.randint(0, data["total"])
        data["graves"] = random.randint(0, data["total"] // 10)
        if code in countries_data:
            country_info = countries_data[code]
            data["capacidad_hospitalaria"] = country_info.get("hospital_capacity", 0)
            data["tasa_vacunacion"] = round(random.uniform(0, 1), 2)
            data["poblacion"] = country_info.get("population", 0)
            data["pib"] = country_info.get("gdp", 0)

            # Calcular PIB per cápita para clasificación
            pib_per_capita = data["pib"] / data["poblacion"] if data["poblacion"] > 0 else 0

            # Clasificación socioeconómica sencilla
            if pib_per_capita < 1000:
                data["nivel_economico"] = "Pobre"
            elif pib_per_capita < 15000:
                data["nivel_economico"] = "Medio"
            else:
                data["nivel_economico"] = "Rico"
        else:
            data["capacidad_hospitalaria"] = 0
            data["tasa_vacunacion"] = 0
            data["poblacion"] = 0
            data["pib"] = 0
            data["nivel_economico"] = "Desconocido"

    # Crear nuevo dict con nombre completo en lugar de código
    named_report = {}
    for code, data in report.items():
        nombre = countries_data.get(code, {}).get("name", code)
        named_report[nombre] = data

    return named_report


# Endpoint para servir countries_data.json (opcional)
@app.get("/countries-data")
def get_countries_data():
    return JSONResponse(content=countries_data)
