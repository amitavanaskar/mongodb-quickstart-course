from data.owners import Owner
import services.data_service as svc

active_account: Owner = None
# By annotating that as Owner, all intellisense works.
# Python Tip : Always annotate for intellisense


def reload_account():
    global active_account
    if not active_account:
        return

    # Done: pull owner account from the database.
    active_account = svc.find_account_by_email(active_account.email)    # Reload account
