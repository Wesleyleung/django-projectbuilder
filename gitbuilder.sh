#!/bin/bash
# Steve Phillips / elimisteve
# 2012.02.05

if [ -z $1 ]; then
    echo Usage: `basename $0` project_name
    exit 0
fi

PROJECT_NAME=$1

echo "Creating $PROJECT_NAME directory and sub-directories"
echo
mkdir $PROJECT_NAME
chmod 777 $PROJECT_NAME  # FIXME
# Code is checked out to here as per bare/hooks/post-receive
mkdir $PROJECT_NAME/${PROJECT_NAME}_site
chmod 777 $PROJECT_NAME/${PROJECT_NAME}_site  # FIXME
git init --bare $PROJECT_NAME/bare
# Delete default hooks
rm $PROJECT_NAME/bare/hooks/*

# Put our custom hooks in place
cp hooks/* $PROJECT_NAME/bare/hooks/
for file in $PROJECT_NAME/bare/hooks/*; do
    sed -i "s/PROJECT_NAME/$PROJECT_NAME/g" $file
done

echo -e "If you're on a server, run\n\n    sudo bash -c \"./apachebuilder.sh $PROJECT_NAME\"\n\nto create and install an Apache config file, as well as set up sites-enabled and sites-available."
echo
echo -e "On your local dev machine, run\n\n    python djangobuilder.py $PROJECT_NAME\n\nthen push to (the probably remote) $PROJECT_NAME/bare/ directory"
#echo "Run proto-new-virtualhost-subdomain.py to manually create a new Apache config file."
