# remnanode-ros

Неофициальная RouterOS-совместимая сборка [Remnawave Node](https://github.com/remnawave/node).

Образ собирается из последнего upstream-релиза Node. Ежедневный workflow
проверяет его новую версию и публикует новые образы `amd64` и `arm64` только
при выходе релиза. Xray-core и s6-overlay берутся из Dockerfile самого upstream Node.

При сборке workflow клонирует этот upstream-тег, собирает `nftables-napi` для
`amd64` и `arm64`, заменяет только эту зависимость и добавляет одну строку
`COPY vendor/ ./vendor/`. Сам финальный образ всегда собирается оригинальным
Dockerfile соответствующего Node-релиза, а не его копией из этого репозитория.

## Совместимость с RouterOS

В Node используется fork `nftables-napi` с нативной netlink-совместимостью для
ядра RouterOS. При доступном `CAP_NET_ADMIN` это позволяет использовать
плагины, которым требуются nftables:

- Ingress Filter;
- Egress Filter;
- Torrent Blocker;
- Connection Drop.

В финальный образ не добавляется `nft` CLI и не нужны дополнительные ENV для
совместимости.

### Что изменено в nftables-napi

- Создание таблиц разделено на небольшие netlink-batch'и: таблицы и sets
  фиксируются ядром до создания chains и rules. Это устраняет `No such file or
  directory` на RouterOS при ссылках на только что созданные sets.
- Rules после создания set используют его имя, а не временный ID из той же
  netlink-транзакции.
- Если ядро не поддерживает per-element counters, создание таблицы повторяется
  без них. Блокировки, timeout'ы и именованные counters сохраняются.
- Для concat set протокол+порт (`tcp . 443`) при `EINVAL` выполняется повторная
  попытка без современного флага `NFT_SET_CONCAT`; descriptor concat остаётся.
- Отправка batch ожидает первый netlink ACK, поэтому ошибка ядра не может быть
  ошибочно принята за успешную операцию.

## Теги образа

- `latest` — последняя автоматическая сборка;
- `node-<node>-xray-<xray>` — точная комбинация upstream Node и Xray-core.

Образы для `amd64` и `arm64` публикуются в `ghcr.io/medium1992/remnanode-ros` и
`medium1992/remnanode-ros`. Версия Node последней сборки хранится в
[VERSIONS](./VERSIONS).

## Требования RouterOS

Нужны RouterOS с пакетом `container`, включённый `device-mode container=yes` и
доступный контейнеру `CAP_NET_ADMIN`. NFT-плагины поддерживаются на RouterOS
`amd64` и `arm64`; для остальных архитектур образ не публикуется. Используется
обычная конфигурация Remnawave Node — отдельный формат ENV или конфигов не
вводится.

## Лицензия

Проект распространяется под [AGPL-3.0-only](./LICENSE). Исходный код Node —
upstream-релиз из [VERSIONS](./VERSIONS); изменения сборки и RouterOS-совместимый
fork `nftables-napi` доступны в соответствующих публичных репозиториях.
