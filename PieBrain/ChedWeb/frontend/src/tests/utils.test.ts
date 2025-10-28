/**
 * Basic component tests
 */
import { describe, it, expect } from 'vitest'
import { formatLatency, formatBatteryVoltage } from '../lib/utils'

describe('formatLatency', () => {
  it('should format null latency', () => {
    const result = formatLatency(null)
    expect(result.value).toBe('--')
    expect(result.color).toBe('text-gray-400')
  })

  it('should format low latency with green color', () => {
    const result = formatLatency(50)
    expect(result.value).toBe('50ms')
    expect(result.color).toBe('text-green-500')
  })

  it('should format medium latency with yellow color', () => {
    const result = formatLatency(150)
    expect(result.value).toBe('150ms')
    expect(result.color).toBe('text-yellow-500')
  })

  it('should format high latency with red color', () => {
    const result = formatLatency(350)
    expect(result.value).toBe('350ms')
    expect(result.color).toBe('text-red-500')
  })
})

describe('formatBatteryVoltage', () => {
  it('should format null voltage', () => {
    const result = formatBatteryVoltage(null)
    expect(result.value).toBe('--')
    expect(result.color).toBe('text-gray-400')
    expect(result.percentage).toBe(0)
  })

  it('should format full battery with green color', () => {
    const result = formatBatteryVoltage(8.4)
    expect(result.value).toBe('8.4V')
    expect(result.color).toBe('text-green-500')
    expect(result.percentage).toBe(100)
  })

  it('should format low battery with red color', () => {
    const result = formatBatteryVoltage(6.6)
    expect(result.value).toBe('6.6V')
    expect(result.color).toBe('text-red-500')
    expect(result.percentage).toBeLessThan(15)
  })
})
