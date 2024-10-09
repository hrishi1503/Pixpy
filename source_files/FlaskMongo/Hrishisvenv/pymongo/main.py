from flask import Blueprint, request

from .extensions import mongo

main = Blueprint('main', __name__) 

@main.route('/')
def index():
    return '''
        <form method="POST" action="/create" enctype="multipart/form-data">
            <input type="text" name="Code">
            <input type="submit">
        </form>
    '''

@main.route('/search', methods=['POST'])
def create():
    
    errortab = mongo.db.errtab
    if errortab.find({'err': request.form.get('Code')}):
        return '<h1>Error Found</h1>'
