// Booking summary (UX-DR14): label and value rows with a line between them, in tabular figures. A value may hold
// several lines (the Venue and Contact rows); each is its own line. Values are text only: React escapes them, so a
// name with a script tag shows as text (FR-18 IV-5). An email address may break only before its "@" (a <wbr>), so
// a narrow column never splits it mid-word; `overflow-wrap: anywhere` stays as the last resort for a very long one.

/** The value with a line-break opportunity before the "@" of an email address; other text as it is. */
function breakable(text) {
  if (typeof text !== 'string') return text;
  const at = text.indexOf('@');
  if (at < 1 || /\s/.test(text)) return text;
  return (
    <>
      {text.slice(0, at)}
      <wbr />
      {text.slice(at)}
    </>
  );
}

/**
 * @param {{rows: {label: string, value: string | string[]}[]}} props
 */
export default function BookingSummary({ rows }) {
  return (
    <dl className="summary">
      {rows.map(({ label, value }) => (
        <div className="summary-row" key={label}>
          <dt>{label}</dt>
          <dd>
            {Array.isArray(value)
              ? value.map((line) => (
                  <span className="summary-line" key={line}>
                    {breakable(line)}
                  </span>
                ))
              : breakable(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}
