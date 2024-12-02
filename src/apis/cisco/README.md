# Cisco XDR Configuration
Currently, the below API types are supported
- [Cisco XDR OAuth](#cisco-xdr-oauth-configuration) (`cisco_xdr`) - Auto replacement of the access token.


## Cisco XDR OAuth Configuration
| Parameter Name                  | Description                                                                                                                                                         | Required/Optional | Default           |
|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|-------------------|
| name                            | Name of the API (custom name)                                                                                                                                       | Optional          | the defined `url` |
| cisco_client_id                 | Cisco Client ID                                                                                                                                                     | Required          | -                 |
| client_password                 | Cisco Client password                                                                                                                                               | Required          | -                 |
| data_request.url                | The request URL                                                                                                                                                     | Required          | -                 |
| data_request.body               | The request body                                                                                                                                                    | Optional          | -                 |
| data_request.method             | The request method (`GET` or `POST`)                                                                                                                                | Optional          | `GET`             |
| data_request.pagination         | Pagination settings if needed (Options in [General API](../general/README.md))                                                                                      | Optional          | -                 |
| data_request.next_url           | If needed to update the URL in next requests based on the last response. Supports using variables (Options in [General API](../general/README.md/#using-variables)) | Optional          | -                 |
| data_request.response_data_path | The path to the data inside the response                                                                                                                            | Optional          | response root     |
| data_request.additional_fields  | Additional custom fields to add to the logs before sending to logzio                                                                                                | Optional          | -                 |
| scrape_interval                 | Time interval to wait between runs (unit: `minutes`)                                                                                                                | Optional          | 1 (minute)        |


## Example
```Yaml
apis:
  - name: cisco
    type: cisco_xdr
    cisco_client_id: <<CISCO_CLIENT_ID>>
    client_password: <<CISCO_CLIENT_SECRET>>
    scrape_interval: 30
    data_request:
      url: https://visibility.amp.cisco.com/iroh/iroh-enrich/deliberate/observables    
      method: POST
      body: [
              {
                  "type": "domain",
                  "value": "ilo.brenz.pl"
              },
              {
                  "type": "email",
                  "value": "no-reply@internetbadguys.com"
              },
              {
                  "type": "sha256",
                  "value": "8fda14f91e27afec5c1b1f71d708775c9b6e2af31e8331bbf26751bc0583dc7e"
              }
          ]
      response_data_path: data
    additional_fields:
      type: cisco
      field_to_add_in_logs: random value


logzio:
  url: https://listener-eu.logz.io:8071
  token: <<SHIPPING_TOKEN>>
```
