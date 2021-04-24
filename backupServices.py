from zipfile import ZipFile
import os
from os import path
import main
from datetime import datetime
import zipfile
import shutil
import util

rootBackupDir = "/backup"


def checkForInitialBackup(config, dockerClient):
    initBckUpFilePath = f"{rootBackupDir}/.initBackup"

    if config.initialBackup:
        if not path.exists(initBckUpFilePath):
            print("Commencing initial backup")
            f = open(initBckUpFilePath, "w")
            f.write("you are a nosy little snowflake, aren't you!?")
            f.close()
            main.startMainProcess(config, dockerClient)
        else:
            print("""Skipping Initial backup! reason: Found the file '.initBackup'""")
    else:
        print("""Skipping Initial backup! reason: Initial backup has been set to 'False' by user in the config.yml file""")


def deleteOldBackups(config):
    bckCount = config.backupsToKeep * (-1)
    bckDirs = [dI for dI in os.listdir(rootBackupDir) if os.path.isdir(os.path.join(rootBackupDir, dI))]
    bckDirs.sort()
    dirsToDel = bckDirs[:bckCount]

    if len(dirsToDel) > 0:
        util.notifyUser(13408299, config, True, descMsg=f"Deleting obsolete backup sessions..")

    for dirToRm in dirsToDel:
        shutil.rmtree(os.path.join(rootBackupDir, dirToRm), True)


def stopContainers(config, dockerClient):
    containersToStop = []
    containersNoStopping = []
    for service in config.dockerServices:
        if service.stopContainer:
            containersToStop.append(service)
        else:
            containersNoStopping.append(service)

    util.notifyUser(13408299, config, True, descMsg=f"Stopping {len(containersToStop)} containers.\nNumber of containers that won't be stopped = {len(containersNoStopping)}")

    for service in containersToStop:
        container = dockerClient.containers.get(service.name)
        container.stop()


def startContainers(config, dockerClient):
    util.notifyUser(13408299, config, True, descMsg=f"Starting all stopped docker containers!")
    for service in config.dockerServices:
        container = dockerClient.containers.get(service.name)
        container.start()


def createBackup(config, dockerClient):
    # stop the containers
    stopContainers(config, dockerClient)

    util.notifyUser(13408299, config, True, f":books: Starting with the backup process (one zipped archive for each service)", "This may take a while..")
    timeNow = str(datetime.now().strftime('%Y_%m_%d %H-%M-%S'))
    currentBckUpJobPath = os.path.join(rootBackupDir, timeNow)

    # create folder with timestamp for the current backup job
    if not os.path.exists(currentBckUpJobPath):
        os.makedirs(currentBckUpJobPath)

    for service in config.dockerServices:
        pathToService = os.path.join(currentBckUpJobPath, service.name)
        # create folder for service
        if not os.path.exists(pathToService):
            os.makedirs(pathToService)

        # put image digest to file in service folder
        container = dockerClient.containers.get(service.name)
        imageDigest = container.attrs["Image"]
        imageName = container.attrs["Config"]["Image"].split(":")[0]
        f = open(os.path.join(pathToService, "imageDigest.txt"), "w")
        f.write(f"{imageName}@{imageDigest}")
        f.close()

        # zip the contents from /appData to /backup
        if service.exclusions is not None:
            exclude = set(service.exclusions)
        else:
            exclude = set()

        if config.useCompression:
            zipType = zipfile.ZIP_LZMA
        else:
            zipType = zipfile.ZIP_STORED

        with ZipFile(file=os.path.join(pathToService, f"{service.name}.zip"), mode='w', compression=zipType,
                     compresslevel=config.compressionLevel) as zipObj:
            for root, dirs, files in os.walk(service.rootDir, topdown=True):
                dirs[:] = [d for d in dirs if d not in exclude]
                files[:] = [f for f in files if f not in exclude]
                for file in files:
                    repath = root[root.find(f"/{service.name}"):]
                    rootFilePath = os.path.join(root, file)
                    zippedFilePath = os.path.join(repath, file)
                    try:
                        zipObj.write(rootFilePath, zippedFilePath)
                    except Exception as e:
                        print(f"WARN: {e}")
                        continue


    # delete the old backups
    deleteOldBackups(config)
