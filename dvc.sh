#!/bin/sh

##### CONSTANT
cfg="dvc.cfg"
if [ -f $cfg ]; then
	source $cfg
fi

##### FUNCTIONS
init()
{
    echo "========================Initialization Start==========================="
    git config --global user.name "$git_user_name"
    git config --global user.email "$git_user_email"
    echo -n "Update DVC? [y/n]"
    read
    if [ "$REPLY" = "y" ]; then
      sudo apt-get update dvc
      sudo apt install dvc
    fi
    pip install requirements.txt
    echo "========================Initialization Finished========================"
}

##### MAIN
#init

for entry in pipelines/*
do
  # echo "$entry"
  python runPipeline.py $entry
done
