#!/usr/bin/env python3
import os
import json
import singer
from singer import utils, metadata, Transformer
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema

from tap_wrike.client import Client, OAuth2Client, CSVClient
from tap_wrike.streams import STREAMS

REQUIRED_CONFIG_KEYS = [] # None since we either allow a permanent token or an OAuth2 refresh token
LOGGER = singer.get_logger()

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
        replication_key = stream.get("replication_key") # Bookmark

        stream_metadata = metadata.get_standard_metadata(
            schema=schema,
            key_properties=key_properties,
            valid_replication_keys=[replication_key],
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
                replication_key=replication_key,
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

    bookmark_column = stream.get("replication_key")
    bookmark_properties = [bookmark_column] if bookmark_column else None
    last_bookmark = singer.get_bookmark(state, stream.catalog_entry.tap_stream_id, bookmark_column)
    bookmark_params = {}
    if (bookmark_column is not None) and (last_bookmark is not None):
        bookmark_params = { bookmark_column: f"{{\"start\":\"{last_bookmark}\"}}" }

    singer.write_schema(
        stream_name=stream.catalog_entry.tap_stream_id,
        schema=stream.catalog_entry.schema.to_dict(),
        key_properties=stream.catalog_entry.key_properties,
        bookmark_properties=bookmark_properties,
    )

    parsed_last_bookmark = utils.strptime_to_utc(last_bookmark) if last_bookmark else None
    max_bookmark = parsed_last_bookmark
    total_records = 0

    tap_data, next_page_token = client.get(stream.path, **stream.params, **bookmark_params)

    with Transformer() as transformer:
        while True:
            for row in tap_data:
                # Use the singer transformer for Field selection
                # https://github.com/singer-io/getting-started/blob/master/docs/SYNC_MODE.md#field-selection
                processed_row = transformer.transform(row,
                                                        stream.catalog_entry.schema.to_dict(),
                                                        metadata.to_map(stream.catalog_entry.metadata))

                if bookmark_column:
                    parsed_bookmark = utils.strptime_with_tz(row[bookmark_column])

                    if parsed_last_bookmark is not None and parsed_bookmark < parsed_last_bookmark:
                        continue # Skip this data point as it is older than the last bookmark

                    if max_bookmark is None or parsed_bookmark >= max_bookmark:
                        max_bookmark = parsed_bookmark

                # write one row to the stream:
                singer.write_record(stream.catalog_entry.tap_stream_id, processed_row)
                total_records += 1

            if next_page_token is None: break

            tap_data, next_page_token = client.get(stream.path, **stream.params, **bookmark_params, nextPageToken=next_page_token)

    if (bookmark_column is not None) and (max_bookmark is not None):
        string_bookmark = utils.strftime(max_bookmark, format_str=utils.DATETIME_PARSE)
        singer.write_bookmark(state, stream.catalog_entry.tap_stream_id, bookmark_column, string_bookmark)
        singer.write_state(state)

    return total_records


def sync(config, state, catalog, client, csv_client):
    # Get selected_streams from catalog
    selected_streams = []
    for catalog_entry in catalog.get_selected_streams(state):
        selected_streams.append(catalog_entry)
    LOGGER.info(f"Selected streams: {selected_streams}")

    # Loop through endpoints in selected_streams
    for catalog_entry in selected_streams:
        stream_name = catalog_entry.stream
        stream = STREAMS.get(stream_name)
        stream["catalog_entry"] = catalog_entry # Merge stream with catalog entry for it

        LOGGER.info(f"Syncing stream: {stream_name}")

        endpoint_client = csv_client if stream.get("csv", False) else client
        total_records = sync_endpoint(config, state, stream, endpoint_client)

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

        if args.config["client_id"] and args.config["client_secret"] and args.config["refresh_token"]:
            client = OAuth2Client(args.config["client_id"], args.config["client_secret"], args.config["refresh_token"])
            csv_client = CSVClient(client)
        else:
            client = Client(args.config["token"])
            csv_client = None

        sync(args.config, args.state, catalog, client, csv_client)


if __name__ == "__main__":
    main()
