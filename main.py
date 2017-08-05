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

    def determination(self, colony_stimulating_factors, heparin, recombinant_human_erythropoientins):

        #Pull required data from the database
        temperature = self.lab_observations.get('Temperature (C)').obs_value
        pulse = self.labs_observations.get('Pulse').obs_value
        respiratory_rate = self.labs_observations.get('Respiratory rate').obs_value
        systolic_blood_pressure = self.labs_observations.get('Systolic blood pressure').obs_value
        systolic_blood_pressure_timestamp = self.labs_observations.get('Systolic blood pressure').get_datetime_string
        diastolic_blood_pressure = self.labs_observations.get('Diastolic blood pressure').obs_value
        diastolic_blood_pressure_timestamp = self.labs_observations.get('Diastolic blood pressure').get_datetime_string
        leukocytes = self.labs_observations.get('Leukocytes (#/mL)').obs_value
        blasts_per_100_leukocytes = self.labs_observations.get('Blasts per 100 Leukocytes').obs_value
        glucose = self.labs_observations.get('Glucose in Blood (mg/dL)').obs_value
        lactate = self.labs_observations.get('Lactate in Blood (mmol/L)').obs_value
        lactate_timestamp = self.labs_observations.get('Lactate in Blood (mmol/L)').get_datetime_string
        creatinine_difference = self.labs_observations.get_creatinine_change
        creatinine_timestamp = self.labs_observations.get('Creatinine in Blood (mg/dL)').get_datetime_string
        bilirubin_total = self.labs_observations.get('Bilirubin Total (mg/dL)').obs_value
        bilirubin_timestamp = self.labs_observations.get('Bilirubin Total (mg/dL)').get_datetime_string
        platelets_timestamp = self.labs_observations.get('Platelets (#/mL)').get_datetime_string
        partial_thromboplastin_time_timestamp = self.labs_observations.get('Parial Thromboplastin Time (s)').get_datetime_string
        bacteria_culture_timestamp = self.labs_observations.get('Blood Cultures, Bacteria').get_datetime_string
        fungus_culture_timestamp = self.labs_observations.get('Blood Cultures, Fungus').get_datetime_string
        virus_culture_timestamp = self.labs_observations.get('Blood Cultures, Viruses').get_datetime_string
        urinalysis_timestamp = self.labs_observations.get('Urinalysis').get_datetime_string

        #SIRS criteria are temperature, pulse, respiratory rate, glucose, and leukocytes / blasts per 100 leukocytes
        SIRS_criteria = [0, 0, 0, 0, 0]

        #Organ dysfunction criteria are lactate, systolic blood pressure / mean arterial blood pressure, creatinine, and bilirubin
        organ_dysfunction_criteria = [0, 0, 0, 0]

        #Suggested labs are lactate, creatinine, bilirubin, platelets, partial thromboplastin time, blood cultures (3), and urinalysis
        suggested_labs = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        mean_arterial_pressure = (systolic_blood_pressure + (2 * diastolic_blood_pressure)) / 3

        #Determine what criteria of SIRS are met
        if temperature < 36 or temperature > 38.3:
            SIRS_criteria[0] = 1
        if pulse > 95:
            SIRS_criteria[1] = 1
        if respiratory_rate >= 21:
            SIRS_criteria[2] = 1
        if glucose >= 140 and glucose < 200:
            SIRS_criteria[3] = 1
            if self.diagnose.get('Diabetes Mellitus') or self.diagnose.get('Diabetes Mellitus, Type II'):
                SIRS_criteria[3] = 0
        if leukocytes > 12000 or leukocytes < 4000 or blasts_per_100_leukocytes > 10:
            SIRS_criteria[4] = 1
            if colony_stimulating_factors:
                SIRS_criteria[4] = 0

        #Determine the number of SIRS criteria met
        SIRS_total = SIRS_criteria[0] + SIRS_criteria[1] + SIRS_criteria[2] + SIRS_criteria[3] + SIRS_criteria[4]

        if SIRS_total < 2:
            return 'Continue Monitoring'

        #Determine what criteria of organ dysfunction are met (with observations that are sufficiently recent)
        #If observations are not sufficiently recent, suggest labs
        if (datetime.now() - lactate_timestamp) < timedelta(hours = 12):
            if lactate > 2:
                organ_dysfunction_criteria[0] = 1
        else:
            suggested_labs[0] = 1

        if systolic_blood_pressure < 90 and (datetime.now() - systolic_blood_pressure_timestamp) < timedelta(hours = 30):
            organ_dysfunction_criteria[1] = 1
        if mean_arterial_pressure < 65 and (datetime.now() - systolic_blood_pressure_timestamp) < timedelta(hours = 30) and (datetime.now() - diastolic_blood_pressure_timestamp) < timedelta(hours = 30):
            organ_dysfunction_criteria[1] = 1

        if (datetime.now() - creatinine_timestamp) < timedelta(hours = 30):
            if creatinine_difference > 0.5:
                organ_dysfunction_criteria[2] = 1
        else:
            suggested_labs[1] = 1

        if (datetime.now() - bilirubin_timestamp) < timedelta(hours = 30):
            if bilirubin_total >= 2 and bilirubin_total < 10:
                organ_dysfunction_criteria[3] = 1
        else:
            suggested_labs[2] = 1

        #Additional labs to be suggested if labs are not within timeframe
        if (datetime.now() - platelets_timestamp) < timedelta(hours = 30):
            suggested_labs[3] = 1
        if (datetime.now() - partial_thromboplastin_time_timestamp) < timedelta(hours = 30):
            suggested_labs[4] = 1
            if heparin:
                suggested_labs[4] = 0
        if (datetime.now() - bacteria_culture_timestamp) < timedelta(hours = 30):
            suggested_labs[5] = 1
        if (datetime.now() - fungus_culture_timestamp) < timedelta(hours = 30):
            suggested_labs[6] = 1
        if (datetime.now() - virus_culture_timestamp) < timedelta(hours = 30):
            suggested_labs[7] = 1
        if (datetime.now() - urinalysis_timestamp) < timedelta(hours = 30):
            suggested_labs[8] = 1

        #Determine the number of organ dysfunction criteria met
        organ_dysfunction_total = organ_dysfunction_criteria[0] + organ_dysfunction_criteria[1] + organ_dysfunction_criteria[2] + organ_dysfunction_criteria[3]

        #Determine if sufficient criteria have been met to diagnose SIRS or sepsis
        if organ_dysfunction_total > 0:
            if organ_dysfunction_total == 1 and organ_dysfunction_criteria[2] == 1:
                if self.diagnose.get('ESRD'):
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


if __name__ == "__main__":
    app = RestApp()
    app.run()
