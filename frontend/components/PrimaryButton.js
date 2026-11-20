// Primary button (UX-DR5): the one action on a page. With `href` it navigates (a link styled as the button, as
// Book seats on Landing); without, it is a <button>. Full width of its column in the rail (app/styles.css).
import Link from 'next/link';

export default function PrimaryButton({ href, children, type = 'button', ...props }) {
  if (href) {
    return (
      <Link className="button-primary" href={href}>
        {children}
      </Link>
    );
  }
  return (
    <button className="button-primary" type={type} {...props}>
      {children}
    </button>
  );
}
