import React, { useEffect, useState } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { useSelector } from "react-redux"
import {
  selectMaxDateRaw,
  selectMinDateRaw,
} from "@/features/date-range/dateRangeSlice"
import { useGetWorstDayQuery } from "@/app/api"

type WorstDayStatsResponse = {
  worst_day: string
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

const WorstDayCards: React.FC = () => {
  const minDate = useSelector(selectMinDateRaw)
  const maxDate = useSelector(selectMaxDateRaw)

  const { data, isFetching } = useGetWorstDayQuery(
    {
      from: minDate,
      to: maxDate,
    },
    { skip: !minDate || !maxDate },
  )
  if (isFetching) {
    return (
      <div>
        <Card>
          <CardHeader>
            <CardTitle>Loading...</CardTitle>
          </CardHeader>
          <CardContent>Please wait while we fetch the data.</CardContent>
        </Card>
      </div>
    )
  }

  if (!data) {
    return (
      <div>
        <Card>
          <CardHeader>
            <CardTitle>No Data</CardTitle>
          </CardHeader>
          <CardContent>No data available to display.</CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 h-full">
      <Card className="col-span-3">
        <CardHeader>
          <CardTitle>Worst Day - {data.worst_day}</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 h-full">
          <Card>
            <CardHeader>
              <CardTitle>Total Fires</CardTitle>
            </CardHeader>
            <CardContent>{data.total_fires}</CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Total Resources deployed this day</CardTitle>
            </CardHeader>
            <CardContent className="flex justify-center items-center">
              <ul className="flex flex-col items-start">
                <li>👨‍🚒: {data.total_resources.man}</li>
                <li>🚒: {data.total_resources.terrain}</li>
                <li>🚁: {data.total_resources.aerial}</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Largest Fire Duration</CardTitle>
            </CardHeader>
            <CardContent>{data.largest_fire_duration_hours}</CardContent>
          </Card>

          <Card className="col-span-1 md:col-span-2 lg:col-span-3 ">
            <CardHeader>
              <CardTitle>Districts</CardTitle>
            </CardHeader>
            <CardContent>{data.districts.join(", ")}</CardContent>
          </Card>
        </CardContent>
      </Card>
    </div>
  )
}

export default WorstDayCards
