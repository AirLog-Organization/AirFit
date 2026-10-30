import { Clock, MapPin, Search } from 'lucide-react'
import { useEffect, useId, useRef, useState } from 'react'
import { searchRegions } from '../api'
import { clearRecentRegions, loadRecentRegions } from '../lib/savedRegion'

const DEBOUNCE_MS = 300

// 글자를 칠 때마다 부르지 않도록 입력이 멈춘 뒤 검색한다
// 검색어가 비어 있으면 최근에 고른 지역을 보여 주고, 결과는 마우스와 키보드(↑↓, Enter, Esc) 모두로 고른다
function RegionSearch({ onSelect, onCancel }) {
  const inputId = useId()
  const listId = useId()
  const [query, setQuery] = useState('')
  const [regions, setRegions] = useState([])
  const [recent, setRecent] = useState(loadRecentRegions)
  const [status, setStatus] = useState('idle')
  const [errorMessage, setErrorMessage] = useState('')
  const [activeIndex, setActiveIndex] = useState(-1)
  const timer = useRef(null)
  const controller = useRef(null)

  useEffect(
    () => () => {
      clearTimeout(timer.current)
      controller.current?.abort()
    },
    [],
  )

  const showingRecent = !query.trim()
  const options = showingRecent ? recent : regions
  const optionId = (index) => `${listId}-option-${index}`

  function search(q) {
    controller.current?.abort()
    controller.current = new AbortController()
    setStatus('loading')
    searchRegions(q, controller.current.signal)
      .then((found) => {
        setRegions(found)
        setActiveIndex(-1)
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
    setActiveIndex(-1)
    clearTimeout(timer.current)
    if (!value.trim()) {
      controller.current?.abort()
      setRegions([])
      setStatus('idle')
      return
    }
    timer.current = setTimeout(() => search(value.trim()), DEBOUNCE_MS)
  }

  function handleKeyDown(event) {
    if (event.key === 'ArrowDown' && options.length > 0) {
      event.preventDefault()
      setActiveIndex((i) => (i + 1) % options.length)
    } else if (event.key === 'ArrowUp' && options.length > 0) {
      event.preventDefault()
      setActiveIndex((i) => (i <= 0 ? options.length - 1 : i - 1))
    } else if (event.key === 'Enter') {
      // 고른 항목이 없어도 결과가 하나뿐이면 그것으로 정한다
      const target = options[activeIndex] ?? (options.length === 1 ? options[0] : null)
      if (target) {
        event.preventDefault()
        onSelect(target)
      }
    } else if (event.key === 'Escape') {
      if (query) {
        handleChange({ target: { value: '' } })
      } else {
        onCancel?.()
      }
    }
  }

  function handleClearRecent() {
    clearRecentRegions()
    setRecent([])
    setActiveIndex(-1)
  }

  const Icon = showingRecent ? Clock : MapPin

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 shadow-sm">
      <label htmlFor={inputId} className="mb-2 block text-sm font-semibold text-slate-500 dark:text-slate-400">
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
            role="combobox"
            aria-expanded={options.length > 0}
            aria-controls={listId}
            aria-autocomplete="list"
            aria-activedescendant={activeIndex >= 0 ? optionId(activeIndex) : undefined}
            value={query}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="예: 강남구, 수원, 월계동"
            autoComplete="off"
            className="w-full rounded-xl border border-slate-300 bg-white py-2 dark:border-slate-600 dark:bg-slate-900 pr-3 pl-9 focus:border-sky-500 focus:outline-none"
          />
        </div>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl px-3 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            닫기
          </button>
        )}
      </div>

      {status === 'loading' && <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">검색 중...</p>}
      {status === 'error' && !showingRecent && (
        <p role="alert" className="mt-3 text-sm text-rose-600 dark:text-rose-400">
          {errorMessage}
        </p>
      )}
      {status === 'done' && !showingRecent && regions.length === 0 && (
        <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">검색 결과가 없어요. 다른 이름으로 찾아보세요.</p>
      )}

      {showingRecent && recent.length > 0 && (
        <div className="mt-3 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span>최근 검색</span>
          <button type="button" onClick={handleClearRecent} className="underline">
            지우기
          </button>
        </div>
      )}
      <ul
        id={listId}
        role="listbox"
        aria-label={showingRecent ? '최근 검색 지역' : '검색 결과'}
        className="mt-2 divide-y divide-slate-100 dark:divide-slate-700"
      >
        {options.map((region, index) => (
          <li
            key={`${region.code ?? ''}-${region.fullName}`}
            id={optionId(index)}
            role="option"
            aria-selected={index === activeIndex}
            onClick={() => onSelect(region)}
            onMouseEnter={() => setActiveIndex(index)}
            className={`flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2 ${
              index === activeIndex ? 'bg-slate-100 dark:bg-slate-700' : ''
            }`}
          >
            <Icon aria-hidden="true" className="size-4 shrink-0 text-slate-400" />
            {region.fullName}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default RegionSearch
