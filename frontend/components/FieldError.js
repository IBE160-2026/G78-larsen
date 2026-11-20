// Field error (UX-DR12, UX-DR34): hint-sized text in --color-error directly under its field. The field refers to
// it with aria-describedby; the field's border does not change.
export default function FieldError({ id, children }) {
  if (!children) return null;
  return (
    <p className="field-error" id={id}>
      {children}
    </p>
  );
}
