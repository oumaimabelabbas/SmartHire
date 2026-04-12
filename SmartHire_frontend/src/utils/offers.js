export const OFFERS_API_URL = import.meta.env.VITE_OFFERS_API_URL || 'http://localhost:8086/offres'

function normalizeOffersPayload(payload) {
  if (Array.isArray(payload)) {
    return payload
  }

  if (Array.isArray(payload?.content)) {
    return payload.content
  }

  if (Array.isArray(payload?.data)) {
    return payload.data
  }

  return []
}

export async function fetchAllOffers() {
  const attempts = [{ credentials: 'include' }, {}]
  let lastError = null

  for (const attempt of attempts) {
    try {
      const response = await fetch(OFFERS_API_URL, {
        method: 'GET',
        ...attempt,
      })

      if (!response.ok) {
        lastError = new Error(`Erreur chargement offres (${response.status})`)
        continue
      }

      const data = await response.json()
      return normalizeOffersPayload(data)
    } catch (error) {
      lastError = error
    }
  }

  throw lastError ?? new Error('Erreur chargement offres')
}

function asArray(value) {
  if (Array.isArray(value)) {
    return value.filter(Boolean)
  }

  if (typeof value === 'string') {
    return value
      .split(/\n|,/) 
      .map((item) => item.trim())
      .filter(Boolean)
  }

  return []
}

function toLogoSrc(value) {
  if (!value) {
    return ''
  }

  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) {
      return ''
    }

    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      return trimmed
    }

    if (trimmed.startsWith('data:image/')) {
      return trimmed
    }

    if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
      try {
        const parsed = JSON.parse(trimmed)
        return toLogoSrc(parsed)
      } catch {
        return ''
      }
    }

    return `data:image/png;base64,${trimmed}`
  }

  const bytes = Array.isArray(value) ? value : Array.isArray(value?.data) ? value.data : null
  if (!bytes || !bytes.length) {
    return ''
  }

  const binary = bytes
    .map((byte) => {
      const unsignedByte = Number(byte)
      return String.fromCharCode(((unsignedByte % 256) + 256) % 256)
    })
    .join('')
  return `data:image/png;base64,${btoa(binary)}`
}

export function mapOfferForCandidate(rawOffer) {
  const title = rawOffer?.titre ?? rawOffer?.title ?? ''
  const company = rawOffer?.entreprise ?? rawOffer?.company ?? ''
  const location = rawOffer?.localisation ?? rawOffer?.location ?? ''
  const contractType = rawOffer?.typeContrat ?? rawOffer?.contractType ?? ''
  const roleSummary = rawOffer?.aProposRole ?? rawOffer?.roleSummary ?? rawOffer?.description ?? ''
  const responsibilities = asArray(rawOffer?.responsabilites ?? rawOffer?.responsibilities)
  const requiredSkills = asArray(rawOffer?.profilRecherche ?? rawOffer?.requiredSkills)
  const logoSrc = toLogoSrc(rawOffer?.logoEntreprise ?? rawOffer?.logoSrc)

  return {
    id: rawOffer?.id ?? Date.now(),
    title,
    company,
    location,
    contractType,
    domain: rawOffer?.domain ?? rawOffer?.modeTravail ?? '',
    roleSummary,
    responsibilities,
    requiredSkills,
    logoSrc,
  }
}

export function mapOfferForRecruiter(rawOffer) {
  return {
    id: rawOffer?.id ?? Date.now(),
    titre: rawOffer?.titre ?? rawOffer?.title ?? '',
    description: rawOffer?.description ?? rawOffer?.aProposRole ?? '',
    entreprise: rawOffer?.entreprise ?? rawOffer?.company ?? '',
    localisation: rawOffer?.localisation ?? rawOffer?.location ?? '',
    typeContrat: rawOffer?.typeContrat ?? rawOffer?.contractType ?? '',
    modeTravail: rawOffer?.modeTravail ?? rawOffer?.domain ?? '',
    actif: rawOffer?.actif ?? true,
    aProposEntreprise: rawOffer?.aProposEntreprise ?? '',
    aProposRole: rawOffer?.aProposRole ?? rawOffer?.description ?? '',
    responsabilites: asArray(rawOffer?.responsabilites ?? rawOffer?.responsibilities),
    profilRecherche: asArray(rawOffer?.profilRecherche ?? rawOffer?.requiredSkills),
    scoreMatching: Number(rawOffer?.scoreMatching ?? 0),
    logoSrc: toLogoSrc(rawOffer?.logoEntreprise ?? rawOffer?.logoSrc),
  }
}
