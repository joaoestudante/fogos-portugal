import { useGetFiresPerMonthQuery } from "@/app/api"
import { NumberOverTime } from "./building-blocks/number-over-time"
import { useSelector } from "react-redux"
import {
  selectMaxDateRaw,
  selectMinDateRaw,
} from "@/features/date-range/dateRangeSlice"

export const FiresPerMonth = () => {
  const minDate = useSelector(selectMinDateRaw)
  const maxDate = useSelector(selectMaxDateRaw)

  const { data, isFetching } = useGetFiresPerMonthQuery(
    {
      from: minDate,
      to: maxDate,
    },
    { skip: !minDate || !maxDate },
  )

  return (
    <NumberOverTime
      title={"Fire frequency over time"}
      valueProperty="month"
      data={data}
      isFetching={isFetching}
    />
  )
}
