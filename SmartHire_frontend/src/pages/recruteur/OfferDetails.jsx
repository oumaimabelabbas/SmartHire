import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { OFFERS_API_URL } from '../../utils/offers'
import smartHireLogo from '../../assets/smarthire-logo.png'

const CANDIDATURES_API_URL = 'http://localhost:8086/candidatures'

function normalizeOfferResponse(rawOffer) {
  // Handle OffreEmploi response structure from backend
  const offer = rawOffer ?? {}
  return {
    id: offer.id ?? offer.offre_id ?? '',
    titre: offer.titre ?? offer.title ?? '',
    description: offer.description ?? offer.aProposRole ?? '',
    entreprise: offer.entreprise ?? offer.company ?? '',
    localisation: offer.localisation ?? offer.location ?? '',
    typeContrat: offer.typeContrat ?? offer.contractType ?? '',
    modeTravail: offer.modeTravail ?? offer.domain ?? '',
    actif: offer.actif ?? true,
    aProposEntreprise: offer.aProposEntreprise ?? offer.aboutCompany ?? '',
    aProposRole: offer.aProposRole ?? offer.aboutRole ?? '',
    responsabilites: Array.isArray(offer.responsabilites) ? offer.responsabilites : [],
    profilRecherche: Array.isArray(offer.profilRecherche) ? offer.profilRecherche : [],
    logoSrc: offer.logoSrc ?? offer.logo ?? '',
  }
}

