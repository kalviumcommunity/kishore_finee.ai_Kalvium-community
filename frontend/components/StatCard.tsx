import React from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: React.ReactNode;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  accentColor?: "emerald" | "amber" | "blue" | "red" | "purple";
  badge?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  subtext,
  icon,
  trend,
  accentColor = "emerald",
  badge,
}) => {
  const accentBorder = {
    emerald: "border-t-emerald-500",
    amber: "border-t-amber-500",
    blue: "border-t-blue-500",
    red: "border-t-red-500",
    purple: "border-t-purple-500",
  }[accentColor];

  return (
    <div
      className={`bg-surface border border-surface-border rounded-xl p-5 relative overflow-hidden transition-all hover:border-surface-borderLight border-t-2 ${accentBorder}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">{label}</span>
        {icon && <div className="text-gray-400 p-1.5 rounded-lg bg-surface-raised">{icon}</div>}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-white">{value}</span>
        {badge && (
          <span className="text-xs px-2 py-0.5 rounded-md bg-surface-raised text-gray-300 border border-surface-border">
            {badge}
          </span>
        )}
      </div>

      {(subtext || trend) && (
        <div className="mt-2 flex items-center gap-2 text-xs text-gray-400">
          {trend && (
            <span
              className={`font-medium ${trend.isPositive ? "text-emerald-400" : "text-amber-400"}`}
            >
              {trend.value}
            </span>
          )}
          {subtext && <span>{subtext}</span>}
        </div>
      )}
    </div>
  );
};
