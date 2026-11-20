// Sauna card (UX-DR16, FR-4): image, name, size line and one line of text. Not a link and not selectable, so a
// Seat booking never seems to choose a Sauna. The name and Capacity come from the Venue facts; the image, alt
// text and line from lib/sauna-copy.js. A Sauna with no copy shows its name and size line only.
import { SAUNA_COPY, SAUNA_IMAGE_SIZE } from '@/lib/sauna-copy';
import { holds } from '@/lib/venue-format';

export default function SaunaCard({ sauna }) {
  const copy = SAUNA_COPY[sauna.id];
  return (
    <li className="sauna-card">
      {copy && (
        <img
          className="sauna-image"
          src={copy.image}
          alt={copy.alt}
          width={SAUNA_IMAGE_SIZE.width}
          height={SAUNA_IMAGE_SIZE.height}
        />
      )}
      <h3 className="heading-lg">{sauna.name}</h3>
      <p className="meta">{holds(sauna.capacity)}</p>
      {copy && <p>{copy.line}</p>}
    </li>
  );
}
