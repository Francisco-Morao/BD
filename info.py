from faker import Faker
import random
from unidecode import unidecode
from datetime import datetime, timedelta, time

# Gerador de dados
fake = Faker('pt_PT')

# Função para remover caracteres especiais
def clean_text(text):
    text = unidecode(text)  # Remove accents and other diacritics
    text = ''.join(e for e in text if e.isalnum() or e.isspace())  # Keep alphanumeric and space characters only
    return text

# Função para gerar clínicas
def gerar_clinicas():
    localidades = ['Lisboa', 'Cascais', 'Sintra', 'Amadora']
    clinicas = []
    for i in range(5):
        nome = f'Clinica{i+1}'
        telefone = fake.unique.bothify(text='###########')
        morada_base = fake.address().replace('\n', ', ')
        localidade = random.choice(localidades)
        morada_base = clean_text(morada_base)
        morada = f"{morada_base}, {localidade}"
        clinicas.append((clean_text(nome), telefone, morada))
    return clinicas

# Função para gerar enfermeiros
def gerar_enfermeiros(clinicas):
    enfermeiros = []
    for clinica in clinicas:
        num_enfermeiros = random.randint(5, 6)  # Randomly select 5 or 6 nurses for each clinic
        for _ in range(num_enfermeiros):
            nif = fake.unique.bothify(text='#########')
            nome = fake.unique.name()
            telefone = fake.unique.bothify(text='###########')
            morada = fake.address().replace('\n', ', ')
            nome_clinica = clinica[0]
            enfermeiros.append((nif, clean_text(nome), telefone, clean_text(morada), clean_text(nome_clinica)))
    return enfermeiros

# Função para gerar médicos
def gerar_medicos():
    especialidades = ['ClinicaGeral', 'Ortopedia', 'Cardiologia', 'Dermatologia', 'Pediatria']
    medicos = []

    for _ in range(20):
        nif = fake.unique.bothify(text='#########')
        nome = fake.unique.name()
        telefone = fake.unique.bothify(text='###########')
        morada = fake.address().replace('\n', ', ')
        especialidade = 'ClinicaGeral'
        medicos.append((nif, clean_text(nome), telefone, clean_text(morada), especialidade))

    for _ in range(20):
        nif = fake.unique.bothify(text='#########')
        nome = fake.unique.name()
        telefone = fake.unique.bothify(text='###########')
        morada = fake.address().replace('\n', ', ')
        especialidade = random.choice(especialidades[1:3])
        medicos.append((nif, clean_text(nome), telefone, clean_text(morada), clean_text(especialidade)))
    for _ in range(20):
        nif = fake.unique.bothify(text='#########')
        nome = fake.unique.name()
        telefone = fake.unique.bothify(text='###########')
        morada = fake.address().replace('\n', ', ')
        especialidade = random.choice(especialidades[3:4])
        medicos.append((nif, clean_text(nome), telefone, clean_text(morada), clean_text(especialidade)))

    return medicos

# Função para gerar dados de pacientes
def gerar_pacientes(num_pacientes):
    pacientes = []
    for _ in range(num_pacientes):
        ssn = fake.unique.bothify(text='###########')
        nif = fake.unique.bothify(text='#########')
        nome = fake.name()
        telefone = fake.unique.bothify(text='###########')
        morada = fake.address().replace('\n', ', ')
        data_nasc = fake.date_of_birth(minimum_age=0, maximum_age=100)
        pacientes.append((ssn, nif, clean_text(nome), telefone, clean_text(morada), data_nasc))
    return pacientes

# Função para garantir que cada clínica tenha pelo menos 8 médicos por dia
def distribuir_medicos(medicos, clinicas):
    clinicas_medicos = {clinica[0]: [] for clinica in clinicas}
    medico_clinicas = {medico[0]: set() for medico in medicos}

    # Ensure each doctor works in at least two clinics
    for medico in medicos:
        clinicas_selecionadas = random.sample(clinicas, 2)
        for clinica in clinicas_selecionadas:
            # Check if the doctor is already assigned to work on the same day in another clinic
            if not any((medico[0], clinica[0]) in clinicas_medicos[other_clinica] for other_clinica in clinicas_medicos.keys()):
                clinicas_medicos[clinica[0]].append(medico[0])
                medico_clinicas[medico[0]].add(clinica[0])

    # Ensure each clinic has at least 8 doctors
    for clinica in clinicas:
        while len(clinicas_medicos[clinica[0]]) < 8:
            medico = random.choice(medicos)[0]
            # Check if the doctor is already assigned to work in another clinic
            if not any((medico, clinica[0]) in clinicas_medicos[other_clinica] for other_clinica in clinicas_medicos.keys()):
                clinicas_medicos[clinica[0]].append(medico)
                medico_clinicas[medico].add(clinica[0])
    
    return clinicas_medicos

# Generate work schedule for doctors in clinics
def gerar_trabalha(medicos, clinicas):
    trabalha = []
    clinicas_medicos = distribuir_medicos(medicos, clinicas)

    for clinica, medicos_clinica in clinicas_medicos.items():
        for dia in range(0, 7):  # de segunda a domingo
            medicos_dia = random.sample(medicos_clinica, 8)  # Select 8 doctors randomly
            for medico in medicos_dia:
                trabalha.append((medico, clinica, dia))
    return trabalha

