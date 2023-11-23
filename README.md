# tasmota_heating

Microservices approach to controlling the temperature in a garden office. 
A heater is connected to a wifi plug, and separately an esp8266 module is collecting temperature data and making it available to be scraped by prometheus.
This project has a service which takes the setpoints and active status and either turns the plug to the heater on or off depending on the inputs. 
There is a separate webapp which allows for scraping of the heater status via prometheus and control of the setpoints, active status etc
