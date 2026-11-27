import { Shirt } from 'lucide-react'
import { useState } from 'react'
import { recommendFromWardrobe } from '../api'
import { CATEGORY_LABELS } from '../lib/wardrobe'

function hasCoordinates(location) {
  return Boolean(location) && Number.isFinite(location.lat) && Number.isFinite(location.lon)
}

function WardrobeRecommend({ location, items }) {
  const [status, setStatus] = useState('idle')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [requestedItems, setRequestedItems] = useState(null)

  // 추천을 받은 뒤 옷장이 바뀌면 그 결과는 지난 옷장 기준이라 숨긴다
  const isCurrent = requestedItems === items
  const ready = hasCoordinates(location)

  function handleRecommend() {
    setStatus('loading')
    setError('')
    setRequestedItems(items)
    recommendFromWardrobe(location, items)
      .then((body) => {
        setResult(body)
        setStatus('ready')
      })
      .catch((err) => {
        setError(err.message)
        setStatus('error')
      })
  }

  return (
    <div className="mt-4 border-t border-slate-200 pt-4 dark:border-slate-700">
      <button
        type="button"
        onClick={handleRecommend}
        disabled={!ready || status === 'loading'}
        className="flex items-center gap-1 rounded-xl border border-sky-600 px-3 py-2 text-sm font-medium text-sky-700 hover:bg-sky-50 disabled:cursor-not-allowed disabled:opacity-50 dark:text-sky-300 dark:hover:bg-sky-950"
      >
        <Shirt aria-hidden="true" className="size-4" />
        {status === 'loading' ? '고르는 중...' : '내 옷장에서 오늘 옷 고르기'}
      </button>
      {!ready && (
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          위치를 정하면 오늘 날씨에 맞는 옷을 옷장에서 골라 드려요.
        </p>
      )}

      {isCurrent && status === 'error' && (
        <p role="alert" className="mt-2 text-sm text-rose-600 dark:text-rose-300">
          {error}
        </p>
      )}

      {isCurrent && status === 'ready' && result && (
        <div aria-label="옷장 추천" className="mt-3">
          <p className="font-semibold">{result.summary}</p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {result.items.map((item) => (
              <li
                key={item.id ?? `${item.category}-${item.name}`}
                className="rounded-xl bg-slate-100 px-3 py-1.5 text-sm dark:bg-slate-700"
              >
                <span className="mr-1.5 text-slate-500 dark:text-slate-400">
                  {CATEGORY_LABELS[item.category] ?? item.category}
                </span>
                <span className="font-medium">{item.name}</span>
                {!item.id && (
                  <span className="ml-1.5 text-xs text-amber-700 dark:text-amber-300">옷장에 없는 옷</span>
                )}
              </li>
            ))}
          </ul>
          {result.tips?.length > 0 && (
            <ul className="mt-2 space-y-1 text-sm text-slate-600 dark:text-slate-300">
              {result.tips.map((tip) => (
                <li key={tip}>{tip}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}

export default WardrobeRecommend
