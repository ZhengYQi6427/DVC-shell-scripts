import os
import sys
import subprocess
import glob
import configparser

class Pipeline:
    def __init__(self, filename):
        self.config = configparser.ConfigParser()
        self.config.read(filename)

        # get code from github
        self.gitHubRepo = self.config.get("Basics", "gitHubRepo")
        self.repoName = self.gitHubRepo.split("/")[-1][:-4]
        self.trainFileList = self.config.get("Data", "trainFileList").split(', ')
        self.testFileList = self.config.get("Data", "testFileList").split(', ')
        self.weights = self.config.get("Data", "weights").split(', ')
        self.branch = self.config.get("Basics", "branch")
        
        self.pipeName = filename.split("/")[-1][:-9]
        self.makedir("../" + self.pipeName)
        self.makedir("../" + self.pipeName + "/" + self.repoName)
        
        try:
            os.system("git clone " + self.gitHubRepo + " ../" + self.pipeName + "/" + self.repoName)
        except Exception as e:
            print(e)
        # all following steps would be done inside this local repo
        os.chdir("../" + self.pipeName + "/" + self.repoName)
        # open a new branch for the experiment
        try:
            os.system("git checkout -b " + self.branch)
        except Exception as e:
            print(e)

    def initDVC(self):
        try:
            os.system("dvc init -f")
            os.system("git add .")
            os.system("git commit -m 'Initialize DVC project'")
        except Exception as e:
            print(e)

    def setRemote(self):
        self.dataRemote = self.config.get("Remote", "dataRemote")
        cmd = "dvc remote add -f dataRemote " + self.dataRemote
        os.system(cmd)
        cmd = "dvc remote add -f gitHubRepo " + self.gitHubRepo
        os.system(cmd)
        os.system("git add .")
        os.system("git commit .dvc/config -m 'Set dvc remote'")

    def getData(self):
        # get data from Synology NAS
        self.dataRemote = self.config.get("Remote", "dataRemote")
        self.password = self.config.get("Remote", "NAS_password")
        os.system("pwd")
        self.makedir("data")
        self.makedir("data/train")
        self.makedir("data/test")
        self.makedir("backup")

        print("##### getting data files for training")
        if self.trainFileList:
            self.getFromNAS("data/train/", self.trainFileList)
        
        print("##### getting data files for testing")
        if self.testFileList:
            self.getFromNAS("data/test/", self.testFileList)

        print("##### getting .weights")
        if self.weights:
            self.getFromNAS("backup/", self.weights)

        print("##### getting other files")
        others = self.config.get("Data", "weights").split(',')
        if others:
            self.getFromNAS("./", others)

        # Commit to Git
        os.system("git add .")
        os.system("git commit -m 'Track data with dvc'")

    def getTrainSet(self):
        srcList = self.config.get("TrainSet", "src").split(', ')
        self.trainSets = []
        prefix = "train_"

        for file in self.trainFileList:
            self.trainSets.append(prefix + file.split('/')[-1] + ".txt")

        cmd1 = "dvc run " \
               "-n TrainSet "
        cmd2 = ""
        cmd3 = "python "
        for file in self.trainFileList:
            cmd1 += "-d " + "./data/train/" + file.split('/')[-1] + " "
        for src in srcList:
            cmd1 += "-d " + src + " "
            cmd3 += src + " && "
        for output in self.trainSets:
            cmd2 += "-o " + output + " "
        cmd3 = "" if cmd3 == "python " else cmd3[:-3]
        cmd = cmd1 + cmd2 + cmd3 + "./data/train/"
        os.system(cmd)

        for file in self.trainFileList:
            print("git add .gitignore ./data/test/frame_dir_" + file.split('/')[-1] + "/*.jpg")
            os.system("git add .gitignore ./data/test/frame_dir_" + file.split('/')[-1] + "/*.jpg")

        # modify config/traffic.data
        self.overwriteLine("config/traffic.data", 2,
                           "train = " + ', '.join(self.trainSets) + "\n")

        os.system("git add .")
        os.system("git commit -m 'Create Stage: generate trainset'")

    def getTestSet(self):
        srcList = self.config.get("TestSet", "src").split(', ')
        self.testSets = []
        prefix = "test_"

        for file in self.testFileList:
            self.testSets.append(prefix + file.split('/')[-1] + ".txt")

        cmd1 = "dvc run -n testSet "
        cmd2 = ""
        cmd3 = "python "
        for file in self.testFileList:
            cmd1 += "-d " + "./data/test/" + file.split('/')[-1] + " "
        for src in srcList:  
            cmd1 += "-d " + src + " " 
            cmd3 += src + " && "
        for output in self.testSets:
            cmd2 += "-o " + output + " "
        cmd3 = "" if cmd3 == "python " else cmd3[:-3]
        cmd = cmd1 + cmd2 + cmd3 + "./data/test/"
        os.system(cmd)

        os.system("sed -i '10,$ d' test_HIKL2D200326T170529_3_0458_0628_calibrated.mp4.txt")

        for file in self.testFileList:
            print("git add .gitignore ./data/test/frame_dir_" + file.split('/')[-1] + "/*.jpg")
            os.system("git add .gitignore ./data/test/frame_dir_" + file.split('/')[-1] + "/*.jpg")

        # modify config/traffic.data
        self.overwriteLine("config/traffic.data", 2, 
            "valid = " + ', '.join(self.testSets) + "\n")

        os.system("git add .")
        os.system("git commit -m 'Create Stage: generate testset'")

    def train(self):
        # for darknet usecase only
        src = self.config.get("Train", "src")

    def validate(self):
        # for darknet usecase only
        if not self.testSets:
            print("No testData available for validation")
            exit(0)
        self.makedir("results")

        cmd = "dvc run -n validation"

        data = " -d " + self.config.get("Validate", "data")
        configuration = " -d " + self.config.get("Validate", "configuration")
        weights = " -d " + self.config.get("Validate", "weights")
        outputs = " --outs-persist ./results/"

        cmd += data + configuration + weights + outputs + " "
        cmd += self.config.get("Validate", "src") + " detector valid " \
               + self.config.get("Validate", "data") + " " + self.config.get("Validate", "configuration")\
               + " " + self.config.get("Validate", "weights") + " -dont_show "

        # print(cmd)
        os.system(cmd)

        os.system("git add .gitignore ./results/")
        os.system("git add .")
        os.system("git commit -m 'Create Stage: validation'")

    def resultConvert(self):
        self.resultsPath = self.config.get("ResultConvert", "resultPath")
        self.result = self.config.get("ResultConvert", "result")
        self.makedir(self.resultsPath)

        # for darknet usecase only
        src = self.config.get("ResultConvert", "src")
        cmd = "dvc run -n res-convert"
        cmd += " -d " + self.config.get("Validate", "data") + " -d ./results"
        cmd += " -d " + src
        cmd += " -o " + os.path.join(self.resultsPath, self.result)
        cmd += " python " + src + " " + self.resultsPath + " " + self.result

        # print(cmd)
        os.system(cmd)

        os.system("git add .gitignore " + os.path.join(self.resultsPath, self.result))
        os.system("git add .")
        os.system("git commit -m 'Create Stage: result conversion'")

    def evaluate(self):
        # for darknet usecase only
        cmd = "dvc run -n evaluation"
        cmd += " -d " + os.path.join(self.resultsPath, self.result)
        cmd += " -d " + self.config.get("Evaluate", "src")
        cmd += " -m metrics.json"
        cmd += " python " + self.config.get("Evaluate", "src") + " " \
               + self.config.get("Evaluate", "groundTruth") + " " + \
               os.path.join(self.resultsPath, self.result)

        # print(cmd)
        os.system(cmd)

        os.system("git add .")
        os.system("git commit -m 'Create Stage: evaluation'")

    def end(self):
        print("Finish building pipelines")
        os.system("cat metrics.json >> report.md")
        os.system("git add .")
        os.system("git commit -m 'Finish building pipelines'")
        # os.system("git tag -a 'new branch " + self.branch + "' -m '"+ self.branch + " new branch'")
        os.system("git push origin " + self.branch)

    def makedir(self, dir):
        if not os.path.isfile(dir):
            os.system("mkdir " + dir)

    def getFromNAS(self, dir, fileList):
        for file in fileList:
            if file:
                name = file.split('/')[-1]
                cmd = "sshpass -p '" + self.password + "' scp -r " + self.dataRemote[4:] + "/" + file + " " + dir
                os.system(cmd)
                # Track a data file
                cmd = "dvc add " + dir + name
                os.system(cmd)
                os.system("git add .gitignore " + dir + name)

    def overwriteLine(self, file, lineNum, text):
        try:
            lines = open(file, 'r').readlines()
            lines[lineNum] = text
            out = open(file, 'w')
            out.writelines(lines)
            out.close()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    newPip = Pipeline(sys.argv[1])
    print("=======================Start building " + newPip.pipeName + "===========================")

    print("Pipeline running ......")

    newPip.initDVC();

    if newPip.config.get("Data", "needGetData") == "true":
        newPip.getData()
    if newPip.config.get("Remote", "needSetRemote") == "true":
        newPip.setRemote()
    if newPip.config.get("Train", "needTrain") == "true":
        newPip.getTrainSet()
        newPip.train()
    if newPip.config.get("Validate", "needValidate") == "true":
        newPip.getTestSet()
        newPip.validate()
        newPip.resultConvert()
    if newPip.config.get("Evaluate", "needEvaluate") == "true":
        newPip.evaluate()

    newPip.end()


    print("=========================Finish building " + newPip.pipeName + "=========================")
    os.chdir("../../DVC-shell-scripts")

