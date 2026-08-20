# SEO Autopilot for OpenAI Codex v1.4.0

Репозиторий содержит две отдельные редакции:

- **User Edition** — простая установка, автоматический выбор SEO-режима и один сквозной цикл аудит → безопасные исправления → проверки → итог;
- **Engineering Edition** — полный skill, contracts, gates, validators, tests, evals и средства воспроизводимой сборки.

Обе редакции находятся в проверяемом source bundle. Команда `python prepare_editions.py --build-zips` материализует каталоги `user/` и `engineering/` и собирает точные релизные архивы.

## Проверка

- deterministic unit, fixture и lifecycle tests: 29/29 PASS;
- static behavioral contracts: 24/24 PASS;
- package и manifest verification: PASS;
- live autonomous Codex behavior: NOT_RUN и не обозначается как PASS.

## SHA-256

```text
e03e522fb7767ad7597452fac78cb982aac4c83337573054a32b3f19516d399e  seo-autopilot-codex-user-v1.4.0.zip
27791aa36257d878c87bc591a03f25ff21ec79fec5251ef34c4a2fe67126db45  seo-autopilot-codex-engineering-v1.4.0.zip
5f96d6ddc4bc4211599d6399fe287e08f44012d20011b5dd9898e913e8b82a28  source-bundle-v1.4.0.tar.xz
```
