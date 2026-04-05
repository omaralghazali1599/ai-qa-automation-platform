from flask import Flask, request, jsonify, session

app = Flask(__name__)
app.secret_key = "thesis-secret-key"

tasks = {}
task_counter = [1]
VALID_CATEGORIES = ["work", "personal", "urgent", "other"]
VALID_PRIORITIES = ["low", "medium", "high"]

def next_id():
    tid = task_counter[0]
    task_counter[0] += 1
    return tid

@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    title = data.get("title", "").strip()
    category = data.get("category", "other").lower()
    priority = data.get("priority", "medium").lower()
    description = data.get("description", "").strip()

    if not title:
        return jsonify({"error": "Title is required"}), 400
    if len(title) > 200:
        return jsonify({"error": "Title exceeds 200 characters"}), 400
    if category not in VALID_CATEGORIES:
        return jsonify({"error": f"Category must be one of {VALID_CATEGORIES}"}), 400
    if priority not in VALID_PRIORITIES:
        return jsonify({"error": f"Priority must be one of {VALID_PRIORITIES}"}), 400

    tid = next_id()
    tasks[tid] = {
        "id": tid,
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
        "completed": False
    }
    return jsonify(tasks[tid]), 201


@app.route("/tasks", methods=["GET"])
def list_tasks():
    category = request.args.get("category")
    priority = request.args.get("priority")
    completed = request.args.get("completed")

    result = list(tasks.values())

    if category:
        result = [t for t in result if t["category"] == category]
    if priority:
        result = [t for t in result if t["priority"] == priority]
    if completed is not None:
        is_done = completed.lower() == "true"
        result = [t for t in result if t["completed"] == is_done]

    return jsonify(result), 200


@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(tasks[task_id]), 200


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()
    task = tasks[task_id]

    if "title" in data:
        if not data["title"].strip():
            return jsonify({"error": "Title cannot be empty"}), 400
        task["title"] = data["title"].strip()
    if "category" in data:
        if data["category"] not in VALID_CATEGORIES:
            return jsonify({"error": f"Invalid category"}), 400
        task["category"] = data["category"]
    if "priority" in data:
        if data["priority"] not in VALID_PRIORITIES:
            return jsonify({"error": f"Invalid priority"}), 400
        task["priority"] = data["priority"]
    if "description" in data:
        task["description"] = data["description"]
    if "completed" in data:
        task["completed"] = bool(data["completed"])

    return jsonify(task), 200


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404
    deleted = tasks.pop(task_id)
    return jsonify({"message": "Task deleted", "task": deleted}), 200


@app.route("/tasks/<int:task_id>/complete", methods=["POST"])
def complete_task(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404
    tasks[task_id]["completed"] = True
    return jsonify({"message": "Task marked as complete", "task": tasks[task_id]}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5002)