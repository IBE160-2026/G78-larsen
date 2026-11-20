-- Venue facts (Story 1.3, FR-1, AD-16, AD-18): name, address and contact, opening hours, Session length and the
-- price per Seat, as columns of the one `settings` row. Each new reference column gets the seed value of
-- `seeds/venue.json` as its default in this same change (AD-18); after the first start the store owns the value.
ALTER TABLE settings
  ADD COLUMN venue_name text NOT NULL DEFAULT 'Saunalöyly',
  ADD COLUMN address_lines text[] NOT NULL DEFAULT ARRAY['Badstubrygga 4', '0000 Havbukta'],
  ADD COLUMN phone text NOT NULL DEFAULT '+47 01 23 45 67',
  ADD COLUMN email text NOT NULL DEFAULT 'hello@saunaloyly.example',
  ADD COLUMN opening_time time NOT NULL DEFAULT '10:00',
  ADD COLUMN closing_time time NOT NULL DEFAULT '22:00',
  ADD COLUMN session_minutes int NOT NULL DEFAULT 90 CONSTRAINT session_minutes_positive CHECK (session_minutes > 0),
  ADD COLUMN price_per_seat_ore int NOT NULL DEFAULT 25000
    CONSTRAINT price_per_seat_not_negative CHECK (price_per_seat_ore >= 0);
