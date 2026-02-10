function escapeHtml(input) {
  return String(input)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function renderInline(text) {
  let out = escapeHtml(text)
  out = out.replace(/`([^`]+)`/g, '<code>$1</code>')
  out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  out = out.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  out = out.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
  return out
}

export function renderMarkdown(input) {
  if (!input || !String(input).trim()) return ''

  const lines = String(input).replace(/\r\n/g, '\n').split('\n')
  const html = []
  let inUl = false
  let inOl = false

  const closeLists = () => {
    if (inUl) {
      html.push('</ul>')
      inUl = false
    }
    if (inOl) {
      html.push('</ol>')
      inOl = false
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trim()

    if (!line) {
      closeLists()
      html.push('<br />')
      continue
    }

    const heading = line.match(/^(#{1,6})\s+(.+)$/)
    if (heading) {
      closeLists()
      const level = heading[1].length
      html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`)
      continue
    }

    const ul = line.match(/^[-*+]\s+(.+)$/)
    if (ul) {
      if (inOl) {
        html.push('</ol>')
        inOl = false
      }
      if (!inUl) {
        html.push('<ul>')
        inUl = true
      }
      html.push(`<li>${renderInline(ul[1])}</li>`)
      continue
    }

    const ol = line.match(/^\d+\.\s+(.+)$/)
    if (ol) {
      if (inUl) {
        html.push('</ul>')
        inUl = false
      }
      if (!inOl) {
        html.push('<ol>')
        inOl = true
      }
      html.push(`<li>${renderInline(ol[1])}</li>`)
      continue
    }

    closeLists()
    html.push(`<p>${renderInline(line)}</p>`)
  }

  closeLists()
  return html.join('')
}
