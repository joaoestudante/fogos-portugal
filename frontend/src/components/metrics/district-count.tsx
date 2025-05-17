import { useGetDistrictCountQuery } from "@/app/api"
import { useSelector } from "react-redux"
import {
  selectMaxDateRaw,
  selectMinDateRaw,
} from "@/features/date-range/dateRangeSlice"
import { BarChartCounts } from "./building-blocks/bar-chart-counts"

export const TotalFiresPerDistrict = () => {
  const minDate = useSelector(selectMinDateRaw)
  const maxDate = useSelector(selectMaxDateRaw)

  const { data, isFetching } = useGetDistrictCountQuery(
    {
      from: minDate,
      to: maxDate,
    },
    { skip: !minDate || !maxDate },
  )

  return (
    <BarChartCounts
      title={"Most affected districts"}
      valueProperty="district"
      data={data}
      loading={isFetching}
    />
  )
}
