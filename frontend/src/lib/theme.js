// index.html의 인라인 스크립트도 같은 키와 규칙으로 첫 화면 테마를 정한다 (깜빡임 방지)
const KEY = 'airfit.theme'

export function initialTheme() {
  try {
    const saved = localStorage.getItem(KEY)
    if (saved === 'light' || saved === 'dark') return saved
  } catch {
    // 저장소를 못 쓰면 시스템 설정을 따른다
  }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function applyTheme(theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
}

// 사용자가 직접 고른 경우에만 저장한다. 고르지 않았다면 다음에 열 때도 시스템 설정을 따른다
export function saveTheme(theme) {
  try {
    localStorage.setItem(KEY, theme)
  } catch {
    // 위와 같음
  }
}
