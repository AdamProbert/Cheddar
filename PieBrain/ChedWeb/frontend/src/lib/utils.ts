import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Utility for merging Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format latency in milliseconds with color indicator
 */
export function formatLatency(latency: number | null): {
  value: string
  color: string
} {
  if (latency === null) {
    return { value: '--', color: 'text-gray-400' }
  }

  const value = `${Math.round(latency)}ms`
  let color = 'text-green-500'

  if (latency > 100) color = 'text-yellow-500'
  if (latency > 200) color = 'text-orange-500'
  if (latency > 300) color = 'text-red-500'

  return { value, color }
}

/**
 * Format battery voltage with color indicator
 */
export function formatBatteryVoltage(voltage: number | null): {
  value: string
  color: string
  percentage: number
} {
  if (voltage === null) {
    return { value: '--', color: 'text-gray-400', percentage: 0 }
  }

  // Assuming 2S LiPo: 8.4V full, 6.4V empty
  const min = 6.4
  const max = 8.4
  const percentage = Math.max(0, Math.min(100, ((voltage - min) / (max - min)) * 100))

  const value = `${voltage.toFixed(1)}V`
  let color = 'text-green-500'

  if (percentage < 50) color = 'text-yellow-500'
  if (percentage < 25) color = 'text-orange-500'
  if (percentage < 10) color = 'text-red-500'

  return { value, color, percentage }
}
