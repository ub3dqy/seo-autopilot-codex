# SEO Autopilot for OpenAI Codex

Отдельный публичный репозиторий SEO-инструмента для OpenAI Codex. Здесь находятся **две редакции одного продукта**:

- **User Edition** — простая установка и запуск без ручного выбора режимов и промптов;
- **Engineering Edition** — полный исходный пакет с contracts, gates, validators, tests, evals и средствами воспроизводимой сборки.

Никакого отношения к Claude Code этот репозиторий не имеет.

## Получить обе редакции

### Windows

Дважды щёлкните:

```text
BUILD_EDITIONS_WINDOWS.cmd
```

### macOS / Linux

```bash
./build_editions.sh
```

Скрипт проверит встроенный source bundle, развернёт каталоги `user/` и `engineering/`, затем соберёт точные релизные ZIP в `dist/`.

Ручной эквивалент:

```bash
python prepare_editions.py --build-zips
```

## Запуск User Edition

После сборки:

1. откройте `user/` или распакуйте `dist/seo-autopilot-codex-user-v1.4.0.zip`;
2. в Windows запустите `1_INSTALL_WINDOWS.cmd`, затем `2_RUN_SEO_WINDOWS.cmd`;
3. либо откройте проект в Codex и напишите:

```text
Проведи SEO-оптимизацию этого сайта.
```

## Engineering Edition

Каталог `engineering/` и архив `dist/seo-autopilot-codex-engineering-v1.4.0.zip` содержат канонический skill, установщики, validators, tests, eval harness и release tooling.

## Контрольные суммы v1.4.0

```text
e03e522fb7767ad7597452fac78cb982aac4c83337573054a32b3f19516d399e  seo-autopilot-codex-user-v1.4.0.zip
27791aa36257d878c87bc591a03f25ff21ec79fec5251ef34c4a2fe67126db45  seo-autopilot-codex-engineering-v1.4.0.zip
5f96d6ddc4bc4211599d6399fe287e08f44012d20011b5dd9898e913e8b82a28  source-bundle-v1.4.0.tar.xz
```

## Проверенный статус

- deterministic unit, fixture и lifecycle tests: **29/29 PASS**;
- static behavioral contracts: **24/24 PASS**;
- package, manifest и reproducibility checks: **PASS**;
- live autonomous Codex suite: **NOT_RUN** и не обозначается как PASS.
