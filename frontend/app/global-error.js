'use client';

// Replaces the root layout when the layout itself fails, so it carries its own <html>, the page language and
// the one stylesheet (AD-17).
import TryAgain from '@/components/TryAgain';
import './styles.css';

export default function GlobalError() {
  return (
    <html lang="en">
      <body>
        <TryAgain />
      </body>
    </html>
  );
}
