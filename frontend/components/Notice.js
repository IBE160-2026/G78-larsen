'use client';

// Notice: neutral information, never shown as an error (DESIGN.md, Components). Without children it says "please
// try again" (EXPERIENCE.md, Fixed copy).
//
// - `focusKey`: the Notice takes focus (tabindex -1) each time it changes, as after a refusal on Review, where Pay
//   held focus and may be gone (UX-DR25).
// - `block`: a <div>, for a Notice that holds more than one paragraph or a list (Nearest sessions).
import { useEffect, useRef } from 'react';

export const TRY_AGAIN = 'The page could not be shown, please try again.';

export default function Notice({ children = TRY_AGAIN, focusKey, block = false }) {
  const ref = useRef(null);
  const focusable = focusKey !== undefined;

  useEffect(() => {
    if (focusable && ref.current) ref.current.focus();
  }, [focusable, focusKey]);

  const Tag = block ? 'div' : 'p';
  return (
    <Tag className="notice" role="status" ref={ref} tabIndex={focusable ? -1 : undefined}>
      {children}
    </Tag>
  );
}
