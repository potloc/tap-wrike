# tap-wrike

This is a [Singer](https://singer.io) tap that produces JSON-formatted data
following the [Singer
spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md).

This tap:

- Pulls raw data from [Wrike](https://developers.wrike.com/api)
- Extracts the following resources:
  - [Projects](https://developers.wrike.com/api/v4/folders-projects/)
  - [Folders](https://developers.wrike.com/api/v4/folders-projects/)
  - [Custom Fields](https://developers.wrike.com/api/v4/custom-fields/) (`FULL_TABLE` replication)
  - [Tasks](https://developers.wrike.com/api/v4/tasks/)
  - [Timelogs](https://developers.wrike.com/api/v4/timelogs/)
  - [Contacts/Users](https://developers.wrike.com/api/v4/contacts/) (`FULL_TABLE` replication)
  - [Workflows](https://developers.wrike.com/api/v4/workflows/) (`FULL_TABLE` replication)
    - And their `customStatuses` (a.k.a. Workflow Stages)
  - Does not (yet) import from other endpoints of the Wrike API
- **Additionally**, provided an OAuth access token (see below), extracts the following resources **from the [Data Export API](https://developers.wrike.com/api/v4/data-export/)**:
  - Workflow Stage History (as a table named `data_export_api_workflow_stage_history`)
  - Data from this export type uses a different ID system so an additional column named `data_export_api_id` is also added to the other resources in order to make joins easier between the 2 data sources
- Outputs the schema for each resource
- Incrementally pulls data based on the input state

## Config

The minimum required configuration is a Wrike **permanent** token (see `sample_config.json`)

### Using an OAuth access token

**Alternatively**, one can use an OAuth access token.

> NOTE: This is required for the `Workflow Stage History` resource as it requires the `dataExportFull` permission

1. Create an app in Wrike following the instructions in "Initial Setup" [here](https://developers.wrike.com/oauth-20-authorization/)
2. Using the client_id from step 1, go to: `https://login.wrike.com/oauth2/authorize/v4?client_id=<client_id>&response_type=code&scope=wsReadOnly,dataExportFull`
3. After login (**using an Admin account**) in to Wrike, retrieve the `code` from the query parameters in the resulting URL.
   This authorization code is only valid for 10 minutes
4. Use the code as `authorization_code` in: `curl -X POST -d "client_id=<client_id>&client_secret=<client_secret>&grant_type=authorization_code&code=<authorization_code>" https://login.wrike.com/oauth2/token`
5. Take the `refresh_token` returned by this request and add it to the `config.json` file
