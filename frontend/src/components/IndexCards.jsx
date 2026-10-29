import { Footprints, Shirt, ShieldPlus, Wind } from 'lucide-react'
import { gradeStyle } from '../lib/grades'

const INDICES = [
  { key: 'outing', name: '외출', Icon: Footprints },
  { key: 'mask', name: '마스크', Icon: ShieldPlus },
  { key: 'ventilation', name: '환기', Icon: Wind },
  { key: 'laundry', name: '빨래', Icon: Shirt },
]

// 등급 이름(label)은 지수마다 달라서 서버가 준 값을 그대로 쓴다
function IndexCards({ indices }) {
  return (
    <section aria-label="생활지수">
      <h2 className="mb-3 text-sm font-semibold text-slate-500 dark:text-slate-400">생활지수</h2>
      <ul className="grid grid-cols-2 gap-3">
        {INDICES.map(({ key, name, Icon }) => {
          const index = indices?.[key]
          return (
            <li
              key={key}
              aria-label={`${name} 지수`}
              className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 font-medium">
                  <Icon aria-hidden="true" className="size-4 text-slate-500 dark:text-slate-400" />
                  {name}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${gradeStyle(index?.grade)}`}
                >
                  {index?.label ?? '준비 중'}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                {index?.summary ?? '산출 기준을 정리하고 있어요.'}
              </p>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

export default IndexCards
