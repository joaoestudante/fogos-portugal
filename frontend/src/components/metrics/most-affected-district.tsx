import { useGetMostAffectedDistrictQuery } from "@/app/api"
import { SingleValue } from "./building-blocks/single-value"
import { useSelector } from "react-redux"
import {
  selectMaxDateRaw,
  selectMinDateRaw,
} from "@/features/date-range/dateRangeSlice"

export const MostAffectedDistrict = () => {
  const minDate = useSelector(selectMinDateRaw)
  const maxDate = useSelector(selectMaxDateRaw)

  const { data, isFetching } = useGetMostAffectedDistrictQuery(
    {
      from: minDate,
      to: maxDate,
    },
    { skip: !minDate || !maxDate },
  )

  return (
    <SingleValue
      title="Most affected district"
      loading={isFetching}
      className="w-full h-full"
      data={data}
    />
  )
}
