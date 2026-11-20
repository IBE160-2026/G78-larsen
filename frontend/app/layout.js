// The root layout (AD-17): English page language, the one stylesheet, the <noscript> line and the one client
// component that moves focus and keeps the "Error: " title prefix (UX-DR33).
import FocusMover from '@/components/FocusMover';
import './styles.css';

// Each page's title is "<h1> – Saunalöyly" (UX-DR33). No default: Landing sets its own, and the error pages set
// theirs with React's <title> element, which a default here would override.
export const metadata = {
  title: {
    template: '%s – Saunalöyly',
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <noscript>
          <p className="noscript">This booking page needs JavaScript.</p>
        </noscript>
        <FocusMover />
        {children}
      </body>
    </html>
  );
}
