# gmail/ — Gmail Integration Package

Standalone Gmail API functions and a 3-stage processing pipeline, following the same architecture as the `tg/` (Telegram) package.

## Structure

```
gmail/
├── api/            # Standalone Gmail API wrappers
├── triggers/       # Poll inbox → trigger_queue.json
├── handlers/       # trigger_queue.json → reply_queue.json
├── actions/        # reply_queue.json → send via Gmail
├── utils/          # Auth, parsing, queue management
└── log/            # Runtime log files
```

## Pipeline

```
Gmail Inbox (unread)
    ↓  gmail/triggers/poll_inbox.py
trigger_queue.json
    ↓  gmail/handlers/build_replies.py
reply_queue.json
    ↓  gmail/actions/send_replies.py
Gmail (sent replies)
```

## Setup

1. Create OAuth2 credentials at [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Enable the **Gmail API** in your project
3. Download the client secrets JSON and save as `credentials/gmail-credentials.json`
4. Add Gmail config to `_config files/config.json`:

```json
{
  "gmail": {
    "credentials_file": "credentials/gmail-credentials.json",
    "token_file": "credentials/gmail-token.json"
  }
}
```

5. On first run, a browser window opens to authorize — the token is saved automatically.

## Dependencies

```
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
```
