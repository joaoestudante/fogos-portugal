import { useGetTotalFiresQuery } from "@/app/api"
import { SingleValue } from "./building-blocks/single-value"
import { useSelector } from "react-redux"
import {
  selectMaxDateRaw,
  selectMinDateRaw,
} from "@/features/date-range/dateRangeSlice"

export const TotalFires = () => {
  const minDate = useSelector(selectMinDateRaw)
  const maxDate = useSelector(selectMaxDateRaw)

  const { data, isFetching } = useGetTotalFiresQuery(
    {
      from: minDate,
      to: maxDate,
    },
    { skip: !minDate || !maxDate },
  )

  return (
    <SingleValue
      title="Total Fires"
      loading={isFetching}
      className="w-full h-full"
      data={data}
    />
  )
}
