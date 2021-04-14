var influxObjectId = "system.adapter.influxdb.0";

const Influx = require('influx');

var influx = null;
var influxObject = getObject(influxObjectId);
if(influxObject['native']){
    var influxhost = influxObject['native']['host'];
    influx = new Influx.InfluxDB({
        host : influxObject['native']['host'],
        port : influxObject['native']['port'], // optional, default 8086
        protocol : influxObject['native']['protocol'], // optional, default 'http'
        username : influxObject['native']['user'],
        password : influxObject['native']['password'],
        database : influxObject['native']['dbname']
    });
}

var onOnlineRegex = /^0_userdata\.0\.vw-connect\.0\.([A-Z0-9]+)\.online$/;
var onClimatizationRegex = /^vw-connect\.0\.([A-Z0-9]+)\.status\.climatisationStatus\.climatisationState$/;
var onChargingRegex = /^vw-connect\.0\.([A-Z0-9]+)\.status\.chargingStatus\.chargingState$/;

on({id: onOnlineRegex, change:'ne'}, function (obj) {
    const match = obj.id.match(onOnlineRegex);
    var vin = match[1];

    if(obj.state.val == true && obj.oldState.val==false){
        influx.writePoint('vw_connect_events', vin, {title: "Online", text: "Car went online", tags:"state"}, null)
        console.log("wrote online annotation for: " + match[1], "debug");
    }
    else if(obj.state.val == false && obj.oldState.val==true){
        influx.writePoint('vw_connect_events', vin, {title: "Offline", text: "Car went offline", tags:"state"}, null)
        console.log("wrote offline annotation for: " + match[1], "debug");
    }
    else{
        console.log("no state change for: " + match[1],"debug");
    }    
});

on({id: onClimatizationRegex, change:'ne'}, function (obj) {
    const match = obj.id.match(onClimatizationRegex);
    var vin = match[1];

    if(obj.state.val == 'off'){
        influx.writePoint('vw_connect_events', vin, {title: "AC off", text: "Climatizaton switched off", tags:"climatization"}, null)
        console.log("wrote climiatization off annotation for: " + match[1], "debug");
    }
    else if(obj.state.val == 'heating'){
        influx.writePoint('vw_connect_events', vin, {title: "AC on", text: "Climatizaton switched on (heating)", tags:"climatization"}, null)
        console.log("wrote climiatization on annotation for: " + match[1], "debug");
    }
    else if(obj.state.val == 'cooling'){
        influx.writePoint('vw_connect_events', vin, {title: "AC on", text: "Climatizaton switched on (cooling)", tags:"climatization"}, null)
        console.log("wrote climiatization on annotation for: " + match[1], "debug");
    }
    else{
        console.log("no climiatization change for: " + match[1],"debug");
    }    
});

on({id: onChargingRegex, change:'ne'}, function (obj) {
    const match = obj.id.match(onChargingRegex);
    var vin = match[1];

    if(obj.state.val == 'readyForCharging'){
        influx.writePoint('vw_connect_events', vin, {title: "Charging stopped", text: "Charging was stopped, vehicle is ready for charging", tags:"charging"}, null)
        console.log("wrote charging off annotation for: " + match[1], "debug");
    }
    else if(obj.state.val == 'charging'){
        influx.writePoint('vw_connect_events', vin, {title: "Charging started", text: "Charging was started", tags:"charging"}, null)
        console.log("wrote charging on annotation for: " + match[1], "debug");
    }
    else{
        console.log("ignoring state ' + obj.state.val + ' for: " + match[1],"debug");
    }    
});

function main() {
}


setTimeout(main,    500);   // Zum Skriptstart ausführen
