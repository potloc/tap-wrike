# tap-wrike

This is a [Singer](https://singer.io) tap that produces JSON-formatted data
following the [Singer
spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md).

This tap:

- Pulls raw data from [Wrike](https://developers.wrike.com/api)
- Extracts the following resources:
  - Projects & Folders
  - Custom Fields
  - Tasks
  - Timelogs
- Outputs the schema for each resource
- (TODO) Incrementally pulls data based on the input state
