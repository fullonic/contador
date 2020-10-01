#!/bin/bash
echo "Actualizando sistema..."
sudo apt update && sudo apt install

echo "Instalando SQLite3"
sudo apt-get install sqlite3

echo "Instalando Firefox"
sudo apt install firefox-esr

echo "Instalando geckodriver"
driver=geckodriver-v0.23.0-arm7hf.tar.gz
if [ -f $driver ] ; then
    echo ""
else
    echo "Bajando gecko driver"
    wget https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-arm7hf.tar.gz

fi
tar -xf $driver
sudo chmod +x ./geckodriver
sudo mv ./geckodriver /usr/local/bin/
rm $driver

# Create start up bash script
base_dir=$(pwd)
echo "#!/bin/bash" > start_app.sh
echo "cd $base_dir && venv/bin/python3 start_ui.py" >> start_app.sh
sudo chmod +x ./start_app.sh

# Add startup script to cron

#write out current crontab
crontab -l > cron_task
#echo new cron into cron file
echo " Add cron task @reboot $basedir/start_app.sh"
echo "@reboot $base_dir/start_app.sh" >> cron_task
#install new cron file
crontab cron_task
rm cron_task

echo "Setup Python"
if [ ! -d "venv" ]; then
    echo --------------------
    echo Creating virtualenv
    echo --------------------
    python3 -m venv venv
fi
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Installacion completa."
echo "Para empenzar a utilizar el 'Contador' en este terminal enter:"
echo "./start_app.sh"
echo ""
echo "Para mas info visite:"
echo "https://github.com/fullonic/contador/blob/master/README.md"
