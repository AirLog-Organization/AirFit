import { Search } from 'lucide-react'
import { useEffect, useId, useRef, useState } from 'react'
import { searchRegions } from '../api'

const DEBOUNCE_MS = 300

// 글자를 칠 때마다 부르지 않도록 입력이 멈춘 뒤 검색한다
function RegionSearch({ onSelect, onCancel }) {
  const inputId = useId()
  const [query, setQuery] = useState('')
  const [regions, setRegions] = useState([])
  const [status, setStatus] = useState('idle')
  const [errorMessage, setErrorMessage] = useState('')
  const timer = useRef(null)
  const controller = useRef(null)

  useEffect(
    () => () => {
      clearTimeout(timer.current)
      controller.current?.abort()
    },
    [],
  )

  function search(q) {
    controller.current?.abort()
    controller.current = new AbortController()
    setStatus('loading')
    searchRegions(q, controller.current.signal)
      .then((found) => {
        setRegions(found)
        setStatus('done')
      })
      .catch((error) => {
        if (error.name === 'AbortError') return
        setErrorMessage(error.message)
        setStatus('error')
      })
  }

  function handleChange(event) {
    const value = event.target.value
    setQuery(value)
    clearTimeout(timer.current)
    if (!value.trim()) {
      controller.current?.abort()
      setRegions([])
      setStatus('idle')
      return
    }
    timer.current = setTimeout(() => search(value.trim()), DEBOUNCE_MS)
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <label htmlFor={inputId} className="mb-2 block text-sm font-semibold text-slate-500">
        지역 검색
      </label>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search
            aria-hidden="true"
            className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400"
          />
          <input
            id={inputId}
            type="search"
            value={query}
            onChange={handleChange}
            placeholder="예: 강남구, 수원, 월계동"
            autoComplete="off"
            className="w-full rounded-xl border border-slate-300 py-2 pr-3 pl-9 focus:border-sky-500 focus:outline-none"
          />
        </div>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl px-3 text-sm text-slate-600 hover:bg-slate-100"
          >
            닫기
          </button>
        )}
      </div>

      {status === 'loading' && <p className="mt-3 text-sm text-slate-500">검색 중...</p>}
      {status === 'error' && (
        <p role="alert" className="mt-3 text-sm text-rose-600">
          {errorMessage}
        </p>
      )}
      {status === 'done' && regions.length === 0 && (
        <p className="mt-3 text-sm text-slate-500">검색 결과가 없어요. 다른 이름으로 찾아보세요.</p>
      )}
      {regions.length > 0 && (
        <ul aria-label="검색 결과" className="mt-3 divide-y divide-slate-100">
          {regions.map((region) => (
            <li key={`${region.code}-${region.fullName}`}>
              <button
                type="button"
                onClick={() => onSelect(region)}
                className="w-full rounded-lg px-2 py-2 text-left hover:bg-slate-50"
              >
                {region.fullName}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default RegionSearch
