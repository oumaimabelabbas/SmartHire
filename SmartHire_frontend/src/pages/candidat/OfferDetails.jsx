import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import smartHireLogo from '../../assets/smarthire-logo.png'
import { fetchAllOffers, mapOfferForCandidate } from '../../utils/offers'

const mockCvSkills = ['react', 'javascript', 'spring boot', 'docker', 'sql']

function computeMatchingScore(offer, hasCv) {
  const required = offer.requiredSkills
  if (!required.length) {
    return hasCv ? 65 : 40
  }
  const matchedSkills = required.filter((skill) => mockCvSkills.includes(skill)).length
  const skillRatio = matchedSkills / required.length
  const cvBonus = hasCv ? 0.12 : -0.1
  const finalRatio = Math.max(0, Math.min(1, skillRatio + cvBonus))
  return Math.round(finalRatio * 100)
}

function explainScore(score, offer) {
  if (score >= 85) {
    return `Très bon alignement pour ${offer.title}. Ton profil couvre bien les compétences principales.`
  }

  if (score >= 70) {
    return `Bon potentiel pour ${offer.title}. Quelques points doivent encore être renforcés.`
  }

  return `Le matching est encore limité pour ${offer.title}. Mets en avant des projets plus proches du besoin.`
}

function generateAssistantAnswer(question, offer, score) {
  const lower = question.toLowerCase()

  if (lower.includes('score') || lower.includes('matching')) {
    return `Ton score actuel est ${score ?? 0}%. Ajoute des projets concrets en lien direct avec les compétences demandées.`
  }

  if (lower.includes('cv') || lower.includes('améliorer') || lower.includes('ameliorer')) {
    return `Pour améliorer ton CV, mets en avant des résultats chiffrés, certifications et missions proches de ${offer.title}.`
  }

  return `Pour cette offre, insiste sur les compétences ${offer.requiredSkills.slice(0, 2).join(' et ')} et des réalisations mesurables.`
}

