#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

api = Api(app)

class Index(Resource):
    def get(self):
        return "<h1>Code challenge</h1>"

class Restaurants(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return make_response(
            [restaurant.to_dict(only=('id', 'name', 'address')) for restaurant in restaurants],
            200
        )

class RestaurantById(Resource):
    def get(self, id):
        restaurant = db.session.get(Restaurant, id)
        if not restaurant:
            return make_response({"error": "Restaurant not found"}, 404)
        
        # Serialize restaurant with restaurant_pizzas and their pizza details
        restaurant_dict = restaurant.to_dict(
            only=('id', 'name', 'address', 'restaurant_pizzas')
        )
        # Manually adjust restaurant_pizzas to include only specified fields
        restaurant_dict['restaurant_pizzas'] = [
            {
                'id': rp.id,
                'pizza_id': rp.pizza_id,
                'price': rp.price,
                'restaurant_id': rp.restaurant_id,
                'pizza': rp.pizza.to_dict(only=('id', 'name', 'ingredients'))
            }
            for rp in restaurant.restaurant_pizzas
        ]
        return make_response(restaurant_dict, 200)
    
    def delete(self, id):
        restaurant = db.session.get(Restaurant, id)
        if not restaurant:
            return make_response({"error": "Restaurant not found"}, 404)
        
        db.session.delete(restaurant)
        db.session.commit()
        return make_response('', 204)

class Pizzas(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return make_response(
            [pizza.to_dict(only=('id', 'name', 'ingredients')) for pizza in pizzas],
            200
        )

class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()
        try:
            restaurant_pizza = RestaurantPizza(
                price=data['price'],
                pizza_id=data['pizza_id'],
                restaurant_id=data['restaurant_id']
            )
            
            # Verify restaurant and pizza exist
            if not db.session.get(Restaurant, data['restaurant_id']):
                return make_response({"errors": ["Restaurant not found"]}, 404)
            if not db.session.get(Pizza, data['pizza_id']):
                return make_response({"errors": ["Pizza not found"]}, 404)
            
            db.session.add(restaurant_pizza)
            db.session.commit()
            
            return make_response(
                restaurant_pizza.to_dict(
                    only=('id', 'price', 'pizza_id', 'restaurant_id', 'pizza', 'restaurant')
                ),
                201
            )
        
        except ValueError:
            # Return specific error message for validation errors
            return make_response({"errors": ["validation errors"]}, 400)
        except Exception:
            return make_response({"errors": ["Invalid request"]}, 400)

# Register resources
api.add_resource(Index, '/')
api.add_resource(Restaurants, '/restaurants')
api.add_resource(RestaurantById, '/restaurants/<int:id>')
api.add_resource(Pizzas, '/pizzas')
api.add_resource(RestaurantPizzas, '/restaurant_pizzas')

if __name__ == "__main__":
    app.run(port=5555, debug=True)