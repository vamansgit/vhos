"""Generate realistic Excel demo data for VHOS v2.4."""
from __future__ import annotations

import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

OUT_DIR = Path(__file__).parent

FIRST_NAMES = ["Rajesh", "Priya", "Amit", "Sunita", "Vikram", "Anita", "Suresh", "Kavita",
               "Rahul", "Deepa", "Arjun", "Meena", "Sanjay", "Pooja", "Anil", "Rekha",
               "Manish", "Nisha", "Kiran", "Usha"]
LAST_NAMES = ["Sharma", "Patel", "Kumar", "Singh", "Mehta", "Gupta", "Joshi", "Verma",
               "Rao", "Nair", "Reddy", "Iyer", "Pillai", "Bose", "Dutta", "Chatterjee",
               "Shah", "Kapoor", "Malhotra", "Agarwal"]
DOCTORS = ["Dr. Priya Mehta", "Dr. Rajesh Kumar", "Dr. Sunita Sharma", "Dr. Arjun Verma",
           "Dr. Anita Singh", "Dr. Vikram Rao", "Dr. Kavita Nair", "Dr. Suresh Reddy",
           "Dr. Deepa Iyer", "Dr. Manish Gupta"]
SPECIALTIES = ["Cardiology", "Orthopaedics", "Neurology", "Oncology", "Gynaecology",
                "Paediatrics", "Gastroenterology", "Nephrology", "Pulmonology", "Psychiatry"]
DEPARTMENTS = ["Emergency", "OPD", "ICU", "Surgery", "Radiology", "Pathology",
               "Pharmacy", "Physiotherapy", "Dietetics", "Administration"]
CONDITIONS = ["Type 2 Diabetes", "Hypertension", "CAD", "COPD", "CKD Stage 3",
               "Osteoarthritis", "Breast Cancer", "Schizophrenia", "Epilepsy", "Hypothyroidism"]


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def random_phone():
    return f"+91 9{random.randint(100000000, 999999999)}"


def random_date(days_back=365, days_forward=30):
    delta = random.randint(-days_back, days_forward)
    return (datetime.now() + timedelta(days=delta)).strftime("%Y-%m-%d")


def generate_patients(n=25):
    rows = []
    for i in range(n):
        uhid = f"UHID-{1000+i}"
        name = random_name()
        rows.append({
            "patient_id": uhid,
            "name": name,
            "age": random.randint(18, 85),
            "gender": random.choice(["Male", "Female"]),
            "dob": random_date(days_back=365*70, days_forward=-365*18),
            "phone": random_phone(),
            "email": f"{name.lower().replace(' ', '.')}@email.com",
            "address": f"{random.randint(1, 500)}, {random.choice(['MG Road', 'Brigade Road', 'Residency Road', 'Jayanagar'])}, Bengaluru",
            "blood_group": random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]),
            "primary_condition": random.choice(CONDITIONS),
            "treating_doctor": random.choice(DOCTORS),
            "abha_id": f"91-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            "last_visit_date": random_date(days_back=400, days_forward=0),
            "emergency_contact_name": random_name(),
            "emergency_contact_phone": random_phone(),
            "preferred_language": random.choice(["Hindi", "English", "Kannada", "Tamil", "Telugu"]),
            "opt_out_outreach": random.choice([False, False, False, True]),
            "insurance_provider": random.choice(["Star Health", "HDFC ERGO", "ICICI Lombard", "Bajaj Allianz", "None"]),
            "policy_number": f"POL-{random.randint(100000, 999999)}",
            "coverage_limit": random.choice([300000, 500000, 750000, 1000000]),
        })
    return pd.DataFrame(rows)


def generate_appointments(n=30):
    rows = []
    patients = [f"UHID-{1000+i}" for i in range(20)]
    for i in range(n):
        dt = datetime.now() + timedelta(days=random.randint(-30, 30))
        rows.append({
            "appointment_id": f"APT-{2000+i}",
            "patient_id": random.choice(patients),
            "doctor": random.choice(DOCTORS),
            "department": random.choice(SPECIALTIES),
            "appointment_date": dt.strftime("%Y-%m-%d"),
            "appointment_time": f"{random.randint(8,17):02d}:{random.choice(['00','15','30','45'])}",
            "status": random.choice(["booked", "booked", "booked", "cancelled", "completed"]),
            "type": random.choice(["OPD", "Follow-up", "Procedure", "Review"]),
            "notes": random.choice(["Routine check-up", "Post-surgery review", "Medication review", ""]),
        })
    return pd.DataFrame(rows)


