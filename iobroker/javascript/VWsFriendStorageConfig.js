const influxInstance = 'influxdb.0'
const connectFetchTimout = 30 * 1000;
const oneMonth = 31 * 24 * 60 * 60;
const oneYear = 365 * 24 * 60 * 60;
const twoYear = oneYear * 2;

const storageConfiguration = {
    'Car captured Timestamp (s)': {
        'regex': /^0_userdata\.\d+\.vw-connect\.\d+.([A-Z0-9]+)\.carCapturedTimestamp_s$/,
        'options': {
            'retention': oneMonth
        }
    },
    'Latest car captured timestamp from all services': {
        'regex': /^0_userdata\.\d+\.vw-connect\.\d+.([A-Z0-9]+)\.carCapturedTimestampLatest$/,
        'options': {
            'retention': oneMonth
        }
    },
    'Current consumption': {
        'regex': /^0_userdata\.\d+\.vw-connect\.\d+.([A-Z0-9]+)\.currentConsumption_kwhp100km$/,
        'options': {
            'retention': 0
        }
    },
    'Current efficiency': {
        'regex': /^0_userdata\.\d+\.vw-connect\.\d+.([A-Z0-9]+)\.efficiency_pct$/,
        'options': {
            'retention': 0
        }
    },
    'Current total range': {
        'regex': /^0_userdata\.\d+\.vw-connect\.\d+.([A-Z0-9]+)\.currentTotalRange_km$/,
        'options': {
            'retention': 0
        }
    },
    'Nickname:VIN': {
        'regex': /^0_userdata\.\d+\.vw-connect\.\d+.([A-Z0-9]+)\.nickname_vin$/,
        'options': {
            'retention': 0
        }
    },
    'Online': {
        'regex': /^0_userdata\.\d+\.vw-connect\.\d+.([A-Z0-9]+)\.online$/,
        'options': {
            'retention': 0
        }
    },
    'Usable Battery Capacity': {
        'regex': /^0_userdata\.\d+\.vw-connect\.\d+.([A-Z0-9]+)\.batteryCapacity_kwh$/,
        'options': {
            'retention': 0
        }
    },
    'WLTP range': {
        'regex': /^0_userdata\.\d+\.vw-connect\.\d+.([A-Z0-9]+)\.wltp_km$/,
        'options': {
            'retention': 0
        }
    },
    'carCapturedTimestamp': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.batteryStatus\.carCapturedTimestamp$/,
        'options': {
            'retention': oneMonth
        }
    },
    'cruisingRangeElectric_km': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.batteryStatus\.cruisingRangeElectric_km$/,
        'options': {
            'retention': oneMonth
        }
    },
    'currentSOC_pct': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.batteryStatus\.currentSOC_pct$/,
        'options': {
            'retention': oneMonth
        }
    },
    'maxChargeCurrentAC': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.chargingSettings\.maxChargeCurrentAC$/,
        'options': {
            'retention': 0
        }
    },
    'targetSOC_pct': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.chargingSettings\.targetSOC_pct$/,
        'options': {
            'retention': 0
        }
    },
    'chargePower_kW': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.chargingStatus\.chargePower_kW$/,
        'options': {
            'retention': 0
        }
    },
    'chargeRate_kmph': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.chargingStatus\.chargeRate_kmph$/,
        'options': {
            'retention': 0
        }
    },
    'chargingState': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.chargingStatus\.chargingState$/,
        'options': {
            'retention': 0
        }
    },
    'remainingChargingTimeToComplete_min': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.chargingStatus\.remainingChargingTimeToComplete_min$/,
        'options': {
            'retention': oneMonth
        }
    },
    'targetTemperature_C': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.climatisationSettings\.targetTemperature_C$/,
        'options': {
            'retention': 0
        }
    },
    'climatisationState': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.climatisationStatus\.climatisationState$/,
        'options': {
            'retention': 0
        }
    },
    'remainingClimatisationTime_min': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.climatisationStatus\.remainingClimatisationTime_min$/,
        'options': {
            'retention': oneMonth
        }
    },
    'plugConnectionState': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.plugStatus\.plugConnectionState$/,
        'options': {
            'retention': oneMonth
        }
    },
    'plugLockState': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.plugStatus\.plugLockState$/,
        'options': {
            'retention': oneMonth
        }
    },
    'carType': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.rangeStatus\.carType$/,
        'options': {
            'retention': 0
        }
    },
    'totalRange_km': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.rangeStatus\.totalRange_km$/,
        'options': {
            'retention': 0
        }
    },
    'windowLocation windowHeatingState': {
        'regex': /^vw-connect\.\d+.([A-Z0-9]+)\.status\.windowHeatingStatus\.windowHeatingStatus\.(front|rear)$/,
        'options': {
            'retention': oneMonth
        }
    }
};

function disableInflux(id) {
    sendTo(influxInstance, 'disableHistory', {
        id: id,
    }, function (result) {
        if (result.error) {
            console.log("Could not disable influx configuration for: " + id + ': ' + result.error, "debug");
        }
        if (result.success) {
            console.log("Disabled influx configuration for: " + id, "debug");
        }
    });
}

function enableInflux(id, options) {//{changesOnly: true, debounce: 0, retention: oneYear, maxLength: 0, changesMinDelta: 0, aliasId; '', changesRelogInterval; 0, storageType; ''}
    var mergedOptions = Object.assign({ changesOnly: true }, options);
    sendTo(influxInstance, 'enableHistory', {
        id: id,
        options: mergedOptions
    }, function (result) {
        if (result.error) {
            console.log("Could not enable influx configuration for: " + id + ': ' + result.error, "debug");
        }
        if (result.success) {
            console.log("Enabled influx configuration for: " + id, "debug");
        }
    });
}

function checkall() {
    for ([statename, config] of Object.entries(storageConfiguration)) {
        var ids = getIdByName(statename, true);
        if (ids) {
            for (id of ids) {
                const match = id.match(config['regex']);
                if (match) {
                    const obj = getObject(id)
                    if (!('common' in obj) || !('custom' in obj.common) || !(influxInstance in obj.common.custom)) {
                        enableInflux(id, config['options']);
                    }
                }
            }
        }
    }
}

function main() {
    checkall();
}

schedule({ minute: 0 }, function () {
    checkall();
});

//Schedule when connector goes online
on({ id: /^vw-connec^\.\d+\.info\.connection$/, change: 'ne', val: true }, function (obj) {
    setTimeout(checkall, connectFetchTimout);
});

setTimeout(main, 500);   // Zum Skriptstart ausführen



