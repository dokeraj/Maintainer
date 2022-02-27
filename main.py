import docker
import schedule
import time
import configInit
import calendar
from datetime import datetime
import backupServices
import sys
import watchtowerService
import util


def checkBinds(dockerClient):
    appDataBind = "/appData"
    backupBind = "/backup"
    for container in dockerClient.containers.list():
        if "dokeraj/maintainer" in container.attrs["Config"]["Image"]:
            listHasBinds = []
            for bind in container.attrs["HostConfig"]["Binds"]:
                if backupBind in bind.split(":")[-1]:
                    listHasBinds.append(True)
                if appDataBind in bind.split(":")[-1]:
                    listHasBinds.append(True)
            filteredBinds = [hasBind for hasBind in listHasBinds if hasBind]
            return len(filteredBinds) == 2
        else:
            return False


def checkIfContainersExist(config, dockerClient):
    for service in config.dockerServices:
        try:
            print(f"Trying to get container ${service.name}!")
            dockerClient.containers.get(service.name)
        except Exception as e:
            util.notifyUser(15539485, config, True,
                            f"Error while checking available Docker containers",
                            f"Cannot find the container `{service.name}` in docker server. \nThis means that the selected container: `{service.name}` cannot be backed up. **Maintainer** will now shut down!")
            ## this will not invoke deathwatch
            sys.exit()



def mainLastDayOfMonth(config, client):
    # check to see if it is in fact the last day of the month - and if so, then allow the schedule to take place
    today = datetime.today()
    curDay = today.day
    daysInCurMonth = calendar.monthrange(today.year, today.month)[1]

    if (daysInCurMonth - 7) < curDay:
        startMainProcess(config, client)


def startMainProcess(config, dockerClient):
    cNamesSet = set()
    for service in config.dockerServices:
        cNamesSet.add(f"- *{service.name}*")

    containerNames = "\n".join(cNamesSet)
    util.notifyUser(4967467, config, True, ":checkered_flag: Starting scheduled docker update process", f"The following services will be backed up:\n{containerNames}")

    checkIfContainersExist(config, dockerClient)

    ## backup All Specified Services
    backupServices.createBackup(config, dockerClient)

    ## run watchtower
    watchtowerService.update(config, dockerClient)

    ## start all stopped services!!
    backupServices.startContainers(config, dockerClient)

    util.notifyUser(4967467, config, True, "Updating finished successfully!",
                    "See you at the next scheduled time :wink:")


def handleScheduling(config, dockerClient):
    if config.dailySchedule is not None:
        schedule.every().day.at(config.dailySchedule.time).do(startMainProcess, config, dockerClient)
    if config.weeklySchedule is not None:
        if config.weeklySchedule.day == "MON":
            schedule.every().monday.at(config.weeklySchedule.time).do(startMainProcess, config, dockerClient)
        if config.weeklySchedule.day == "TUE":
            schedule.every().tuesday.at(config.weeklySchedule.time).do(startMainProcess, config, dockerClient)
        if config.weeklySchedule.day == "WED":
            schedule.every().wednesday.at(config.weeklySchedule.time).do(startMainProcess, config, dockerClient)
        if config.weeklySchedule.day == "THU":
            schedule.every().thursday.at(config.weeklySchedule.time).do(startMainProcess, config, dockerClient)
        if config.weeklySchedule.day == "FRI":
            schedule.every().friday.at(config.weeklySchedule.time).do(startMainProcess, config, dockerClient)
        if config.weeklySchedule.day == "SAT":
            schedule.every().saturday.at(config.weeklySchedule.time).do(startMainProcess, config, dockerClient)
        if config.weeklySchedule.day == "SUN":
            schedule.every().sunday.at(config.weeklySchedule.time).do(startMainProcess, config, dockerClient)
    if config.lastDayOfMonthSchedule is not None:
        if config.lastDayOfMonthSchedule.day == "MON":
            schedule.every().monday.at(config.lastDayOfMonthSchedule.time).do(mainLastDayOfMonth, config, dockerClient)
        if config.lastDayOfMonthSchedule.day == "TUE":
            schedule.every().tuesday.at(config.lastDayOfMonthSchedule.time).do(mainLastDayOfMonth, config, dockerClient)
        if config.lastDayOfMonthSchedule.day == "WED":
            schedule.every().wednesday.at(config.lastDayOfMonthSchedule.time).do(mainLastDayOfMonth, config,
                                                                                 dockerClient)
        if config.lastDayOfMonthSchedule.day == "THU":
            schedule.every().thursday.at(config.lastDayOfMonthSchedule.time).do(mainLastDayOfMonth, config,
                                                                                dockerClient)
        if config.lastDayOfMonthSchedule.day == "FRI":
            schedule.every().friday.at(config.lastDayOfMonthSchedule.time).do(mainLastDayOfMonth, config, dockerClient)
        if config.lastDayOfMonthSchedule.day == "SAT":
            schedule.every().saturday.at(config.lastDayOfMonthSchedule.time).do(mainLastDayOfMonth, config,
                                                                                dockerClient)
        if config.lastDayOfMonthSchedule.day == "SUN":
            schedule.every().sunday.at(config.lastDayOfMonthSchedule.time).do(mainLastDayOfMonth, config, dockerClient)


if __name__ == '__main__':
    print("STARTING SCRIPT!")

    try:
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    except Exception as e:
        print("ERROR: cannot find docker server! now exiting!")
        sys.exit(0)

    # Check if /appData and /backup bind has been setup properly
    if checkBinds(client):
        config = configInit.initConfig(client)

        backupServices.checkForInitialBackup(config, client)

        handleScheduling(config, client)

        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        print("ERROR: The mounts /appData or /backup were not bound! Please use the `-v` docker param to bind these two folders! Now exiting!")
        sys.exit(0)
