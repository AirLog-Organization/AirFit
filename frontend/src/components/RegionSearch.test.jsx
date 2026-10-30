import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { saveRegion } from '../lib/savedRegion'
import { jsonResponse, regions } from '../test/fixtures'
import RegionSearch from './RegionSearch'

beforeEach(() => {
  localStorage.clear()
  vi.stubGlobal('fetch', vi.fn(() => jsonResponse({ regions })))
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function input() {
  return screen.getByRole('combobox', { name: '지역 검색' })
}

test('shows recently chosen regions, newest first, without duplicates', () => {
  saveRegion(regions[0])
  saveRegion(regions[1])
  saveRegion(regions[0])

  render(<RegionSearch onSelect={() => {}} />)

  const recent = screen.getByRole('listbox', { name: '최근 검색 지역' })
  expect(within(recent).getAllByRole('option').map((o) => o.textContent)).toEqual([
    '서울 강남구',
    '경기 수원시',
  ])
})

test('keeps at most five recent regions', () => {
  for (let i = 0; i < 7; i++) {
    saveRegion({ ...regions[0], fullName: `지역 ${i}` })
  }

  render(<RegionSearch onSelect={() => {}} />)

  expect(screen.getAllByRole('option')).toHaveLength(5)
  expect(screen.getAllByRole('option')[0]).toHaveTextContent('지역 6')
})

test('clears recent regions', async () => {
  const user = userEvent.setup()
  saveRegion(regions[0])

  render(<RegionSearch onSelect={() => {}} />)
  await user.click(screen.getByRole('button', { name: '지우기' }))

  expect(screen.queryAllByRole('option')).toHaveLength(0)
  expect(localStorage.getItem('airfit.recentRegions')).toBeNull()
})

test('picks a search result with arrow keys and Enter', async () => {
  const user = userEvent.setup()
  const onSelect = vi.fn()

  render(<RegionSearch onSelect={onSelect} />)
  await user.type(input(), '강남')
  await screen.findByRole('option', { name: '서울 강남구' })

  await user.keyboard('{ArrowDown}{ArrowDown}')
  expect(screen.getByRole('option', { name: '경기 수원시' })).toHaveAttribute('aria-selected', 'true')
  expect(input()).toHaveAttribute('aria-activedescendant', screen.getByRole('option', { name: '경기 수원시' }).id)

  await user.keyboard('{ArrowDown}')
  expect(screen.getByRole('option', { name: '서울 강남구' })).toHaveAttribute('aria-selected', 'true')

  await user.keyboard('{Enter}')
  expect(onSelect).toHaveBeenCalledWith(regions[0])
})

test('Enter picks the only result without moving the cursor', async () => {
  const user = userEvent.setup()
  const onSelect = vi.fn()
  vi.stubGlobal('fetch', vi.fn(() => jsonResponse({ regions: [regions[1]] })))

  render(<RegionSearch onSelect={onSelect} />)
  await user.type(input(), '수원')
  await screen.findByRole('option', { name: '경기 수원시' })
  await user.keyboard('{Enter}')

  expect(onSelect).toHaveBeenCalledWith(regions[1])
})

test('Escape clears the query first, then closes', async () => {
  const user = userEvent.setup()
  const onCancel = vi.fn()

  render(<RegionSearch onSelect={() => {}} onCancel={onCancel} />)
  await user.type(input(), '강남')
  await user.keyboard('{Escape}')
  expect(input()).toHaveValue('')
  expect(onCancel).not.toHaveBeenCalled()

  await user.keyboard('{Escape}')
  expect(onCancel).toHaveBeenCalled()
})
