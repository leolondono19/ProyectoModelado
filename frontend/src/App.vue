<template>
  <div class="app-container">
    <h1>🦠 Simulación de Epidemia Global</h1>

    <div class="control-panel">
      <div class="input-group">
        <label>Población:</label>
        <input type="number" v-model.number="populationSize" />
      </div>

      <div class="input-group">
        <label>Tasa de infección (0 - 1):</label>
        <input type="number" step="0.01" v-model.number="infectionRate" />
      </div>

      <div class="input-group">
        <label>Duración (ticks):</label>
        <input type="number" v-model.number="duration" />
      </div>

      <div class="input-group checkbox">
        <label>Modo Instantáneo:</label>
        <input type="checkbox" v-model="instantMode" />
      </div>

      <div class="button-group">
        <button @click="startSimulation" :disabled="running" class="start-btn">
          Iniciar Simulación
        </button>
        <button @click="stopSimulation" :disabled="!autoRunning && !instantRunning" class="stop-btn">
          Detener Simulación
        </button>
      </div>

      <div class="tick-info">
        <strong>Tick actual: {{ tick }}</strong>
      </div>
    </div>

    <MapView :population="population" />

    <!-- Tabla de resultados extendida -->
    <div v-if="!running && report.length > 0" class="report-table">
      <h2>📊 Reporte Final por País</h2>
      <table>
        <thead>
          <tr>
            <th>País</th>
            <th>Contagiados</th>
            <th>Muertes</th>
            <th>Vacunados</th>
            <th>Centros Médicos</th>
            <th>Incidencia</th>
            <th>Recuperados</th>
            <th>Casos Graves</th>
            <th>Capacidad Hospitalaria</th>
            <th>Tasa de Vacunación</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="fila in report" :key="fila.pais">
            <td>{{ fila.pais }}</td>
            <td>{{ fila.contagiados }}</td>
            <td>{{ fila.muertes }}</td>
            <td>{{ fila.vacunados }}</td>
            <td>{{ fila.centros_medicos }}</td>
            <td>{{ fila.incidencia }}</td>
            <td>{{ fila.recuperados }}</td>
            <td>{{ fila.graves }}</td>
            <td>{{ fila.capacidad_hospitalaria }}</td>
            <td>{{ fila.tasa_vacunacion }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>


<script setup>
import { ref } from 'vue';
import axios from "axios";
import MapView from './components/MapView.vue';

const populationSize = ref(50);
const infectionRate = ref(0.1);
const duration = ref(50);
const instantMode = ref(false);
const population = ref([]);
const tick = ref(0);
const running = ref(false);
const autoRunning = ref(false);
const instantRunning = ref(false);
const report = ref([]);
let intervalId = null;
let stopRequested = false;

// 🟦 Función para obtener el reporte final
const generateReport = async () => {
  try {
    const res = await axios.get("http://127.0.0.1:8000/report");
    report.value = Object.entries(res.data).map(([pais, datos]) => ({
  pais,
  contagiados: datos.contagiados,
  muertes: datos.muertes,
  vacunados: datos.vacunados,
  centros_medicos: datos.centros_medicos,
  incidencia: datos.incidencia,
  recuperados: datos.recuperados,
  graves: datos.graves,
  capacidad_hospitalaria: datos.capacidad_hospitalaria,
  tasa_vacunacion: datos.tasa_vacunacion
}));
  } catch (error) {
    console.error("Error al obtener el reporte:", error);
  }
};

const startSimulation = async () => {
  try {
    stopRequested = false;
    const res = await axios.post("http://127.0.0.1:8000/start", {
      population_size: populationSize.value,
      infection_rate: infectionRate.value,
      initial_infected: 1,
    });
    population.value = res.data.population;
    tick.value = 0;
    running.value = true;
    report.value = [];

    if (instantMode.value) {
      instantRunning.value = true;
      for (let i = 0; i < duration.value; i++) {
        if (stopRequested) break;
        await nextTick();
        if (!running.value) break; // se detuvo sola
      }
      instantRunning.value = false;

      // Si terminó automáticamente, genera reporte
      if (!running.value && !stopRequested) {
        await generateReport();
      }
    } else {
      autoRunning.value = true;
      intervalId = setInterval(async () => {
        if (stopRequested || tick.value >= duration.value || !running.value) {
          clearInterval(intervalId);
          if (!stopRequested && !running.value) {
            await generateReport();
          }
          stopSimulation(false);
          return;
        }
        await nextTick();
      }, 1000);
    }
  } catch (error) {
    console.error(error);
  }
};

const nextTick = async () => {
  if (!running.value) return;
  try {
    const res = await axios.post("http://127.0.0.1:8000/tick");
    population.value = res.data.population;
    tick.value = res.data.tick;
    running.value = res.data.running;

    if (!res.data.running && !stopRequested) {
      await generateReport();
      stopSimulation(false);
    }
  } catch (error) {
    console.error(error);
  }
};

const stopSimulation = (manual = true) => {
  stopRequested = true;
  clearInterval(intervalId);
  autoRunning.value = false;
  instantRunning.value = false;
  running.value = false;

  // Generar reporte solo si fue detenido manualmente
  if (manual && report.value.length === 0) {
  generateReport();
}
};
</script>


<style scoped>
.app-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: #f5f7fa;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

h1 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 20px;
}

.control-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  justify-content: center;
  margin-bottom: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  width: 180px;
}

.input-group label {
  font-weight: 600;
  margin-bottom: 4px;
  color: #34495e;
}

.input-group input[type="number"],
.input-group input[type="checkbox"] {
  padding: 6px;
  border-radius: 6px;
  border: 1px solid #ccc;
}

.checkbox {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}

.button-group {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 10px;
}

.start-btn {
  background-color: #2ecc71;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}

.stop-btn {
  background-color: #e74c3c;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}

.start-btn:disabled,
.stop-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tick-info {
  width: 100%;
  text-align: center;
  font-size: 1.1em;
  margin-top: 10px;
}

.report-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  background: white;
  border: 1px solid #ccc;
}

.report-table th,
.report-table td {
  padding: 10px;
  text-align: center;
  border: 1px solid #ddd;
}

.report-table th {
  background-color: #3498db;
  color: white;
}
</style>