function RecruiterOfferDetailsPage() {
  const { offerId } = useParams()
  const [offer, setOffer] = useState(null)
  const [candidatures, setCandidatures] = useState([])
  const [state, setState] = useState({ loading: true, error: '' })
  const [candidaturesState, setCandidaturesState] = useState({ loading: false, error: '' })
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [editLogoFile, setEditLogoFile] = useState(null)
  const [editSubmitState, setEditSubmitState] = useState({ loading: false, message: '', error: '' })
  const [editFormState, setEditFormState] = useState({
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

  useEffect(() => {
    const load = async () => {
      setState({ loading: true, error: '' })
      try {
        // Try to fetch offer detail from GET /offres/{id}
        let fetchedOffer = null
        try {
          const res = await fetch(`${OFFERS_API_URL}/${offerId}`, { method: 'GET', credentials: 'include' })
          if (res.ok) {
            const data = await res.json()
            fetchedOffer = normalizeOfferResponse(data)
          }
        } catch {
          // fallback
        }

        // If not available, try listing and finding
        if (!fetchedOffer) {
          const listRes = await fetch(OFFERS_API_URL, { method: 'GET', credentials: 'include' })
          if (!listRes.ok) throw new Error('Impossible de recuperer l offre')
          const listData = await listRes.json()
          const arr = Array.isArray(listData) ? listData : Array.isArray(listData?.content) ? listData.content : Array.isArray(listData?.data) ? listData.data : []
          const found = arr.find((o) => String(o.id) === String(offerId))
          if (!found) throw new Error('Offre introuvable')
          fetchedOffer = normalizeOfferResponse(found)
        }

        setOffer(fetchedOffer)
        setState({ loading: false, error: '' })
        
        // Fetch candidatures from GET /candidatures/offre/{offreId}
        setCandidaturesState({ loading: true, error: '' })
        try {
          const candUrl = `${CANDIDATURES_API_URL}/offre/${offerId}`
          const candRes = await fetch(candUrl, { method: 'GET', credentials: 'include' })
          if (candRes.ok) {
            const candData = await candRes.json()
            const candList = Array.isArray(candData) ? candData : Array.isArray(candData?.content) ? candData.content : Array.isArray(candData?.data) ? candData.data : []
            setCandidatures(candList)
            setCandidaturesState({ loading: false, error: '' })
          } else {
            setCandidaturesState({ loading: false, error: '' })
          }
        } catch (err) {
          console.error('Erreur candidatures:', err)
          setCandidaturesState({ loading: false, error: '' })
        }
      } catch (error) {
        console.error(error)
        setState({ loading: false, error: error?.message || 'Erreur chargement details.' })
      }
    }

    load()
  }, [offerId])

  const parseList = (value) => {
    return value
      .split(/\n|,/)
      .map((item) => item.trim())
      .filter(Boolean)
  }

  const handleEditOpen = () => {
    if (offer) {
      setEditFormState({
        titre: offer.titre || '',
        description: offer.description || '',
        entreprise: offer.entreprise || '',
        localisation: offer.localisation || '',
        typeContrat: offer.typeContrat || 'CDI',
        modeTravail: offer.modeTravail || 'HYBRIDE',
        actif: offer.actif ?? true,
        aProposEntreprise: offer.aProposEntreprise || '',
        aProposRole: offer.aProposRole || '',
        responsabilites: Array.isArray(offer.responsabilites) ? offer.responsabilites.join('\n') : '',
        profilRecherche: Array.isArray(offer.profilRecherche) ? offer.profilRecherche.join('\n') : '',
      })
      setEditSubmitState({ loading: false, message: '', error: '' })
      setEditLogoFile(null)
    }
    setIsEditOpen(true)
  }

  const handleEditFormChange = (field, value) => {
    setEditFormState((prev) => ({ ...prev, [field]: value }))
  }

  const handleEditLogoChange = (event) => {
    const file = event.target.files?.[0]
    if (!file) {
      setEditLogoFile(null)
      return
    }
    if (!file.type.startsWith('image/')) {
      setEditSubmitState({ loading: false, message: '', error: 'Le logo doit être une image valide.' })
      setEditLogoFile(null)
      return
    }
    setEditSubmitState({ loading: false, message: '', error: '' })
    setEditLogoFile(file)
  }

  const handleEditSubmit = async (event) => {
    event.preventDefault()
    setEditSubmitState({ loading: true, message: '', error: '' })

    if (!editFormState.titre.trim() || !editFormState.description.trim() || !editFormState.entreprise.trim()) {
      setEditSubmitState({ loading: false, message: '', error: 'Titre, description et entreprise sont obligatoires.' })
      return
    }

    const payload = {
      titre: editFormState.titre.trim(),
      description: editFormState.description.trim(),
      entreprise: editFormState.entreprise.trim(),
      localisation: editFormState.localisation.trim(),
      typeContrat: editFormState.typeContrat,
      modeTravail: editFormState.modeTravail,
      actif: editFormState.actif,
      aProposEntreprise: editFormState.aProposEntreprise.trim(),
      aProposRole: editFormState.aProposRole.trim(),
      responsabilites: parseList(editFormState.responsabilites),
      profilRecherche: parseList(editFormState.profilRecherche),
    }

    try {
      const formData = new FormData()
      formData.append('offre', new Blob([JSON.stringify(payload)], { type: 'application/json' }))
      
      if (editLogoFile) {
        formData.append('logo', editLogoFile)
      } else {
        // Append empty blob if no new logo
        formData.append('logo', new Blob([], { type: 'image/png' }))
      }

      const response = await fetch(`${OFFERS_API_URL}/${offerId}`, {
        method: 'PUT',
        credentials: 'include',
        body: formData,
      })

      if (!response.ok) {
        const backendMessage = await response.text().catch(() => '')
        throw new Error(backendMessage || 'Erreur lors de la modification de l\'offre.')
      }

      const updatedOfferData = await response.json().catch(() => null)
      const updatedOffer = normalizeOfferResponse(updatedOfferData ?? payload)
      setOffer(updatedOffer)
      setIsEditOpen(false)
      setEditSubmitState({ loading: false, message: 'Offre modifiée avec succès.', error: '' })
    } catch (error) {
      console.error(error)
      setEditSubmitState({ loading: false, message: '', error: error?.message || 'Erreur serveur pendant la modification.' })
    }
  }

  if (state.loading) {
    return (
      <main className="candidate-layout-page">
        <section className="candidate-v2-empty-card">
          <h3>Chargement...</h3>
        </section>
      </main>
    )
  }

  if (state.error) {
    return (
      <main className="candidate-layout-page">
        <section className="candidate-v2-empty-card">
          <h3>Erreur</h3>
          <p>{state.error}</p>
          <Link to="/recruteur/dashboard" className="back-home">Retour au dashboard</Link>
        </section>
      </main>
    )
  }

  return (
    <main className="candidate-layout-page">
      <section className="candidate-board-shell" aria-label="Détails offre recruteur">
        <aside className="candidate-board-rail" aria-hidden="true">
          <img src={smartHireLogo} alt="" className="candidate-board-rail-logo" />
        </aside>

        <div className="candidate-board-main recruiter-board-main">
          <header className="candidate-board-header">
            <h1>Détails Offre</h1>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button type="button" className="btn btn-light" onClick={handleEditOpen}>
                 Modifier offre
              </button>
              <Link to="/recruteur/dashboard" className="btn btn-light">Retour offres</Link>
            </div>
          </header>

          {editSubmitState.error ? <p className="candidate-v2-error">{editSubmitState.error}</p> : null}
          {editSubmitState.message ? <p className="candidate-v2-success">{editSubmitState.message}</p> : null}

          {isEditOpen ? (
            <section className="recruiter-offer-form-card" aria-label="Formulaire modification offre">
              <h2>Modifier l'offre</h2>
              <form className="recruiter-offer-form" onSubmit={handleEditSubmit}>
                <label htmlFor="edit-offer-titre">Titre</label>
                <input
                  id="edit-offer-titre"
                  type="text"
                  value={editFormState.titre}
                  onChange={(event) => handleEditFormChange('titre', event.target.value)}
                  required
                />

                <label htmlFor="edit-offer-description">Description</label>
                <textarea
                  id="edit-offer-description"
                  rows={3}
                  value={editFormState.description}
                  onChange={(event) => handleEditFormChange('description', event.target.value)}
                  required
                />

                <label htmlFor="edit-offer-entreprise">Entreprise</label>
                <input
                  id="edit-offer-entreprise"
                  type="text"
                  value={editFormState.entreprise}
                  onChange={(event) => handleEditFormChange('entreprise', event.target.value)}
                  required
                />

                <label htmlFor="edit-offer-logo">Logo entreprise (image) - Optionnel</label>
                <input
                  id="edit-offer-logo"
                  type="file"
                  accept="image/*"
                  onChange={handleEditLogoChange}
                />

                <label htmlFor="edit-offer-localisation">Localisation</label>
                <input
                  id="edit-offer-localisation"
                  type="text"
                  value={editFormState.localisation}
                  onChange={(event) => handleEditFormChange('localisation', event.target.value)}
                />

                <label htmlFor="edit-offer-type">Type contrat</label>
                <select
                  id="edit-offer-type"
                  value={editFormState.typeContrat}
                  onChange={(event) => handleEditFormChange('typeContrat', event.target.value)}
                >
                  <option value="CDI">CDI</option>
                  <option value="CDD">CDD</option>
                  <option value="STAGE">Stage</option>
                  <option value="FREELANCE">Freelance</option>
                </select>

                <label htmlFor="edit-offer-mode">Mode travail</label>
                <select
                  id="edit-offer-mode"
                  value={editFormState.modeTravail}
                  onChange={(event) => handleEditFormChange('modeTravail', event.target.value)}
                >
                  <option value="SUR_SITE">Presentiel</option>
                  <option value="HYBRIDE">Hybride</option>
                  <option value="TELETRAVAIL">Distance</option>
                </select>

                <label className="recruiter-checkline" htmlFor="edit-offer-actif">
                  <input
                    id="edit-offer-actif"
                    type="checkbox"
                    checked={editFormState.actif}
                    onChange={(event) => handleEditFormChange('actif', event.target.checked)}
                  />
                  Offre active
                </label>

                <label htmlFor="edit-offer-about-company">A propos entreprise</label>
                <textarea
                  id="edit-offer-about-company"
                  rows={2}
                  value={editFormState.aProposEntreprise}
                  onChange={(event) => handleEditFormChange('aProposEntreprise', event.target.value)}
                />

                <label htmlFor="edit-offer-about-role">A propos role</label>
                <textarea
                  id="edit-offer-about-role"
                  rows={2}
                  value={editFormState.aProposRole}
                  onChange={(event) => handleEditFormChange('aProposRole', event.target.value)}
                />

                <label htmlFor="edit-offer-responsabilites">Responsabilites (une ligne par item)</label>
                <textarea
                  id="edit-offer-responsabilites"
                  rows={3}
                  value={editFormState.responsabilites}
                  onChange={(event) => handleEditFormChange('responsabilites', event.target.value)}
                />

                <label htmlFor="edit-offer-profil">Profil recherche (une ligne par item)</label>
                <textarea
                  id="edit-offer-profil"
                  rows={3}
                  value={editFormState.profilRecherche}
                  onChange={(event) => handleEditFormChange('profilRecherche', event.target.value)}
                />

                <div className="recruiter-form-actions">
                  <button
                    type="button"
                    className="recruiter-form-cancel"
                    onClick={() => setIsEditOpen(false)}
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="candidate-offer-view-btn recruiter-form-save"
                    disabled={editSubmitState.loading}
                  >
                    {editSubmitState.loading ? 'Modification...' : 'Modifier l\'offre'}
                  </button>
                </div>
              </form>
            </section>
          ) : null}

          <section className="recruiter-offer-details-card">
            <h2>{offer?.titre}</h2>
            <div className="offer-details-meta">
              <p><strong>Entreprise:</strong> {offer?.entreprise}</p>
              <p><strong>Localisation:</strong> {offer?.localisation || '-'}</p>
              <p><strong>Type contrat:</strong> {offer?.typeContrat || '-'}</p>
              <p><strong>Mode travail:</strong> {offer?.modeTravail || '-'}</p>
            </div>

            {offer?.aProposEntreprise ? (
              <div>
                <h3>À propos de l'entreprise</h3>
                <p>{offer.aProposEntreprise}</p>
              </div>
            ) : null}

            {offer?.aProposRole ? (
              <div>
                <h3>À propos du rôle</h3>
                <p>{offer.aProposRole}</p>
              </div>
            ) : null}

            {offer?.description ? (
              <div>
                <h3>Description</h3>
                <p>{offer.description}</p>
              </div>
            ) : null}

            {offer?.responsabilites && offer.responsabilites.length > 0 ? (
              <div>
                <h3>Responsabilités</h3>
                <ul>
                  {offer.responsabilites.map((resp, idx) => (
                    <li key={idx}>{resp}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {offer?.profilRecherche && offer.profilRecherche.length > 0 ? (
              <div>
                <h3>Profil recherché</h3>
                <ul>
                  {offer.profilRecherche.map((skill, idx) => (
                    <li key={idx}>{skill}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            <h3>Candidatures</h3>
            {candidaturesState.error ? <p className="candidate-v2-error">{candidaturesState.error}</p> : null}
            <table className="recruiter-applications-table">
              <thead>
                <tr>
                  <th>Nom</th>
                  <th>Prenom</th>
                  <th>CV</th>
                  <th>Score</th>
                  <th>Explication</th>
                </tr>
              </thead>
              <tbody>
                {candidaturesState.loading ? (
                  <tr>
                    <td colSpan={5} className="recruiter-table-empty">Chargement des candidatures...</td>
                  </tr>
                ) : candidatures.length ? (
                  candidatures.map((cand) => (
                    <tr key={cand.candidatureId}>
                      <td>{cand.nom || '-'}</td>
                      <td>{cand.prenom || '-'}</td>
                      <td>
                        {cand.cvName ? (
                          <a href={`/api/cv/download/${cand.cvId}`} target="_blank" rel="noreferrer" download>
                            {cand.cvName}
                          </a>
                        ) : (
                          <span>-</span>
                        )}
                      </td>
                      <td>{cand.overallScore ?? 0}%</td>
                      <td>{cand.scoreExplanation || '-'}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="recruiter-table-empty">Pas de candidatures pour cette offre.</td>
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

export default RecruiterOfferDetailsPage
