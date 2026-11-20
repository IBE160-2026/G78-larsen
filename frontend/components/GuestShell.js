// The Guest shell (UX-DR3): a sticky rail plus a main column, centred up to --page-max. Main comes first in
// the source, so the rail is last in tab order while it is drawn on the left (EXPERIENCE.md, Accessibility
// Floor). The layout lives in app/styles.css (.shell, .rail, .main).
import Rail from './Rail';

export default function GuestShell({ rail, children }) {
  return (
    <div className="shell">
      <main id="main" className="main">
        {children}
      </main>
      <Rail>{rail}</Rail>
    </div>
  );
}
