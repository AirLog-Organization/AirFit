// 대기질과 생활지수 모두 1이 가장 좋고 4가 가장 나쁘다 (docs/api.md)
export const AIR_GRADE_LABELS = { 1: '좋음', 2: '보통', 3: '나쁨', 4: '매우나쁨' }

const GRADE_STYLES = {
  1: 'bg-sky-100 text-sky-800',
  2: 'bg-emerald-100 text-emerald-800',
  3: 'bg-amber-100 text-amber-800',
  4: 'bg-rose-100 text-rose-800',
}

const UNKNOWN_STYLE = 'bg-slate-100 text-slate-500'

export function gradeStyle(grade) {
  return GRADE_STYLES[grade] ?? UNKNOWN_STYLE
}
