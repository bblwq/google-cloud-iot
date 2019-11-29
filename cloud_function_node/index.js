const {google} = require('googleapis');

var serviceAccount = '<paste contents of the service account json blob here>';

exports.raspberryPiEvent = (event) => {
  const payload = JSON.parse(Buffer.from(event.data,'base64').toString());
  const jwtAccess = new google.auth.JWT();
  jwtAccess.fromJSON(serviceAccount);
  jwtAccess.scopes = 'https://www.googleapis.com/auth/cloud-platform';
  google.options({ auth:jwtAccess });

  var client = google.cloudiot('v1');
  var devicePath = 'projects/${payload.project_id}/locations/${payload.gcp_location}/registries/${payload.registryId}/devices/${payload.deviceId}';
  if (payload.prev_temperature < payload.curr_temperature) {
    const request = {
      name: devicePath,
      binaryData: Buffer.from('red').toString('base64')
    };
    client.projects.locations.registries.devices.sendCommandToDevice(request);
  }
  else if (payload.prev_temperature == payload.curr_temperature) {
    const request = {
      name: devicePath,
      binaryData: Buffer.from('green').toString('base64')
    };
    client.projects.locations.registries.devices.sendCommandToDevice(request);
  }
  else {
    const request = {
      name: devicePath,
      binaryData: Buffer.from('blue').toString('base64')
    };
    client.projects.locations.registries.devices.sendCommandToDevice(request);
  }
};

/*
const request = {
  name: devicePath,
  versionToUpdate: '0',
  binaryData: Buffer.from('whatever').toString('base64')
};
client.projects.locations.registries.devices.modifyCloudToDeviceConfig(configRequest);
*/