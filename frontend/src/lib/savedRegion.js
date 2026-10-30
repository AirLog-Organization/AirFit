// 위치 권한을 거부한 사용자가 매번 다시 검색하지 않도록 고른 지역을 브라우저에 남긴다
// lastRegion은 첫 화면에서 바로 조회할 지역, recentRegions는 검색창에 보여 줄 최근 목록이다
const LAST_KEY = 'airfit.lastRegion'
const RECENT_KEY = 'airfit.recentRegions'
const RECENT_LIMIT = 5

function isRegion(value) {
  return Boolean(value) && Number.isFinite(value.lat) && Number.isFinite(value.lon)
}

function pick({ name, fullName, lat, lon }) {
  return { name, fullName, lat, lon }
}

function read(key) {
  try {
    return JSON.parse(localStorage.getItem(key))
  } catch {
    // 저장소를 못 쓰는 환경(사생활 보호 모드 등)이면 저장 없이 동작한다
    return null
  }
}

function write(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // 위와 같음
  }
}

export function loadSavedRegion() {
  const saved = read(LAST_KEY)
  return isRegion(saved) ? saved : null
}

export function loadRecentRegions() {
  const recent = read(RECENT_KEY)
  return Array.isArray(recent) ? recent.filter(isRegion) : []
}

// 같은 지역을 다시 고르면 맨 앞으로 옮기고, 최대 5개만 남긴다
export function saveRegion(region) {
  const saved = pick(region)
  write(LAST_KEY, saved)
  const others = loadRecentRegions().filter((r) => r.fullName !== saved.fullName)
  write(RECENT_KEY, [saved, ...others].slice(0, RECENT_LIMIT))
}

export function clearRecentRegions() {
  try {
    localStorage.removeItem(RECENT_KEY)
  } catch {
    // 위와 같음
  }
}
