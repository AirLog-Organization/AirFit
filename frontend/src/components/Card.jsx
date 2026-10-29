function Card({ title, children, className = '' }) {
  return (
    <section
      aria-label={title}
      className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}
    >
      <h2 className="mb-3 text-sm font-semibold text-slate-500">{title}</h2>
      {children}
    </section>
  )
}

export default Card
