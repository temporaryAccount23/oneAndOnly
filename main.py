import sys
import json
import psycopg2
from flask import Flask, request, jsonify, make_response
from dijkstar import Graph, find_path

# for dfs

app = Flask(__name__)


@app.route("/planets", methods=["GET", "POST"])
def planets():

    if request.method == "GET":

        list_of_planets = database_execute("SELECT * FROM planet", None, fetchOne=False)

        if list_of_planets is None:
            response = make_response(jsonify(list()), 200)
            response.headers["Content-Type"] = "application/json"
            return response

        ret_val = list()
        for tpl in list_of_planets:
            tmp = dict()
            tmp["id"] = tpl[0]
            tmp["name"] = tpl[1]
            ret_val.append(tmp)

        response = make_response(jsonify(ret_val), 200)
        response.headers["Content-Type"] = "application/json"
        return response

    elif request.method == "POST":

        received_data = json.loads(request.data)
        planet_name = received_data["name"]
        planet_id = received_data["id"]
        if planet_id is not None:
            response = make_response(jsonify("Error"), 422)
            response.headers["Content-Type"] = "application/json"
            return response

        # into db

        planet = database_execute("insert into planet(id, name) values(default, %s) returning (id, name)", [planet_name], fetchOne=True)

        tmp_dict = dict()
        tmp_dict["id"] = int(planet[0])
        tmp_dict["name"] = planet_name[1]

        response = make_response(jsonify(tmp_dict), 200)
        response.headers["Content-Type"] = "application/json"
        return response

    else:
        make_response(jsonify("Error"), 422)


@app.route("/connections", methods=["GET", "POST"])
def connections():

    if request.method == "GET":

        list_of_connections = database_execute("SELECT id, price, from_planet_id, to_planet_id FROM connection", None, fetchOne=False)

        if list_of_connections is None:
            response = make_response(jsonify(list()), 200)
            response.headers["Content-Type"] = "application/json"
            return response

        ret_val = list()
        for tpl in list_of_connections:
            tmp = dict()
            tmp["id"] = tpl[0]
            tmp["from_planet_id"] = str(tpl[2])
            tmp["to_planet_id"] = str(tpl[3])
            tmp["price"] = str(tpl[1])
            ret_val.append(tmp)

        response = make_response(jsonify(ret_val), 200)
        response.headers["Content-Type"] = "application/json"
        return response

    elif request.method == "POST":

        received_data = json.loads(request.data)
        from_planet_id = received_data["from_planet_id"]
        to_planet_id = received_data["to_planet_id"]
        price = received_data["price"]

        if price is None or price < 0 or from_planet_id is None or to_planet_id is None:
            return make_response(jsonify("Error"), 422)

        # check if from and to are valid
        to_planet = database_execute("SELECT id from planet where id = %d", [to_planet_id], True)
        if to_planet is None:
            return make_response(jsonify("Error"), 404)
        from_planet = database_execute("SELECT id from planet where id = %d", [from_planet_id], True)
        if from_planet is None:
            return make_response(jsonify("Error"), 404)

        # into db
        connection = database_execute("INSERT INTO connection(id, price, from_planet_id, to_planet_id) VALUES (default, %d, %d, %d) RETURNING (id, price, from_planet_id, to_planet_id)", [price, from_planet_id, to_planet_id], fetchOne=True)

        ret_val = dict()
        ret_val["id"] = connection[0]
        ret_val["price"] = connection[1]
        ret_val["from_planet_id"] = connection[2]
        ret_val["to_planet_id"] = connection[3]

        response = make_response(jsonify(ret_val), 200)
        response.headers["Content-Type"] = "application/json"
        return response

    else:
        make_response(jsonify("Error"), 422)


@app.route("/bookings/inquiry/<int:fromPlanet>/<int:toPlanet>", methods=["GET"])
def bookings(fromPlanet: int, toPlanet: int):

    # TODO: check if planets exist

    if request.method != "GET":
        return make_response(jsonify("Error"), 422)

    connection_list = database_execute("SELECT price, from_planet_id, to_planet_id FROM connection", None, fetchOne=False)

    if connection_list is None:
        response = make_response(jsonify(list()), 200)
        response.headers["Content-Type"] = "application/json"
        return response

    graph = Graph()
    for connection in connection_list:
        graph.add_edge(connection[0], connection[1], connection[2])

    try:
        path = find_path(graph, fromPlanet, toPlanet)
    except Exception as e:
        response = make_response(jsonify(" "), 409)
        response.headers["Content-Type"] = "application/json"
        return response

    ret_val = dict()
    ret_val["total_price"] = path.total_cost
    ret_val["used_connections"]

    # todo: get corresponding conn


def database_execute(script: str, parameters: list or None, fetchOne: bool):

    hostname = "localhost"
    database = "ase"
    username = "ase"
    pwd = "ase"
    port_id = 5432

    try:
        conn = psycopg2.connect(
            host=hostname,
            dbname=database,
            user=username,
            password=pwd,
            port=port_id
        )

        cur = conn.cursor()
        if parameters is None:
            cur.execute(script)
        else:
            cur.execute(script, parameters)

        if fetchOne:
            ret_val = cur.fetchone()
        else:
            ret_val = cur.fetchall()

        if ret_val is None:
            cur.close()
            conn.close()
            return None


        cur.close()
        conn.close()
        return ret_val

    except Exception as error:
        print(error)
        sys.exit(1)




if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
