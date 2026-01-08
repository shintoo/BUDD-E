# Setup

## L293D Connections

GND should connect to BOTH Pi ground and 4xAA battery pack ground.

| Pi/Mx/Bat | L293D |
| -- | ----- |
| GPIO13   | 1 (EN1)    |
| GPIO4   | 2  (IN1)   |
| M1+   | 3 (OUT1)    |
|    | 4 (0V)    |
| GND   | 5 (0V)    |
| M1-   | 6 (OUT2)    |
| GPIO17   | 7 (IN2)    |
| Battery+   | 8 +Vm    |
| GPIO12   | 9 (EN2)    |
| GPIO24   | 10 (IN3)   |
| M2+   | 11 (OUT3)   |
| GND   | 12 (0V)   |
|    | 13 (0V)   |
| M2-   | 14 (OUT4)   |
| GPIO16    | 15 (IN4)   |
| Pi 5v | 16 (+V) |

[!L293D](https://res.cloudinary.com/rs-designspark-live/image/upload/c_limit,w_420/f_auto/v1/article/learn_arduino_L293D_8cd42ada1b6263da0fa8c8ed760e59682a52846b)


## 240x240 TFT LCD Connections
| Pi | LCD |
| -- | --- |
| 3.3v | VCC |
| GND | GND |
| GPIO11| SCL | 
| GPIO10| SDA |
| GPIO25| DC |
| GPIO8| CS | 
| GPIO27 | RST |
