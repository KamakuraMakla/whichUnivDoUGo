<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'
import type { PrefectureTrends, RateMetric } from '../types/migration'

const props = defineProps<{
  trends: PrefectureTrends
  prefecture: string
  selectedYear: number
  selectedMetric: RateMetric
}>()
const chartElement = ref<HTMLElement | null>(null)

async function draw(): Promise<void> {
  await nextTick()
  if (!chartElement.value) return
  const { default: Plotly } = await import('plotly.js-dist-min')
  const years = Object.keys(props.trends[props.prefecture] ?? {}).map(Number)
  const series = [
    ['kanto', '関東進学率', '#16739b'],
    ['kansai', '関西進学率', '#b45309'],
    ['chukyo', '中京進学率', '#7c3aed'],
    ['local', '地元進学率', '#15803d'],
  ] as const
  const traces = series.map(([key, name, color]) => ({
    x: years,
    y: years.map((year) => props.trends[props.prefecture][String(year)][key]),
    name,
    type: 'scatter' as const,
    mode: 'lines+markers' as const,
    line: { color, width: key === props.selectedMetric ? 4 : 2 },
    marker: { size: years.map((year) => year === props.selectedYear ? 10 : 4) },
    hovertemplate: '%{x}年<br>%{y:.2f}%<extra>' + name + '</extra>',
  }))
  await Plotly.react(chartElement.value, traces, {
    margin: { t: 12, r: 12, b: 42, l: 58 },
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: '#fff',
    xaxis: { title: '年度', dtick: 5, fixedrange: true },
    yaxis: { title: '進学率（%）', rangemode: 'tozero', fixedrange: true },
    hovermode: 'x unified',
    shapes: [{ type: 'line', x0: props.selectedYear, x1: props.selectedYear, y0: 0, y1: 1, yref: 'paper', line: { color: '#b45309', dash: 'dot', width: 2 } }],
    legend: { orientation: 'h', y: -0.2 },
  }, { responsive: true, displayModeBar: false })
}
onMounted(draw)
watch(() => [props.trends, props.prefecture, props.selectedYear, props.selectedMetric], draw)
</script>
<template><div ref="chartElement" class="chart" aria-label="選択都道府県の進学率推移"></div></template>
