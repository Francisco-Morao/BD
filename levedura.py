from faker import Faker
import random
from unidecode import unidecode
from datetime import datetime, timedelta, time
import string


# Create a Faker instance
fake = Faker('pt_PT') 

# List of neighborhoods/districts within Lisbon
lisbon_neighborhoods = ["Odivelas", "Sintra", "Lisboa", "Amadora"]

def clean_text(text):
    text = unidecode(text)  # Remove accents and other diacritics
    text = ''.join(e for e in text if e.isalnum() or e.isspace())  # Keep alphanumeric and space characters only
    return text

# Function to generate random clinic data
def generate_clinic_data(num_entries):
    clinic_data = []
    for _ in range(num_entries):
        nome = fake.company()
        telefone = fake.unique.numerify(text='#########')  
        morada = f'{fake.street_name()}, {fake.building_number()} {fake.postcode()}, {fake.random_element(lisbon_neighborhoods)}'
        clinic_data.append((nome, telefone, morada))
    return clinic_data


# Function to generate random nurse data for a given clinic
def generate_nurse_data(clinic_name, num_nurses):
    nurse_data = []
    for _ in range(num_nurses):
        nif = fake.unique.numerify(text='#########')  # Generates a 9-digit number
        nome = fake.unique.name()
        telefone = fake.unique.numerify(text='#########') 
        morada = f'{fake.street_name()}, {fake.building_number()} {fake.postcode()}, {fake.random_element(lisbon_neighborhoods)},  Lisboa'
        nurse_data.append((nif, nome, telefone, morada, clinic_name))
    return nurse_data


# Function to generate random doctor data
def generate_doctor_data(num_doctors):
    # List of specialities
    specialities = ["cardiologia", "dermatologia", "ortopedia", "pediatria", "ginecologia"]
    doctor_data = []
    for i in range(num_doctors):
        nif = fake.unique.numerify(text='#########')  # Generates a 9-digit number
        nome = fake.unique.name()
        telefone = fake.unique.numerify(text='#########') 
        morada = f'{fake.street_name()}, {fake.building_number()} {fake.postcode()}, {fake.random_element(lisbon_neighborhoods)}, Lisboa'
        if i < 20:
            especialidade = "clínica geral"
        else:
            especialidade = fake.random_element(specialities)
        doctor_data.append((nif, nome, telefone, morada, especialidade))
    return doctor_data

    
# Generate work schedule for doctors in clinics
def generate_works_data(medicos, clinicas):
    trabalha = []

    clinicas_medicos = {clinica[0]: [] for clinica in clinicas}
    medico_clinicas = {medico[0]: set() for medico in medicos}

    # Ensure each doctor works in at least two clinics
    for medico in medicos:
        clinicas_selecionadas = random.sample(clinicas, 2)
        for clinica in clinicas_selecionadas:
            clinicas_medicos[clinica[0]].append(medico[0])
            medico_clinicas[medico[0]].add(clinica[0])

    # Ensure each clinic has at least 8 doctors
    for clinica in clinicas:
        while len(clinicas_medicos[clinica[0]]) < 8:
            medico = random.choice(medicos)[0]
            if clinica[0] not in medico_clinicas[medico]:
                clinicas_medicos[clinica[0]].append(medico)
                medico_clinicas[medico].add(clinica[0])

    # Assign workdays for doctors in each clinic
    for clinica, medicos_clinica in clinicas_medicos.items():
        for dia in range(0, 7):  # Sunday = 0
            assigned_medicos = []
            while len(assigned_medicos) < 8:
                medico = random.choice(medicos_clinica)
                if not any(item[0] == medico and item[2] == dia for item in trabalha):
                    assigned_medicos.append(medico)
                    trabalha.append((medico, clinica, dia))

    return trabalha

def generate_patient_data(num_entries):
    pacientes = []
    for _ in range(num_entries):
        ssn = fake.unique.bothify(text='###########')
        nif = fake.unique.bothify(text='#########')
        nome = fake.name()
        telefone = fake.unique.bothify(text='###########')
        morada = fake.address().replace('\n', ', ')
        data_nasc = fake.date_of_birth(minimum_age=0, maximum_age=100).strftime('%Y-%m-%d')
        pacientes.append((ssn, nif, clean_text(nome), telefone, clean_text(morada), data_nasc))
    return pacientes


def generate_time():
    possible_hours_morning = list(range(8, 13))  # 08:00 to 12:30
    possible_hours_afternoon = list(range(14, 19))  # 14:00 to 18:30
    possible_minutes = [0, 30]  # Minutes can be 00 or 30

    if random.choice([True, False]):
        hour = random.choice(possible_hours_morning)
    else:
        hour = random.choice(possible_hours_afternoon)
    
    minute = random.choice(possible_minutes)
    return time(hour, minute, 0)  # Hours, minutes, and seconds set to 00

