import React from 'react';

export default function PatientLoading() {
  return (
    <div
      role="status"
      aria-label="Loading Patient Portal"
      className="min-h-screen bg-canvas p-6 max-w-7xl mx-auto space-y-4 animate-pulse"
    >
      <span className="sr-only">Loading patient health records and emergency identity...</span>

      {/* Responsive Bento Grid Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Row 1: Hero Profile Card Skeleton (8 cols) */}
        <div className="lg:col-span-8 rounded-[18px] bg-surface border border-black/10 p-6 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_8px_24px_rgba(0,0,0,0.06)] space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <div className="h-6 w-48 bg-black/10 rounded-md" />
              <div className="h-4 w-32 bg-black/5 rounded-md" />
            </div>
            <div className="h-8 w-24 bg-black/10 rounded-full" />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-black/5">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="space-y-1.5">
                <div className="h-3 w-16 bg-black/5 rounded" />
                <div className="h-5 w-24 bg-black/10 rounded" />
              </div>
            ))}
          </div>
        </div>

        {/* Row 1: QR Studio Skeleton (4 cols) */}
        <div className="lg:col-span-4 rounded-[18px] bg-surface border border-black/10 p-6 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_8px_24px_rgba(0,0,0,0.06)] flex flex-col items-center justify-center space-y-3">
          <div className="h-5 w-32 bg-black/10 rounded-md" />
          <div className="h-44 w-44 bg-black/10 rounded-xl" />
          <div className="h-4 w-28 bg-black/5 rounded" />
        </div>

        {/* Row 2: Emergency Contact Skeleton (4 cols) */}
        <div className="lg:col-span-4 rounded-[18px] bg-surface border border-black/10 p-6 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_8px_24px_rgba(0,0,0,0.06)] space-y-3">
          <div className="h-5 w-36 bg-black/10 rounded-md" />
          <div className="space-y-2 pt-2">
            <div className="h-4 w-28 bg-black/5 rounded" />
            <div className="h-6 w-40 bg-black/10 rounded" />
            <div className="h-4 w-32 bg-black/5 rounded" />
          </div>
        </div>

        {/* Row 2: Medical Overview Skeleton (8 cols) */}
        <div className="lg:col-span-8 rounded-[18px] bg-surface border border-black/10 p-6 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_8px_24px_rgba(0,0,0,0.06)] space-y-4">
          <div className="flex items-center justify-between">
            <div className="h-5 w-40 bg-black/10 rounded-md" />
            <div className="h-6 w-20 bg-black/10 rounded-full" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div className="space-y-2 p-3 rounded-xl bg-black/5">
              <div className="h-4 w-24 bg-black/10 rounded" />
              <div className="h-8 w-full bg-black/5 rounded" />
            </div>
            <div className="space-y-2 p-3 rounded-xl bg-black/5">
              <div className="h-4 w-24 bg-black/10 rounded" />
              <div className="h-8 w-full bg-black/5 rounded" />
            </div>
          </div>
        </div>

        {/* Row 3: Demographics Skeleton (12 cols) */}
        <div className="lg:col-span-12 rounded-[18px] bg-surface border border-black/10 p-6 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_8px_24px_rgba(0,0,0,0.06)] space-y-4">
          <div className="h-5 w-48 bg-black/10 rounded-md" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-10 bg-black/5 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
