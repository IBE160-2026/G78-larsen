// Booking summary (UX-DR14): label and value rows with a line between them, in tabular figures. A value may hold
// several lines (the Venue and Contact rows); each is its own line. Values are text only: React escapes them, so a
// name with a script tag shows as text (FR-18 IV-5).
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
                    {line}
                  </span>
                ))
              : value}
          </dd>
        </div>
      ))}
    </dl>
  );
}
