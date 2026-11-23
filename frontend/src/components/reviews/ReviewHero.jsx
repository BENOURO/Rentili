export default function ReviewHero({ reviewCount, average, positiveCount }) {
  return (
    <section className="review-hero">
      <div className="hero-deco" />
      <div className="wrap">
        <p className="eyebrow">Avis & communauté</p>
        <h1>Des locations <em>bien notées</em>, des expériences fiables.</h1>
        <p className="lead">
          Consultez les avis, partagez votre expérience et faites confiance à la communauté Rentili.
        </p>
        <div className="hero-stats">
          <span><b>{reviewCount}</b> avis publiés</span>
          <span><b>{average}/5</b> note moyenne</span>
          <span><b>{positiveCount}</b> avis positifs</span>
        </div>
      </div>
    </section>
  )
}
