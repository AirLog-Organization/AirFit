// 브라우저는 우리 백엔드 API만 부른다. 명세는 docs/api.md

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message)
    this.status = status
    this.code = code
  }
}

const FALLBACK_MESSAGE = '정보를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.'

async function getJson(path, params, signal) {
  const query = new URLSearchParams(params).toString()
  let response
  try {
    response = await fetch(`${path}?${query}`, { signal })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError(0, 'network_error', '인터넷 연결을 확인해 주세요.')
  }

  const body = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(
      response.status,
      body?.error ?? 'unknown_error',
      body?.message ?? FALLBACK_MESSAGE,
    )
  }
  return body
}

export function fetchConditions({ lat, lon }, signal) {
  return getJson('/api/conditions', { lat, lon }, signal)
}

export async function searchRegions(q, signal) {
  const body = await getJson('/api/regions', { q }, signal)
  return body.regions
}
