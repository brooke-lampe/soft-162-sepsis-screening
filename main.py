from datetime import *

from kivy.app import App
from kivy.logger import Logger
from kivy.properties import BooleanProperty, StringProperty


from medications import Medications, MedicationsDatabase
from observations import Observation, Diagnosis, Creatinine
from openmrs import RESTConnection

__app_package__ = 'edu.sepsis'
__app__ = 'Sepsis'
__version__ = '1.0'
__flags__ = ['--bootstrap=sdl2', '--requirements=python2,kivy', '--permission=INTERNET']

class RestApp(App):
    message = StringProperty()
    taking_erythropoietin= BooleanProperty()
    taking_colonyfactors= BooleanProperty()
    taking_heparin = BooleanProperty()

    # Data members
    lab_observations = {}
    vitals_observations = {}
    diagnosis_observations = {}
    SIRS_criteria = []
    organ_criteria = []
    suggested_labs = []

    global patient_info
    patient_info = 'Patient has no data.'

    def __init__(self, **kwargs):
        super(RestApp, self).__init__(**kwargs)
        url = MedicationsDatabase.construct_mysql_url('cse.unl.edu', 3306, 'kheyen', 'kheyen', 'AdJ:8w')
        self.medications_database = MedicationsDatabase(url)
        self.session = self.medications_database.create_session()

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

    # check HEprain the function take the date that entered by the user and check if it valid date, then it check if the user take heprain in the last 24 hours
    def check_heparin(self):
        date_entered = self.root.ids.heparin_id.text
        if date_entered != '':
            try:
                date_entered= datetime.strptime(date_entered, '%Y-%m-%d')
                medication_list=[]
                while(datetime.today()-date_entered == timedelta(1)):
                    query = self.session.query(Medications).filter(Medications.name == 'Heparin', Medications .patient_name == date_entered).delete()
                    self.session.add(medication_list)
                    if date_entered >  timedelta(1) and date_entered < timedelta(0):
                       self.taking_heparin= False
                    elif date_entered ==  timedelta(0):
                        self.staking_heparin=True
            except ValueError:
                self.message = 'Invalid Input - Enter proper format: YYYY-MM-DD'
            except Exception:
                self.message = 'Invalid Input - Enter a valid date: YYYY-MM-DD'

        new_medication= Medications(medications_name='Heparin', taking_date= date_entered, patient_id = self.root.ids.openmrs_id.text)
        self.session.add(new_medication)
        self.session.commit()


    def CheckColonyFactor(self):
        date_entered = self.root.ids.colonyFactor_id.text
        if date_entered != '':
            try:
                date_entered =datetime.strptime(date_entered, '%Y-%m-%d')
                medication_list=[]
                while(datetime.today()-date_entered < timedelta(60)):
                    query = self.session.query(Medications).filter(Medications.name == 'ColonyFactors', Medications.taking_date == date_entered).delete()
                    self.session.add(medication_list)
                    if date_entered > timedelta(60) and date_entered < timedelta(0):
                       self.taking_colonyfactors=False
                    elif date_entered <=  timedelta(60):
                        self.taking_colonyfactors= True
            except ValueError():
                self.message = 'Invalid Input - Enter proper format: YYYY-MM-DD'
            except Exception():
                self.message = 'Invalid Input - Enter a valid date: YYYY-MM-DD'

        new_medication= Medications(medications_name='ColonyFactors', taking_date= date_entered, patient_id = self.root.ids.openmrs_id.text )
        self.session.add(new_medication)
        self.session.commit()

    def check_erythropoietin(self):
        date_entered = self.root.ids.eythropoitiens_id.text
        if date_entered == '':
            pass
        else:
            try:
                date_entered=datetime.strptime(date_entered, '%Y-%m-%d')
                medication_list=[]
                while(datetime.today()-date_entered < timedelta(60)):
                    query = self.session.query(Medications).filter(Medications.name == 'Erythropoietin', Medications.taking_date == date_entered).delete()
                    self.session.add(medication_list)
                    if date_entered >  timedelta(60) and date_entered < timedelta(0):
                       self.taking_erythropoietin= False
                    elif date_entered <=  timedelta(60):
                        self.taking_erythropoietin = True
            except ValueError:
                self.message = 'Invalid Input - Enter proper format: YYYY-MM-DD'
            except Exception:
                self.message = 'Invalid Input - Enter a valid date: YYYY-MM-DD'

        new_medication= Medications(medications_name='Erythropoietin', patient_id= self.root.ids.openmrs_id.text)
        self.session.add(new_medication)
        self.session.commit()


if __name__ == "__main__":
    app = RestApp()
    app.run()
