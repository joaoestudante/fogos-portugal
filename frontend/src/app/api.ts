import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react"
import {
  FiresCountPerDistrictResponse,
  FiresDurationHistogramResponse,
  FiresPerMonthResponse,
  FiresTotalResponse,
  FiresWorstDayStatsResponse,
  MostAffectedDistrictResponse,
} from "./api-types"

export const firesApi = createApi({
  reducerPath: "firesApi",
  tagTypes: ["Fires"],

  baseQuery: fetchBaseQuery({
    baseUrl: `${import.meta.env.VITE_API_URL}/api/`,
  }),
  endpoints: build => ({
    getFiresPerMonth: build.query<
      FiresPerMonthResponse,
      { from: number; to: number }
    >({
      // note: an optional `queryFn` may be used in place of `query`
      query: ({ from, to }) => ({
        url: `fires/months?fromDate=${from}&toDate=${to}`,
      }),
    }),
    getTotalFires: build.query<
      FiresTotalResponse,
      { from: number; to: number }
    >({
      // note: an optional `queryFn` may be used in place of `query`
      query: ({ from, to }) => ({
        url: `fires/total?fromDate=${from}&toDate=${to}`,
      }),
    }),
    getMostAffectedDistrict: build.query<
      MostAffectedDistrictResponse,
      { from: number; to: number }
    >({
      // note: an optional `queryFn` may be used in place of `query`
      query: ({ from, to }) => ({
        url: `fires/most-affected-district?fromDate=${from}&toDate=${to}`,
      }),
    }),
    getDistrictCount: build.query<
      FiresCountPerDistrictResponse,
      { from: number; to: number }
    >({
      // note: an optional `queryFn` may be used in place of `query`
      query: ({ from, to }) => ({
        url: `fires/count-per-district?fromDate=${from}&toDate=${to}`,
      }),
    }),
    getFireDurations: build.query<
      FiresDurationHistogramResponse,
      { from: number; to: number }
    >({
      // note: an optional `queryFn` may be used in place of `query`
      query: ({ from, to }) => ({
        url: `fires/duration-histogram?fromDate=${from}&toDate=${to}`,
      }),
    }),
    getWorstDay: build.query<
      FiresWorstDayStatsResponse,
      { from: number; to: number }
    >({
      // note: an optional `queryFn` may be used in place of `query`
      query: ({ from, to }) => ({
        url: `fires/worst-day-stats?fromDate=${from}&toDate=${to}`,
      }),
    }),
  }),
})
///
export const {
  useGetFiresPerMonthQuery,
  useGetTotalFiresQuery,
  useGetMostAffectedDistrictQuery,
  useGetDistrictCountQuery,
  useGetFireDurationsQuery,
  useGetWorstDayQuery,
} = firesApi
