// A component to display a number metric over time, such as a line chart

"use client"

import { TrendingUp } from "lucide-react"
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { cn } from "@/lib/utils"
import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"

// props: title, min height
export function NumberOverTime({
  title,
  valueProperty,
  data,
  isFetching,
}: {
  title?: string
  valueProperty: string
  data: any
  isFetching: boolean
}) {
  return (
    <Card className="lg:col-span-3">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-96 w-full">
          {!isFetching ? (
            <ChartContainer
              config={{
                count: {
                  label: "Count",
                  color: "hsl(var(--chart-1))",
                },
              }}
              className="h-full w-full"
            >
              <LineChart
                data={data}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey={valueProperty}
                  axisLine={false}
                  tickLine={false}
                  tickMargin={10}
                />
                <YAxis axisLine={false} tickLine={false} tickMargin={10} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="var(--chart-1)"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ChartContainer>
          ) : (
            <div className="w-full h-full">
              <Skeleton className="w-full h-full"></Skeleton>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
