import "./App.css"
import { ChartsDateRange } from "./components/charts-date-range"
import { FiresPerMonth } from "./components/metrics/fires-per-month"
import WorstDayCard from "./components/metrics/worst-day"
import { Separator } from "./components/ui/separator"
import { TotalFires } from "./components/metrics/total-fires"
import { MostAffectedDistrict } from "./components/metrics/most-affected-district"
import { TotalFiresPerDistrict } from "./components/metrics/district-count"
import { FireDuration } from "./components/metrics/fire-duration"

export const App = () => {
  return (
    <div className="App min-h-screen pb-8">
      <div className="w-full md:px-12 px-4 flex flex-col p-4">
        <div className="w-full flex justify-start pb-4">
          <div className="flex flex-col items-start">
            <p className="text-xl font-bold">Portugal Fires 🔥</p>
            <p className="font-light">
              An exploration of recent wildfires in Portugal. Data from{" "}
              <a href="https://fogos.pt" className="underline">
                fogos.pt
              </a>
            </p>
          </div>
        </div>
        <Separator className="mb-4" />
        <div className="flex flex-col gap-4 w-full">
          <div className="flex w-full justify-end flex-wrap">
            <ChartsDateRange />
          </div>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
            <div className="col-span-1 gap-4 flex flex-col justify-between">
              <TotalFires />
              <MostAffectedDistrict />
            </div>
            <FiresPerMonth />
          </div>
          <div className="grid grid-cols-1 gap-4">
            <TotalFiresPerDistrict />
          </div>
          <div className="grid lg:grid-cols-2 grid-cols-1 gap-4">
            <div className="col-span-1">
              <FireDuration />
            </div>
            <div className="col-span-1">
              <WorstDayCard />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
