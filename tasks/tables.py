import sqlalchemy


metadata_obj = sqlalchemy.MetaData()

opencodelists_logins = sqlalchemy.Table(
    "opencodelists_logins",
    metadata_obj,
    sqlalchemy.Column("login_at", sqlalchemy.DateTime, primary_key=True),
    sqlalchemy.Column("email_hash", sqlalchemy.String(64), primary_key=True),
)
