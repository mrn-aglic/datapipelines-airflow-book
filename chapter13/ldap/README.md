# LDAP

Demonstrate RBAC UI + LDAP authentication using OpenLDAP.
Login in Airflow with username `aflow` and password `test`.

## Details

OpenLDAP is bootstrapped with:

- An admin user (DN=`cn=admin,dc=apacheairflow,dc=com`, password=`admin`)
- A readonly user (DN=`cn=readonly,dc=apacheairflow,dc=com`, password=`readonly`)
- A group named "engineers" (DN=`cn=engineers,dc=apacheairflow,dc=com`)
- A user in this group (DN=`cn=bob smith,dc=apacheairflow,dc=com`, password=`test`)
