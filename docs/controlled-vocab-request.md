id | name | data type | cardinality | description
-- | -- | -- | -- | --
id | id | string | 1..1 | 
handleUrl | Handle identifier | uri | 1..1 | Persistent identifier for the record.
name | Name | string | 1..1 | 
description | Description | string | 1..1 | Maps to the property dc:description
creator | Organisation Creator | string | 0..1 | Maps to the property dc:creator
urlSourceReference | External source URL | uri | 0..1 | Maps to the dc:source property at the vocabulary level.
urlReference | URLs for the external vocabulary | uri | 0..n | Maps to the property rdf:seeAlso.
urlBartoc | Bartoc URL | uri | 0..1 | URL of the BARTOC registry. Maps to the property rdf:seeAlso. 
urlConceptScheme | Concept scheme URL | uri | 0..1 | Maps to the property skos:ConceptScheme. If not available, leave blank and it will be assigned by the NKR
technicalArtifacts | SKOS technical artifacts | object | 0..n | SKOS technical artifacts for the vocabulary. May be in the CSV, TTL, RDF/XML or JSON-LD formats.
technicalArtifacts.technicalArtifactUrl | Technical artifact URL | uri | 1..1 | 
technicalArtifacts.technicalArtifactFormat | Format | enum | 1..1 | Format of the technical artifact
status | Status | enum | 0..1 | 
repository | Repository | handle reference | 0..n | 
controlledVocabulary | Approved as | handle reference | 0..1 | Approved as controlled vocabulary. Provide a link to an object of type ControlledVocab.
contactPerson | Contact person | object | 0..n | 
contactPerson.name | Name | string | 1..1 | 
contactPerson.email | Email | email | 1..1 | 
contactPerson.affiliation | Affiliation | string | 0..1 | 
curatorComment | NKR curator comment | string | 0..1 | 
