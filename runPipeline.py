import os
import sys
import subprocess
import glob
import configparser


class Pipeline:
    def __init__(self, filename):
        self.experimentName = filename[:-9]
        self.config = configparser.ConfigParser()
        self.config.read(filename)
        # get code from gthub
        self.gitHubRepo = self.config.get("Basics", "gitHubRepo")
        self.repoName = self.gitHubRepo.split("/")[-1][:-4]
        try:
            os.system("git clone " + self.gitHubRepo)
        except Exception as e:
            print(e)
        # all following steps would be done inside local repo
        os.system("cd " + self.repoName)
        

    def getRepo(self):
        try:
            os.system("init dvc ")
            os.system("git add . ")
            os.system("git commit -m 'Initialize DVC project'")
        except Exception as e:
            print(e)

    def setRemote(self):
        self.dataRemote = self.config.get("Remote", "dataRemote")
        self.cfgFilesRemote = self.config.get("Remote", "cfgFilesRemote")
        cmd = "dvc remote add  -f dataRemote " + self.dataRemote
        os.system(cmd)
        cmd = "dvc remote add -f cfgFilesRemote " + self.cfgFilesRemote
        os.system(cmd)
        cmd = "dvc remote add -f gitHubRepo" + self.gitHubRepo
        os.system(cmd)
        os.system("git commit .dvc/config -m 'Configure data storage'")
        # os.system("dvc push -r gitHubRepo")

    def getData(self):
        self.dataRemote = self.config.get("Remote", "dataRemote")
        self.cfgFilesRemote = self.config.get("Remote", "cfgFileRemote")
        if not os.path.isfile("/data"):
            os.system("mkdir data")
        if not os.path.isfile("/cfg"):
            os.system("mkdir cfg")

        dataFileList = self.config.get("Data", "dataFileList").split(', ')
        cfgFileList = self.config.get("Data", "cfgFileList").split(', ')

        for file in dataFileList:
            cmd = "dvc get -q " + self.dataRemote + "/" + file + " -o data/" + file
            os.system(cmd)
            # Track a data file
            cmd = "dvc add data/" + file
            os.system(cmd)
        # Commit to Git
        os.system("git add /data")
        os.system("git commit -m 'Add raw data to project'")

        for file in cfgFileList:
            cmd = "dvc get -q " + self.cfgFilesRemote + "/" + file + " -o cfg/" + file
            os.system(cmd)
            # Track a data file
            cmd = "dvc add cfg/" + file
            os.system(cmd)
        os.system("git add /cfg")
        os.system("git commit -m 'Add config files to project'")

        # os.system("dvc push -q")

    def preprocess(self):
        scrList = self.config.get("Preprocess", "scrList").split(', ')
        outputs = self.config.get("Preprocess", "output").split(', ')
        cmd1 = "dvc run " \
               "-f preprocess.dvc "
        cmd2 = ""
        cmd3 = "python "
        for scr in scrList:
            cmd1 += "-d " + scr + " "
            cmd3 += scr + " && "
        for output in outputs:
            cmd2 += "-o " + output + " "
        cmd = cmd1 + cmd2 + "" if cmd3 == "python " else cmd3[:-3]
        os.system(cmd)

        os.system("git add preprocess.dvc")
        os.system("git commit -m 'Create Stage: preprocess'")
        os.system("dvc push -q")

    def train(self):
        # for darknet usecase only
        scr = self.config.get("Train", "scr")

    def validate(self):
        # for darknet usecase only
        cmd = "dvc run -n validation"
        input = " -d " + self.config.get("Validate", "input")
        configuration = " -d " + self.config.get("Validate", "configuration")
        weights = " -d " + self.config.get("Validate", "weights")
        outputs = self.config.get("Validate", "outputs").split(', ')
        outputsCmd = ""
        for output in outputs:
            outputsCmd = " -o " + output
        cmd += input + configuration + weights + outputsCmd + " -w " + self.config.get("Validate", "directory") + " "
        cmd += self.config.get("Validate", "src") + " detector valid " \
               + self.config.get("Validate", "data") + self.config.get("Validate", "configuration")\
               + self.config.get("Validate", "weights") + " -dont_show "\

        # print(cmd)
        '''
        os.system(cmd)

        os.system("git add validation.dvc")
        os.system("git commit -m 'Create Stage: validation'")
        os.system("dvc push -q")
        '''

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



    def showMetric(self):
        os.system("dvc metrics show")

    def showPipeline(self):
        os.system("tree -a")


if __name__ == "__main__":
    newPip = Pipeline(sys.argv[1])
    print("=======================Start building " + newPip.experimentName + "===========================")

    print("Pipeline running ......")

    if newPip.config.get("Data", "needGetData") == "true":
        newPip.getData()
    if newPip.config.get("Remote", "needSetRemote") == "true":
        newPip.setRemote()
    if newPip.config.get("Preprocess", "needPreprocess") == "true":
        newPip.preprocess()
    if newPip.config.get("Train", "needTrain") == "true":
        newPip.train()
    if newPip.config.get("Validate", "needValidate") == "true":
        newPip.validate()
    if newPip.config.get("ResultConvert", "needResultConvert") == "true":
        newPip.resultConvert()
    if newPip.config.get("Evaluate", "needEvaluate") == "true":
        newPip.evaluate()

    print("=========================Finish building " + newPip.experimentName + "=========================")
    os.system("cd .. ")

