from unittest import TestCase, main
from main import RestApp
from datetime import *

from observations import Observation, Creatinine


class TestRestApp(TestCase):

    def test_indeterminate_1(self):
        app = RestApp()
        app.load_config()
        app.load_kv(filename=app.kv_file)
        patient_id_and_name = '10000X - Brooke Lampe'
        current_timestamp = datetime(2017, 8, 6, 15, 14, 52, 608206)
        obs_timestamp = datetime(2017, 8, 6, 13, 14, 52, 608206)
        diabetes_i = False
        diabetes_ii = False
        ESRD = False
        temperature = Observation('Vitals', 'Temperature (C)', 37.5, obs_timestamp)
        pulse = Observation('Vitals', 'Pulse', 90, obs_timestamp)
        respiratory_rate = Observation('Vitals', 'Respiratory rate', 20, obs_timestamp)
        systolic_blood_pressure = Observation('Vitals', 'Systolic blood pressure', 120, obs_timestamp)
        diastolic_blood_pressure = Observation('Vitals', 'Diastolic blood pressure', 80, obs_timestamp)
        leukocytes = Observation('Labs', 'Leukocytes (#/mL)', 10000, obs_timestamp)
        blasts_per_100_leukocytes = Observation('Labs', 'Blasts per 100 Leukocytes (%)', 8, obs_timestamp)
        glucose = Observation('Labs', 'Glucose in Blood (mg/dL)', 120, obs_timestamp)
        lactate = Observation('Labs', 'Lactate in Blood (mmol/L)', 1, obs_timestamp)
        creatinine = Creatinine('Labs', 'Creatinine in Blood (mg/dL)', 0.75, 0.5, obs_timestamp, 0)
        bilirubin_total = Observation('Labs', 'Bilirubin Total (mg/dL)', 12, obs_timestamp)
        platelets_timestamp = 0
        partial_thromboplastin_time_timestamp = 0
        bacteria_culture_timestamp = 0
        fungus_culture_timestamp = 0
        virus_culture_timestamp = 0
        urinalysis_timestamp = 0
        colony_stimulating_factors = False
        heparin = False
        recombinant_human_erythropoientins = False

        app.determination(patient_id_and_name, current_timestamp, diabetes_i, diabetes_ii, ESRD, temperature, pulse, respiratory_rate, systolic_blood_pressure, diastolic_blood_pressure,
                      leukocytes, blasts_per_100_leukocytes, glucose, lactate, creatinine, bilirubin_total,
                      platelets_timestamp, partial_thromboplastin_time_timestamp, bacteria_culture_timestamp, fungus_culture_timestamp, virus_culture_timestamp,
                      urinalysis_timestamp, colony_stimulating_factors, heparin, recombinant_human_erythropoientins)
        self.assertEqual(app.root.ids.determination_summary.text, 'Indeterminate')
        self.assertEqual(app.SIRS_criteria[0], 0)
        self.assertEqual(app.SIRS_criteria[1], 0)
        self.assertEqual(app.SIRS_criteria[2], 0)
        self.assertEqual(app.SIRS_criteria[3], 0)
        self.assertEqual(app.SIRS_criteria[4], 0)
        self.assertEqual(app.organ_criteria[0], 0)
        self.assertEqual(app.organ_criteria[1], 0)
        self.assertEqual(app.organ_criteria[2], 0)
        self.assertEqual(app.organ_criteria[3], 0)

    def test_indeterminate_2(self):
        app = RestApp()
        app.load_config()
        app.load_kv(filename=app.kv_file)
        patient_id_and_name = '10000X - Brooke Lampe'
        current_timestamp = datetime(2017, 8, 6, 15, 14, 52, 608206)
        obs_timestamp = datetime(2017, 8, 6, 13, 14, 52, 608206)
        diabetes_i = False
        diabetes_ii = False
        ESRD = True
        temperature = Observation('Vitals', 'Temperature (C)', 41, obs_timestamp)
        pulse = Observation('Vitals', 'Pulse', 99, obs_timestamp)
        respiratory_rate = Observation('Vitals', 'Respiratory rate', 20, obs_timestamp)
        systolic_blood_pressure = Observation('Vitals', 'Systolic blood pressure', 120, obs_timestamp)
        diastolic_blood_pressure = Observation('Vitals', 'Diastolic blood pressure', 80, obs_timestamp)
        leukocytes = Observation('Labs', 'Leukocytes (#/mL)', 10000, obs_timestamp)
        blasts_per_100_leukocytes = Observation('Labs', 'Blasts per 100 Leukocytes (%)', 8, obs_timestamp)
        glucose = Observation('Labs', 'Glucose in Blood (mg/dL)', 120, obs_timestamp)
        lactate = Observation('Labs', 'Lactate in Blood (mmol/L)', 1, obs_timestamp)
        creatinine = Creatinine('Labs', 'Creatinine in Blood (mg/dL)', 1.75, 0.5, obs_timestamp, 0)
        bilirubin_total = Observation('Labs', 'Bilirubin Total (mg/dL)', 12, obs_timestamp)
        platelets_timestamp = 0
        partial_thromboplastin_time_timestamp = 0
        bacteria_culture_timestamp = 0
        fungus_culture_timestamp = 0
        virus_culture_timestamp = 0
        urinalysis_timestamp = 0
        colony_stimulating_factors = False
        heparin = False
        recombinant_human_erythropoientins = False

        app.determination(patient_id_and_name, current_timestamp, diabetes_i, diabetes_ii, ESRD, temperature, pulse, respiratory_rate, systolic_blood_pressure, diastolic_blood_pressure,
                      leukocytes, blasts_per_100_leukocytes, glucose, lactate, creatinine, bilirubin_total,
                      platelets_timestamp, partial_thromboplastin_time_timestamp, bacteria_culture_timestamp, fungus_culture_timestamp, virus_culture_timestamp,
                      urinalysis_timestamp, colony_stimulating_factors, heparin, recombinant_human_erythropoientins)
        self.assertEqual(app.root.ids.determination_summary.text, 'Indeterminate')
        self.assertEqual(app.SIRS_criteria[0], 1)
        self.assertEqual(app.SIRS_criteria[1], 1)
        self.assertEqual(app.SIRS_criteria[2], 0)
        self.assertEqual(app.SIRS_criteria[3], 0)
        self.assertEqual(app.SIRS_criteria[4], 0)
        self.assertEqual(app.organ_criteria[0], 0)
        self.assertEqual(app.organ_criteria[1], 0)
        self.assertEqual(app.organ_criteria[2], 1)
        self.assertEqual(app.organ_criteria[3], 0)

    def test_indeterminate_3(self):
        app = RestApp()
        app.load_config()
        app.load_kv(filename=app.kv_file)
        patient_id_and_name = '10000X - Brooke Lampe'
        current_timestamp = datetime(2017, 8, 6, 15, 14, 52, 608206)
        obs_timestamp = datetime(2017, 8, 6, 13, 14, 52, 608206)
        diabetes_i = False
        diabetes_ii = False
        ESRD = False
        temperature = Observation('Vitals', 'Temperature (C)', 41, obs_timestamp)
        pulse = Observation('Vitals', 'Pulse', 99, obs_timestamp)
        respiratory_rate = Observation('Vitals', 'Respiratory rate', 20, obs_timestamp)
        systolic_blood_pressure = Observation('Vitals', 'Systolic blood pressure', 120, obs_timestamp)
        diastolic_blood_pressure = Observation('Vitals', 'Diastolic blood pressure', 80, obs_timestamp)
        leukocytes = Observation('Labs', 'Leukocytes (#/mL)', 10000, obs_timestamp)
        blasts_per_100_leukocytes = Observation('Labs', 'Blasts per 100 Leukocytes (%)', 8, obs_timestamp)
        glucose = Observation('Labs', 'Glucose in Blood (mg/dL)', 120, obs_timestamp)
        lactate = Observation('Labs', 'Lactate in Blood (mmol/L)', 1, obs_timestamp)
        creatinine = Creatinine('Labs', 'Creatinine in Blood (mg/dL)', 1.75, 0.5, obs_timestamp, 0)
        bilirubin_total = Observation('Labs', 'Bilirubin Total (mg/dL)', 12, obs_timestamp)
        platelets_timestamp = 0
        partial_thromboplastin_time_timestamp = 0
        bacteria_culture_timestamp = 0
        fungus_culture_timestamp = 0
        virus_culture_timestamp = 0
        urinalysis_timestamp = 0
        colony_stimulating_factors = False
        heparin = False
        recombinant_human_erythropoientins = True

        app.determination(patient_id_and_name, current_timestamp, diabetes_i, diabetes_ii, ESRD, temperature, pulse, respiratory_rate, systolic_blood_pressure, diastolic_blood_pressure,
                      leukocytes, blasts_per_100_leukocytes, glucose, lactate, creatinine, bilirubin_total,
                      platelets_timestamp, partial_thromboplastin_time_timestamp, bacteria_culture_timestamp, fungus_culture_timestamp, virus_culture_timestamp,
                      urinalysis_timestamp, colony_stimulating_factors, heparin, recombinant_human_erythropoientins)
        self.assertEqual(app.root.ids.determination_summary.text, 'Indeterminate')
        self.assertEqual(app.SIRS_criteria[0], 1)
        self.assertEqual(app.SIRS_criteria[1], 1)
        self.assertEqual(app.SIRS_criteria[2], 0)
        self.assertEqual(app.SIRS_criteria[3], 0)
        self.assertEqual(app.SIRS_criteria[4], 0)
        self.assertEqual(app.organ_criteria[0], 0)
        self.assertEqual(app.organ_criteria[1], 0)
        self.assertEqual(app.organ_criteria[2], 1)
        self.assertEqual(app.organ_criteria[3], 0)

    def test_sirs_1(self):
        app = RestApp()
        app.load_config()
        app.load_kv(filename=app.kv_file)
        patient_id_and_name = '10000X - Brooke Lampe'
        current_timestamp = datetime(2017, 8, 6, 15, 14, 52, 608206)
        obs_timestamp = datetime(2017, 8, 6, 13, 14, 52, 608206)
        diabetes_i = True
        diabetes_ii = True
        ESRD = True
        temperature = Observation('Vitals', 'Temperature (C)', 39, obs_timestamp)
        pulse = Observation('Vitals', 'Pulse', 100, obs_timestamp)
        respiratory_rate = Observation('Vitals', 'Respiratory rate', 22, obs_timestamp)
        systolic_blood_pressure = Observation('Vitals', 'Systolic blood pressure', 120, obs_timestamp)
        diastolic_blood_pressure = Observation('Vitals', 'Diastolic blood pressure', 80, obs_timestamp)
        leukocytes = Observation('Labs', 'Leukocytes (#/mL)', 15000, obs_timestamp)
        blasts_per_100_leukocytes = Observation('Labs', 'Blasts per 100 Leukocytes (%)', 12, obs_timestamp)
        glucose = Observation('Labs', 'Glucose in Blood (mg/dL)', 160, obs_timestamp)
        lactate = Observation('Labs', 'Lactate in Blood (mmol/L)', 1, obs_timestamp)
        creatinine = Creatinine('Labs', 'Creatinine in Blood (mg/dL)', 0.75, 0.5, obs_timestamp, 0)
        bilirubin_total = Observation('Labs', 'Bilirubin Total (mg/dL)', 12, obs_timestamp)
        platelets_timestamp = obs_timestamp
        partial_thromboplastin_time_timestamp = obs_timestamp
        bacteria_culture_timestamp = obs_timestamp
        fungus_culture_timestamp = obs_timestamp
        virus_culture_timestamp = obs_timestamp
        urinalysis_timestamp = obs_timestamp
        colony_stimulating_factors = True
        heparin = False
        recombinant_human_erythropoientins = True

        app.determination(patient_id_and_name, current_timestamp, diabetes_i, diabetes_ii, ESRD, temperature, pulse, respiratory_rate, systolic_blood_pressure, diastolic_blood_pressure,
                      leukocytes, blasts_per_100_leukocytes, glucose, lactate, creatinine, bilirubin_total,
                      platelets_timestamp, partial_thromboplastin_time_timestamp, bacteria_culture_timestamp, fungus_culture_timestamp, virus_culture_timestamp,
                      urinalysis_timestamp, colony_stimulating_factors, heparin, recombinant_human_erythropoientins)
        self.assertEqual(app.root.ids.determination_summary.text, 'SIRS Likely')
        self.assertEqual(app.SIRS_criteria[0], 1)
        self.assertEqual(app.SIRS_criteria[1], 1)
        self.assertEqual(app.SIRS_criteria[2], 1)
        self.assertEqual(app.SIRS_criteria[3], 0)
        self.assertEqual(app.SIRS_criteria[4], 0)
        self.assertEqual(app.organ_criteria[0], 0)
        self.assertEqual(app.organ_criteria[1], 0)
        self.assertEqual(app.organ_criteria[2], 0)
        self.assertEqual(app.organ_criteria[3], 0)
        self.assertEqual(app.suggested_labs[0], 0)
        self.assertEqual(app.suggested_labs[1], 0)
        self.assertEqual(app.suggested_labs[2], 0)
        self.assertEqual(app.suggested_labs[3], 0)
        self.assertEqual(app.suggested_labs[4], 0)
        self.assertEqual(app.suggested_labs[5], 0)
        self.assertEqual(app.suggested_labs[6], 0)
        self.assertEqual(app.suggested_labs[7], 0)
        self.assertEqual(app.suggested_labs[8], 0)

    def test_sirs_2(self):
        app = RestApp()
        app.load_config()
        app.load_kv(filename=app.kv_file)
        patient_id_and_name = '10000X - Brooke Lampe'
        current_timestamp = datetime(2017, 8, 6, 15, 14, 52, 608206)
        obs_timestamp = datetime(2017, 8, 6, 13, 14, 52, 608206)
        diabetes_i = False
        diabetes_ii = False
        ESRD = False
        temperature = Observation('Vitals', 'Temperature (C)', 40, obs_timestamp)
        pulse = Observation('Vitals', 'Pulse', 90, obs_timestamp)
        respiratory_rate = Observation('Vitals', 'Respiratory rate', 20, obs_timestamp)
        systolic_blood_pressure = Observation('Vitals', 'Systolic blood pressure', 120, obs_timestamp)
        diastolic_blood_pressure = Observation('Vitals', 'Diastolic blood pressure', 80, obs_timestamp)
        leukocytes = Observation('Labs', 'Leukocytes (#/mL)', 15000, obs_timestamp)
        blasts_per_100_leukocytes = Observation('Labs', 'Blasts per 100 Leukocytes (%)', 8, obs_timestamp)
        glucose = Observation('Labs', 'Glucose in Blood (mg/dL)', 160, obs_timestamp)
        lactate = Observation('Labs', 'Lactate in Blood (mmol/L)', 1, obs_timestamp)
        creatinine = Creatinine('Labs', 'Creatinine in Blood (mg/dL)', 0.75, 0.5, obs_timestamp, 0)
        bilirubin_total = Observation('Labs', 'Bilirubin Total (mg/dL)', 12, obs_timestamp)
        platelets_timestamp = 0
        partial_thromboplastin_time_timestamp = 0
        bacteria_culture_timestamp = 0
        fungus_culture_timestamp = 0
        virus_culture_timestamp = 0
        urinalysis_timestamp = 0
        colony_stimulating_factors = False
        heparin = False
        recombinant_human_erythropoientins = False

        app.determination(patient_id_and_name, current_timestamp, diabetes_i, diabetes_ii, ESRD, temperature, pulse, respiratory_rate, systolic_blood_pressure, diastolic_blood_pressure,
                      leukocytes, blasts_per_100_leukocytes, glucose, lactate, creatinine, bilirubin_total,
                      platelets_timestamp, partial_thromboplastin_time_timestamp, bacteria_culture_timestamp, fungus_culture_timestamp, virus_culture_timestamp,
                      urinalysis_timestamp, colony_stimulating_factors, heparin, recombinant_human_erythropoientins)
        self.assertEqual(app.root.ids.determination_summary.text, 'SIRS Likely')
        self.assertEqual(app.SIRS_criteria[0], 1)
        self.assertEqual(app.SIRS_criteria[1], 0)
        self.assertEqual(app.SIRS_criteria[2], 0)
        self.assertEqual(app.SIRS_criteria[3], 1)
        self.assertEqual(app.SIRS_criteria[4], 1)
        self.assertEqual(app.organ_criteria[0], 0)
        self.assertEqual(app.organ_criteria[1], 0)
        self.assertEqual(app.organ_criteria[2], 0)
        self.assertEqual(app.organ_criteria[3], 0)
        self.assertEqual(app.suggested_labs[0], 0)
        self.assertEqual(app.suggested_labs[1], 0)
        self.assertEqual(app.suggested_labs[2], 0)
        self.assertEqual(app.suggested_labs[3], 1)
        self.assertEqual(app.suggested_labs[4], 1)
        self.assertEqual(app.suggested_labs[5], 1)
        self.assertEqual(app.suggested_labs[6], 1)
        self.assertEqual(app.suggested_labs[7], 1)
        self.assertEqual(app.suggested_labs[8], 1)

    def test_sirs_3(self):
        app = RestApp()
        app.load_config()
        app.load_kv(filename=app.kv_file)
        patient_id_and_name = '10000X - Brooke Lampe'
        current_timestamp = datetime(2017, 8, 6, 15, 14, 52, 608206)
        obs_timestamp = datetime(2017, 8, 6, 13, 14, 52, 608206)
        diabetes_i = False
        diabetes_ii = False
        ESRD = False
        temperature = Observation('Vitals', 'Temperature (C)', 40, obs_timestamp)
        pulse = Observation('Vitals', 'Pulse', 90, obs_timestamp)
        respiratory_rate = Observation('Vitals', 'Respiratory rate', 20, obs_timestamp)
        systolic_blood_pressure = Observation('Vitals', 'Systolic blood pressure', 120, obs_timestamp)
        diastolic_blood_pressure = Observation('Vitals', 'Diastolic blood pressure', 80, obs_timestamp)
        leukocytes = Observation('Labs', 'Leukocytes (#/mL)', 15000, obs_timestamp)
        blasts_per_100_leukocytes = Observation('Labs', 'Blasts per 100 Leukocytes (%)', 8, obs_timestamp)
        glucose = Observation('Labs', 'Glucose in Blood (mg/dL)', 160, obs_timestamp)
        lactate = Observation('Labs', 'Lactate in Blood (mmol/L)', 0, 0)
        creatinine = Creatinine('Labs', 'Creatinine in Blood (mg/dL)', 0, 0, 0, 0)
        bilirubin_total = Observation('Labs', 'Bilirubin Total (mg/dL)', 0, 0)
        platelets_timestamp = 0
        partial_thromboplastin_time_timestamp = 0
        bacteria_culture_timestamp = 0
        fungus_culture_timestamp = 0
        virus_culture_timestamp = 0
        urinalysis_timestamp = 0
        colony_stimulating_factors = False
        heparin = False
        recombinant_human_erythropoientins = False

        app.determination(patient_id_and_name, current_timestamp, diabetes_i, diabetes_ii, ESRD, temperature, pulse, respiratory_rate, systolic_blood_pressure, diastolic_blood_pressure,
                      leukocytes, blasts_per_100_leukocytes, glucose, lactate, creatinine, bilirubin_total,
                      platelets_timestamp, partial_thromboplastin_time_timestamp, bacteria_culture_timestamp, fungus_culture_timestamp, virus_culture_timestamp,
                      urinalysis_timestamp, colony_stimulating_factors, heparin, recombinant_human_erythropoientins)
        self.assertEqual(app.root.ids.determination_summary.text, 'SIRS Likely')
        self.assertEqual(app.SIRS_criteria[0], 1)
        self.assertEqual(app.SIRS_criteria[1], 0)
        self.assertEqual(app.SIRS_criteria[2], 0)
        self.assertEqual(app.SIRS_criteria[3], 1)
        self.assertEqual(app.SIRS_criteria[4], 1)
        self.assertEqual(app.organ_criteria[0], 0)
        self.assertEqual(app.organ_criteria[1], 0)
        self.assertEqual(app.organ_criteria[2], 0)
        self.assertEqual(app.organ_criteria[3], 0)
        self.assertEqual(app.suggested_labs[0], 1)
        self.assertEqual(app.suggested_labs[1], 1)
        self.assertEqual(app.suggested_labs[2], 1)
        self.assertEqual(app.suggested_labs[3], 1)
        self.assertEqual(app.suggested_labs[4], 1)
        self.assertEqual(app.suggested_labs[5], 1)
        self.assertEqual(app.suggested_labs[6], 1)
        self.assertEqual(app.suggested_labs[7], 1)
        self.assertEqual(app.suggested_labs[8], 1)

    def test_sepsis_1(self):
        app = RestApp()
        app.load_config()
        app.load_kv(filename=app.kv_file)
        patient_id_and_name = '10000X - Brooke Lampe'
        current_timestamp = datetime(2017, 8, 6, 15, 14, 52, 608206)
        obs_timestamp = datetime(2017, 8, 6, 13, 14, 52, 608206)
        diabetes_i = True
        diabetes_ii = True
        ESRD = True
        temperature = Observation('Vitals', 'Temperature (C)', 34, obs_timestamp)
        pulse = Observation('Vitals', 'Pulse', 100, obs_timestamp)
        respiratory_rate = Observation('Vitals', 'Respiratory rate', 22, obs_timestamp)
        systolic_blood_pressure = Observation('Vitals', 'Systolic blood pressure', 60, obs_timestamp)
        diastolic_blood_pressure = Observation('Vitals', 'Diastolic blood pressure', 40, obs_timestamp)
        leukocytes = Observation('Labs', 'Leukocytes (#/mL)', 3000, obs_timestamp)
        blasts_per_100_leukocytes = Observation('Labs', 'Blasts per 100 Leukocytes (%)', 12, obs_timestamp)
        glucose = Observation('Labs', 'Glucose in Blood (mg/dL)', 120, obs_timestamp)
        lactate = Observation('Labs', 'Lactate in Blood (mmol/L)', 4, obs_timestamp)
        creatinine = Creatinine('Labs', 'Creatinine in Blood (mg/dL)', 1.75, 0.5, obs_timestamp, 0)
        bilirubin_total = Observation('Labs', 'Bilirubin Total (mg/dL)', 8, obs_timestamp)
        platelets_timestamp = 0
        partial_thromboplastin_time_timestamp = 0
        bacteria_culture_timestamp = 0
        fungus_culture_timestamp = 0
        virus_culture_timestamp = 0
        urinalysis_timestamp = 0
        colony_stimulating_factors = False
        heparin = True
        recombinant_human_erythropoientins = True

        app.determination(patient_id_and_name, current_timestamp, diabetes_i, diabetes_ii, ESRD, temperature, pulse, respiratory_rate, systolic_blood_pressure, diastolic_blood_pressure,
                      leukocytes, blasts_per_100_leukocytes, glucose, lactate, creatinine, bilirubin_total,
                      platelets_timestamp, partial_thromboplastin_time_timestamp, bacteria_culture_timestamp, fungus_culture_timestamp, virus_culture_timestamp,
                      urinalysis_timestamp, colony_stimulating_factors, heparin, recombinant_human_erythropoientins)
        self.assertEqual(app.root.ids.determination_summary.text, 'Sepsis Likely')
        self.assertEqual(app.SIRS_criteria[0], 1)
        self.assertEqual(app.SIRS_criteria[1], 1)
        self.assertEqual(app.SIRS_criteria[2], 1)
        self.assertEqual(app.SIRS_criteria[3], 0)
        self.assertEqual(app.SIRS_criteria[4], 1)
        self.assertEqual(app.organ_criteria[0], 1)
        self.assertEqual(app.organ_criteria[1], 1)
        self.assertEqual(app.organ_criteria[2], 1)
        self.assertEqual(app.organ_criteria[3], 1)


    def test_sepsis_2(self):
        app = RestApp()
        app.load_config()
        app.load_kv(filename=app.kv_file)
        patient_id_and_name = '10000X - Brooke Lampe'
        current_timestamp = datetime(2017, 8, 6, 15, 14, 52, 608206)
        obs_timestamp = datetime(2017, 8, 6, 13, 14, 52, 608206)
        diabetes_i = True
        diabetes_ii = True
        ESRD = False
        temperature = Observation('Vitals', 'Temperature (C)', 34, obs_timestamp)
        pulse = Observation('Vitals', 'Pulse', 100, obs_timestamp)
        respiratory_rate = Observation('Vitals', 'Respiratory rate', 22, obs_timestamp)
        systolic_blood_pressure = Observation('Vitals', 'Systolic blood pressure', 120, obs_timestamp)
        diastolic_blood_pressure = Observation('Vitals', 'Diastolic blood pressure', 80, obs_timestamp)
        leukocytes = Observation('Labs', 'Leukocytes (#/mL)', 3000, obs_timestamp)
        blasts_per_100_leukocytes = Observation('Labs', 'Blasts per 100 Leukocytes (%)', 12, obs_timestamp)
        glucose = Observation('Labs', 'Glucose in Blood (mg/dL)', 120, obs_timestamp)
        lactate = Observation('Labs', 'Lactate in Blood (mmol/L)', 1, obs_timestamp)
        creatinine = Creatinine('Labs', 'Creatinine in Blood (mg/dL)', 1.75, 0.5, obs_timestamp, 0)
        bilirubin_total = Observation('Labs', 'Bilirubin Total (mg/dL)', 12, obs_timestamp)
        platelets_timestamp = 0
        partial_thromboplastin_time_timestamp = 0
        bacteria_culture_timestamp = 0
        fungus_culture_timestamp = 0
        virus_culture_timestamp = 0
        urinalysis_timestamp = 0
        colony_stimulating_factors = False
        heparin = True
        recombinant_human_erythropoientins = False

        app.determination(patient_id_and_name, current_timestamp, diabetes_i, diabetes_ii, ESRD, temperature, pulse, respiratory_rate, systolic_blood_pressure, diastolic_blood_pressure,
                      leukocytes, blasts_per_100_leukocytes, glucose, lactate, creatinine, bilirubin_total,
                      platelets_timestamp, partial_thromboplastin_time_timestamp, bacteria_culture_timestamp, fungus_culture_timestamp, virus_culture_timestamp,
                      urinalysis_timestamp, colony_stimulating_factors, heparin, recombinant_human_erythropoientins)
        self.assertEqual(app.root.ids.determination_summary.text, 'Sepsis Likely')
        self.assertEqual(app.SIRS_criteria[0], 1)
        self.assertEqual(app.SIRS_criteria[1], 1)
        self.assertEqual(app.SIRS_criteria[2], 1)
        self.assertEqual(app.SIRS_criteria[3], 0)
        self.assertEqual(app.SIRS_criteria[4], 1)
        self.assertEqual(app.organ_criteria[0], 0)
        self.assertEqual(app.organ_criteria[1], 0)
        self.assertEqual(app.organ_criteria[2], 1)
        self.assertEqual(app.organ_criteria[3], 0)


    if __name__ == '__main__':
        main()
