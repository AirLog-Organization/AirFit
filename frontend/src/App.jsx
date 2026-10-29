import { LocateFixed, MapPin, RotateCw, Search } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { fetchConditions } from './api'
import AirCard from './components/AirCard'
import IndexCards from './components/IndexCards'
import RegionSearch from './components/RegionSearch'
import WeatherCard from './components/WeatherCard'
import { loadSavedRegion, saveRegion } from './lib/savedRegion'

const GEO_OPTIONS = { timeout: 10_000, maximumAge: 10 * 60 * 1000 }

function hasGeolocation() {
  return typeof navigator !== 'undefined' && 'geolocation' in navigator
}

// 첫 화면: 위치 권한을 먼저 묻고, 거부하면 마지막에 고른 지역, 그것도 없으면 지역 검색을 띄운다
function initialState() {
  if (hasGeolocation()) return { status: 'locating', location: null }
  const saved = loadSavedRegion()
  if (saved) return { status: 'loading', location: { ...saved, source: 'region' } }
  return { status: 'need-location', location: null }
}

function App() {
  const [initial] = useState(initialState)
  const [status, setStatus] = useState(initial.status)
  const [location, setLocation] = useState(initial.location)
  const [conditions, setConditions] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [notice, setNotice] = useState('')
  const [searchOpen, setSearchOpen] = useState(initial.status === 'need-location')
  const controller = useRef(null)
  // 위치 확인 중에 사용자가 지역을 고르면 늦게 온 위치 결과가 그 선택을 덮지 않도록 요청마다 번호를 붙인다
  const positionRequest = useRef(0)

  function requestConditions(target) {
    controller.current?.abort()
    controller.current = new AbortController()
    fetchConditions(target, controller.current.signal)
      .then((body) => {
        setConditions(body)
        setStatus('ready')
      })
      .catch((error) => {
        if (error.name === 'AbortError') return
        setErrorMessage(error.message)
        setStatus('error')
        // 해외 좌표처럼 위치 자체가 문제면 바로 지역을 고를 수 있게 한다
        if (error.code === 'invalid_params') setSearchOpen(true)
      })
  }

  function load(target) {
    setLocation(target)
    setStatus('loading')
    setErrorMessage('')
    requestConditions(target)
  }

  function fallBack(message) {
    setNotice(message)
    const saved = loadSavedRegion()
    if (saved) {
      load({ ...saved, source: 'region' })
    } else {
      setStatus('need-location')
      setSearchOpen(true)
    }
  }

  function requestPosition(failMessage) {
    const id = ++positionRequest.current
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        if (id !== positionRequest.current) return
        load({ lat: coords.latitude, lon: coords.longitude, source: 'gps' })
      },
      () => {
        if (id !== positionRequest.current) return
        fallBack(failMessage)
      },
      GEO_OPTIONS,
    )
  }

  function locate() {
    controller.current?.abort()
    setNotice('')
    setStatus('locating')
    requestPosition('위치를 확인하지 못해 지역 검색으로 보여 드려요.')
  }

  function selectRegion(region) {
    positionRequest.current += 1
    saveRegion(region)
    setSearchOpen(false)
    setNotice('')
    load({ ...region, source: 'region' })
  }

  useEffect(() => {
    if (initial.status === 'locating') {
      requestPosition('위치 권한이 없어 지역 검색으로 보여 드려요.')
    } else if (initial.status === 'loading') {
      requestConditions(initial.location)
    }
    return () => controller.current?.abort()
    // 첫 화면에서 한 번만 실행한다
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const placeName =
    (status === 'ready' && conditions?.location?.fullName) ||
    location?.fullName ||
    (location?.source === 'gps' ? '현재 위치' : '위치를 골라 주세요')

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <main className="mx-auto flex max-w-xl flex-col gap-4 p-4 sm:p-6">
        <header className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="text-2xl font-bold">AirFit</h1>
            <p className="flex items-center gap-1 text-sm text-slate-600">
              <MapPin aria-hidden="true" className="size-4" />
              <span data-testid="place-name">{placeName}</span>
            </p>
          </div>
          <div className="flex gap-2">
            {hasGeolocation() && (
              <button
                type="button"
                onClick={locate}
                className="flex items-center gap-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm hover:bg-slate-100"
              >
                <LocateFixed aria-hidden="true" className="size-4" />
                현재 위치
              </button>
            )}
            <button
              type="button"
              onClick={() => setSearchOpen((open) => !open)}
              aria-expanded={searchOpen}
              className="flex items-center gap-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm hover:bg-slate-100"
            >
              <Search aria-hidden="true" className="size-4" />
              지역 검색
            </button>
          </div>
        </header>

        {notice && <p className="rounded-xl bg-sky-50 px-4 py-2 text-sm text-sky-800">{notice}</p>}

        {searchOpen && (
          <RegionSearch
            onSelect={selectRegion}
            onCancel={location ? () => setSearchOpen(false) : undefined}
          />
        )}

        {(status === 'locating' || status === 'loading') && (
          <p role="status" className="py-10 text-center text-slate-500">
            {status === 'locating' ? '위치를 확인하고 있어요...' : '날씨와 대기질을 불러오고 있어요...'}
          </p>
        )}

        {status === 'error' && (
          <div role="alert" className="rounded-2xl bg-rose-50 p-4 text-rose-800">
            <p>{errorMessage}</p>
            {location && (
              <button
                type="button"
                onClick={() => load(location)}
                className="mt-2 flex items-center gap-1 text-sm font-medium underline"
              >
                <RotateCw aria-hidden="true" className="size-4" />
                다시 시도
              </button>
            )}
          </div>
        )}

        {status === 'ready' && conditions && (
          <>
            {conditions.warnings?.length > 0 && (
              <ul className="rounded-xl bg-amber-50 px-4 py-2 text-sm text-amber-800">
                {conditions.warnings.map((warning, i) => (
                  <li key={i}>{warning.message}</li>
                ))}
              </ul>
            )}
            <WeatherCard weather={conditions.weather} />
            <AirCard air={conditions.air} />
            <IndexCards indices={conditions.indices} />
          </>
        )}

        {/* 이용 조건상 필수 출처 표기 (README의 데이터 출처와 이용 조건) */}
        <footer className="pt-2 text-center text-xs text-slate-500">
          <p>출처: 한국환경공단 에어코리아</p>
          <p>
            Weather data provided by{' '}
            <a
              href="https://openweathermap.org/"
              target="_blank"
              rel="noreferrer"
              className="underline"
            >
              OpenWeather
            </a>
          </p>
        </footer>
      </main>
    </div>
  )
}

export default App
