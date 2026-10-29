// 위치 권한을 거부한 사용자가 매번 다시 검색하지 않도록 마지막에 고른 지역만 브라우저에 남긴다
const KEY = 'airfit.lastRegion'

export function loadSavedRegion() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY))
    if (saved && Number.isFinite(saved.lat) && Number.isFinite(saved.lon)) return saved
  } catch {
    // 저장소를 못 쓰는 환경(사생활 보호 모드 등)이면 저장 없이 동작한다
  }
  return null
}

export function saveRegion(region) {
  try {
    const { name, fullName, lat, lon } = region
    localStorage.setItem(KEY, JSON.stringify({ name, fullName, lat, lon }))
  } catch {
    // 위와 같음
  }
}
