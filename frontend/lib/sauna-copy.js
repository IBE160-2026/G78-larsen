// The Sauna cards' copy on Landing, keyed by Sauna id (FR-1.5): the image, its alt text and the one line
// (EXPERIENCE.md, Open Item 2; alt texts as in ASSETS.md). The name and Capacity come from `GET /api/venue`;
// a Sauna whose id has no entry here shows its name and size line only.
export const SAUNA_COPY = Object.freeze({
  1: {
    image: '/images/sauna-rauha-door.jpg',
    alt: 'A glass sauna door with a long pale wooden handle, and a stove filled with grey stones seen through it.',
    line: 'Rauha means peace.',
  },
  2: {
    image: '/images/sauna-loyly-kiuas.jpg',
    alt: 'Steam drifting through a softly lit wooden sauna, above dark stones heaped in a square stove, with a pale bench to the right.',
    line: 'Named for the steam from the stones, like the venue.',
  },
  3: {
    image: '/images/sauna-kajo-kiulu.jpg',
    alt: 'A black sauna bucket with a curved wooden handle and a wooden-handled ladle, on a pale wooden bench.',
    line: 'Kajo means a soft glow of light.',
  },
  4: {
    image: '/images/sauna-lumo-lauteet.jpg',
    alt: 'Empty wooden sauna benches along a wall, lit softly from behind the backrest.',
    line: 'Lumo means enchantment.',
  },
});

// Every Sauna image is 1000 × 757 px.
export const SAUNA_IMAGE_SIZE = Object.freeze({ width: 1000, height: 757 });
