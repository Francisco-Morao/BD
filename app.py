#!/usr/bin/python3
# Copyright (c) BDist Development Team
# Distributed under the terms of the Modified BSD License.
import os
from logging.config import dictConfig

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from psycopg.rows import namedtuple_row
from psycopg_pool import ConnectionPool

# Use the DATABASE_URL environment variable if it exists, otherwise use the default.
# Use the format postgres://username:password@hostname/database_name to connect to the database.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://saude:saude@postgres/saude")

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    kwargs={
        "autocommit": True,  # If True don’t start transactions automatically.
        "row_factory": namedtuple_row,
    },
    min_size=4,
    max_size=10,
    open=True,
    # check=ConnectionPool.check_connection,
    name="postgres_pool",
    timeout=5,
)

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)s - %(funcName)20s(): %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

app = Flask(__name__)
app.config.from_prefixed_env()
log = app.logger


def confirma_nif_medico(nif):

    if len(nif) != 9 or not nif.isdigit():
        return False

    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            result = cur.execute(
                """
                SELECT 1
                FROM medico
                WHERE nif = %(nif)s;
                """,
                {"nif": nif},
            ).fetchone()
    
    # Retorna True se o nif foi encontrado
    return result is not None

def confirma_ssn_paciente(ssn):
        
    if len(ssn) != 11 or not ssn.isdigit():
        return False

    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            result = cur.execute(
                """
                SELECT 1
                FROM paciente
                WHERE ssn = %(ssn)s;
                """,
                {"ssn": ssn},
            ).fetchone()
    
    # Retorna True se o ssn foi encontrado
    return result is not None


def confirma_data(data):
    try:
        data_obj = datetime.strptime(data, "%Y-%m-%d")
        
        if data_obj.year in [2023, 2024]:
            return True
        else:
            return False
    except ValueError:
        return False

def confirma_hora(hora):
    try:
        # Converte a string de hora para um objeto datetime
        hora_obj = datetime.strptime(hora, "%H:%M:%S")
        return True
    except ValueError:
        # Se a conversão falhar, a hora é inválida
        return False


@app.route("/", methods=("GET",))
def clinicas_view():
    """Lista todas as clínicas (nome e morada)."""

    with psycopg.connection(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            clinicas = cur.execute(
                """
                SELECT nome, morada
                FROM clinica;
                """,{},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    return jsonify(clinicas)


@app.route("/c/<clinica>/", methods=("GET",))
def clinica_especialidade_view(clinica):
    """Lista todas as especialidades oferecidas na <clinica>."""

    with psycopg.connection(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            especialidades = cur.execute(
                """
                SELECT DISTINCT m.especialidade
                FROM  medico m
                JOIN 
                    trabalha t ON m.nif = t.nif
                JOIN 
                    clinica c ON t.nome = c.nome
                WHERE c.nome = %(clinica)s;
                """,
                {"clinica": clinica},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    if especialidades:
        return jsonify([e.especialidade for e in especialidades])
    else:
        return jsonify({"Erro": "Nao existem especialidades para a clinica."}), 400


@app.route("/c/<clinica>/<especialidade>/", methods=("GET",))
def medicos_na_clinica(clinica,especialidade):
    """Lista todos os médicos (nome) da <especialidade> que trabalham na <clínica> 
    e os primeiros três horários disponíveis para consulta de cada um deles (data e hora)."""
    with psycopg.connection(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            medicos = cur.execute(
                    """ 
                    WITH medico_horarios_disponiveis AS (
                        SELECT
                            m.nif, 
                            m.nome AS medico, 
                            c.data, 
                            t.hora,
                            ROW_NUMBER() OVER (PARTITION BY m.nif ORDER BY c.data, c.hora) AS row_num
                        FROM 
                            medico m 
                        JOIN consulta c ON m.nif = c.nif
                        JOIN tempo t ON t.data = c.data
                        WHERE 
                            m.especialidade = %(especialidade)s AND
                            c.nome = %(clinica)s AND
                            c.data > CURRENT_DATE AND 
                            t.hora <> c.hora
                        ORDER BY c.nif, c.data, c.hora
                    )
                    SELECT 
                        nif,
                        medico,
                        data,
                        hora
                    FROM 
                        medico_horarios_disponiveis
                    WHERE 
                        row_num <= 3;
                        """,
                    {"clinica": clinica, "especialidade": especialidade},
                ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

        if medicos:
            return jsonify([medico.nome for medico in medicos])
        else:
            return jsonify({"Erro": "Nao existem especialidades para a clinica ou nenhum medico tem vagas disponiveis"}), 400


@app.route("/a/<clinica>/registar/", methods=("POST",))
def registar(clinica):
    """Registra uma marcação de consulta na <clinica> na base de dados."""

    paciente_ssn = request.args.get("ssn paciente")
    medico_nif = request.args.get("nif medico")
    data = request.args.get("data")
    hora = request.args.get("hora")

    error = None

    if not paciente_ssn or not medico_nif or not data or not hora:
        error = "Data missing."
    if not confirma_ssn_paciente(paciente_ssn):
        error = "SSN doesn't exist." 
    if not confirma_nif_medico(medico_nif):
        error = "Nif doesn't exist."
    if not confirma_data(data):
        error = "Date doesn't exist."
    if not confirma_hora(hora):
        error = "Hour doesn't exist."

    if error is not None:
        return jsonify({"error": error}), 400
    else:
        with psycopg.connection(conninfo=DATABASE_URL) as conn:
            with conn.cursor(row_factory=namedtuple_row) as cur:
                cur.execute(
                    """
                    INSERT INTO consulta (id, ssn, nif, clinica.nome, data, hora, codigo_sns)
                    VALUES (%s, %s, %s, %s);
                    FROM clinica
                    WHERE clinica.nome = %(clinica)s;
                    """,
                    {"clinica": clinica, "ssn" : paciente_ssn, "nif" : medico_nif, "data": data, "hora": hora},
                )
            conn.commit()
    return "", 204


@app.route("/a/<clinica>/cancelar/", methods=("DELETE",))
def cancelar_marcacao(clinica):
    """Cancela uma marcação de consulta que ainda não se realizou na <clinica>, 
    removendo a entrada da respectiva tabela na base de dados.
     removendo a entrada da respectiva tabela na
    base de dados. Recebe como argumentos um paciente, um
    médico, e uma data e hora"""

    paciente_ssn = request.args.get("ssn paciente")
    medico_nif = request.args.get("nif medico")
    data = request.args.get("data")
    hora = request.args.get("hora")

    error = None

    if not paciente_ssn or not medico_nif or not data or not hora:
        error = "Data missing."
    if not confirma_ssn_paciente(paciente_ssn):
        error = "SSN doesn't exist."
    if not confirma_nif_medico(medico_nif):
        error = "Nif doesn't exist."
    if not confirma_data(data):
        error = "Date doesn't exist."
    if not confirma_hora(hora):
        error = "Hour doesn't exist."
    if error is not None:
        return error, 400

    with psycopg.connection(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                    """
                    DELETE FROM consulta
                    WHERE 
                        clinica.nome = %(clinica)s AND 
                        paciente.ssn = %(ssn)s AND 
                        medico.nif = %(nif)s AND 
                        consulta.data = %(data)s AND 
                        consulta.hora = %(hora)s;
                    """,
                    {"clinica": clinica, "ssn_paciente": paciente_ssn, "nif_medico": medico_nif, "data": data, "hora": hora,}
                )
            conn.commit()
        conn.commit()

    return "", 204


if __name__ == "__main__":
    app.run()