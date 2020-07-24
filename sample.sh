#!/bin/sh
# sample scripting

##### CONSTANT

#echo -n "Enter your github repository url > "
#read github_link
#echo -n "Enter your Github repository name > "
#read repo_name
#echo -n "Enter your Synology video file path > "
#read video_link
NAS_account="ra_yz3622"
NAS_password="summer"
echo -n "Enter yout target directory > "
read dir

##### FUNCTIONS

get_videos()
{
   git clone https://github.com/ZhengYQi6427/DVC-data.git
   mv $(pwd)/DVC-data/images $(pwd)
   mv $(pwd)/DVC-data/annotations $(pwd)
   rm -rf DVC-data
   
   dvc add $(pwd)/images
   dvc add $(pwd)/annotations
   git add images.dvc
   git add annotations.dvc
   git commit -m 'add data archive'
}

get_code()
{
   git clone "$github_link"
   rm -rf .git
   cd $repo_name
   sed -i 's+$(pwd)+g' json2voc.py
   cd ..

   git add $(pwd)/$repo_name
   git commit -m 'add code'
}

init()
{  
   if [ -e $dir ]; then
       cd $dir
       echo "Successfully open directory $dir"
   else
       echo "No directory named $dir"
       echo -n "Generate a new directory $dir? [y/n]: "
       read
       if [ "$REPLY" = "y" ]; then
          mkdir $dir
          cd $dir
       else
          echo "Sorry, please create a directory for git and dvc first!"
          exit 0
       fi
   fi

   echo -n "Do you want to install or update DVC? [y/n]"
   read
   if [ "$REPLY" = "y" ]; then 
       sudo apt update
       sudo apt install dvc
       sudo apt install tree
   fi
 
   echo -n "Enter git user name > "
   read git_user_name
   echo -n "Enter git user email > "
   read git_user_email

   git init
   dvc init
}

preprocess(){
    echo -n "Begin preprocessing? [y/n] "
    read
    if [ "$REPLY" = "y" ]; then
        echo -n "How many preprocessing scripts need to run > "
        read file_num

        cd $repo_name
        sudo apt install python-pip
        pip install -r requirements.txt
        echo "$(pwd)"

        i=0
        until [ $i -ge $file_num ];
        do
            echo -n "Enter file $i name > "
            read file_name
            if [ !-e $file_name ]; then
                echo "ERROR: File $varname doesn't exist"
                exit 0
            fi
            python $file_name
            i=$((i + 1))
        done

        cd ..
    fi
}

installDarknet(){
    git clone https://github.com/pjreddie/darknet.git
    cd darknet
    make
    cd ..
}

train(){
    path=$(pwd)
    backup="backup"

    cd $repo_name
    mkdir $backup
    wget https://pjreddie.com/media/files/darknet53.conv.74
    $path/darknet/darknet detector train train_data/traffic.data train_data/traffic.cfg darknet53.conv.74
    
    until [ -e ./$backup/traffic_final.weights ];
    do
        echo "Train ERROR: traffic_final.weights has not been generated! "
        echo -n "Train again? [y/n] "
        read
        if [ "$REPLY" = "y" ]; then
            $path/darknet/darknet detector train train_data/traffic.data train_data/traffic.cfg darknet53.conv.74
        else
            exit 0
        fi
    done

    dvc add ./$backup/traffic_final.weights
    git add ./$backup/traffic_final.weights.dvc

    cd ..
}

getTestVideo(){
    path=$(pwd)

    cd $repo_name
    svn checkout https://github.com/ZhengYQi6427/DVC-data/trunk/vids
    cd vids
    rm -rf .svn
    cd -

    # test video preprocess
    python video2frame.py

    cd ..
}

detect(){
    cd $repo_name
    echo -n "Enter test .txt file name > "
    read $txt_file
    $path/darknet/darknet detector test /traffic_data/traffic.data /traffic_data/traffic.cfg $backup/traffic_final.weights -ext_output  < $txt_file >  ./ result.txt
    cd ..
}

evaluate(){
    python darknet2maskrcnn.py
    dvc add

    dvc run 

    show .metrics
}

##### MAIN
init
rm -rf .dvc
rm -rf .git
# get_code
# get_videos
# preprocess
# train
