import { Lightbulb } from 'lucide-react'
import Card from './Card'

// category 값은 docs/api.md의 outfit 명세와 3단계 옷장 등록이 함께 쓴다
const CATEGORY_LABELS = {
  outer: '겉옷',
  top: '상의',
  bottom: '하의',
  shoes: '신발',
  accessory: '소품',
}

function OutfitCard({ outfit }) {
  if (!outfit) {
    return (
      <Card title="오늘의 옷차림">
        <p className="text-slate-500 dark:text-slate-400">옷차림 추천 규칙을 준비하고 있어요.</p>
      </Card>
    )
  }

  return (
    <Card title="오늘의 옷차림">
      <p className="text-lg font-semibold">{outfit.summary}</p>
      {outfit.items?.length > 0 && (
        <ul aria-label="추천 옷" className="mt-3 flex flex-wrap gap-2">
          {outfit.items.map((item) => (
            <li
              key={`${item.category}-${item.name}`}
              className="rounded-xl bg-slate-100 px-3 py-1.5 text-sm dark:bg-slate-700"
            >
              <span className="mr-1.5 text-slate-500 dark:text-slate-400">
                {CATEGORY_LABELS[item.category] ?? item.category}
              </span>
              <span className="font-medium">{item.name}</span>
            </li>
          ))}
        </ul>
      )}
      {outfit.tips?.length > 0 && (
        <ul aria-label="옷차림 팁" className="mt-3 space-y-1 text-sm text-slate-600 dark:text-slate-300">
          {outfit.tips.map((tip) => (
            <li key={tip} className="flex gap-1.5">
              <Lightbulb aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-amber-500" />
              {tip}
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

export default OutfitCard
