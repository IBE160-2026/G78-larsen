"""FR-19 / PW-1 to PW-4 / AD-11 / AD-18 / AD-19: passwords are stored only as Argon2id hashes, and the one rule check
`services.auth.check_password_rules` guards the seed and `create-admin`.

- At least 15 characters after NFC, not on the packaged common list (compared lower-cased), not equal to the email
  (case-insensitive); 64 characters with spaces and non-ASCII are accepted, with no composition rules.
- The same password stored twice gives two hashes, each in PHC format `$argon2id$`, and no column holds it readably.
- The seeded Administrator exists once; a restart keeps its hash. A seed password that breaks a rule is a one-line
  `SeedError` that never shows the password.
- `create-admin` prompts (email, then the password twice without echo), creates or re-hashes, prints the email and
  "created" or "password changed", and refuses a rule break or a mismatch with one line and exit code 2, writing
  nothing. It takes no password argument.
"""

from __future__ import annotations

import builtins
import getpass
import json

import psycopg
import pytest
from argon2 import PasswordHasher

import booking_platform
from booking_platform import config
from booking_platform.services import auth, seed
from client import ADMIN_LOGIN, api_client, sign_in
from conftest import start_backend

EMAIL, PASSWORD = ADMIN_LOGIN["email"], ADMIN_LOGIN["password"]
PHC = "$argon2id$v=19$m=65536,t=3,p=4$"
GOOD_64 = "en lang setning med mellomrom og ø, æ og å som er helt i orden!!"
CLI_EMAIL = "staff.cli@saunaloyly.example"


def test_the_good_example_is_64_characters():
    assert len(GOOD_64) == 64


@pytest.mark.parametrize("password,reason", [
    ("a" * 14, "too_short"),
    ("é" * 8, "too_short"),  # 16 code points, 8 characters after NFC
    ("CristianoRonaldo", "common"),  # on the list, in another case
    ("californication", "common"),
    ("Admin@SaunaLoyly.Example", "equals_email"),
], ids=["14", "nfc", "common-case", "common", "email"])
def test_a_password_that_breaks_a_rule_is_refused(password, reason):
    with pytest.raises(auth.PasswordRuleError) as e:
        auth.check_password_rules(password, EMAIL)
    assert e.value.reason == reason


@pytest.mark.parametrize("password", ["fifteen chars!!", GOOD_64, "x" * 1024, "        " * 2, PASSWORD],
                         ids=["15", "64-spaces-and-oslash", "1024", "spaces-only", "the-seed"])
def test_any_characters_of_15_or_more_are_accepted(password):
    auth.check_password_rules(password, EMAIL)


def test_the_list_is_packaged_lower_cased_and_of_15_or_more():
    words = auth.common_passwords()
    assert len(words) > 100
    assert all(len(w) >= 15 and w == w.lower() for w in words)


@pytest.fixture
def scratch_accounts(pg):
    """Accounts made by a test are removed afterwards (the seed's stays)."""
    made: list[str] = []
    yield made
    pg.rollback()
    pg.execute("DELETE FROM accounts WHERE email = ANY(%s)", ([e.lower() for e in made],))
    pg.commit()


def test_the_same_password_for_two_accounts_gives_two_argon2id_hashes(database, pg, scratch_accounts):
    emails = ["one@saunaloyly.example", "two@saunaloyly.example"]
    scratch_accounts.extend(emails)
    with psycopg.connect(database) as c:
        for e in emails:
            assert auth.set_account(c, e, GOOD_64, overwrite=True) is True
    hashes = [pg.execute("SELECT password_hash FROM accounts WHERE email = %s", (e,)).fetchone()[0] for e in emails]
    pg.rollback()
    assert hashes[0] != hashes[1]
    assert all(h.startswith(PHC) for h in hashes)
    assert all(PasswordHasher().verify(h, GOOD_64) for h in hashes)


def test_the_seeded_administrator_has_a_phc_hash_and_no_column_holds_a_readable_password(admin, pg):
    rows = pg.execute("SELECT email, role, password_hash FROM accounts WHERE email = %s", (EMAIL,)).fetchall()
    assert len(rows) == 1 and rows[0][:2] == (EMAIL, "admin") and rows[0][2].startswith(PHC)
    cols = [r[0] for r in pg.execute("SELECT column_name FROM information_schema.columns "
                                     "WHERE table_name = 'accounts' ORDER BY ordinal_position")]
    assert cols == ["id", "email", "password_hash", "role"]
    tables = [r[0] for r in pg.execute("SELECT table_name FROM information_schema.tables "
                                       "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")]
    for t in tables:  # after a real sign-in (the `admin` fixture), no row of any table holds the password
        (n,) = pg.execute(f'SELECT count(*) FROM "{t}" x WHERE strpos(x::text, %s) > 0', (PASSWORD,)).fetchone()
        assert n == 0, t
    pg.rollback()


def test_a_restart_keeps_the_seeded_hash_and_creates_no_second_account(database, pg, tmp_path):
    before = pg.execute("SELECT id, password_hash FROM accounts WHERE email = %s", (EMAIL,)).fetchall()
    pg.rollback()
    assert len(before) == 1
    second = start_backend(database, tmp_path, name="restart", sample_bookings=False)
    second.stop()
    after = pg.execute("SELECT id, password_hash FROM accounts WHERE email = %s", (EMAIL,)).fetchall()
    pg.rollback()
    assert after == before


