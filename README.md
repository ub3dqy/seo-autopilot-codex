# SEO Autopilot for OpenAI Codex

Автоматизированный SEO-инструмент для Codex: один запрос запускает аудит, безопасные исправления, валидацию и формирование итогового отчёта.

## Две редакции

| Редакция | Назначение |
|---|---|
| **User Edition** | Простая установка и ежедневное использование без ручного выбора режимов и промптов |
| **Engineering Edition** | Полные исходники, contracts, validators, tests, evals и средства воспроизводимой сборки |

После публикации релиза обе редакции доступны на странице [Releases](../../releases/tag/v1.4.0).

## Быстрый запуск User Edition

### Windows

1. Скачайте `seo-autopilot-codex-user-v1.4.0.zip`.
2. Распакуйте архив.
3. Запустите `1_INSTALL_WINDOWS.cmd`.
4. Запустите `2_RUN_SEO_WINDOWS.cmd` и выберите каталог сайта.

После установки можно открыть проект в Codex и написать:

```text
Проведи SEO-оптимизацию этого сайта.
```

Для аудита без изменений:

```text
$seo-autopilot Проведи только SEO-аудит. Ничего не изменяй.
```

## Содержимое репозитория

```text
user/          # распакованная пользовательская редакция v1.4.0
engineering/   # распакованная инженерная редакция v1.4.0
.github/       # автоматическая проверка и публикация релиза
SHA256SUMS     # контрольные суммы релизных ZIP
```

## Контрольные суммы v1.4.0

```text
e03e522fb7767ad7597452fac78cb982aac4c83337573054a32b3f19516d399e  seo-autopilot-codex-user-v1.4.0.zip
27791aa36257d878c87bc591a03f25ff21ec79fec5251ef34c4a2fe67126db45  seo-autopilot-codex-engineering-v1.4.0.zip
```

## Проверенный статус

- deterministic unit, fixture и lifecycle tests: **29/29 PASS**;
- static behavioral contracts: **24/24 PASS**;
- package и manifest verification: **PASS**;
- live Codex behavioral suite: **NOT_RUN** и не обозначается как PASS.

## Безопасные границы

SEO Autopilot не меняет URL, не удаляет страницы, не публикует неподтверждённые сведения, не включает tracking и не выполняет production deployment без явного решения пользователя. Недоступные внешние сервисы отмечаются как `DEFERRED`, не блокируя безопасную работу с репозиторием.
