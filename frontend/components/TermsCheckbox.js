// Terms checkbox (UX-DR10): never pre-ticked; the checkbox sits inside its label, so the whole line is the target.
// With `error`, the Field error sits under it and the box refers to it (aria-describedby).
import FieldError from './FieldError';
import { REVIEW } from '@/lib/copy';

export default function TermsCheckbox({ checked, onChange, error }) {
  return (
    <div className="terms-check-field">
      <label className="terms-check">
        <input
          id="terms"
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error ? 'terms-error' : undefined}
        />
        {REVIEW.accept}
      </label>
      <FieldError id="terms-error">{error}</FieldError>
    </div>
  );
}
