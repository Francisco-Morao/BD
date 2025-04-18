#!/usr/bin/python3
# Copyright (c) BDist Development Team
# Distributed under the terms of the Modified BSD License.
import os
from logging.config import dictConfig
from datetime import datetime
import string
import psycopg
from flask import Flask, jsonify, request
from psycopg.rows import namedtuple_row
import random

# Use the DATABASE_URL environment variable if it exists, otherwise use the default.
# Use the format postgres://username:password@hostname/database_name to connect to the database.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://saude:saude@postgres/saude")

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
                '''
                SELECT 1
                FROM consulta
                WHERE nif = %(nif)s;
                ''',
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
                '''
                SELECT 1
                FROM consulta
                WHERE ssn = %(ssn)s;
                ''',
                {"ssn": ssn},
            ).fetchone()
    
    # Retorna True se o ssn foi encontrado
    #retorn true se o result for 1
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
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            clinicas = cur.execute(
                '''
                SELECT nome, morada
                FROM clinica;
                ''',
                {},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    return jsonify(clinicas)


@app.route("/c/<clinica>/", methods=("GET",))
def clinica_especialidade_view(clinica):
    """Lista todas as especialidades oferecidas na <clinica>."""

    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            especialidades = cur.execute(
                '''
                SELECT DISTINCT m.especialidade
                FROM  medico m
                JOIN 
                    trabalha t ON m.nif = t.nif
                JOIN 
                    clinica c ON t.nome = c.nome
                WHERE c.nome = %(clinica)s;
                ''',
                {"clinica": clinica},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    if especialidades:
        return jsonify([e.especialidade for e in especialidades])
    else:
        return jsonify({"Erro": "Nao existem especialidades para a clinica."}), 400



@app.route("/c/<clinica>/<especialidade>/", methods=("GET",))
def medicos_na_clinica(clinica, especialidade):
    """Lista todos os médicos (nome) da <especialidade> que trabalham na <clínica> 
    e os primeiros três horários disponíveis para consulta de cada um deles (data e hora)."""
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            medicos = cur.execute(
                ''' 
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
                ''',
                {"clinica": clinica, "especialidade": especialidade},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    if medicos:
        medicos_list = [
            {
                "nif": medico.nif,
                "medico": medico.medico,
                "data": medico.data.isoformat(),
                "hora": medico.hora.strftime("%H:%M:%S")
            }
            for medico in medicos
        ]
        return jsonify(medicos_list)
    else:
        return jsonify({"Erro": "Não existem especialidades para a clínica ou nenhum médico tem vagas disponíveis"}), 400


def gerar_codigo_sns():

    while True:
        codigo_sns = ''.join(random.choices(string.digits, k=12))
        #comfirmar se existe ou nao
        with psycopg.connect(conninfo=DATABASE_URL) as conn:
            with conn.cursor(row_factory=namedtuple_row) as cur:
                testcodigo_sns = cur.execute(
                    '''
                    SELECT 1
                    FROM consulta
                    WHERE codigo_sns = %(codigo_sns)s;
                    ''',
                    {"codigo_sns": codigo_sns},
                ).fetchone()
        if testcodigo_sns is None:
            break
    return codigo_sns

def gerar_codigo_sns():

    while True:
        codigo_sns = ''.join(random.choices(string.digits, k=12))
        #confirmar se existe ou nao
        with psycopg.connect(conninfo=DATABASE_URL) as conn:
            with conn.cursor(row_factory=namedtuple_row) as cur:
                testcodigo_sns = cur.execute(
                    '''
                    SELECT 1
                    FROM consulta
                    WHERE codigo_sns = %(codigo_sns)s;
                    ''',
                    {"codigo_sns": codigo_sns},
                ).fetchone()
        if testcodigo_sns is None:
            break
    return codigo_sns


@app.route("/a/<clinica>/registar/", methods=("POST",))
def registar(clinica):
    """Registra uma marcação de consulta na <clinica> na base de dados."""
    paciente_ssn = request.json.get("ssn paciente")
    medico_nif = request.json.get("nif medico")
    data = request.json.get("data")
    hora = request.json.get("hora")
    codigo_sns = gerar_codigo_sns()
    error = None

    if not paciente_ssn or not medico_nif or not data or not hora or not codigo_sns:
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
        with psycopg.connect(conninfo=DATABASE_URL) as conn:
            try:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    cur.execute(
                        '''
                        SELECT COALESCE(MAX(id), 0) + 1 AS new_id
                        FROM consulta;
                        '''
                    )
                    new_id = cur.fetchone().new_id
                    cur.execute(
                        '''
                        INSERT INTO consulta (id, ssn, nif, nome, data, hora, codigo_sns)
                        VALUES (%(id)s, %(ssn)s, %(nif)s, %(clinica_nome)s, %(data)s, %(hora)s, %(codigo_sns)s);
                        ''',
                        {
                            "id": new_id, "ssn": paciente_ssn, "nif": medico_nif, "clinica_nome": clinica, \
                            "data": data, "hora": hora, "codigo_sns": codigo_sns
                        }
                    )
                conn.commit()
            except :
                return jsonify({"erro": "Não foi possível marcar consulta"})
    return jsonify({"Status": "Sucess"})


@app.route("/a/<clinica>/cancelar/", methods=("POST",))
def cancelar_marcacao(clinica):
    """Cancela uma marcação de consulta que ainda não se realizou na <clinica>, 
    removendo a entrada da respectiva tabela na base de dados.
     removendo a entrada da respectiva tabela na
    base de dados. Recebe como argumentos um paciente, um
    médico, e uma data e hora"""

    paciente_ssn = request.json.get("ssn paciente")
    medico_nif = request.json.get("nif medico")
    data = request.json.get("data")
    hora = request.json.get("hora")

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

    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                    '''
                    DELETE 
                    FROM consulta
                    WHERE 
                        nome = %(clinica)s AND 
                        ssn = %(ssn)s AND 
                        nif = %(nif)s AND 
                        data = %(data)s AND 
                        hora = %(hora)s
                    ''',
                    {"clinica": clinica, "ssn": paciente_ssn, "nif": medico_nif, "data": data, "hora": hora}
                )
            deleted_count = cur.rowcount
            conn.commit()
            
    if deleted_count :
        return jsonify({"Status": "Success"}), 200
    else:
        return jsonify({"error": "Não existe consulta"}), 400

if __name__ == "__main__":
    app.run()