from flask_restx import Namespace, Resource, fields
from models.users import UserModel

user = Namespace("Users", "User related endpoints")

# Model for documentation
user_model = user.model(
    "User",
    {
        "users_pk": fields.Integer(readonly=True),
        "name": fields.String(required=True),
        "email": fields.String(required=True),
    },
)


@user.route("/")
class UserList(Resource):
    @user.marshal_list_with(user_model)
    def get(self):
        """Get all users"""
        return UserModel.query.all()

    @user.expect(user_model)
    @user.marshal_with(user_model, code=201)
    def post(self):
        """Create a new user"""
        data = user.payload
        if UserModel.find_by_email(data["email"]):
            user.abort(400, "Email already exists")

        new_user = UserModel(name=data["name"], email=data["email"])
        new_user.save_user()
        return new_user, 201


@user.route("/<int:users_pk>")
class User(Resource):
    @user.marshal_with(user_model)
    def get(self, users_pk):
        """Get user by ID"""
        user_obj = UserModel.find_user(users_pk)
        if not user_obj:
            user.abort(404, "User not found")
        return user_obj

    @user.expect(user_model)
    @user.marshal_with(user_model)
    def put(self, users_pk):
        """Update user"""
        user_obj = UserModel.find_user(users_pk)
        if not user_obj:
            user.abort(404, "User not found")

        data = user.payload
        # Check if email is being changed and if it's unique
        if "email" in data and data["email"] != user_obj.email:
            if UserModel.find_by_email(data["email"]):
                user.abort(400, "Email already exists")

        user_obj.update_user(**data)
        return user_obj

    def delete(self, users_pk):
        """Delete user"""
        user_obj = UserModel.find_user(users_pk)
        if not user_obj:
            user.abort(404, "User not found")

        user_obj.delete_user()
        return {"message": "User deleted successfully"}, 200
