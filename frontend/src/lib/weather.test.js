import { Cloud, CloudRain, Moon, Sun } from 'lucide-react'
import { describe, expect, test } from 'vitest'
import { conditionIcon, conditionLabel } from './weather'

describe('conditionLabel', () => {
  test.each([
    [800, '맑음'],
    [804, '흐림'],
    [501, '비'],
    [503, '강한 비'],
    [521, '소나기'],
    [211, '뇌우'],
    [612, '진눈깨비'],
    [741, '안개'],
    [null, '알 수 없음'],
  ])('%s -> %s', (code, label) => {
    expect(conditionLabel(code)).toBe(label)
  })
})

describe('conditionIcon', () => {
  test('clear sky follows day and night', () => {
    expect(conditionIcon(800, true)).toBe(Sun)
    expect(conditionIcon(800, false)).toBe(Moon)
  })

  test('rain group uses the rain icon', () => {
    expect(conditionIcon(502)).toBe(CloudRain)
  })

  test('unknown code falls back to a cloud', () => {
    expect(conditionIcon(null)).toBe(Cloud)
  })
})
