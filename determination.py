__app_package__ = 'edu.sepsis'


class Determination:

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

        colony_stimulating_factors = False
        heparin = False
        recombinant_human_erythropoientins = False

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
