#!/usr/bin/env python
from shutil import copyfile
from shutil import copytree
from shutil import rmtree
from functools import reduce
import subprocess
import fnmatch
import pickle
import time
import sys
import os

## TODO:
## Deleted files
## Moved files
## Cleanup when deploy fails, better error and ignore options

LAZY_DIR = os.path.dirname(__file__) + "/"
LOCAL_DIR = os.getcwd() + "/"
MODEL_FILENAME = "model.p"
TEMP_DIR_NAME = "temp"

PIPE = subprocess.PIPE

def printProgress(preamble, progress, segments):
	fillThresh = 1/segments
	fill = 0
	while progress > fillThresh * fill:
		fill += 1
	bar = "\r" + preamble + "[" + fill * "=" + (segments-fill) * " " + "]"
	print(bar, end="")

def execute(cmd):
    process = subprocess.Popen(cmd, stdout=PIPE, universal_newlines=True)
    for stdout_line in iter(process.stdout.readline, ""):
        yield stdout_line 
    process.stdout.close()
    process.wait()

class LazyDeployer:
	def registerSeed(self, model):
		print("Registered seed commit")
		process = subprocess.Popen(["git", "rev-parse", "--short", "HEAD"], stdout=PIPE, stderr=PIPE)
		stdoutput, stderroutput = process.communicate()
		model[LOCAL_DIR] = stdoutput.decode("utf-8")[:-1]
		pickle.dump(model, open(LAZY_DIR + MODEL_FILENAME, "wb"))

	def deploy(self, reset):
		## Load local storage
		model = None
		try:
			model = pickle.load(open((LAZY_DIR + MODEL_FILENAME), "rb"))
		except:
			print("Registering model")
			model = {LOCAL_DIR + "FILES": {}}

		## Clear cache if reset flag provided
		if reset:
			print("Cleared file tracking")
			model[LOCAL_DIR + "FILES"] = {}
			self.registerSeed(model)
			sys.exit(0)

		## Get last successful commit otherwise register current
		lastHash = None
		try:
			lastHash = model[LOCAL_DIR]
		except:
			self.registerSeed(model)
			sys.exit(0)

		## Read forceignore
		patterns = ["**.json", ".*", "**.ts", "**.resource"]
		ignore = open(".forceignore", "r")
		ignorelines = ignore.readlines()
		for line in ignorelines:
			if "#" in line or len(line.strip()) == 0:
				continue
			patterns.append(line.strip())

		## Get diffed files against last commit
		process = subprocess.Popen(["git", "diff", lastHash, "--name-only", "--diff-filter=AMB"], stdout=PIPE, stderr=PIPE)
		stdoutput, stderroutput = process.communicate()
		diffFileList = stdoutput.decode("utf-8")[:-1].split("\n")

		## Get untracked diffed files
		process = subprocess.Popen(["git", "ls-files", ".", "--exclude-standard", "--others"], stdout=PIPE, stderr=PIPE)
		stdoutput, stderroutput = process.communicate()
		untrackedFileList = stdoutput.decode("utf-8")[:-1].split("\n")

		## Filter untracked files
		dirtyFileList = []
		for file in untrackedFileList:
			if file != "":
				dirtyFileList.append(file)

		## Merge untracked files with diffed committed files
		uniqueFileList = diffFileList + list(set(dirtyFileList) - set(diffFileList))

		## Filter filelist by forceignore and last modified date
		fileList = []
		for file in uniqueFileList:
			isIgnored = False
			for pattern in patterns:
				if fnmatch.fnmatch(file, pattern) or file.split("/")[-1][0] == ".":
					isIgnored = True
					break
			modTime = os.path.getctime(file)
			if file in model[LOCAL_DIR + "FILES"]:
				if modTime == model[LOCAL_DIR + "FILES"][file]:
					continue
			model[LOCAL_DIR + "FILES"][file] = modTime
			if file.startswith("src") and not isIgnored:
				fileList.append(file)

		if not len(fileList):
			print("No files changed.")
			sys.exit(0)

		## Create temporary directory
		process = subprocess.Popen(["mkdir", TEMP_DIR_NAME], stdout=PIPE, stderr=PIPE)
		stdoutput, stderroutput = process.communicate()

		## Copy files to temporary directory
		count = 0
		copyIssues = []
		copiedTrees = []
		for file in fileList:
			name = file.split("/")[-1]
			printProgress("Preparing files ", count/len(fileList), 30)
			count += 1

			if "staticresources" in file:
				index = file.index("staticresources") + 15
				if file[0:index] in copiedTrees:
					continue
				copiedTrees.append(file[0:index])
				os.makedirs(os.path.dirname("./" + TEMP_DIR_NAME + "/" + file[0:len(name)-1]), exist_ok=True)
				copytree(file[0:index], "./" + TEMP_DIR_NAME + "/" + file[0:index])
				continue
			elif "object-meta.xml" in file:
				index = file.rindex("/")
				if file[0:index] in copiedTrees:
					continue
				copiedTrees.append(file[0:index])
				os.makedirs(os.path.dirname("./" + TEMP_DIR_NAME + "/" + file[0:len(name)-1]), exist_ok=True)
				copytree(file[0:index], "./" + TEMP_DIR_NAME + "/" + file[0:index])
				continue
			elif "field-meta.xml" in file:
				index = file[0:file.rindex("/")].rindex("/")
				if file[0:index] in copiedTrees:
					continue
				copiedTrees.append(file[0:index])
				os.makedirs(os.path.dirname("./" + TEMP_DIR_NAME + "/" + file[0:len(name)-1]), exist_ok=True)
				copytree(file[0:index], "./" + TEMP_DIR_NAME + "/" + file[0:index])
				continue
			try:
				copyfile(file, "./" + TEMP_DIR_NAME + "/" + name)
			except:
				copyIssues.append(name)
			if "-meta.xml" in file:
				try:
					copyfile(file[0:-8], "./" + TEMP_DIR_NAME + "/" + name[0:-8])
				except:
					pass
			else:
				try:
					copyfile(file + "-meta.xml", "./" + TEMP_DIR_NAME + "/" + name + "-meta.xml")
				except:
					pass
		print("\r", end="")
		if len(copyIssues):
			print("Unable to copy:" + reduce(lambda cur, next: "\n" + cur + "\n" + next, copyIssues))

		## Deploy temporary directory
		errors = ""
		for line in execute(["sfdx", "force:source:deploy", "-p", TEMP_DIR_NAME]):
			if line[0:5] == "SOURCE" or line[0:3] =="***":
				print("\r" + line.strip() + " "*30, end="")
				continue
			elif line[0:6] == "Job ID":
				print("\n" + line.strip())
				continue
			if "error" in line.lower() and not "Dependent class is invalid" in line:
				errors += line

		## Remove temporary directory
		rmtree(TEMP_DIR_NAME)

		if len(errors):
			print(errors.strip())
			sys.exit(0)

		## Save current commit as next seed if successful
		process = subprocess.Popen(["git", "rev-parse", "--short", "HEAD"], stdout=PIPE, stderr=PIPE)
		stdoutput, stderroutput = process.communicate()
		model[LOCAL_DIR] = stdoutput.decode("utf-8")[:-1]
		pickle.dump(model, open(LAZY_DIR + MODEL_FILENAME, "wb"))
		sys.exit(0)

def main():
	reset = False
	if len(sys.argv) == 2 and sys.argv[1] == "-r":
		reset = True
	elif len(sys.argv) > 1:
		print("Invalid syntax. Run without args or with -r to reset cache.")
		sys.exit(0)
	deployer = LazyDeployer()
	deployer.deploy(reset)

if __name__ == "__main__":
	main()