'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { segmentedPillTransition } from '@/lib/motion';

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
  layoutId?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  className,
  layoutId = 'active-pill',
}) => {
  return (
    <div
      role="tablist"
      aria-orientation="horizontal"
      className={cn(
        'inline-flex h-[44px] min-h-[44px] items-center rounded-xl bg-black/5 p-1 text-sm font-medium',
        className
      )}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            tabIndex={isActive ? 0 : -1}
            onClick={() => onChange(tab.id)}
            className={cn(
              'relative z-10 flex h-full items-center justify-center px-4 py-1.5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action rounded-lg select-none',
              isActive
                ? 'text-text-primary font-semibold'
                : 'text-text-body-secondary hover:text-text-primary'
            )}
          >
            {isActive && (
              <motion.div
                layoutId={layoutId}
                transition={segmentedPillTransition}
                className="absolute inset-0 z-[-1] rounded-lg bg-surface shadow-[0_1px_3px_rgba(0,0,0,0.1),0_1px_2px_rgba(0,0,0,0.06)]"
              />
            )}
            <span className="flex items-center gap-1.5">
              {tab.icon && <span className="shrink-0">{tab.icon}</span>}
              {tab.label}
            </span>
          </button>
        );
      })}
    </div>
  );
};
