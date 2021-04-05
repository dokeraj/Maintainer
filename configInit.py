import yaml
import util
from dataclasses import dataclass
import sys
from typing import List
import os
from os import path
import docker

@dataclass
class DockerService:
    name: str
    rootDir: str
    exclusions: list
    stopContainer: bool


@dataclass
class ConfSchedule:
    day: str
    time: str


@dataclass
class Config:
    watchtowerImage: str
    initialBackup: bool
    weeklySchedule: ConfSchedule
    dailySchedule: ConfSchedule
    lastDayOfMonthSchedule: ConfSchedule
    dockerServices: List[DockerService]
    maintainerUrl: str
    watchtowerUrl: str
    backupsToKeep: int
    useCompression: bool
    compressionLevel: int


conf = Config("containrrr/watchtower:latest", False, None, None, None, None, None, None, 3, False, 5)


def checkMandatoryFields():
    if conf.watchtowerImage is None:
        print("ERROR: Watchtower image digest must be setup in order to start the script! Now exiting!")
        sys.exit(0)
    if conf.weeklySchedule is None and conf.dailySchedule is None and conf.lastDayOfMonthSchedule is None:
        print("ERROR: At least one backup schedule must be setup in order for the script to work! Now exiting!")
        sys.exit(0)
    if conf.weeklySchedule is not None and (conf.weeklySchedule.time is None or conf.weeklySchedule.day is None):
        print("ERROR: Weekly Schedule must have TIME and DAY setup! Now exiting!")
        sys.exit(0)
    if conf.lastDayOfMonthSchedule is not None and (conf.lastDayOfMonthSchedule.time is None or conf.lastDayOfMonthSchedule.day is None):
        print("ERROR: Last Day Of Month Schedule must have TIME and DAY setup! Now exiting!")
        sys.exit(0)
    if conf.dailySchedule is not None and conf.dailySchedule.time is None:
        print("ERROR: Daily Schedule must have TIME field setup! Now exiting!")
        sys.exit(0)

    for s in conf.dockerServices:
        if s.rootDir is None:
            print(f"""ERROR: service "{s.name}" cannot have empty root directory! Now Exiting!""")
            sys.exit(0)

    if conf.maintainerUrl is None:
        print("WARN: Maintainer discord webhook has not been set! Discord notifications are not mandatory but highly recommended!")
    if conf.watchtowerUrl is None:
        print("WARN: Watchtower discord webhook has not been set! Discord notifications are not mandatory but highly recommended!")


def printSetConfig():
    resultStr = "The following config params were set:\n"
    resultStr += f"- watchtower_digest = {conf.watchtowerImage}\n"
    resultStr += f"- initial_backup = {conf.initialBackup}\n"
    resultStr += f"- backups_count = {conf.backupsToKeep}\n"
    resultStr += f"- use_compression = {conf.useCompression}\n"
    resultStr += f"- compression_level = {conf.compressionLevel}\n"

    resultStr += f"Backup Schedule:\n"
    if conf.weeklySchedule is not None:
        resultStr += f"- weekly.day = {conf.weeklySchedule.day}\n"
        resultStr += f"- weekly.time = {conf.weeklySchedule.time}\n"
    if conf.dailySchedule is not None:
        resultStr += f"- daily.time = {conf.dailySchedule.time}\n"
    if conf.lastDayOfMonthSchedule is not None:
        resultStr += f"- last_day_of_month.day = {conf.lastDayOfMonthSchedule.day}\n"
        resultStr += f"- last_day_of_month.time = {conf.lastDayOfMonthSchedule.time}\n"

    resultStr += f"Services to backup:\n"
    for service in conf.dockerServices:
        resultStr += f"- name = {service.name}\n"
        resultStr += f"- root_directory = {service.rootDir}\n"
        if service.exclusions is not None:
            resultStr += f"- exclusions = {'; '.join((str(w) for w in service.exclusions))}\n"
            resultStr += "--------------\n"
        else:
            resultStr += "--------------\n"

    resultStr += f"- discord_webhooks.maintainer = {conf.maintainerUrl}\n"
    resultStr += f"- discord_webhooks.watchtower = {conf.watchtowerUrl}\n"

    print(resultStr)


