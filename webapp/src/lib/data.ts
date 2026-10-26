import type { Metadata, PrefectureTrends, RateRow } from '../types/migration'
import type { FeatureCollection } from 'geojson'

export async function fetchMetadata(): Promise<Metadata> {
  const response = await fetch('./data/metadata.json')
  if (!response.ok) throw new Error(`metadata.json の読み込みに失敗しました (${response.status})`)
  return response.json() as Promise<Metadata>
}

export async function fetchGeoJson(): Promise<FeatureCollection> {
  const response = await fetch('./data/prefectures.geojson')
  if (!response.ok) throw new Error(`prefectures.geojson の読み込みに失敗しました (${response.status})`)
  return response.json() as Promise<FeatureCollection>
}

export async function fetchMapRates(): Promise<RateRow[]> {
  const response = await fetch('./data/map_rates.json')
  if (!response.ok) throw new Error(`map_rates.json の読み込みに失敗しました (${response.status})`)
  return response.json() as Promise<RateRow[]>
}

export async function fetchTrends(): Promise<PrefectureTrends> {
  const response = await fetch('./data/prefecture_trends.json')
  if (!response.ok) throw new Error(`prefecture_trends.json の読み込みに失敗しました (${response.status})`)
  return response.json() as Promise<PrefectureTrends>
}