def generate_doctor_availability(n=20):
    rows = []
    for i in range(n):
        doctor = DOCTORS[i % len(DOCTORS)]
        dt = datetime.now() + timedelta(days=random.randint(1, 14))
        rows.append({
            "doctor": doctor,
            "specialty": SPECIALTIES[i % len(SPECIALTIES)],
            "available_date": dt.strftime("%Y-%m-%d"),
            "available_time": f"{random.randint(8,17):02d}:{random.choice(['00','30'])}",
            "slot_id": f"SLT-{3000+i}",
            "slot_duration_min": 15,
            "consultation_fee": random.choice([500, 800, 1000, 1200, 1500]),
        })
    return pd.DataFrame(rows)


def generate_medications(n=25):
    drugs = [
        ("Metformin", "500mg", "Twice daily"), ("Amlodipine", "5mg", "Once daily"),
        ("Atorvastatin", "10mg", "Once daily at night"), ("Aspirin", "75mg", "Once daily"),
        ("Metoprolol", "25mg", "Twice daily"), ("Pantoprazole", "40mg", "Once daily"),
        ("Furosemide", "40mg", "Once daily morning"), ("Insulin Glargine", "10 units", "Once daily bedtime"),
        ("Lisinopril", "10mg", "Once daily"), ("Gabapentin", "300mg", "Three times daily"),
    ]
    rows = []
    patients = [f"UHID-{1000+i}" for i in range(20)]
    for i in range(n):
        drug, dose, freq = drugs[i % len(drugs)]
        rows.append({
            "medication_id": f"MED-{4000+i}",
            "patient_id": random.choice(patients),
            "drug_name": drug,
            "dose": dose,
            "frequency": freq,
            "route": random.choice(["Oral", "Oral", "Oral", "Subcutaneous", "IV"]),
            "start_date": random_date(days_back=180, days_forward=0),
            "end_date": random_date(days_back=0, days_forward=180),
            "prescribing_doctor": random.choice(DOCTORS),
            "adherence_last_7d_pct": random.randint(60, 100),
        })
    return pd.DataFrame(rows)


def generate_vitals(n=30):
    rows = []
    patients = [f"UHID-{1000+i}" for i in range(20)]
    for i in range(n):
        dt = datetime.now() - timedelta(hours=random.randint(0, 72))
        rows.append({
            "observation_id": f"OBS-{5000+i}",
            "patient_id": random.choice(patients),
            "timestamp": dt.strftime("%Y-%m-%d %H:%M"),
            "bp_systolic": random.randint(100, 160),
            "bp_diastolic": random.randint(60, 100),
            "heart_rate": random.randint(55, 110),
            "spo2_pct": random.randint(92, 100),
            "temperature_c": round(random.uniform(36.0, 38.5), 1),
            "respiratory_rate": random.randint(14, 22),
            "weight_kg": random.randint(45, 110),
            "steps_today": random.randint(1000, 12000),
        })
    return pd.DataFrame(rows)


def generate_labs(n=30):
    rows = []
    patients = [f"UHID-{1000+i}" for i in range(20)]
    params = [
        ("HbA1c", "%", 4.0, 5.6), ("Creatinine", "mg/dL", 0.7, 1.2),
        ("Potassium", "mmol/L", 3.5, 5.0), ("Sodium", "mmol/L", 136, 145),
        ("Haemoglobin", "g/dL", 12.0, 16.0), ("Platelets", "x10^9/L", 150, 400),
        ("TSH", "mIU/L", 0.4, 4.0), ("ALT", "U/L", 7, 40),
        ("Urea", "mmol/L", 2.5, 7.1), ("Glucose_fasting", "mmol/L", 3.9, 5.5),
    ]
    for i in range(n):
        param, unit, lo, hi = random.choice(params)
        val = round(random.uniform(lo * 0.7, hi * 1.4), 2)
        rows.append({
            "report_id": f"LAB-{6000+i}",
            "patient_id": random.choice(patients),
            "test_date": random_date(days_back=365, days_forward=0),
            "parameter": param,
            "value": val,
            "unit": unit,
            "reference_low": lo,
            "reference_high": hi,
            "status": "NORMAL" if lo <= val <= hi else "HIGH" if val > hi else "LOW",
            "ordering_doctor": random.choice(DOCTORS),
            "lab_ref": f"LIS-{random.randint(100000, 999999)}",
        })
    return pd.DataFrame(rows)


