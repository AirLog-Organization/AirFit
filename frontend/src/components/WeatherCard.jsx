import { conditionLabel } from '../lib/weather'
import Card from './Card'
import ConditionIcon from './ConditionIcon'

function round(value) {
  return value == null ? '-' : Math.round(value)
}

function WeatherCard({ weather }) {
  if (!weather) {
    return (
      <Card title="날씨">
        <p className="text-slate-500">날씨 정보가 없어요.</p>
      </Card>
    )
  }

  const details = [
    ['체감', `${round(weather.feelsLike)}°`],
    ['최저/최고', `${round(weather.tempMin)}° / ${round(weather.tempMax)}°`],
    ['습도', `${weather.humidity ?? '-'}%`],
    ['바람', `${weather.windSpeed ?? '-'}m/s`],
    ['강수(1시간)', `${weather.precipitation ?? 0}mm`],
  ]

  return (
    <Card title="날씨">
      <div className="flex items-center gap-4">
        <ConditionIcon
          code={weather.condition?.code}
          isDay={weather.isDay ?? true}
          className="size-14 text-sky-500"
          strokeWidth={1.5}
        />
        <div>
          <p className="text-4xl font-bold">{round(weather.temp)}°</p>
          <p className="text-slate-600">{conditionLabel(weather.condition?.code)}</p>
        </div>
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-3">
        {details.map(([term, value]) => (
          <div key={term}>
            <dt className="text-slate-500">{term}</dt>
            <dd className="font-medium">{value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  )
}

export default WeatherCard
