## General overview
This container is useful in the following cases :
* Your favourite downloader(s) (sickrage, couchpotato, sonarr, deluge...) runs in a docker container(s)
* You want to use sickbeard_mp4_automator to process files downloaded by those containers or to add conversion jobs manually.
In order to do this, ffmpeg and sickbeard_mp4_automator need to be deployed in each container, which is not maintainable in the long run.

This container provides 2 things :
* A server which will accept conversion jobs based on settings provided.
* A watchfolder, that will convert any mkv files put in there. The watchfolder is configured through the environment variable. Any mkv added to the folder will be transformed into an mp4 file using the defaults in /config/autoProcess.ini. I'll probably remove that once it's easier to add manual jobs to the server.


This container pulls and builds the latest stable version of ffmpeg and dependencies, from git repos when available and relevant. This part is *heavily* inspired by [jrottenberg's docker files on ffmpeg](https://github.com/jrottenberg/ffmpeg).
The container will also pull [sickbeard_mp4_automator from mdhiggins](https://github.com/mdhiggins/sickbeard_mp4_automator), with the necessary python dependencies.

The container exposes the following volumes :
* /config, which contains autoProcess.ini, the main configuration file for sickbeard_mp4_automator
* the watchfolder which can be set to anything

## Usage

docker run \
-e WATCHFOLDER=/PATH-TO-WATCHFOLDER \ # where the watchfolder will be created
-v PATH-TO-CONFIG-DIR:/config \ #where autoProcess.ini goes
-v PATH-TO-DOWNLOADS-DIR:/videos \ # for example, in case you want to move the files there after they are processed
-d --name automator phtagn/docker_mp4_automator