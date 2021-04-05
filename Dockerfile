FROM python:3.9.2-alpine

RUN pip install docker
RUN pip install discord-webhook
RUN pip install schedule
RUN pip install pyyaml

RUN mkdir /appData
RUN mkdir /backup
RUN mkdir /yaml
RUN mkdir /maintainer

ADD backupServices.py /maintainer/
ADD configInit.py /maintainer/
ADD main.py /maintainer/
ADD util.py /maintainer/
ADD watchtowerService.py /maintainer/

WORKDIR /maintainer/
CMD [ "python", "-u", "main.py" ]