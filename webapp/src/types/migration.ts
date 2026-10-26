export type RateMetric = 'kanto' | 'kansai' | 'chukyo' | 'local'

export interface Prefecture {
  code: string
  name: string
}

export interface YearData {
  students: Record<string, number>
  total: number
  shares: Record<string, number>
}

export interface OriginData {
  origin: string
  originCode: string
  years: Record<string, YearData>
}

export interface Metadata {
  title: string
  years: number[]
  prefectures: Prefecture[]
  rateMetrics: Record<RateMetric, string>
  regions: Record<string, string[]>
  source: string
  geojsonSource: string
  definition: string
  recordCount: number
}

export interface RateRow {
  year: number
  origin: string
  kanto: number
  kansai: number
  chukyo: number
  local: number
}

export interface TrendRates {
  [year: string]: Omit<RateRow, 'year' | 'origin'>
}

export type PrefectureTrends = Record<string, TrendRates>
