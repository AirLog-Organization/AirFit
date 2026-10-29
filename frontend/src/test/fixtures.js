// docs/api.md의 GET /api/conditions 응답 모양
export const conditions = {
  location: {
    name: '노원구 월계1동',
    fullName: '서울특별시 노원구 월계1동',
    regionCode: '1135056000',
    lat: 37.6199,
    lon: 127.063,
  },
  weather: {
    observedAt: '2026-10-29T14:00:00+09:00',
    temp: 14.2,
    feelsLike: 12.8,
    tempMin: 9.1,
    tempMax: 16.4,
    humidity: 48,
    windSpeed: 3.4,
    clouds: 20,
    precipitation: 0,
    isDay: true,
    condition: { code: 801, main: 'Clouds', description: 'few clouds' },
  },
  air: {
    measuredAt: '2026-10-29T14:00:00+09:00',
    station: { name: '화랑로', distanceKm: 1.1 },
    pm10: { value: 43, grade: 2 },
    pm25: { value: 15, grade: 1 },
    o3: { value: 0.031, grade: 1 },
    khai: { value: 68, grade: 2 },
  },
  indices: { outing: null, mask: null, ventilation: null, laundry: null },
  outfit: null,
  hourly: null,
  warnings: [],
  meta: {
    fetchedAt: '2026-10-29T14:07:12+09:00',
    cached: false,
    sources: ['에어코리아', 'OpenWeatherMap'],
  },
}

export const regions = [
  { code: '1168000000', name: '강남구', fullName: '서울 강남구', lat: 37.5172, lon: 127.0473 },
  { code: '4111000000', name: '수원시', fullName: '경기 수원시', lat: 37.2636, lon: 127.0286 },
]

export function jsonResponse(body, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  )
}
