from kivy.app import App
from kivy.logger import Logger
from kivy.uix.label import Label
from openmrs import RESTConnection


class RestApp(App):

    def __init__(self, **kwargs):
        super(RestApp, self).__init__(**kwargs)

    def connect(self):
        self.openmrs_connection = RESTConnection('localhost', 8080, self.root.ids.username.text, self.root.ids.password.text)

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
            self.root.current = 'summary'

        if patient_uuid == 'NULL':
            self.root.ids.retrieve.text = 'Unable to retrieve patient information.'
            self.root.ids.retrieve2.text = 'Please verify that OpenMRS ID is correct and try again.'

    def on_patient_not_loaded(self, request, error):
        self.root.ids.retrieve.text = 'Unable to connect.'
        self.root.ids.retrieve2.text = 'Please verify internet connection and try again.'
        Logger.error('RestApp: {error}'.format(error=error))

    def load_encounters(self, patient_uuid):
        encounters_request = 'encounter?patient={patient_uuid}&limit=10&v=full'.format(patient_uuid=patient_uuid)
        self.openmrs_connection.send_request(encounters_request, None, self.on_encounters_loaded,
                                             self.on_encounters_not_loaded, self.on_encounters_not_loaded)

    def on_encounters_loaded(self, request, response):
        data = []

        for result in response['results']:
            for ob in result['obs']:
                data.append(ob['display'])
                data.append(ob['obsDatetime'])

        self.display_diagnosis(data)
        self.display_vitals(data)
        self.display_labs(data)

    def display_diagnosis(self, data):
        timestamp = 'N/A'
        diagnosis_array = []

        diagnosis_layout = self.root.ids.diagnosis
        diagnosis_timestamp_layout = self.root.ids.diagnosis_timestamp
        for i in range(len(data)):
            if data[i].find('Visit Diagnoses:') != -1:
                timestamp = data[i + 1]
                diagnosis_array.append(data[i])
                diagnosis_array.append(data[i + 1])

        for j in range(len(diagnosis_array)):
            if diagnosis_array[j] == timestamp:
                diagnosis_layout.add_widget(Label(text=diagnosis_array[j - 1]))
                diagnosis_timestamp_layout.add_widget(Label(text=timestamp))

    def display_vitals(self, data):
        vitals = ['Height (cm):', 'Weight (kg):', 'Temperature (C):', 'Pulse:', 'Respiratory rate:', 'Systolic blood pressure:', 'Diastolic blood pressure:', 'Blood oxygen saturation:']
        recent = 'N/A'
        timestamp = 'N/A'

        vitals_layout = self.root.ids.vitals
        vitals_timestamp_layout = self.root.ids.vitals_timestamp
        for vital in vitals:
            for i in range(len(data)):
                if data[i].find(vital) != -1:
                    recent = data[i]
                    timestamp = data[i + 1]
            vitals_layout.add_widget(Label(text=recent))
            vitals_timestamp_layout.add_widget(Label(text=timestamp))

    def display_labs(self, data):
        labs = ['Leukocytes (#/mL)', 'Blasts per 100 Leukocytes', 'Platelets', 'Partial Thromboplastin Time', 'Glucose', 'Lactate', 'Creatinine',
                'Bilirubin Direct', 'Bilirubin Total', 'Blood Cultures, Bacteria', 'Blood Cultures, Fungus', 'Blood Cultures, Viruses', 'Urinalysis']
        recent = 'N/A'
        timestamp = 'N/A'

        labs_layout = self.root.ids.labs
        labs_timestamp_layout = self.root.ids.labs_timestamp
        for lab in labs:
            for i in range(len(data)):
                if data[i].find(lab) != -1:
                    recent = data[i]
                    timestamp = data[i + 1]
            labs_layout.add_widget(Label(text=recent))
            labs_timestamp_layout.add_widget(Label(text=timestamp))

    def on_encounters_not_loaded(self, request, error):
        self.root.ids.patient.add_widget(Label(text='[Failed to load patient information.  Please try again.]'))
        Logger.error('RestApp: {error}'.format(error=error))


if __name__ == "__main__":
    app = RestApp()
    app.run()
