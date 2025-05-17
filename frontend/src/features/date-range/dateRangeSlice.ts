import { createSelector, createSlice } from "@reduxjs/toolkit"

export const dateRangeSlice = createSlice({
  name: "dateRange",
  initialState: {
    minDateRange: null,
    maxDateRange: null,
  },
  reducers: {
    setMinDate: (state, action) => {
      state.minDateRange = action.payload
    },
    setMaxDate: (state, action) => {
      state.maxDateRange = action.payload
    },
    setMinAndMaxDates: (state, action) => {
      state.minDateRange = action.payload[0]
      state.maxDateRange = action.payload[1]
    },
  },
})

// Action creators are generated for each case reducer function
export const { setMinDate, setMaxDate, setMinAndMaxDates } =
  dateRangeSlice.actions

// Base selector
const selectDateRangeState = (state: { dateRange: any }) => state.dateRange

// Memoized selectors
export const selectMinDate = createSelector(
  [selectDateRangeState],
  dateRange => {
    return dateRange.minDateRange
      ? new Date(dateRange.minDateRange)
      : new Date()
  },
)

export const selectMaxDate = createSelector(
  [selectDateRangeState],
  dateRange => {
    return dateRange.maxDateRange
      ? new Date(dateRange.maxDateRange)
      : new Date()
  },
)

export const selectMinDateRaw = createSelector(
  [selectDateRangeState],
  dateRange => dateRange.minDateRange,
)

export const selectMaxDateRaw = createSelector(
  [selectDateRangeState],
  dateRange => dateRange.maxDateRange,
)

export default dateRangeSlice.reducer