function OfferDetailsPage() {
  const { offerId } = useParams()
  const [offers, setOffers] = useState([])
  const [offersState, setOffersState] = useState({ loading: true, error: '' })
  const selectedOffer = useMemo(
    () => offers.find((offer) => offer.id === Number(offerId)) ?? null,
    [offerId, offers],
  )

  const [uploadedCvName, setUploadedCvName] = useState('')
  const [uploadState, setUploadState] = useState({ loading: false, message: '', error: '' })
  const [applicationState, setApplicationState] = useState({ score: null, note: '' })
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState([])

  useEffect(() => {
    const loadOffers = async () => {
      setOffersState({ loading: true, error: '' })

      try {
        const incoming = await fetchAllOffers()
        setOffers(incoming.map((offer) => mapOfferForCandidate(offer)))
        setOffersState({ loading: false, error: '' })
      } catch (error) {
        console.error(error)
        setOffersState({ loading: false, error: 'Impossible de charger les details de l offre.' })
      }
    }

    loadOffers()
  }, [])

  if (offersState.loading) {
    return (
      <main className="candidate-offer-page">
        <article className="candidate-v2-empty-card">
          <h3>Chargement...</h3>
          <p>Récupération de l offre depuis le serveur.</p>
        </article>
      </main>
    )
  }

  if (offersState.error) {
    return (
      <main className="candidate-offer-page">
        <article className="candidate-v2-empty-card">
          <h3>Erreur chargement</h3>
          <p>{offersState.error}</p>
          <Link to="/candidat/dashboard" className="back-home">
            Retour au dashboard
          </Link>
        </article>
      </main>
    )
  }

  const handleCvUpload = async (event) => {
    const selectedFile = event.target.files?.[0]
    if (!selectedFile) {
      return
    }

    setUploadState({ loading: true, message: '', error: '' })

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await fetch('http://localhost:8086/cv/upload', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Erreur upload')
      }

      setUploadedCvName(selectedFile.name)
      setUploadState({ loading: false, message: 'CV uploadé avec succès.', error: '' })
      setChatMessages([
        {
          id: Date.now(),
          role: 'assistant',
          content:
            'J ai analysé votre CV pour cette offre. Souhaitez-vous des conseils pour l améliorer et augmenter votre score ?',
        },
      ])
    } catch (error) {
      console.error(error)
      setUploadState({ loading: false, message: '', error: 'Erreur serveur pendant l upload du CV.' })
    }
  }

  const handleApply = () => {
    if (!selectedOffer) {
      return
    }

    if (!uploadedCvName) {
      setApplicationState({ score: null, note: 'Upload ton CV pour calculer un matching fiable.' })
      return
    }

    const score = computeMatchingScore(selectedOffer, Boolean(uploadedCvName))
    setApplicationState({ score, note: explainScore(score, selectedOffer) })
  }

  const handleSendQuestion = (event) => {
    event.preventDefault()
    const question = chatInput.trim()
    if (!question || !selectedOffer) {
      return
    }

    const assistantAnswer = generateAssistantAnswer(question, selectedOffer, applicationState.score)

    setChatMessages((prev) => [
      ...prev,
      { id: Date.now(), role: 'user', content: question },
      { id: Date.now() + 1, role: 'assistant', content: assistantAnswer },
    ])
    setChatInput('')
  }

  if (!selectedOffer) {
    return (
      <main className="candidate-offer-page">
        <article className="candidate-v2-empty-card">
          <h3>Offre introuvable</h3>
          <p>Cette offre n existe pas ou a été supprimée.</p>
          <Link to="/candidat/dashboard" className="back-home">
            Retour au dashboard
          </Link>
        </article>
      </main>
    )
  }

  return (
    <main className="candidate-offer-page">
      <section className="candidate-offer-browser">
        <header className="candidate-offer-browser-header">
          <span>Offre Details</span>
          <Link to="/candidat/dashboard">Retour</Link>
        </header>

        <div className="candidate-offer-browser-content">
          <article className="candidate-offer-center-panel">
            <h2>
              {selectedOffer.title} | {selectedOffer.company}
            </h2>
            <h3>Role :</h3>
            <p>{selectedOffer.roleSummary}</p>
        

            <div className="candidate-offer-meta">
              <p>{selectedOffer.location}</p>
              <p>{selectedOffer.contractType}</p>
              <p>{selectedOffer.domain}</p>
            </div>

            <div className="candidate-offer-details-grid">
              <div>
                <h3>Responsabilités</h3>
                <ul>
                  {selectedOffer.responsibilities.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h3>Compétences requises</h3>
                <ul>
                  {selectedOffer.requiredSkills.map((skill) => (
                    <li key={skill}>{skill}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="candidate-offer-upload-row">
              <label className="candidate-v2-upload-box" htmlFor={`offer-detail-cv-${selectedOffer.id}`}>
                <input
                  id={`offer-detail-cv-${selectedOffer.id}`}
                  type="file"
                  accept="application/pdf"
                  onChange={handleCvUpload}
                />
                <span>{uploadedCvName ? uploadedCvName : '[ Uploader mon CV (PDF) ]'}</span>
                <small>
                  {uploadState.loading ? 'Upload en cours...' : uploadState.message || 'Format PDF uniquement'}
                </small>
              </label>

              <button type="button" className="candidate-v2-apply-btn" onClick={handleApply}>
                Postuler
              </button>
            </div>

            {uploadState.error ? <p className="candidate-v2-error">{uploadState.error}</p> : null}

            <div className="candidate-offer-score-wrap">
              <div
                className="candidate-offer-score-circle"
                style={{ '--score': `${applicationState.score ?? 0}%` }}
              >
                <div>
                  <span>Score de</span>
                  <strong>Matching</strong>
                  <b>{applicationState.score ?? 0}%</b>
                </div>
              </div>

              <p>
                {applicationState.note ||
                  'Votre profil correspond fortement aux exigences techniques de cette offre.'}
              </p>
            </div>
          </article>

          <aside className="candidate-board-chat" aria-label="Assistant SmartHire">
            <div className="candidate-board-chat-head">
              <img src={smartHireLogo} alt="SmartHire" />
              <h2>Assistant SmartHire</h2>
            </div>

            <div className="candidate-v2-chat-messages">
              {chatMessages.length ? (
                chatMessages.map((message) => (
                  <div
                    key={message.id}
                    className={
                      message.role === 'assistant'
                        ? 'candidate-v2-chat-message is-assistant'
                        : 'candidate-v2-chat-message is-user'
                    }
                  >
                    {message.content}
                  </div>
                ))
              ) : (
                <div className="candidate-v2-chat-message is-assistant">
                  Upload ton CV pour démarrer l assistant SmartHire.
                </div>
              )}
            </div>

            <form className="candidate-v2-chat-form" onSubmit={handleSendQuestion}>
              <input
                type="text"
                placeholder="Comment améliorer mon score pour cette offre ?"
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                disabled={!uploadedCvName}
              />
              <button type="submit" aria-label="Envoyer" disabled={!uploadedCvName}>
                ➤
              </button>
            </form>
          </aside>
        </div>
      </section>
    </main>
  )
}

export default OfferDetailsPage
