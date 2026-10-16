# Bug Log

| # | Date | What happened | Cause | Fix | Test |
| --- | --- | --- | --- | --- | --- |
| 1 | | A locked database raised a raw pandas error instead of a friendly message | pandas wraps SQLite errors in its own exception | `db.connection()` now catches `pandas.errors.DatabaseError` too | test_T13_database_locked |
| 2 | | Consent could be stored as 0 | Schema `CHECK (IN (0,1))` allows 0 | `db.add_person()` refuses `consent=False` | test_T02_consent_required_at_db_layer |
