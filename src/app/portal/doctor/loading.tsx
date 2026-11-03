import React from 'react';

export default function DoctorLoading() {
  return (
    <div
      role="status"
      aria-label="Loading Doctor Portal"
      className="min-h-screen bg-canvas p-6 max-w-7xl mx-auto space-y-6 animate-pulse"
    >
      <span className="sr-only">Loading clinical workstation and patient records...</span>

      {/* Top Header & Search Bar Skeleton */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-surface border border-black/10 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_8px_24px_rgba(0,0,0,0.06)]">
        <div className="space-y-2">
          <div className="h-4 w-44 bg-black/10 rounded-md" />
          <div className="h-7 w-64 bg-black/15 rounded-md" />
        </div>
        <div className="w-full md:max-w-md h-11 bg-black/5 rounded-xl border border-black/10" />
      </div>

      {/* Tab Navigation Skeleton */}
      <div className="h-13 min-h-[52px] w-80 bg-black/5 rounded-xl border border-black/10 p-1 flex items-center gap-2">
        <div className="h-10 flex-1 bg-surface rounded-lg shadow-xs" />
        <div className="h-10 flex-1 bg-transparent rounded-lg" />
        <div className="h-10 flex-1 bg-transparent rounded-lg" />
      </div>

      {/* Content Area Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column Skeleton (8 cols) */}
        <div className="lg:col-span-8 rounded-2xl bg-surface border border-black/10 p-6 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_8px_24px_rgba(0,0,0,0.06)] space-y-4">
          <div className="flex items-center justify-between border-b border-black/5 pb-3">
            <div className="h-6 w-48 bg-black/10 rounded-md" />
            <div className="h-8 w-28 bg-black/10 rounded-md" />
          </div>
          <div className="space-y-3 pt-2">
            <div className="h-4 w-32 bg-black/10 rounded" />
            <div className="h-20 w-full bg-black/5 rounded-xl" />
          </div>
          <div className="space-y-3 pt-2">
            <div className="h-4 w-32 bg-black/10 rounded" />
            <div className="h-20 w-full bg-black/5 rounded-xl" />
          </div>
        </div>

        {/* Right Column Skeleton (4 cols) */}
        <div className="lg:col-span-4 rounded-2xl bg-surface border border-black/10 p-6 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_8px_24px_rgba(0,0,0,0.06)] space-y-4">
          <div className="h-6 w-36 bg-black/10 rounded-md border-b border-black/5 pb-3" />
          <div className="space-y-3 pt-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-3 rounded-xl bg-black/5 space-y-2">
                <div className="h-4 w-28 bg-black/10 rounded" />
                <div className="h-3 w-40 bg-black/5 rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
