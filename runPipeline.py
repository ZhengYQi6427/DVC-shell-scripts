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
        
        self.pipeName = filename.split("/")[-1][:-9]
        self.makedir("../" + self.pipeName)
        self.makedir("../" + self.pipeName + "/" + self.repoName)
        
        try:
            os.system("git clone " + self.gitHubRepo + 
                " ../" + self.pipeName + "/" + self.repoName)
        except Exception as e:
            print(e)
        # all following steps would be done inside this local repo
        os.chdir("../" + self.pipeName + "/" + self.repoName)       

    def initDVC(self):
        try:
            os.system("dvc init -f")
            os.system("git add . ")
            os.system("git commit -m 'Initialize DVC project'")
        except Exception as e:
            print(e)

    def setRemote(self):
        self.dataRemote = self.config.get("Remote", "dataRemote")
        cmd = "dvc remote add -f dataRemote " + self.dataRemote
        os.system(cmd)
        cmd = "dvc remote add -f gitHubRepo " + self.gitHubRepo
        os.system(cmd)
        os.system("git add . ")
        os.system("git commit .dvc/config -m 'Set dvc remote'")
        # os.system("dvc push -r gitHubRepo")

    def getData(self):
        # get data from Synology NAS
        self.dataRemote = self.config.get("Remote", "dataRemote")
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

        # Commit to Git
        os.system("git commit -m 'Track data with dvc'")

        # os.system("dvc push -q")

    def getTrainSet(self):
        scrList = self.config.get("TrainSet", "scr").split(', ')
        self.trainSets = []
        prefix = "train_"

        for file in self.trainFileList:
            self.trainSets.append(prefix + file.split('/')[-1] + ".txt")

        cmd1 = "dvc run " \
               "-f getTrainSet.dvc "
        cmd2 = ""
        cmd3 = "python "
        for scr in scrList:
            cmd1 += "-d " + scr + " "
            cmd3 += scr + " && "
        for output in self.trainSets:
            cmd2 += "-o " + output + " "
        cmd3 = "" if cmd3 == "python " else cmd3[:-3]
        cmd = cmd1 + cmd2 + cmd3 + "./data/train/"
        os.system(cmd)

        os.system("git add getTrainSet.dvc .gitignore")
        os.system("git commit -m 'Create Stage: generate trainset'")
        # os.system("dvc push -q")

        # modify config/traffic.data
        self.overwriteLine("config/traffic.data", 1, 
            "valid = " + ', '.join(self.trainSets) + "\n")
        os.system("git add config/traffic.data")
        os.system("git commit -m 'modify traffic.data'")

    def getTestSet(self):
        scrList = self.config.get("TestSet", "scr").split(', ')
        self.testSets = []
        prefix = "test_"

        for file in self.testFileList:
            self.testSets.append(prefix + file.split('/')[-1] + ".txt")

        cmd1 = "dvc run " \
               "-f getTestSet.dvc "
        cmd2 = ""
        cmd3 = "python "
        for scr in scrList:
            cmd1 += "-d " + scr + " "
            cmd3 += scr + " && "
        for output in self.testSets:
            cmd2 += "-o " + output + " "
        cmd3 = "" if cmd3 == "python " else cmd3[:-3]
        cmd = cmd1 + cmd2 + cmd3 + "./data/test/"
        os.system(cmd)

        os.system("git add getTestSet.dvc .gitignore")
        os.system("git commit -m 'Create Stage: generate testset'")
        # os.system("dvc push -q")

        # modify config/traffic.data
        self.overwriteLine("config/traffic.data", 2, 
            "valid = " + ', '.join(self.testSets) + "\n")
        os.system("git add config/traffic.data")
        os.system("git commit -m 'modify traffic.data'")

    def train(self):
        # for darknet usecase only
        scr = self.config.get("Train", "scr")

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

        cmd += data + configuration + weights + outputs + " -w ./ --force "
        cmd += self.config.get("Validate", "src") + " detector valid " \
               + self.config.get("Validate", "data") + " " + self.config.get("Validate", "configuration")\
               + " " + self.config.get("Validate", "weights") + " -dont_show "

        # print(cmd)
        os.system(cmd)

        os.system("git add validation.dvc")
        os.system("git commit -m 'Create Stage: validation'")
        # os.system("dvc push -q")

    def resultConvert(self):
        # for darknet usecase only
        cmd = "dvc run -n result-conversion"
        inputs = self.config.get("ResultConvert", "inputs").split(', ')
        for input in inputs:
            cmd += " -d " + input
        outputs = self.config.get("ResultConvert", "outputs").split(', ')
        for output in outputs:
            cmd += " -o " + output
        cmd += " -w " + self.config.get("ResultConvert", "directory")
        scrList = self.config.get("ResultConvert", "src").split(', ')
        cmd1 = " python "
        for scr in scrList:
            cmd1 += scr + " && "
        cmd += "" if cmd1 == " python " else cmd1[:-3]

        # print(cmd)
        '''
        os.system(cmd)

        os.system("git add result-conversion.dvc")
        os.system("git commit -m 'Create Stage: result conversion'")
        os.system("dvc push -q")
        '''

    def evaluate(self):
        # for darknet usecase only
        cmd = "dvc run -n evaluation"
        inputs = self.config.get("Evaluate", "inputs").split(', ')
        for input in inputs:
            cmd += " -d " + input
        cmd += " -M metrics.json"
        cmd += " -w " + self.config.get("ResultConvert", "directory")
        scrList = self.config.get("ResultConvert", "src").split(', ')
        cmd1 = " python "
        for scr in scrList:
            cmd1 += scr + " && "
        cmd += "" if cmd1 == " python " else cmd1[:-3]

        # print(cmd)

        '''
        os.system(cmd)

        os.system("git add evaluation.dvc")
        os.system("git commit -m 'Create Stage: evaluation'")
        os.system("dvc push -q")
        '''
        cmd = "git tag -a '" + self.experimentName + "' -m '" + self.experimentName + " evaluation'"
        # print(cmd)
        # os.system(cmd)

    def makedir(self, dir):
        if not os.path.isfile(dir):
            os.system("mkdir " + dir)

    def getFromNAS(self, dir, fileList):
        try:
            for file in fileList:
                name = file.split('/')[-1]
                cmd = "scp " + self.dataRemote[4:] + "/" + file + " " + dir
                os.system(cmd)
                # Track a data file
                cmd = "dvc add " + dir + name
                os.system(cmd)
                os.system("git add " + dir + name + ".dvc" + " .gitignore")
        except Exception as e:
            print(e)

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
    newPip.getTestSet()
    if newPip.config.get("Validate", "needValidate") == "true":
        # newPip.getTestSet()
        newPip.validate()
    if newPip.config.get("ResultConvert", "needResultConvert") == "true":
        newPip.resultConvert()
    if newPip.config.get("Evaluate", "needEvaluate") == "true":
        newPip.evaluate()

    print("=========================Finish building " + newPip.pipeName + "=========================")
    os.chdir("../../DVC-shell-scripts")

