from datetime import *

from kivy.app import App
from kivy.logger import Logger

from observations import Observation, Diagnosis
from openmrs import RESTConnection
from kivy.uix.label import Label


class RestApp(App):

    def __init__(self, **kwargs):
        super(RestApp, self).__init__(**kwargs)

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
        lab_observations = {}
        vitals_observations = {}
        diagnosis_observations = {}

        visits = response.get('results')
        for visit in visits:
            for encounter in visit.get('encounters'):
                encounter_type = encounter.get('encounterType').get('display')
                if encounter_type == 'Labs':
                    lab_observations = self.populate_observation_dict('Labs', encounter, lab_observations)
                if encounter_type == 'Vitals':
                    vitals_observations = self.populate_observation_dict('Vitals', encounter, vitals_observations)
                if encounter_type == 'Visit Note':
                    for observation in encounter.get('obs'):
                        if 'diagnosis' in observation.get('display'):
                            diagnosis_observations = self.populate_diagnosis_dict(encounter, diagnosis_observations)

    def populate_observation_dict(self, obs_type, encounter, obs_dict):
            # create datetime object based on encounter time so we can easily compare them
            date_time_temp = encounter.get('encounterDatetime').split('.')[0]
            date_time = datetime.strptime(date_time_temp, '%Y-%m-%dT%H:%M:%S')
            observations = encounter.get('obs')

            # if the dictionary is empty just place the encounter info into it
            # empty dictionaries evaluate to false
            if not obs_dict:
                for obs in observations:
                    obs_string, obs_value = obs.get('display').split(':')
                    obs_object = Observation(obs_type, obs_string.strip(), obs_value.strip(), date_time)
                    obs_dict[obs_string.strip()] = obs_object
                return obs_dict
            else:
                for obs in observations:
                    obs_string, obs_value = obs.get('display').split(':')
                    obs_string = obs_string.strip()
                    obs_value = obs_value.strip()
                    obs_object = Observation( obs_type, obs_string, obs_value, date_time)

                    if obs_string in obs_dict:
                        # if data entry is older than what is currently in the dictionary continue
                        if obs_dict.get(obs_string).obs_datetime >= date_time:
                            continue
                        # if the data entry is newer update the dictionary
                        elif obs_dict.get(obs_string).obs_datetime < date_time:
                            obs_dict.update(obs_string, obs_object)
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
                obs_diagnosis = obs.get('display').split(',')[-1]
                obs_diagnosis = obs_diagnosis.strip()
                obs_dict[obs_diagnosis] = Diagnosis(obs_diagnosis, date_time)
            return obs_dict
        else:
            for obs in observations:
                obs_diagnosis = obs.get('display').split(',')[-1]
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

    #This function no longer shows data on the GUI, which has been prepped for the medication information.
    #Instead, it prints information to the standard output.
    #If we don't need this function, we can delete it.

    #This function shows recent diagnosese for a patient
    def display_diagnosis(self, data):
        timestamp = 'N/A'
        diagnosis_array = []

        for i in range(len(data)):
            if data[i].find('Visit Diagnoses:') != -1:
                timestamp = data[i + 1]
                diagnosis_array.append(data[i])
                diagnosis_array.append(data[i + 1])

        print('Diagnosis')

        for j in range(len(diagnosis_array)):
            if diagnosis_array[j] == timestamp:
                print(diagnosis_array[j - 1])
                print(timestamp)

    #This function no longer shows data on the GUI, which has been prepped for the medication information.
    #Instead, it prints information to the standard output.
    #If we don't need this function, we can delete it.

    #This function shows the recent observations of a patient's vitals
    def display_vitals(self, data):
        vitals = ['Height (cm):', 'Weight (kg):', 'Temperature (C):', 'Pulse:', 'Respiratory rate:', 'Systolic blood pressure:', 'Diastolic blood pressure:', 'Blood oxygen saturation:']
        recent = 'N/A'
        timestamp = 'N/A'

        print('Vitals')

        for vital in vitals:
            for i in range(len(data)):
                if data[i].find(vital) != -1:
                    recent = data[i]
                    timestamp = data[i + 1]
            print(recent)
            print(timestamp)

    #This function no longer shows data on the GUI, which has been prepped for the medication information.
    #Instead, it prints information to the standard output.
    #If we don't need this function, we can delete it.

    #This function shows a patient's recent lab results
    def display_labs(self, data):
        labs = ['Leukocytes (#/mL)', 'Blasts per 100 Leukocytes', 'Platelets', 'Partial Thromboplastin Time', 'Glucose', 'Lactate', 'Creatinine',
                'Bilirubin Direct', 'Bilirubin Total', 'Blood Cultures, Bacteria', 'Blood Cultures, Fungus', 'Blood Cultures, Viruses', 'Urinalysis']
        recent = 'N/A'
        timestamp = 'N/A'

        print('Labs')

        for lab in labs:
            for i in range(len(data)):
                if data[i].find(lab) != -1:
                    recent = data[i]
                    timestamp = data[i + 1]
            print(recent)
            print(timestamp)

    def on_encounters_not_loaded(self, request, error):
        Logger.error('RestApp: {error}'.format(error=error))


if __name__ == "__main__":
    app = RestApp()
    app.run()
