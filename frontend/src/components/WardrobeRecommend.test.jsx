import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonResponse } from '../test/fixtures'
import WardrobeRecommend from './WardrobeRecommend'

const LOCATION = { lat: 37.6199, lon: 127.063, source: 'gps' }
const ITEMS = [
  { id: 'w1', category: 'outer', name: '바람막이', thickness: 'thin', waterproof: true },
  { id: 'w2', category: 'top', name: '회색 니트', thickness: 'medium', waterproof: false },
]
const RESULT = {
  summary: '쌀쌀해요. 가벼운 재킷을 걸치세요.',
  items: [
    { id: 'w1', category: 'outer', name: '바람막이' },
    { id: 'w2', category: 'top', name: '회색 니트' },
    { category: 'bottom', name: '청바지' },
  ],
  tips: ['일교차가 10도 이상이에요.'],
}

function mockFetch(response) {
  const fetchMock = vi.fn(() => response)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('WardrobeRecommend', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('위치와 옷장을 보내고, 옷장에 없는 옷을 구분해 보여 준다', async () => {
    const fetchMock = mockFetch(jsonResponse(RESULT))
    const user = userEvent.setup()
    render(<WardrobeRecommend location={LOCATION} items={ITEMS} />)

    await user.click(screen.getByRole('button', { name: '내 옷장에서 오늘 옷 고르기' }))

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/wardrobe/recommend')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ lat: 37.6199, lon: 127.063, wardrobe: ITEMS })

    const result = await screen.findByLabelText('옷장 추천')
    expect(within(result).getByText('쌀쌀해요. 가벼운 재킷을 걸치세요.')).toBeInTheDocument()
    expect(within(result).getByText('바람막이')).toBeInTheDocument()
    expect(within(result).getAllByText('옷장에 없는 옷')).toHaveLength(1)
    expect(within(result).getByText('청바지').parentElement).toHaveTextContent('옷장에 없는 옷')
    expect(within(result).getByText('일교차가 10도 이상이에요.')).toBeInTheDocument()
  })

  it('위치가 없으면 버튼을 막고 안내한다', () => {
    mockFetch(jsonResponse(RESULT))
    render(<WardrobeRecommend location={null} items={ITEMS} />)

    expect(screen.getByRole('button', { name: '내 옷장에서 오늘 옷 고르기' })).toBeDisabled()
    expect(screen.getByText(/위치를 정하면/)).toBeInTheDocument()
  })

  it('서버 오류면 메시지를 보여 준다', async () => {
    mockFetch(jsonResponse({ error: 'upstream_error', message: '날씨 정보를 잠시 불러오지 못해 추천할 수 없어요.' }, 502))
    const user = userEvent.setup()
    render(<WardrobeRecommend location={LOCATION} items={ITEMS} />)

    await user.click(screen.getByRole('button', { name: '내 옷장에서 오늘 옷 고르기' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('날씨 정보를 잠시 불러오지 못해 추천할 수 없어요.')
  })

  it('추천을 받은 뒤 옷장이 바뀌면 지난 결과를 숨긴다', async () => {
    mockFetch(jsonResponse(RESULT))
    const user = userEvent.setup()
    const { rerender } = render(<WardrobeRecommend location={LOCATION} items={ITEMS} />)

    await user.click(screen.getByRole('button', { name: '내 옷장에서 오늘 옷 고르기' }))
    expect(await screen.findByLabelText('옷장 추천')).toBeInTheDocument()

    rerender(<WardrobeRecommend location={LOCATION} items={ITEMS.slice(1)} />)
    expect(screen.queryByLabelText('옷장 추천')).not.toBeInTheDocument()
  })
})
