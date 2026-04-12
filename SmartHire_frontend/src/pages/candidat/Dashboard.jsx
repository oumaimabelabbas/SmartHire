import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import smartHireLogo from '../../assets/smarthire-logo.png'
import { enrichOffersWithApplicationStatus, fetchAllOffers, mapOfferForCandidate } from '../../utils/offers'

function normalizeText(value) {
  return value.trim().toLowerCase()
}

function CandidatDashboardPage() {
  const navigate = useNavigate()
  const [offers, setOffers] = useState([])
  const [offersState, setOffersState] = useState({ loading: true, error: '' })
  const [preferences, setPreferences] = useState({
    keywords: '',
    location: '',
    contractType: 'all',
  })
  const [hasSearched, setHasSearched] = useState(false)

  useEffect(() => {
    const loadOffers = async () => {
      setOffersState({ loading: true, error: '' })

      try {
        const incoming = await fetchAllOffers()
        const mapped = incoming.map((offer) => mapOfferForCandidate(offer))
        setOffers(enrichOffersWithApplicationStatus(mapped))
        setOffersState({ loading: false, error: '' })
      } catch (error) {
        console.error(error)
        setOffersState({ loading: false, error: 'Impossible de charger les offres pour le moment.' })
      }
    }

    loadOffers()
  }, [])

  const filteredOffers = useMemo(() => {
    const keyword = normalizeText(preferences.keywords)
    const location = normalizeText(preferences.location)

    return offers.filter((offer) => {
      const searchable = `${offer.title} ${offer.company} ${offer.location} ${offer.contractType}`.toLowerCase()
      const matchKeyword = keyword ? searchable.includes(keyword) : true
      const matchLocation = location ? normalizeText(offer.location).includes(location) : true
      const matchContract =
        preferences.contractType === 'all'
          ? true
          : normalizeText(offer.contractType) === normalizeText(preferences.contractType)

      return matchKeyword && matchLocation && matchContract
    })
  }, [offers, preferences])

  const handlePreferencesChange = (field, value) => {
    setPreferences((prev) => ({ ...prev, [field]: value }))
  }

  const handleSearch = (event) => {
    event.preventDefault()
    setHasSearched(true)
  }

  return (
    <main className="candidate-layout-page">
      <section className="candidate-board-shell" aria-label="Dashboard candidat">
        <aside className="candidate-board-rail" aria-hidden="true">
          <img src={smartHireLogo} alt="" className="candidate-board-rail-logo" />
          <span className="candidate-board-rail-dot" />
          <span className="candidate-board-rail-dot" />
          <span className="candidate-board-rail-dot" />
        </aside>

        <div className="candidate-board-main">
          <header className="candidate-board-header">
            <h1>Dashboard Candidat</h1>
            <span className="candidate-board-status" aria-hidden="true" />
          </header>

          <form className="candidate-board-filters" onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="[Rechercher un poste]"
              value={preferences.keywords}
              onChange={(event) => handlePreferencesChange('keywords', event.target.value)}
            />
            <input
              type="text"
              placeholder="[Lieu]"
              value={preferences.location}
              onChange={(event) => handlePreferencesChange('location', event.target.value)}
            />
            <select
              value={preferences.contractType}
              onChange={(event) => handlePreferencesChange('contractType', event.target.value)}
            >
              <option value="all">[Type de contrat]</option>
              <option value="CDI">CDI</option>
              <option value="CDD">CDD</option>
              <option value="Freelance">Freelance</option>
            </select>
            <button type="submit" className="candidate-board-search-btn" aria-label="Rechercher">
              🔎
            </button>
          </form>

          <section className="candidate-board-offers" aria-label="Offres">
            {offersState.error ? <p className="candidate-v2-error">{offersState.error}</p> : null}

            {hasSearched ? (
              <p className="candidate-board-result-count">{filteredOffers.length} offre(s) trouvée(s)</p>
            ) : null}

            {offersState.loading ? (
              <article className="candidate-v2-empty-card">
                <h3>Chargement des offres...</h3>
              </article>
            ) : filteredOffers.length ? (
              <div className="candidate-offers-cards-grid">
                {filteredOffers.map((offer) => (
                  <article key={offer.id} className="candidate-offer-list-card">
                    <div className="candidate-offer-list-top">
                      <div className="candidate-offer-list-logo" aria-hidden={!offer.logoSrc}>
                        {offer.logoSrc ? <img src={offer.logoSrc} alt={`Logo ${offer.company}`} /> : null}
                      </div>
                      <div>
                        <h3>{offer.title}</h3>
                        <p>{offer.company}</p>
                        <div className="candidate-offer-inline-meta">
                          <span>{offer.location}</span>
                          <span>{offer.contractType}</span>
                          <span>{offer.location === 'Télétravail' ? 'Télétravail' : 'Sur site'}</span>
                        </div>
                      </div>
                    </div>

                    <div className="candidate-offer-list-bottom">
                      <small>il y a 3 heures</small>
                      <button
                        type="button"
                        className="candidate-offer-view-btn"
                        onClick={() => navigate(`/candidat/offres/${offer.id}`)}
                      >
                        {offer.hasApplied ? offer.statut || 'EN_ATTENTE' : 'Voir'}
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <article className="candidate-v2-empty-card">
                <h3>Aucune offre pour ces filtres</h3>
                <p>Modifie tes préférences pour voir des opportunités correspondantes.</p>
              </article>
            )}
          </section>
        </div>
      </section>
    </main>
  )
}

export default CandidatDashboardPage
