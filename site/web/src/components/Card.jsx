export default function Card({ story, variant = "default", onOpen }) {
  return (
    <button className={`card card--${variant}`} onClick={() => onOpen(story)}>
      <div className="card__media">
        <img src={story.image} alt="" loading="lazy" />
        <span className="card__cat">{story.cat}</span>
      </div>
      <div className="card__text">
        <h3>{story.title}</h3>
        <p className="when">{story.time}</p>
      </div>
    </button>
  );
}
