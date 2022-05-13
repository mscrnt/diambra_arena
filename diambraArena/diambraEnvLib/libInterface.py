import sys, platform, os
from pathlib import Path
import numpy as np

import threading
from diambraArena.diambraEnvLib.pipe import Pipe, DataPipe
from diambraArena.utils.splashScreen import DIAMBRASplashScreen
import time

def diambraApp(diambraAppPath, pipesPath, envId, romsPath, render):
    print("Args = ", diambraAppPath, pipesPath, envId, romsPath, render)

    if diambraAppPath != "":
        command = '{} --pipesPath {} --envId {}'.format(diambraAppPath, pipesPath, envId)
    else:
        dockerRomsFolder = "/opt/diambraArena/roms"
        dockerPipesFolder = "/tmp/"
        dockerImageName = "diambra/diambra-app:main"
        dockerContainerName = "container"+envId
        romsVol = '--mount src={},target="{}",type=bind '.format(romsPath, dockerRomsFolder)
        homeFolder = os.getenv("HOME")
        if render:
            x11exec = os.path.join(pipesPath, "x11docker")
            command  = '{} --cap-default --hostipc --network=host --name={}'.format(x11exec, dockerContainerName)
            command += ' --wm=host --pulseaudio --size=1024x600 -- --privileged'
            command += ' {} --mount src="{}",target="{}",type=bind'.format(romsVol, pipesPath, dockerPipesFolder)
            command += ' -e HOME=/tmp/ --mount src="{}/.diambraCred",target="/tmp/.diambraCred",type=bind'.format(homeFolder)
            command += ' -- {} &>/dev/null & sleep 4s;'.format(dockerImageName)
            command += ' docker exec -u $(id -u) --privileged -it {}'.format(dockerContainerName)
            command += ' sh -c "set -m; cd /opt/diambraArena/ &&'
            command += ' ./diambraApp --pipesPath {} --envId {}";'.format(dockerPipesFolder, envId)
            command += ' pkill -f "bash {}*"'.format(x11exec)
        else:
            command  = 'docker run --user $(id -u) -it --rm --privileged {}'.format(romsVol)
            command += ' --mount src="{}",target="{}",type=bind'.format(pipesPath, dockerPipesFolder)
            command += ' -e HOME=/tmp/ --mount src="{}/.diambraCred",target="/tmp/.diambraCred",type=bind'.format(homeFolder)
            command += ' --name {} {}'.format(dockerContainerName, dockerImageName)
            command += ' sh -c "cd /opt/diambraArena/ &&'
            command += ' ./diambraApp --pipesPath {} --envId {}"'.format(dockerPipesFolder, envId)

    print("Command = ", command)
    os.system(command)

# DIAMBRA Env Gym
class diambraArenaLib:
    """Diambra Environment gym interface"""

    def __init__(self, envSettings):

        self.pipesPath = os.path.dirname(os.path.abspath(__file__))

        self.envSettings = envSettings

        # Splash Screen
        DIAMBRASplashScreen()

        # Create pipes
        self.writePipe = Pipe(self.envSettings["envId"], "input", "w", self.envSettings["pipesPath"])
        self.readPipe = DataPipe(self.envSettings["envId"], "output", "r", self.envSettings["pipesPath"])

        # Open pipes
        self.writePipe.open()
        self.readPipe.open()

        # Send environment settings
        envSettingsString = self.envSettingsToString()
        self.writePipe.sendEnvSettings(envSettingsString)

    # Transforming env kwargs to string
    def envSettingsToString(self):

        maxCharToSelect = 3
        sep = ","
        endChar = "+"

        output = ""

        output += "envId"+            sep+"2"+sep + self.envSettings["envId"] + sep
        output += "gameId"+           sep+"2"+sep + self.envSettings["gameId"] + sep
        output += "continueGame"+     sep+"3"+sep + str(self.envSettings["continueGame"]) + sep
        output += "showFinal"+        sep+"0"+sep + str(int(self.envSettings["showFinal"])) + sep
        output += "stepRatio"+        sep+"1"+sep + str(self.envSettings["stepRatio"]) + sep
        output += "player"+           sep+"2"+sep + self.envSettings["player"] + sep
        output += "difficulty"+       sep+"1"+sep + str(self.envSettings["difficulty"]) + sep
        output += "character1"+       sep+"2"+sep + self.envSettings["characters"][0][0] + sep
        output += "character2"+       sep+"2"+sep + self.envSettings["characters"][1][0] + sep
        for iChar in range(1, maxCharToSelect):
            output += "character1_{}".format(iChar+1)+     sep+"2"+sep + self.envSettings["characters"][0][iChar] + sep
            output += "character2_{}".format(iChar+1)+     sep+"2"+sep + self.envSettings["characters"][1][iChar] + sep
        output += "charOutfits1"+     sep+"1"+sep + str(self.envSettings["charOutfits"][0]) + sep
        output += "charOutfits2"+     sep+"1"+sep + str(self.envSettings["charOutfits"][1]) + sep

        # SFIII Specific
        output += "superArt1"+        sep+"1"+sep + str(self.envSettings["superArt"][0]) + sep
        output += "superArt2"+        sep+"1"+sep + str(self.envSettings["superArt"][1]) + sep
        # UMK3 Specific
        output += "tower"+            sep+"1"+sep + str(self.envSettings["tower"]) + sep
        # KOF Specific
        output += "fightingStyle1"+   sep+"1"+sep + str(self.envSettings["fightingStyle"][0]) + sep
        output += "fightingStyle2"+   sep+"1"+sep + str(self.envSettings["fightingStyle"][1]) + sep
        for idx in range(2):
            output += "ultimateStyleDash"+str(idx+1)+  sep+"1"+sep + str(self.envSettings["ultimateStyle"][idx][0]) + sep
            output += "ultimateStyleEvade"+str(idx+1)+ sep+"1"+sep + str(self.envSettings["ultimateStyle"][idx][1]) + sep
            output += "ultimateStyleBar"+str(idx+1)+   sep+"1"+sep + str(self.envSettings["ultimateStyle"][idx][2]) + sep

        output += "disableKeyboard"+  sep+"0"+sep + str(int(self.envSettings["disableKeyboard"])) + sep
        output += "disableJoystick"+  sep+"0"+sep + str(int(self.envSettings["disableJoystick"])) + sep
        output += "rank"+             sep+"1"+sep + str(self.envSettings["rank"]) + sep
        output += "recordConfigFile"+ sep+"2"+sep + self.envSettings["recordConfigFile"] + sep

        output += endChar

        return output

    # Set frame size
    def setFrameSize(self, hwcDim):
        self.readPipe.setFrameSize(hwcDim)

    # Get Env Info
    def readEnvInfo(self):
        return self.readPipe.readEnvInfo()

    # Get Env Int Data Vars List
    def readEnvIntDataVarsList(self):
        self.readPipe.readEnvIntDataVarsList()

    # Reset the environment
    def reset(self):
        self.writePipe.sendComm(1);
        return self.readPipe.readResetData()

    # Step the environment
    def step(self, movP1=0, attP1=0, movP2=0, attP2=0):
        self.writePipe.sendComm(0, movP1, attP1, movP2, attP2);
        return self.readPipe.readStepData()

    # Closing DIAMBRA Arena
    def close(self):
        self.writePipe.sendComm(2)

        # Close pipes
        self.writePipe.close()
        self.readPipe.close()

        self.diambraEnvThread.join(timeout=30)
        if self.diambraEnvThread.isAlive():
            error = "Failed to close DIAMBRA Env process"
            raise RuntimeError(error)
