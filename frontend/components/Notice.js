// Notice: neutral information, never shown as an error (DESIGN.md, Components). This story has one
// variant, "please try again" (EXPERIENCE.md, Fixed copy); later stories add theirs here.
export const TRY_AGAIN = 'The page could not be shown, please try again.';

export default function Notice({ children = TRY_AGAIN }) {
  return (
    <p className="notice" role="status">
      {children}
    </p>
  );
}
