USE master
CREATE CREDENTIAL [https://<blob_account_name>.blob.core.windows.net/ratings/*/*.csv]
    WITH IDENTITY='SHARED ACCESS SIGNATURE'
    , SECRET = '<SAS token>'
GO
