import { createElement } from 'react'
import { conditionIcon } from '../lib/weather'

// 날씨 코드마다 아이콘 컴포넌트가 달라서 렌더 중에 고른 컴포넌트를 createElement로 그린다
function ConditionIcon({ code, isDay = true, ...props }) {
  return createElement(conditionIcon(code, isDay), { 'aria-hidden': 'true', ...props })
}

export default ConditionIcon
