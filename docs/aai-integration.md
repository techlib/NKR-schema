id | name | data type | cardinality | description
-- | -- | -- | -- | --
id | id | string | 1..1 | 
handleUrl | Handle identifier | uri | 1..1 | Persistent identifier for the record.
name | Name | string | 1..1 | 
voName | Name of the Perun virtual organization | string | 0..1 | Maps to VO attribute "displayName" in AAI for human-readable repository name in GUI.
voShortName | Short name of the Perun virtual organization | string | 0..1 | Short repository name used by the authentication and authorisation infrastructure. Maps to VO attribute "shortName" in AAI for human-readable repository ID in GUI.
facilityId | Perun facility ID | number | 0..1 | Repository identifier used by the access control system. Maps to facility attribute "id" as permanent unique repository ID.
loginUrl | Login URL | uri | 0..1 | Maps to Facility attribute "loginUrl" in AAI for manual validation.
aaiUap | Provisioning | boolean | 0..1 | Information about provisioning user access for the repository.
aaiRbac | RBAC | boolean | 0..1 | Information about the repository implementing centralized role-based access control.
aaiPbac | PBAC | boolean | 0..1 | Information about the repository implementing centralized policy-based access control.
