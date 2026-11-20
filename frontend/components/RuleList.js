// Rule list (UX-DR16): a group title and its items, static text with no bullets ("Before you come" on Landing).
export default function RuleList({ title, items }) {
  return (
    <div className="rule-list">
      <h3 className="heading-md">{title}</h3>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
