# Raw changelog (engineering notes) - v2.4.0

- feat: recurring tasks support custom weekdays (e.g. Mon/Wed/Fri) (#812)
- feat: GitHub integration auto-moves task to Done on PR merge (#790)
- feat(api): add `task.completed` webhook event
- perf: board loads ~40% faster for projects with >2k tasks (virtualized columns)
- fix: due-date reminders sent twice for users in UTC+5:30 timezone (#834)
- fix: blocked tasks could be dragged to Done on mobile (#829)
- fix: CSV export dropped labels containing commas
- chore: upgrade React to 19, bump CI node version
- refactor: split notification service into worker + scheduler
- test: add e2e tests for SSO login
- BREAKING(api): `GET /v1/tasks` now paginates by default (50 per page, use `cursor`)
- deprecate: `priority=critical` alias removed, use `urgent`
