<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import L from 'leaflet'
import type { FeatureCollection } from 'geojson'
import type { RateMetric } from '../types/migration'

const props = defineProps<{
  geoJson: FeatureCollection
  values: Record<string, number>
  selectedOrigin: string
  metric: RateMetric
  scaleMaximum: number
}>()
const emit = defineEmits<{ originSelected: [name: string] }>()
const mapElement = ref<HTMLElement | null>(null)
let map: L.Map | undefined
let layer: L.GeoJSON | undefined

function color(value: number, max: number): string {
  if (value <= 0) return '#f1f5f9'
  // 固定した最大値を使い、平方根で低〜中程度の値の差も見やすくする。
  const ratio = Math.min(value / Math.max(max, 1), 1)
  const contrast = Math.sqrt(ratio)
  const palettes = {
    kanto: { hue: 3, saturation: 78 },
    chukyo: { hue: 29, saturation: 88 },
    kansai: { hue: 211, saturation: 78 },
    local: { hue: 0, saturation: 0 },
  } as const
  const palette = palettes[props.metric]
  const lightness = 96 - contrast * 56
  return `hsl(${palette.hue} ${palette.saturation}% ${lightness}%)`
}

function redraw(): void {
  if (!map) return
  layer?.remove()
  layer = L.geoJSON(props.geoJson, {
    style: (feature) => {
      const name = feature?.properties?.nam_ja as string
      return {
        color: name === props.selectedOrigin ? '#b45309' : '#64748b',
        weight: name === props.selectedOrigin ? 3 : 1,
        fillColor: color(props.values[name] ?? 0, props.scaleMaximum),
        fillOpacity: 0.9,
      }
    },
    onEachFeature: (feature, featureLayer) => {
      const name = feature.properties?.nam_ja as string
      const pathLayer = featureLayer as L.Path
      pathLayer.bindTooltip(`${name}: ${(props.values[name] ?? 0).toFixed(2)}%`)
      pathLayer.on('click', () => emit('originSelected', name))
      pathLayer.on('mouseover', () => pathLayer.setStyle({ weight: 3, color: '#0f172a' }))
      pathLayer.on('mouseout', () => pathLayer.setStyle({
        weight: name === props.selectedOrigin ? 3 : 1,
        color: name === props.selectedOrigin ? '#b45309' : '#64748b',
      }))
    },
  }).addTo(map)
}

onMounted(() => {
  if (!mapElement.value) return
  map = L.map(mapElement.value, { zoomControl: true, minZoom: 4, maxZoom: 10 }).setView([36.2, 138.3], 5)
  redraw()
})
watch(() => [props.geoJson, props.values, props.selectedOrigin, props.metric], redraw)
onUnmounted(() => map?.remove())
</script>

<template><div ref="mapElement" class="map" aria-label="出身高校所在地別の進学率地図"></div></template>
