import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import smartHireLogo from '../../assets/smarthire-logo.png'
import {
  CV_ANALYSIS_APPLY_API_URL,
  CV_ANALYSIS_CHATBOT_API_URL,
  CV_ANALYSIS_HEALTH_API_URL,
  CV_ANALYSIS_SCORE_API_URL,
  enrichOffersWithApplicationStatus,
  fetchAllOffers,
  getOfferApplicationStatus,
  mapOfferForCandidate,
  writeOfferApplicationStatus,
} from '../../utils/offers'

const candidateSuggestedQuestions = [
  'Propose 2 actions concretes pour ameliorer mon CV sur cette offre.',
  'Donne 2 priorites concretes pour augmenter mon score.',
]

function containsSensitiveErrorDetails(value) {
  const text = String(value || '')
  return (
    /[?&]key=/i.test(text) ||
    /gemini[_-]?api[_-]?key/i.test(text) ||
    /generativelanguage\.googleapis\.com/i.test(text) ||
    /AIza[0-9A-Za-z_-]{20,}/.test(text) ||
    /AQ\.[0-9A-Za-z_.-]{10,}/.test(text)
  )
}

function sanitizeUserFacingMessage(rawMessage, fallbackMessage) {
  if (!rawMessage || containsSensitiveErrorDetails(rawMessage)) {
    return fallbackMessage
  }
  return String(rawMessage)
}

function isGeminiKeyProblem(rawMessage) {
  const text = String(rawMessage || '').toLowerCase()
  return (
    text.includes('gemini') &&
    (text.includes('cle') ||
      text.includes('clé') ||
      text.includes('api key') ||
      text.includes('gemini_api_key') ||
      text.includes('authentification') ||
      text.includes('acces refuse') ||
      text.includes('accès refusé') ||
      text.includes('invalide') ||
      text.includes('revoquee') ||
      text.includes('revoquée'))
  )
}

