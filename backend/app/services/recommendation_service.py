from typing import Dict, Any

CLINICAL_DISCLAIMER = (
    "DISCLAIMER: This platform provides decision-support risk assessment based on historical medical-device data. "
    "It does not monitor real-time physical device telemetry, predict exact days to failure, or replace manufacturer "
    "instructions, approved hospital maintenance procedures, safety notices, recalls, or professional biomedical engineering judgment."
)

class RecommendationService:
    def generate_recommendation(
        self,
        prediction: int,
        probability: float,
        input_data: Dict[str, Any]
    ) -> str:
        implanted = str(input_data.get("implanted", "NO")).upper() == "YES"
        risk_class = str(input_data.get("risk_class", ""))
        event_count = int(input_data.get("event_count", 0))

        lines = []

        if prediction == 1 or probability >= 0.5:
            lines.append("ACTION PROTOCOL: HIGH PRIORITY MAINTENANCE REVIEW")
            lines.append("1. Inspection Schedule: Expedite physical verification and performance testing within 24 to 48 hours.")
            lines.append("2. Maintenance History: Audit historical maintenance logs and calibration records for recurrent anomalies.")
            
            if event_count > 5:
                lines.append("3. Failure Pattern Investigation: Conduct targeted diagnostics focusing on subsystems flagged in previous event history.")
            else:
                lines.append("3. Preventive Maintenance: Perform manufacturer-recommended preventive maintenance and sensor/battery verification.")

            if implanted:
                lines.append("4. Critical Implant Protocol: Coordinate immediately with biomedical engineering leadership and clinical department.")
            else:
                lines.append("4. Quality Review: Check for applicable manufacturer field safety notices, safety alerts, or recall notices.")

            lines.append("5. Escalation: Log assessment findings into the hospital CMMS (Computerized Maintenance Management System).")
        else:
            lines.append("ACTION PROTOCOL: STANDARD PREVENTIVE MAINTENANCE")
            lines.append("1. Routine Inspection: Maintain standard periodic inspection interval as specified by the manufacturer.")
            lines.append("2. Operational Verification: Verify calibration tolerances and power/sensor baselines during standard rounds.")
            lines.append("3. Record Keeping: Log current operational hours and inspection outcome in routine maintenance records.")
            lines.append("4. Continuous Surveillance: Monitor upcoming manufacturer safety bulletins and periodic updates.")
            lines.append("5. Anomaly Escalation: If uncharacteristic sensor drift or physical wear is observed, initiate ad-hoc risk reassessment.")

        lines.append("")
        lines.append(CLINICAL_DISCLAIMER)

        return "\n".join(lines)

recommendation_service = RecommendationService()
