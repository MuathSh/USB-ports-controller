# USB-ports-controller
A cross-platform project for monitoring and controlling hardware devices and ports on Linux, Windows, and macOS.

## Screanshots:
**some of the UI used and how it works:**

Main UI:

<img src="./images/1.png" width="450">

chosing the device:

<img src="./images/2.png" width="450">

unbinding device:

<img src="./images/3.png" width="450">

rebinding device:

<img src="./images/4.png" width="450">


## Features

1. Detect connected devices and ports.
2. View device and port information.
3. Enable and disable supported devices and ports.
4. Support multiple device buses and types.
5. Cross-platform backends for Linux, Windows, and macOS.
6. Simple graphical interface.


## How to use

### Install dependencies

```bash
pip install PyQt6
```

On Linux:

```bash
pip install pyudev
```

### Run

#### Linux

```bash
sudo python3 USBcontroller.py
```

Root privileges are required for operations such as binding and unbinding device drivers.

#### macOS

```bash
python3 USBcontroller.py
```

Some device-control operations may require elevated privileges.

#### Windows

```powershell
python USBcontroller.py
```

Run the terminal or application as Administrator when using device enable/disable operations.

*The project need the sudo permession because it binds and unbinds USB ports*