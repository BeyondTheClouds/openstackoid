#!/usr/bin/env bash

. /opt/stack/devstack/openrc admin admin

CLOUD1="CloudOne"
CLOUD2="CloudTwo"

if [ "$OS_REGION_NAME" == "$CLOUD1" ]
then
    CLOUD="$CLOUD1"
    DUOLC="$CLOUD2"
else
    CLOUD="$CLOUD2"
    DUOLC="$CLOUD1"
fi

echo "'$CLOUD' is your current cloud"
echo "'$DUOLC' is your second cloud"

# `help set'
set -o errexit
set -o xtrace

# Endpoint list
openstack endpoint list
openstack endpoint list --os-scope '{"identity": "'$CLOUD1'"}'
openstack endpoint list --os-scope '{"identity": "'$CLOUD2'"}'

# Image list
openstack image list
openstack image list --os-scope '{"image": "'$CLOUD1'"}'
openstack image list --os-scope '{"image": "'$CLOUD2'"}'

# Network list
openstack network list
openstack network list --os-scope '{"image": "'$CLOUD1'"}'
openstack network list --os-scope '{"image": "'$CLOUD2'"}'

# Start of a VM with image in another Cloud
openstack server create my-vm \
          --os-scope '{"image": "'$DUOLC'"}' \
          --flavor m1.tiny \
          --image cirros-0.3.5-x86_64-disk \
          --wait

openstack server list

openstack server delete my-vm

# Start of a VM in another Cloud
#
# XXX: network is not set properly, maybe because their is no net in
# $DUOLC with the project id of $CLOUD.
openstack server create my-vm \
          --os-scope '{"compute": "'$DUOLC'", "network": "'$DUOLC'", "placement": "'$DUOLC'"}' \
          --flavor m1.tiny \
          --image cirros-0.3.5-x86_64-disk \
          --wait

openstack server list --os-scope '{"compute": "'$DUOLC'", "network": "'$DUOLC'"}'

openstack server delete my-vm --os-scope '{"compute": "'$DUOLC'", "network": "'$DUOLC'"}'