def initConfig(dockerClient):
    try:
        if path.exists('/yaml/config.yml'):
            with open('/yaml/config.yml') as f:
                docs = yaml.load_all(f, Loader=yaml.FullLoader)

                for doc in docs:
                    for k, v in doc.items():
                        if k == "general_settings" and v is not None:
                            for generalKey, generalVal in v.items():
                                if generalKey == "watchtower_digest" and generalVal != "<PASTE IMAGE DIGEST HERE>":
                                    conf.watchtowerImage = f"containrrr/watchtower@{generalVal}"
                                if generalKey == "initial_backup":
                                    conf.initialBackup = util.safeCastBool(generalVal, False)
                                if generalKey == "backups_count" and generalVal is not None:
                                    conf.backupsToKeep = util.safeCast(generalVal, int, 3)
                                if generalKey == "use_compression" and generalVal is not None:
                                    conf.useCompression = util.safeCastBool(generalVal, False)
                                if generalKey == "compression_level" and generalVal is not None:
                                    compressionLevel = util.safeCast(generalVal, int, 5)
                                    if compressionLevel > 0 and compressionLevel < 10:
                                        conf.compressionLevel = compressionLevel

                        # Backup Schedule
                        if k == "backup_schedule" and v is not None:
                            for backupKey, backupVal in v.items():
                                if backupKey == "weekly" and backupVal is not None:
                                    weeklySchedule = ConfSchedule(None, None)
                                    for weeklyKey, weeklyVal in backupVal.items():
                                        if weeklyKey == "day":
                                            if weeklyVal in ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]:
                                                weeklySchedule.day = weeklyVal
                                            else:
                                                print("ERROR: Weekly schedule's day is not set properly - Please use MON, TUE, WED, THU, FRI, SAT or SUN to specify the day. Now exiting!")
                                                sys.exit(0)
                                        if weeklyKey == "time":
                                            if util.isTimeFormat(weeklyVal):
                                                weeklySchedule.time = weeklyVal
                                            else:
                                                print("ERROR: Weekly time format is not valid! Please use HH:mm format! Now exiting!")
                                                sys.exit(0)

                                    conf.weeklySchedule = weeklySchedule

                                if backupKey == "daily" and backupVal is not None:
                                    dailySchedule = ConfSchedule(None, None)
                                    for dailyKey, dailyVal in backupVal.items():
                                        if dailyKey == "time":
                                            if util.isTimeFormat(dailyVal):
                                                dailySchedule.time = dailyVal
                                            else:
                                                print("ERROR: Daily time format is not valid! Please use HH:mm format! Now exiting!")
                                                sys.exit(0)

                                    conf.dailySchedule = dailySchedule

                                if backupKey == "last_day_of_month" and backupVal is not None:
                                    lastDaySchedule = ConfSchedule(None, None)
                                    for lastDayKey, lastDayVal in backupVal.items():
                                        if lastDayKey == "day":
                                            if lastDayVal.upper() in ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]:
                                                lastDaySchedule.day = lastDayVal
                                            else:
                                                print(
                                                    "ERROR: Last Day Of Month schedule's day is not set properly - Please use MON, TUE, WED, THU, FRI, SAT or SUN to specify the day. Now exiting!")
                                                sys.exit(0)
                                        if lastDayKey == "time":
                                            if util.isTimeFormat(lastDayVal):
                                                lastDaySchedule.time = lastDayVal
                                            else:
                                                print("ERROR: Last Day Of Month time format is not valid! Please use HH:mm format! Now exiting!")
                                                sys.exit(0)

                                    conf.lastDayOfMonthSchedule = lastDaySchedule

                        # Docker services to backup
                        if k == "services_to_backup":
                            tmpSetServices = list()
                            for serviceKey, serviceVal in v.items():
                                try:
                                    dockerClient.containers.get(serviceKey)
                                except Exception as e:
                                    print(f"ERROR: Cannot find docker container with name {serviceKey}! Check the services_to_backup object in the config.yml. Now exiting!")
                                    sys.exit(0)

                                tmpService = DockerService(serviceKey, None, None, True)
                                tmpExclusionFiles = set()
                                for serviceSetting, serviceSettingVal in serviceVal.items():
                                    if serviceSetting == "root_directory" and serviceSettingVal is not None:
                                        if os.path.exists(serviceSettingVal):
                                            if os.listdir(serviceSettingVal):
                                                tmpService.rootDir = serviceSettingVal
                                            else:
                                                print(f"""ERROR: The service: "{serviceKey}" has been specified at an empty directory! Please choose a directory that has the config files for the specified service. Now exiting!""")
                                                sys.exit(0)
                                        else:
                                            print(f"""ERROR: The service: "{serviceKey}" has wrongly setup root_directory! Please make sure the path starts with /appData/<PATH TO SERVICE>. Now exiting!""")
                                            sys.exit(0)
                                    if serviceSetting == "exclusions":
                                        for item in serviceSettingVal:
                                            tmpExclusionFiles.add(util.safeCast(item, str))
                                        tmpService.exclusions = set(filter(None, tmpExclusionFiles))
                                    if serviceSetting == "stop_container" and serviceSettingVal is not None:
                                        tmpService.stopContainer = util.safeCastBool(serviceSettingVal, True)
                                tmpSetServices.append(tmpService)

                            conf.dockerServices = tmpSetServices

                        # Notifications
                        if k == "discord_webhooks":
                            for discordKey, discordVal in v.items():
                                if discordKey == "maintainer" and discordVal != "<PASTE YOUR DISCORD WEBHOOK HERE>":
                                    conf.maintainerUrl = discordVal
                                if discordKey == "watchtower" and discordVal != "<PASTE YOUR DISCORD WEBHOOK HERE>":
                                    conf.watchtowerUrl = discordVal

            checkMandatoryFields()
            printSetConfig()
            return conf

        else:
            print(
                "ERROR: config.yml file not found (please bind the volume that contains the config.yml file) - now exiting!")
            sys.exit(0)

    except Exception as e:
        print("ERROR: config.yml file is not a valid yml file - now exiting!", e)
        sys.exit(0)
