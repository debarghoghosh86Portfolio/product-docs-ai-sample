# Integrations

## Slack

Connect Slack from **Settings > Integrations > Slack** and approve the permissions. After connecting:

- Use `/taskflow new <title>` in any channel to create a task.
- Choose a channel per project to receive notifications when tasks are created, completed, or overdue.

Only admins and owners can connect or disconnect Slack.

## GitHub

The GitHub integration links pull requests to tasks. Mention the task ID (for example `TF-123`) in a branch name, commit message, or pull request title. When the pull request is merged, the task moves to *Done* automatically.

## Webhooks

Webhooks send an HTTP POST with a JSON payload to your URL when events happen (`task.created`, `task.updated`, `task.completed`, `project.archived`). Configure them under **Settings > Integrations > Webhooks**. Each request includes an `X-TaskFlow-Signature` header (HMAC-SHA256 of the body using your webhook secret) so you can verify it came from TaskFlow. Failed deliveries are retried 5 times with exponential backoff.

## REST API

The REST API base URL is `https://api.taskflow.example/v1`. Create a personal API token from **Profile > API tokens** and send it as `Authorization: Bearer <token>`.

Rate limit: 100 requests per minute per token. When you exceed it, the API returns HTTP `429 Too Many Requests` with a `Retry-After` header.
