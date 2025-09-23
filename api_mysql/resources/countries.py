import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.countries import CountriesModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from utils import boolean_string


country = Namespace("Countries", "Countries related Endpoints")


@country.route("/cadastro")
class CountryRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "name",
        type=str,
        required=True,
    ),
    atributos.add_argument(
        "abbreviation",
        type=str,
        required=True,
    ),
    atributos.add_argument("active", type=bool, required=False, default=True),

    @country.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        if CountriesModel.find_by_name(dados["name"]):
            return (
                {"message": "The country '{}' already exists.".format(dados["name"])},
                400,
            )

        country = CountriesModel(**dados)
        try:
            country.save_country()

        except:
            country.remove_country()
            traceback.print_exc()
            return {"message": "Internal server error"}, 500

        return {
            "message": "country created successfully",
            "user": country.json(),
        }, 201  # Created


@country.route("/search")
class CountrySearch(Resource):
    country_model = country.model(
        "Countries Model",
        {
            "countries_pk": fields.Integer(required=True, description="country key"),
            "name": fields.String(
                required=True, max_length=145, description="country name"
            ),
            "abbreviation": fields.String(
                required=True, max_length=3, description="country name"
            ),
            "active": fields.Boolean(
                required=True, description="country is visible for users?"
            ),
        },
    )

    retorno_model = country.model(
        "Search country Model",
        {
            "countries": fields.List(fields.Nested(country_model)),
        },
    )

    parser = country.parser()
    parser.add_argument("name", type=str, required=False)
    parser.add_argument("abbreviation", type=str, required=False)
    parser.add_argument("active", type=boolean_string, required=False, default=True)

    @jwt_required()
    @country.expect(parser)
    # @country.marshal_with(retorno_model)
    def get(self):
        CAMPOS = [
            "countries_pk",
            "name",
            "abbreviation",
            "active",
        ]

        dados = self.parser.parse_args()

        query = """SELECT 
            countries_pk, 
            name, 
            abbreviation,
            active FROM countries """
        query_params = []

        where = False

        if dados["name"]:
            name = dados["name"]
            query += "WHERE name LIKE %s"
            query_params.append(f"%{name}%")
            where = True

        if dados["abbreviation"]:
            if where:
                query += "AND abbreviation = %s "
            else:
                query += "WHERE abbreviation = %s "
                where = True

            query_params.append(dados["abbreviation"])

        if where:
            query += "AND active = %s "
        else:
            query += "WHERE active = %s "

        query_params.append(dados["active"])

        # return {
        #     "query": query,
        #     "params": query_params,
        # }

        conn = MySQLConnection()
        resultado = conn.execute(query, tuple(query_params))

        countries = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                countries.append(aux_dict.copy())

        else:
            return {"message": "None countrie found with the required filters."}, 404

        retorno = {
            "countries": countries,
        }

        return marshal(retorno, self.retorno_model), 200


@country.route("/<int:countries_pk>")
class countryGet(Resource):

    @jwt_required()
    def get(self, countries_pk):
        country = CountriesModel.find_country(countries_pk)

        if country:
            return country.json(), 200

        return {"message": "country not found."}, 404  # not found


@country.route("/<int:countries_pk>/delete/")
class countryDelete(Resource):

    @jwt_required()
    def delete(self, countries_pk):
        try:
            country = CountriesModel.find_country(countries_pk)
            if country:
                country.delete_country()
                return {"message": "country successfully deleted"}, 200
            return {"message": "country not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
