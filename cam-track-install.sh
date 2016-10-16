#!/bin/bash
# Convenient cam-track cam-track-install.sh script written by Claude Pageau 1-Jul-2016
ver="1.2"
APP_DIR='cam-track'  # Default folder install location

cd ~
if [ -d "$APP_DIR" ] ; then
  STATUS="Upgrade"
  echo "Upgrade cam-track files"
else  
  echo "New cam-track Install"
  STATUS="New Install"
  mkdir -p $APP_DIR
  echo "$APP_DIR Folder Created"
fi 

cd $APP_DIR
INSTALL_PATH=$( pwd )   

# Remember where this script was launched from
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "------------------------------------------------"
echo "  cam-track-Install.sh script ver $ver"
echo "  $STATUS cam-track for Camera movement tracking"
echo "------------------------------------------------"
echo ""
echo "1 - Downloading GitHub Repo files to $INSTALL_PATH"
wget -O cam-track-install.sh -q --show-progress https://raw.github.com/pageauc/rpi-cam-track/master/cam-track-install.sh
if [ $? -ne 0 ] ;  then
  wget -O cam-track-install.sh https://raw.github.com/pageauc/rpi-cam-track/master/cam-track-install.sh
  wget -O cam-track.py https://raw.github.com/pageauc/rpi-cam-track/master/cam-track.py
  wget -O config.py https://raw.github.com/pageauc/rpi-cam-track/master/config.py  
  wget -O Readme.md https://raw.github.com/pageauc/rpi-cam-track/master/Readme.md  
else
  wget -O cam-track.py -q --show-progress https://raw.github.com/pageauc/rpi-cam-track/master/cam-track.py
  wget -O config.py -q --show-progress https://raw.github.com/pageauc/rpi-cam-track/master/config.py  
  wget -O Readme.md -q --show-progress  https://raw.github.com/pageauc/rpi-cam-track/master/Readme.md  
fi
echo "Done Download"
echo "------------------------------------------------"
echo ""
echo "2 - Make required Files Executable"
chmod +x cam-track.py
chmod +x cam-track-install.sh
echo "Done Permissions"
echo "------------------------------------------------"
echo ""
echo "3 - Performing Raspbian System Update"
echo "    This Will Take Some Time ...."
echo ""
sudo apt-get -y update
echo "Done update"
echo "------------------------------------------------"
echo ""
echo "4 - Performing Raspbian System Upgrade"
echo "    This Will Take Some Time ...."
echo ""
sudo apt-get -y upgrade
echo "Done upgrade"
echo "------------------------------------------------"
echo ""
echo "5 - Installing cam-track Dependencies"
sudo apt-get install -y python-opencv python-picamera
echo "Done Dependencies"
cd $DIR
# Check if cam-track-install.sh was launched from cam-track folder
if [ "$DIR" != "$INSTALL_PATH" ]; then
  if [ -e 'cam-track-install.sh' ]; then
    echo "$STATUS Cleanup cam-track-install.sh"
    rm cam-track-install.sh
  fi
fi
echo "-----------------------------------------------"
echo "6 - $STATUS Complete"
echo "-----------------------------------------------"
echo ""
echo "1. Reboot RPI if there are significant Raspbian system updates"
echo "2. Raspberry pi needs a monitor/TV attached to display openCV window"
echo "3. Run cam-track.py with the Raspbian Desktop GUI running"
echo "4. To start open file manager or a Terminal session then change to" 
echo "   rpi-cam-track folder and launch per commands below"
echo ""
echo "   cd ~/rpi-cam-track"
echo "   ./cam-track.py"
echo ""
echo "-----------------------------------------------"
echo "See Readme.md for Further Details"
echo $APP_DIR "Good Luck Claude ..."
echo "Bye"
echo ""