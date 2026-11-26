// 3단계 옷장: 사용자가 등록한 옷을 브라우저에만 저장한다 (서버에는 저장하지 않는다)
// 옷 하나의 값은 docs/outfit-rules.md "옷장 추천"의 필드(id, category, name, thickness, waterproof)를 따른다
const KEY = 'airfit.wardrobe'

export const CATEGORIES = ['outer', 'top', 'bottom', 'shoes', 'accessory']
export const THICKNESSES = ['thin', 'medium', 'thick']

export const CATEGORY_LABELS = {
  outer: '겉옷',
  top: '상의',
  bottom: '하의',
  shoes: '신발',
  accessory: '소품',
}

export const THICKNESS_LABELS = {
  thin: '얇음',
  medium: '보통',
  thick: '두꺼움',
}

// 저장된 값이 깨졌거나 예전 모양이면 그 옷만 빼고 읽는다
function isItem(value) {
  return (
    Boolean(value) &&
    typeof value.id === 'string' &&
    CATEGORIES.includes(value.category) &&
    typeof value.name === 'string' &&
    value.name.trim() !== '' &&
    THICKNESSES.includes(value.thickness) &&
    typeof value.waterproof === 'boolean'
  )
}

function save(items) {
  try {
    localStorage.setItem(KEY, JSON.stringify(items))
  } catch {
    // 저장소를 못 쓰는 환경(사생활 보호 모드 등)이면 저장 없이 동작한다
  }
}

export function loadWardrobe() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY))
    return Array.isArray(saved) ? saved.filter(isItem) : []
  } catch {
    return []
  }
}

export function addItem(items, { category, name, thickness, waterproof }) {
  const item = { id: crypto.randomUUID(), category, name: name.trim(), thickness, waterproof }
  const next = [...items, item]
  save(next)
  return next
}

export function removeItem(items, id) {
  const next = items.filter((item) => item.id !== id)
  save(next)
  return next
}

export function updateItem(items, id, { category, name, thickness, waterproof }) {
  const next = items.map((item) =>
    item.id === id ? { ...item, category, name: name.trim(), thickness, waterproof } : item,
  )
  save(next)
  return next
}
