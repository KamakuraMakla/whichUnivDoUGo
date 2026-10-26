<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { FeatureCollection } from 'geojson'
import JapanMap from './components/JapanMap.vue'
import MigrationChart from './components/MigrationChart.vue'
import { fetchGeoJson, fetchMapRates, fetchMetadata, fetchTrends } from './lib/data'
import type { Metadata, PrefectureTrends, RateMetric, RateRow } from './types/migration'

const metadata = ref<Metadata | null>(null)
const geoJson = ref<FeatureCollection | null>(null)
const mapRates = ref<RateRow[]>([])
const trends = ref<PrefectureTrends>({})
const selectedYear = ref(2025)
const selectedMetric = ref<RateMetric>('kanto')
const selectedOrigin = ref('石川県')
const isPlaying = ref(false)
const playSpeed = ref(700)
const error = ref('')
let timer: number | undefined

const yearRows = computed(() => mapRates.value.filter((row) => row.year === selectedYear.value))
const mapValues = computed(() => Object.fromEntries(yearRows.value.map((row) => [row.origin, row[selectedMetric.value]])))
const scaleMaximum = computed(() => Math.max(...mapRates.value.map((row) => row[selectedMetric.value]), 0))
const selectedValue = computed(() => mapValues.value[selectedOrigin.value] ?? 0)
const metricLabel = computed(() => metadata.value?.rateMetrics[selectedMetric.value] ?? '')
const progress = computed(() => ((selectedYear.value - 1975) / 50) * 100)
const wordmarkBackgroundUrl = `${import.meta.env.BASE_URL}japan-wordmark-bg.svg`

function togglePlay(): void {
  isPlaying.value = !isPlaying.value
  if (isPlaying.value) scheduleNextYear()
  else if (timer !== undefined) window.clearTimeout(timer)
}
function scheduleNextYear(): void {
  timer = window.setTimeout(() => {
    if (selectedYear.value >= 2025) {
      isPlaying.value = false
      return
    }
    selectedYear.value += 1
    scheduleNextYear()
  }, playSpeed.value)
}
watch(playSpeed, () => {
  if (isPlaying.value) {
    if (timer !== undefined) window.clearTimeout(timer)
    scheduleNextYear()
  }
})
onMounted(async () => {
  try {
    const [loadedMetadata, loadedGeoJson, loadedRates, loadedTrends] = await Promise.all([
      fetchMetadata(), fetchGeoJson(), fetchMapRates(), fetchTrends(),
    ])
    metadata.value = loadedMetadata
    geoJson.value = loadedGeoJson
    mapRates.value = loadedRates
    trends.value = loadedTrends
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '初期データの読み込みに失敗しました。'
  }
})
</script>

<template>
  <main class="app-shell">
    <header class="masthead">
      <h1 class="wordmark">
        <img :src="wordmarkBackgroundUrl" alt="" class="wordmark-map">
        <span>都道府県進学先マップ</span>
        <small>PREFECTURAL DESTINATIONS / 1975—2025</small>
      </h1>
      <p>出身高校の所在地ごとに、どの地域の大学へ進学したかを1975〜2025年で探索できます。</p>
    </header>
    <div v-if="error" class="error" role="alert">{{ error }}</div>
    <div v-else-if="!metadata || !geoJson || !mapRates.length" class="loading">データを読み込んでいます…</div>
    <template v-else>
      <section class="metric-tabs card" aria-label="表示指標">
        <button v-for="(label, key) in metadata.rateMetrics" :key="key" type="button" :class="{ active: selectedMetric === key }" @click="selectedMetric = key as RateMetric">{{ label }}</button>
      </section>
      <section class="map-panel card">
        <div class="section-heading">
          <div><p class="eyebrow">ORIGIN PREFECTURES</p><h2>{{ selectedYear }}年 {{ metricLabel }}</h2></div>
          <span class="legend">{{ metricLabel }}（0〜{{ scaleMaximum.toFixed(2) }}%）</span>
        </div>
        <JapanMap :geo-json="geoJson" :values="mapValues" :selected-origin="selectedOrigin" :metric="selectedMetric" :scale-maximum="scaleMaximum" @origin-selected="selectedOrigin = $event" />
        <div class="year-control">
          <div class="year-heading"><span>年度</span><strong>{{ selectedYear }}</strong></div>
          <input v-model.number="selectedYear" type="range" min="1975" max="2025" step="1" :style="{ '--progress': `${progress}%` }">
          <div class="range-labels"><span>1975</span><span>2025</span></div>
          <div class="play-controls">
            <button type="button" @click="togglePlay">{{ isPlaying ? '一時停止' : '再生' }}</button>
            <label>速度<select v-model.number="playSpeed"><option :value="1200">ゆっくり</option><option :value="700">標準</option><option :value="300">速い</option></select></label>
          </div>
        </div>
        <p class="map-note">色が濃いほど進学率が高くなります。地図をクリックすると、その県をグラフの対象にします。</p>
      </section>
      <section class="details-panel card">
        <div class="section-heading"><div><p class="eyebrow">SELECTED ORIGIN</p><h2>{{ selectedOrigin }}出身者の進学率推移</h2></div><strong class="selected-rate">{{ selectedYear }}年 {{ metricLabel }} {{ selectedValue.toFixed(2) }}%</strong></div>
        <MigrationChart :trends="trends" :prefecture="selectedOrigin" :selected-year="selectedYear" :selected-metric="selectedMetric" />
      </section>
      <footer class="source card">
        <strong>データの出典と定義</strong>
        <p>{{ metadata.source }}。出身地は居住地ではなく出身高校の所在地です。各進学率は、該当地域または自県の大学入学者数を、同じ出身高校所在地の47都道府県向け大学入学者総数で割った値です。</p>
        <p>地図：{{ metadata.geojsonSource }}。地域別進学率と地元進学率は重複し得るため、合計100%になる指標ではありません。</p>
      </footer>
    </template>
  </main>
</template>
