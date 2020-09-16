#!/bin/bash
echo "Actualizando sistema..."
sudo apt update && sudo apt install
echo "Instalando Firefox"
sudo apt install firefox-esr

driver=geckodriver-v0.23.0-arm7hf.tar.gz
if [ -f $driver ] ; then
    echo ""
else
    echo "Bajando gecko driver"
    wget https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-arm7hf.tar.gz

fi
echo "Instalando geckodriver"
tar -xf $driver
sudo chmod +x ./geckodriver
sudo mv ./geckodriver /usr/local/bin/
rm $driver

sudo chmod +x ./start_app.sh
echo "Setup python"
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
echo "Para empenzar a utilizar el 'Contador' haga en este terminal:"
echo "python start_ui.py"
echo ""
echo "Para mas info visite:"
echo "https://github.com/fullonic/contador/blob/master/README.md"
