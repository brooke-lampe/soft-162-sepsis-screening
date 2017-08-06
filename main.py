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
    global patient_info
    patient_info = 'null'

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

    def retrieve(self):
        pass

    def determination(self, colony_stimulating_factors, heparin, recombinant_human_erythropoientins):

        #Fill in user interface information
        determination_layout = self.root.ids.determination_layout

        self.root.ids.patient_info = patient_info

        date_object = datetime.now()
        current_time = date_object.strftime('%Y-%m-%d@%H:%M:%S')
        self.root.ids.determination_timestamp = current_time

        #Pull required data from the database

        #Vitals Observations
        temperature = float(self.vitals_observations.get('Temperature (C)').obs_value)
        pulse = float(self.vitals_observations.get('Pulse').obs_value)
        respiratory_rate = float(self.vitals_observations.get('Respiratory rate').obs_value)
        systolic_blood_pressure = float(self.vitals_observations.get('Systolic blood pressure').obs_value)
        systolic_blood_pressure_timestamp = self.vitals_observations.get('Systolic blood pressure').obs_datetime
        diastolic_blood_pressure = float(self.vitals_observations.get('Diastolic blood pressure').obs_value)
        diastolic_blood_pressure_timestamp = self.vitals_observations.get('Diastolic blood pressure').obs_datetime

        #Labs Observations
        leukocytes = float(self.lab_observations.get('Leukocytes (#/mL)').obs_value)
        blasts_per_100_leukocytes = float(self.lab_observations.get('Blasts per 100 Leukocytes (%)').obs_value)
        glucose = float(self.lab_observations.get('Glucose in Blood (mg/dL)').obs_value)
        lactate = float(self.lab_observations.get('Lactate in Blood (mmol/L)').obs_value)
        lactate_timestamp = self.lab_observations.get('Lactate in Blood (mmol/L)').obs_datetime
        #creatinine_difference = float(self.lab_observations.get_creatinine_change)
        creatinine_difference = 0.25
        #creatinine_timestamp = self.lab_observations.get('Creatinine in Blood (mg/dL)').obs_datetime
        creatinine_timestamp = lactate_timestamp
        bilirubin_total = float(self.lab_observations.get('Bilirubin Total (mg/dL)').obs_value)
        bilirubin_timestamp = self.lab_observations.get('Bilirubin Total (mg/dL)').obs_datetime
        platelets_timestamp = self.lab_observations.get('Platelets (#/mL)').obs_datetime
        partial_thromboplastin_time_timestamp = self.lab_observations.get('Partial Thromboplastin Time (s)').obs_datetime
        bacteria_culture_timestamp = self.lab_observations.get('Blood Cultures, Bacteria').obs_datetime
        fungus_culture_timestamp = self.lab_observations.get('Blood Cultures, Fungus').obs_datetime
        virus_culture_timestamp = self.lab_observations.get('Blood Cultures, Viruses').obs_datetime
        urinalysis_timestamp = self.lab_observations.get('Urinalysis').obs_datetime

        #SIRS criteria are temperature, pulse, respiratory rate, glucose, and leukocytes / blasts per 100 leukocytes
        SIRS_criteria = [0, 0, 0, 0, 0]

        #Organ dysfunction criteria are lactate, systolic blood pressure / mean arterial blood pressure, creatinine, and bilirubin
        organ_dysfunction_criteria = [0, 0, 0, 0]

        #Suggested labs are lactate, creatinine, bilirubin, platelets, partial thromboplastin time, blood cultures (3), and urinalysis
        suggested_labs = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        labs_string = ['Lactate', 'Creatinine', 'Bilirubin Total', 'Platelets', 'Partial Thromboplastin Time',
                       'Blood Cultures, Bacteria', 'Blood Cultures, Fungus', 'Blood Cultures, Viruses', 'Urinalysis']

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

        #Determine what criteria of organ dysfunction are met (with observations that are sufficiently recent)
        #If observations are not sufficiently recent, suggest labs
        if (date_object - lactate_timestamp) < timedelta(hours = 12):
            if lactate > 2:
                organ_dysfunction_criteria[0] = 1
        else:
            suggested_labs[0] = 1

        if systolic_blood_pressure < 90 and (date_object - systolic_blood_pressure_timestamp) < timedelta(hours = 30):
            organ_dysfunction_criteria[1] = 1
        if mean_arterial_pressure < 65 and (date_object - systolic_blood_pressure_timestamp) < timedelta(hours = 30) and (date_object - diastolic_blood_pressure_timestamp) < timedelta(hours = 30):
            organ_dysfunction_criteria[1] = 1

        if (date_object - creatinine_timestamp) < timedelta(hours = 30):
            if creatinine_difference > 0.5:
                organ_dysfunction_criteria[2] = 1
        else:
            suggested_labs[1] = 1

        if (date_object - bilirubin_timestamp) < timedelta(hours = 30):
            if bilirubin_total >= 2 and bilirubin_total < 10:
                organ_dysfunction_criteria[3] = 1
        else:
            suggested_labs[2] = 1

        #Additional labs to be suggested if labs are not within timeframe
        if (date_object - platelets_timestamp) < timedelta(hours = 30):
            suggested_labs[3] = 1
        if (date_object - partial_thromboplastin_time_timestamp) < timedelta(hours = 30):
            suggested_labs[4] = 1
            if heparin:
                suggested_labs[4] = 0
        if (date_object - bacteria_culture_timestamp) < timedelta(hours = 30):
            suggested_labs[5] = 1
        if (date_object - fungus_culture_timestamp) < timedelta(hours = 30):
            suggested_labs[6] = 1
        if (date_object - virus_culture_timestamp) < timedelta(hours = 30):
            suggested_labs[7] = 1
        if (date_object - urinalysis_timestamp) < timedelta(hours = 30):
            suggested_labs[8] = 1

        #Determine the number of organ dysfunction criteria met
        organ_dysfunction_total = organ_dysfunction_criteria[0] + organ_dysfunction_criteria[1] + organ_dysfunction_criteria[2] + organ_dysfunction_criteria[3]

        #Determine if sufficient criteria have been met to diagnose SIRS or sepsis
        if SIRS_total < 2:
            determination_layout.add_widget(Label(text='Indeterminate'))
        elif organ_dysfunction_total > 0:
            if organ_dysfunction_total == 1 and organ_dysfunction_criteria[2] == 1:
                if self.diagnose.get('ESRD'):
                    determination_layout.add_widget(Label(text='Indeterminate'))
                elif recombinant_human_erythropoientins:
                    determination_layout.add_widget(Label(text='Indeterminate'))
                else:
                    determination_layout.add_widget(Label(text='Sepsis Likely'))
            else:
                determination_layout.add_widget(Label(text='Sepsis Likely'))
        elif SIRS_total < 3:
            determination_layout.add_widget(Label(text='Indeterminate'))
        else:
            #When firing SIRS alert, suggest labs/cultures not found within timeframe in the database
            determination_layout.add_widget(Label(text='SIRS Likely'))
            determination_layout.add_widget(Label(text='Suggested Labs:'))

            count = 0

            for i in range(len(suggested_labs)):
                if suggested_labs[i] == 1:
                    determination_layout.add_widget(Label(text=labs_string[i]))
                    count = 1

            if count == 0:
                determination_layout.add_widget(Label(text='N/A'))


if __name__ == "__main__":
    app = RestApp()
    app.run()
