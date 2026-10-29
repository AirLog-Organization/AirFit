import { AIR_GRADE_LABELS, gradeStyle } from '../lib/grades'
import Card from './Card'

const POLLUTANTS = [
  { key: 'pm10', name: '미세먼지', unit: '㎍/㎥' },
  { key: 'pm25', name: '초미세먼지', unit: '㎍/㎥' },
  { key: 'o3', name: '오존', unit: 'ppm' },
]

function formatTime(iso) {
  if (!iso) return null
  const date = new Date(iso)
  return date.toLocaleTimeString('ko-KR', {
    hour: 'numeric',
    minute: '2-digit',
    timeZone: 'Asia/Seoul',
  })
}

function AirCard({ air }) {
  if (!air) {
    return (
      <Card title="대기질">
        <p className="text-slate-500 dark:text-slate-400">대기질 정보가 없어요.</p>
      </Card>
    )
  }

  return (
    <Card title="대기질">
      <ul className="grid grid-cols-3 gap-3">
        {POLLUTANTS.map(({ key, name, unit }) => {
          const { value, grade } = air[key] ?? {}
          return (
            <li key={key} className="text-center">
              <p className="text-sm text-slate-500 dark:text-slate-400">{name}</p>
              <p className="my-1 text-lg font-semibold">
                {value ?? '-'}
                <span className="ml-0.5 text-xs font-normal text-slate-500 dark:text-slate-400">{unit}</span>
              </p>
              <span
                className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${gradeStyle(grade)}`}
              >
                {AIR_GRADE_LABELS[grade] ?? '정보 없음'}
              </span>
            </li>
          )
        })}
      </ul>
      {air.station && (
        <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
          {air.station.name} 측정소 ({air.station.distanceKm}km)
          {air.measuredAt && ` · ${formatTime(air.measuredAt)} 측정`}
        </p>
      )}
    </Card>
  )
}

export default AirCard
