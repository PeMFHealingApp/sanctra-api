from flask import Flask, jsonify, request
import numpy as np
import scipy.signal as signal
import os

app = Flask(__name__)

# Dictionary of sacred sites with RT60, dimensions, and geometry notes
SACRED_SITES = {
    "Great Pyramid King's Chamber": {
    "rt60": 2.5,
    "dims": [10.47, 5.235, 5.827],
    "geometry": "Golden ratio (height:width≈φ/2), length:width=2:1, ~121 Hz resonance",
    "description": "The King's Chamber is a remarkable granite room in the Great Pyramid of Giza, an architectural marvel supporting massive weight and featuring a sarcophagus, special for its potential astronomical alignments and symbolic representation of heavenly redemption.",
    "benefits": "Provides meditative resonance for spiritual initiation and relaxation; ideal for those seeking ancient mysteries or sound therapy.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
    "Great Pyramid Queen's Chamber": {
        "rt60": 1.5,
        "dims": [5.75, 5.23, 6.23],
        "geometry": "Similar to King’s; sqrt(5) in height; niche ratios follow φ"
    },
    "Great Pyramid Grand Gallery": {
        "rt60": 3.5,
        "dims": [46.68, 2.09, 8.68],
        "geometry": "Slope angle ~26° (seked 5.5, related to sqrt(φ)); length:height≈φ^2"
    },
    "Pyramid of Khafre": {
        "rt60": 2.5,
        "dims": [10.0, 5.0, 6.0],
        "geometry": "Pi/phi integrations like Great Pyramid"
    },
    "Abu Simbel Temple": {
        "rt60": 5.0,
        "dims": [18.0, 16.4, 8.0],
        "geometry": "Rock-cut with solar alignments; ratios 9:5 (≈φ)"
    },
    "Karnak Temple Hypostyle Hall": {
        "rt60": 6.5,
        "dims": [50.0, 103.0, 24.0],
        "geometry": "Column grid follows 1:√2; vast scale encodes solar ratios"
    },
    "Luxor Temple": {
        "rt60": 5.0,
        "dims": [190.0, 55.0, 15.0],
        "geometry": "Avenue aligns with Nile; pylon ratios 4:3 (fifth interval)"
    },
    "Dendera Temple of Hathor": {
        "rt60": 4.0,
        "dims": [10.0, 8.0, 6.0],
        "geometry": "Zodiac ceiling; vesica piscis in layouts"
    },
    "Philae Temple": {
        "rt60": 5.0,
        "dims": [32.0, 18.0, 12.0],
        "geometry": "Island layout; golden spiral in colonnades"
    },
    "Kailasa Temple Ellora": {
        "rt60": 4.0,
        "dims": [60.0, 30.0, 33.0],
        "geometry": "Rock-cut mandala; ratios 1:φ:φ^2 (Fibonacci)"
    },
    "Konark Sun Temple": {
        "rt60": 5.0,
        "dims": [229.0, 128.0, 20.0],
        "geometry": "Chariot form; 12 wheels (zodiac), ratios 7:4 (solar)"
    },
    "Brihadeeswarar Temple": {
        "rt60": 6.0,
        "dims": [60.0, 30.0, 30.0],
        "geometry": "Height:base≈2:1; shikhara follows sqrt(2)"
    },
    "Meenakshi Temple": {
        "rt60": 5.0,
        "dims": [50.0, 30.0, 15.0],
        "geometry": "Gopuram ratios φ; mandala plan"
    },
    "Golden Temple": {
        "rt60": 4.0,
        "dims": [20.0, 20.0, 15.0],
        "geometry": "Square (stability); dome φ curve"
    },
    "Jagannath Temple": {
        "rt60": 5.0,
        "dims": [65.0, 20.0, 20.0],
        "geometry": "Vimana ratios 3:2 (fifth)"
    },
    "Kandariya Mahadev": {
        "rt60": 4.0,
        "dims": [31.0, 15.0, 15.0],
        "geometry": "Shikharas in φ progression"
    },
    "Kashi Vishwanath": {
        "rt60": 3.0,
        "dims": [10.0, 8.0, 12.0],
        "geometry": "Lingam alignment; sqrt(3) in dome"
    },
    "Ramanathaswamy Temple": {
        "rt60": 6.0,
        "dims": [205.0, 10.0, 5.0],
        "geometry": "Pillar grid 5:3; infinite perspective (φ)"
    },
    "Virupaksha Temple": {
        "rt60": 5.0,
        "dims": [50.0, 25.0, 15.0],
        "geometry": "Ratios 2:1; ruins alignment"
    },
    "Ajanta Caves": {
        "rt60": 4.0,
        "dims": [35.0, 11.0, 10.0],
        "geometry": "Chaitya arch vesica piscis"
    },
    "Elephanta Caves": {
        "rt60": 4.0,
        "dims": [35.0, 11.0, 10.0],
        "geometry": "Trimurti sculpture φ proportions"
    },
    "Mahabodhi Temple": {
        "rt60": 3.5,
        "dims": [55.0, 15.0, 15.0],
        "geometry": "Pyramid ratios 4:3; stupa circle"
    },
    "Jokhang Temple": {
        "rt60": 5.0,
        "dims": [20.0, 15.0, 10.0],
        "geometry": "Mandala plan; 8:5 (minor sixth)"
    },
    "Potala Palace Chapel": {
        "rt60": 4.0,
        "dims": [8.0, 6.0, 5.0],
        "geometry": "Golden section in tiers"
    },
    "Tashi Lhunpo Monastery": {
        "rt60": 6.0,
        "dims": [30.0, 20.0, 15.0],
        "geometry": "Ratios 3:2; monastic grid"
    },
    "Boudhanath Stupa Gallery": {
        "rt60": 3.0,
        "dims": [36.0, 10.0, 5.0],
        "geometry": "Circle/square mandala; φ spiral"
    },
    "Swayambhunath Caves": {
        "rt60": 4.0,
        "dims": [10.0, 5.0, 4.0],
        "geometry": "Hill alignments; vesica piscis"
    },
    "Mount Kailash Caves": {
        "rt60": 3.0,
        "dims": [10.0, 5.0, 4.0],
        "geometry": "Sacred mountain circuit 1:φ"
    },
    "Angkor Wat Outer Galleries": {
        "rt60": 5.0,
        "dims": [187.0, 215.0, 10.0],
        "geometry": "4:5 & 6:7 rectangles (multiples of 216m, precessional); cosmic mountain model"
    },
    "Angkor Wat Inner Sanctum": {
        "rt60": 4.0,
        "dims": [10.0, 10.0, 12.0],
        "geometry": "Central tower φ proportions"
    },
    "Bayon Temple": {
        "rt60": 5.0,
        "dims": [45.0, 45.0, 15.0],
        "geometry": "Face towers in mandala; 3:4:5 triangle"
    },
    "Ta Prohm": {
        "rt60": 4.0,
        "dims": [50.0, 30.0, 10.0],
        "geometry": "Tree-integrated φ spirals"
    },
    "Preah Khan": {
        "rt60": 5.0,
        "dims": [50.0, 30.0, 10.0],
        "geometry": "Linear alignments; golden mean"
    },
    "Borobudur Central Stupa": {
        "rt60": 3.0,
        "dims": [10.0, 10.0, 10.0],
        "geometry": "Mandala squares/circles; 9 levels (sacred 9)"
    },
    "Borobudur Upper Terraces": {
        "rt60": 2.0,
        "dims": [123.0, 123.0, 5.0],
        "geometry": "Ratios 5:4 (third); fractal stupas"
    },
    "Prambanan Temple": {
        "rt60": 4.0,
        "dims": [47.0, 47.0, 15.0],
        "geometry": "Trimurti triangles; φ in spires"
    },
    "Tanah Lot Shrine": {
        "rt60": 3.0,
        "dims": [10.0, 10.0, 5.0],
        "geometry": "Sea alignments; wave harmonics"
    },
    "Temple of Heaven": {
        "rt60": 5.0,
        "dims": [38.0, 38.0, 38.0],
        "geometry": "Circle (heaven); 3 tiers, ratios 9:3:1 (sacred 9)"
    },
    "Mogao Caves": {
        "rt60": 4.0,
        "dims": [5.0, 4.0, 3.0],
        "geometry": "Buddhist mandalas; vesica piscis"
    },
    "Longmen Grottoes": {
        "rt60": 3.0,
        "dims": [5.0, 4.0, 3.0],
        "geometry": "Rock-cut φ proportions"
    },
    "Todai-ji Daibutsuden": {
        "rt60": 6.5,
        "dims": [57.0, 50.0, 48.0],
        "geometry": "Golden Buddha; hall ratios 6:5"
    },
    "Horyu-ji": {
        "rt60": 5.0,
        "dims": [32.0, 20.0, 15.0],
        "geometry": "Fibonacci tiers; sqrt(2) base"
    },
    "Kiyomizu-dera": {
        "rt60": 4.0,
        "dims": [13.0, 20.0, 10.0],
        "geometry": "Balcony alignments; 3:4:5"
    },
    "Fushimi Inari": {
        "rt60": 3.0,
        "dims": [50.0, 5.0, 5.0],
        "geometry": "Torii arcs; infinite φ perspective"
    },
    "Parthenon": {
        "rt60": 3.0,
        "dims": [69.5, 30.9, 13.7],
        "geometry": "Facade golden ratio (width:height≈φ); 4:9 base (≈2.25:1)"
    },
    "Temple of Apollo Delphi": {
        "rt60": 4.0,
        "dims": [23.0, 11.0, 9.0],
        "geometry": "Oracle ratios 2:1; mountain phi"
    },
    "Theatre o"Great Pyramid King's Chamber": {
    "rt60": 2.5,
    "dims": [10.47, 5.235, 5.827],
    "geometry": "Golden ratio (height:width≈φ/2), length:width=2:1, ~121 Hz resonance",
    "description": "The King's Chamber in the Great Pyramid of Giza, a granite marvel with a sarcophagus, is special for its astronomical alignments and symbolic spiritual transformation.",
    "benefits": "Promotes deep meditation and spiritual awakening; ideal for those exploring ancient mysteries or sound therapy.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Great Pyramid Queen's Chamber": {
    "rt60": 1.5,
    "dims": [5.75, 5.23, 6.23],
    "geometry": "Similar to King’s; sqrt(5) in height; niche ratios follow φ",
    "description": "The Queen's Chamber in the Great Pyramid is a compact space with niche alignments, revered for its mystical resonance.",
    "benefits": "Supports introspection and calmness; suitable for meditators seeking inner peace.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Great Pyramid Grand Gallery": {
    "rt60": 3.5,
    "dims": [46.68, 2.09, 8.68],
    "geometry": "Slope angle ~26° (seked 5.5, related to sqrt(φ)); length:height≈φ^2",
    "description": "The Grand Gallery, a soaring corridor in the Great Pyramid, is notable for its precise engineering and cosmic symbolism.",
    "benefits": "Enhances focus and spiritual connection; ideal for those drawn to ancient architecture.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Pyramid of Khafre": {
    "rt60": 2.5,
    "dims": [10.0, 5.0, 6.0],
    "geometry": "Pi/phi integrations like Great Pyramid",
    "description": "The Pyramid of Khafre, with its intact casing stones, is special for its solar alignments and enduring grandeur.",
    "benefits": "Fosters grounding and stability; great for those seeking balance through sound meditation.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Abu Simbel Temple": {
    "rt60": 5.0,
    "dims": [18.0, 16.4, 8.0],
    "geometry": "Rock-cut with solar alignments; ratios 9:5 (≈φ)",
    "description": "Abu Simbel’s rock-cut temples, aligned with the sun, are renowned for their colossal statues and sacred precision.",
    "benefits": "Promotes spiritual alignment and awe; ideal for meditators and history enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Karnak Temple Hypostyle Hall": {
    "rt60": 6.5,
    "dims": [50.0, 103.0, 24.0],
    "geometry": "Column grid follows 1:√2; vast scale encodes solar ratios",
    "description": "Karnak’s Hypostyle Hall, with its towering columns, is a monumental space embodying cosmic order.",
    "benefits": "Enhances contemplation and cosmic connection; suitable for spiritual seekers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Luxor Temple": {
    "rt60": 5.0,
    "dims": [190.0, 55.0, 15.0],
    "geometry": "Avenue aligns with Nile; pylon ratios 4:3 (fifth interval)",
    "description": "Luxor Temple, aligned with the Nile, is celebrated for its sacred geometry and ceremonial significance.",
    "benefits": "Supports emotional balance and ritual focus; ideal for meditators and cultural explorers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Dendera Temple of Hathor": {
    "rt60": 4.0,
    "dims": [10.0, 8.0, 6.0],
    "geometry": "Zodiac ceiling; vesica piscis in layouts",
    "description": "Dendera’s Temple of Hathor, with its zodiac ceiling, is special for its celestial symbolism and divine feminine energy.",
    "benefits": "Fosters creativity and spiritual insight; great for artists and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Philae Temple": {
    "rt60": 5.0,
    "dims": [32.0, 18.0, 12.0],
    "geometry": "Island layout; golden spiral in colonnades",
    "description": "Philae Temple, on its sacred island, is revered for its connection to Isis and harmonious design.",
    "benefits": "Promotes emotional healing and serenity; ideal for those seeking divine feminine resonance.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Kailasa Temple Ellora": {
    "rt60": 4.0,
    "dims": [60.0, 30.0, 33.0],
    "geometry": "Rock-cut mandala; ratios 1:φ:φ^2 (Fibonacci)",
    "description": "Kailasa Temple, a rock-cut marvel in Ellora, is special for its intricate carvings and cosmic mandala layout.",
    "benefits": "Enhances spiritual focus and creativity; ideal for meditators and art enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Konark Sun Temple": {
    "rt60": 5.0,
    "dims": [229.0, 128.0, 20.0],
    "geometry": "Chariot form; 12 wheels (zodiac), ratios 7:4 (solar)",
    "description": "Konark Sun Temple, shaped as a cosmic chariot, is celebrated for its solar alignments and intricate carvings.",
    "benefits": "Boosts vitality and inspiration; suitable for those seeking solar energy and creativity.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Brihadeeswarar Temple": {
    "rt60": 6.0,
    "dims": [60.0, 30.0, 30.0],
    "geometry": "Height:base≈2:1; shikhara follows sqrt(2)",
    "description": "Brihadeeswarar Temple, with its towering shikhara, is a Chola masterpiece embodying divine grandeur.",
    "benefits": "Promotes strength and spiritual elevation; ideal for meditators and cultural historians.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Meenakshi Temple": {
    "rt60": 5.0,
    "dims": [50.0, 30.0, 15.0],
    "geometry": "Gopuram ratios φ; mandala plan",
    "description": "Meenakshi Temple in Madurai is renowned for its vibrant gopurams and divine feminine energy.",
    "benefits": "Fosters love and spiritual connection; great for devotees and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Golden Temple": {
    "rt60": 4.0,
    "dims": [20.0, 20.0, 15.0],
    "geometry": "Square (stability); dome φ curve",
    "description": "The Golden Temple, a Sikh sacred site, is special for its golden dome and serene sarovar.",
    "benefits": "Promotes peace and unity; ideal for spiritual seekers and community-focused meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Jagannath Temple": {
    "rt60": 5.0,
    "dims": [65.0, 20.0, 20.0],
    "geometry": "Vimana ratios 3:2 (fifth)",
    "description": "Jagannath Temple in Puri is revered for its vibrant festivals and divine trinity worship.",
    "benefits": "Enhances devotion and joy; suitable for spiritual practitioners and festival enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Kandariya Mahadev": {
    "rt60": 4.0,
    "dims": [31.0, 15.0, 15.0],
    "geometry": "Shikharas in φ progression",
    "description": "Kandariya Mahadev in Khajuraho is famous for its ornate shikharas and tantric symbolism.",
    "benefits": "Supports spiritual transformation and creativity; ideal for meditators and art lovers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Kashi Vishwanath": {
    "rt60": 3.0,
    "dims": [10.0, 8.0, 12.0],
    "geometry": "Lingam alignment; sqrt(3) in dome",
    "description": "Kashi Vishwanath in Varanasi is a sacred Shiva temple, revered for its spiritual potency.",
    "benefits": "Fosters liberation and divine connection; great for devotees and spiritual seekers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Ramanathaswamy Temple": {
    "rt60": 6.0,
    "dims": [205.0, 10.0, 5.0],
    "geometry": "Pillar grid 5:3; infinite perspective (φ)",
    "description": "Ramanathaswamy Temple is known for its long corridor and sacred lingam, tied to Ramayana legends.",
    "benefits": "Promotes purification and spiritual focus; ideal for pilgrims and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Virupaksha Temple": {
    "rt60": 5.0,
    "dims": [50.0, 25.0, 15.0],
    "geometry": "Ratios 2:1; ruins alignment",
    "description": "Virupaksha Temple in Hampi is a living Shiva shrine with intricate Vijayanagara architecture.",
    "benefits": "Enhances devotion and grounding; suitable for spiritual practitioners and history buffs.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Ajanta Caves": {
    "rt60": 4.0,
    "dims": [35.0, 11.0, 10.0],
    "geometry": "Chaitya arch vesica piscis",
    "description": "Ajanta Caves are famed for their Buddhist rock-cut architecture and vibrant frescoes.",
    "benefits": "Promotes peace and artistic inspiration; ideal for meditators and art enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Elephanta Caves": {
    "rt60": 4.0,
    "dims": [35.0, 11.0, 10.0],
    "geometry": "Trimurti sculpture φ proportions",
    "description": "Elephanta Caves feature a grand Trimurti Shiva sculpture, symbolizing cosmic balance.",
    "benefits": "Fosters spiritual harmony and creativity; great for meditators and cultural explorers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Mahabodhi Temple": {
    "rt60": 3.5,
    "dims": [55.0, 15.0, 15.0],
    "geometry": "Pyramid ratios 4:3; stupa circle",
    "description": "Mahabodhi Temple marks the site of Buddha’s enlightenment, revered for its sacred Bodhi tree.",
    "benefits": "Supports mindfulness and enlightenment; ideal for Buddhists and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Jokhang Temple": {
    "rt60": 5.0,
    "dims": [20.0, 15.0, 10.0],
    "geometry": "Mandala plan; 8:5 (minor sixth)",
    "description": "Jokhang Temple in Lhasa is Tibet’s holiest site, housing the sacred Jowo Buddha statue.",
    "benefits": "Promotes spiritual clarity and devotion; suitable for Buddhists and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Potala Palace Chapel": {
    "rt60": 4.0,
    "dims": [8.0, 6.0, 5.0],
    "geometry": "Golden section in tiers",
    "description": "The Potala Palace Chapel, a sacred space in Lhasa, is revered for its spiritual aura.",
    "benefits": "Fosters inner peace and contemplation; ideal for meditators and Tibetan culture enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Tashi Lhunpo Monastery": {
    "rt60": 6.0,
    "dims": [30.0, 20.0, 15.0],
    "geometry": "Ratios 3:2; monastic grid",
    "description": "Tashi Lhunpo Monastery is a key Tibetan Buddhist site, home to the Panchen Lama’s teachings.",
    "benefits": "Enhances spiritual learning and serenity; great for Buddhists and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Boudhanath Stupa Gallery": {
    "rt60": 3.0,
    "dims": [36.0, 10.0, 5.0],
    "geometry": "Circle/square mandala; φ spiral",
    "description": "Boudhanath Stupa in Kathmandu is a massive mandala, revered for its spiritual energy.",
    "benefits": "Promotes peace and mindfulness; ideal for Buddhists and meditation practitioners.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Swayambhunath Caves": {
    "rt60": 4.0,
    "dims": [10.0, 5.0, 4.0],
    "geometry": "Hill alignments; vesica piscis",
    "description": "Swayambhunath, the Monkey Temple, is special for its hilltop stupa and ancient caves.",
    "benefits": "Supports spiritual clarity and grounding; suitable for meditators and pilgrims.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Mount Kailash Caves": {
    "rt60": 3.0,
    "dims": [10.0, 5.0, 4.0],
    "geometry": "Sacred mountain circuit 1:φ",
    "description": "Mount Kailash’s caves are sacred for their connection to the revered Himalayan pilgrimage.",
    "benefits": "Enhances spiritual journey and resilience; ideal for adventurers and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Angkor Wat Outer Galleries": {
    "rt60": 5.0,
    "dims": [187.0, 215.0, 10.0],
    "geometry": "4:5 & 6:7 rectangles (multiples of 216m, precessional); cosmic mountain model",
    "description": "Angkor Wat’s outer galleries, part of a vast temple, reflect cosmic order and Khmer artistry.",
    "benefits": "Promotes awe and spiritual alignment; great for meditators and history enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Angkor Wat Inner Sanctum": {
    "rt60": 4.0,
    "dims": [10.0, 10.0, 12.0],
    "geometry": "Central tower φ proportions",
    "description": "Angkor Wat’s inner sanctum is a sacred core, symbolizing the cosmic center of the universe.",
    "benefits": "Fosters spiritual focus and balance; ideal for meditators and cultural explorers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Bayon Temple": {
    "rt60": 5.0,
    "dims": [45.0, 45.0, 15.0],
    "geometry": "Face towers in mandala; 3:4:5 triangle",
    "description": "Bayon Temple’s smiling face towers create a serene, meditative atmosphere in Angkor.",
    "benefits": "Enhances compassion and mindfulness; suitable for Buddhists and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Ta Prohm": {
    "rt60": 4.0,
    "dims": [50.0, 30.0, 10.0],
    "geometry": "Tree-integrated φ spirals",
    "description": "Ta Prohm, entwined with ancient trees, is special for its mystical, nature-infused ruins.",
    "benefits": "Promotes grounding and connection to nature; ideal for eco-spiritual meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Preah Khan": {
    "rt60": 5.0,
    "dims": [50.0, 30.0, 10.0],
    "geometry": "Linear alignments; golden mean",
    "description": "Preah Khan in Angkor is a sprawling temple with sacred alignments and serene courtyards.",
    "benefits": "Supports spiritual exploration and calm; great for meditators and historians.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Borobudur Central Stupa": {
    "rt60": 3.0,
    "dims": [10.0, 10.0, 10.0],
    "geometry": "Mandala squares/circles; 9 levels (sacred 9)",
    "description": "Borobudur’s central stupa is a Buddhist monument symbolizing the path to enlightenment.",
    "benefits": "Fosters mindfulness and spiritual growth; ideal for Buddhists and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Borobudur Upper Terraces": {
    "rt60": 2.0,
    "dims": [123.0, 123.0, 5.0],
    "geometry": "Ratios 5:4 (third); fractal stupas",
    "description": "Borobudur’s upper terraces feature stupas in a mandala layout, embodying cosmic harmony.",
    "benefits": "Promotes peace and enlightenment; suitable for spiritual seekers and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Prambanan Temple": {
    "rt60": 4.0,
    "dims": [47.0, 47.0, 15.0],
    "geometry": "Trimurti triangles; φ in spires",
    "description": "Prambanan’s Hindu temple complex is renowned for its towering spires and divine trimurti.",
    "benefits": "Enhances devotion and spiritual focus; great for Hindus and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Tanah Lot Shrine": {
    "rt60": 3.0,
    "dims": [10.0, 10.0, 5.0],
    "geometry": "Sea alignments; wave harmonics",
    "description": "Tanah Lot, a sea temple, is special for its oceanfront setting and spiritual resonance.",
    "benefits": "Promotes tranquility and connection to nature; ideal for meditators and coastal enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Temple of Heaven": {
    "rt60": 5.0,
    "dims": [38.0, 38.0, 38.0],
    "geometry": "Circle (heaven); 3 tiers, ratios 9:3:1 (sacred 9)",
    "description": "The Temple of Heaven in Beijing is a circular complex symbolizing cosmic unity.",
    "benefits": "Fosters harmony and spiritual alignment; suitable for meditators and cultural explorers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Mogao Caves": {
    "rt60": 4.0,
    "dims": [5.0, 4.0, 3.0],
    "geometry": "Buddhist mandalas; vesica piscis",
    "description": "Mogao Caves, with Buddhist art, are a treasure of spiritual and artistic heritage.",
    "benefits": "Enhances contemplation and creativity; ideal for Buddhists and art lovers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Longmen Grottoes": {
    "rt60": 3.0,
    "dims": [5.0, 4.0, 3.0],
    "geometry": "Rock-cut φ proportions",
    "description": "Longmen Grottoes feature vast Buddhist carvings, symbolizing spiritual devotion.",
    "benefits": "Promotes peace and artistic inspiration; great for meditators and historians.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Todai-ji Daibutsuden": {
    "rt60": 6.5,
    "dims": [57.0, 50.0, 48.0],
    "geometry": "Golden Buddha; hall ratios 6:5",
    "description": "Todai-ji’s Daibutsuden houses a giant Buddha, a pinnacle of Japanese Buddhist architecture.",
    "benefits": "Fosters serenity and reverence; ideal for Buddhists and spiritual seekers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Horyu-ji": {
    "rt60": 5.0,
    "dims": [32.0, 20.0, 15.0],
    "geometry": "Fibonacci tiers; sqrt(2) base",
    "description": "Horyu-ji, one of Japan’s oldest temples, is revered for its ancient Buddhist heritage.",
    "benefits": "Promotes mindfulness and historical connection; suitable for meditators and scholars.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Kiyomizu-dera": {
    "rt60": 4.0,
    "dims": [13.0, 20.0, 10.0],
    "geometry": "Balcony alignments; 3:4:5",
    "description": "Kiyomizu-dera’s wooden stage offers stunning views and spiritual significance in Kyoto.",
    "benefits": "Enhances clarity and peace; ideal for meditators and nature lovers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Fushimi Inari": {
    "rt60": 3.0,
    "dims": [50.0, 5.0, 5.0],
    "geometry": "Torii arcs; infinite φ perspective",
    "description": "Fushimi Inari’s endless torii gates create a sacred path for Shinto worship in Kyoto.",
    "benefits": "Promotes spiritual journey and focus; great for Shinto devotees and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Parthenon": {
    "rt60": 3.0,
    "dims": [69.5, 30.9, 13.7],
    "geometry": "Facade golden ratio (width:height≈φ); 4:9 base (≈2.25:1)",
    "description": "The Parthenon in Athens is a Doric masterpiece, embodying classical Greek harmony.",
    "benefits": "Fosters balance and intellectual clarity; ideal for meditators and classical scholars.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Temple of Apollo Delphi": {
    "rt60": 4.0,
    "dims": [23.0, 11.0, 9.0],
    "geometry": "Oracle ratios 2:1; mountain phi",
    "description": "The Temple of Apollo at Delphi, an oracle site, is revered for its prophetic legacy.",
    "benefits": "Enhances intuition and spiritual insight; suitable for meditators and mystics.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Theatre of Epidaurus": {
    "rt60": 1.5,
    "dims": [114.0, 114.0, 10.0],
    "geometry": "Rows φ progression; perfect acoustics",
    "description": "Epidaurus Theatre is famed for its exceptional acoustics and healing sanctuary.",
    "benefits": "Promotes harmony and healing; great for meditators and performance enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Meteora Monasteries": {
    "rt60": 4.0,
    "dims": [10.0, 8.0, 6.0],
    "geometry": "Cliff mandalas; 3:5 ratios",
    "description": "Meteora’s cliff-top monasteries in Greece are spiritual havens of solitude and beauty.",
    "benefits": "Fosters contemplation and spiritual retreat; ideal for meditators and pilgrims.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Hosios Loukas Monastery": {
    "rt60": 5.0,
    "dims": [15.0, 10.0, 10.0],
    "geometry": "Byzantine circles/squares",
    "description": "Hosios Loukas is a Byzantine gem with stunning mosaics and spiritual serenity.",
    "benefits": "Promotes peace and artistic inspiration; suitable for meditators and art lovers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Pantheon": {
    "rt60": 7.0,
    "dims": [43.3, 43.3, 43.3],
    "geometry": "Perfect sphere; oculus:base=1:6; proportions 1:1:√2",
    "description": "The Pantheon in Rome, with its iconic dome and oculus, embodies cosmic harmony.",
    "benefits": "Fosters awe and spiritual connection; ideal for meditators and architecture enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"St. Peter’s Basilica": {
    "rt60": 9.0,
    "dims": [136.0, 42.0, 42.0],
    "geometry": "Michelangelo φ in dome; cross plan",
    "description": "St. Peter’s Basilica, with its grand dome, is a pinnacle of Christian architecture.",
    "benefits": "Promotes reverence and spiritual upliftment; great for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Florence Cathedral": {
    "rt60": 8.0,
    "dims": [114.0, 45.0, 45.0],
    "geometry": "Brunelleschi octagon; φ ratios",
    "description": "Florence Cathedral’s iconic dome by Brunelleschi is a Renaissance architectural marvel.",
    "benefits": "Enhances creativity and spiritual awe; ideal for meditators and art historians.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Basilica di San Marco": {
    "rt60": 6.0,
    "dims": [13.0, 13.0, 13.0],
    "geometry": "Byzantine 5 domes (pentagram?); mosaic diffusion",
    "description": "San Marco’s Byzantine domes and mosaics create a radiant spiritual space in Venice.",
    "benefits": "Fosters serenity and artistic inspiration; suitable for meditators and art lovers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Basilica di San Francesco": {
    "rt60": 5.0,
    "dims": [80.0, 20.0, 20.0],
    "geometry": "Ratios 4:1; fresco harmony",
    "description": "San Francesco in Assisi is revered for its Giotto frescoes and Franciscan spirituality.",
    "benefits": "Promotes peace and spiritual reflection; great for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"San Vitale": {
    "rt60": 6.0,
    "dims": [16.0, 16.0, 15.0],
    "geometry": "Octagonal (sacred 8); central dome φ",
    "description": "San Vitale in Ravenna is famous for its octagonal design and stunning Byzantine mosaics.",
    "benefits": "Enhances spiritual harmony and creativity; ideal for meditators and art enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Chartres Cathedral": {
    "rt60": 6.5,
    "dims": [73.0, 16.0, 37.0],
    "geometry": "Vesica piscis windows; labyrinth φ spiral; proportions 1:φ:φ^2",
    "description": "Chartres Cathedral, with its labyrinth and stained glass, is a Gothic masterpiece of sacred geometry.",
    "benefits": "Fosters spiritual insight and contemplation; ideal for meditators and pilgrims.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Notre-Dame de Paris": {
    "rt60": 7.0,
    "dims": [48.0, 12.0, 35.0],
    "geometry": "Rose windows circles; ratios 5:4",
    "description": "Notre-Dame de Paris is iconic for its Gothic architecture and radiant rose windows.",
    "benefits": "Promotes reverence and emotional healing; great for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Mont-Saint-Michel Abbey": {
    "rt60": 6.0,
    "dims": [50.0, 20.0, 20.0],
    "geometry": "Spire φ curve; island mandala",
    "description": "Mont-Saint-Michel’s abbey, perched on a rocky island, is a medieval marvel of spiritual solitude.",
    "benefits": "Enhances contemplation and grounding; ideal for meditators and pilgrims.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Sainte-Chapelle": {
    "rt60": 5.0,
    "dims": [36.0, 11.0, 20.0],
    "geometry": "Stained glass ratios 3:2",
    "description": "Sainte-Chapelle’s stained glass creates a jewel-like space of divine light in Paris.",
    "benefits": "Fosters inspiration and spiritual upliftment; great for meditators and art lovers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Sagrada Família": {
    "rt60": 7.0,
    "dims": [90.0, 45.0, 60.0],
    "geometry": "Gaudi hyperbolic paraboloids; tree φ branching",
    "description": "Sagrada Família, Gaudí’s masterpiece, is renowned for its organic forms and spiritual vision.",
    "benefits": "Promotes creativity and divine connection; ideal for meditators and architecture enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Mezquita-Cathedral": {
    "rt60": 6.0,
    "dims": [180.0, 130.0, 15.0],
    "geometry": "Columns 856 (sacred 8); arches vesica",
    "description": "The Mezquita-Cathedral in Córdoba blends Islamic and Christian architecture with iconic arches.",
    "benefits": "Fosters harmony and cultural unity; suitable for meditators and historians.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Seville Cathedral": {
    "rt60": 8.0,
    "dims": [115.0, 76.0, 42.0],
    "geometry": "Largest Gothic; ratios 3:2",
    "description": "Seville Cathedral, the largest Gothic cathedral, is a monumental space of spiritual grandeur.",
    "benefits": "Promotes awe and spiritual reflection; great for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Jerónimos Monastery": {
    "rt60": 6.0,
    "dims": [90.0, 30.0, 25.0],
    "geometry": "Manueline knots; φ spirals",
    "description": "Jerónimos Monastery in Lisbon is a Manueline masterpiece with intricate nautical motifs.",
    "benefits": "Enhances spiritual exploration and creativity; ideal for meditators and art lovers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Stonehenge": {
    "rt60": 2.0,
    "dims": [33.0, 33.0, 5.0],
    "geometry": "Circles align solstices; Pythagorean triangles; 8x8 grid ratios",
    "description": "Stonehenge, a prehistoric monument, is special for its solstice alignments and ancient mystery.",
    "benefits": "Promotes grounding and cosmic connection; ideal for meditators and nature enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Newgrange Passage Tomb": {
    "rt60": 3.0,
    "dims": [19.0, 6.0, 4.0],
    "geometry": "Solstice alignment; sqrt(2) in kerb",
    "description": "Newgrange’s passage tomb in Ireland is revered for its winter solstice light alignment.",
    "benefits": "Fosters renewal and spiritual awakening; great for meditators and Celtic enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Iona Abbey": {
    "rt60": 5.0,
    "dims": [20.0, 10.0, 10.0],
    "geometry": "Celtic knots φ",
    "description": "Iona Abbey, a Celtic Christian site, is special for its serene island spirituality.",
    "benefits": "Promotes peace and spiritual reflection; ideal for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Rosslyn Chapel": {
    "rt60": 4.0,
    "dims": [21.0, 11.0, 12.0],
    "geometry": "Carvings cubes (Platonic); ratios 2:1",
    "description": "Rosslyn Chapel is famed for its intricate carvings and mysterious Templar connections.",
    "benefits": "Enhances contemplation and mystery; suitable for meditators and history buffs.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Westminster Abbey": {
    "rt60": 7.0,
    "dims": [156.0, 31.0, 31.0],
    "geometry": "Henry VII chapel fan vault φ",
    "description": "Westminster Abbey, with its Gothic vaults, is a historic site of royal and spiritual significance.",
    "benefits": "Fosters reverence and historical connection; great for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"St Paul’s Cathedral": {
    "rt60": 9.0,
    "dims": [111.0, 34.0, 34.0],
    "geometry": "Whisper gallery circle; 3:2 ratios",
    "description": "St Paul’s Cathedral, with its iconic dome, is renowned for its whispering gallery and grandeur.",
    "benefits": "Promotes awe and spiritual upliftment; ideal for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"York Minster": {
    "rt60": 7.5,
    "dims": [80.0, 15.0, 30.0],
    "geometry": "Windows vesica; scale φ",
    "description": "York Minster, a Gothic masterpiece, is celebrated for its stunning stained glass and vast nave.",
    "benefits": "Fosters inspiration and spiritual reflection; great for meditators and art lovers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Durham Cathedral": {
    "rt60": 6.5,
    "dims": [145.0, 12.0, 22.0],
    "geometry": "Norman arches; 3:4:5",
    "description": "Durham Cathedral’s Norman architecture is a powerful symbol of spiritual endurance.",
    "benefits": "Promotes grounding and reverence; ideal for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Cologne Cathedral": {
    "rt60": 8.5,
    "dims": [144.0, 86.0, 43.0],
    "geometry": "Spires 157m (φ progression)",
    "description": "Cologne Cathedral’s soaring Gothic spires make it a monumental spiritual landmark.",
    "benefits": "Fosters awe and spiritual elevation; great for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Frauenkirche Dresden": {
    "rt60": 7.0,
    "dims": [26.0, 26.0, 20.0],
    "geometry": "Baroque circle/square",
    "description": "Frauenkirche in Dresden, rebuilt after destruction, symbolizes peace and resilience.",
    "benefits": "Promotes healing and hope; suitable for meditators and history enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"St. Stephen’s Cathedral": {
    "rt60": 6.0,
    "dims": [107.0, 34.0, 28.0],
    "geometry": "Roof tiles mosaic; ratios 3:1",
    "description": "St. Stephen’s Cathedral in Vienna is famed for its colorful roof and Gothic elegance.",
    "benefits": "Fosters spiritual harmony and inspiration; great for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Matthias Church": {
    "rt60": 5.0,
    "dims": [60.0, 23.0, 20.0],
    "geometry": "Neo-Gothic φ tiles",
    "description": "Matthias Church in Budapest is known for its vibrant tiles and neo-Gothic beauty.",
    "benefits": "Enhances creativity and spiritual connection; ideal for meditators and art lovers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Hagia Sophia": {
    "rt60": 10.5,
    "dims": [55.0, 31.0, 31.0],
    "geometry": "Pendentive geometry; floor plan cross/circle; light cosmology",
    "description": "Hagia Sophia in Istanbul, with its vast dome, is a Byzantine marvel of divine light.",
    "benefits": "Promotes awe and spiritual transcendence; ideal for meditators and historians.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Blue Mosque": {
    "rt60": 9.0,
    "dims": [43.0, 23.0, 23.0],
    "geometry": "Similar to Hagia; 6 minarets (hexagon)",
    "description": "The Blue Mosque, with its six minarets, is an Ottoman masterpiece of spiritual serenity.",
    "benefits": "Fosters peace and devotion; great for Muslims and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Chora Church": {
    "rt60": 6.0,
    "dims": [15.0, 10.0, 10.0],
    "geometry": "Byzantine mosaics; vesica",
    "description": "Chora Church in Istanbul is renowned for its exquisite Byzantine mosaics and sacred art.",
    "benefits": "Enhances contemplation and artistic inspiration; ideal for meditators and art lovers.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Church of the Holy Sepulchre": {
    "rt60": 5.0,
    "dims": [30.0, 30.0, 20.0],
    "geometry": "Circle (resurrection); multi-room φ",
    "description": "The Church of the Holy Sepulchre in Jerusalem is sacred as the site of Jesus’ crucifixion and resurrection.",
    "benefits": "Promotes reverence and spiritual healing; great for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Al-Aqsa Dome of the Rock": {
    "rt60": 4.0,
    "dims": [20.0, 20.0, 15.0],
    "geometry": "Octagon (8); golden dome ratios",
    "description": "The Dome of the Rock in Jerusalem is revered for its golden dome and sacred rock.",
    "benefits": "Fosters spiritual unity and peace; ideal for Muslims and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Ummayad Mosque": {
    "rt60": 6.0,
    "dims": [157.0, 97.0, 15.0],
    "geometry": "Ratios 1.618 (φ); courtyard reverb",
    "description": "The Ummayad Mosque in Damascus is a historic Islamic site with a vast courtyard and ornate mosaics.",
    "benefits": "Promotes devotion and tranquility; great for Muslims and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Chichén Itzá El Castillo": {
    "rt60": 1.5,
    "dims": [55.3, 55.3, 30.0],
    "geometry": "365 steps (calendar); chirp echo from stairs; equinox serpent shadow",
    "description": "El Castillo at Chichén Itzá is famous for its equinox serpent shadow and acoustic chirp effect.",
    "benefits": "Enhances cosmic connection and energy; ideal for meditators and Mayan culture enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Teotihuacan Feathered Serpent": {
    "rt60": 3.0,
    "dims": [65.0, 65.0, 20.0],
    "geometry": "Pyramid ratios 4:3; serpent alignments",
    "description": "Teotihuacan’s Feathered Serpent Pyramid is a Mesoamerican marvel with cosmic alignments.",
    "benefits": "Promotes spiritual grounding and ancient wisdom; great for meditators and historians.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Tulum Temple": {
    "rt60": 2.0,
    "dims": [20.0, 10.0, 5.0],
    "geometry": "Coastal alignments; wave harmonics",
    "description": "Tulum’s coastal temple is special for its oceanfront setting and Mayan spiritual heritage.",
    "benefits": "Fosters tranquility and connection to nature; ideal for meditators and coastal enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Machu Picchu Sun Temple": {
    "rt60": 3.0,
    "dims": [10.0, 10.0, 5.0],
    "geometry": "Intihuatana solar; stone φ fittings",
    "description": "Machu Picchu’s Sun Temple is revered for its solar alignments and Inca stonework.",
    "benefits": "Promotes spiritual alignment and energy; great for meditators and Inca enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Sacsayhuamán": {
    "rt60": 2.0,
    "dims": [50.0, 20.0, 5.0],
    "geometry": "Polygonal interlock; sqrt(3) angles",
    "description": "Sacsayhuamán’s massive stone walls in Cusco are a testament to Inca engineering and spirituality.",
    "benefits": "Fosters grounding and ancient wisdom; ideal for meditators and historians.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Basilica of Guadalupe": {
    "rt60": 6.0,
    "dims": [100.0, 50.0, 20.0],
    "geometry": "Modern oval; Tepeyac hill; modern φ curves",
    "description": "The Basilica of Guadalupe in Mexico City is a sacred site for the Virgin of Guadalupe’s apparition.",
    "benefits": "Promotes devotion and emotional healing; great for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Mission San Carlos Borromeo": {
    "rt60": 4.0,
    "dims": [30.0, 10.0, 10.0],
    "geometry": "Adobe arches; 3:2 ratios",
    "description": "Mission San Carlos Borromeo in Carmel is a historic Spanish mission with serene architecture.",
    "benefits": "Fosters peace and historical connection; ideal for meditators and history enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Kiva Spaces Mesa Verde": {
    "rt60": 3.0,
    "dims": [7.0, 7.0, 5.0],
    "geometry": "Circular (unity); underground mandala",
    "description": "Mesa Verde’s kiva spaces are sacred Ancestral Puebloan underground chambers for rituals.",
    "benefits": "Promotes grounding and community connection; great for meditators and indigenous culture enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Lalibela Rock-Hewn Churches": {
    "rt60": 4.0,
    "dims": [12.0, 10.0, 11.0],
    "geometry": "Cross plans; ratios 1:1 (equality)",
    "description": "Lalibela’s rock-hewn churches in Ethiopia are monolithic marvels of Christian devotion.",
    "benefits": "Fosters spiritual depth and reverence; ideal for Christians and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Great Mosque of Djenné": {
    "rt60": 5.0,
    "dims": [75.0, 75.0, 10.0],
    "geometry": "Mud-brick spirals; annual renewal (cycle)",
    "description": "The Great Mosque of Djenné, a mud-brick masterpiece, is a symbol of Malian spirituality.",
    "benefits": "Promotes community and spiritual grounding; great for Muslims and meditators.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
},
"Great Zimbabwe Enclosures": {
    "rt60": 3.0,
    "dims": [50.0, 20.0, 5.0],
    "geometry": "Elliptical (vesica-like); stone ratios",
    "description": "Great Zimbabwe’s stone enclosures are a testament to ancient African architectural prowess.",
    "benefits": "Fosters grounding and historical connection; ideal for meditators and African heritage enthusiasts.",
    "disclaimer": "This is a simulated representation; consult historical sources for accuracy."
}
}

# Countries mapping for sites
COUNTRIES = {
    "Egypt": [
        "Great Pyramid King's Chamber", "Great Pyramid Queen's Chamber", "Great Pyramid Grand Gallery",
        "Pyramid of Khafre", "Abu Simbel Temple", "Karnak Temple Hypostyle Hall",
        "Luxor Temple", "Dendera Temple of Hathor", "Philae Temple"
    ],
    "India": [
        "Kailasa Temple Ellora", "Konark Sun Temple", "Brihadeeswarar Temple", "Meenakshi Temple",
        "Golden Temple", "Jagannath Temple", "Kandariya Mahadev", "Kashi Vishwanath",
        "Ramanathaswamy Temple", "Virupaksha Temple", "Ajanta Caves", "Elephanta Caves",
        "Mahabodhi Temple"
    ],
    "Nepal": [
        "Boudhanath Stupa Gallery", "Swayambhunath Caves"
    ],
    "Tibet": [
        "Jokhang Temple", "Potala Palace Chapel", "Tashi Lhunpo Monastery", "Mount Kailash Caves"
    ],
    "Cambodia": [
        "Angkor Wat Outer Galleries", "Angkor Wat Inner Sanctum", "Bayon Temple",
        "Ta Prohm", "Preah Khan"
    ],
    "Indonesia": [
        "Borobudur Central Stupa", "Borobudur Upper Terraces", "Prambanan Temple", "Tanah Lot Shrine"
    ],
    "China": [
        "Temple of Heaven", "Mogao Caves", "Longmen Grottoes"
    ],
    "Japan": [
        "Todai-ji Daibutsuden", "Horyu-ji", "Kiyomizu-dera", "Fushimi Inari"
    ],
    "Greece": [
        "Parthenon", "Temple of Apollo Delphi", "Theatre of Epidaurus"
    ],
    "Italy": [
        "Pantheon", "St. Peter’s Basilica", "Florence Cathedral", "Basilica di San Marco",
        "Basilica di San Francesco", "San Vitale"
    ],
    "France": [
        "Chartres Cathedral", "Notre-Dame de Paris", "Mont-Saint-Michel Abbey", "Sainte-Chapelle"
    ],
    "Spain": [
        "Sagrada Família", "Mezquita-Cathedral", "Seville Cathedral"
    ],
    "Portugal": [
        "Jerónimos Monastery"
    ],
    "United Kingdom": [
        "Stonehenge", "Westminster Abbey", "St Paul’s Cathedral", "York Minster", "Rosslyn Chapel"
    ],
    "Ireland": [
        "Newgrange Passage Tomb", "Iona Abbey"
    ],
    "Germany": [
        "Cologne Cathedral", "Frauenkirche Dresden"
    ],
    "Austria": [
        "St. Stephen’s Cathedral"
    ],
    "Hungary": [
        "Matthias Church"
    ],
    "Turkey": [
        "Hagia Sophia", "Blue Mosque", "Chora Church"
    ],
    "Israel/Palestine": [
        "Church of the Holy Sepulchre", "Al-Aqsa Dome of the Rock"
    ],
    "Syria": [
        "Ummayad Mosque"
    ],
    "Mexico": [
        "Chichén Itzá El Castillo", "Teotihuacan Feathered Serpent", "Tulum Temple",
        "Basilica of Guadalupe"
    ],
    "Peru": [
        "Machu Picchu Sun Temple", "Sacsayhuamán"
    ],
    "United States": [
        "Kiva Spaces Mesa Verde"
    ],
    "Ethiopia": [
        "Lalibela Rock-Hewn Churches"
    ],
    "Mali": [
        "Great Mosque of Djenné"
    ],
    "Zimbabwe": [
        "Great Zimbabwe Enclosures"
    ]
}

def calculate_fundamental_frequency(dims, phi=1.618):
    c = 343  # Speed of sound in m/s
    Lx, Ly, Lz = dims
    f = (c / 2) * (1 / max(Lx, Ly, Lz))
    f_adjusted = f * phi
    f_adjusted = max(20, min(100, f_adjusted))
    return f_adjusted

def calculate_binaural_delta(base_freq, phi=1.618):
    delta = base_freq / phi
    delta = max(2, min(8, delta))  # Constrain to 2-8 Hz for meditative effect
    return delta

def calculate_isochronic_rate(dims):
    c = 343  # Speed of sound in m/s
    sorted_dims = sorted(dims, reverse=True)
    second_dim = sorted_dims[1]
    f = (c / 2) * (1 / second_dim)
    f = max(2, min(10, f))  # Constrain to 2-10 Hz for isochronic pulsing
    return f

def generate_synthetic_ir(fs=44100, rt60=2.5, length_sec=1, dims=[10.47, 5.235, 5.827], phi=1.618):
    t = np.linspace(0, length_sec, int(fs * length_sec))
    beta = np.log(1000) / rt60
    noise = np.random.normal(0, 1, len(t))
    tail = noise * np.exp(-beta * t)
    max_dim = max(dims)
    reflection_delay = max_dim / 343
    er_times = np.linspace(0.005, min(0.15, reflection_delay), 6)
    er = np.zeros(len(t))
    for et in er_times:
        idx = int(et * fs)
        if idx < len(t):
            er[idx] = np.random.uniform(0.3, 0.9)
    ir = signal.convolve(er, tail[:len(er)])[:len(t)]
    c = 343
    modes = []
    for l in range(3):
        for m in range(3):
            for n in range(3):
                if l == m == n == 0: continue
                f = (c / 2) * np.sqrt((l / dims[0])**2 + (m / dims[1])**2 + (n / dims[2])**2)
                modes.append(f)
    freqs = np.fft.rfftfreq(len(t), 1/fs)
    spec = np.fft.rfft(ir)
    for mode in sorted(modes)[:6]:
        idx = np.argmin(np.abs(freqs - mode))
        spec[idx] *= phi
        for mult in [phi, phi**2]:
            harm = mode * mult
            if harm < fs/2:
                idx = np.argmin(np.abs(freqs - harm))
                spec[idx] *= 1.3
    ir = np.fft.irfft(spec, len(t))
    ir /= np.max(np.abs(ir)) * 0.7
    return ir

def generate_binaural_isochronic_tone(fs=44100, rt60=2.5, dims=[10.47, 5.235, 5.827], phi=1.618, length_sec=1, pulse=True):
    t = np.linspace(0, length_sec, int(fs * length_sec))
    base_freq = calculate_fundamental_frequency(dims, phi)
    delta_freq = calculate_binaural_delta(base_freq, phi)
    pulse_rate = calculate_isochronic_rate(dims)
    left_tone = 0.15 * np.sin(2 * np.pi * base_freq * t)
    right_tone = 0.15 * np.sin(2 * np.pi * (base_freq + delta_freq) * t)
    if pulse:
        envelope = 0.5 * (1 + np.sin(2 * np.pi * pulse_rate * t))
        left_tone *= envelope
        right_tone *= envelope
    max_dim = max(dims)
    lowpass_freq = 400 + (max_dim / max([max(data['dims']) for data in SACRED_SITES.values()])) * 200
    noise = np.random.normal(0, 1, len(t))
    b, a = signal.butter(4, lowpass_freq / (fs / 2), btype='low')
    air = 0.02 * signal.filtfilt(b, a, noise)
    signal_combined_left = left_tone + air
    signal_combined_right = right_tone + air
    signal_combined_left /= np.max(np.abs(signal_combined_left))
    signal_combined_right /= np.max(np.abs(signal_combined_right))
    ir = generate_synthetic_ir(fs, rt60, length_sec, dims, phi)
    output_left = signal.convolve(signal_combined_left, ir, mode='full')[:len(t)]
    output_right = signal.convolve(signal_combined_right, ir, mode='full')[:len(t)]
    output_left /= np.max(np.abs(output_left))
    output_right /= np.max(np.abs(output_right))
    output_stereo = np.stack((output_left, output_right), axis=1)
    return output_stereo.tolist()

@app.route('/')
def home():
    return jsonify({"message": "Welcome to Sanctra API! Use /generate-ir, /sites, /sites-by-country, or /generate-tone."})

@app.route('/sites', methods=['GET'])
def get_sites():
    return jsonify({"sites": list(SACRED_SITES.keys())})

@app.route('/sites-by-country', methods=['GET'])
def get_sites_by_country():
    return jsonify(COUNTRIES)

@app.route('/generate-ir', methods=['POST'])
def generate_ir():
    data = request.get_json()
    site = data.get('site', 'Great Pyramid King\'s Chamber')
    if site not in SACRED_SITES:
        return jsonify({"error": "Site not found, use /sites to see available sites"}), 400
    rt60 = SACRED_SITES[site]['rt60']
    dims = SACRED_SITES[site]['dims']
    geometry = SACRED_SITES[site]['geometry']
    ir_data = generate_synthetic_ir(fs=44100, rt60=rt60, dims=dims)
    return jsonify({
        "site": site,
        "rt60": rt60,
        "dimensions": dims,
        "geometry": geometry,
        "ir_data": ir_data[:44100]  # ~1s
    })

@app.route('/generate-tone', methods=['POST'])
def generate_tone_endpoint():
    data = request.get_json()
    site = data.get('site', 'Great Pyramid King\'s Chamber')
    pulse = data.get('pulse', True)
    if site not in SACRED_SITES:
        return jsonify({"error": "Site not found, use /sites to see available sites"}), 400
    rt60 = SACRED_SITES[site]['rt60']
    dims = SACRED_SITES[site]['dims']
    geometry = SACRED_SITES[site]['geometry']
    fs = 44100
    tone_data = generate_binaural_isochronic_tone(fs=fs, rt60=rt60, dims=dims, pulse=pulse)
    return jsonify({
        "site": site,
        "rt60": rt60,
        "dimensions": dims,
        "geometry": geometry,
        "tone_data": tone_data[:44100]  # ~1s, stereo (left, right)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render uses port 10000
    app.run(host='0.0.0.0', port=port, debug=False)
