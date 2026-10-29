import { render, screen, within } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import HourlyCard from './HourlyCard'

// jsdom에는 canvas가 없어서 그래프는 받은 데이터만 확인한다
vi.mock('react-chartjs-2', () => ({
  Chart: ({ data, ...props }) => (
    <div role="img" aria-label={props['aria-label']} data-labels={data.labels.join(',')} />
  ),
}))

const hourly = [
  { time: '2026-10-29T15:00:00+09:00', temp: 15.1, feelsLike: 14, pop: 10, precipitation: 0, conditionCode: 801, isDay: true },
  { time: '2026-10-29T18:00:00+09:00', temp: 12.6, feelsLike: 11.2, pop: 40, precipitation: 0, conditionCode: 500, isDay: false },
  { time: '2026-10-30T00:00:00+09:00', temp: 9.4, feelsLike: 8, pop: 0, precipitation: 0, conditionCode: 800, isDay: false },
]

test('labels each slot by Korean hour', () => {
  render(<HourlyCard hourly={hourly} />)

  const chart = screen.getByRole('img', { name: /기온과 강수 확률/ })
  expect(chart.dataset.labels).toBe('15시,18시,0시')
})

test('lists temperature and rain chance for each slot', () => {
  render(<HourlyCard hourly={hourly} />)

  const slots = within(screen.getByRole('list', { name: '시간대별 날씨' })).getAllByRole('listitem')
  expect(slots).toHaveLength(3)
  expect(slots[1]).toHaveTextContent('18시13°40%')
})

test('shows a message when there is no forecast', () => {
  render(<HourlyCard hourly={null} />)

  expect(screen.getByText('시간대별 예보가 없어요.')).toBeInTheDocument()
})