# Function to generate a random time within specific ranges
def generate_random_time():
    possible_hours_morning = list(range(8, 13))  # 08:00 to 12:30
    possible_hours_afternoon = list(range(14, 19))  # 14:00 to 18:30
    possible_minutes = [0, 30]  # Minutes can be 00 or 30

    if random.choice([True, False]):
        hour = random.choice(possible_hours_morning)
    else:
        hour = random.choice(possible_hours_afternoon)
    
    minute = random.choice(possible_minutes)
    return time(hour, minute, 0)  # Hours, minutes, and seconds set to 00

# Function to generate consultations and prescriptions
def gerar_consultas_receitas(pacientes, medicos, clinicas, start_date, end_date, trabalha):
    consultas = []
    receitas = []
    consulta_id = 1
    delta_days = (end_date - start_date).days
    patient_schedule = {p[0]: set() for p in pacientes}  # Dictionary to track each patient's schedule
    doctor_schedule = {m[0]: set() for m in medicos}  # Dictionary to track each doctor's schedule
    unique_receitas = set()
    
    for day_offset in range(delta_days):
        data = (start_date + timedelta(days=day_offset)).date()
        day_of_week = (data.weekday() + 1) % 7  # Convert to 0 = Sunday, ..., 6 = Saturday

        for clinica in clinicas:
            consultas_por_clinica = 0
            
            # Seleciona médicos disponíveis para a clínica e o dia da semana
            medicos_disponiveis = [t[0] for t in trabalha if t[1] == clinica[0] and t[2] == day_of_week]
            if not medicos_disponiveis:
                continue  # Continue para a próxima clínica se não houver médicos disponíveis

            while consultas_por_clinica < 20:
                medico = random.choice(medicos_disponiveis)
                consultas_por_medico = 0

                while consultas_por_medico < 2:
                    if consultas_por_clinica >= 20:
                        break

                    hora = generate_random_time()  # Gera um horário dentro dos intervalos especificados
                    paciente_disponiveis = [p for p in pacientes if (data, hora) not in patient_schedule[p[0]]]

                    if not paciente_disponiveis:
                        break  # Interrompe se não houver pacientes disponíveis

                    paciente = random.choice(paciente_disponiveis)
                    if paciente[0] == medico[0]:  # Pula se o paciente for o mesmo que o médico
                        continue

                    if (data, hora) in doctor_schedule[medico]:
                        continue  # Pula se o médico já tiver uma consulta neste horário

                    # Adiciona a nova consulta aos agendamentos
                    patient_schedule[paciente[0]].add((data, hora))
                    doctor_schedule[medico].add((data, hora))

                    codigo_sns = fake.unique.bothify(text='############')
                    consultas.append((consulta_id, paciente[0], medico, clinica[0], data, hora, codigo_sns))

                    # ~80% das consultas têm receita
                    if random.random() < 0.8:
                        num_meds = random.randint(1, 6)
                        for _ in range(num_meds):
                            medicamento = fake.word()
                            quantidade = random.randint(1, 3)
                            # Verifica se a receita já foi prescrita para este paciente nesta consulta
                            if (codigo_sns, clean_text(medicamento)) not in unique_receitas:
                                unique_receitas.add((codigo_sns, clean_text(medicamento)))
                                receitas.append((codigo_sns, clean_text(medicamento), quantidade))

                    consulta_id += 1
                    consultas_por_clinica += 1
                    consultas_por_medico += 1

                    if consultas_por_medico >= 2:
                        break

                if consultas_por_clinica >= 20:
                    break

    return consultas, receitas

# Função para gerar observações
def gerar_observacoes(consultas):
    observacoes = []
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
                observacoes.append(observation)
                unique_observacoes.add(observation)

        for parametro in parametros_metricas:
            observation = (consulta[0], clean_text(parametro), random.uniform(1.0, 100.0))
            if observation not in unique_observacoes:
                observacoes.append(observation)
                unique_observacoes.add(observation)

    return observacoes

# Gerar dados
pacientes = gerar_pacientes(5000)
for i in pacientes:
    print(f"INSERT INTO paciente values ('{i[0]}', '{i[1]}', '{i[2]}', '{i[3]}', '{i[4]}', '{i[5]}');")



clinicas = gerar_clinicas()
for i in clinicas:
    print(f"INSERT INTO clinica values ('{i[0]}', '{i[1]}', '{i[2]}');")


enfermeiros = gerar_enfermeiros(clinicas)
for i in enfermeiros:
    print(f"INSERT INTO enfermeiro values ('{i[0]}', '{i[1]}', '{i[2]}', '{i[3]}', '{i[4]}');")



medicos = gerar_medicos()
for i in medicos:
    print(f"INSERT INTO medico values ('{i[0]}', '{i[1]}', '{i[2]}', '{i[3]}', '{i[4]}');")


trabalha = gerar_trabalha(medicos, clinicas)
for i in trabalha:
    print(f"INSERT INTO trabalha values ('{i[0]}', '{i[1]}', {i[2]});")


start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)
consultas, receitas = gerar_consultas_receitas(pacientes, medicos, clinicas, start_date, end_date,trabalha)

for i in consultas:
    print(f"INSERT INTO consulta values ({i[0]}, '{i[1]}', '{i[2]}', '{i[3]}', '{i[4]}', '{i[5]}', '{i[6]}');")


for i in receitas:
    print(f"INSERT INTO receita values ('{i[0]}', '{i[1]}', {i[2]});")



observacoes = gerar_observacoes(consultas)
for i in observacoes:
    if len(i) > 2:
        print(f"INSERT INTO observacao values ({i[0]}, '{i[1]}', {i[2]});")
    else:
        print(f"INSERT INTO observacao values ({i[0]}, '{i[1]}');")
