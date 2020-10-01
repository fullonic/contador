### Contador: Consulta automatizada al contador online de [edistribucion](https://www.edistribucion.com/es/index.html)

Con este script es posible automatizar la consulta periódica al contador online, ya sea la consulta individual o la de múltiples contratos.

#### Herramientas necesarias:

- python >3.7 (https://www.python.org/downloads/)
- Firefox (https://www.mozilla.org/en-US/exp/firefox/new/)
- geckodriver (https://github.com/mozilla/geckodriver/releases) [ [como instalar](https://www.guru99.com/gecko-marionette-driver-selenium.html) ]
- contador (este script) (https://github.com/fullonic/contador/archive/master.zip)

#### Como utilizar en plataforma tipo Raspberry [recomendado]:

Una vez dentro de la carpeta `contador`, abrir una terminal y ejecutar el comando:

```bash
>> ./rpi_install.sh
```

Que hace el script:

1 - Hace una actualización del sistema


2 - Download y instalación de las dependencias necesarias: Firefox, Firefox driver y SQLite3 (base de datos)

3 - Crea un nuevo script que es el punto de partir para iniciar la aplicación (start_app.sh)

4 - Añade la aplicación al arranque del sistema \*

5 - Instala todos las librarias de python necesarias

Una vez terminada el proceso, para empezar la aplicación apenas hay que ejecutar el comando:

```bash
>> ./start_app.sh
```
* La aplicación es añadida el arranque del sistema para garantir que empieza automáticamente en caso de una falla energética


#### Como utilizar plataforma "Desktop" [apenas para testar]:

Una vez instalado todo, entramos en la carpeta `contador` y abrimos una ventana de terminal. Y hacemos el siguiente:

- En algunas plataformas utilizar `python3` en lugar de `python`

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

Para añadir mas cuentas, es fácil como repetir los campos "username" y "password":

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

Caso tengamos varios usuario@s, para acelerar el proceso es recomendado:

`python auto_run.py multiple`

\*Isto hara el script hacer varias consultas en _paralelo_

#### Configuraciones

Para cambiar el intervalo de tiempo entre una consulta y otra, abrimos el archivo `config.json`.
En el campo `"script": {"frecuencia [minutos]": 3` podemos ajustar la frecuencia de las consultas.

Por defecto, la automatizacion del browser es oculta, pero alterando el valor del campo `"headless"` de `true` para `false`, esto hara que el processo sea visible. Sin embargo es recomendado que el valor sea `false` para envitar el abrir y cerrar de ventadas.

#### Resultados

Los resultados seran guardados en el archivo `results.json` en el formato:

```json
{
  "DNI": [
    ["27-07-2020_19:30:33", 0.14, 4.24, 3.3],
    ["27-07-2020_19:35:28", 0.12, 3.64, 3.3]
  ]
}
```

Cada secuencia `["27-07-2020_19:30:33", 0.14, 4.24, 3.3]` repesenta una consulta donde los valores son lo seguientes:

1.  Data
2.  Consumo instantáneo (kW)
3.  Porcentaje (%)
4.  Potencia contratada (kW)
