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

# ------------------------------------------------------------------------------
# Simple collaboration

# Endpoint list
openstack endpoint list
openstack endpoint list --os-scope '{"identity": "'$CLOUD'"}'
openstack endpoint list --os-scope '{"identity": "'$DUOLC'"}'

# Image list
openstack image list
openstack image list --os-scope '{"image": "'$CLOUD'"}'
openstack image list --os-scope '{"image": "'$DUOLC'"}'

# Network list
openstack network list
openstack network list --os-scope '{"network": "'$CLOUD'"}'
openstack network list --os-scope '{"network": "'$DUOLC'"}'

# Start of a VM with image in another Cloud
openstack server create my-vm \
          --os-scope '{"image": "'$DUOLC'"}' \
          --flavor m1.tiny \
          --image cirros-0.3.5-x86_64-disk \
          --network private \
          --wait

openstack server list

openstack server delete my-vm

# ------------------------------------------------------------------------------
# Identity collaboration

# Define a scope where the identity is on CLOUD, and everything else
# on DUOLC.
SCOPE=' { "identity":  "'$CLOUD'"'`
      `', "compute":   "'$DUOLC'"'`
      `', "network":   "'$DUOLC'"'`
      `', "placement": "'$DUOLC'"'`
      `'}'

# Use credential of CLOUD and starts VM on DUOLC.
#
# Note: Using `--network private` works because I am doing my request
# as an admin. And admin can use any network. But with a non admin
# member, the project-id of the private network would be wrong and I
# would have to create a network with the project-id@CloudOne.
openstack server create my-vm \
          --os-scope "$SCOPE" \
          --flavor m1.tiny \
          --image cirros-0.3.5-x86_64-disk \
          --network private \
          --wait

# Nothing appear: the VM doesn't exist on CLOUD
openstack server list

# Here, it works because we go with the "$SCOPE".
openstack server list --os-scope "$SCOPE"

# We are only interested in VM. Does it mean we could shrink the scope
# to only `compute`? Yes it works.
openstack server list --os-scope '{"compute": "'$DUOLC'"}'

# But actually, I am not really shrinking the scope to only `compute`.
# I am rather saying that everything happens in CLOUD except for
# compute that happens in DUOLC. If I would like to /infer/ the SCOPE,
# it should be
openstack server list --os-scope '{"identity": "'$CLOUD'", "compute": "'$DUOLC'"}'

# My VM is living on DUOLC. Does it work if I use `identity` of DUOLC?
# NOP, it doesn't. My VM has been booted with identity in CLOUD, which
# means its project-id is `project-id@CLOUD`. Whereas, the following
# command filters on project-id `project-id@DUOLC` due to `identity`
# of DUOLC.
openstack server list --os-scope '{"identity": "'$DUOLC'", "compute": "'$DUOLC'"}'

# But the VM is living on DUOLC. I mean, doing a ` sudo virsh list` on
# DUOLC shows me the VM. Same by looking into `nova.Cell1.instances`
# database. So I would be able to see it at some point with the
# OpenStack CLI. Yes, I can see it, by adding the `--all-project`
# parameter to the CLI, so it doesn't filter on `project-id`.
openstack server list --all-project --os-scope '{"identity": "'$DUOLC'", "compute": "'$DUOLC'"}'

openstack server delete my-vm --os-scope "$SCOPE"

# ------------------------------------------------------------------------------
# ill collaboration
set +o errexit

# Start a VM on CLOUD with a network in DUOLC.
openstack server create my-vm \
          --os-scope '{"network": "'$DUOLC'"}' \
          --flavor m1.tiny \
          --image cirros-0.3.5-x86_64-disk \
          --network private \
          --wait

# Start a VM on CLOUD with placement in DUOLC.
# FIXME
openstack server create my-vm \
          --os-scope '{"placement": "'$DUOLC'"}' \
          --flavor m1.tiny \
          --image cirros-0.3.5-x86_64-disk \
          --network private \
          --wait

# XXX: Because the previous command works -- and I don't understand
# how! -- I have to delete `my-vm`.
openstack server delete my-vm
