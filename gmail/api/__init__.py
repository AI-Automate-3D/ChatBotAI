"""Gmail API functions — standalone wrappers for the Gmail REST API.

Each module provides one or more functions that take an authenticated
Gmail service object and perform a single operation.

    from gmail.api.get_email import get_email
    from gmail.api.list_emails import list_emails, search_emails
    from gmail.api.send_email import send_email
    from gmail.api.reply_email import reply_email
    from gmail.api.modify_labels import mark_read, archive, trash, star
    from gmail.api.get_attachments import get_attachment, download_all_attachments
"""
