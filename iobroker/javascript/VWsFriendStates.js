const process = require("process");

var carGeneralRegex = /(vw-connect\.\d+\.[A-Z0-9]+)/;
var carCapturedTimestampRegex = /^(vw-connect\.\d+\.[A-Z0-9]+)\.status\.(.*)\.carCapturedTimestamp$/;
var carCapturedTimestampName = 'carCapturedTimestamp';
var enrollmentStatusRegex = /^(vw-connect\.\d+\.[A-Z0-9]+)\.general\.enrollmentStatus$/;
var cruisingRangeElectricRegex = /^vw-connect\.\d+\.([A-Z0-9]+)\.status\.batteryStatus\.cruisingRangeElectric_km$/;
var cruisingRangeElectricName = 'status.batteryStatus.cruisingRangeElectric_km';
var currentSOCRegex = /^vw-connect\.\d+\.([A-Z0-9]+)\.status\.batteryStatus\.currentSOC_pct$/;
var currentSOCName = 'status.batteryStatus.currentSOC_pct';
var batteryCapacityRegex = /^0_userdata\.\d+\.vw-connect\.\d+\.([A-Z0-9]+)\.batteryCapacity_kwh$/;
var batteryCapacityName = 'batteryCapacity_kwh';
var wltpRangeRegex = /^0_userdata\.\d+\.vw-connect\.\d+\.([A-Z0-9]+)\.wltp_km$/;
var wltpRangeName = 'wltp_km';
var nicknameRegex = /^(vw-connect\.\d+\.[A-Z0-9]+)\.general\.nickname$/;
var nicknameVINonlyRegex = /^vw-connect\.\d+\.([A-Z0-9]+)\.general\.nickname$/;
var nicknameName = 'nickname';
var userdata = '0_userdata.0.'
var captureIntervalSeconds = 60 * 5; 

var stateTemplates = {
    "online" : {
            "name": 'Online',
            "type": 'boolean',
            "role": 'value',
            "unit": ''
    },
    "nickname_vin" : {
            "name": 'Nickname:VIN',
            "type": 'string',
            "role": 'value',
            "unit": ''
    },
    "currentTotalRange_km" : {
            "name": 'Current total range',
            "desc": 'Current total range projected on 100% battery state (requires batteryCapacity_kwh to be set)',
            "type": 'number',
            "role": 'value',
            "unit": 'km'
    },
    "currentConsumption_kwhp100km" : {
            "name": 'Current consumption',
            "desc": 'Current consumption for 100km (requires batteryCapacity_kwh to be set)',
            "type": 'number',
            "role": 'value',
            "unit": 'kWh/100km'
    },
    "efficiency_pct" : {
            "name": 'Current efficiency',
            "desc": 'Current efficiency in percent related to WLTP range (requires wltp_km to be set)',
            "type": 'number',
            "role": 'value',
            "unit": '%'
    },
    "batteryCapacity_kwh" : {
            "name": 'Usable Battery Capacity',
            "desc": 'The usable energy in the cars battery, necessary for calculations',
            "type": 'number',
            "role": 'value',
            "unit": 'kWh'
    },
    "wltp_km" : {
            "name": 'WLTP range',
            "desc": 'WLTP range of the car, necessary for calculations',
            "type": 'number',
            "role": 'value',
            "unit": 'km'
    },
    "carCapturedTimestamp_s" : {
            "name": 'Car captured Timestamp (s)',
            "desc": 'carCapturedTimestamp in seconds instead of date',
            "type": 'number',
            "role": 'value',
            "unit": 's'
    }
};

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

function carGetFirstIdWithName(car, name){
    var states = getIdByName(name, true);
    if(states){
        for (state of states){
            if (state.startsWith(car)){
                return state;
            }
        }
    }
    return null;
}

function carHasStateWithName(car, name){
    var state = carGetFirstIdWithName(car, name)
    return (state != null);
}

function createStateFromTemplate(template, id, init, forceCreation = false) {
    createState(id, init , forceCreation, template, function (err) {
        if (err) console.log('Cannot write object: ' + err, 'error');
        else console.log(id + ': New state was created','debug');
    });
    
}

