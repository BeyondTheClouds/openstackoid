#!/bin/bash

SCOPE_DELIM="!SCOPE!"
DEVSTACK_URL_PHONY=http://0.0.0.0
DEVSTACK_URL_ONE=http://192.168.144.247
DEVSTACK_URL_TWO=http://192.168.144.248
DEVSTACK_NAME_PHONY="NoWhere"
DEVSTACK_NAME_ONE="CloudOne"
DEVSTACK_NAME_TWO="CloudTwo"

DEVSTACK_URL_LOCAL=${DEVSTACK_URL_ONE}
DEVSTACK_URL_REMOTE=${DEVSTACK_URL_TWO}

DEVSTACK_NAME_LOCAL=${DEVSTACK_NAME_ONE}
DEVSTACK_NAME_REMOTE=${DEVSTACK_NAME_TWO}

#set -x

## get token with "auth.json" file as configuration
## token result is located in headers
function get_token()
{
    local devstack_url=$1
    local token=$(http --headers \
                       ${devstack_url}/identity/v3/auth/tokens \
                       @auth.json | sed '/X-Subject-Token/!d;s/.* //')

    ## cleaning new lines
    token=${token//[$'\t\r\n']} && token=${token%%*( )}
    echo ${token}
}

TOKEN_LOCAL=$(get_token ${DEVSTACK_URL_LOCAL})
echo ${TOKEN_LOCAL}

TOKEN_REMOTE=$(get_token ${DEVSTACK_URL_REMOTE})
echo ${TOKEN_REMOTE}
## tests using glance cli WITHOUT scope

### test glance local
glance --verbose --debug \
       --os-region-name=${DEVSTACK_NAME_LOCAL} \
       --os-auth-url=${DEVSTACK_URL_LOCAL}/identity \
       --os-auth-token=${TOKEN_LOCAL} \
       --os-image-url=${DEVSTACK_URL_LOCAL}/image \
       image-list

### test glance remote SCOPE is required!
SCOPE="{\"identity\":\"${DEVSTACK_NAME_REMOTE}\",\"image\":\"${DEVSTACK_NAME_REMOTE}\"}"
### test glance remote
glance --verbose --debug \
       --os-region-name=${DEVSTACK_NAME_REMOTE} \
       --os-auth-url=${DEVSTACK_URL_REMOTE}/identity \
       --os-auth-token=${TOKEN_REMOTE}${SCOPE_DELIM}${SCOPE} \
       --os-image-url=${DEVSTACK_URL_REMOTE}/image \
       image-list

# ## test using direct API calls
# http ${DEVSTACK_URL_LOCAL}/image/v2/images \
#      X-Auth-Token:${TOKEN_LOCAL} \
#      X-Identity-Region:${DEVSTACK_NAME_LOCAL} \
#      X-Identity-Url:${DEVSTACK_URL_LOCAL}/identity \
#      X-Identity-Cloud:${CLOUD_INSTANCE}

# http --verbose -all ${DEVSTACK_URL_LOCAL}/image/v2/images \
#      X-Auth-Token:"${TOKEN_LOCAL}${SCOPE_DELIM}${SCOPE}" \
#      X-Identity-Region:${DEVSTACK_NAME_LOCAL} \
#      X-Identity-Url:${DEVSTACK_URL_LOCAL}/identity \
#      X-Identity-Cloud:${DEVSTACK_NAME_LOCAL}

# tail -f /var/log/syslog| grep devstack@g-api.service|grep -e "POST\|curl" -i -C2
