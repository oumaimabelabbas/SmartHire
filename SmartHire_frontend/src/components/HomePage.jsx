import { Link } from 'react-router-dom'
import { ROLE_VALUES } from '../constants/roles'

function HomePage() {
  return (
    <main>
      <section className="hero-section">
        <p className="tagline">Plateforme IA de recrutement</p>
        <h1>
          SmartHire : L'intelligence qui transforme vos recrutements en decisions rapides et humaines.
        </h1>
        <p className="slogan">Recrutez mieux. Plus vite. Avec precision.</p>

        <div className="cta-frame" role="group" aria-label="Choisissez votre profil">
          <Link className="btn btn-candidate" to={`/auth?mode=register&role=${ROLE_VALUES.CANDIDAT}`}>
            Je suis Candidat
          </Link>
          <Link className="btn btn-recruiter" to={`/auth?mode=register&role=${ROLE_VALUES.RECRUTEUR}`}>
            Je suis Recruteur
          </Link>
        </div>

        <p className="route-note">Routage dynamique selon l'acteur</p>
      </section>

      <section className="content-section" id="about">
        <h2>Structure du contenu : A propos et contact</h2>
        <div className="feature-grid">
          <article className="feature-card">
            <span className="icon">&#8682;</span>
            <h3>Upload Simplifie</h3>
            <p>Soumettez vos offres ou votre CV PDF en un clic.</p>
          </article>
          <article className="feature-card">
            <span className="icon">&#9881;</span>
            <h3>Matching IA</h3>
            <p>Notre modele LLM analyse et score la compatibilite instantanement.</p>
          </article>
          <article className="feature-card">
            <span className="icon">&#128172;</span>
            <h3>Feedback Enrichi</h3>
            <p>Obtenez des explications claires et des suggestions d'amelioration.</p>
          </article>
        </div>
      </section>

      <section className="contact-section" id="contact">
        <form className="contact-form" onSubmit={(event) => event.preventDefault()}>
          <input type="text" placeholder="Nom complet" />
          <input type="email" placeholder="Adresse Email" />
          <input type="text" placeholder="Sujet" />
          <textarea rows="5" placeholder="Votre message..." />
          <button className="btn btn-contact" type="submit">
            Envoyer la demande
          </button>
        </form>
      </section>
    </main>
  )
}

export default HomePage
