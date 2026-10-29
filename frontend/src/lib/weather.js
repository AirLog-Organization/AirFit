import {
  Cloud,
  CloudDrizzle,
  CloudFog,
  CloudLightning,
  CloudMoon,
  CloudRain,
  CloudSnow,
  CloudSun,
  Cloudy,
  Moon,
  Sun,
  Tornado,
  Wind,
} from 'lucide-react'

// 백엔드는 OpenWeather 날씨 설명을 영어로 넘기므로, 화면 문구와 아이콘은 condition code로 고른다
// 코드 목록: https://openweathermap.org/weather-conditions
const EXACT = {
  500: '약한 비',
  501: '비',
  511: '어는 비',
  600: '약한 눈',
  601: '눈',
  602: '폭설',
  701: '옅은 안개',
  711: '연기',
  721: '연무',
  731: '황사',
  741: '안개',
  751: '모래바람',
  761: '먼지',
  762: '화산재',
  771: '돌풍',
  781: '토네이도',
  800: '맑음',
  801: '구름 조금',
  802: '구름 많음',
  803: '구름 많음',
  804: '흐림',
}

function groupLabel(code) {
  if (code >= 200 && code < 300) return '뇌우'
  if (code >= 300 && code < 400) return '이슬비'
  if (code >= 502 && code <= 504) return '강한 비'
  if (code >= 520 && code < 600) return '소나기'
  if (code >= 611 && code <= 616) return '진눈깨비'
  if (code >= 620 && code < 700) return '소낙눈'
  return '알 수 없음'
}

export function conditionLabel(code) {
  if (code == null) return '알 수 없음'
  return EXACT[code] ?? groupLabel(code)
}

export function conditionIcon(code, isDay = true) {
  if (code == null) return Cloud
  if (code >= 200 && code < 300) return CloudLightning
  if (code >= 300 && code < 400) return CloudDrizzle
  if (code >= 500 && code < 600) return CloudRain
  if (code >= 600 && code < 700) return CloudSnow
  if (code === 771) return Wind
  if (code === 781) return Tornado
  if (code >= 700 && code < 800) return CloudFog
  if (code === 800) return isDay ? Sun : Moon
  if (code === 801) return isDay ? CloudSun : CloudMoon
  if (code === 802) return Cloud
  return Cloudy
}
