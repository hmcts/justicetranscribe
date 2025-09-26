import React from "react";

import { Label } from "@/components/ui/label";

interface Step2SetupProps {
  crissaTime: string;
  appointmentsPerWeek: string;
  onCrissaTimeChange: (time: string) => void;
  onAppointmentsChange: (appointments: string) => void;
}

export default function Step2Setup({
  crissaTime,
  appointmentsPerWeek,
  onCrissaTimeChange,
  onAppointmentsChange,
}: Step2SetupProps) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="mb-6 text-[2.625rem] font-semibold sm:text-[2.875rem] md:text-[3rem] lg:text-[3.25rem] xl:text-[3.5rem]">
          Get started
        </h2>
      </div>

      <div className="space-y-6">
        <fieldset>
          <legend id="crissa-time-legend" className="mb-3 block text-base font-medium">
            Please estimate your usual time to write a CRISSA note:
          </legend>
          <div
            className="space-y-3"
            role="radiogroup"
            aria-labelledby="crissa-time-legend"
          >
            {[
              { value: "<5", label: "<5 min" },
              { value: "5-10", label: "5–10 min" },
              { value: "11-20", label: "11–20 min" },
              { value: "21-30", label: "21–30 min" },
              { value: ">30", label: ">30 min" },
              { value: "n/a", label: "N/A" },
            ].map((option) => (
              <div key={option.value} className="flex items-center space-x-3">
                <input
                  type="radio"
                  id={`crissa-${option.value}`}
                  name="crissa-time"
                  value={option.value}
                  checked={crissaTime === option.value}
                  onChange={(e) => onCrissaTimeChange(e.target.value)}
                  className="size-4 border-gray-300 text-blue-600 focus:outline-none focus:ring-0"
                  tabIndex={0}
                  aria-describedby={`crissa-${option.value}-label`}
                />
                <Label
                  htmlFor={`crissa-${option.value}`}
                  id={`crissa-${option.value}-label`}
                  className="cursor-pointer select-none text-sm font-normal transition-colors hover:text-blue-600"
                >
                  {option.label}
                </Label>
              </div>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend id="appointments-legend" className="mb-3 block text-base font-medium">
            In a typical week, how many appointments with People on Probation do
            you have?
          </legend>
          <div
            className="space-y-3"
            role="radiogroup"
            aria-labelledby="appointments-legend"
          >
            {[
              { value: "0", label: "0" },
              { value: "1-5", label: "1–5" },
              { value: "6-10", label: "6–10" },
              { value: "11-20", label: "11–20" },
              { value: "21-30", label: "21–30" },
              { value: "31-40", label: "31–40" },
              { value: "41+", label: "41+" },
              { value: "n/a", label: "N/A (I don't meet PoP in my role)" },
            ].map((option) => (
              <div key={option.value} className="flex items-center space-x-3">
                <input
                  type="radio"
                  id={`appointments-${option.value}`}
                  name="appointments-per-week"
                  value={option.value}
                  checked={appointmentsPerWeek === option.value}
                  onChange={(e) => onAppointmentsChange(e.target.value)}
                  className="size-4 border-gray-300 text-blue-600 focus:outline-none focus:ring-0"
                  tabIndex={0}
                  aria-describedby={`appointments-${option.value}-label`}
                />
                <Label
                  htmlFor={`appointments-${option.value}`}
                  id={`appointments-${option.value}-label`}
                  className="cursor-pointer select-none text-sm font-normal transition-colors hover:text-blue-600"
                >
                  {option.label}
                </Label>
              </div>
            ))}
          </div>
        </fieldset>
      </div>
    </div>
  );
}
