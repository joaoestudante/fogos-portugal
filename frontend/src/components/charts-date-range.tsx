// Date Range picker affecting all charts
import { useEffect, useState } from "react"
import { DatePicker } from "@/components/ui/date-picker"
import { useDispatch, useSelector } from "react-redux"
import {
  selectMaxDate,
  selectMinDate,
  setMaxDate,
  setMinAndMaxDates,
  setMinDate,
} from "@/features/date-range/dateRangeSlice"

export const ChartsDateRange = () => {
  const minDate = useSelector(selectMinDate)
  const maxDate = useSelector(selectMaxDate)

  const [minDateRange, setMinDateRange] = useState<Date>()
  const [maxDateRange, setMaxDateRange] = useState<Date>()

  const dispatch = useDispatch()

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await fetch(
          "http://localhost:5000/fires/available-date-range",
        )
        const data = await response.json()
        setMinDateRange(new Date(data.min_date * 1000))
        setMaxDateRange(new Date(data.max_date * 1000))
        dispatch(
          setMinAndMaxDates([data.min_date * 1000, data.max_date * 1000]),
        )
      } catch (error) {
        console.error("Failed to fetch chart data:", error)
      }
    }
    fetchData()
  }, [])

  let minusOneDay = (date: Date) => {
    let newDate = new Date(date)
    newDate.setDate(newDate.getDate() - 1)
    return newDate
  }

  let addOneDay = (date: Date) => {
    let newDate = new Date(date)
    newDate.setDate(newDate.getDate() + 1)
    return newDate
  }

  return minDateRange != undefined && maxDateRange != undefined ? (
    <div className="flex gap-2 flex-wrap w-full">
      <div className="flex flex-col justify-start items-start md:w-fit w-full">
        <p className="text-sm text-orange-600 ml-1 mb-1">From</p>
        <DatePicker
          minDate={minDateRange}
          maxDate={maxDateRange}
          value={minDate}
          dateUpdated={value => dispatch(setMinDate(value?.getTime()))}
          blockValuesAfter={minusOneDay(maxDate)}
        />
      </div>
      <div className="flex flex-col justify-start items-start md:w-fit w-full">
        <p className="text-sm text-orange-600 ml-1 mb-1">To</p>
        <DatePicker
          minDate={minDateRange}
          maxDate={maxDateRange}
          value={maxDate}
          dateUpdated={value => dispatch(setMaxDate(value?.getTime()))}
          blockValuesBefore={addOneDay(minDate)}
        />
      </div>
    </div>
  ) : (
    <p>Loading...</p>
  )
}
