import { useGetFireDurationsQuery } from "@/app/api"
import { useSelector } from "react-redux"
import {
  selectMaxDateRaw,
  selectMinDateRaw,
} from "@/features/date-range/dateRangeSlice"
import { BarChartCounts } from "./building-blocks/bar-chart-counts"

export const FireDuration = () => {
  const minDate = useSelector(selectMinDateRaw)
  const maxDate = useSelector(selectMaxDateRaw)

  const { data, isFetching } = useGetFireDurationsQuery(
    {
      from: minDate,
      to: maxDate,
    },
    { skip: !minDate || !maxDate },
  )

  return (
    <BarChartCounts
      title={"Duration of fires"}
      valueProperty="label"
      data={data}
      loading={isFetching}
    />
  )
}
