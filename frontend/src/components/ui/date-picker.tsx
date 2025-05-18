"use client"

import { format } from "date-fns"
import { CalendarIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

export function DatePicker({
  minDate,
  maxDate,
  value,
  dateUpdated,
  blockValuesBefore,
  blockValuesAfter,
}: {
  minDate: Date
  maxDate: Date
  value?: Date
  dateUpdated: (date: Date | undefined) => {}
  blockValuesBefore?: Date
  blockValuesAfter?: Date
}) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant={"outline"}
          className={cn(
            "md:w-[280px] w-full justify-start text-left font-normal",
            !value && "text-muted-foreground",
          )}
        >
          <CalendarIcon />
          {value ? format(value, "PPP") : <span>Pick a date</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0">
        <Calendar
          mode="single"
          selected={value}
          onSelect={dateUpdated}
          defaultMonth={value}
          initialFocus
          disabled={[
            ...(minDate ? [{ before: minDate }] : []),
            ...(maxDate ? [{ after: maxDate }] : []),
            ...(blockValuesBefore ? [{ before: blockValuesBefore }] : []),
            ...(blockValuesAfter ? [{ after: blockValuesAfter }] : []),
          ]}
        />
      </PopoverContent>
    </Popover>
  )
}