def generate_codigo_sns():
    return ''.join(random.choices(string.digits, k=12))


def generate_receitas(consultas, prob_receita=0.8):
    receitas = []
    unique_receitas = []

    for consulta in consultas:
        if random.random() < prob_receita:
            num_meds = random.randint(1, 6) 
            for _ in range(num_meds):
                med = f'Medicamento {random.randint(1, 100)}'
                while ((consulta[6], med) in unique_receitas): # (codigo sns, med) is primary key
                    med = f'Medicamento {random.randint(1, 100)}'

                receita = (consulta[6], med, random.randint(1, 3))
                receitas.append(receita)
                unique_receitas.append((consulta[6], med))

    return receitas


def generate_observacoes(consultas):
    observacoes_sintomas = []
    observacoes_metricas = []
    sintomas = [f'Sintoma{i}' for i in range(1, 51)]
    metricas = [f'Metrica{i}' for i in range(1, 21)]
    
    # Set to keep track of unique observations
    unique_observacoes = set()

    for consulta in consultas:
        num_sintomas = random.randint(1, 5)
        num_metricas = random.randint(0, 3)
        parametros_sintomas = random.sample(sintomas, num_sintomas)
        parametros_metricas = random.sample(metricas, num_metricas)

        for parametro in parametros_sintomas:
            observation = (consulta[0], clean_text(parametro))
            if observation not in unique_observacoes:
                observacoes_sintomas.append(observation)
                unique_observacoes.add(observation)

        for parametro in parametros_metricas:
            observation = (consulta[0], clean_text(parametro), random.uniform(1.0, 100.0))
            if observation not in unique_observacoes:
                observacoes_metricas.append(observation)
                unique_observacoes.add(observation)

    return observacoes_sintomas , observacoes_metricas

# Function to generate consultations and prescriptions
def gerar_consultas_receitas(pacientes, medicos, clinicas, start_date, end_date, trabalha):
    consultas = []
    receitas = []
    consulta_id = 1

    delta_days = (end_date - start_date).days
    patient_schedule = {p[0]: set() for p in pacientes}  # Dictionary to track each patient's schedule
    doctor_schedule = {m[0]: set() for m in medicos}  # Dictionary to track each doctor's schedule
    unique_receitas = set()
    paciente_especifico = pacientes[0]

    for day_offset in range(delta_days + 1):
        data = (start_date + timedelta(days=day_offset)).date()

        # weekday --> monday = 0, sunday = 6

        # isoweekday --> monday = 1, sunday = 7
        # we want sunday = 0, monday = 1, ... saturday = 6
        
        day_of_week = (data.isoweekday()) % 7 # sunday = 0, monday = 1
        for clinica in clinicas:
            consultas_por_clinica = 0
            
            # Seleciona médicos disponíveis para a clínica e o dia da semana
            medicos_disponiveis = [t[0] for t in trabalha if t[1] == clinica[0] and t[2] == day_of_week]
            # if not medicos_disponiveis:
            #     continue  # Continue para a próxima clínica se não houver médicos disponíveis

            while consultas_por_clinica < 20:
                for medico in medicos_disponiveis:
                    consultas_por_medico = 0

                    while consultas_por_medico < 2:

                        hora = generate_time()  # Gera um horário dentro dos intervalos especificados
                        paciente_disponiveis = [p for p in pacientes if (data, hora) not in patient_schedule[p[0]]]

                        paciente = random.choice(paciente_disponiveis)

                        # Pula se o médico já tiver uma consulta neste horário
                        # Pula se o paciente for o mesmo que o médico
                            
                        if paciente[0] == medico[0] or (data, hora) in doctor_schedule[medico]:  
                            continue

                        # Adiciona a nova consulta aos agendamentos
                        patient_schedule[paciente[0]].add((data, hora))
                        doctor_schedule[medico].add((data, hora))

                        codigo_sns = fake.unique.bothify(text='############')
                        consultas.append((consulta_id, paciente[0], medico, clinica[0], data.strftime('%Y-%m-%d'), hora.strftime('%H:%M:%S'), codigo_sns))

                        # ~80% das consultas têm receita
                        if random.random() < 0.8:
                            num_meds = random.randint(1, 6)
                            for _ in range(num_meds):
                                med = f'Medicamento {random.randint(1, 100)}'
                                while ((codigo_sns, med) in unique_receitas): # (codigo sns, med) is primary key
                                    med = f'Medicamento {random.randint(1, 100)}'
                                quantidade = random.randint(1, 3)
                                # Verifica se a receita já foi prescrita para este paciente nesta consulta
                                if (codigo_sns, med) not in unique_receitas:
                                    unique_receitas.add((codigo_sns, med))
                                    receitas.append((codigo_sns, med, quantidade))

                        consulta_id += 1
                        consultas_por_clinica += 1
                        consultas_por_medico += 1

                        if consultas_por_medico >= 2:
                            break

                if consultas_por_clinica >= 20:
                    break

    for paciente in pacientes:
        if not any(paciente[0] == consulta[1] for consulta in consultas): # if paciente doesnt have any consulta yet
            consulta_date = start_date + timedelta(days=random.randint(0, delta_days))
            day_of_week = (data.isoweekday()) % 7
            hora = generate_time()

            # Filtra trabalha por dia da semana
            trabalha_dia = []
            for item in trabalha:
                if item[2] == day_of_week and item not in trabalha_dia:
                    trabalha_dia.append(item)
            
            # Seleciona um trabalha aleatório
            trabalha_item = random.choice(trabalha_dia)
            medico = trabalha_item[0]

            while paciente[0] == medico or ((consulta_date, hora) in patient_schedule[paciente[0]]) \
                or ((consulta_date, hora) in doctor_schedule[medico]):
                trabalha_item = random.choice(trabalha_dia)
                medico = trabalha_item[0]
                hora = generate_time()

            patient_schedule[paciente[0]].add((consulta_date, hora))
            doctor_schedule[medico].add((consulta_date, hora))

            consulta = (len(consultas) + 1, paciente[0], medico[0], trabalha_item[1],
                        consulta_date.strftime('%Y-%m-%d'), time.strftime('%H:%M:%S'), generate_codigo_sns())
    
            consultas.append(consulta)
    
    return consultas, receitas




