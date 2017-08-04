from datetime import *

from kivy.app import App
from kivy.logger import Logger

from observations import Observation, Diagnosis, Creatinine
from openmrs import RESTConnection
from kivy.uix.label import Label


class RestApp(App):

    # Data members
    lab_observations = {}
    vitals_observations = {}
    diagnosis_observations = {}

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
        visits = response.get('results')
        for visit in visits:
            visit_uuid = visit.get('uuid')
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
                            if creat.visit_id == visit_uuid:
                                creat.update_baseline(obs_value)
                                obs_dict[obs_string] = creat
                                continue
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

    def determination(self, diagnosis, temperature, heart_rate, respiratory_rate, systolic_blood_pressure, diastolic_blood_pressure,
                      glucose, leukocytes, blasts_per_100_leukocytes, lactate, creatinine, creatinine_baseline,
                      bilirubin_total, colony_stimulating_factors, heparin, recombinant_human_erythropoientins):

        SIRS_criteria = [0, 0, 0, 0, 0]
        organ_dysfunction_criteria = [0, 0, 0, 0]
        mean_arterial_pressure = (systolic_blood_pressure + (2 * diastolic_blood_pressure)) / 3

        if temperature < 36 or temperature > 38.3:
            SIRS_criteria[0] = 1
        if heart_rate > 95:
            SIRS_criteria[1] = 1
        if respiratory_rate >= 21:
            SIRS_criteria[2] = 1
        if glucose >= 140 and glucose < 200:
            SIRS_criteria[3] = 1
            if diagnosis.find('Diabetes'):
                SIRS_criteria[3] = 0
        if leukocytes > 12000 or leukocytes < 4000 or blasts_per_100_leukocytes > 10:
            SIRS_criteria[4] = 1
            if colony_stimulating_factors:
                SIRS_criteria[4] = 0

        SIRS_total = SIRS_criteria[0] + SIRS_criteria[1] + SIRS_criteria[2] + SIRS_criteria[3] + SIRS_criteria[4]

        if SIRS_total < 2:
            return 'Continue Monitoring'

        if lactate > 2:
            organ_dysfunction_criteria[0] = 1
        if systolic_blood_pressure < 90 or mean_arterial_pressure < 65:
            organ_dysfunction_criteria[1] = 1
        if creatinine - creatinine_baseline > 0.5:
            organ_dysfunction_criteria[2] = 1
        if bilirubin_total >= 2 and bilirubin_total < 10:
            organ_dysfunction_criteria[3] = 1

        organ_dysfunction_total = organ_dysfunction_criteria[0] + organ_dysfunction_criteria[1] + organ_dysfunction_criteria[2] + organ_dysfunction_criteria[3]

        if organ_dysfunction_total > 0:
            if organ_dysfunction_total == 1 and organ_dysfunction_criteria[2] == 1:
                if diagnosis.find('ESRD'):
                    return 'Continue Monitoring'
                elif recombinant_human_erythropoientins:
                    return 'Continue Monitoring'
                else:
                    'Sepsis Alert'
            else:
                'Sepsis Alert'
        elif SIRS_total < 3:
            return 'Continue Monitoring'
        else:
            return 'SIRS Alert'

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
