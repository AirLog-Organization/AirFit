// 브라우저는 우리 백엔드 API만 부른다. 명세는 docs/api.md

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message)
    this.status = status
    this.code = code
  }
}

const FALLBACK_MESSAGE = '정보를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.'

async function request(url, options) {
  let response
  try {
    response = await fetch(url, options)
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError(0, 'network_error', '인터넷 연결을 확인해 주세요.')
  }

  const body = await response.json().catch(() => null)
  if (!response.ok || body === null) {
    throw new ApiError(
      response.status,
      body?.error ?? 'unknown_error',
      body?.message ?? FALLBACK_MESSAGE,
    )
  }
  return body
}

function getJson(path, params, signal) {
  const query = new URLSearchParams(params).toString()
  return request(`${path}?${query}`, { signal })
}

function postJson(path, payload, signal) {
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
}

export function fetchConditions({ lat, lon }, signal) {
  return getJson('/api/conditions', { lat, lon }, signal)
}

export async function searchRegions(q, signal) {
  const body = await getJson('/api/regions', { q }, signal)
  return body.regions
}

// 옷장은 서버에 저장하지 않고, 추천받을 때만 본문으로 보낸다 (docs/outfit-rules.md "옷장 추천")
export function recommendFromWardrobe({ lat, lon }, wardrobe, signal) {
  return postJson('/api/wardrobe/recommend', { lat, lon, wardrobe }, signal)
}
