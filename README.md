### Contador: Consulta automatizada al contador online de [edistribucion](https://www.edistribucion.com/es/index.html)

Con este script es posible automatizar la consulta periódica al contador online, ya sea la consulta individual o múltiples contratos.

#### Herramientas necesarias:
- python >3.7 (https://www.python.org/downloads/)
- Firefox (https://www.mozilla.org/en-US/exp/firefox/new/)
- geckodriver (https://github.com/mozilla/geckodriver/releases) [ [como instalar](https://www.guru99.com/gecko-marionette-driver-selenium.html) ]
- contador (este script) (https://github.com/fullonic/contador/archive/master.zip)

#### Como utilizar:
Una vez instalado todo, entramos en la carpeta `contador` y abrimos una ventana de terminal. Y hacemos el siguiente:

`python -m pip install -r requeriments.txt`

Cuando haya concluido la instalación de las dependencias, hay que añadir el DNI y la contraseña. Para tal, abrimos el archivo `users.json` y indroducimos nuestros dados.
Por ejemplo:
```json
{
  "usuarios": [
    {
      "username": "dni1",
      "password": "pass1"
    }
  ]
}


```
Para añadir mas cuentas, es fácil como repetir lso campos "username" y "password":
```json 
{
  "username": "dni2",
  "password": "pass2"
}
```
Resultando en:
```
{
  "usuarios": [
    {
      "username": "dni1",
      "password": "pass1"
    },  // <- Todos los usuario@s tienen que estar separados por una coma y entre {}
    {
      "username": "dni2",
      "password": "pass2"
    }
  ]
}
```

Para activar el script hacemos:
`python auto_run.py`

Caso tengamos varios usuario@s, para acelerar el proceso hacemos:

`python auto_run.py multiple`  # Isto hara el script hacer varias consultas en _paralelo_

#### Configuraciones
Para cambiar el intervalo de tiempo entre una consulta y otra, abrimos el archivo `config.json`.
En el campo `"script": {"frecuencia [minutos]": 3` podemos ajustar la frecuencia de las consultas.

Por defecto, la automatizacion del browser es oculta, pero alterando el valor `"headless": true` para `false`, esto hara que el processo sea visible.
