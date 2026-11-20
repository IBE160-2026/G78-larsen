'use client';

// Error summary (UX-DR12, UX-DR33): at the top of a form's main column, in --color-error, with no title. Each entry
// with a field is a link that moves focus to that field (through `onChoose`, so a radio group can focus its chosen
// or first available radio); an entry with no field is plain text. It takes focus each time `focusKey` changes,
// and while it is on the page FocusMover starts the title with "Error: " ([data-error-summary]).
import { useEffect, useRef } from 'react';

/**
 * @param {{errors: {key: string, text: string, href?: string}[], focusKey: number,
 *          onChoose?: (key: string) => void}} props
 */
export default function ErrorSummary({ errors, focusKey, onChoose }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) ref.current.focus();
  }, [focusKey]);

  if (!errors.length) return null;
  return (
    <div className="error-summary" data-error-summary="" tabIndex={-1} ref={ref}>
      <ul>
        {errors.map((e) => (
          <li key={e.key}>
            {e.href ? (
              <a
                href={e.href}
                onClick={(event) => {
                  if (!onChoose) return;
                  event.preventDefault();
                  onChoose(e.key);
                }}
              >
                {e.text}
              </a>
            ) : (
              e.text
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
