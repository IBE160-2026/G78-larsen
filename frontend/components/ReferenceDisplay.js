// Reference display (UX-DR14): the 8-character Booking reference in heading-lg with tabular figures, selectable, its
// label above. It opens nothing by itself (FR-8).
import { CONFIRMATION } from '@/lib/copy';

export default function ReferenceDisplay({ reference }) {
  return (
    <div className="reference-box">
      <p className="reference-label">{CONFIRMATION.reference}</p>
      <p className="reference">{reference}</p>
    </div>
  );
}
