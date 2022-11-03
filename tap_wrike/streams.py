class dotdict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

STREAMS = {
    "customfields": dotdict({
        "path": "customfields",
        "params": {},
    }),
    "folders": dotdict({
        "path": "folders",
        "params": {
            "fields": "[\"metadata\",\"hasAttachments\",\"attachmentCount\",\"briefDescription\",\"customFields\",\"customColumnIds\",\"superParentIds\",\"space\",\"contractType\"]",
            "project": "false",
        },
        "replication_method": "INCREMENTAL",
        "replication_key": "updatedDate",
        "transforms": [{
            "name": "decode_ids",
            "config": {
                "keymaps": {
                    "id": "data_export_api_id",
                },
            },
        }],
    }),
    "projects": dotdict({
        "path": "folders",
        "params": {
            "fields": "[\"metadata\",\"hasAttachments\",\"attachmentCount\",\"briefDescription\",\"customFields\",\"customColumnIds\",\"superParentIds\",\"space\",\"contractType\"]",
            "project": "true",
        },
        "replication_method": "INCREMENTAL",
        "replication_key": "updatedDate",
        "transforms": [{
            "name": "decode_ids",
            "config": {
                "keymaps": {
                    "id": "data_export_api_id",
                },
            },
        }],
    }),
    "tasks": dotdict({
        "path": "tasks",
        "params": {
            "fields": "[\"authorIds\",\"hasAttachments\",\"attachmentCount\",\"parentIds\",\"superParentIds\",\"sharedIds\",\"responsibleIds\",\"description\",\"briefDescription\",\"recurrent\",\"superTaskIds\",\"subTaskIds\",\"dependencyIds\",\"metadata\",\"customFields\",\"effortAllocation\",\"billingType\"]",
            "pageSize": 1000,
        },
        "replication_method": "INCREMENTAL",
        "replication_key": "updatedDate",
        "transforms": [{
            "name": "decode_ids",
            "config": {
                "keymaps": {
                    "id": "data_export_api_id",
                },
            },
        }],
    }),
    "timelogs": dotdict({
        "path": "timelogs",
        "params": {
            "fields": "[\"billingType\"]"
        },
        "replication_method": "INCREMENTAL",
        "replication_key": "updatedDate",
    }),
    "users": dotdict({
        "path": "contacts",
        "params": {
            "fields": "[\"metadata\",\"workScheduleId\"]",
        },
        "transforms": [{
            "name": "decode_ids",
            "config": {
                "keymaps": {
                    "id": "data_export_api_id",
                },
            },
        }],
    }),
    "workflows": dotdict({
        "path": "workflows",
        "params": {},
        "transforms": [{
            "name": "decode_ids",
            "config": {
                "keymaps": {
                    "id": "data_export_api_id",
                    "customStatuses": {
                        "id": "data_export_api_id",
                    },
                },
            },
        }],
    }),
    "data_export_api_workflow_stage_history": dotdict({
        "csv": True,
        "path": "work_workflow_stage_history",
        "params": {},
        "key_properties": ["work_id", "old_workflow_stage_id", "new_workflow_stage_id", "user_id", "change_datetime"],
        "replication_method": "INCREMENTAL",
        "replication_key": "change_datetime",
    }),
    "data_export_api_work_custom_field_history": dotdict({
        "csv": True,
        "path": "work_custom_field_history",
        "params": {},
        "key_properties": ["work_id", "user_resource_id", "old_custom_field_value", "custom_field_id", "change_datetime"],
        "replication_method": "INCREMENTAL",
        "replication_key": "change_datetime",
    }),
    "groups": dotdict({
        "path": "groups",
        "params": {
            "fields": "[\"metadata\"]",
        },
        "replication_method": "FULL_TABLE",
        "transforms": [{
            "name": "decode_ids",
            "config": {
                "keymaps": {
                    "id": "data_export_api_id",
                },
            },
        }],
    })
}
