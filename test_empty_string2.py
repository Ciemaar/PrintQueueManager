# What if you move the item up, but the item above it was deleted?
# No, "deleted" items don't show up in the main view (status != DELETED).
# Is there any chance `above_job` is fetching the wrong thing?
# "above_job = db.query(PrintJob).filter(PrintJob.id == above_id).first() if above_id else None"
# Let's think about `normalize_priorities_sync`.
# Wait. Look closely at `reorder_job`:

"""
    # Detect priority collisions or inversions that prevent calculating a midpoint
    if above_job and below_job:
        above_priority = getattr(above_job, "user_priority")
        below_priority = getattr(below_job, "user_priority")

        # If priorities are identical or inverted, normalize the entire list first
        if above_priority >= below_priority:
            _normalize_priorities_sync(db)
            db.refresh(above_job)
            db.refresh(below_job)
"""

# Wait... what if `above_job` is NONE, and `below_job` is NOT None.
# And `below_priority` is `0.0`.
# The assignment becomes `below_priority - 1.0` => `-1.0`.
# Job gets `-1.0`.
# What happens to the NEXT item pulled to the top?
# It gets `below_priority - 1.0` = `-1.0 - 1.0` => `-2.0`.
# The order is:
# -2.0
# -1.0
# 0.0

# So this works.
# Is it possible that `user_priority` is an Integer in the database?
# The migration `3dc1a2df7d43_add_user_priority_column_to_print_jobs.py` added it.