def generate_ward_patients(n=20):
    rows = []
    for i in range(n):
        ward = random.choice(["3A", "3B", "ICU", "HDU", "2A"])
        rows.append({
            "ward_patient_id": f"WP-{7000+i}",
            "patient_id": f"UHID-{1000+i}",
            "name": random_name(),
            "ward": f"Ward {ward}",
            "bed": random.randint(1, 30),
            "admitting_doctor": random.choice(DOCTORS),
            "admitting_diagnosis": random.choice(CONDITIONS),
            "admission_date": random_date(days_back=10, days_forward=0),
            "post_op_day": random.randint(0, 7),
            "vitals": f"BP {random.randint(100,150)}/{random.randint(60,90)}, HR {random.randint(60,100)}, SpO2 {random.randint(92,100)}%",
            "news2_score": random.randint(0, 8),
            "nursing_notes_count": random.randint(1, 10),
            "pending_orders": random.randint(0, 5),
        })
    return pd.DataFrame(rows)


def generate_discharge_summaries(n=20):
    rows = []
    procedures = ["CABG", "Total knee replacement", "Laparoscopic cholecystectomy",
                   "Hip replacement", "Appendectomy", "Hysterectomy", "TURP",
                   "Laminectomy", "Mastectomy", "Caesarean section"]
    for i in range(n):
        discharge_dt = datetime.now() - timedelta(days=random.randint(1, 30))
        rows.append({
            "summary_id": f"DS-{8000+i}",
            "patient_id": f"UHID-{1000+i}",
            "patient_name": random_name(),
            "procedure": random.choice(procedures),
            "surgeon": random.choice(DOCTORS),
            "admission_date": (discharge_dt - timedelta(days=random.randint(2, 10))).strftime("%Y-%m-%d"),
            "discharge_date": discharge_dt.strftime("%Y-%m-%d"),
            "discharge_condition": random.choice(["Good", "Stable", "Satisfactory"]),
            "follow_up_date": (discharge_dt + timedelta(days=7)).strftime("%Y-%m-%d"),
            "medications_on_discharge": random.randint(2, 6),
            "wound_care_instructions": "Keep dry. Change dressing every 2 days.",
            "red_flags": "Fever >38.5°C, wound discharge, increasing pain — attend ED",
            "fasting_required": random.choice([True, False]),
        })
    return pd.DataFrame(rows)


def generate_care_plans(n=20):
    rows = []
    patients = [f"UHID-{1000+i}" for i in range(20)]
    for i in range(n):
        rows.append({
            "plan_id": f"CP-{9000+i}",
            "patient_id": patients[i],
            "condition": random.choice(CONDITIONS),
            "treating_doctor": random.choice(DOCTORS),
            "created_date": random_date(days_back=180, days_forward=0),
            "review_date": random_date(days_back=0, days_forward=90),
            "steps_target_per_day": random.choice([5000, 6000, 8000, 10000]),
            "caloric_target": random.choice([1600, 1800, 2000, 2200]),
            "bp_target": random.choice(["<130/80", "<140/90", "<125/75"]),
            "hba1c_target": random.choice(["<7%", "<7.5%", "<8%"]),
            "medication_schedule": f"{random.randint(2,4)} medications",
            "care_gap": random.choice(["HbA1c overdue", "Eye review due", "Foot review due", "None"]),
        })
    return pd.DataFrame(rows)


