export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return ''
  const mins = Math.max(0, Math.floor((Date.now() - new Date(dateStr).getTime()) / 60000))
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export function formatDateTime(dateStr: string | null): string {
  return dateStr ? new Date(dateStr).toLocaleString() : ''
}