function runden(wert,stellen) {
    var gerundet = Math.round(wert*Math.pow(10, stellen))/Math.pow(10, stellen);
    return gerundet;
}

function setOnlineState(car, changedId=null, setTimer=true) {
    if (!carHasStateWithName(car, carCapturedTimestampName)){
        console.log(car + ': has no state carCapturedTimestamp, cannot check online/offline state', 'debug');
        return
    }
    var onlineState = userdata + car + '.online';
    var timestamp_string = getState(carGetFirstIdWithName(car, carCapturedTimestampName)).val;   // source
    var timestamp = Date.parse(timestamp_string);
    var online = true;
    if ((Date.now() - timestamp) > ((captureIntervalSeconds + 10) * 1000)){
        online = false;
    }
    else if (setTimer == true){
        setTimeout(setOnlineState.bind(null, car, changedId, false), ((captureIntervalSeconds + 10) * 1000));
    }
    
    if(!existsState(onlineState)){
        createStateFromTemplate(stateTemplates['online'], onlineState, online.toString(), false);
    }
    else{
        setState(onlineState , online, function (err) {
            if (err) console.log('Cannot write object: ' + err, 'error');
        });
    }

    console.log(onlineState + ': car is '+ (online?'online':'offline'), 'debug');
}

function setStimestamSState(car, changedId=null){
    if(changedId!=null){
        var source = changedId;
    }
    else{
        if (!carHasStateWithName(car, carCapturedTimestampName)){
            console.log(car + ': has no state carCapturedTimestamp, cannot check online/offline state', 'debug');
            return
        }
        var source = carGetFirstIdWithName(car, carCapturedTimestampName);
    }
    

    var timestamp_string = getState(source).val;   // source
    var timestamp = Date.parse(timestamp_string)/1000; //date in ms to seconds

    var timestampSId = userdata + car + '.carCapturedTimestamp_s';

    if(!existsState(timestampSId)){
        createStateFromTemplate(stateTemplates['carCapturedTimestamp_s'], timestampSId, timestamp.toString(), false);
    }
    else {
        setState(timestampSId , timestamp, function (err) {
            if (err) console.log('Cannot write object: ' + err, 'error');
        });
    }

}

function setNicknameVIN(car, changedId=null){
    if(changedId!=null){
        var source = changedId;
    }
    else{
        if (!carHasStateWithName(car, nicknameName)){
            console.log(car + ': has no state nickname, cannot do nickname vin mapping', 'debug');
            return
        }
        var source = carGetFirstIdWithName(car, nicknameName);
    }
    
    const match = source.match(nicknameVINonlyRegex);
    var vin = match[1];
    var nicknameVIN_string = getState(source).val + ':' + vin;

    var nicknameVINId = userdata + car + '.nickname_vin';

    if(!existsState(nicknameVINId)){
        createStateFromTemplate(stateTemplates['nickname_vin'], nicknameVINId, nicknameVIN_string, false);
    }
    else {
        setState(nicknameVINId , nicknameVIN_string, function (err) {
            if (err) console.log('Cannot write object: ' + err, 'error');
        });
    }

}

