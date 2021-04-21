var influxObjectId = "system.adapter.influxdb.0";

const Influx = require('influx');

var influx = null;
var influxObject = getObject(influxObjectId);
if(influxObject['native']){
    var influxhost = influxObject['native']['host'];
    influx = new Influx.InfluxDB({
        host : influxObject['native']['host'],
        port : influxObject['native']['port'],
        protocol : influxObject['native']['protocol'],
        username : influxObject['native']['user'],
        password : influxObject['native']['password'],
        database : influxObject['native']['dbname']
    });
}

var onOnlineRegex = /^(0_userdata\.\d+\.vw-connect\.\d+\.([A-Z0-9]+))\.online$/;
var carCapturedTimestampLatestState = '.carCapturedTimestampLatest';

var onClimatizationRegex = /^(vw-connect\.\d+\.([A-Z0-9]+))\.status\.climatisationStatus\.climatisationState$/;
var climatizationCapturedTimestampState = '.status.climatisationSettings.carCapturedTimestamp';

var onChargingRegex = /^(vw-connect\.\d+\.([A-Z0-9]+))\.status\.chargingStatus\.chargingState$/;
var chargingCapturedTimestampState = '.status.chargingStatus.carCapturedTimestamp';

on({id: onOnlineRegex, change:'ne'}, async function (obj) {
    //Wait 10 seconds to let other states to be set
    await wait(10000);

    const match = obj.id.match(onOnlineRegex);
    var car = match[1];
    var vin = match[2];

    var stateId = car + carCapturedTimestampLatestState;

    var timestamp = null;
    if(existsState(stateId)){
        var timestamp_string = getState(stateId).val;   // source
        timestamp = Date.parse(timestamp_string);
    }
    else{
        timestamp = new Date();
    }
    var timestamp_string = formatDate(timestamp, "YYYY-MM-DD hh:mm:ss.sss");

    if(obj.state.val == true && obj.oldState.val==false){
        influx.writePoint('vw_connect_events', {time: timestamp, value: vin}, {title: "Online", text: "Car went online", tags:"state"}, function (err) {
                if (err) console.log('Cannot write to influxdb: ' + err, 'error');
            });
        console.log("wrote online annotation for: " + match[2] + ' with timestamp ' + timestamp_string, "debug");
    }
    else if(obj.state.val == false && obj.oldState.val==true){
        influx.writePoint('vw_connect_events', {time: timestamp, value: vin}, {title: "Offline", text: "Car went offline", tags:"state"}, function (err) {
                if (err) console.log('Cannot write to influxdb: ' + err, 'error');
            });
        console.log("wrote offline annotation for: " + match[2] + ' with timestamp ' + timestamp_string, "debug");
    }
    else{
        console.log("no state change for: " + match[2] + ' with timestamp ' + timestamp_string,"debug");
    }
});

on({id: onClimatizationRegex, change:'ne'}, async function (obj) {
    //Wait 10 seconds to let other states to be set
    await wait(10000);

    const match = obj.id.match(onClimatizationRegex);
    var car = match[1];
    var vin = match[2];

    var stateId = car + climatizationCapturedTimestampState;

    var timestamp = null;
    if(existsState(stateId)){
        var timestamp_string = getState(stateId).val;   // source
        timestamp = Date.parse(timestamp_string);
    }
    else{
        timestamp = new Date();
    }
    var timestamp_string = formatDate(timestamp, "YYYY-MM-DD hh:mm:ss.sss");

    if(obj.state.val == 'off'){
        influx.writePoint('vw_connect_events', {time: timestamp, value: vin}, {title: "AC off", text: "Climatizaton switched off", tags:"climatization"}, function (err) {
                if (err) console.log('Cannot write to influxdb: ' + err, 'error');
            });
        console.log("wrote climiatization off annotation for: " + match[2] + ' with timestamp ' + timestamp_string, "debug");
    }
    else if(obj.state.val == 'heating'){
        influx.writePoint('vw_connect_events', {time: timestamp, value: vin}, {title: "AC on", text: "Climatizaton switched on (heating)", tags:"climatization"}, function (err) {
                if (err) console.log('Cannot write to influxdb: ' + err, 'error');
            });
        console.log("wrote climiatization on annotation for: " + match[2] + ' with timestamp ' + timestamp_string, "debug");
    }
    else if(obj.state.val == 'cooling'){
        influx.writePoint('vw_connect_events', {time: timestamp, value: vin}, {title: "AC on", text: "Climatizaton switched on (cooling)", tags:"climatization"}, function (err) {
                if (err) console.log('Cannot write to influxdb: ' + err, 'error');
            });
        console.log("wrote climiatization on annotation for: " + match[2] + ' with timestamp ' + timestamp_string, "debug");
    }
    else if(obj.state.val == 'ventilation'){
        influx.writePoint('vw_connect_events', {time: timestamp, value: vin}, {title: "AC on", text: "Climatizaton switched on (ventilation)", tags:"climatization"}, function (err) {
                if (err) console.log('Cannot write to influxdb: ' + err, 'error');
            });
        console.log("wrote climiatization on annotation for: " + match[2] + ' with timestamp ' + timestamp_string, "debug");
    }
    else{
        console.log("no climiatization change for: " + match[2] + ' with timestamp' + timestamp_string,"debug");
    }
});

on({id: onChargingRegex, change:'ne'}, async function (obj) {
    //Wait 10 seconds to let other states to be set
    await wait(10000);

    const match = obj.id.match(onChargingRegex);
    var car = match[1];
    var vin = match[2];

    var stateId = car + chargingCapturedTimestampState;

    var timestamp = null;
    if(existsState(stateId)){
        var timestamp_string = getState(stateId).val;   // source
        timestamp = Date.parse(timestamp_string);
    }
    else{
        timestamp = new Date();
    }
    var timestamp_string = formatDate(timestamp, "YYYY-MM-DD hh:mm:ss.sss");

    if(obj.state.val == 'readyForCharging'){
        influx.writePoint('vw_connect_events', {time: timestamp, value: vin}, {title: "Charging stopped", text: "Charging was stopped, vehicle is ready for charging", tags:"charging"}, function (err) {
                if (err) console.log('Cannot write to influxdb: ' + err, 'error');
            });
        console.log("wrote charging off annotation for: " + match[2] + ' with timestamp ' + timestamp_string, "debug");
    }
    else if(obj.state.val == 'charging'){
        influx.writePoint('vw_connect_events', {time: timestamp, value: vin}, {title: "Charging started", text: "Charging was started", tags:"charging"}, function (err) {
                if (err) console.log('Cannot write to influxdb: ' + err, 'error');
            });
        console.log("wrote charging on annotation for: " + match[2] + ' with timestamp ' + timestamp_string, "debug");
    }
    else{
        console.log("ignoring state ' + obj.state.val + ' for: " + match[2] + ' with timestamp ' + timestamp_string,"debug");
    }
});

function main() {
}


setTimeout(main,    500);   // Zum Skriptstart ausführen

