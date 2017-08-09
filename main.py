from kivy.app import App
from kivy.logger import Logger
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.label import Label

from datetime import *

from medications import Medications, MedicationsDatabase
from observations import Observation, Diagnosis, Creatinine
from openmrs import RESTConnection

__app_package__ = 'edu.sepsis'
__app__ = 'Sepsis'
__version__ = '1.0'
__flags__ = ['--bootstrap=sdl2', '--requirements=python2,kivy,pyjnius,sqlalchemy,mysql_connector', '--permission=INTERNET']

class RestApp(App):
    message = StringProperty()
    taking_erythropoietin = BooleanProperty()
    taking_colonyfactors = BooleanProperty()
    taking_heparin = BooleanProperty()
    advance = [True, True, True]

    global patient_info
    patient_info = 'Patient has no data.'

    def __init__(self, **kwargs):

        super(RestApp, self).__init__(**kwargs)

        # Data members
        self.lab_observations = {}
        self.vitals_observations = {}
        self.diagnosis_observations = {}
        self.SIRS_criteria = []
        self.organ_criteria = []
        self.suggested_labs = []

        url = MedicationsDatabase.construct_mysql_url('cse.unl.edu', 3306, 'kheyen', 'kheyen', 'AdJ:8w')
        self.medications_database = MedicationsDatabase(url)
        self.session = self.medications_database.create_session()
        self.reset_dicts()

    def connect(self):
        self.openmrs_connection = RESTConnection(self.root.ids.authority.text, self.root.ids.port_number.text, self.root.ids.username.text, self.root.ids.password.text)

    def load_session(self):
        self.root.ids.session.clear_widgets()
        self.openmrs_connection.send_request('session', None, self.on_session_loaded,
                                             self.on_session_not_loaded, self.on_session_not_loaded)

    def on_session_loaded(self, request, response):
        if response['authenticated']:
            self.root.current = 'selection'
        else:
            self.root.ids.session.text = 'Unable to authenticate.  Invalid username or password.'
            self.root.ids.session2.text = 'Please verify credentials and try again.'
            self.root.ids.password.text = ''

    def on_session_not_loaded(self, request, error):
        self.root.ids.session.text = 'Unable to connect.'
        self.root.ids.session2.text = 'Please verify internet connection and try again.'
        Logger.error('RestApp: {error}'.format(error=error))

    def load_patient(self):
        self.openmrs_connection.send_request('patient?q={openmrs_id}'.format(openmrs_id=self.root.ids.openmrs_id.text), None, self.on_patient_loaded,
                                             self.on_patient_not_loaded, self.on_patient_not_loaded)

    def on_patient_loaded(self, request, response):
        patient_uuid = 'NULL'
        for result in response['results']:
            patient_uuid = result['uuid']
            self.load_encounters(patient_uuid)
            self.root.current = 'medication'
            for medication_list, text_input in ('Heparin', self.root.ids.heparin_id), ( 'ColonyFactors',self.root.ids.colonyFactor_id), ('Erythropoietin', self.root.ids.eythropoitiens_id):
                if self.session.query(Medications).filter(Medications.medications_name == medication_list, Medications.patient_id == self.root.ids.openmrs_id.text).first() is None:
                    text_input.text = ''
                else:
                    #query = self.session.query(Medications).filter(Medications.medications_name== medication_list, Medications.patient_id == self.root.ids.openmrs_id.text).first().taking_date
                    query = self.session.query(Medications).filter(Medications.medications_name == medication_list, Medications.patient_id == self.root.ids.openmrs_id.text).first()
                    text_input.text = str(self.session.query(Medications).filter(Medications.medications_name == medication_list, Medications.patient_id == self.root.ids.openmrs_id.text).first().taking_date)

        if patient_uuid == 'NULL':
            self.root.ids.retrieve.text = 'Unable to retrieve patient information.'
            self.root.ids.retrieve2.text = 'Please verify that OpenMRS ID is correct and try again.'

    def on_patient_not_loaded(self, request, error):
        self.root.ids.retrieve.text = 'Unable to connect.'
        self.root.ids.retrieve2.text = 'Please verify internet connection and try again.'
        Logger.error('RestApp: {error}'.format(error=error))

    def load_encounters(self, patient_uuid):
        self.openmrs_connection.send_request('visit?patient={patient_uuid}&v=full'.format(patient_uuid=patient_uuid), None,
                self.on_encounters_loaded,
                self.on_encounters_not_loaded, self.on_encounters_not_loaded)

    def on_encounters_loaded(self, request, response):
        visits = response.get('results')

        for visit in visits:
            visit_uuid = visit.get('uuid')
            global patient_info
            patient_info = visit.get('patient').get('display')
            for encounter in visit.get('encounters'):
                encounter_type = encounter.get('encounterType').get('display')
                if encounter_type == 'Labs':
                    self.lab_observations = self.populate_observation_dict('Labs', encounter, self.lab_observations, visit_uuid)
                if encounter_type == 'Vitals':
                    self.vitals_observations = self.populate_observation_dict('Vitals', encounter, self.vitals_observations, visit_uuid)
                if encounter_type == 'Visit Note':
                    for observation in encounter.get('obs'):
                        if 'diagnosis' in observation.get('display'):
                            self.diagnosis_observations = self.populate_diagnosis_dict(encounter, self.diagnosis_observations)

    def on_encounters_not_loaded(self, request, error):
        Logger.error('RestApp: {error}'.format(error=error))

    def populate_observation_dict(self, obs_type, encounter, obs_dict, visit_uuid):
            # create datetime object based on encounter time so we can easily compare them
            date_time_temp = encounter.get('encounterDatetime').split('.')[0]
            date_time = datetime.strptime(date_time_temp, '%Y-%m-%dT%H:%M:%S')
            observations = encounter.get('obs')

            # if the dictionary is empty just place the encounter info into it
            # empty dictionaries evaluate to false
            if not obs_dict:
                for obs in observations:
                    obs_string, obs_value = obs.get('display').split(':')
                    # Creatinine readings require a baseline reading so the have to be handled seperately from everything else
                    if obs_string == 'Creatinine in Blood (mg/dL)':
                        obs_object = Creatinine('Labs', obs_string.strip(), obs_value, obs_value, date_time, visit_uuid)
                    else:
                        obs_object = Observation(obs_type, obs_string.strip(), obs_value.strip(), date_time)
                    obs_dict[obs_string.strip()] = obs_object
                return obs_dict
            else:
                for obs in observations:
                    obs_string, obs_value = obs.get('display').split(':')
                    obs_string = obs_string.strip()
                    obs_value = obs_value.strip()
                    obs_object = Observation(obs_type, obs_string, obs_value, date_time)
                    if obs_string in obs_dict:
                        # if a second creatinine value is found under the same visit update the baseline
                        if obs_string == 'Creatinine in Blood (mg/dL)':
                            creat = obs_dict.get('Creatinine in Blood (mg/dL)')
                            if creat.visit_id == 0:
                                obs_dict[obs_string] = Creatinine('Labs', obs_string, obs_value, obs_value, date_time, visit_uuid)
                            if creat.visit_id == visit_uuid:
                                creat.update_baseline(obs_value)
                                obs_dict[obs_string] = creat
                                continue

                        # if its a blank entry set the object
                        if obs_dict.get(obs_string).obs_datetime == 0:
                            obs_dict[obs_string] = obs_object

                        # if data entry is older than what is currently in the dictionary continue
                        if obs_dict.get(obs_string).obs_datetime >= date_time:
                            continue
                        # if the data entry is newer update the dictionary
                        elif obs_dict.get(obs_string).obs_datetime < date_time:
                            obs_dict[obs_string] = obs_object
                            continue
                    # if observation is not found in the dict add it
                    else:
                        obs_dict[obs_string] = obs_object
            return obs_dict

    def populate_diagnosis_dict(self, encounter, obs_dict):
        date_time_temp = encounter.get('encounterDatetime').split('.')[0]
        date_time = datetime.strptime(date_time_temp, '%Y-%m-%dT%H:%M:%S')
        observations = encounter.get('obs')
        if not obs_dict:
            for obs in observations:
                # the last thing in the diagnosis string is the actual diagnosis
                obs_diagnosis = obs.get('display').split(':')[1]
                obs_diagnosis = obs_diagnosis.split(',')
                # openMRS is inconsistent in the way it returns diagnosis information
                # This removes all of the assorted words and gives only the diagnosis
                non_diagnosis_keywords = ['Primary', 'Secondary', 'Confirmed diagnosis', 'Presumed diagnosis']
                for item in obs_diagnosis:
                    item = item.strip()
                    if item not in non_diagnosis_keywords:
                        obs_diagnosis_str = item
                        break
                obs_diagnosis_str = obs_diagnosis_str.strip()
                obs_dict[obs_diagnosis_str] = Diagnosis(obs_diagnosis_str, date_time)
            return obs_dict
        else:
            for obs in observations:
                obs_diagnosis_list = obs.get('display').split(':')[1]
                obs_diagnosis_list = obs_diagnosis_list.split(',')
                non_diagnosis_keywords = ['Primary', 'Secondary', 'Confirmed diagnosis', 'Presumed diagnosis']
                for item in obs_diagnosis_list:
                    item = item.strip()
                    if item not in non_diagnosis_keywords:
                        obs_diagnosis = item
                        break
                obs_diagnosis = obs_diagnosis.strip()
                if obs_diagnosis in obs_dict:
                    if obs_dict.get(obs_diagnosis).obs_datetime >= date_time:
                        continue
                    elif obs_dict.get(obs_diagnosis).obs_datetime < date_time:
                        obs_dict.update(obs_diagnosis, Diagnosis(obs_diagnosis, date_time))
                        continue
                else:
                    obs_dict[obs_diagnosis] = Diagnosis(obs_diagnosis, date_time)
        return obs_dict

    def clear(self):
        self.lab_observations.clear()
        self.vitals_observations.clear()
        self.diagnosis_observations.clear()
        self.reset_dicts()
        global patient_info
        patient_info = 'Patient has no data.'
        self.root.ids.patient_info.text = ''
        self.root.ids.determination_timestamp.text = ''
        self.root.ids.determination_summary.text = ''
        self.root.ids.SIRS_criteria.clear_widgets()
        self.root.ids.SIRS_reason.clear_widgets()
        self.root.ids.organ_criteria.clear_widgets()
        self.root.ids.organ_reason.clear_widgets()
        self.root.ids.treatment.text = ''
        self.root.ids.suggested_layout.clear_widgets()

    def reset_dicts(self):
        self.vitals_observations = {'Temperature (C)': Observation('Vitals', 'Temperature (C)', 0, 0),
                                    'Pulse': Observation('Vitals', 'Pulse', 0, 0),
                                    'Respiratory rate': Observation('Vitals', 'Respiratory rate', 0, 0),
                                    'Systolic blood pressure': Observation('Vitals', 'Systolic blood pressure', 0, 0),
                                    'Diastolic blood pressure': Observation('Vitals', 'Diastolic blood pressure', 0, 0)}

        self.lab_observations = {'Leukocytes (#/mL)': Observation('Labs', 'Leukocytes (#/mL)', 0, 0),
                                        'Blasts per 100 Leukocytes (%)': Observation('Labs', 'Blasts per 100 Leukocytes (%)', 0, 0),
                                        'Glucose in Blood (mg/dL)': Observation('Labs', 'Glucose in Blood (mg/dL)', 0, 0),
                                        'Lactate in Blood (mmol/L)': Observation('Labs', 'Lactate in Blood (mmol/L)', 0, 0),
                                        'Creatinine in Blood (mg/dL)': Creatinine('Labs', 'Creatinine in Blood (mg/dL)', 0, 0, 0, 0),
                                        'Bilirubin Total (mg/dL)': Observation('Labs', 'Bilirubin Total (mg/dL)', 0, 0),
                                        'Platelets (#/mL)': Observation('Labs', 'Platelets (#/mL)', 0, 0),
                                        'Partial Thromboplastin Time (s)': Observation('Labs', 'Partial Thromboplastin Time (s)', 0, 0),
                                        'Blood Cultures, Viruses': Observation('Labs', 'Blood Cultures, Viruses', 0, 0),
                                        'Blood Cultures, Bacteria': Observation('Labs', 'Blood Cultures, Bacteria', 0, 0),
                                        'Blood Cultures, Fungus': Observation('Labs', 'Blood Cultures, Fungus', 0, 0),
                                        'Urinalysis': Observation('Labs', 'Urinalysis', 0, 0)}
    def clear_limited(self):
        self.root.ids.patient_info.text = ''
        self.root.ids.determination_timestamp.text = ''
        self.root.ids.determination_summary.text = ''
        self.root.ids.SIRS_criteria.clear_widgets()
        self.root.ids.SIRS_reason.clear_widgets()
        self.root.ids.organ_criteria.clear_widgets()
        self.root.ids.organ_reason.clear_widgets()
        self.root.ids.treatment.text = ''
        self.root.ids.suggested_layout.clear_widgets()

    #check_heparin:  The function accepts the date that entered by the user and checks if it valid date, then it checks if the user has taken heparin in the last 24 hours
    def check_heparin(self):
        date_entered = self.root.ids.heparin_id.text
        if date_entered != '':
            try:
                date_entered = datetime.strptime(date_entered, '%Y-%m-%d')
                while timedelta(0) <= datetime.today() - date_entered <= timedelta(1):
                    self.session.query(Medications).filter(Medications.name == 'Heparin', Medications.patient_id == self.root.ids.openmrs_id.text).delete()
                    if timedelta(1) < datetime.today() - date_entered < timedelta(0):
                        self.taking_heparin = False
                    elif timedelta(0) <= datetime.today() - date_entered <= timedelta(1):
                        self.taking_heparin = True
            except ValueError:
                self.root.ids.error_log.text = 'Invalid Input - Enter proper format: YYYY-MM-DD'
                self.root.current = 'medication'
                self.advance[0] = False
                return
            except Exception:
                self.root.ids.error_log.text = 'Invalid Input - Enter a valid date: YYYY-MM-DD'
                self.root.current = 'medication'
                self.advance[0] = False
                return

        new_medication= Medications(medications_name='Heparin', taking_date=date_entered, patient_id=self.root.ids.openmrs_id.text)
        self.session.add(new_medication)
        self.session.commit()
        self.advance[0] = True

    def check_colony_factor(self):
        date_entered = self.root.ids.colonyFactor_id.text
        if date_entered != '':
            try:
                date_entered = datetime.strptime(date_entered, '%Y-%m-%d')
                medication_list = []
                while datetime.today() - date_entered < timedelta(60):
                    query = self.session.query(Medications).filter(Medications.name == 'ColonyFactors', Medications.patient_id == self.root.ids.openmrs_id.text).delete()
                    self.session.add(medication_list)
                    if timedelta(60) < datetime.today() - date_entered < timedelta(0):
                       self.taking_colonyfactors = False
                    elif datetime.today()- date_entered <= timedelta(60):
                        self.taking_colonyfactors = True
            except ValueError:
                self.root.ids.error_log.text = 'Invalid Input - Enter proper format: YYYY-MM-DD'
                self.root.current = 'medication'
                self.advance[1] = False
                return
            except Exception:
                self.root.ids.error_log.text = 'Invalid Input - Enter a valid date: YYYY-MM-DD'
                self.root.current = 'medication'
                self.advance[1] = False
                return

        new_medication= Medications(medications_name='ColonyFactors', taking_date= date_entered, patient_id = self.root.ids.openmrs_id.text )
        self.session.add(new_medication)
        self.session.commit()
        self.advance[1] = True

    def check_erythropoietin(self):
        date_entered = self.root.ids.eythropoitiens_id.text
        if date_entered == '':
            pass
        else:
            try:
                date_entered=datetime.strptime(date_entered, '%Y-%m-%d')
                medication_list=[]
                while datetime.today() - date_entered <= timedelta(30):
                    query = self.session.query(Medications).filter(Medications.name == 'Erythropoietin', Medications.taking_date == date_entered).delete()
                    self.session.add(medication_list)
                    if datetime.today() - date_entered > timedelta(30) and date_entered < timedelta(0):
                        self.taking_erythropoietin = False
                    elif datetime.today() - date_entered <= timedelta(30):
                        self.taking_erythropoietin = True
            except ValueError:
                self.root.ids.error_log.text = 'Invalid Input - Enter proper format: YYYY-MM-DD'
                self.root.current = 'medication'
                self.advance[2] = False
                return
            except Exception:
                self.root.ids.error_log.text = 'Invalid Input - Enter a valid date: YYYY-MM-DD'
                self.root.current = 'medication'
                self.advance[2] = False
                return

        new_medication= Medications(medications_name='Erythropoietin', taking_date=date_entered, patient_id=self.root.ids.openmrs_id.text)
        self.session.add(new_medication)
        self.session.commit()
        self.advance[2] = True

    def retrieve(self):
        #Pull required data from the database

        #General Information
        global patient_info
        patient_id_and_name = patient_info
        current_timestamp = datetime.now()

        #Diagnosis Observations
        diabetes_i = self.diagnosis_observations.get('Diabetes Mellitus')
        diabetes_ii = self.diagnosis_observations.get('Diabetes Mellitus, Type II')
        ESRD = self.diagnosis_observations.get('ESRD')

        #Vitals Observations
        temperature = self.vitals_observations.get('Temperature (C)')
        pulse = self.vitals_observations.get('Pulse')
        respiratory_rate = self.vitals_observations.get('Respiratory rate')
        systolic_blood_pressure = self.vitals_observations.get('Systolic blood pressure')
        diastolic_blood_pressure = self.vitals_observations.get('Diastolic blood pressure')

        #Labs Observations
        leukocytes = self.lab_observations.get('Leukocytes (#/mL)')
        blasts_per_100_leukocytes = self.lab_observations.get('Blasts per 100 Leukocytes (%)')
        glucose = self.lab_observations.get('Glucose in Blood (mg/dL)')
        lactate = self.lab_observations.get('Lactate in Blood (mmol/L)')
        creatinine = self.lab_observations.get('Creatinine in Blood (mg/dL)')
        bilirubin_total = self.lab_observations.get('Bilirubin Total (mg/dL)')

        #Timestamp only
        platelets_timestamp = self.lab_observations.get('Platelets (#/mL)').obs_datetime
        partial_thromboplastin_time_timestamp = self.lab_observations.get('Partial Thromboplastin Time (s)').obs_datetime
        bacteria_culture_timestamp = self.lab_observations.get('Blood Cultures, Bacteria').obs_datetime
        fungus_culture_timestamp = self.lab_observations.get('Blood Cultures, Fungus').obs_datetime
        virus_culture_timestamp = self.lab_observations.get('Blood Cultures, Viruses').obs_datetime
        urinalysis_timestamp = self.lab_observations.get('Urinalysis').obs_datetime

        #Medications within timeframe
        colony_stimulating_factors = self.taking_colonyfactors
        heparin = self.taking_heparin
        recombinant_human_erythropoientins = self.taking_erythropoietin

        #Advance to determination screen if no ValueError or Exception
        if self.advance[0] and self.advance[1] and self.advance[2]:
            self.root.current = 'determination'

        #This will return True if more labs are needed, False if more labs are not needed
        self.determination(patient_id_and_name, current_timestamp, diabetes_i, diabetes_ii, ESRD, temperature, pulse, respiratory_rate, systolic_blood_pressure, diastolic_blood_pressure,
                          leukocytes, blasts_per_100_leukocytes, glucose, lactate, creatinine, bilirubin_total,
                          platelets_timestamp, partial_thromboplastin_time_timestamp, bacteria_culture_timestamp, fungus_culture_timestamp, virus_culture_timestamp,
                          urinalysis_timestamp, colony_stimulating_factors, heparin, recombinant_human_erythropoientins)

    def determination(self, patient_id_and_name, current_timestamp, diabetes_i, diabetes_ii, ESRD, temperature, pulse, respiratory_rate, systolic_blood_pressure, diastolic_blood_pressure,
                      leukocytes, blasts_per_100_leukocytes, glucose, lactate, creatinine, bilirubin_total,
                      platelets_timestamp, partial_thromboplastin_time_timestamp, bacteria_culture_timestamp, fungus_culture_timestamp, virus_culture_timestamp,
                      urinalysis_timestamp, colony_stimulating_factors, heparin, recombinant_human_erythropoientins):

        #Fill in user interface information
        suggested_layout = self.root.ids.suggested_layout
        SIRS_criteria_layout = self.root.ids.SIRS_criteria
        SIRS_reason_layout = self.root.ids.SIRS_reason
        organ_criteria_layout = self.root.ids.organ_criteria
        organ_reason_layout = self.root.ids.organ_reason

        self.root.ids.patient_info.text = patient_id_and_name

        current_time = current_timestamp.strftime('%Y-%m-%d@%H:%M:%S')
        self.root.ids.determination_timestamp.text = current_time

        #Classifications are '0' for indeterminate, '1' for SIRS, and '2' for sepsis (default is '0')
        classification = 0

        #SIRS criteria are temperature, pulse, respiratory rate, glucose, and leukocytes / blasts per 100 leukocytes
        self.SIRS_criteria = [0, 0, 0, 0, 0]

        #Organ dysfunction criteria are lactate, systolic blood pressure / mean arterial blood pressure, creatinine, and bilirubin
        self.organ_criteria = [0, 0, 0, 0]

        #Suggested labs are lactate, creatinine, bilirubin, platelets, partial thromboplastin time, blood cultures (3), and urinalysis
        self.suggested_labs = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        labs_string = ['Lactate', 'Creatinine', 'Bilirubin Total', 'Platelets', 'Partial Thromboplastin Time',
                       'Blood Cultures, Bacteria', 'Blood Cultures, Fungus', 'Blood Cultures, Viruses', 'Urinalysis']

        mean_arterial_pressure = (float(systolic_blood_pressure.obs_value) + (2 * float(diastolic_blood_pressure.obs_value))) / 3

        #Determine what criteria of SIRS are met
        if temperature.obs_datetime != 0 and float(temperature.obs_value) < 36:
            self.SIRS_criteria[0] = 1
            SIRS_criteria_layout.add_widget(Label(text=str(temperature)))
            SIRS_reason_layout.add_widget(Label(text='Below 36'))
        elif temperature.obs_datetime != 0 and float(temperature.obs_value) > 38.3:
            self.SIRS_criteria[0] = 1
            SIRS_criteria_layout.add_widget(Label(text=str(temperature)))
            SIRS_reason_layout.add_widget(Label(text='Above 38.3'))

        if pulse.obs_datetime != 0 and float(pulse.obs_value) > 95:
            self.SIRS_criteria[1] = 1
            SIRS_criteria_layout.add_widget(Label(text=str(pulse)))
            SIRS_reason_layout.add_widget(Label(text='Above 95'))

        if respiratory_rate.obs_datetime != 0 and float(respiratory_rate.obs_value) >= 21:
            self.SIRS_criteria[2] = 1
            SIRS_criteria_layout.add_widget(Label(text=str(respiratory_rate)))
            SIRS_reason_layout.add_widget(Label(text='Above 21'))

        if diabetes_i or diabetes_ii:
            pass
        elif glucose.obs_datetime != 0 and 140 <= float(glucose.obs_value) < 200:
            self.SIRS_criteria[3] = 1
            SIRS_criteria_layout.add_widget(Label(text=str(glucose)))
            SIRS_reason_layout.add_widget(Label(text='Between 140 and 200'))

        if colony_stimulating_factors:
            pass
        elif leukocytes.obs_datetime != 0 and float(leukocytes.obs_value) > 12000:
            self.SIRS_criteria[4] = 1
            SIRS_criteria_layout.add_widget(Label(text=str(leukocytes)))
            SIRS_reason_layout.add_widget(Label(text='Above 12000'))
        elif leukocytes.obs_datetime != 0 and float(leukocytes.obs_value) < 4000:
            self.SIRS_criteria[4] = 1
            SIRS_criteria_layout.add_widget(Label(text=str(leukocytes)))
            SIRS_reason_layout.add_widget(Label(text='Below 4000'))
        elif blasts_per_100_leukocytes.obs_datetime != 0 and float(blasts_per_100_leukocytes.obs_value) > 10:
            self.SIRS_criteria[4] = 1
            SIRS_criteria_layout.add_widget(Label(text=str(blasts_per_100_leukocytes)))
            SIRS_reason_layout.add_widget(Label(text='Above 10'))

        #Determine the number of SIRS criteria met
        SIRS_total = self.SIRS_criteria[0] + self.SIRS_criteria[1] + self.SIRS_criteria[2] + self.SIRS_criteria[3] + self.SIRS_criteria[4]

        #Determine what criteria of organ dysfunction are met (with observations that are sufficiently recent)
        #If observations are not sufficiently recent, suggest labs
        if lactate.obs_datetime != 0 and (current_timestamp - lactate.obs_datetime) < timedelta(hours = 12):
            if float(lactate.obs_value) > 2:
                self.organ_criteria[0] = 1
                organ_criteria_layout.add_widget(Label(text=str(lactate)))
                organ_reason_layout.add_widget(Label(text='Above 2'))
        else:
            self.suggested_labs[0] = 1

        if systolic_blood_pressure.obs_datetime != 0 and float(systolic_blood_pressure.obs_value) < 90 and (current_timestamp - systolic_blood_pressure.obs_datetime) < timedelta(hours = 30):
            self.organ_criteria[1] = 1
            organ_criteria_layout.add_widget(Label(text=str(systolic_blood_pressure)))
            organ_reason_layout.add_widget(Label(text='Below 90'))
        elif systolic_blood_pressure.obs_datetime != 0 and diastolic_blood_pressure.obs_datetime != 0 and mean_arterial_pressure < 65 and (current_timestamp - systolic_blood_pressure.obs_datetime) < timedelta(hours = 30) and (current_timestamp - diastolic_blood_pressure.obs_datetime) < timedelta(hours = 30):
            self.organ_criteria[1] = 1
            organ_criteria_layout.add_widget(Label(text=str(systolic_blood_pressure)))
            organ_criteria_layout.add_widget(Label(text=str(diastolic_blood_pressure)))
            organ_reason_layout.add_widget(Label(text='Mean Arterial Pressure'))
            organ_reason_layout.add_widget(Label(text='is below 65'))

        if creatinine.obs_datetime != 0 and (current_timestamp - creatinine.obs_datetime) < timedelta(hours = 30):
            if creatinine.get_creatinine_change() > 0.5:
                self.organ_criteria[2] = 1
                organ_criteria_layout.add_widget(Label(text=str(creatinine)))
                organ_reason_layout.add_widget(Label(text='Above 0.5 difference from baseline'))
        else:
            self.suggested_labs[1] = 1

        if bilirubin_total.obs_datetime != 0 and (current_timestamp - bilirubin_total.obs_datetime) < timedelta(hours = 30):
            if 2 <= float(bilirubin_total.obs_value) < 10:
                self.organ_criteria[3] = 1
                organ_criteria_layout.add_widget(Label(text=str(bilirubin_total)))
                organ_reason_layout.add_widget(Label(text='Between 2 and 10'))
        else:
            self.suggested_labs[2] = 1

        #Additional labs to be suggested if labs are not within timeframe
        if platelets_timestamp != 0 and (current_timestamp - platelets_timestamp) < timedelta(hours = 30):
            pass
        else:
            self.suggested_labs[3] = 1

        if heparin:
            pass
        elif partial_thromboplastin_time_timestamp != 0 and (current_timestamp - partial_thromboplastin_time_timestamp) < timedelta(hours = 30):
            pass
        else:
            self.suggested_labs[4] = 1

        if bacteria_culture_timestamp != 0 and (current_timestamp - bacteria_culture_timestamp) < timedelta(hours = 30):
            pass
        else:
            self.suggested_labs[5] = 1

        if fungus_culture_timestamp != 0 and (current_timestamp - fungus_culture_timestamp) < timedelta(hours = 30):
            pass
        else:
            self.suggested_labs[6] = 1

        if virus_culture_timestamp != 0 and (current_timestamp - virus_culture_timestamp) < timedelta(hours = 30):
            pass
        else:
            self.suggested_labs[7] = 1

        if urinalysis_timestamp != 0 and (current_timestamp - urinalysis_timestamp) < timedelta(hours = 30):
            pass
        else:
            self.suggested_labs[8] = 1

        #Determine the number of organ dysfunction criteria met
        organ_dysfunction_total = self.organ_criteria[0] + self.organ_criteria[1] + self.organ_criteria[2] + self.organ_criteria[3]

        #Determine if sufficient criteria have been met to diagnose SIRS or sepsis
        if SIRS_total < 2:
            classification = 0
        elif organ_dysfunction_total > 0:
            if organ_dysfunction_total == 1 and self.organ_criteria[2] == 1:
                if ESRD:
                    classification = 0
                elif recombinant_human_erythropoientins:
                    classification = 0
                else:
                    classification = 2

            else:
                classification = 2
        elif SIRS_total < 3:
            classification = 0
        else:
            classification = 1

        #Show determination summary, next steps, and suggested labs to the user
        # (Note: evidence, which appears beneath determination summary, is added to the user interface in above code)

        #Determination summary and next steps
        if classification == 0:
            self.root.ids.determination_summary.text = 'Indeterminate'
            self.root.ids.treatment.text = 'No treatment at this time'
            suggested_layout.add_widget(Label(text='N/A'))
        elif classification == 1:
            self.root.ids.determination_summary.text = 'SIRS Likely'
            self.root.ids.treatment.text = 'Treat patient for SIRS'

            #Suggested labs
            count = 0
            for i in range(len(self.suggested_labs)):
                if self.suggested_labs[i] == 1:
                    suggested_layout.add_widget(Label(text=labs_string[i]))
                    count = 1
            if count == 0:
                suggested_layout.add_widget(Label(text='N/A'))
            else:
                return True

        elif classification == 2:
            self.root.ids.determination_summary.text = 'Sepsis Likely'
            self.root.ids.treatment.text = 'Treat patient for Sepsis'
            suggested_layout.add_widget(Label(text='N/A'))

        return False


if __name__ == "__main__":
    app = RestApp()
    app.run()
