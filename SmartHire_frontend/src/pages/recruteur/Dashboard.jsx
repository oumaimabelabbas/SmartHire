import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import smartHireLogo from '../../assets/smarthire-logo.png'
import { mapOfferForRecruiter, OFFERS_API_URL, CANDIDATURES_API_URL } from '../../utils/offers'

function normalizeText(value) {
  return value.trim().toLowerCase()
}

function parseList(value) {
  return value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function buildScoreFromTitle(title) {
  const base = title.length % 38
  return 58 + base
}

function RecruiterDashboardPage() {
  const [offers, setOffers] = useState([])
  const navigate = useNavigate()
  const [offersState, setOffersState] = useState({ loading: true, error: '' })
  const [searchTitle, setSearchTitle] = useState('')
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [logoFile, setLogoFile] = useState(null)
  const [submitState, setSubmitState] = useState({ loading: false, message: '', error: '' })
  const [formState, setFormState] = useState({
    titre: '',
    description: '',
    entreprise: '',
    localisation: '',
    typeContrat: 'CDI',
    modeTravail: 'HYBRIDE',
    actif: true,
    aProposEntreprise: '',
    aProposRole: '',
    responsabilites: '',
    profilRecherche: '',
  })

  const filteredOffers = useMemo(() => {
    const needle = normalizeText(searchTitle)
    return offers.filter((offer) => normalizeText(offer.titre).includes(needle))
  }, [offers, searchTitle])

  useEffect(() => {
    const loadOffers = async () => {
      setOffersState({ loading: true, error: '' })

      try {
        const response = await fetch(OFFERS_API_URL, {
          method: 'GET',
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error('Erreur chargement offres')
        }

        const data = await response.json()
        const incoming = Array.isArray(data) ? data : []
        // Keep only offers that appear to belong to the current recruiter (attempt by entreprise or creator)
        const mapped = incoming.map((offer) => mapOfferForRecruiter(offer))

        // try to fetch current user to filter offers owned by this recruiter
        let currentUser = null
        try {
          const profileRes = await fetch('/profile', { method: 'GET', credentials: 'include' })
          if (profileRes.ok) {
            currentUser = await profileRes.json().catch(() => null)
          }
        } catch {
          // ignore
        }

        let visible = mapped
        if (currentUser) {
          const normalizedCompany = (currentUser?.entreprise ?? currentUser?.company ?? currentUser?.username ?? '').toString().trim().toLowerCase()
          visible = mapped.filter((o) => {
            const offerCompany = (o.entreprise ?? o.company ?? o.companyName ?? o.entreprise ?? '').toString().trim().toLowerCase()
            if (offerCompany && normalizedCompany && offerCompany === normalizedCompany) return true
            // try match by creator id if available
            if (o.creatorId && (currentUser?.id ?? currentUser?.userId) && String(o.creatorId) === String(currentUser?.id ?? currentUser?.userId)) return true
            return false
          })
        }

        setOffers(visible)
        setOffersState({ loading: false, error: '' })
      } catch (error) {
        console.error(error)
        setOffersState({ loading: false, error: 'Impossible de charger les offres depuis le serveur.' })
      }
    }

    loadOffers()
  }, [])

  const handleSelectOffer = (offer) => {
    if (!offer || !offer.id) return
    navigate(`/recruteur/offres/${offer.id}`)
  }

  const handleFormChange = (field, value) => {
    setFormState((prev) => ({ ...prev, [field]: value }))
  }

  const resetForm = () => {
    setFormState({
      titre: '',
      description: '',
      entreprise: '',
      localisation: '',
      typeContrat: 'CDI',
      modeTravail: 'HYBRIDE',
      actif: true,
      aProposEntreprise: '',
      aProposRole: '',
      responsabilites: '',
      profilRecherche: '',
    })
    setLogoFile(null)
  }

  const handleLogoChange = (event) => {
    const file = event.target.files?.[0]

    if (!file) {
      setLogoFile(null)
      return
    }

    if (!file.type.startsWith('image/')) {
      setSubmitState({ loading: false, message: '', error: 'Le logo doit etre une image valide.' })
      setLogoFile(null)
      return
    }

    setSubmitState({ loading: false, message: '', error: '' })
    setLogoFile(file)
  }

  const handleAddOffer = async (event) => {
    event.preventDefault()
    setSubmitState({ loading: true, message: '', error: '' })

    if (!formState.titre.trim() || !formState.description.trim() || !formState.entreprise.trim()) {
      setSubmitState({ loading: false, message: '', error: 'Titre, description et entreprise sont obligatoires.' })
      return
    }

    if (!logoFile) {
      setSubmitState({ loading: false, message: '', error: 'Le logo est obligatoire.' })
      return
    }

    const payload = {
      titre: formState.titre.trim(),
      description: formState.description.trim(),
      entreprise: formState.entreprise.trim(),
      localisation: formState.localisation.trim(),
      typeContrat: formState.typeContrat,
      modeTravail: formState.modeTravail,
      actif: formState.actif,
      aProposEntreprise: formState.aProposEntreprise.trim(),
      aProposRole: formState.aProposRole.trim(),
      responsabilites: parseList(formState.responsabilites),
      profilRecherche: parseList(formState.profilRecherche),
    }

    try {
      const selectedFile = logoFile
      const formData = new FormData()

      formData.append('offre', new Blob([JSON.stringify(payload)], { type: 'application/json' }))
      formData.append('logo', selectedFile)

      const response = await fetch(OFFERS_API_URL, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          throw new Error('Session expirée ou non autorisée. Reconnectez-vous avec un compte recruteur.')
        }
        const backendMessage = await response.text().catch(() => '')
        throw new Error(backendMessage || 'Erreur lors de la creation de l offre.')
      }

      const createdOffer = await response.json().catch(() => null)

      const newOffer = {
        ...mapOfferForRecruiter(createdOffer ?? payload),
        id: createdOffer?.id ?? Date.now(),
        scoreMatching: buildScoreFromTitle(payload.titre),
        logoNom: logoFile?.name ?? null,
      }

      setOffers((prev) => [newOffer, ...prev])
      resetForm()
      setIsFormOpen(false)
      setSubmitState({ loading: false, message: 'Offre enregistree avec succes.', error: '' })
    } catch (error) {
      console.error(error)
      setSubmitState({ loading: false, message: '', error: error?.message || 'Erreur serveur pendant l enregistrement de l offre.' })
    }
  }

  return (
    <main className="candidate-layout-page">
      <section className="candidate-board-shell" aria-label="Dashboard recruteur">
        <aside className="candidate-board-rail" aria-hidden="true">
          <img src={smartHireLogo} alt="" className="candidate-board-rail-logo" />
          <span className="candidate-board-rail-dot" />
          <span className="candidate-board-rail-dot" />
          <span className="candidate-board-rail-dot" />
        </aside>

        <div className="candidate-board-main recruiter-board-main">
          <header className="candidate-board-header">
            <h1>Dashboard Recruteur</h1>
            <span className="candidate-board-status" aria-hidden="true" />
          </header>

          <div className="recruiter-board-toolbar">
            <form className="candidate-board-filters recruiter-board-search" onSubmit={(event) => event.preventDefault()}>
              <input
                type="text"
                placeholder="[Rechercher une offre par nom]"
                value={searchTitle}
                onChange={(event) => setSearchTitle(event.target.value)}
              />
              <button type="submit" className="candidate-board-search-btn" aria-label="Rechercher">
                🔎
              </button>
            </form>

            <button
              type="button"
              className="recruiter-add-offer-btn"
              onClick={() => {
                setSubmitState({ loading: false, message: '', error: '' })
                setIsFormOpen((prev) => !prev)
              }}
            >
              + Nouvelle Offre d'Emploi
            </button>
          </div>

          {submitState.error ? <p className="candidate-v2-error">{submitState.error}</p> : null}
          {submitState.message ? <p className="candidate-v2-success">{submitState.message}</p> : null}
          {offersState.error ? <p className="candidate-v2-error">{offersState.error}</p> : null}

          {isFormOpen ? (
            <section className="recruiter-offer-form-card" aria-label="Formulaire ajout offre">
              <h2>Ajouter une offre</h2>
              <form className="recruiter-offer-form" onSubmit={handleAddOffer}>
                <label htmlFor="offer-titre">Titre</label>
                <input
                  id="offer-titre"
                  type="text"
                  value={formState.titre}
                  onChange={(event) => handleFormChange('titre', event.target.value)}
                  required
                />

                <label htmlFor="offer-description">Description</label>
                <textarea
                  id="offer-description"
                  rows={3}
                  value={formState.description}
                  onChange={(event) => handleFormChange('description', event.target.value)}
                  required
                />

                <label htmlFor="offer-entreprise">Entreprise</label>
                <input
                  id="offer-entreprise"
                  type="text"
                  value={formState.entreprise}
                  onChange={(event) => handleFormChange('entreprise', event.target.value)}
                  required
                />

                <label htmlFor="offer-logo">Logo entreprise (image)</label>
                <input
                  id="offer-logo"
                  type="file"
                  accept="image/*"
                  onChange={handleLogoChange}
                />

                <label htmlFor="offer-localisation">Localisation</label>
                <input
                  id="offer-localisation"
                  type="text"
                  value={formState.localisation}
                  onChange={(event) => handleFormChange('localisation', event.target.value)}
                />

                <label htmlFor="offer-type">Type contrat</label>
                <select
                  id="offer-type"
                  value={formState.typeContrat}
                  onChange={(event) => handleFormChange('typeContrat', event.target.value)}
                >
                  <option value="CDI">CDI</option>
                  <option value="CDD">CDD</option>
                  <option value="STAGE">Stage</option>
                  <option value="FREELANCE">Freelance</option>
                </select>

                <label htmlFor="offer-mode">Mode travail</label>
                <select
                  id="offer-mode"
                  value={formState.modeTravail}
                  onChange={(event) => handleFormChange('modeTravail', event.target.value)}
                >
                  <option value="SUR_SITE">Presentiel</option>
                  <option value="HYBRIDE">Hybride</option>
                  <option value="TELETRAVAIL">Distance</option>
                </select>

                <label className="recruiter-checkline" htmlFor="offer-actif">
                  <input
                    id="offer-actif"
                    type="checkbox"
                    checked={formState.actif}
                    onChange={(event) => handleFormChange('actif', event.target.checked)}
                  />
                  Offre active
                </label>

                <label htmlFor="offer-about-company">A propos entreprise</label>
                <textarea
                  id="offer-about-company"
                  rows={2}
                  value={formState.aProposEntreprise}
                  onChange={(event) => handleFormChange('aProposEntreprise', event.target.value)}
                />

                <label htmlFor="offer-about-role">A propos role</label>
                <textarea
                  id="offer-about-role"
                  rows={2}
                  value={formState.aProposRole}
                  onChange={(event) => handleFormChange('aProposRole', event.target.value)}
                />

                <label htmlFor="offer-responsabilites">Responsabilites (une ligne par item)</label>
                <textarea
                  id="offer-responsabilites"
                  rows={3}
                  value={formState.responsabilites}
                  onChange={(event) => handleFormChange('responsabilites', event.target.value)}
                />

                <label htmlFor="offer-profil">Profil recherche (une ligne par item)</label>
                <textarea
                  id="offer-profil"
                  rows={3}
                  value={formState.profilRecherche}
                  onChange={(event) => handleFormChange('profilRecherche', event.target.value)}
                />

                <div className="recruiter-form-actions">
                  <button
                    type="button"
                    className="recruiter-form-cancel"
                    onClick={() => {
                      setSubmitState({ loading: false, message: '', error: '' })
                      setLogoFile(null)
                      setIsFormOpen(false)
                    }}
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="candidate-offer-view-btn recruiter-form-save"
                    disabled={submitState.loading}
                  >
                    {submitState.loading ? 'Enregistrement...' : "Enregistrer l'offre"}
                  </button>
                </div>
              </form>
            </section>
          ) : null}

          <section className="recruiter-offers-table-card" aria-label="Offres publiees">
            <table className="recruiter-offers-table">
              <thead>
                <tr>
                  <th>Offre</th>
                  <th>Entreprise</th>
                  <th>Localisation</th>
                  <th>Type</th>
                  <th>Mode</th>
                </tr>
              </thead>
              <tbody>
                {offersState.loading ? (
                  <tr>
                    <td colSpan={5} className="recruiter-table-empty">
                      Chargement des offres...
                    </td>
                  </tr>
                ) : filteredOffers.length ? (
                  filteredOffers.map((offer) => (
                    <tr key={offer.id} onClick={() => handleSelectOffer(offer)} className="recruiter-offer-row">
                      <td>{offer.titre}</td>
                      <td>{offer.entreprise}</td>
                      <td>{offer.localisation || '-'}</td>
                      <td>{offer.typeContrat}</td>
                      <td>{offer.modeTravail}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="recruiter-table-empty">
                      Aucune offre trouvee pour cette recherche.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>

          
        </div>
      </section>
    </main>
  )
}

export default RecruiterDashboardPage
