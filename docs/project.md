id | name | data type | cardinality | description
-- | -- | -- | -- | --
id | id | string | 1..1 | 
handleUrl | Handle identifier | uri | 1..1 | Persistent identifier for the record.
name | Project name | string | 1..1 | 
additionalName | Additional names | string | 0..n | 
code | Project identifiers | object | 0..n | Project identifier as specified by the respective schemes.
code.projectId | Identifier | string | 1..1 | 
code.projectScheme | Scheme | enum | 1..1 | 
code.projectUrl | URL | uri | 0..1 | 
