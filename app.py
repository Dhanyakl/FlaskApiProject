from flask import Flask, request, jsonify
from azure.cosmos import CosmosClient
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime


load_dotenv()

app = Flask(__name__)


COSMOS_CONN_STRING = os.environ.get("COSMOS_CONNECTION_STRING")


client = CosmosClient.from_connection_string(COSMOS_CONN_STRING)


database = client.get_database_client("blogdb")
container = database.get_container_client("posts")


@app.get("/posts")
def get_posts():
    items = list(container.read_all_items())
    return jsonify(items), 200



@app.get("/posts/<id>")
def get_post(id):
    try:
        query = "SELECT * FROM c WHERE c.id = @id"
        items = list(container.query_items(
            query=query,
            parameters=[{"name": "@id", "value": id}],
            enable_cross_partition_query=True
        ))

        if not items:
            return jsonify({"error": "Post not found"}), 404

        return jsonify(items[0]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.post("/posts")
def create_post():
    data = request.get_json()

  
    if not all(k in data for k in ("title", "content", "author")):
        return jsonify({"error": "title, content, and author are required"}), 400

    new_post = {
        "id": str(uuid.uuid4()),
        "title": data["title"],
        "content": data["content"],
        "author": data["author"],
        "timestamp": datetime.utcnow().isoformat()
    }

    container.create_item(new_post)
    return jsonify(new_post), 201


@app.delete("/posts/<id>")
def delete_post(id):
    query = "SELECT * FROM c WHERE c.id = @id"
    items = list(container.query_items(
        query=query,
        parameters=[{"name": "@id", "value": id}],
        enable_cross_partition_query=True
    ))

    if not items:
        return jsonify({"error": "Post not found"}), 404

    post = items[0]

    container.delete_item(post["id"], partition_key=post["author"])

    return jsonify({"message": "Post deleted"}), 200



if __name__ == "__main__":
    app.run(debug=True)
