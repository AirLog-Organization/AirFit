function Card({ title, children, className = '' }) {
  return (
    <section
      aria-label={title}
      className={`rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-5 shadow-sm ${className}`}
    >
      <h2 className="mb-3 text-sm font-semibold text-slate-500 dark:text-slate-400">{title}</h2>
      {children}
    </section>
  )
}

export default Card
