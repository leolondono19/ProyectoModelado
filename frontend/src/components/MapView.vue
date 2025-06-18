<template>
  <div>
    <h2>Simulador de Expansión Epidémica - Mapa</h2>
    <div id="map"></div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import axios from 'axios';
import L from 'leaflet';

const countries = ref({});

onMounted(async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/countries-data');
    countries.value = res.data;
    console.log("Countries loaded:", countries.value);
  } catch (error) {
    console.error("Error loading countries data:", error);
  }
});

const props = defineProps({
  population: {
    type: Array,
    required: true
  }
});

const map = ref(null);
const markers = ref([]);

onMounted(() => {
  map.value = L.map('map', {
    maxBounds: [
      [-90, -180],
      [90, 180]
    ],
    maxBoundsViscosity: 1.0,
    worldCopyJump: false,
    zoomSnap: 0.5
  }).setView([20, 0], 2);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    noWrap: true,
    bounds: [
      [-90, -180],
      [90, 180]
    ]
  }).addTo(map.value);
});

watch(() => props.population, (newPopulation) => {
  markers.value.forEach(marker => map.value.removeLayer(marker));
  markers.value = [];

  newPopulation.forEach(person => {
    let color = 'gray';
    if (person.state === 'I' || person.state === 'infected') color = 'red';
    else if (person.state === 'S' || person.state === 'susceptible') color = 'green';

    const circle = L.circleMarker([person.lat, person.lon], {
      radius: 6,
      color: color,
      fillColor: color,
      fillOpacity: 0.7,
      weight: 1
    }).addTo(map.value);

    markers.value.push(circle);
  });
}, { immediate: true });
</script>

<style scoped>
#map {
  width: 100%;
  height: 500px;
  border-radius: 8px;
  border: 1px solid #ccc;
}
</style>