def generate_hospital_master():
    depts = pd.DataFrame([
        {"department_name": dept, "floor": random.randint(0, 5),
         "head_doctor": random.choice(DOCTORS),
         "bed_count": random.randint(10, 40),
         "phone_extension": random.randint(100, 999)}
        for dept in DEPARTMENTS + list(set(SPECIALTIES))
    ])
    doctors = pd.DataFrame([
        {"doctor_id": f"DR-{i:03d}", "name": doc,
         "specialty": SPECIALTIES[i % len(SPECIALTIES)],
         "qualification": "MBBS, MD", "available_today": random.choice([True, True, False]),
         "consultation_fee": random.choice([500, 800, 1000, 1500]),
         "languages": random.choice(["English, Hindi", "English, Kannada", "English, Tamil"])}
        for i, doc in enumerate(DOCTORS)
    ])
    timings = pd.DataFrame([
        {"department_name": dept,
         "weekday_hours": "08:00–20:00",
         "weekend_hours": "09:00–17:00",
         "emergency": "24/7",
         "last_updated": datetime.now().strftime("%Y-%m-%d")}
        for dept in DEPARTMENTS
    ])
    map_data = pd.DataFrame([
        {"location_name": loc, "floor": fl, "directions_from_entrance": direction}
        for loc, fl, direction in [
            ("OPD Registration", 0, "Straight ahead from main entrance, 50m"),
            ("Emergency", 0, "Turn left at main entrance, 30m"),
            ("Pharmacy", 0, "Right of OPD Registration"),
            ("Radiology", -1, "Take lift B1 — basement"),
            ("ICU", 3, "Lift to 3rd floor, turn right"),
            ("Surgery OT", 2, "Lift to 2nd floor, follow green signs"),
            ("Cardiology OPD", 1, "1st floor, turn left from lift"),
            ("Physiotherapy", 1, "1st floor, right wing"),
        ]
    ])
    procedures = pd.DataFrame([
        {"procedure_name": proc, "estimated_cost_inr": cost,
         "duration_minutes": dur, "department": dept}
        for proc, cost, dur, dept in [
            ("CABG", 250000, 240, "Cardiology"), ("Total Knee Replacement", 180000, 120, "Orthopaedics"),
            ("Laparoscopic Cholecystectomy", 60000, 60, "Surgery"),
            ("MRI Brain", 8000, 45, "Radiology"), ("CT Chest", 4500, 20, "Radiology"),
            ("Echocardiogram", 3500, 30, "Cardiology"), ("Coronary Angiography", 45000, 60, "Cardiology"),
            ("Appendectomy", 55000, 60, "Surgery"), ("Hysterectomy", 80000, 90, "Gynaecology"),
            ("Caesarean Section", 65000, 60, "Gynaecology"),
        ]
    ])
    return depts, doctors, timings, map_data, procedures


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # patients.xlsx
    patients_df = generate_patients(25)
    with pd.ExcelWriter(OUT_DIR / "patients.xlsx") as w:
        patients_df.to_excel(w, sheet_name="Patients", index=False)
        patients_df[["patient_id", "insurance_provider", "policy_number", "coverage_limit"]].to_excel(w, sheet_name="Insurance", index=False)

    # appointments.xlsx
    generate_appointments(30).to_excel(OUT_DIR / "appointments.xlsx", index=False)

    # doctor_availability.xlsx
    generate_doctor_availability(20).to_excel(OUT_DIR / "doctor_availability.xlsx", index=False)

    # medications.xlsx
    generate_medications(25).to_excel(OUT_DIR / "medications.xlsx", index=False)

    # vitals.xlsx
    generate_vitals(30).to_excel(OUT_DIR / "vitals.xlsx", index=False)

    # labs.xlsx
    generate_labs(30).to_excel(OUT_DIR / "labs.xlsx", index=False)

    # ward_patients.xlsx
    generate_ward_patients(20).to_excel(OUT_DIR / "ward_patients.xlsx", index=False)

    # discharge_summaries.xlsx
    generate_discharge_summaries(20).to_excel(OUT_DIR / "discharge_summaries.xlsx", index=False)

    # care_plans.xlsx
    generate_care_plans(20).to_excel(OUT_DIR / "care_plans.xlsx", index=False)

    # hospital_master.xlsx
    depts, doctors, timings, map_data, procedures = generate_hospital_master()
    with pd.ExcelWriter(OUT_DIR / "hospital_master.xlsx") as w:
        depts.to_excel(w, sheet_name="Departments", index=False)
        doctors.to_excel(w, sheet_name="Doctors", index=False)
        timings.to_excel(w, sheet_name="Timings", index=False)
        map_data.to_excel(w, sheet_name="Map", index=False)
        procedures.to_excel(w, sheet_name="Procedures", index=False)

    print("✅ Demo data generated successfully:")
    files = list(OUT_DIR.glob("*.xlsx"))
    for f in sorted(files):
        print(f"   {f.name}")
    return files


if __name__ == "__main__":
    main()