fgit status



def main():
    num_clinics = 5 
    clinic_data = generate_clinic_data(num_clinics)
    print("INSERT INTO clinica VALUES", ",".join(str(clinic) for clinic in clinic_data) + ";")

    num_patients = 5000
    patients = generate_patient_data(num_patients)
    print("INSERT INTO paciente VALUES", ",".join(str(patient) for patient in patients) + ";")

    nurse_data_all = []
    for clinic in clinic_data:
        clinic_name = clinic[0]
        num_nurses = fake.random_int(min=5, max=6)
        nurse_data = generate_nurse_data(clinic_name, num_nurses)
        nurse_data_all.extend(nurse_data)
    print("INSERT INTO enfermeiro VALUES", ",".join(str(nurse) for nurse in nurse_data_all) + ";")

    num_doctors = 60
    doctor_data = generate_doctor_data(num_doctors)
    print("INSERT INTO medico VALUES", ",".join(str(doctor) for doctor in doctor_data) + ";")

    works_data = generate_works_data(doctor_data, clinic_data)
    print("INSERT INTO trabalha VALUES", ",".join(str(work) for work in works_data) + ";")

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    consultas, receitas =  gerar_consultas_receitas(patients, doctor_data, clinic_data, start_date, end_date, works_data)
    observacoes_sintomas, observacoes_metricas = generate_observacoes(consultas)
    # Define uma função para imprimir uma lista de consultas
    def print_consultas(consultas):
        print("INSERT INTO consulta VALUES ", end="")
        print(",".join(str(consulta) for consulta in consultas) + ";")

    # Imprime as consultas divididas em blocos de 10000 registros
    for i in range(0, len(consultas), 20000):
        print_consultas(consultas[i:i+20000])

    # Define uma função para imprimir uma lista de receitas
    def print_receitas(receitas):
        print("INSERT INTO receita VALUES ", end="")
        print(",".join(str(receita) for receita in receitas) + ";")

    # Imprime as receitas divididas em blocos de 10000 registros
    for i in range(0, len(receitas), 20000):
        print_receitas(receitas[i:i+20000])

    # Imprime as observações
    def print_observacoes_sintomas(observacoes):
        print("INSERT INTO observacao (id, parametro) VALUES ", end="")
        print(",".join(str(observacao) for observacao in observacoes) + ";")

    def print_observacoes_metricas(observacoes):
        print("INSERT INTO observacao (id, parametro, valor) VALUES ", end="")
        print(",".join(str(observacao) for observacao in observacoes) + ";")

    # Imprime as observações divididas em blocos de 10000 registros
    for i in range(0, len(observacoes_sintomas), 20000):
        print_observacoes_sintomas(observacoes_sintomas[i:i+20000])
    for i in range(0, len(observacoes_metricas), 20000):
        print_observacoes_metricas(observacoes_metricas[i:i+20000])


    tart_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)

    tempo_data = generate_tempo_data(start_date, end_date)

    def print_tempo_data(tempo_data, chunk_size=20000):
        def print_chunk(chunk):
            print("INSERT INTO tempo (data, hora) VALUES ", end="")
            print(",".join(f"('{date}', '{time}')" for date, time in chunk) + ";")

        for i in range(0, len(tempo_data), chunk_size):
            print_chunk(tempo_data[i:i+chunk_size])

    print_tempo_data(tempo_data)

if __name__ == "__main__":
    main()