#!/bin/sh
echo "Cleaning all to default state..."
rm -rf ./okd-ignition/
rm -rf ./secrets/
rm -r ./terraform/.terraform
rm ./terraform/.terraform.lock.hcl
rm ./terraform/terraform.tfstate
rm ./terraform/terraform.tfstate.backup
rm -rf __pycache__
FILE=./terraform/main.tf.without
rm ./terraform/temp_hosts.txt
if [ -f "$FILE" ]; then
    echo "$FILE exists."
else 
    mv ./terraform/main.tf ./terraform/main.tf.without
    mv ./terraform/main.tf.save ./terraform/main.tf
fi