function buildSafeServiceMessage(payload, rawText, fallbackMessage) {
  const payloadMessage = payload?.message ?? payload?.detail ?? ''
  const combined = payloadMessage || rawText || ''
  if (isGeminiKeyProblem(combined)) {
    return 'Une erreur s est produite: probleme de cle Gemini. Verifie la configuration backend.'
  }
  return sanitizeUserFacingMessage(combined, fallbackMessage)
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

function OfferDetailsPage() {
  const { offerId } = useParams()
  const [offers, setOffers] = useState([])
  const [offersState, setOffersState] = useState({ loading: true, error: '' })
  const selectedOffer = useMemo(
    () => offers.find((offer) => offer.id === Number(offerId)) ?? null,
    [offerId, offers],
  )

  const [uploadedCvName, setUploadedCvName] = useState('')
  const [uploadedCvFile, setUploadedCvFile] = useState(null)
  const [uploadState, setUploadState] = useState({ loading: false, message: '', error: '' })
  const [applicationState, setApplicationState] = useState({
    score: null,
    note: '',
    hasApplied: false,
    statut: '',
    loading: false,
    error: '',
  })
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState([])

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
        setOffersState({ loading: false, error: 'Impossible de charger les details de l offre.' })
      }
    }

    loadOffers()
  }, [])

  useEffect(() => {
    if (!selectedOffer) {
      return
    }

    if (selectedOffer.hasApplied) {
      setApplicationState((prev) => ({
        ...prev,
        hasApplied: true,
        statut: selectedOffer.statut || 'EN_ATTENTE',
      }))
      return
    }

    const status = getOfferApplicationStatus(selectedOffer)
    if (!status) {
      return
    }

    setApplicationState((prev) => ({
      ...prev,
      hasApplied: true,
      statut: status.statut || 'EN_ATTENTE',
    }))
  }, [selectedOffer])

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

    setUploadedCvFile(selectedFile)
    setUploadedCvName(selectedFile.name)
    setUploadState({ loading: true, message: '', error: '' })

    const scoreFormData = new FormData()
    scoreFormData.append('cvFile', selectedFile)
    scoreFormData.append('offreId', String(selectedOffer.id))

    try {
      const scoreResponse = await fetch(CV_ANALYSIS_SCORE_API_URL, {
        method: 'POST',
        credentials: 'include',
        body: scoreFormData,
      })

      if (scoreResponse.status === 401 || scoreResponse.status === 403) {
        throw new Error('Session expirée ou accès non autorisé. Reconnecte-toi puis réessaie.')
      }

      const scorePayload = await scoreResponse.json().catch(() => null)
      if (!scoreResponse.ok || scorePayload?.status !== 'SUCCESS') {
        const errorText = await scoreResponse.text().catch(() => '')
        throw new Error(
          buildSafeServiceMessage(
            scorePayload,
            errorText,
            'Une erreur s est produite lors du calcul du score RAG.',
          ),
        )
      }

      const ragScore = Number(scorePayload?.data?.overallScore)
      const ragExplanation = sanitizeUserFacingMessage(
        scorePayload?.data?.scoreExplanation,
        'Score indisponible. Le moteur RAG n a pas pu calculer le matching.',
      )

      setApplicationState({
        score: Number.isFinite(ragScore) ? ragScore : 0,
        note: ragExplanation || explainScore(Number.isFinite(ragScore) ? ragScore : 0, selectedOffer),
        hasApplied: false,
        statut: '',
        loading: false,
        error: '',
      })

      setUploadState({ loading: false, message: 'Score calculé avec succès. Tu peux postuler ensuite.', error: '' })
      setChatMessages([
        {
          id: Date.now(),
          role: 'assistant',
          content:
            'Ton score est prêt. Tu peux maintenant utiliser le chatbot pour améliorer ton CV avant de postuler.',
        },
      ])
    } catch (error) {
      console.error(error)
      setUploadState({
        loading: false,
        message: '',
        error: error?.message || 'Erreur serveur pendant l analyse du CV.',
      })
    }
  }

  const handleApply = async () => {
    if (!selectedOffer) {
      return
    }

    if (applicationState.hasApplied) {
      return
    }

    if (!uploadedCvName || !uploadedCvFile) {
      setApplicationState((prev) => ({
        ...prev,
        score: null,
        note: 'Upload ton CV pour calculer un matching fiable.',
        error: '',
      }))
      return
    }

    if (applicationState.score === null) {
      setApplicationState((prev) => ({
        ...prev,
        error: 'Le score RAG doit être calculé avant de postuler.',
      }))
      return
    }

    setApplicationState((prev) => ({ ...prev, loading: true, error: '' }))

    try {
      const formData = new FormData()
      formData.append('cvFile', uploadedCvFile)
      formData.append('offreId', String(selectedOffer.id))

      const response = await fetch(CV_ANALYSIS_APPLY_API_URL, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })

      const payload = await response.json().catch(() => null)
      if (!response.ok || payload?.status !== 'SUCCESS') {
        const message = buildSafeServiceMessage(payload, '', 'Erreur lors de la candidature.')
        throw new Error(message)
      }

      const statut = 'EN_ATTENTE'
      const updatedScore = Number(payload?.overallScore)
      const updatedNote = sanitizeUserFacingMessage(
        payload?.scoreExplanation,
        explainScore(Number.isFinite(updatedScore) ? updatedScore : applicationState.score ?? 0, selectedOffer),
      )
      writeOfferApplicationStatus(selectedOffer, statut)

      setApplicationState({
        score: Number.isFinite(updatedScore) ? updatedScore : applicationState.score,
        note: updatedNote,
        hasApplied: true,
        statut,
        loading: false,
        error: '',
      })

      setOffers((prev) =>
        prev.map((offer) =>
          offer.id === selectedOffer.id ? { ...offer, hasApplied: true, statut } : offer,
        ),
      )
    } catch (error) {
      console.error(error)
      setApplicationState((prev) => ({
        ...prev,
        loading: false,
        error: error?.message || 'Erreur serveur pendant la candidature.',
      }))
    }
  }

  const sendQuestion = (question) => {
    if (!question || !selectedOffer || !uploadedCvFile) {
      return
    }

    setChatMessages((prev) => [
      ...prev,
      { id: Date.now(), role: 'user', content: question },
    ])
    setChatInput('')

    const formData = new FormData()
    formData.append('cvFile', uploadedCvFile)
    formData.append('offreId', String(selectedOffer.id))
    formData.append('question', question)

    fetch(CV_ANALYSIS_CHATBOT_API_URL, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    })
      .then(async (response) => {
        if (response.status === 401 || response.status === 403) {
          throw new Error('Session expirée ou accès non autorisé. Reconnecte-toi pour utiliser le chatbot.')
        }
        const payload = await response.json().catch(() => null)
        if (!response.ok || payload?.status !== 'SUCCESS') {
          const message = buildSafeServiceMessage(
            payload,
            '',
            'Une erreur s est produite lors du traitement chatbot.',
          )
          throw new Error(message)
        }

        const answer = payload?.data?.answer || 'Aucune reponse fournie par l assistant.'
        const actionItems = Array.isArray(payload?.data?.actionItems) ? payload.data.actionItems : []
        const hasInlineActions = /2\s+actions\s+concretes\s*:/i.test(answer)
        const content = !hasInlineActions && actionItems.length
          ? `${answer}\n\n- ${actionItems.join('\n- ')}`
          : answer

        setChatMessages((prev) => [
          ...prev,
          { id: Date.now() + 1, role: 'assistant', content },
        ])
      })
      .catch((error) => {
        const safeMessage = sanitizeUserFacingMessage(
          error?.message,
          'Service chatbot temporairement indisponible.',
        )
        setChatMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            role: 'assistant',
            content: `Erreur chatbot: ${safeMessage}`,
          },
        ])
      })
  }

  const handleSendQuestion = (event) => {
    event.preventDefault()
    sendQuestion(chatInput.trim())
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

              <button
                type="button"
                className="candidate-v2-apply-btn"
                onClick={handleApply}
                disabled={applicationState.hasApplied || applicationState.loading || applicationState.score === null}
              >
                {applicationState.hasApplied
                  ? applicationState.statut || 'EN_ATTENTE'
                  : !uploadedCvName
                    ? 'Uploader mon CV'
                  : applicationState.loading
                    ? 'Postulation...'
                    : applicationState.score === null
                      ? 'Calcul du score...'
                      : 'Postuler'}
              </button>
            </div>

            {uploadState.error ? <p className="candidate-v2-error">{uploadState.error}</p> : null}
            {applicationState.error ? <p className="candidate-v2-error">{applicationState.error}</p> : null}

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

            <div className="recruiter-questions">
              <h3>Questions suggerees</h3>
              {candidateSuggestedQuestions.map((item) => (
                <button
                  key={item}
                  type="button"
                  className="recruiter-question-item"
                  onClick={() => sendQuestion(item)}
                  disabled={!uploadedCvName}
                >
                  <p>{item}</p>
                </button>
              ))}
            </div>
          </aside>
        </div>
      </section>
    </main>
  )
}

export default OfferDetailsPage
