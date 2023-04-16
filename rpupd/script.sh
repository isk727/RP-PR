sudo rm play.html
sudo rm script.py
sudo rm script.js
sudo rm style.css

wget https://raw.githubusercontent.com/isk727/RP-PR/main/0.9.9c/play.html
wget https://raw.githubusercontent.com/isk727/RP-PR/main/0.9.9c/script.py
wget https://raw.githubusercontent.com/isk727/RP-PR/main/0.9.9c/script.js
wget https://raw.githubusercontent.com/isk727/RP-PR/main/0.9.9c/style.css

sudo chmod 755 play.html
sudo chmod 755 script.py
sudo chmod 755 script.js
sudo chmod 755 style.css

sudo mv play.html /usr/share/webiopi/htdocs/.
sudo mv script.py /usr/share/webiopi/python/.
sudo mv script.js /usr/share/webiopi/htdocs/js/.
sudo mv style.css /usr/share/webiopi/htdocs/css/.

sudo reboot
