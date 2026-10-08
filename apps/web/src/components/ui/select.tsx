import * as React from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options?: Array<{ value: string; label: string; disabled?: boolean }>;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, helperText, options, children, id, ...props }, ref) => {
    const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label htmlFor={selectId} className="block text-xs font-medium text-slate">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            id={selectId}
            className={cn(
              "flex h-9 w-full appearance-none rounded-xl border border-border bg-surface px-3 py-1.5 pr-8 text-sm text-ink transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal focus-visible:border-teal disabled:cursor-not-allowed disabled:bg-cloud disabled:opacity-60",
              error && "border-danger focus-visible:ring-danger",
              className
            )}
            ref={ref}
            aria-invalid={!!error}
            {...props}
          >
            {options ? (
              options.length === 0 ? (
                <option value="" disabled className="text-slate-500 bg-white">
                  No options available
                </option>
              ) : (
                options.map((opt) => (
                  <option
                    key={opt.value}
                    value={opt.value}
                    disabled={opt.disabled}
                    className="text-slate-800 bg-white"
                  >
                    {opt.label}
                  </option>
                ))
              )
            ) : (
              children
            )}
          </select>
          <ChevronDown
            className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate"
            aria-hidden="true"
          />
        </div>
        {error && <p className="text-xs text-danger font-medium">{error}</p>}
        {!error && helperText && <p className="text-xs text-slate">{helperText}</p>}
      </div>
    );
  }
);
Select.displayName = "Select";
