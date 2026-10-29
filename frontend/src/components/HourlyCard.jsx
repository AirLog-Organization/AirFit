import {
  BarController,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { Chart } from 'react-chartjs-2'
import Card from './Card'
import ConditionIcon from './ConditionIcon'

// 쓰는 요소만 등록해 번들을 줄인다
ChartJS.register(
  BarController,
  BarElement,
  CategoryScale,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
)

function hourLabel(iso) {
  const hour = Number(
    new Date(iso).toLocaleString('en-US', { hour: 'numeric', hour12: false, timeZone: 'Asia/Seoul' }),
  )
  return `${hour % 24}시`
}

function chartColors(isDark) {
  return isDark
    ? { temp: '#fb923c', feels: '#fdba74', pop: 'rgba(56, 189, 248, 0.35)', grid: '#334155', text: '#cbd5e1' }
    : { temp: '#ea580c', feels: '#fb923c', pop: 'rgba(14, 165, 233, 0.25)', grid: '#e2e8f0', text: '#475569' }
}

// 기온은 선, 강수 확률은 막대로 겹쳐 그린다. OpenWeather 무료 예보라 3시간 간격이다
function HourlyCard({ hourly, isDark = false }) {
  if (!hourly?.length) {
    return (
      <Card title="시간대별 예보">
        <p className="text-slate-500 dark:text-slate-400">시간대별 예보가 없어요.</p>
      </Card>
    )
  }

  const colors = chartColors(isDark)
  const labels = hourly.map((item) => hourLabel(item.time))
  const data = {
    labels,
    datasets: [
      {
        type: 'line',
        label: '기온',
        data: hourly.map((item) => item.temp),
        borderColor: colors.temp,
        backgroundColor: colors.temp,
        tension: 0.35,
        yAxisID: 'temp',
      },
      {
        type: 'line',
        label: '체감',
        data: hourly.map((item) => item.feelsLike),
        borderColor: colors.feels,
        backgroundColor: colors.feels,
        borderDash: [4, 4],
        pointRadius: 0,
        tension: 0.35,
        yAxisID: 'temp',
      },
      {
        type: 'bar',
        label: '강수 확률',
        data: hourly.map((item) => item.pop),
        backgroundColor: colors.pop,
        yAxisID: 'pop',
      },
    ],
  }
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { labels: { color: colors.text, boxWidth: 12 } },
      tooltip: {
        callbacks: {
          label: (ctx) =>
            `${ctx.dataset.label} ${ctx.parsed.y}${ctx.dataset.yAxisID === 'pop' ? '%' : '°'}`,
        },
      },
    },
    scales: {
      x: { ticks: { color: colors.text }, grid: { display: false } },
      temp: {
        position: 'left',
        ticks: { color: colors.text, callback: (value) => `${value}°` },
        grid: { color: colors.grid },
      },
      pop: {
        position: 'right',
        min: 0,
        max: 100,
        ticks: { color: colors.text, callback: (value) => `${value}%` },
        grid: { display: false },
      },
    },
  }

  return (
    <Card title="시간대별 예보">
      <div className="h-48">
        <Chart
          type="bar"
          data={data}
          options={options}
          aria-label="앞으로 24시간 기온과 강수 확률 그래프"
          role="img"
        />
      </div>
      <ol aria-label="시간대별 날씨" className="mt-4 grid grid-cols-4 gap-2 text-center text-xs sm:grid-cols-8">
        {hourly.map((item, i) => (
          <li key={item.time}>
            <p className="text-slate-500 dark:text-slate-400">{labels[i]}</p>
            <ConditionIcon
              code={item.conditionCode}
              isDay={item.isDay ?? true}
              className="mx-auto my-1 size-5 text-sky-500"
            />
            <p className="font-medium">{Math.round(item.temp)}°</p>
            <p className="text-sky-600 dark:text-sky-400">{item.pop}%</p>
          </li>
        ))}
      </ol>
    </Card>
  )
}

export default HourlyCard
