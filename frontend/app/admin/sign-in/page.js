// Sign-in (FR-15, UX-DR30): the one Administrator page open to anonymous visitors, and with Book seats the only page
// that opens a browser session (AD-8). Everything happens in the client component.
import SignIn from '@/components/SignIn';

export const metadata = { title: 'Sign in' };

export default function SignInPage() {
  return <SignIn />;
}
