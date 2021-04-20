const process = require("process");
const os = require('os')

var enrollmentStatusRegex = /^(vw-connect\.\d+\.[A-Z0-9]+)\.general\.enrollmentStatus$/;

function findCars(){
    var cars = [];
    var enrollmentStatuses = getIdByName('enrollmentStatus', true);
    if(enrollmentStatuses){
        for (enrollmentStatus of enrollmentStatuses){
            if (getState(enrollmentStatus).val == 'COMPLETED'){
                const match = enrollmentStatus.match(enrollmentStatusRegex);
                var car = match[1];
                cars.push(car)
            }
        }
    }
    return cars;
}

function updateConfig(yahkainstance){
    var config = getObject('system.adapter.' + yahkainstance);
    if (! config){
        console.log('Adapter: '+ yahkainstance + ' not found!',"error");
        return;
    }

    var bridge = null;
    if(config.native){
        if(config.native.bridge){
            bridge = config.native.bridge;
            console.log('Homekit config was already existing, updating config: '+ yahkainstance,"debug");
        }
        else{
            bridge = new Object();
            config.native.bridge = bridge;
            console.log('Homekit config was not existing, creating config: '+ yahkainstance,"debug");
        }
    }
    else{
        config.native = new Object();
        bridge = new Object();
        config.native.bridge = bridge;
        console.log('Homekit config was not existing, creating config: '+ yahkainstance,"debug");
    }

    var devices = null;

    if(config.native.bridge.devices){
        devices = config.native.bridge.devices
    }
    else{
        devices = new Array();
        config.native.bridge.devices = devices;
    }

    var cars = findCars()
    console.log('Found the following cars: '+ cars,"debug");
    cars.forEach(function(car){
        //Device Climatization
        if(existsState(car + '.status.climatisationStatus.climatisationState')
                && existsState(car + '.status.climatisationSettings.targetTemperature_C')
                && existsState(car + '.remote.climatisation')
                && existsState(car + '.general.nickname')
                && existsState(car + '.general.vin')){
            var deviceName = getState(car + '.general.nickname').val + ' Climate';
            var device = null;
            for(existingDevice of devices){
                if (existingDevice["name"] == deviceName){
                    console.log('Car '+car+' has climatisationState, climatization device already exsisting, updating it',"debug");
                    device = existingDevice;
                    break;
                }
            }
            if(!device){
                console.log('Car '+car+' has climatisationState, creating climatization device',"debug");
                device = new Map();
                devices.push(device)
            }
            device["configType"]= "customdevice";
            device["manufacturer"] = "unknown";
            device["model"] = "unknown";
            device["name"] = deviceName;
            device["serial"] = getState(car + '.general.vin').val;
            device["firmware"] = "";
            device["enabled"] = true;
            device["category"] = "9";

            device["services"] = new Array();

            //Service Thermostat
            var service = new Map();
            var climateServiceName = deviceName
            service["name"] = climateServiceName;
            service["subType"] = "";
            service["type"] = "Thermostat";
            var characteristics = new Array();

            var characteristic = new Map();
            characteristic["name"] = "CurrentHeatingCoolingState";
            characteristic["enabled"] = true;
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".status.climatisationStatus.climatisationState";
            characteristic["conversionFunction"] = "script";
            characteristic["conversionParameters"] = new Map();
            characteristic["conversionParameters"]["toHomeKit"] = "if(value=='off')\n  return 0;\nif(value=='heating')\n  return 1;\nif(value=='cooling')\n  return 2;\n\nreturn 0;";
            characteristics.push(characteristic);

            var characteristic = new Map();
            characteristic["name"] = "TargetTemperature";
            characteristic["enabled"] = true;
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".status.climatisationSettings.targetTemperature_C";
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            var characteristic = new Map();
            characteristic["name"] = "TemperatureDisplayUnits";
            characteristic["enabled"] = true;
            characteristic["inOutFunction"] = "const";
            characteristic["inOutParameters"] = 0;
            characteristics.push(characteristic);

            var characteristic = new Map();
            characteristic["name"] = "TargetHeatingCoolingState";
            characteristic["enabled"] = true;
            characteristic["inOutFunction"] = "ioBroker.MultiState";
            characteristic["inOutParameters"] = new Array();
            characteristic["inOutParameters"][0] = new Map();
            characteristic["inOutParameters"][0]["readState"] = car + ".status.climatisationStatus.climatisationState";
            characteristic["inOutParameters"][0]["writeState"] = car + ".remote.climatisation";
            characteristic["conversionFunction"] = "script";
            characteristic["conversionParameters"] = new Map();
            characteristic["conversionParameters"]["toHomeKit"] = "if(value=='off')\n  return 0;\nif(value=='heating')\n  return 1;\nif(value=='cooling')\n  return 2;\n\nreturn 3;";
            characteristic["conversionParameters"]["toIOBroker"] = "if(value==0)\n  return false;\nelse if(value==1)\n  return true;\nelse if(value==2)\n  return true;\nelse\n  return false;";
            characteristics.push(characteristic);

            if(existsState(car + '.climatisationStatus.remainingClimatisationTime_min')){
                var characteristic = new Map();
                characteristic["name"] = "RemainingDuration";
                characteristic["enabled"] = true;
                characteristic["customCharacteristic"] =  true,
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".status.climatisationStatus.remainingClimatisationTime_min"
                characteristic["conversionFunction"] = "script";
                characteristic["conversionParameters"] = new Map();
                characteristic["conversionParameters"]["toHomeKit"] = "return ((value * 60) + 1)";
                characteristics.push(characteristic);
            }

            //Custom characteristics in Thermostat Service
            var characteristic = new Map();
            characteristic["name"] = "AdministratorOnlyAccess";
            characteristic["enabled"] = true;
            characteristic["customCharacteristic"] =  true,
            characteristic["inOutFunction"] = "const";
            characteristic["inOutParameters"] = "true"
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            var characteristic = new Map();
            characteristic["name"] = "StatusActive";
            characteristic["enabled"] = true;
            characteristic["customCharacteristic"] =  true,
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = "vw-connect.0.info.connection" //Todo determine adapter instance
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            service["characteristics"] = characteristics;

            device["services"].push(service)

            //Service AccessoryInformation
            var service = new Map();
            service["name"] = climateServiceName + ' AccessoryInformation';
            service["subType"] = "";
            service["type"] = "AccessoryInformation";
            service["linkTo"]= climateServiceName;
            var characteristics = new Array();

            if(existsState(car + '.general.model')){
                var characteristic = new Map();
                characteristic["name"] = "Model";
                characteristic["enabled"] = true;
                characteristic["customCharacteristic"] =  true,
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".general.model"
                characteristic["conversionFunction"] = "passthrough";
                characteristics.push(characteristic);
            }

            var characteristic = new Map();
            characteristic["name"] = "Name";
            characteristic["enabled"] = true;
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".general.nickname"
            characteristic["conversionFunction"] = "script";
            characteristic["conversionParameters"] = new Map();
            characteristic["conversionParameters"]["toHomeKit"] = "return value + ' Climate';";
            characteristics.push(characteristic);

            var characteristic = new Map();
            characteristic["name"] = "SerialNumber";
            characteristic["enabled"] = true;
            characteristic["customCharacteristic"] =  true,
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".general.vin"
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            service["characteristics"] = characteristics;

            device["services"].push(service)
        }
        //Device Charging
        if(existsState(car + '.status.chargingStatus.chargingState')
                && existsState(car + '.remote.charging')
                && existsState(car + '.general.nickname')
                && existsState(car + '.general.vin')){
            var deviceName = getState(car + '.general.nickname').val + ' Charging';
            var device = null;
            for(existingDevice of devices){
                if (existingDevice["name"] == deviceName){
                    console.log('Car '+car+' has chargingState, charging device already exsisting, updating it',"debug");
                    device = existingDevice;
                    break;
                }
            }
            if(!device){
                console.log('Car '+car+' has chargingState, creating charging device',"debug");
                device = new Map();
                devices.push(device)
            }
            device["configType"]= "customdevice";
            device["manufacturer"] = "unknown";
            device["model"] = "unknown";
            device["name"] = deviceName;
            device["serial"] = getState(car + '.general.vin').val;
            device["firmware"] = "";
            device["enabled"] = true;
            device["category"] = "7";

            device["services"] = new Array();

            // Outlet Service
            var service = new Map();
            var chargingServiceName = deviceName;
            service["name"] = chargingServiceName;
            service["subType"] = "";
            service["type"] = "Outlet";
            var characteristics = new Array();

            if(existsState(car + '.status.plugStatus.plugConnectionState')){
                var characteristic = new Map();
                characteristic["name"] = "OutletInUse";
                characteristic["enabled"] = true;
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".status.plugStatus.plugConnectionState"
                characteristic["conversionFunction"] = "script";
                characteristic["conversionParameters"] = new Map();
                characteristic["conversionParameters"]["toHomeKit"] = "if (value == \"connected\")\n  return true;\nelse\n  return false;";
                characteristics.push(characteristic);
            }

            var characteristic = new Map();
            characteristic["name"] = "On";
            characteristic["enabled"] = true;
            characteristic["inOutFunction"] = "ioBroker.MultiState";
            characteristic["inOutParameters"] = new Array();
            characteristic["inOutParameters"][0] = new Map();
            characteristic["inOutParameters"][0]["readState"] = car + ".status.chargingStatus.chargingState";
            characteristic["inOutParameters"][0]["writeState"] = car + ".remote.charging";
            characteristic["conversionFunction"] = "script";
            characteristic["conversionParameters"] = new Map();
            characteristic["conversionParameters"]["toHomeKit"] = "if(value == 'charging')\n  return true;\nreturn false;";
            characteristic["conversionParameters"]["toIOBroker"] = "return value;";
            characteristics.push(characteristic);

            if(existsState(car + '.status.chargingStatus.remainingChargingTimeToComplete_min')){
                var characteristic = new Map();
                characteristic["name"] = "RemainingDuration";
                characteristic["enabled"] = true;
                characteristic["customCharacteristic"] =  true,
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".status.chargingStatus.remainingChargingTimeToComplete_min"
                characteristic["conversionFunction"] = "script";
                characteristic["conversionParameters"] = new Map();
                characteristic["conversionParameters"]["toHomeKit"] = "return ((value * 60) + 1)";
                characteristics.push(characteristic);
            }

            //Custom Characteristics (not in service)

            if(existsState(car + '.status.chargingStatus.chargePower_kW')){
                var characteristic = new Map();
                characteristic["name"] = "Community: Watts";
                characteristic["enabled"] = true;
                characteristic["customCharacteristic"] =  true,
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".status.chargingStatus.chargePower_kW"
                characteristic["conversionFunction"] = "script";
                characteristic["conversionParameters"] = new Map();
                characteristic["conversionParameters"]["toHomeKit"] = "return value * 1000";
                characteristics.push(characteristic);
            }

            var characteristic = new Map();
            characteristic["name"] = "AdministratorOnlyAccess";
            characteristic["enabled"] = true;
            characteristic["customCharacteristic"] =  true,
            characteristic["inOutFunction"] = "const";
            characteristic["inOutParameters"] = "true"
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            var characteristic = new Map();
            characteristic["name"] = "StatusActive";
            characteristic["enabled"] = true;
            characteristic["customCharacteristic"] =  true,
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = "vw-connect.0.info.connection" //Todo determine adapter instance
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            service["characteristics"] = characteristics;
            device["services"].push(service)

            //Service BatteryService
            if(existsState(car + '.status.batteryStatus.currentSOC_pct')
                    && existsState(car + '.status.chargingStatus.chargingState')){
                
                var service = new Map();
                service["name"] = chargingServiceName + ' Battery';
                service["subType"] = "";
                service["type"] = "BatteryService";
                service["linkTo"] = chargingServiceName;
                var characteristics = new Array();

                var characteristic = new Map();
                characteristic["name"] = "BatteryLevel";
                characteristic["enabled"] = true;
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".status.batteryStatus.currentSOC_pct"
                characteristic["conversionFunction"] = "passthrough";
                characteristics.push(characteristic);

                var characteristic = new Map();
                characteristic["name"] = "ChargingState";
                characteristic["enabled"] = true;
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".status.chargingStatus.chargingState"
                characteristic["conversionFunction"] = "script";
                characteristic["conversionParameters"] = new Map();
                characteristic["conversionParameters"]["toHomeKit"] = "if(value=='readyForCharging')\n  return 0;\nelse if(value=='charging')\n  return 1;\nreturn 2;";
                characteristics.push(characteristic);

                var characteristic = new Map();
                characteristic["name"] = "StatusLowBattery";
                characteristic["enabled"] = true;
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".status.batteryStatus.currentSOC_pct"
                characteristic["conversionFunction"] = "script";
                characteristic["conversionParameters"] = new Map();
                characteristic["conversionParameters"]["toHomeKit"] = "if(value<10)\n  return 1;\nelse\n  return 0;";
                characteristics.push(characteristic);

                service["characteristics"] = characteristics;

                device["services"].push(service)
            }

            //Service AccessoryInformation
            var service = new Map();
            service["name"] = chargingServiceName + ' AccessoryInformation';
            service["subType"] = "";
            service["type"] = "AccessoryInformation";
            service["linkTo"]= chargingServiceName;
            var characteristics = new Array();

            if(existsState(car + '.general.model')){
                var characteristic = new Map();
                characteristic["name"] = "Model";
                characteristic["enabled"] = true;
                characteristic["customCharacteristic"] =  true,
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".general.model"
                characteristic["conversionFunction"] = "passthrough";
                characteristics.push(characteristic);
            }

            var characteristic = new Map();
            characteristic["name"] = "Name";
            characteristic["enabled"] = true;
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".general.nickname"
            characteristic["conversionFunction"] = "script";
            characteristic["conversionParameters"] = new Map();
            characteristic["conversionParameters"]["toHomeKit"] = "return value + ' Charging';";
            characteristics.push(characteristic);

            var characteristic = new Map();
            characteristic["name"] = "SerialNumber";
            characteristic["enabled"] = true;
            characteristic["customCharacteristic"] =  true,
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".general.vin"
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            service["characteristics"] = characteristics;

            device["services"].push(service)
        }

        //Device Battery
        if(existsState(car + '.status.batteryStatus.currentSOC_pct')
                && existsState(car + '.general.nickname')
                && existsState(car + '.general.vin')){
            var deviceName = getState(car + '.general.nickname').val + ' Battery';
            var device = null;
            for(existingDevice of devices){
                if (existingDevice["name"] == deviceName){
                    console.log('Car '+car+' has batteryStatus, battery device already exsisting, updating it',"debug");
                    device = existingDevice;
                    break;
                }
            }
            if(!device){
                console.log('Car '+car+' has batteryStatus, creating battery device',"debug");
                device = new Map();
                devices.push(device)
            }
            device["configType"]= "customdevice";
            device["manufacturer"] = "unknown";
            device["model"] = "unknown";
            device["name"] = deviceName;
            device["serial"] = getState(car + '.general.vin').val;
            device["firmware"] = "";
            device["enabled"] = true;
            device["category"] = "1";

            device["services"] = new Array();

            //Service BatteryService
            var service = new Map();
            var batteryServiceName = deviceName;
            service["name"] = batteryServiceName;
            service["subType"] = "";
            service["type"] = "BatteryService";
            var characteristics = new Array();

            var characteristic = new Map();
            characteristic["name"] = "BatteryLevel";
            characteristic["enabled"] = true;
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".status.batteryStatus.currentSOC_pct"
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            if(existsState(car + '.status.chargingStatus.chargingState')){
                var characteristic = new Map();
                characteristic["name"] = "ChargingState";
                characteristic["enabled"] = true;
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".status.chargingStatus.chargingState"
                characteristic["conversionFunction"] = "script";
                characteristic["conversionParameters"] = new Map();
                characteristic["conversionParameters"]["toHomeKit"] = "if(value=='readyForCharging')\n  return 0;\nelse if(value=='charging')\n  return 1;\nreturn 2;";
                characteristics.push(characteristic);
            }

            var characteristic = new Map();
            characteristic["name"] = "StatusLowBattery";
            characteristic["enabled"] = true;
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".status.batteryStatus.currentSOC_pct"
            characteristic["conversionFunction"] = "script";
            characteristic["conversionParameters"] = new Map();
            characteristic["conversionParameters"]["toHomeKit"] = "if(value<10)\n  return 1;\nelse\n  return 0;";
            characteristics.push(characteristic);

            var characteristic = new Map();
            characteristic["name"] = "StatusActive";
            characteristic["enabled"] = true;
            characteristic["customCharacteristic"] =  true,
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = "vw-connect.0.info.connection" //Todo determine adapter instance
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            service["characteristics"] = characteristics;

            device["services"].push(service)

            //Service AccessoryInformation
            var service = new Map();
            service["name"] = batteryServiceName + ' AccessoryInformation';
            service["subType"] = "";
            service["type"] = "AccessoryInformation";
            service["linkTo"]= batteryServiceName;
            var characteristics = new Array();

            if(existsState(car + '.general.model')){
                var characteristic = new Map();
                characteristic["name"] = "Model";
                characteristic["enabled"] = true;
                characteristic["customCharacteristic"] =  true,
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".general.model"
                characteristic["conversionFunction"] = "passthrough";
                characteristics.push(characteristic);
            }

            var characteristic = new Map();
            characteristic["name"] = "Name";
            characteristic["enabled"] = true;
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".general.nickname"
            characteristic["conversionFunction"] = "script";
            characteristic["conversionParameters"] = new Map();
            characteristic["conversionParameters"]["toHomeKit"] = "return value + ' Battery';";
            characteristics.push(characteristic);

            var characteristic = new Map();
            characteristic["name"] = "SerialNumber";
            characteristic["enabled"] = true;
            characteristic["customCharacteristic"] =  true,
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".general.vin"
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            service["characteristics"] = characteristics;

            device["services"].push(service)
        }
        //Device Plug
        if(existsState(car + '.status.plugStatus.plugConnectionState')
                && existsState(car + '.general.nickname')
                && existsState(car + '.general.vin')){
            var deviceName = getState(car + '.general.nickname').val + ' Plug';
            var device = null;
            for(existingDevice of devices){
                if (existingDevice["name"] == deviceName){
                    console.log('Car '+car+' has plugSensor, plug device already exsisting, updating it',"debug");
                    device = existingDevice;
                    break;
                }
            }
            if(!device){
                console.log('Car '+car+' has plugSensor, creating plug device',"debug");
                device = new Map();
                devices.push(device)
            }
            device["configType"]= "customdevice";
            device["manufacturer"] = "unknown";
            device["model"] = "unknown";
            device["name"] = deviceName;
            device["serial"] = getState(car + '.general.vin').val;
            device["firmware"] = "";
            device["enabled"] = true;
            device["category"] = "10";

            device["services"] = new Array();

            //Service ContactSensor
            var service = new Map();
            var contactServiceName = deviceName;
            service["name"] = contactServiceName;
            service["subType"] = "";
            service["type"] = "ContactSensor";
            var characteristics = new Array();

            if(existsState(car + '.status.plugStatus.plugConnectionState')){
                var characteristic = new Map();
                characteristic["name"] = "ContactSensorState";
                characteristic["enabled"] = true;
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".status.plugStatus.plugConnectionState"
                characteristic["conversionFunction"] = "script";
                characteristic["conversionParameters"] = new Map();
                characteristic["conversionParameters"]["toHomeKit"] = "if(value=='connected')\n  return 0;\nreturn 1;";
                characteristics.push(characteristic);
            }

            if(existsState(car + '.status.plugStatus.plugConnectionState')){
                var characteristic = new Map();
                characteristic["name"] = "StatusFault";
                characteristic["enabled"] = true;
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".status.plugStatus.plugConnectionState"
                characteristic["conversionFunction"] = "script";
                characteristic["conversionParameters"] = new Map();
                characteristic["conversionParameters"]["toHomeKit"] = "if(value=='connected' || value=='disconnected')\n  return 0;\nreturn 1;";
                characteristics.push(characteristic);
            }

            var characteristic = new Map();
            characteristic["name"] = "StatusActive";
            characteristic["enabled"] = true;
            characteristic["customCharacteristic"] =  true,
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = "vw-connect.0.info.connection" //Todo determine adapter instance
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            service["characteristics"] = characteristics;

            device["services"].push(service)

            //Service AccessoryInformation
            var service = new Map();
            service["name"] = contactServiceName + ' AccessoryInformation';
            service["subType"] = "";
            service["type"] = "AccessoryInformation";
            service["linkTo"]= contactServiceName;
            var characteristics = new Array();

            if(existsState(car + '.general.model')){
                var characteristic = new Map();
                characteristic["name"] = "Model";
                characteristic["enabled"] = true;
                characteristic["customCharacteristic"] =  true,
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".general.model"
                characteristic["conversionFunction"] = "passthrough";
                characteristics.push(characteristic);
            }

            var characteristic = new Map();
            characteristic["name"] = "Name";
            characteristic["enabled"] = true;
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".general.nickname"
            characteristic["conversionFunction"] = "script";
            characteristic["conversionParameters"] = new Map();
            characteristic["conversionParameters"]["toHomeKit"] = "return value + ' Plug';";
            characteristics.push(characteristic);

            var characteristic = new Map();
            characteristic["name"] = "SerialNumber";
            characteristic["enabled"] = true;
            characteristic["customCharacteristic"] =  true,
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".general.vin"
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            service["characteristics"] = characteristics;

            device["services"].push(service)
        }
        //Device PlugLock
        if(existsState(car + '.status.plugStatus.plugLockState')
                && existsState(car + '.general.nickname')
                && existsState(car + '.general.vin')){
            var deviceName = getState(car + '.general.nickname').val + ' Plug Lock';
            var device = null;
            for(existingDevice of devices){
                if (existingDevice["name"] == deviceName){
                    console.log('Car '+car+' has plugSensor, plug device already exsisting, updating it',"debug");
                    device = existingDevice;
                    break;
                }
            }
            if(!device){
                console.log('Car '+car+' has plugSensor, creating plug device',"debug");
                device = new Map();
                devices.push(device)
            }
            device["configType"]= "customdevice";
            device["manufacturer"] = "unknown";
            device["model"] = "unknown";
            device["name"] = deviceName;
            device["serial"] = getState(car + '.general.vin').val;
            device["firmware"] = "";
            device["enabled"] = true;
            device["category"] = "10";

            device["services"] = new Array();

            //Service ContactSensor
            var service = new Map();
            var contactServiceName = deviceName;
            service["name"] = contactServiceName;
            service["subType"] = "";
            service["type"] = "ContactSensor";
            var characteristics = new Array();

            if(existsState(car + '.status.plugStatus.plugLockState')){
                var characteristic = new Map();
                characteristic["name"] = "ContactSensorState";
                characteristic["enabled"] = true;
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".status.plugStatus.plugLockState"
                characteristic["conversionFunction"] = "script";
                characteristic["conversionParameters"] = new Map();
                characteristic["conversionParameters"]["toHomeKit"] = "if(value=='locked')\n  return 0;\nreturn 1;";
                characteristics.push(characteristic);
            }

            if(existsState(car + '.status.plugStatus.plugLockState')){
                var characteristic = new Map();
                characteristic["name"] = "StatusFault";
                characteristic["enabled"] = true;
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".status.plugStatus.plugLockState"
                characteristic["conversionFunction"] = "script";
                characteristic["conversionParameters"] = new Map();
                characteristic["conversionParameters"]["toHomeKit"] = "if(value=='locked' || value=='unlocked')\n  return 0;\nreturn 1;";
                characteristics.push(characteristic);
            }

            var characteristic = new Map();
            characteristic["name"] = "StatusActive";
            characteristic["enabled"] = true;
            characteristic["customCharacteristic"] =  true,
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = "vw-connect.0.info.connection" //Todo determine adapter instance
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            service["characteristics"] = characteristics;

            device["services"].push(service)

            //Service AccessoryInformation
            var service = new Map();
            service["name"] = contactServiceName + ' AccessoryInformation';
            service["subType"] = "";
            service["type"] = "AccessoryInformation";
            service["linkTo"]= contactServiceName;
            var characteristics = new Array();

            if(existsState(car + '.general.model')){
                var characteristic = new Map();
                characteristic["name"] = "Model";
                characteristic["enabled"] = true;
                characteristic["customCharacteristic"] =  true,
                characteristic["inOutFunction"] = "ioBroker.State";
                characteristic["inOutParameters"] = car + ".general.model"
                characteristic["conversionFunction"] = "passthrough";
                characteristics.push(characteristic);
            }

            var characteristic = new Map();
            characteristic["name"] = "Name";
            characteristic["enabled"] = true;
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".general.nickname"
            characteristic["conversionFunction"] = "script";
            characteristic["conversionParameters"] = new Map();
            characteristic["conversionParameters"]["toHomeKit"] = "return value + ' Plug Lock';";
            characteristics.push(characteristic);

            var characteristic = new Map();
            characteristic["name"] = "SerialNumber";
            characteristic["enabled"] = true;
            characteristic["customCharacteristic"] =  true,
            characteristic["inOutFunction"] = "ioBroker.State";
            characteristic["inOutParameters"] = car + ".general.vin"
            characteristic["conversionFunction"] = "passthrough";
            characteristics.push(characteristic);

            service["characteristics"] = characteristics;

            device["services"].push(service)
        }
    });
    bridge.devices = devices;
    bridge.configType = "bridge";
    bridge.name = "VWsFriend";
    bridge.manufacturer = "https://github.com/tillsteinbach/VWsFriend";
    bridge.model = "VWsFriend";

    var username = null;
    if(process.env.HOMEKIT_USERNAME){
        username = process.env.HOMEKIT_USERNAME
        console.log('Configured homekit username (mac address format) from environment variable HOMEKIT_INTERFACE: '+ username,"debug");
    }
    else{
        username = "ee:6e:fb:c4:03:60";
        console.log('Configured homekit username (mac address format) from default: '+ username,"debug");
    }
    bridge.username = username;


    var pincode = "123-45-678";
    if(process.env.HOMEKIT_PIN){
        pincode = process.env.HOMEKIT_PIN
    }
    console.log('using PIN for homekit: '+ pincode,"debug");

    var listenInterface = "0.0.0.0";
    if(process.env.HOMEKIT_IP){
        listenInterface = process.env.HOMEKIT_IP
        console.log('Configured listenInterface from environment variable HOMEKIT_INTERFACE: '+ listenInterface,"debug");
    }
    else{
        var interfaces = os.networkInterfaces()
        for (const [name, ifConfigs] of Object.entries(interfaces)){
            if(name.startsWith("lo")){
                continue;
            }
            var found = false;
            for (const ifConfig of ifConfigs){
                if(ifConfig.address.startsWith("127")){
                    continue;
                }
                else{
                    listenInterface = ifConfig.address;
                    found = true;
                    break;
                }
            }
            if (found){
                break;
            }
        }
        console.log('Configured interface by guessing to address: ' + listenInterface + ' if this is wrong or your device cannot be found, try to set HOMEKIT_INTERFACE to the correct IP address of the host', "debug");
    }

    bridge.pincode = pincode;
    bridge.interface = listenInterface;
    bridge.ident = "Yahka-0";
    bridge.serial = "";
    bridge.port = 0;
    bridge.verboseLogging = false;
    bridge.firmware = "0.0.0";

    setObject('system.adapter.' + yahkainstance, config, function (err) {
        if (err)
            console.log('Cannot write object: ' + err, 'error');
        else
            console.log('Config written: ' + yahkainstance, 'debug');
    });
}

function main() {
    updateConfig('yahka.0');

}

setTimeout(main,    500);   // Zum Skriptstart ausführen

