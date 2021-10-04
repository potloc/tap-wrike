#!/usr/bin/env python3
import os
import json
import singer
from singer import utils, metadata
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema

from tap_wrike.client import Client


class dotdict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

REQUIRED_CONFIG_KEYS = ["token"]
LOGGER = singer.get_logger()

STREAMS = {
    "customfields": dotdict({
        "path": "customfields",
        "params": {},
    }),
    "folders": dotdict({
        # "replication_method": "INCREMENTAL", TODO
        # "replication_keys": ["updatedDate"],
        "path": "folders",
        "params": {
            "fields": "[\"metadata\",\"hasAttachments\",\"attachmentCount\",\"briefDescription\",\"customFields\",\"customColumnIds\",\"superParentIds\",\"space\",\"contractType\"]",
            "project": "false",
        },
    }),
    "projects": dotdict({
        "path": "folders",
        "params": {
            "fields": "[\"metadata\",\"hasAttachments\",\"attachmentCount\",\"briefDescription\",\"customFields\",\"customColumnIds\",\"superParentIds\",\"space\",\"contractType\"]",
            "project": "true",
        },
    }),
    "tasks": dotdict({
        "path": "tasks",
        "params": {
            "fields": "[\"authorIds\",\"hasAttachments\",\"attachmentCount\",\"parentIds\",\"superParentIds\",\"sharedIds\",\"responsibleIds\",\"description\",\"briefDescription\",\"recurrent\",\"superTaskIds\",\"subTaskIds\",\"dependencyIds\",\"metadata\",\"customFields\",\"effortAllocation\",\"billingType\"]",
            "pageSize": 1000,
        },
    }),
    "timelogs": dotdict({
        "path": "timelogs",
        "params": {
            "fields": "[\"billingType\"]"
        }
    }),
}

def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schema(stream_name):
    """ Load a schema from schemas folder """
    path = f"{get_abs_path('schemas')}/{stream_name}.json"
    with open(path) as file:
        schema = json.load(file)
    return schema


def discover():
    streams = []
    for stream_name, stream in STREAMS.items():
        schema = load_schema(stream_name)

        key_properties = stream.get("key_properties", ["id"])
        replication_method = stream.get("replication_method", "FULL_TABLE")
        replication_keys = stream.get("replication_keys", []) # Bookmark

        stream_metadata = metadata.get_standard_metadata(
            schema=schema,
            key_properties=key_properties,
            valid_replication_keys=replication_keys,
            replication_method=replication_method,
        )
        for entry in stream_metadata:
            if entry.get("breadcrumb") == ():
                table_metadata = entry.get("metadata", {})
                table_metadata["table-key-properties"] = key_properties

        LOGGER.info(stream_metadata)
        streams.append(
            CatalogEntry(
                tap_stream_id=stream_name,
                stream=stream_name,
                schema=Schema.from_dict(schema),
                key_properties=key_properties,
                metadata=stream_metadata,
                replication_key=None,
                is_view=None,
                database=None,
                table=None,
                row_count=None,
                stream_alias=None,
                replication_method=None,
            )
        )
    return Catalog(streams)


def sync_endpoint(config, state, stream, client):
    """ Sync data from tap source """

    bookmark_column = stream.catalog_entry.replication_key
    is_sorted = True  # TODO: indicate whether data is sorted ascending on bookmark value

    singer.write_schema(
        stream_name=stream.catalog_entry.tap_stream_id,
        schema=stream.catalog_entry.schema.to_dict(),
        key_properties=stream.catalog_entry.key_properties,
    )

    max_bookmark = None
    total_records = 0

    tap_data, next_page_token = client.get(stream.path, **stream.params)

    while True:
        for row in tap_data:
            # TODO: Field selection https://github.com/singer-io/getting-started/blob/master/docs/SYNC_MODE.md#field-selection

            # write one row to the stream:
            singer.write_records(stream.catalog_entry.tap_stream_id, [row])
            total_records += 1

            if bookmark_column:
                if is_sorted:
                    # update bookmark to latest value
                    singer.write_state({ stream.catalog_entry.tap_stream_id: row[bookmark_column] })
                else:
                    # if data unsorted, save max value until end of writes
                    max_bookmark = max(max_bookmark, row[bookmark_column])

        if next_page_token is None: break

        tap_data, next_page_token = client.get(stream.path, **stream.params, nextPageToken=next_page_token)

    if bookmark_column and not is_sorted:
        singer.write_state({ stream.catalog_entry.tap_stream_id: max_bookmark })

    return total_records

# Currently syncing sets the stream currently being delivered in the state.
# If the integration is interrupted, this state property is used to identify
#  the starting point to continue from.
# Reference: https://github.com/singer-io/singer-python/blob/master/singer/bookmarks.py#L41-L46
def update_currently_syncing(state, stream_name):
    if (stream_name is None) and ("currently_syncing" in state):
        del state["currently_syncing"]
    else:
        singer.set_currently_syncing(state, stream_name)
    singer.write_state(state)


def sync(config, state, catalog, client):
    # Get selected_streams from catalog, based on state last_stream
    #   last_stream = Previous currently synced stream, if the load was interrupted
    last_stream = singer.get_currently_syncing(state)
    LOGGER.info(f"last/currently syncing stream: {last_stream}")
    selected_streams = []
    for stream in catalog.get_selected_streams(state):
        selected_streams.append(stream.stream)
    LOGGER.info(f"Selected streams: {selected_streams}")
    if not selected_streams or selected_streams == []:
        return

    # Loop through endpoints in selected_streams
    for stream_name, stream in STREAMS.items():
        if stream_name in selected_streams:
            LOGGER.info(f"Syncing stream: {stream_name}")

            update_currently_syncing(state, stream_name)

            # Merge stream with catalog entry for it?
            stream["catalog_entry"] = catalog.get_stream(stream_name)

            total_records = sync_endpoint(config, state, stream, client)

            update_currently_syncing(state, None)
            LOGGER.info(f"FINISHED Syncing: {stream_name}, total_records: {total_records}")

@utils.handle_top_exception(LOGGER)
def main():
    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog = discover()
        catalog.dump()
    # Otherwise run in sync mode
    else:
        if args.catalog:
            catalog = args.catalog
        else:
            catalog = discover()

        client = Client(args.config["token"])
        sync(args.config, args.state, catalog, client)


if __name__ == "__main__":
    main()
