# Kabernetes

- Importante hacer: `sudo chmod 666 /var/run/docker.sock` antes de correr la app, sino no va a tener permisos para levantar contenedores.

### How to run

```
$ python -m venv my-project-env
$ source my-project-env/bin/activate
$ pip install -r requirements.txt
$ python main.py
```

### Como terminar la aplicacion

Para terminar la aplicacion primero debemos terminar el cliente de docker actual con `DELETE /client`. De esta forma, todos los contenedores que esten siendo ejecutados por la aplicacion serán frenados y eliminados.

De no hacerlo, habrá que frenar y eliminar los contenedores manualmente.


### Endpoints

1. GET "/client"

Retorna las estadisticas del cliente de docker actual:

```
{
    "status", // Estado del cliente (STARTING, READY, STOPPING, BUSY, DEAD)
    "image" // Imagen que se va a utilizar para instanciar los contenedores 
    "cpu_target" // Porcentaje de cpu promedio que se quiere tener como maximo en el sistema 
    "constants": { // Default 0
        "kp": // Constante proporcional 
        "kd": // Constante derivativa
        "ki": // Constante integral
    },
    "error": // Medicion actual del error del sistema
    "avg_cpu_usage": // Medicion del uso promedio de cpu actual
    "containers": // Cantidad de contenedores activos
    "cpu_usage": // Porcentaje de cpu utilizado por cada contenedor (una lista)
}
```

Retorna un error si no hay un cliente en ejecucion.

2. POST "/client"

Instancia un nuevo cliente de docker.

Recibe por body un JSON con el siguiente formato:
```
{
    "image",
    "cpu_target",
    "constants": {
        "kp",
        "kd",
        "ki"
    }
}
```

De faltar alguno de los atributos ("image", "cpu_target", "constants")

Tambien fallará si ya existe una instancia activa.

3. PATCH "/client"

Actualiza los valores de las constantes del controlador de una instancia activa.

Recibe por body un JSON con el siguiente formato:
```
{
    "kp",
    "kd",
    "ki"
}
```

Si no se le invia ningun body, se asumiran todas las constantes como 0. Lo mismo sucede si se omite alguna de las constantes.

Retornará un error si no existe una instancia activa.

4. DELETE "/client"

Borra la instancia del cliente de docker actual, dando lugar para la creacion de una nueva con `POST "/client"`.


5. POST "/client/containers"

Da de alta una dada cantidad de contenedores nuevos en el sistema.

Recibe por body un JSON con el siguiente formato:
```
{
    "amount"  // Indica la cantidad de contenedores a dar de alta
}
```


6. DELETE "/client/containers"

Da de baja una dada cantidad de contenedores del sistema. 
El sistema nunca podrá tener menos de 1 contenedor corriendo.

Recibe por body un JSON con el siguiente formato:
```
{
    "amount"  // Indica la cantidad de contenedores a dar de baja
}
```