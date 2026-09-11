id | name | data type | cardinality | description
-- | -- | -- | -- | --
id | id | string | 1..1 | 
handleUrl | Handle identifier | uri | 1..1 | Persistent identifier for the record.
name | Institution name | string | 1..1 | 
additionalName | Additional names | string | 0..n | 
rorUrl | ROR identifier (URL) | uri | 0..1 | 
country | Country | enum | 1..1 | 
url | Institution URL | uri | 0..n | 
parentOrganization | Parent Organizations | handle reference | 0..n | 
