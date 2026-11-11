# Phonk Hub

App de música para Android y Windows, basada en [SimpMusic](https://github.com/maxrave-dev/SimpMusic) (GPL-3.0).

Este repositorio no guarda una copia de SimpMusic: guarda los cambios de Phonk Hub y GitHub los aplica al compilar.

| Carpeta | Qué hay |
| --- | --- |
| `marca/` | `logo.png` y `nombre.txt`. Cámbialos y la próxima compilación usa el nuevo nombre y logo. |
| `phonk/version.env` | La versión exacta de SimpMusic sobre la que se aplican los cambios. |
| `phonk/app.patch`, `phonk/core.patch` | Los cambios de Phonk Hub. |
| `phonk/preparar.sh`, `phonk/aplicar_marca.py` | Descargan SimpMusic, aplican los cambios y la marca. |
| `.github/workflows/compilar.yml` | Compila el `.apk` y el `.msi` y los publica en **Releases**. |

Cada vez que subes un cambio a `main`, GitHub compila y publica una versión nueva. La app avisa sola cuando hay una.

Licencia: GPL-3.0, igual que SimpMusic.
