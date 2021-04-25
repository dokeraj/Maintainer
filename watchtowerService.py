import sys
import util


def update(config, dockerClient):
    util.notifyUser(13408299, config, True, descMsg=f"Cleaning up all watchtower images and containers..")

    # remove watchtower container if it exists
    try:
        for container in dockerClient.containers.list(all=True):
            if "containrrr/watchtower" in container.attrs["Config"]["Image"]:
                container.remove(force=True)

        imagesToRemove = []
        for im in dockerClient.images.list():
            if any("containrrr/watchtower" in s for s in im.attrs["RepoTags"]):
                imagesToRemove.append(im.attrs["Id"])

        for imgId in imagesToRemove:
            dockerClient.images.remove(image=imgId, force=True)

    except Exception as e:
        print("Error: couldn't remove watchtower container! This may potentially create duplicate containers", e)

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
