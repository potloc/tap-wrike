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
  - [Contacts](https://developers.wrike.com/api/v4/contacts/) (`FULL_TABLE` replication)
  - Does not (yet) import from other endpoints of the Wrike API
- Outputs the schema for each resource
- Incrementally pulls data based on the input state

## Config

The only configuration required is a Wrike token (see `sample_config.json`)
