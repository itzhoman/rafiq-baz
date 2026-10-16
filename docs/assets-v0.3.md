# v0.3 assets and motion

- Vazirmatn variable font, pinned v33.003, self-hosted as public/assets/vazirmatn-variable.woff2 (111,152 bytes). Source: https://github.com/rastikerdar/vazirmatn/tree/v33.003/fonts/webfonts. SIL Open Font License is included as VAZIRMATN-LICENSE.txt. This replaces the previous split font files.
- One hundred fictional adult profiles are generated reproducibly by scripts/generate-demo-profiles.py. All biographical fields, first-date prompts, interests, relationship goals and eight personal attributes are populated. Their badges are not marked verified.
- Their 100 local SVG avatar illustrations are original code-native vector assets, with varied skin/hair/clothing/background colours. Combined SVG size: 165,401 bytes. They contain a fictional-profile caption and use no real photographs or external avatar service.
- The ten earlier fictional sample portraits remain. public/data/profiles.json holds all 110 profiles (166,757 bytes), loaded separately from initial JavaScript. PWA caches profiles and avatars lazily; native apps bundle these files.
- Motion is CSS-based, with no background animation loop in JavaScript. Page entries, cards, hover images, controls, tabs, navigation, messages, dialogs, mutual-match art and notifications have coordinated timings. The loading skeleton animates only while loading. prefers-reduced-motion disables transitions, animation and smooth scrolling.

Screenshots from browser review: finding-desktop-v3.jpg, finding-mobile-v3.jpg and account-mobile-v3.jpg in docs/screenshots.
