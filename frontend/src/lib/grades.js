// 대기질과 생활지수 모두 1이 가장 좋고 4가 가장 나쁘다 (docs/api.md)
export const AIR_GRADE_LABELS = { 1: '좋음', 2: '보통', 3: '나쁨', 4: '매우나쁨' }

const GRADE_STYLES = {
  1: 'bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-100',
  2: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-100',
  3: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-100',
  4: 'bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-100',
}

const UNKNOWN_STYLE = 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-300'

export function gradeStyle(grade) {
  return GRADE_STYLES[grade] ?? UNKNOWN_STYLE
}
