import logging
import azure.functions as func
import json
import os
import uuid
from azure.cosmos import CosmosClient, exceptions, PartitionKey

COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
COSMOS_KEY = os.environ.get("COSMOS_KEY")
DATABASE_NAME = os.environ.get("COSMOS_DATABASE", "ToDoDb")
TODO_CONTAINER_NAME = os.environ.get("COSMOS_TODO_CONTAINER", "ToDoItems")
IDEMPOTENCY_CONTAINER_NAME = os.environ.get("COSMOS_IDEMPOTENCY_CONTAINER", "IdempotencyKeys")

client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.get_database_client(DATABASE_NAME)
todo_container = database.get_container_client(TODO_CONTAINER_NAME)
idempotency_container = database.get_container_client(IDEMPOTENCY_CONTAINER_NAME)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing ToDo request.')

    method = req.method
    path = req.route_params.get('id')  # For /items/{id} or None

    idempotency_key = req.headers.get('Idempotency-Key')

    if method in ('POST', 'DELETE') and not idempotency_key:
        return func.HttpResponse(
            "Idempotency-Key header required for POST and DELETE",
            status_code=400
        )

    try:
        if method == 'GET':
            if path:
                try:
                    item = todo_container.read_item(item=path, partition_key=path)
                    return func.HttpResponse(body=json.dumps(item), status_code=200, mimetype="application/json")
                except exceptions.CosmosResourceNotFoundError:
                    return func.HttpResponse("Item not found", status_code=404)
            else:
                query = "SELECT * FROM c"
                items = list(todo_container.query_items(query=query, enable_cross_partition_query=True))
                return func.HttpResponse(body=json.dumps(items), status_code=200, mimetype="application/json")

        elif method == 'POST':
            try:
                record = idempotency_container.read_item(item=idempotency_key, partition_key=idempotency_key)
                return func.HttpResponse(body=json.dumps(record['response']), status_code=201, mimetype="application/json")
            except exceptions.CosmosResourceNotFoundError:
                pass

            item_data = req.get_json()
            item_id = str(uuid.uuid4())
            item_data['id'] = item_id

            todo_container.create_item(body=item_data)

            idempotency_container.create_item(body={
                'id': idempotency_key,
                'operation': 'create',
                'resourceId': item_id,
                'response': item_data
            })

            return func.HttpResponse(body=json.dumps(item_data), status_code=201, mimetype="application/json")

        elif method == 'DELETE':
            if not path:
                return func.HttpResponse("Missing Item id in URL", status_code=400)

            try:
                record = idempotency_container.read_item(item=idempotency_key, partition_key=idempotency_key)
                return func.HttpResponse(status_code=204)
            except exceptions.CosmosResourceNotFoundError:
                pass

            try:
                todo_container.read_item(item=path, partition_key=path)
            except exceptions.CosmosResourceNotFoundError:
                return func.HttpResponse("Item not found", status_code=404)

            todo_container.delete_item(item=path, partition_key=path)

            idempotency_container.create_item(body={
                'id': idempotency_key,
                'operation': 'delete',
                'resourceId': path,
                'response': None
            })

            return func.HttpResponse(status_code=204)

        else:
            return func.HttpResponse("Method not allowed", status_code=405)

    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Cosmos DB error: {e}")
        return func.HttpResponse("Internal server error", status_code=500)
    except Exception as ex:
        logging.error(f"General error: {ex}")
        return func.HttpResponse("Internal server error", status_code=500)
