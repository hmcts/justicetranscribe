import React from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Step2SetupProps {
  email: string;
  crissaTime: string;
  appointmentsPerWeek: string;
  onEmailChange: (email: string) => void;
  onCrissaTimeChange: (time: string) => void;
  onAppointmentsChange: (appointments: string) => void;
}

export default function Step2Setup({
  email,
  crissaTime,
  appointmentsPerWeek,
  onEmailChange,
  onCrissaTimeChange,
  onAppointmentsChange,
}: Step2SetupProps) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="mb-6 text-[2.625rem] sm:text-[2.875rem] md:text-[3rem] lg:text-[3.25rem] xl:text-[3.5rem] font-semibold">Get started</h3>
      </div>

      <div className="space-y-6">
        <div>
          <Label htmlFor="email" className="text-base font-medium">
            Email address
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => onEmailChange(e.target.value)}
            className="mt-2"
            required
          />
        </div>

        <fieldset>
          <legend className="text-base font-medium mb-3 block">
            Please estimate your usual time to write a CRISSA note:
          </legend>
          <div className="space-y-3" role="radiogroup" aria-labelledby="crissa-time-legend">
            {[
              { value: "<5", label: "<5 min" },
              { value: "5-10", label: "5–10 min" },
              { value: "11-20", label: "11–20 min" },
              { value: "21-30", label: "21–30 min" },
              { value: ">30", label: ">30 min" },
              { value: "n/a", label: "N/A" }
            ].map((option, index) => (
              <div key={option.value} className="flex items-center space-x-3">
                <input
                  type="radio"
                  id={`crissa-${option.value}`}
                  name="crissa-time"
                  value={option.value}
                  checked={crissaTime === option.value}
                  onChange={(e) => onCrissaTimeChange(e.target.value)}
                  className="size-4 text-blue-600 border-gray-300 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  tabIndex={0}
                  aria-describedby={`crissa-${option.value}-label`}
                />
                <Label 
                  htmlFor={`crissa-${option.value}`} 
                  id={`crissa-${option.value}-label`}
                  className="text-sm font-normal cursor-pointer hover:text-blue-600 transition-colors select-none"
                >
                  {option.label}
                </Label>
              </div>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend className="text-base font-medium mb-3 block">
            In a typical week, how many appointments with People on Probation do you have?
          </legend>
          <div className="space-y-3" role="radiogroup" aria-labelledby="appointments-legend">
            {[
              { value: "0", label: "0" },
              { value: "1-5", label: "1–5" },
              { value: "6-10", label: "6–10" },
              { value: "11-20", label: "11–20" },
              { value: "21-30", label: "21–30" },
              { value: "31-40", label: "31–40" },
              { value: "41+", label: "41+" },
              { value: "n/a", label: "N/A (I don't meet PoP in my role)" }
            ].map((option, index) => (
              <div key={option.value} className="flex items-center space-x-3">
                <input
                  type="radio"
                  id={`appointments-${option.value}`}
                  name="appointments-per-week"
                  value={option.value}
                  checked={appointmentsPerWeek === option.value}
                  onChange={(e) => onAppointmentsChange(e.target.value)}
                  className="size-4 text-blue-600 border-gray-300 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  tabIndex={0}
                  aria-describedby={`appointments-${option.value}-label`}
                />
                <Label 
                  htmlFor={`appointments-${option.value}`} 
                  id={`appointments-${option.value}-label`}
                  className="text-sm font-normal cursor-pointer hover:text-blue-600 transition-colors select-none"
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
