import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import App from './App'
import { conditions, jsonResponse, regions } from './test/fixtures'

function mockGeolocation(result) {
  const getCurrentPosition = vi.fn((success, failure) => {
    if (result === 'denied') failure({ code: 1 })
    else success({ coords: result })
  })
  // jsdom에는 navigator.geolocation이 없어서 테스트마다 붙였다 뗀다
  Object.defineProperty(navigator, 'geolocation', {
    value: { getCurrentPosition },
    configurable: true,
  })
  return getCurrentPosition
}

function mockApi(routes) {
  const fetchMock = vi.fn((url) => {
    const path = new URL(url, 'http://localhost').pathname
    return routes[path]?.(url) ?? jsonResponse({ error: 'not_found', message: '없는 경로' }, 404)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

beforeEach(() => {
  localStorage.clear()
})

afterEach(() => {
  vi.unstubAllGlobals()
  delete navigator.geolocation
})

test('renders the service name', () => {
  mockGeolocation({ latitude: 37.6199, longitude: 127.063 })
  mockApi({ '/api/conditions': () => new Promise(() => {}) })
  render(<App />)
  expect(screen.getByRole('heading', { name: 'AirFit' })).toBeInTheDocument()
})

test('shows weather and air cards for the current position', async () => {
  mockGeolocation({ latitude: 37.6199, longitude: 127.063 })
  const fetchMock = mockApi({ '/api/conditions': () => jsonResponse(conditions) })

  render(<App />)

  const weather = await screen.findByRole('region', { name: '날씨' })
  expect(within(weather).getByText('14°')).toBeInTheDocument()
  expect(within(weather).getByText('구름 조금')).toBeInTheDocument()

  const air = screen.getByRole('region', { name: '대기질' })
  expect(within(air).getByText('43')).toBeInTheDocument()
  expect(within(air).getByText(/화랑로 측정소/)).toBeInTheDocument()

  expect(screen.getByTestId('place-name')).toHaveTextContent('서울특별시 노원구 월계1동')
  expect(screen.getByText('출처: 한국환경공단 에어코리아')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'OpenWeather' })).toHaveAttribute(
    'href',
    'https://openweathermap.org/',
  )
  expect(fetchMock.mock.calls[0][0]).toBe('/api/conditions?lat=37.6199&lon=127.063')
})

test('life index cards wait for the rules when the server sends null', async () => {
  mockGeolocation({ latitude: 37.6199, longitude: 127.063 })
  mockApi({ '/api/conditions': () => jsonResponse(conditions) })

  render(<App />)

  const mask = await screen.findByRole('listitem', { name: '마스크 지수' })
  expect(within(mask).getByText('준비 중')).toBeInTheDocument()
})

test('shows index grade labels sent by the server', async () => {
  mockGeolocation({ latitude: 37.6199, longitude: 127.063 })
  const indices = {
    ...conditions.indices,
    mask: { grade: 3, label: '권장', summary: '마스크를 챙기세요.' },
  }
  mockApi({ '/api/conditions': () => jsonResponse({ ...conditions, indices }) })

  render(<App />)

  const mask = await screen.findByRole('listitem', { name: '마스크 지수' })
  expect(within(mask).getByText('권장')).toBeInTheDocument()
  expect(within(mask).getByText('마스크를 챙기세요.')).toBeInTheDocument()
})

test('keeps the weather card when only air quality failed', async () => {
  mockGeolocation({ latitude: 37.6199, longitude: 127.063 })
  const partial = {
    ...conditions,
    air: null,
    warnings: [{ source: 'air', message: '대기질 정보를 잠시 불러오지 못했어요.' }],
  }
  mockApi({ '/api/conditions': () => jsonResponse(partial) })

  render(<App />)

  expect(await screen.findByText('대기질 정보를 잠시 불러오지 못했어요.')).toBeInTheDocument()
  expect(screen.getByRole('region', { name: '날씨' })).toBeInTheDocument()
  expect(screen.getByText('대기질 정보가 없어요.')).toBeInTheDocument()
})

test('falls back to region search when location is denied', async () => {
  const user = userEvent.setup()
  mockGeolocation('denied')
  const fetchMock = mockApi({
    '/api/regions': () => jsonResponse({ regions }),
    '/api/conditions': () => jsonResponse(conditions),
  })

  render(<App />)

  expect(screen.getByText(/위치 권한이 없어/)).toBeInTheDocument()
  await user.type(screen.getByLabelText('지역 검색'), '강남')
  await user.click(await screen.findByRole('button', { name: '서울 강남구' }))

  await screen.findByRole('region', { name: '날씨' })
  expect(fetchMock).toHaveBeenLastCalledWith(
    '/api/conditions?lat=37.5172&lon=127.0473',
    expect.anything(),
  )
  expect(JSON.parse(localStorage.getItem('airfit.lastRegion')).fullName).toBe('서울 강남구')
})

test('uses the last chosen region when location is denied again', async () => {
  localStorage.setItem('airfit.lastRegion', JSON.stringify(regions[1]))
  mockGeolocation('denied')
  const fetchMock = mockApi({ '/api/conditions': () => jsonResponse(conditions) })

  render(<App />)

  await screen.findByRole('region', { name: '날씨' })
  expect(fetchMock.mock.calls[0][0]).toBe('/api/conditions?lat=37.2636&lon=127.0286')
})

test('shows the server message and retries on error', async () => {
  const user = userEvent.setup()
  mockGeolocation({ latitude: 37.6199, longitude: 127.063 })
  const fetchMock = mockApi({
    '/api/conditions': vi
      .fn()
      .mockReturnValueOnce(
        jsonResponse(
          { error: 'upstream_error', message: '날씨와 대기질 정보를 잠시 불러오지 못했어요.' },
          502,
        ),
      )
      .mockReturnValueOnce(jsonResponse(conditions)),
  })

  render(<App />)

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('날씨와 대기질 정보를 잠시 불러오지 못했어요.')
  await user.click(within(alert).getByRole('button', { name: '다시 시도' }))

  await screen.findByRole('region', { name: '날씨' })
  expect(fetchMock).toHaveBeenCalledTimes(2)
})

test('opens region search when the position is outside Korea', async () => {
  mockGeolocation({ latitude: 51.5, longitude: -0.1 })
  mockApi({
    '/api/conditions': () =>
      jsonResponse({ error: 'invalid_params', message: '국내 좌표만 조회할 수 있어요.' }, 400),
  })

  render(<App />)

  expect(await screen.findByText('국내 좌표만 조회할 수 있어요.')).toBeInTheDocument()
  expect(screen.getByLabelText('지역 검색')).toBeInTheDocument()
})

test('a late position does not override the region the user picked', async () => {
  const user = userEvent.setup()
  let resolvePosition
  Object.defineProperty(navigator, 'geolocation', {
    value: { getCurrentPosition: (success) => (resolvePosition = success) },
    configurable: true,
  })
  const fetchMock = mockApi({
    '/api/regions': () => jsonResponse({ regions }),
    '/api/conditions': () => jsonResponse(conditions),
  })

  render(<App />)
  await user.click(screen.getByRole('button', { name: '지역 검색' }))
  await user.type(screen.getByLabelText('지역 검색'), '수원')
  await user.click(await screen.findByRole('button', { name: '경기 수원시' }))
  await screen.findByRole('region', { name: '날씨' })

  resolvePosition({ coords: { latitude: 37.6199, longitude: 127.063 } })

  const conditionCalls = fetchMock.mock.calls.filter(([url]) => url.startsWith('/api/conditions'))
  expect(conditionCalls).toHaveLength(1)
  expect(conditionCalls[0][0]).toBe('/api/conditions?lat=37.2636&lon=127.0286')
})