@pytest.mark.parametrize("password,reason", [("short password", "too_short"), ("californication", "common"),
                                             (EMAIL.upper(), "equals_email")])
def test_a_seed_password_that_breaks_a_rule_is_one_line_without_the_password(tmp_path, password, reason):
    (tmp_path / "admin.json").write_text(json.dumps({"email": EMAIL, "password": password}), encoding="utf-8")
    with pytest.raises(seed.SeedError) as e:
        seed.load_admin(tmp_path)
    msg = str(e.value)
    assert "\n" not in msg and "admin.json" in msg and reason in msg, msg
    assert password not in msg


def test_a_malformed_seed_file_never_quotes_the_password(tmp_path):
    (tmp_path / "admin.json").write_text(json.dumps({"email": EMAIL, "password": "p" * 1025}), encoding="utf-8")
    with pytest.raises(seed.SeedError) as e:
        seed.load_admin(tmp_path)
    assert "password" in str(e.value) and "ppp" not in str(e.value)


def test_the_repository_seed_passes_the_rules():
    a = seed.load_admin()
    assert (a.email, a.password) == (EMAIL, PASSWORD)


# ------------------------------------------------------------------ create-admin


@pytest.fixture
def cli(database, monkeypatch, scratch_accounts):
    """Run `main(["create-admin"])` against the test database with the prompts answered: `answers` is the email and
    the two passwords."""
    monkeypatch.setenv("BP_DATABASE_URL", database)
    config.settings.cache_clear()
    scratch_accounts.append(CLI_EMAIL)

    def run(email: str | None, first: str, second: str | None = None):
        """`email=None`: the email prompt meets the end of input (EOF)."""
        passwords = iter([first, first if second is None else second])
        prompts = []

        def answer(prompt=""):
            prompts.append(prompt)
            if email is None:
                raise EOFError
            return email

        monkeypatch.setattr(builtins, "input", answer)
        monkeypatch.setattr(getpass, "getpass", lambda prompt="": prompts.append(prompt) or next(passwords))
        booking_platform.main(["create-admin"])
        return prompts

    yield run
    config.settings.cache_clear()


def stored_hash(pg, email=CLI_EMAIL):
    row = pg.execute("SELECT password_hash FROM accounts WHERE email = %s", (email,)).fetchone()
    pg.rollback()
    return row[0] if row else None


def test_create_admin_creates_then_changes_the_password(cli, pg, capsys):
    prompts = cli(CLI_EMAIL.upper(), GOOD_64)
    assert prompts == ["Email: ", "Password: ", "Password again: "]
    out = capsys.readouterr()
    assert out.out.strip() == f"{CLI_EMAIL}: created"
    first = stored_hash(pg)
    assert first.startswith(PHC) and PasswordHasher().verify(first, GOOD_64)
    assert pg.execute("SELECT role FROM accounts WHERE email = %s", (CLI_EMAIL,)).fetchone() == ("admin",)
    pg.rollback()

    cli(CLI_EMAIL, "another long password for staff")
    out = capsys.readouterr()
    assert out.out.strip() == f"{CLI_EMAIL}: password changed"
    assert GOOD_64 not in out.out + out.err and "another long" not in out.out + out.err
    second = stored_hash(pg)
    assert second != first and PasswordHasher().verify(second, "another long password for staff")


@pytest.mark.parametrize("email,first,second,words", [
    (CLI_EMAIL, "fourteen chars", None, "too_short"),
    (CLI_EMAIL, "californication", None, "common"),
    (CLI_EMAIL, CLI_EMAIL.upper(), None, "equals_email"),
    (CLI_EMAIL, GOOD_64, GOOD_64 + "!", "differ"),
    ("staff.cli at saunaloyly", GOOD_64, None, "not an email"),
    (CLI_EMAIL, "p" * 1025, None, "longer than 1024"),
    (None, GOOD_64, None, "cancelled"),
], ids=["short", "common", "email", "mismatch", "bad-email", "too-long", "eof"])
def test_create_admin_refuses_with_one_line_exit_2_and_writes_nothing(cli, pg, capsys, email, first, second, words):
    with pytest.raises(SystemExit) as e:
        cli(email, first, second)
    assert e.value.code == 2
    out = capsys.readouterr()
    lines = out.err.strip().splitlines()
    assert len(lines) == 1 and words in lines[0], out.err
    assert first not in out.out + out.err and out.out == ""
    assert stored_hash(pg) is None


def test_a_changed_password_signs_the_account_out_everywhere(cli, admin, world, database, capsys):
    """`create-admin` for an account that is signed in: its sessions end in the same transaction (the new hash must
    not leave the old sign-in valid)."""
    with psycopg.connect(database) as c:
        auth.set_account(c, CLI_EMAIL, GOOD_64, overwrite=True)
    with api_client(world) as staff:
        assert sign_in(staff, CLI_EMAIL, GOOD_64).status_code == 200
        assert staff.get("/api/admin/me").status_code == 200
        cli(CLI_EMAIL, "another long password for staff")
        assert capsys.readouterr().out.strip() == f"{CLI_EMAIL}: password changed"
        r = staff.get("/api/admin/me")
        assert r.status_code == 401 and r.json() == {"detail": {"error": "not_signed_in"}}
    assert admin.get("/api/admin/me").status_code == 200  # another account's sign-in is untouched


def test_create_admin_takes_no_password_argument(capsys):
    with pytest.raises(SystemExit) as e:
        booking_platform.main(["create-admin", "--password", GOOD_64])
    assert e.value.code == 2
