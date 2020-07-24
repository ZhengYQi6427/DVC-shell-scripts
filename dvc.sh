#!/bin/sh

##### CONSTANT
cfg="dvc.cfg"
if [ -f $cfg ]; then
	source $cfg
fi

repo=$(echo "$github_repo" | cut -d'/' -f 5)
repo_name=${repo:0:${#repo}-4}

##### FUNCTIONS
init()
{ 
    cd $repo_name	

    echo -n "Do you need to install or update DVC? [y/n]"
    read
    if [ "$REPLY" = "y" ]; then 
        sudo apt update
        sudo apt install dvc
        sudo apt install tree
    fi
    
    # Initialize DVC
    if [ ! -e ".dvc" ]; then
	    dvc init
    fi
    # commit to git
    git add .
    git commit -m "Initialize DVC project"
    cd ..
    echo "========================Initialization Finished========================"
}

getCode()
{
    if [ -f "$repo_name" ]; then
	    rm -rf $repo_name
    fi
    git clone "$github_repo"
    rm -rf .git

    git add $(pwd)/$repo_name
    git commit -m 'add code'

    echo "==============================Code Added==============================="
}


##### MAIN
getCode

if [ "$needInitialize" = "true" ]; then
	init
fi

i=1
until [ $i -gt $pipelinesNum ];
do
	python runPipeline.py ${pipeline[$i]}
	# runPipeline ${pipeline[$i]}
    # echo "${pipeline[$i]}"
	i=$((i + 1))
    echo " "
    echo " "
done

echo -n "Show metrics? [y/n]"
read
if [ "$REPLY" = "y" ]; then 
    dvc metrics show
fi
