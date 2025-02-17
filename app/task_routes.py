from app import db
from app.models.task import Task
from flask import Blueprint, jsonify, make_response, request, abort
from datetime import datetime
from dotenv import load_dotenv
import os
import requests

load_dotenv()

task_bp = Blueprint("task_bp", __name__, url_prefix='/tasks')


@task_bp.route("", methods=["POST"])
def create_task():        
    request_body = request.get_json()
    if 'title' not in request_body or 'description' not in request_body:
        return make_response(jsonify({"details":"Invalid data"})),400
    new_task= Task(
        title = request_body['title'],
        description =  request_body['description']
        
    )
    
            
    db.session.add(new_task)
    db.session.commit()
    
           
    return {"task": {
                "id": new_task.task_id,
                "title": new_task.title,
                "description": new_task.description,
                "is_complete": False
            }},201


@task_bp.route("", methods=["GET"])
def read_all_tasks():

    task_query = Task.query
    
    sort_query = request.args.get("sort")

    if sort_query == "asc":
        task_query = task_query.order_by(Task.title.asc())
    
    elif sort_query == "desc":
        task_query = task_query.order_by(Task.title.desc())   
    tasks = task_query.all()
    
    tasks_response = []
    for task in tasks:
        tasks_response.append({
            "id": task.task_id,
            "title": task.title,
            "description": task.description,
            "is_complete": False
            })

    return jsonify(tasks_response),200

def validate_task(task_id):
    try:
        task_id = int(task_id)
    except:
        abort(make_response({"details": "Invalid data"}, 400))

    task = Task.query.get(task_id)

    if not task:
        abort(make_response(jsonify(dict(details=f"There is no existing task {task_id}")), 404))

    return task


@task_bp.route("/<task_id>", methods=['GET'])
def get_one_task(task_id):
    task = validate_task(task_id)
    
    if task.goal_id:
        response = {"task":{
            "id": task.task_id,
            "goal_id": task.goal_id,
            "title": task.title,
            "description": task.description,
            "is_complete": False
            }},200
    else:        
        response = {"task":{
                    "id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "is_complete": False
                    }},200

    return response

@task_bp.route("/<task_id>", methods=["PUT"])
def update_task(task_id):
    task = validate_task(task_id)
    request_body = request.get_json()

    task.title = request_body["title"]
    task.description = request_body["description"]
    

    db.session.commit()

    return make_response(jsonify({f"task": {
                "id": task.task_id,
                "title": task.title,
                "description": task.description,
                "is_complete": False
            }})),200


@task_bp.route("/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = validate_task(task_id)

    db.session.delete(task)
    db.session.commit()

    return {
        "details": f'Task {task.task_id} "{task.title}" successfully deleted'
    }

def slack_helper(title):

    URL = "https://slack.com/api/chat.postMessage"

    payload={"channel":"slack-bot-test-channel",
            "text": f"Someone just completed the task {title}"}

    headers = {
    "Authorization": os.environ.get('token_slack')
    }
#     
    return requests.post(URL,headers= headers, data=payload) 



@task_bp.route("/<task_id>/<complete>", methods=['PATCH'])
def mark_task(task_id,complete):
    task = validate_task(task_id)
    if complete == "mark_complete":
        task.completed_at = datetime.today()
        is_complete = True
        slack_helper(task.title)

    elif complete == "mark_incomplete":
        task.completed_at = None
        is_complete = False
        

    db.session.commit()
    response = make_response(jsonify({f"task": {
                "id": task.task_id,
                "title": task.title,
                "description": task.description,
                "is_complete": is_complete
            }}))
    
    return response,200
    