function setConsumptionAndRangeStates(car, changedId=null) {
    var socId = car + '.' + currentSOCName;
    var rangeId = car + '.' + cruisingRangeElectricName;
    var capacityId = userdata + car + '.' + batteryCapacityName;
    var wltpId = userdata + car + '.' + wltpRangeName;
    var currentTotalRangeId = userdata + car + '.' + 'currentTotalRange_km';
    var currentConsumptionId = userdata + car + '.' + 'currentConsumption_kwhp100km';
    var efficiencyId = userdata + car + '.' + 'efficiency_pct';

    if(!existsState(socId)){
        console.log(car + ': has no state ' + socId + ': cannot calculate additional consumption parameters', 'debug');
        return;
    }
    else {
        var soc = getState(socId).val;   // soc auslesen
    }

    if(!existsState(rangeId)){
        console.log(car + ': has no state ' + rangeId + ': cannot calculate additional consumption parameters', 'debug');
        return;
    }
    else {
        var range = getState(rangeId).val; // range auslesen
    }

    if(!existsState(capacityId)){
        if(process.env.CAR_BATTERYSIZE_KWH){
            var capacity = process.env.CAR_BATTERYSIZE_KWH
            console.log(car + ': has no state ' + capacityId + ': will create it from CAR_BATTERYSIZE_KWH variable with '+wltp+'kWh', 'debug');
        }
        else{
            var capacity = 58
            console.log(car + ': has no state ' + capacityId + ': will create it with default of '+capacity+'kWh, you have to change it for your car in the config setting CAR_BATTERYSIZE_KWH', 'debug');
        }
        createStateFromTemplate(stateTemplates['batteryCapacity_kwh'], capacityId, capacity, false);
    }
    else {
        var capacity = getState(capacityId).val; // capacity auslesen
    }
    if(!existsState(wltpId)){
        if(process.env.CAR_ELECTRIC_RANGE_KM){
            var wltp = process.env.CAR_ELECTRIC_RANGE_KM
            console.log(car + ': has no state ' + wltpId + ': will create it from CAR_ELECTRIC_RANGE_KM variable with '+wltp+'km', 'debug');
        }
        else{
            var wltp = 416
            console.log(car + ': has no state ' + wltpId + ': will create it with default of '+wltp+'km, you have to change it for your car in the config setting CAR_ELECTRIC_RANGE_KM', 'debug');
            
        }
        createStateFromTemplate(stateTemplates['wltp_km'], wltpId, wltp, false);
    }
    else {
        var wltp = getState(wltpId).val; // wltp auslesen
    }

    var currentTotalRange = range / soc*100;
    var currentConsumption = capacity / currentTotalRange*100;
    var efficiency = currentTotalRange / wltp * 100;

    if(!existsState(currentTotalRangeId)){
        createStateFromTemplate(stateTemplates['currentTotalRange_km'], currentTotalRangeId, Math.round(currentTotalRange).toString(), false);
    }
    else{
        setState(currentTotalRangeId , Math.round(currentTotalRange), function (err) {
            if (err) console.log('Cannot write object: ' + err, 'error');
        });
    }
    if(!existsState(currentConsumptionId)){
        createStateFromTemplate(stateTemplates['currentConsumption_kwhp100km'], currentConsumptionId, runden(currentConsumption,2).toString(), false);
    }
    else{
        setState(currentConsumptionId , runden(currentConsumption,2), function (err) {
            if (err) console.log('Cannot write object: ' + err, 'error');
        });
    }
    if(!existsState(efficiencyId)){
        createStateFromTemplate(stateTemplates['efficiency_pct'], efficiencyId, Math.round(efficiency).toString(), false);
    }
    else{
        setState(efficiencyId , Math.round(efficiency), function (err) {
            if (err) console.log('Cannot write object: ' + err, 'error');
        });
    }

    console.log("currentTotalRange_km: " + currentTotalRange,"debug");
    console.log("currentConsumption_kwhp100km: " + currentConsumption,"debug");
    console.log("efficiency_pct: " + efficiency,"debug");
}

function main() {
    var cars = findCars()
    console.log('Found the following cars: '+ cars,"debug");
    cars.forEach(function(car){
        setOnlineState(car);
        setStimestamSState(car);
        setConsumptionAndRangeStates(car)
        setNicknameVIN(car)
    });
}

//For Online State
on({id: carCapturedTimestampRegex, change:'ne'}, function (obj) {
    const match = obj.id.match(carCapturedTimestampRegex);
    var car = match[1];
    setOnlineState(car, obj.id);
    setStimestamSState(car, obj.id);
});

//For Nickname State
on({id: nicknameRegex, change:'ne'}, function (obj) {
    const match = obj.id.match(carCapturedTimestampRegex);
    var car = match[1];
    setNicknameVIN(car, obj.id);
});

//For Range and Efficiency State
on({id: [cruisingRangeElectricRegex, currentSOCRegex, batteryCapacityRegex], change:'ne'}, function (obj) {
    const match = obj.id.match(carGeneralRegex);
    var car = match[1];
    setConsumptionAndRangeStates(car, obj.id);
});

setTimeout(main,    500);   // Zum Skriptstart ausführen



