// Types for /fires (GET)
export type Fire = {
  fire_id: string
  lat: number | null
  lng: number | null
  location: string | null
  district: string | null
  concelho: string | null
  freguesia: string | null
  natureza: string | null
  first_seen_commit_hash: string | null
  first_seen_data_timestamp: number | null
  last_updated_commit_hash: string | null
  last_updated_data_timestamp: number | null
  is_currently_active: number | null
}
export type FiresResponse = Fire[]

// Types for /fires/months (GET)
export type FiresPerMonth = {
  month: string // e.g. "2023-07"
  count: number
}
export type FiresPerMonthResponse = FiresPerMonth[]

// Types for /fires/total (GET)
export type FiresTotalResponse = {
  value: string
}

// Types for /fires/most-affected-district (GET)
export type MostAffectedDistrictResponse =
  | { value: string; subValue: string }
  | { value: "None" }

// Types for /fires/count-per-district (GET)
export type FiresCountPerDistrict = {
  district: string | null
  count: number
}
export type FiresCountPerDistrictResponse = FiresCountPerDistrict[]

// Types for /fires/duration-histogram (GET)
export type FiresDurationHistogramBin = {
  label: string // e.g. "0.0-0.5", "> 14.5"
  count: number
}
export type FiresDurationHistogramResponse = FiresDurationHistogramBin[]

// Types for /fires/duration-stats (GET)
export type FiresDurationStatsResponse = {
  value: number // average
  subValue: string // e.g. "Median: 2.50"
}

// Types for /fires/worst-day-stats (GET)
export type FiresWorstDayStatsResponse = {
  worst_day: string // e.g. "2023-08-15"
  total_fires: number
  total_resources: {
    man: number
    terrain: number
    aerial: number
  }
  largest_fire_duration_hours: number
  fire_with_longest_duration: string | null
  districts: string[]
}

// Types for /fires/available-date-range (GET)
export type FiresAvailableDateRangeResponse =
  | { min_date: number; max_date: number }
  | { message: string } // "No data available for date range."
