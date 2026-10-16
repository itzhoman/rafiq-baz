# Find someone / پیدا کردن · v0.2

The product is for dating and forming a relationship. The brand name does not change that purpose.

The Find someone screen shows one profile at a time. A like or pass advances the queue. A like that is mutual opens the existing demo match dialog. Passing affects only that specific profile and can be undone from the immediate toast.

“Don’t suggest people like this” stores a separate feedback reference. The selected profile is excluded. Profiles with a weighted Dice similarity of at least 0.60 are also excluded. Other profiles receive a smaller ranking penalty based on their similarity to the feedback.

Similarity uses declared interests with weight 1 and exact normalized attribute key/value pairs with weight 2. It does not analyze photographs, age, city, names, gender, or inferred personal traits. No model, remote AI service or invented compatibility percentage is involved.

Remaining profiles are ranked by matching relationship intention, shared interests and matching personal attributes. Age, distance, online status and selected-interest filters are always applied as hard constraints first. Likes and passes are not recycled silently.

The feedback list exposes each saved pattern and lets the user restore it. Restoring a pattern does not undo likes or ordinary passes.

## Personal attributes

Each demo account can store a relationship intention and up to 12 attributes. An attribute has a name (1–32 characters) and a value (1–80 characters), for example “سبک زندگی: آرام”. Blank values and duplicate normalized names are rejected by the API and editor.

Arabic/Persian letter variants, surrounding whitespace and common spacing differences are normalized for matching. Values remain the user’s literal text in the interface and are rendered as text, never HTML.

The Python API retains attributes and feedback per demo session. Existing sessions gain missing fields, while their likes, passes, messages and customized biography remain intact. An old client’s profile update does not erase attributes it did not send.

Static hosting and native preview builds use the same recommendation rules with browser/device-local sample state. The Python-backed local preview persists state to SQLite. These are sample sessions, not production user accounts.
