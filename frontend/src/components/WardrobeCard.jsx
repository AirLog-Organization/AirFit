import { Check, Pencil, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import {
  addItem,
  CATEGORIES,
  CATEGORY_LABELS,
  loadWardrobe,
  removeItem,
  THICKNESSES,
  THICKNESS_LABELS,
  updateItem,
} from '../lib/wardrobe'
import Card from './Card'

const NAME_MAX = 30
const FIELD =
  'rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900'

function WardrobeCard() {
  const [items, setItems] = useState(loadWardrobe)
  const [category, setCategory] = useState('top')
  const [name, setName] = useState('')
  const [thickness, setThickness] = useState('medium')
  const [waterproof, setWaterproof] = useState(false)
  const [error, setError] = useState('')
  const [editingId, setEditingId] = useState(null)

  function handleSubmit(event) {
    event.preventDefault()
    if (name.trim() === '') {
      setError('옷 이름을 적어 주세요.')
      return
    }
    const fields = { category, name, thickness, waterproof }
    if (editingId) {
      setItems(updateItem(items, editingId, fields))
    } else {
      setItems(addItem(items, fields))
    }
    resetForm()
  }

  function resetForm() {
    setEditingId(null)
    setName('')
    setWaterproof(false)
    setError('')
  }

  function startEdit(item) {
    setEditingId(item.id)
    setCategory(item.category)
    setName(item.name)
    setThickness(item.thickness)
    setWaterproof(item.waterproof)
    setError('')
  }

  function handleRemove(id) {
    setItems(removeItem(items, id))
    if (id === editingId) resetForm()
  }

  return (
    <Card title="내 옷장">
      <form onSubmit={handleSubmit} aria-label="옷 추가" className="flex flex-wrap items-end gap-2">
        <label className="flex flex-col gap-1 text-xs text-slate-500 dark:text-slate-400">
          종류
          <select value={category} onChange={(e) => setCategory(e.target.value)} className={FIELD}>
            {CATEGORIES.map((value) => (
              <option key={value} value={value}>
                {CATEGORY_LABELS[value]}
              </option>
            ))}
          </select>
        </label>
        <label className="flex min-w-32 flex-1 flex-col gap-1 text-xs text-slate-500 dark:text-slate-400">
          이름
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={NAME_MAX}
            placeholder="예: 회색 니트"
            className={FIELD}
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-slate-500 dark:text-slate-400">
          두께
          <select value={thickness} onChange={(e) => setThickness(e.target.value)} className={FIELD}>
            {THICKNESSES.map((value) => (
              <option key={value} value={value}>
                {THICKNESS_LABELS[value]}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1 py-2 text-sm">
          <input
            type="checkbox"
            checked={waterproof}
            onChange={(e) => setWaterproof(e.target.checked)}
          />
          방수
        </label>
        <button
          type="submit"
          className="flex items-center gap-1 rounded-xl bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-700"
        >
          {editingId ? (
            <Check aria-hidden="true" className="size-4" />
          ) : (
            <Plus aria-hidden="true" className="size-4" />
          )}
          {editingId ? '수정 완료' : '추가'}
        </button>
        {editingId && (
          <button
            type="button"
            onClick={resetForm}
            className="rounded-xl border border-slate-300 px-3 py-2 text-sm hover:bg-slate-100 dark:border-slate-600 dark:hover:bg-slate-700"
          >
            취소
          </button>
        )}
      </form>
      {error && (
        <p role="alert" className="mt-2 text-sm text-rose-600 dark:text-rose-300">
          {error}
        </p>
      )}

      {items.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
          아직 등록한 옷이 없어요. 가진 옷을 추가하면 옷장 안에서 옷차림을 골라 드릴 수 있어요.
        </p>
      ) : (
        <div className="mt-4 space-y-3">
          {CATEGORIES.map((value) => {
            const group = items.filter((item) => item.category === value)
            if (group.length === 0) return null
            return (
              <div key={value}>
                <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                  {CATEGORY_LABELS[value]}
                </h3>
                <ul aria-label={`${CATEGORY_LABELS[value]} 목록`} className="mt-1 space-y-1">
                  {group.map((item) => (
                    <li
                      key={item.id}
                      className="flex items-center justify-between rounded-xl bg-slate-100 px-3 py-1.5 text-sm dark:bg-slate-700"
                    >
                      <span>
                        <span className="font-medium">{item.name}</span>
                        <span className="ml-1.5 text-slate-500 dark:text-slate-400">
                          {THICKNESS_LABELS[item.thickness]}
                          {item.waterproof && ' · 방수'}
                        </span>
                      </span>
                      <span className="flex gap-1">
                        <button
                          type="button"
                          onClick={() => startEdit(item)}
                          aria-label={`${item.name} 수정`}
                          className="rounded-lg p-1 hover:bg-slate-200 dark:hover:bg-slate-600"
                        >
                          <Pencil aria-hidden="true" className="size-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRemove(item.id)}
                          aria-label={`${item.name} 삭제`}
                          className="rounded-lg p-1 hover:bg-slate-200 dark:hover:bg-slate-600"
                        >
                          <Trash2 aria-hidden="true" className="size-4" />
                        </button>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}

export default WardrobeCard
