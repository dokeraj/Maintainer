import sys
import util


def update(config, dockerClient):
    # remove watchtower container if it exists
    try:
        watchtower = dockerClient.containers.get("watchtower")
        watchtower.remove()
    except Exception as e:
        None

    util.notifyUser(3387350, config, True, descMsg=f"Please welcome Watchtower service to the main stage..")

    bindVolume = {'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'}}
    watchtowerHook = f"{config.watchtowerUrl}/slack"
    watchtowerEnvironmentVars = {"WATCHTOWER_NOTIFICATIONS": "slack",
                                 "WATCHTOWER_NOTIFICATION_SLACK_HOOK_URL": watchtowerHook}

    try:
        if config.watchtowerUrl is not None:
            dockerClient.containers.run(config.watchtowerImage,
                                        command=["--run-once=true", "--cleanup=true", "--include-stopped=true"],
                                        name="watchtower", volumes=bindVolume,
                                        environment=watchtowerEnvironmentVars)
        else:
            dockerClient.containers.run(config.watchtowerImage,
                                        command=["--run-once=true", "--cleanup=true", "--include-stopped=true"],
                                        name="watchtower", volumes=bindVolume)
    except Exception as e:
        util.notifyUser(14297642, config, True,
                        descMsg=f""""ERROR: Couldn't not run watchtower container! Please check the watchtower's image digest! No images were updated! Run watchtower manually! Now Exiting! {e}""")
        sys.exit(0)
