from flask import Blueprint, abort
from flask_restful import (Resource, reqparse, fields, marshal_with, url_for,
                           Api, marshal)

import models


todo_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'completed': fields.Boolean,
}


def get_todo_or_404(todo_id):
    query = models.Todo.select().where(models.Todo.id == todo_id)
    if query.exists():
        return query.get()
    else:
        abort(404)


class Todo(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name',
            required=True,
            help='no todo name provided',
            location=['form', 'json']
        )
        self.reqparse.add_argument(
            'completed',
            required=True,
            help='no completion status provided',
            location=['form', 'json']
        )
        super().__init__()

    @marshal_with(todo_fields)
    def put(self, todo_id):
        todo = get_todo_or_404(todo_id)
        args = self.reqparse.parse_args()
        if args.completed == 'False':
            args.completed = False
        query = models.Todo.update(**args).where(models.Todo.id == todo.id)
        query.execute()
        todo = get_todo_or_404(todo_id)
        return (todo, 200,
                {'location': url_for('resources.todos.todo', todo_id=todo_id)})

    def delete(self, todo_id):
        todo = get_todo_or_404(todo_id)
        todo.delete_instance()
        return '', 204


class TodoList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name',
            required=True,
            help='no todo name provided',
            location=['form', 'json']
        )
        self.reqparse.add_argument(
            'completed',
            required=True,
            help='no completion status provided',
            location=['form', 'json']
        )
        super().__init__()

    @marshal_with(todo_fields)
    def get(self):
        todos = [marshal(todo, todo_fields) for todo in models.Todo.select()]
        return (todos, 200)

    @marshal_with(todo_fields)
    def post(self):
        args = self.reqparse.parse_args()
        if args.completed == 'False':
            args.completed = False
        todo = models.Todo.create(**args)
        return (todo, 201,
                {'location': url_for('resources.todos.todo', todo_id=todo.id)})


todos_api = Blueprint('resources.todos', __name__)
api = Api(todos_api)
api.add_resource(TodoList, '/todos', endpoint='todos')
api.add_resource(Todo, '/todos/<int:todo_id>', endpoint='todo')
