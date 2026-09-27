# USB-ports-controller
A project that focus on controlling external and internal USB ports and show there informations

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
1. Monitor every USB port weither it is an internal or external ones. 
2. Unbind and bind ports by one click.
3. Easy UI to understand and use


## How to use
### First
**Install the libraries used:**

```py
pip install PyQt6 pyudev
```


### Second
**Run the project:**
```py
sudo python3 USBcontroller.py
```
*The project need the sudo permession because it binds and unbinds USB ports*