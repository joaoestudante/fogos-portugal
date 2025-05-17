// A component to display a single number metric, start with an hardcoded value

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

import { cn } from "@/lib/utils"

export function SingleValue({
  title,
  loading = false,
  className,
  data,
}: {
  title: string
  loading?: boolean
  className?: string
  data: { value: string; subValue?: string } | undefined
}) {
  return (
    <Card className={cn("w-48 h-48", className)}>
      <CardHeader className="flex flex-col items-center justify-center h-12">
        <CardTitle className="">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-center h-full">
        {loading || !data ? (
          <Skeleton className="h-10 w-20" />
        ) : (
          <div>
            <p className="text-2xl font-bold">{data.value}</p>
            {data.subValue && (
              <p className="text-sm text-gray-500">{data.subValue}</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
