#!/bin/sh
echo "Cleaning all to default state..."
rm -rf ./okd-ignition/
rm -rf ./terraform/.terraform
rm ./terraform/.terraform.lock.hcl
rm ./terraform/terraform.tfstate
rm ./terraform/terraform.tfstate.backup
rm -rf __pycache__
rm ./terraform/temp_hosts.txt
