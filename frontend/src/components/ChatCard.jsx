import { Bot, Send } from 'lucide-react'
import { useState } from 'react'
import { askChat } from '../api'
import Card from './Card'

const MESSAGE_MAX = 200

function hasCoordinates(location) {
  return Boolean(location) && Number.isFinite(location.lat) && Number.isFinite(location.lon)
}

function ChatCard({ location }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const ready = hasCoordinates(location)

  function handleSubmit(event) {
    event.preventDefault()
    const question = input.trim()
    if (question === '' || sending || !ready) return

    setMessages((prev) => [...prev, { role: 'user', text: question }])
    setInput('')
    setSending(true)
    askChat(location, question)
      .then((body) => {
        setMessages((prev) => [...prev, { role: 'bot', text: body.answer, source: body.source }])
      })
      .catch((err) => {
        setMessages((prev) => [...prev, { role: 'error', text: err.message }])
      })
      .finally(() => setSending(false))
  }

  return (
    <Card title="날씨 챗봇">
      {messages.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">
          "오늘 뭐 입어?", "우산 챙겨야 해?"처럼 물어보세요. 오늘 날씨와 대기질을 바탕으로 답해 드려요.
        </p>
      ) : (
        <ul aria-label="대화" className="space-y-2">
          {messages.map((message, i) => (
            <li key={i} className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
              <div
                className={
                  message.role === 'user'
                    ? 'max-w-[85%] rounded-2xl bg-sky-600 px-3 py-2 text-sm text-white'
                    : message.role === 'error'
                      ? 'max-w-[85%] rounded-2xl bg-rose-50 px-3 py-2 text-sm text-rose-800 dark:bg-rose-950 dark:text-rose-200'
                      : 'max-w-[85%] rounded-2xl bg-slate-100 px-3 py-2 text-sm dark:bg-slate-700'
                }
              >
                {message.source === 'llm' && (
                  <span className="mb-1 flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                    <Bot aria-hidden="true" className="size-3.5" />
                    AI 답
                  </span>
                )}
                {message.text}
              </div>
            </li>
          ))}
        </ul>
      )}
      {sending && (
        <p role="status" className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          답을 만들고 있어요...
        </p>
      )}

      <form onSubmit={handleSubmit} aria-label="질문하기" className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          maxLength={MESSAGE_MAX}
          disabled={!ready}
          aria-label="질문"
          placeholder={ready ? '오늘 뭐 입어?' : '위치를 먼저 정해 주세요'}
          className="min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm disabled:opacity-50 dark:border-slate-600 dark:bg-slate-900"
        />
        <button
          type="submit"
          disabled={!ready || sending || input.trim() === ''}
          aria-label="보내기"
          className="rounded-xl bg-sky-600 px-3 py-2 text-white hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Send aria-hidden="true" className="size-4" />
        </button>
      </form>
    </Card>
  )
}

export default ChatCard
