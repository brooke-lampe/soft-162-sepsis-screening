__app_package__ = 'edu.sepsis'


class Observation:

    def __init__(self, obs_type, obs_string, obs_value, obs_datetime):
        self.obs_type = obs_type
        self.obs_string = obs_string
        self.obs_value = obs_value
        self.obs_datetime = obs_datetime

    def __str__(self):
        return '{obs_string}: {obs_value} @ {obs_timestamp}'.format(obs_string=self.obs_string, obs_value=self.obs_value, obs_timestamp=self.obs_datetime.strftime('%Y-%m-%d %H:%M:%S'))

    def get_datetime_string(self):
        return self.obs_datetime.strftime('%Y-%m-%d@%H:%M:%S')


class Diagnosis:

    def __init__(self, diagnosis_string, obs_datetime):
        self.obs_string = diagnosis_string
        self.obs_datetime = obs_datetime

    def __str__(self):
        return 'Diagnosis: {obs_value} @ {obs_timestamp}'.format(obs_value=self.obs_string, obs_timestamp=self.obs_datetime.strftime('%Y-%m-%d %H:%M:%S'))

    def get_datetime_string(self):
        return self.obs_datetime.strftime('%Y-%m-%d@%H:%M:%S')


class Creatinine(Observation):

    def __init__(self, obs_type, obs_string, obs_value, obs_baseline,  obs_datetime, visit_uuid):
        super(Creatinine, self).__init__(obs_type, obs_string, obs_value, obs_datetime)
        self.obs_baseline = obs_baseline
        self.visit_id = visit_uuid

    def update_creatinine_reading(self, obs_value):
        self.obs_value = obs_value

    def update_baseline(self, obs_value):
        self.obs_baseline = obs_value

    def get_creatinine_change(self):
        return float(self.obs_value) - float(self.obs_baseline)
