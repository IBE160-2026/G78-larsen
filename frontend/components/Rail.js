// Rail (UX-DR8): the shell's left column, in --color-page with no fill or border of its own. Its contents
// stack in one column: Wordmark, then the page's facts or total, the action, then notes. Sticky on laptop.
export default function Rail({ children }) {
  return (
    <header className="rail">
      <div className="rail-inner">{children}</div>
    </header>
  );
}
