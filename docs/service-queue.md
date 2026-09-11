id | name | data type | cardinality | description
-- | -- | -- | -- | --
id | id | string | 1..1 | 
handleUrl | Handle identifier | uri | 1..1 | Persistent identifier for the record.
name | Name of the service queue | string | 1..1 | 
alias | Queue alias | string | 1..1 | 
description | Description of the service queue | string | 1..1 | Describe the purpose of the queue; who is it intended for, etc.
cesnetProvidesQueue | Queue provided by CESNET | boolean | 1..1 | Select whether CESNET should provide the service queue or if this is handled differently.
