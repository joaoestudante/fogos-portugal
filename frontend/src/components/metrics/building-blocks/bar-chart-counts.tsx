// A component to display the count of categories

"use client"

import { CartesianGrid, BarChart, XAxis, YAxis, Bar } from "recharts"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { Skeleton } from "@/components/ui/skeleton"

// props: title, min height
export function BarChartCounts({
  title,
  data,
  valueProperty,
  loading,
}: {
  title: string
  data: any
  valueProperty: string
  loading: boolean
}) {
  return (
    <Card className="lg:col-span-3">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {loading || !data ? (
          <Skeleton className="h-10 w-20" />
        ) : (
          <div className="h-96 w-full">
            <ChartContainer
              config={{
                count: {
                  label: "Count",
                  color: "hsl(var(--chart-1))",
                },
              }}
              className="h-full w-full"
            >
              <BarChart
                data={data}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey={valueProperty}
                  axisLine={false}
                  tickLine={false}
                  height={120}
                  type="category"
                  interval={0}
                  tick={props => {
                    const { x, y, payload } = props
                    return (
                      <g transform={`translate(${x},${y})`}>
                        <text
                          x={0}
                          y={0}
                          dy={16}
                          textAnchor="end"
                          fill="currentColor"
                          transform="rotate(-45)"
                        >
                          {payload.value}
                        </text>
                      </g>
                    )
                  }}
                />
                <YAxis axisLine={false} tickLine={false} tickMargin={10} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar
                  type="monotone"
                  dataKey="count"
                  fill="var(--chart-1)"
                  radius={4}
                />
              </BarChart>
            </ChartContainer>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
